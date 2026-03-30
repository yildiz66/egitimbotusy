"""
AI Modülü — Groq
================
Groq: Günlük 14,400 istek — tamamen ücretsiz
Model: llama-3.3-70b-versatile (Türkçe çok iyi)

API Key: console.groq.com → ücretsiz hesap → API Keys
GitHub Secret: GROQ_API_KEY
"""

import os
import json
import re
import requests

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_MODEL   = "llama-3.3-70b-versatile"
GROQ_URL     = "https://api.groq.com/openai/v1/chat/completions"

_PLAN_CACHE = {}


def _groq_cagir(prompt: str, max_token: int = 2000) -> str:
    if not GROQ_API_KEY:
        print("   ⚠  GROQ_API_KEY eksik — şablon kullanılıyor.")
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
            print("   ⚠  Groq kota doldu — şablon kullanılıyor.")
        elif r.status_code == 401:
            print("   ⚠  Groq API key geçersiz!")
        else:
            print(f"   ⚠  Groq hata {r.status_code}: {r.text[:100]}")
        return ""
    except Exception as e:
        print(f"   ⚠  Groq bağlantı hatası: {e}")
        return ""


def _json_cikart(metin: str) -> dict | None:
    temiz = re.sub(r"```json|```", "", metin).strip()
    try:
        return json.loads(temiz)
    except Exception:
        m = re.search(r"\{.*\}", temiz, re.DOTALL)
        if m:
            try:
                return json.loads(m.group())
            except Exception:
                pass
    return None


