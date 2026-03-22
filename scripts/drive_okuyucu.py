"""
Google Drive Okuyucu
====================
Google Drive'daki dosyaları indirir ve okur.
Ekstra kütüphane gerekmez — sadece requests kullanır.
"""

import os
import json
import time
import tempfile
from pathlib import Path

import requests

# GitHub Secrets'tan gelir
CREDENTIALS_JSON = os.getenv("GOOGLE_CREDENTIALS", "")
DRIVE_YENI       = os.getenv("DRIVE_YENI_KLASOR", "")
DRIVE_ESKI       = os.getenv("DRIVE_ESKI_KLASOR", "")

TOKEN_CACHE = {"token": None, "expires": 0}


def _token_al() -> str:
    """Service Account ile Google API token alır."""
    if TOKEN_CACHE["token"] and time.time() < TOKEN_CACHE["expires"] - 60:
        return TOKEN_CACHE["token"]

    if not CREDENTIALS_JSON:
        print("   ⚠  GOOGLE_CREDENTIALS eksik!")
        return ""

    try:
        creds = json.loads(CREDENTIALS_JSON)
    except Exception:
        print("   ⚠  GOOGLE_CREDENTIALS JSON formatı hatalı!")
        return ""

    import base64
    import hashlib
    import hmac

    # JWT oluştur
    now = int(time.time())
    header = base64.urlsafe_b64encode(
        json.dumps({"alg": "RS256", "typ": "JWT"}).encode()
    ).rstrip(b"=").decode()

    payload = base64.urlsafe_b64encode(json.dumps({
        "iss": creds["client_email"],
        "scope": "https://www.googleapis.com/auth/drive.readonly",
        "aud": "https://oauth2.googleapis.com/token",
        "exp": now + 3600,
        "iat": now,
    }).encode()).rstrip(b"=").decode()

    # RSA imzala — cryptography kütüphanesi gerekli
    try:
        from cryptography.hazmat.primitives import hashes, serialization
        from cryptography.hazmat.primitives.asymmetric import padding

        private_key = serialization.load_pem_private_key(
            creds["private_key"].encode(), password=None
        )
        message = f"{header}.{payload}".encode()
        signature = private_key.sign(message, padding.PKCS1v15(), hashes.SHA256())
        sig = base64.urlsafe_b64encode(signature).rstrip(b"=").decode()
        jwt = f"{header}.{payload}.{sig}"
    except ImportError:
        print("   ⚠  cryptography kütüphanesi eksik!")
        return ""
    except Exception as e:
        print(f"   ⚠  JWT imzalama hatası: {e}")
        return ""

    # Token al
    r = requests.post(
        "https://oauth2.googleapis.com/token",
        data={
            "grant_type": "urn:ietf:params:oauth:grant-type:jwt-bearer",
            "assertion": jwt,
        },
        timeout=15,
    )
    if r.status_code == 200:
        data = r.json()
        TOKEN_CACHE["token"]   = data["access_token"]
        TOKEN_CACHE["expires"] = now + data.get("expires_in", 3600)
        return TOKEN_CACHE["token"]
    else:
        print(f"   ⚠  Token alınamadı: {r.text[:200]}")
        return ""


def klasor_listele(klasor_id: str) -> list:
    """Drive klasöründeki dosyaları listeler."""
    token = _token_al()
    if not token:
        return []

    url = "https://www.googleapis.com/drive/v3/files"
    params = {
        "q": f"'{klasor_id}' in parents and trashed=false",
        "fields": "files(id,name,mimeType,size)",
        "pageSize": 100,
    }
    r = requests.get(url, headers={"Authorization": f"Bearer {token}"},
                     params=params, timeout=15)
    if r.status_code == 200:
        return r.json().get("files", [])
    print(f"   ⚠  Klasör listelenemedi: {r.text[:200]}")
    return []


def dosya_indir(dosya_id: str, dosya_adi: str, hedef_klasor: Path) -> Path | None:
    """Drive'dan dosyayı indirir, geçici klasöre kaydeder."""
    token = _token_al()
    if not token:
        return None

    hedef = hedef_klasor / dosya_adi
    if hedef.exists():
        return hedef  # Zaten indirilmiş

    # Google Docs ise export et
    EXPORT_MAP = {
        "application/vnd.google-apps.document":     ("application/vnd.openxmlformats-officedocument.wordprocessingml.document", ".docx"),
        "application/vnd.google-apps.spreadsheet":  ("application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", ".xlsx"),
        "application/vnd.google-apps.presentation": ("application/vnd.openxmlformats-officedocument.presentationml.presentation", ".pptx"),
    }

    r = requests.get(
        f"https://www.googleapis.com/drive/v3/files/{dosya_id}",
        headers={"Authorization": f"Bearer {token}"},
        params={"fields": "mimeType"},
        timeout=10,
    )
    mime = r.json().get("mimeType", "") if r.status_code == 200 else ""

    if mime in EXPORT_MAP:
        export_mime, ext = EXPORT_MAP[mime]
        hedef = hedef_klasor / (Path(dosya_adi).stem + ext)
        url = f"https://www.googleapis.com/drive/v3/files/{dosya_id}/export"
        params = {"mimeType": export_mime}
    else:
        url = f"https://www.googleapis.com/drive/v3/files/{dosya_id}"
        params = {"alt": "media"}

    r = requests.get(url, headers={"Authorization": f"Bearer {token}"},
                     params=params, timeout=60, stream=True)
    if r.status_code == 200:
        with open(hedef, "wb") as f:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)
        return hedef
    print(f"   ⚠  İndirilemedi: {dosya_adi}")
    return None


def drive_klasor_oku(klasor_id: str, gecici_klasor: Path) -> list[Path]:
    """
    Drive klasöründeki tüm dosyaları indirir,
    indirilen dosyaların yollarını döndürür.
    """
    if not klasor_id:
        return []

    gecici_klasor.mkdir(parents=True, exist_ok=True)
    dosyalar = klasor_listele(klasor_id)

    if not dosyalar:
        return []

    print(f"   📂 Drive'dan {len(dosyalar)} dosya bulundu.")
    indirilenler = []
    for d in dosyalar:
        # Geçici dosyaları atla
        if d["name"].startswith("~$") or d["name"].startswith("."):
            continue
        yol = dosya_indir(d["id"], d["name"], gecici_klasor)
        if yol:
            print(f"   ⬇  {d['name']}")
            indirilenler.append(yol)

    return indirilenler


def drive_aktif() -> bool:
    """Drive bağlantısı aktif mi kontrol eder."""
    return bool(CREDENTIALS_JSON and DRIVE_YENI)
