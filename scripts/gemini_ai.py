"""
AI Modülü — Groq (Birincil) + Gemini (Yedek)
==============================================
Groq: Günlük 14,400 istek — ücretsiz, çok hızlı
Gemini: Yedek olarak kullanılır

Groq modeli: llama-3.3-70b-versatile (Türkçe çok iyi)
"""

import os
import json
import re
import requests

GROQ_API_KEY   = os.getenv("GROQ_API_KEY", "")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

GROQ_MODEL   = "llama-3.3-70b-versatile"
GROQ_URL     = "https://api.groq.com/openai/v1/chat/completions"
GEMINI_URL   = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"

# Cache — aynı konu için tekrar çağrı yapma
_PLAN_CACHE = {}


def _groq_cagir(prompt: str, max_token: int = 2000) -> str:
    """Groq API çağrısı."""
    if not GROQ_API_KEY:
        return ""
    try:
        r = requests.post(
            GROQ_URL,
            headers={
                "Authorization": f"Bearer {GROQ_API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "model": GROQ_MODEL,
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": max_token,
                "temperature": 0.3,
            },
            timeout=30,
        )
        if r.status_code == 200:
            return r.json()["choices"][0]["message"]["content"].strip()
        elif r.status_code == 429:
            print("   ⚠  Groq kota doldu — Gemini'ye geçiliyor.")
            return ""
        else:
            print(f"   ⚠  Groq hata {r.status_code}")
            return ""
    except Exception as e:
        print(f"   ⚠  Groq bağlantı hatası: {e}")
        return ""


def _gemini_cagir(prompt: str, max_token: int = 2000) -> str:
    """Gemini API yedek çağrısı."""
    if not GEMINI_API_KEY:
        return ""
    try:
        r = requests.post(
            f"{GEMINI_URL}?key={GEMINI_API_KEY}",
            json={
                "contents": [{"parts": [{"text": prompt}]}],
                "generationConfig": {"maxOutputTokens": max_token, "temperature": 0.3}
            },
            timeout=30,
        )
        if r.status_code == 200:
            return r.json()["candidates"][0]["content"]["parts"][0]["text"].strip()
        elif r.status_code == 429:
            print("   ⚠  Gemini de kota doldu — şablon kullanılıyor.")
        return ""
    except Exception:
        return ""


def _ai_cagir(prompt: str, max_token: int = 2000) -> str:
    """Önce Groq, başarısız olursa Gemini dener."""
    yanit = _groq_cagir(prompt, max_token)
    if yanit:
        return yanit
    return _gemini_cagir(prompt, max_token)


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
    """Kazanıma özel ders akışı. Cache ile kota tasarrufu."""
    if not (GROQ_API_KEY or GEMINI_API_KEY) or not konu:
        return {}

    seviye    = sinif.split("-")[0]
    cache_key = f"{seviye}_{konu[:30]}"

    if cache_key in _PLAN_CACHE:
        print(f"   ♻️  Cache: {sinif} — {konu[:30]}")
        return _PLAN_CACHE[cache_key]

    model_notu = (
        "Maarif modeli — değerler eğitimi ekle."
        if model == "maarif" else
        "MEB normal müfredatı."
    )

    prompt = f"""Türk ortaokulu {seviye}. sınıf için {sure_dk} dakikalık ders planı hazırla.
Ders: {ders} | Konu: {konu} | Kazanım: {kazanim} | {model_notu}

SADECE JSON döndür, başka hiçbir şey yazma:
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
  "materyal": "Gerekli materyal listesi",
  "odev": "Ev ödevi",
  "degerlendirme_sorulari": ["Soru 1?", "Soru 2?", "Soru 3?"]
}}"""

    print(f"   🤖 Groq plan yazıyor: {seviye}. sınıf — {konu[:40]}")
    yanit = _ai_cagir(prompt, max_token=1500)
    sonuc = _json_cikart(yanit) or {}
    if sonuc:
        _PLAN_CACHE[cache_key] = sonuc
    return sonuc


def tutanak_doldur(tur: str, ay: str, yil: int,
                   onceki_metin: str = "", sinif_bilgisi: str = "") -> dict:
    """Tutanak gündem ve kararlarını doldurur."""
    if not (GROQ_API_KEY or GEMINI_API_KEY):
        return {}

    tur_ad = {
        "sok":   "Şube Öğretmenler Kurulu (ŞÖK)",
        "zumre": "Zümre Öğretmenler Kurulu",
        "veli":  "Veli Toplantısı"
    }.get(tur, tur)

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

    print(f"   🤖 Groq tutanak dolduruyor: {tur_ad}")
    yanit = _ai_cagir(prompt, max_token=1000)
    return _json_cikart(yanit) or {}


def rehberlik_yorum_olustur(sinif: str, ay: str, tema: str,
                              etkinlikler: list, notlar: str = "") -> str:
    """Rehberlik raporu yorum bölümü yazar."""
    if not (GROQ_API_KEY or GEMINI_API_KEY):
        return ""
    prompt = f"""{sinif} sınıfı {ay} ayı rehberlik raporu yorumu yaz.
Tema: {tema} | Etkinlikler: {', '.join(etkinlikler)}
2-3 paragraf, resmi Türkçe. Sadece metin döndür."""
    return _ai_cagir(prompt, max_token=400)


def ai_kontrol() -> bool:
    """Bağlantı testi."""
    if GROQ_API_KEY:
        yanit = _groq_cagir("Sadece OK yaz.", max_token=5)
        if yanit:
            print("   ✓  Groq bağlantısı başarılı.")
            return True
    if GEMINI_API_KEY:
        yanit = _gemini_cagir("Sadece OK yaz.", max_token=5)
        if yanit:
            print("   ✓  Gemini yedek bağlantısı başarılı.")
            return True
    print("   ⚠  AI bağlantısı yok — şablon kullanılacak.")
    return False


# Geriye dönük uyumluluk
gemini_kontrol = ai_kontrol
