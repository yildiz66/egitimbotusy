"""
Gemini AI Modülü — Optimize Edilmiş
=====================================
Kota kullanımı minimuma indirildi:
- Aynı konu için cache — tekrar çağrı yok
- Belge sınıflandırma için Gemini kullanılmıyor (anahtar kelime yeterli)
- Günde maksimum 5-6 istek
"""

import os
import json
import re
import base64
from pathlib import Path
import requests

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
MODEL   = "gemini-2.0-flash"
API_URL = f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL}:generateContent"

# Cache — aynı konu için tekrar çağrı yapma
_PLAN_CACHE = {}


def _api_cagir(icerik: list, max_token: int = 2000) -> str:
    if not GEMINI_API_KEY:
        return ""
    payload = {
        "contents": [{"parts": icerik}],
        "generationConfig": {"maxOutputTokens": max_token, "temperature": 0.3}
    }
    try:
        r = requests.post(f"{API_URL}?key={GEMINI_API_KEY}", json=payload, timeout=30)
        if r.status_code == 200:
            return r.json()["candidates"][0]["content"]["parts"][0]["text"].strip()
        elif r.status_code == 429:
            print("   ⚠  Gemini günlük kota doldu — yarın sıfırlanır, şablon kullanılıyor.")
        else:
            print(f"   ⚠  Gemini hata {r.status_code}")
        return ""
    except Exception as e:
        print(f"   ⚠  Gemini bağlantı hatası: {e}")
        return ""


def _json_cikart(metin: str) -> dict | list | None:
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


def gunluk_plan_olustur(sinif: str, ders: str, konu: str,
                         kazanim: str, model: str, sure_dk: int = 80) -> dict:
    """
    Kazanıma özel ders akışı üretir.
    CACHE: Aynı konu+sınıf seviyesi için tekrar çağrı yapmaz.
    """
    if not GEMINI_API_KEY or not konu:
        return {}

    # Cache key: sınıf seviyesi + konu (aynı seviyedeki farklı şubeler aynı planı kullanır)
    seviye   = sinif.split("-")[0]
    cache_key = f"{seviye}_{konu[:30]}"

    if cache_key in _PLAN_CACHE:
        print(f"   ♻️  Cache'den plan: {sinif} — {konu[:30]}")
        return _PLAN_CACHE[cache_key]

    model_notu = (
        "Maarif modeli — değerler eğitimi ve Maarif vizyonuna uygun etkinlikler ekle."
        if model == "maarif" else
        "MEB normal müfredatına uygun etkinlikler."
    )

    prompt = f"""Türk ortaokulu {seviye}. sınıf için {sure_dk} dakikalık ders planı hazırla.
Ders: {ders} | Konu: {konu} | Kazanım: {kazanim}
{model_notu}

SADECE JSON döndür:
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
  "simulasyon": "https://phet.colorado.edu/tr/... veya uygun link",
  "materyal": "Gerekli materyal",
  "odev": "Ev ödevi",
  "degerlendirme_sorulari": ["Soru 1?", "Soru 2?", "Soru 3?"]
}}"""

    print(f"   🤖 Gemini plan yazıyor: {seviye}. sınıf — {konu[:40]}")
    yanit  = _api_cagir([{"text": prompt}], max_token=1500)
    sonuc  = _json_cikart(yanit) or {}

    if sonuc:
        _PLAN_CACHE[cache_key] = sonuc  # Cache'e kaydet

    return sonuc


def tutanak_doldur(tur: str, ay: str, yil: int,
                   onceki_metin: str = "", sinif_bilgisi: str = "") -> dict:
    """Toplantı tutanağı gündem ve kararlarını doldurur."""
    if not GEMINI_API_KEY:
        return {}

    tur_ad = {"sok":"Şube Öğretmenler Kurulu","zumre":"Zümre","veli":"Veli Toplantısı"}.get(tur, tur)
    onceki = f"\nÖnceki toplantı özeti:\n{onceki_metin[:800]}" if onceki_metin else ""

    prompt = f"""Türk ortaokulu {ay} {yil} {tur_ad} tutanağı hazırla.{onceki}

SADECE JSON döndür:
{{
  "gundem_maddeleri": [
    {{"no": 1, "madde": "...", "karar": "..."}},
    {{"no": 2, "madde": "...", "karar": "..."}},
    {{"no": 3, "madde": "...", "karar": "..."}},
    {{"no": 4, "madde": "...", "karar": "..."}},
    {{"no": 5, "madde": "Dilek ve öneriler", "karar": "Toplantı sona erdi."}}
  ],
  "genel_karar": "Kararlar oy birliği ile alındı."
}}"""

    print(f"   🤖 Gemini tutanak dolduruyor: {tur_ad}")
    yanit = _api_cagir([{"text": prompt}], max_token=1000)
    return _json_cikart(yanit) or {}


def rehberlik_yorum_olustur(sinif: str, ay: str, tema: str,
                              etkinlikler: list, notlar: str = "") -> str:
    """Rehberlik raporu yorum bölümü yazar."""
    if not GEMINI_API_KEY:
        return ""
    prompt = f"""{sinif} sınıfı {ay} ayı rehberlik raporu yorum yaz.
Tema: {tema} | Etkinlikler: {', '.join(etkinlikler)}
2-3 paragraf, resmi dil. Sadece metin döndür."""
    return _api_cagir([{"text": prompt}], max_token=400)


def gemini_kontrol() -> bool:
    if not GEMINI_API_KEY:
        print("   ⚠  GEMINI_API_KEY eksik — aistudio.google.com'dan ücretsiz key al")
        return False
    yanit = _api_cagir([{"text": "Sadece OK yaz."}], max_token=5)
    if yanit:
        print("   ✓  Gemini bağlantısı başarılı.")
        return True
    return False
