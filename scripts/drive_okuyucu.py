"""
Google Drive Okuyucu
====================
Drive'daki dosyaları indirir.
Excel, Word, PDF, Google Docs hepsini destekler.
"""

import os
import json
import time
import re
from pathlib import Path
import requests

CREDENTIALS_JSON = os.getenv("GOOGLE_CREDENTIALS", "")
DRIVE_YENI       = os.getenv("DRIVE_YENI_KLASOR", "")
DRIVE_ESKI       = os.getenv("DRIVE_ESKI_KLASOR", "")

TOKEN_CACHE = {"token": None, "expires": 0}

# Google Docs formatlarını dönüştür
EXPORT_MAP = {
    "application/vnd.google-apps.document":
        ("application/vnd.openxmlformats-officedocument.wordprocessingml.document", ".docx"),
    "application/vnd.google-apps.spreadsheet":
        ("application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", ".xlsx"),
    "application/vnd.google-apps.presentation":
        ("application/vnd.openxmlformats-officedocument.presentationml.presentation", ".pptx"),
}


def _token_al() -> str:
    if TOKEN_CACHE["token"] and time.time() < TOKEN_CACHE["expires"] - 60:
        return TOKEN_CACHE["token"]
    if not CREDENTIALS_JSON:
        return ""
    try:
        creds = json.loads(CREDENTIALS_JSON)
    except Exception:
        print("   ⚠  GOOGLE_CREDENTIALS JSON formatı hatalı!")
        return ""
    try:
        import base64
        from cryptography.hazmat.primitives import hashes, serialization
        from cryptography.hazmat.primitives.asymmetric import padding

        now = int(time.time())
        header  = base64.urlsafe_b64encode(json.dumps({"alg":"RS256","typ":"JWT"}).encode()).rstrip(b"=").decode()
        payload = base64.urlsafe_b64encode(json.dumps({
            "iss":   creds["client_email"],
            "scope": "https://www.googleapis.com/auth/drive.readonly",
            "aud":   "https://oauth2.googleapis.com/token",
            "exp":   now + 3600, "iat": now,
        }).encode()).rstrip(b"=").decode()

        private_key = serialization.load_pem_private_key(creds["private_key"].encode(), password=None)
        sig = base64.urlsafe_b64encode(
            private_key.sign(f"{header}.{payload}".encode(), padding.PKCS1v15(), hashes.SHA256())
        ).rstrip(b"=").decode()
        jwt = f"{header}.{payload}.{sig}"

        r = requests.post("https://oauth2.googleapis.com/token",
                          data={"grant_type":"urn:ietf:params:oauth:grant-type:jwt-bearer","assertion":jwt},
                          timeout=15)
        if r.status_code == 200:
            data = r.json()
            TOKEN_CACHE["token"]   = data["access_token"]
            TOKEN_CACHE["expires"] = now + data.get("expires_in", 3600)
            return TOKEN_CACHE["token"]
        print(f"   ⚠  Token alınamadı: {r.text[:200]}")
        return ""
    except ImportError:
        print("   ⚠  cryptography kütüphanesi eksik!")
        return ""
    except Exception as e:
        print(f"   ⚠  JWT hatası: {e}")
        return ""


def klasor_listele(klasor_id: str) -> list:
    token = _token_al()
    if not token:
        return []
    r = requests.get(
        "https://www.googleapis.com/drive/v3/files",
        headers={"Authorization": f"Bearer {token}"},
        params={
            "q": f"'{klasor_id}' in parents and trashed=false",
            "fields": "files(id,name,mimeType,size)",
            "pageSize": 100,
        }, timeout=15,
    )
    if r.status_code == 200:
        return r.json().get("files", [])
    print(f"   ⚠  Klasör listelenemedi: {r.text[:200]}")
    return []


def dosya_indir(dosya_id: str, dosya_adi: str, mime_type: str, hedef_klasor: Path) -> Path | None:
    """Drive'dan dosyayı indirir. MIME type'a göre export veya direkt indirir."""
    token = _token_al()
    if not token:
        return None

    # Dosya adını temizle
    temiz_ad = re.sub(r'[<>:"/\\|?*]', '_', dosya_adi)

    # Google Docs formatı → export et
    if mime_type in EXPORT_MAP:
        export_mime, ext = EXPORT_MAP[mime_type]
        hedef = hedef_klasor / (Path(temiz_ad).stem + ext)
        if hedef.exists():
            return hedef
        url    = f"https://www.googleapis.com/drive/v3/files/{dosya_id}/export"
        params = {"mimeType": export_mime}
    else:
        # Uzantı yoksa mime'dan tahmin et
        uzanti = Path(temiz_ad).suffix
        if not uzanti:
            mime_uzanti = {
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": ".xlsx",
                "application/vnd.openxmlformats-officedocument.wordprocessingml.document": ".docx",
                "application/pdf": ".pdf",
            }
            uzanti = mime_uzanti.get(mime_type, "")
            temiz_ad = temiz_ad + uzanti

        hedef = hedef_klasor / temiz_ad
        if hedef.exists():
            return hedef
        url    = f"https://www.googleapis.com/drive/v3/files/{dosya_id}"
        params = {"alt": "media"}

    r = requests.get(url, headers={"Authorization": f"Bearer {token}"},
                     params=params, timeout=120, stream=True)
    if r.status_code == 200:
        with open(hedef, "wb") as f:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)
        return hedef

    print(f"   ⚠  İndirilemedi ({r.status_code}): {dosya_adi}")
    return None


def drive_klasor_oku(klasor_id: str, gecici_klasor: Path) -> list[Path]:
    """Drive klasöründeki tüm dosyaları indirir."""
    if not klasor_id:
        return []
    gecici_klasor.mkdir(parents=True, exist_ok=True)
    dosyalar = klasor_listele(klasor_id)
    if not dosyalar:
        return []

    print(f"   📂 Drive'dan {len(dosyalar)} dosya bulundu.")
    indirilenler = []
    for d in dosyalar:
        ad = d.get("name", "")
        # Geçici ve gizli dosyaları atla
        if ad.startswith("~$") or ad.startswith("."):
            continue
        # Klasörleri atla
        if d.get("mimeType") == "application/vnd.google-apps.folder":
            print(f"   ℹ  Klasör atlandı: {ad} (dosyaları direkt yeni_belgeler'e koy)")
            continue
        yol = dosya_indir(d["id"], ad, d.get("mimeType",""), gecici_klasor)
        if yol:
            print(f"   ⬇  {yol.name}")
            indirilenler.append(yol)

    return indirilenler


def drive_aktif() -> bool:
    return bool(CREDENTIALS_JSON and DRIVE_YENI)