def gunluk_plan_olustur(sinif: str, ders: str, konu: str,
                         kazanim: str, model: str, sure_dk: int = 80,
                         kitap_icerigi: str = "", eski_plan: str = "") -> dict:
    """
    Kazanıma özel ders akışı.
    kitap_icerigi: Ders kitabından ilgili bölüm (etkinlik + değerlendirme dahil)
    eski_plan: Önceki yıllarda yapılan benzer plan örneği
    """
    if not GROQ_API_KEY or not konu:
        return {}

    seviye    = sinif.split("-")[0]
    cache_key = f"{seviye}_{konu[:30]}"

    if cache_key in _PLAN_CACHE:
        print(f"   ♻️  Cache: {sinif} — {konu[:30]}")
        return _PLAN_CACHE[cache_key]

    if model == "maarif":
        model_notu = (
            "TURKİYE YÜZYILI MAALİF MODELİ (TYMM) formatinda plan hazirla. "
            "Su bolumler EKSIKSIZ doldurulmali: "
            "Ogrenme Ciktisi (FB kodu), Alt Ogrenme Ciktilari (a/b/c), "
            "Surec Bilesenleri, Egilimler (en az 2), Kavramsal Beceriler (en az 2), "
            "Sosyal-Duygusal Ogrenme (SDB kodu), Erdem-Deger-Eylem (somut), "
            "Farklilaştirma Zenginlestirme, Farklilaştirma Destekleme, "
            "Ogrenme Kanitlari. "
            "Ders kitabi icerigindeki etkinlikleri ve sorulari plana dahil et."
        )
    else:
        model_notu = "MEB normal mufredatina uygun, MEB kazanim kodlari (F.X.X.X.X) ile plan hazirla."

    # Ders kitabı ve eski plan bilgilerini ekle
    ek_bilgi = ""
    if kitap_icerigi and len(kitap_icerigi.strip()) > 50:
        ek_bilgi += "\n\nDERS KİTABI İÇERİĞİ (Bu bölüme sadık kal, etkinlikleri plana ekle):\n" + kitap_icerigi[:1500]
    else:
        ek_bilgi += "\n\n(Not: Ders kitabı içeriği bulunamadı, genel MEB müfredatına ve kazanım açıklamasına göre yaratıcı bir plan oluştur.)"
    
    if eski_plan:
        ek_bilgi += "\n\nÖNCEKİ YIL BENZER PLAN ÖRNEĞİ (stilini kullan):\n" + eski_plan[:600]

    if model == "maarif":
        json_format = """{{
  "ders_akisi": [
    {{"sure": "0-10 dk", "asama": "Öğrenmeye Hazırlık", "etkinlik": "..."}},
    {{"sure": "10-30 dk", "asama": "Keşfetme ve Araştırma", "etkinlik": "..."}},
    {{"sure": "30-50 dk", "asama": "Açıklama ve Tartışma", "etkinlik": "..."}},
    {{"sure": "50-65 dk", "asama": "Uygulama ve Derinleştirme", "etkinlik": "..."}},
    {{"sure": "65-80 dk", "asama": "Değerlendirme ve Yansıtma", "etkinlik": "..."}}
  ],
  "ogrenme_ciktisi": "FB.{seviye}.X.X — Tam ifade",
  "surec_bilesenleri": "a) ... b) ... c) ...",
  "egilimler": "Meraklı, Araştırmacı",
  "kavramsal_beceriler": "Sınıflama, Karşılaştırma",
  "sosyal_duygusal": "SDB1.2 — Kendini Düzenleme: ...",
  "erdem_deger_eylem": "Değer: Sorumluluk | Eylem: ...",
  "farklilaştirma_zenginlestirme": "İleri düzey öğrenciler için ek etkinlik: ...",
  "farklilaştirma_destekleme": "Güçlük çeken öğrenciler için destek: ...",
  "ogrenme_kanitlari": "Gözlem formu ve performans görevi",
  "simulasyon": "https://phet.colorado.edu/tr/...",
  "materyal": "Ders kitabı, deney malzemeleri",
  "odev": "...",
  "degerlendirme_sorulari": ["Soru 1?", "Soru 2?", "Soru 3?"]
}}"""
    else:
        json_format = """{{
  "ders_akisi": [
    {{"sure": "0-5 dk", "asama": "Giriş", "etkinlik": "..."}},
    {{"sure": "5-15 dk", "asama": "Motivasyon", "etkinlik": "..."}},
    {{"sure": "15-35 dk", "asama": "Kavram Sunumu", "etkinlik": "..."}},
    {{"sure": "35-55 dk", "asama": "Etkinlik/Deney", "etkinlik": "..."}},
    {{"sure": "55-65 dk", "asama": "Tartışma", "etkinlik": "..."}},
    {{"sure": "65-75 dk", "asama": "Değerlendirme", "etkinlik": "..."}},
    {{"sure": "75-80 dk", "asama": "Kapanış", "etkinlik": "..."}}
  ],
  "simulasyon": "https://phet.colorado.edu/tr/...",
  "materyal": "Gerekli materyal listesi",
  "odev": "Ev ödevi",
  "degerlendirme_sorulari": ["Soru 1?", "Soru 2?", "Soru 3?"]
}}"""

    prompt = f"""Türk ortaokulu {seviye}. sınıf için {sure_dk} dakikalık ders planı hazırla.
Ders: {ders} | Konu: {konu} | Kazanım: {kazanim}
{model_notu}{ek_bilgi}

Ders kitabındaki etkinlikleri ve değerlendirme sorularını plana dahil et.
Varsa eski plan stilini benimse ama içeriği güncelle.

SADECE JSON döndür, başka hiçbir şey yazma:
{json_format}"""

    print(f"   🤖 Groq plan yazıyor: {seviye}. sınıf — {konu[:40]}")
    yanit = _groq_cagir(prompt, max_token=1500)
    sonuc = _json_cikart(yanit) or {}
    if sonuc:
        _PLAN_CACHE[cache_key] = sonuc
    return sonuc


def tutanak_doldur(tur: str, ay: str, yil: int,
                   onceki_metin: str = "", sinif_bilgisi: str = "") -> dict:
    if not GROQ_API_KEY:
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
    yanit = _groq_cagir(prompt, max_token=1000)
    return _json_cikart(yanit) or {}


def rehberlik_yorum_olustur(sinif: str, ay: str, tema: str,
                              etkinlikler: list, notlar: str = "") -> str:
    if not GROQ_API_KEY:
        return ""
    prompt = f"""{sinif} sınıfı {ay} ayı rehberlik raporu yorumu yaz.
Tema: {tema} | Etkinlikler: {', '.join(etkinlikler)}
2-3 paragraf, resmi Türkçe. Sadece metin döndür."""
    return _groq_cagir(prompt, max_token=400)


def gemini_kontrol() -> bool:
    """Groq bağlantı testi."""
    if not GROQ_API_KEY:
        print("   ⚠  GROQ_API_KEY eksik!")
        print("      → console.groq.com → ücretsiz hesap → API Keys")
        print("      → GitHub Secrets → GROQ_API_KEY olarak ekle")
        return False
    yanit = _groq_cagir("Sadece OK yaz.", max_token=5)
    if yanit:
        print("   ✓  Groq bağlantısı başarılı.")
        return True
    print("   ✗  Groq bağlantısı başarısız.")
    return False
