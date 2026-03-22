"""
Belge Sınıflandırıcı
====================
girdi/eski_belgeler/ ve girdi/yeni_belgeler/ klasörlerindeki
dosyaları okur, Gemini ile ne tür belge olduğunu anlar,
doğru yere yönlendirir.

Belge türleri:
  - yillik_plan      → Yıllık ders planı
  - ders_kitabi      → Ders kitabı
  - sok              → ŞÖK tutanağı
  - zumre            → Zümre tutanağı
  - veli             → Veli toplantısı tutanağı
  - rehberlik        → Rehberlik planı/raporu
  - ders_programi    → Haftalık ders programı
  - diger            → Diğer
"""

import os
import re
from pathlib import Path
from evrensel_okuyucu import dosya_oku, klasor_tara

# Anahtar kelime bazlı hızlı sınıflandırma (Gemini yokken)
ANAHTAR_KELIMELER = {
    "yillik_plan": [
        "yıllık plan", "yillik plan", "ünite", "kazanım", "hafta",
        "öğretim yılı", "ders planı"
    ],
    "sok": [
        "şube öğretmenler", "şök", "sok", "şube öğretmen kurulu"
    ],
    "zumre": [
        "zümre", "zumre", "zümre öğretmenler"
    ],
    "veli": [
        "veli toplantı", "veli bilgilendirme", "veli görüşme"
    ],
    "rehberlik": [
        "rehberlik", "pdr", "rehber öğretmen", "bireysel görüşme"
    ],
    "ders_kitabi": [
        "ders kitabı", "meb yayınları", "öğrenci kitabı", "alıştırma"
    ],
    "ders_programi": [
        "ders programı", "haftalık program", "ders çizelge",
        "pazartesi", "salı", "çarşamba"
    ],
}


def anahtar_ile_siniflandir(metin: str) -> str:
    """Metindeki anahtar kelimelere göre belge türünü tahmin eder."""
    metin_lower = metin.lower()
    sayimlar = {}
    for tur, kelimeler in ANAHTAR_KELIMELER.items():
        sayim = sum(1 for k in kelimeler if k in metin_lower)
        if sayim > 0:
            sayimlar[tur] = sayim
    if sayimlar:
        return max(sayimlar, key=sayimlar.get)
    return "diger"


def gemini_ile_siniflandir(dosya_adi: str, metin_ozet: str) -> str:
    """Gemini ile belge türünü tespit eder."""
    try:
        from gemini_ai import _api_cagir, _json_cikart
        prompt = f"""Bu bir Türk ortaokulu belgesinin adı ve özeti:

Dosya adı: {dosya_adi}
İçerik özeti: {metin_ozet[:500]}

Bu belge hangi türdür? Sadece şu seçeneklerden birini yaz:
yillik_plan / sok / zumre / veli / rehberlik / ders_kitabi / ders_programi / diger"""

        yanit = _api_cagir([{"text": prompt}], max_token=20)
        if yanit:
            yanit = yanit.strip().lower()
            for tur in ANAHTAR_KELIMELER:
                if tur in yanit:
                    return tur
    except Exception:
        pass
    return None


def belge_siniflandir(dosya: Path) -> str:
    """Bir dosyanın türünü tespit eder."""
    # 1. Dosya adından tahmin
    ad = dosya.stem.lower()
    for tur, kelimeler in ANAHTAR_KELIMELER.items():
        for k in kelimeler:
            if k.replace(" ", "") in ad.replace(" ", ""):
                return tur

    # 2. İçerik oku
    metin = dosya_oku(dosya)
    if not metin:
        return "diger"

    # 3. Gemini ile dene
    gemini_sonuc = gemini_ile_siniflandir(dosya.name, metin)
    if gemini_sonuc:
        return gemini_sonuc

    # 4. Anahtar kelime ile
    return anahtar_ile_siniflandir(metin)


class BelgeYoneticisi:
    """
    eski_belgeler/ ve yeni_belgeler/ klasörlerini yönetir.
    Dosyaları okur, türlerine göre sınıflandırır.
    """

    def __init__(self, girdi_klasoru: Path):
        self.eski = girdi_klasoru / "eski_belgeler"
        self.yeni = girdi_klasoru / "yeni_belgeler"
        self.eski.mkdir(parents=True, exist_ok=True)
        self.yeni.mkdir(parents=True, exist_ok=True)
        self._cache = {}

    def _klasor_tara(self, klasor: Path) -> dict:
        """Klasördeki dosyaları türlerine göre gruplar."""
        sonuc = {}
        for dosya in klasor_tara(klasor):
            tur = belge_siniflandir(dosya)
            if tur not in sonuc:
                sonuc[tur] = []
            sonuc[tur].append(dosya)
            print(f"   📄 {dosya.name} → {tur}")
        return sonuc

    def yeni_belgeler(self) -> dict:
        """Yeni belgeler klasörünü tarar."""
        anahtar = "yeni"
        if anahtar not in self._cache:
            print("   🔍 Yeni belgeler taranıyor...")
            self._cache[anahtar] = self._klasor_tara(self.yeni)
        return self._cache[anahtar]

    def eski_belgeler(self) -> dict:
        """Eski belgeler klasörünü tarar."""
        anahtar = "eski"
        if anahtar not in self._cache:
            print("   🔍 Eski belgeler taranıyor...")
            self._cache[anahtar] = self._klasor_tara(self.eski)
        return self._cache[anahtar]

    def tur_dosyalari(self, tur: str, kaynak: str = "yeni") -> list:
        """Belirli türdeki dosyaları döndürür."""
        belgeler = self.yeni_belgeler() if kaynak == "yeni" else self.eski_belgeler()
        return belgeler.get(tur, [])

    def yillik_plan_metni(self, model: str = "normal") -> str:
        """Yeni belgelerden yıllık plan metnini döndürür."""
        dosyalar = self.tur_dosyalari("yillik_plan", "yeni")
        if not dosyalar:
            return ""
        metin = ""
        for d in dosyalar:
            metin += dosya_oku(d) + "\n"
        return metin

    def onceki_tutanak_metni(self, tur: str) -> str:
        """Eski belgelerden belirli tür tutanak metnini döndürür."""
        dosyalar = self.tur_dosyalari(tur, "eski")
        if not dosyalar:
            return ""
        # En son 2 tutanağı al
        return "\n".join(dosya_oku(d) for d in dosyalar[-2:])

    def ozet(self):
        """Yüklenen dosyaların özetini yazdırır."""
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
