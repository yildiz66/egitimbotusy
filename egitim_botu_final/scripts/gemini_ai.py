"""
Gemini AI Modülü
================
Google Gemini Flash API'yi kullanır.
Tamamen ücretsiz (günlük 1500 istek kotası).
Ekstra kütüphane gerekmez — sadece requests kullanır.

API Key alma:
  1. https://aistudio.google.com adresine git
  2. "Get API Key" → "Create API key"
  3. Kopyala → GitHub Secret'a GEMINI_API_KEY olarak ekle
"""

import os
import json
import re
import base64
from pathlib import Path

import requests

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
# Ücretsiz ve hızlı model
MODEL = "gemini-2.0-flash"
API_URL = f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL}:generateContent"


def _api_cagir(icerik: list, max_token: int = 2000) -> str:
    """Gemini REST API'yi çağırır, ham metin döndürür."""
    if not GEMINI_API_KEY:
        return ""

    payload = {
        "contents": [{"parts": icerik}],
        "generationConfig": {
            "maxOutputTokens": max_token,
            "temperature": 0.3,
        }
    }
    try:
        r = requests.post(
            f"{API_URL}?key={GEMINI_API_KEY}",
            json=payload,
            timeout=30,
        )
        if r.status_code == 200:
            data = r.json()
            return data["candidates"][0]["content"]["parts"][0]["text"].strip()
        else:
            print(f"   ⚠  Gemini hata {r.status_code}: {r.text[:200]}")
            return ""
    except Exception as e:
        print(f"   ⚠  Gemini bağlantı hatası: {e}")
        return ""


def _json_cikart(metin: str) -> dict | list | None:
    """Gemini çıktısından JSON çıkarır."""
    temiz = re.sub(r"```json|```", "", metin).strip()
    try:
        return json.loads(temiz)
    except Exception:
        m = re.search(r"\{.*\}|\[.*\]", temiz, re.DOTALL)
        if m:
            try:
                return json.loads(m.group())
            except Exception:
                pass
    return None


# ══════════════════════════════════════════════════════
# 1. DERS PROGRAMI GÖRSELI OKU
# ══════════════════════════════════════════════════════

def gorsel_program_oku(gorsel_yolu: Path) -> dict:
    """
    Ders programı fotoğrafını Gemini Vision ile okur.
    OCR'dan çok daha akıllı — karmaşık tablo formatlarını anlar.
    """
    if not GEMINI_API_KEY:
        return {}

    with open(gorsel_yolu, "rb") as f:
        gorsel_b64 = base64.b64encode(f.read()).decode()

    uzanti = gorsel_yolu.suffix.lower().lstrip(".")
    mime = {"jpg": "image/jpeg", "jpeg": "image/jpeg",
            "png": "image/png", "webp": "image/webp"}.get(uzanti, "image/jpeg")

    prompt = """Bu görsel bir okul ders programıdır.
Tablodan tüm dersleri çıkar ve SADECE şu JSON formatında döndür, başka hiçbir şey yazma:

{
  "Pazartesi": [{"saat": "08:00", "sinif": "7-A"}, ...],
  "Sali": [...],
  "Carsamba": [...],
  "Persembe": [...],
  "Cuma": [...]
}

Kurallar:
- Sınıf adını "7-A", "6-C" gibi yaz
- Saati "08:00" formatında yaz
- Boş hücreleri ekleme
- Türkçe karakter olmayan gün adları kullan (Sali, Carsamba, Persembe)"""

    icerik = [
        {"text": prompt},
        {"inline_data": {"mime_type": mime, "data": gorsel_b64}},
    ]

    print(f"   🤖 Gemini görsel okuyor: {gorsel_yolu.name}")
    yanit = _api_cagir(icerik, max_token=1000)
    if not yanit:
        return {}

    veri = _json_cikart(yanit)
    if not isinstance(veri, dict):
        return {}

    # Gün adlarını normalize et
    gun_map = {
        "Sali": "Salı", "Carsamba": "Çarşamba",
        "Persembe": "Perşembe", "Pazartesi": "Pazartesi", "Cuma": "Cuma"
    }
    return {gun_map.get(k, k): v for k, v in veri.items() if v}


