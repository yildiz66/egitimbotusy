"""
Web Arayüzü Güncelleyici
=========================
cikti/ klasörünü tarar → docs/dosyalar.json üretir.
GitHub Pages bu JSON'u okuyarak arayüzü günceller.
"""

import os
import json
from pathlib import Path
from datetime import datetime

BASE  = Path(__file__).parent.parent
CIKTI = BASE / "cikti"
DOCS  = BASE / "docs"
DOCS.mkdir(exist_ok=True)

TUR_META = {
    "gunluk_planlar": {"etiket":"Günlük Plan", "renk":"blue",   "ikon":"📚"},
    "sok":            {"etiket":"ŞÖK",         "renk":"blue",   "ikon":"📋"},
    "zumre":          {"etiket":"Zümre",       "renk":"green",  "ikon":"📗"},
    "veli":           {"etiket":"Veli",        "renk":"purple", "ikon":"👨‍👩‍👧"},
    "rehberlik":      {"etiket":"Rehberlik",   "renk":"amber",  "ikon":"💛"},
}


def dosya_tara() -> list:
    sonuc = []
    for yol in sorted(CIKTI.rglob("*.docx"), reverse=True):
        tur = yol.parent.name
        if tur == "tutanaklar":
            tur = "tutanaklar"
        meta = TUR_META.get(tur, {"etiket": tur, "renk": "gray", "ikon": "📄"})
        st   = yol.stat()
        tarih = datetime.fromtimestamp(st.st_mtime)
        sonuc.append({
            "ad":       yol.name,
            "tur":      tur,
            "etiket":   meta["etiket"],
            "renk":     meta["renk"],
            "ikon":     meta["ikon"],
            "boyut_kb": round(st.st_size / 1024, 1),
            "tarih":    tarih.strftime("%d.%m.%Y"),
            "tarih_ts": int(tarih.timestamp()),
            "url":      "../" + str(yol.relative_to(BASE)).replace("\\", "/"),
        })
    return sonuc


def ozetle(dosyalar):
    o = {"plan":0,"tutanak":0,"rehberlik":0,"toplam":len(dosyalar)}
    for d in dosyalar:
        if d["tur"] == "gunluk_planlar": o["plan"] += 1
        elif d["tur"] in ("sok","zumre","veli"): o["tutanak"] += 1
        elif d["tur"] == "rehberlik": o["rehberlik"] += 1
    return o


if __name__ == "__main__":
    dosyalar = dosya_tara()
    veri = {
        "okul_adi":    os.getenv("OKUL_ADI","Eğitim Asistanı"),
        "guncellendi": datetime.now().strftime("%d.%m.%Y %H:%M"),
        "ozet":        ozetle(dosyalar),
        "dosyalar":    dosyalar,
    }
    with open(DOCS / "dosyalar.json","w",encoding="utf-8") as f:
        json.dump(veri, f, ensure_ascii=False, indent=2)
    print(f"   ✓  {len(dosyalar)} dosya → docs/dosyalar.json")

def main():
    dosyalar = dosya_tara()
    veri = {
        "okul_adi":    os.getenv("OKUL_ADI","Eğitim Asistanı"),
        "guncellendi": datetime.now().strftime("%d.%m.%Y %H:%M"),
        "ozet":        ozetle(dosyalar),
        "dosyalar":    dosyalar,
    }
    with open(DOCS / "dosyalar.json","w",encoding="utf-8") as f:
        json.dump(veri, f, ensure_ascii=False, indent=2)
    print(f"   ✓  {len(dosyalar)} dosya → docs/dosyalar.json")
