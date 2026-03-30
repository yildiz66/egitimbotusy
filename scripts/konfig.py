import os
from pathlib import Path
from datetime import datetime

BASE = Path(__file__).parent.parent

OKUL_ADI        = os.getenv("OKUL_ADI",        "Atatürk Ortaokulu")
OGRETMEN_ADI    = os.getenv("OGRETMEN_ADI",    "Öğretmen Adı Soyadı")
DERS            = os.getenv("DERS",            "Fen Bilimleri")
REHBERLIK_SINIF = os.getenv("REHBERLIK_SINIF", "6-C")
SINIF_LISTESI   = os.getenv("SINIFLAR",        "6-C:normal,7-A:normal")

def sinif_modeli_parse(s):
    sonuc = {}
    for p in s.split(","):
        p = p.strip()
        if ":" in p:
            k, v = p.split(":", 1)
            sonuc[k.strip()] = v.strip()
        else:
            sonuc[p] = "normal"
    return sonuc

SINIFLAR = sinif_modeli_parse(SINIF_LISTESI)

TELEGRAM_TOKEN   = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID",   "")

# YENİ: İki klasör sistemi ve Tarih bazlı çıktı
simdi = datetime.now()
klasor_eki = f"{simdi.year}-{simdi.month:02d}"
DOCS = BASE / "docs"

GIRDI = {
    "eski_belgeler":  BASE / "girdi" / "eski_belgeler",
    "yeni_belgeler":  BASE / "girdi" / "yeni_belgeler",
    "ders_programi":  BASE / "girdi" / "ders_programi",
}
CIKTI = {
    "ana":            DOCS / "cikti" / klasor_eki,
    "gunluk_planlar": DOCS / "cikti" / klasor_eki / "gunluk_planlar",
    "sok":            DOCS / "cikti" / klasor_eki / "tutanaklar" / "sok",
    "zumre":          DOCS / "cikti" / klasor_eki / "tutanaklar" / "zumre",
    "veli":           DOCS / "cikti" / klasor_eki / "tutanaklar" / "veli",
    "rehberlik":      DOCS / "cikti" / klasor_eki / "rehberlik",
}

for k in {**GIRDI, **CIKTI}.values():
    k.mkdir(parents=True, exist_ok=True)
DOCS.mkdir(exist_ok=True)

TOPLANTI_TAKVIMI = {
    "sok":   [9,10,11,12,1,2,3,4,5],
    "zumre": [9, 1],
    "veli":  [10, 2, 4],
}

AYLAR_TR = {1:"Ocak",2:"Şubat",3:"Mart",4:"Nisan",5:"Mayıs",6:"Haziran",
            7:"Temmuz",8:"Ağustos",9:"Eylül",10:"Ekim",11:"Kasım",12:"Aralık"}
GUNLER_TR = {0:"Pazartesi",1:"Salı",2:"Çarşamba",3:"Perşembe",4:"Cuma",5:"Cumartesi",6:"Pazar"}