# ══════════════════════════════════════════════════════
# 2. YILLIK PLANDAN KONU + KAZANIM ÇEK
# ══════════════════════════════════════════════════════

def yillik_plandan_hafta_cikart(plan_metni: str, sinif: str,
                                  model: str, hafta: int) -> dict | None:
    """
    Yıllık plan metninden belirli haftanın konusunu ve kazanımını çıkarır.
    Word/PDF/Excel'den okunmuş ham metin girer, yapılandırılmış veri çıkar.
    """
    if not GEMINI_API_KEY or not plan_metni.strip():
        return None

    prompt = f"""Aşağıdaki yıllık plan metni bir {sinif} sınıfı {model} müfredatına aittir.
{hafta}. haftanın bilgilerini çıkar ve SADECE şu JSON formatında döndür:

{{
  "unite": "Ünite adı",
  "konu": "Haftanın konusu",
  "kazanim": "F.X.X.X.X — Kazanım ifadesi",
  "alt_konular": ["alt konu 1", "alt konu 2"]
}}

Eğer {hafta}. hafta bulunamazsa en yakın haftayı kullan.
Sadece JSON döndür, açıklama yazma.

YILLIK PLAN METNİ:
{plan_metni[:3000]}"""

    yanit = _api_cagir([{"text": prompt}], max_token=500)
    return _json_cikart(yanit) if yanit else None


# ══════════════════════════════════════════════════════
# 3. GÜNLÜK PLAN ETKİNLİK OLUŞTUR
# ══════════════════════════════════════════════════════

def gunluk_plan_olustur(sinif: str, ders: str, konu: str,
                         kazanim: str, model: str, sure_dk: int = 80) -> dict:
    """
    Kazanıma özel, sınıfa uygun ders akışı ve etkinlikler üretir.
    Simülasyon önerileri de içerir.
    """
    if not GEMINI_API_KEY:
        return {}

    model_notu = (
        "Bu sınıf Maarif modeli ile eğitim görmektedir. "
        "Değerler eğitimi ve Maarif vizyonuna uygun etkinlikler ekle."
        if model == "maarif" else
        "MEB normal müfredatına uygun etkinlikler ekle."
    )

    prompt = f"""Sen deneyimli bir Türk ortaokul öğretmenisin.
Aşağıdaki bilgilere göre {sure_dk} dakikalık bir ders planı hazırla.

Sınıf: {sinif}
Ders: {ders}
Konu: {konu}
Kazanım: {kazanim}
Model Notu: {model_notu}

SADECE şu JSON formatında döndür, başka hiçbir şey yazma:
{{
  "ders_akisi": [
    {{"sure": "0-5 dk", "asama": "Giriş", "etkinlik": "..."}},
    {{"sure": "5-15 dk", "asama": "Motivasyon", "etkinlik": "..."}},
    {{"sure": "15-35 dk", "asama": "Kavram Sunumu", "etkinlik": "..."}},
    {{"sure": "35-55 dk", "asama": "Etkinlik/Deney", "etkinlik": "..."}},
    {{"sure": "55-65 dk", "asama": "Tartışma", "etkinlik": "..."}},
    {{"sure": "65-75 dk", "asama": "Değerlendirme", "etkinlik": "..."}},
    {{"sure": "75-80 dk", "asama": "Kapanış", "etkinlik": "..."}}
  ],
  "simulasyon": "https://phet.colorado.edu/tr/... veya başka uygun link",
  "materyal": "Gerekli materyal listesi",
  "odev": "Ev ödevi",
  "degerlendirme_sorulari": ["Soru 1?", "Soru 2?", "Soru 3?"]
}}"""

    print(f"   🤖 Gemini plan yazıyor: {sinif} — {konu}")
    yanit = _api_cagir([{"text": prompt}], max_token=1500)
    return _json_cikart(yanit) or {}


