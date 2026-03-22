"""
Belge Yöneticisi
================
Önce Google Drive'a bakar, sonra GitHub'daki klasörlere.
Sen dosyaları Drive'a atarsın, bot oradan okur.

Klasör yapısı (Drive'da):
  egitim-botu/
  ├── yeni_belgeler/   ← yıllık plan, ders kitabı, rehberlik planı
  └── eski_belgeler/   ← eski tutanaklar, evraklar

Bot:
  1. Drive'dan dosyaları indirir
  2. Ne tür belge olduğunu anlar
  3. Planlara, tutanaklara dahil eder
"""

import os
import re
import tempfile
from pathlib import Path
from evrensel_okuyucu import dosya_oku, klasor_tara

ANAHTAR_KELIMELER = {
    "yillik_plan":  ["yıllık plan","yillik plan","ünite","kazanım","hafta","öğretim yılı"],
    "sok":          ["şube öğretmenler","şök","sok"],
    "zumre":        ["zümre","zumre"],
    "veli":         ["veli toplantı","veli bilgilendirme"],
    "rehberlik":    ["rehberlik","pdr","rehber öğretmen"],
    "ders_kitabi":  ["ders kitabı","meb yayınları","öğrenci kitabı"],
    "ders_programi":["ders programı","haftalık program","pazartesi","salı"],
}


def anahtar_ile_siniflandir(metin: str) -> str:
    ml = metin.lower()
    sayimlar = {}
    for tur, kelimeler in ANAHTAR_KELIMELER.items():
        s = sum(1 for k in kelimeler if k in ml)
        if s > 0:
            sayimlar[tur] = s
    return max(sayimlar, key=sayimlar.get) if sayimlar else "diger"


def belge_siniflandir(dosya: Path) -> str:
    ad = dosya.stem.lower()
    for tur, kelimeler in ANAHTAR_KELIMELER.items():
        for k in kelimeler:
            if k.replace(" ","") in ad.replace(" ",""):
                return tur
    metin = dosya_oku(dosya)
    if not metin:
        return "diger"
    # Gemini ile dene
    try:
        from gemini_ai import _api_cagir
        prompt = f"Dosya adı: {dosya.name}\nİçerik: {metin[:300]}\n\nBu belge hangi tür? Sadece şunu yaz: yillik_plan / sok / zumre / veli / rehberlik / ders_kitabi / ders_programi / diger"
        yanit = _api_cagir([{"text": prompt}], max_token=20)
        if yanit:
            yanit = yanit.strip().lower()
            for tur in ANAHTAR_KELIMELER:
                if tur in yanit:
                    return tur
    except Exception:
        pass
    return anahtar_ile_siniflandir(metin)


class BelgeYoneticisi:
    def __init__(self, girdi_klasoru: Path):
        self.girdi        = girdi_klasoru
        self.eski_lokal   = girdi_klasoru / "eski_belgeler"
        self.yeni_lokal   = girdi_klasoru / "yeni_belgeler"
        self._gecici      = Path(tempfile.mkdtemp())
        self._cache       = {}

        self.eski_lokal.mkdir(parents=True, exist_ok=True)
        self.yeni_lokal.mkdir(parents=True, exist_ok=True)

    def _drive_indir(self, tip: str) -> list[Path]:
        """Drive'dan ilgili klasörü indirir."""
        try:
            from drive_okuyucu import drive_klasor_oku, drive_aktif, DRIVE_YENI, DRIVE_ESKI
            if not drive_aktif():
                return []
            klasor_id = DRIVE_YENI if tip == "yeni" else DRIVE_ESKI
            if not klasor_id:
                return []
            gecici = self._gecici / tip
            return drive_klasor_oku(klasor_id, gecici)
        except Exception as e:
            print(f"   ⚠  Drive bağlantısı: {e}")
            return []

    def _tara(self, tip: str) -> dict:
        if tip in self._cache:
            return self._cache[tip]

        # Önce Drive
        drive_dosyalar = self._drive_indir(tip)

        # Sonra lokal GitHub klasörü
        lokal = self.yeni_lokal if tip == "yeni" else self.eski_lokal
        lokal_dosyalar = klasor_tara(lokal)

        tum_dosyalar = drive_dosyalar + lokal_dosyalar

        sonuc = {}
        for dosya in tum_dosyalar:
            tur = belge_siniflandir(dosya)
            if tur not in sonuc:
                sonuc[tur] = []
            sonuc[tur].append(dosya)
            print(f"   📄 {dosya.name} → {tur}")

        self._cache[tip] = sonuc
        return sonuc

    def yeni_belgeler(self) -> dict:
        print("   🔍 Yeni belgeler taranıyor...")
        return self._tara("yeni")

    def eski_belgeler(self) -> dict:
        print("   🔍 Eski belgeler taranıyor...")
        return self._tara("eski")

    def tur_dosyalari(self, tur: str, kaynak: str = "yeni") -> list:
        b = self.yeni_belgeler() if kaynak == "yeni" else self.eski_belgeler()
        return b.get(tur, [])

    def yillik_plan_metni(self, model: str = "normal") -> str:
        dosyalar = self.tur_dosyalari("yillik_plan", "yeni")
        if not dosyalar:
            return ""
        return "\n".join(dosya_oku(d) for d in dosyalar)

    def onceki_tutanak_metni(self, tur: str) -> str:
        dosyalar = self.tur_dosyalari(tur, "eski")
        return "\n".join(dosya_oku(d) for d in dosyalar[-2:])

    def ozet(self):
        print("\n   📁 YENİ BELGELER:")
        yeni = self.yeni_belgeler()
        if not yeni:
            print("      Henüz dosya yüklenmemiş.")
        for tur, dosyalar in yeni.items():
            print(f"      {tur}: {len(dosyalar)} dosya")

        print("\n   📁 ESKİ BELGELER:")
        eski = self.eski_belgeler()
        if not eski:
            print("      Henüz dosya yüklenmemiş.")
        for tur, dosyalar in eski.items():
            print(f"      {tur}: {len(dosyalar)} dosya")
        print()
