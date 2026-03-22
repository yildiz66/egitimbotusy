"""
Merkezi Konfigürasyon
=====================
Tüm ayarlar buradan yönetilir.
GitHub Secrets ile doldurulur, .env ile lokal test edilir.
"""

import os
from pathlib import Path

BASE = Path(__file__).parent.parent

# ── Kişisel Bilgiler (GitHub Secrets'tan gelir) ──
OKUL_ADI       = os.getenv("OKUL_ADI",       "Atatürk Ortaokulu")
OGRETMEN_ADI   = os.getenv("OGRETMEN_ADI",   "Öğretmen Adı Soyadı")
DERS           = os.getenv("DERS",           "Fen Bilimleri")
REHBERLIK_SINIF = os.getenv("REHBERLIK_SINIF", "6-C")   # Sınıf öğretmenliği

# Sınıflar: hangi modelle öğretim gördüğünü belirt
# Format: "SınıfŞube:model"  model = maarif | normal
SINIF_LISTESI = os.getenv("SINIFLAR", "6-C:normal,7-A:maarif,8-B:normal")

def sinif_modeli_parse(sinif_str: str) -> dict:
    """'6-C:normal,7-A:maarif' → {'6-C': 'normal', '7-A': 'maarif'}"""
    sonuc = {}
    for parca in sinif_str.split(","):
        parca = parca.strip()
        if ":" in parca:
            s, m = parca.split(":", 1)
            sonuc[s.strip()] = m.strip()
        else:
            sonuc[parca] = "normal"
    return sonuc

SINIFLAR = sinif_modeli_parse(SINIF_LISTESI)

# ── Telegram ──
TELEGRAM_TOKEN   = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID",   "")

# ── Klasörler ──
GIRDI = {
    "yillik_plan":      BASE / "girdi" / "yillik_plan",
    "ders_programi":    BASE / "girdi" / "ders_programi",
    "ders_kitaplari":   BASE / "girdi" / "ders_kitaplari",
    "onceki_evraklar":  BASE / "girdi" / "onceki_evraklar",
    "rehberlik_plani":  BASE / "girdi" / "rehberlik_plani",
}
CIKTI = {
    "gunluk_planlar":   BASE / "cikti" / "gunluk_planlar",
    "sok":              BASE / "cikti" / "tutanaklar" / "sok",
    "zumre":            BASE / "cikti" / "tutanaklar" / "zumre",
    "veli":             BASE / "cikti" / "tutanaklar" / "veli",
    "rehberlik":        BASE / "cikti" / "rehberlik",
}
DOCS = BASE / "docs"

for k in {**GIRDI, **CIKTI}.values():
    k.mkdir(parents=True, exist_ok=True)
DOCS.mkdir(exist_ok=True)

# ── Toplantı Takvimi ──
# Her ay hangi toplantı tutanağı üretilmeli
TOPLANTI_TAKVIMI = {
    "sok":    [9, 10, 11, 12, 1, 2, 3, 4, 5],  # Her ay (Eylül-Mayıs)
    "zumre":  [9, 1],                            # Dönem başları
    "veli":   [10, 2, 4],                        # Ekim, Şubat, Nisan
}

# ── Simülasyon/Animasyon Kaynakları ──
SIM_KAYNAKLARI = {
    "phet":  "https://phet.colorado.edu/tr/simulations/filter?subjects=",
    "eba":   "https://www.eba.gov.tr",
    "fenokulu": "https://www.fenokulu.net",
}

AYLAR_TR = {
    1:"Ocak", 2:"Şubat", 3:"Mart", 4:"Nisan", 5:"Mayıs", 6:"Haziran",
    7:"Temmuz", 8:"Ağustos", 9:"Eylül", 10:"Ekim", 11:"Kasım", 12:"Aralık"
}
GUNLER_TR = {
    0:"Pazartesi", 1:"Salı", 2:"Çarşamba",
    3:"Perşembe",  4:"Cuma", 5:"Cumartesi", 6:"Pazar"
}