# ══════════════════════════════════════════════════════
# 4. TUTANAK DOLDUR
# ══════════════════════════════════════════════════════

def tutanak_doldur(tur: str, ay: str, yil: int,
                   onceki_tutanak_metni: str = "",
                   sinif_bilgisi: str = "") -> dict:
    """
    Toplantı türüne, aya ve önceki tutanaklara bakarak
    gündem maddelerini ve karar önerilerini doldurur.
    """
    if not GEMINI_API_KEY:
        return {}

    tur_aciklama = {
        "sok":    "Şube Öğretmenler Kurulu (ŞÖK)",
        "zumre":  "Zümre Öğretmenler Kurulu",
        "veli":   "Veli Toplantısı",
    }.get(tur, tur)

    onceki_bilgi = f"\nÖnceki toplantı özeti:\n{onceki_tutanak_metni[:1000]}" if onceki_tutanak_metni else ""
    sinif_bilgi  = f"\nSınıf bilgisi: {sinif_bilgisi}" if sinif_bilgisi else ""

    prompt = f"""Türk ortaokulu için {ay} {yil} ayına ait {tur_aciklama} tutanağı hazırla.
{onceki_bilgi}{sinif_bilgi}

SADECE şu JSON formatında döndür:
{{
  "gundem_maddeleri": [
    {{"no": 1, "madde": "...", "karar": "..."}},
    {{"no": 2, "madde": "...", "karar": "..."}},
    {{"no": 3, "madde": "...", "karar": "..."}},
    {{"no": 4, "madde": "...", "karar": "..."}},
    {{"no": 5, "madde": "Dilek ve öneriler", "karar": "Toplantı sona erdi."}}
  ],
  "genel_karar": "Toplantı kararları oy birliği ile alınmıştır.",
  "sonraki_toplanti": "Bir sonraki toplantı tarihi okul idaresi tarafından duyurulacaktır."
}}"""

    print(f"   🤖 Gemini tutanak dolduruyor: {tur_aciklama} — {ay} {yil}")
    yanit = _api_cagir([{"text": prompt}], max_token=1200)
    return _json_cikart(yanit) or {}


# ══════════════════════════════════════════════════════
# 5. REHBERLİK RAPORU YORUM OLUŞTUR
# ══════════════════════════════════════════════════════

def rehberlik_yorum_olustur(sinif: str, ay: str, tema: str,
                              etkinlikler: list, notlar: str = "") -> str:
    """
    Aylık rehberlik raporu için öğretmen yorum bölümünü yazar.
    """
    if not GEMINI_API_KEY:
        return ""

    prompt = f"""Türk ortaokulu {sinif} sınıfı için {ay} ayı rehberlik raporu yorum bölümünü yaz.
Tema: {tema}
Yapılan etkinlikler: {', '.join(etkinlikler)}
Öğretmen notu: {notlar or 'Yok'}

2-3 paragraf, resmi ama sıcak bir dille yaz. 
Sadece metni döndür, başka hiçbir şey ekleme."""

    yanit = _api_cagir([{"text": prompt}], max_token=400)
    return yanit


# ══════════════════════════════════════════════════════
# DURUM KONTROLÜ
# ══════════════════════════════════════════════════════

def gemini_kontrol() -> bool:
    """API key ve bağlantıyı test eder."""
    if not GEMINI_API_KEY:
        print("   ⚠  GEMINI_API_KEY bulunamadı — YZ özellikleri devre dışı.")
        print("      → https://aistudio.google.com adresinden ücretsiz API key al")
        print("      → GitHub Secrets'a GEMINI_API_KEY olarak ekle")
        return False

    yanit = _api_cagir([{"text": "Merhaba, sadece 'OK' yaz."}], max_token=10)
    if yanit:
        print("   ✓  Gemini bağlantısı başarılı.")
        return True
    else:
        print("   ✗  Gemini bağlantısı başarısız — API key doğru mu?")
        return False
