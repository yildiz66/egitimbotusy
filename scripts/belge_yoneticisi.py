"""
Belge Yöneticisi
================
Drive ve GitHub'daki dosyaları tarar, türlerine göre sınıflandırır.
Dosya adından akıllıca tür tahmin eder.
"""

import re
from pathlib import Path
import tempfile
from evrensel_okuyucu import dosya_oku, klasor_tara

# ── Dosya adı bazlı kesin kurallar (öncelikli) ──
AD_KURALLARI = [
    (r'\d+_sinif_\d+_hafta',           "gunluk_plan"),
    (r'soktopt|toptut|sok.*tut|tut.*sok', "sok"),
    (r'zumre|zümre',                   "zumre"),
    (r'veli.*top|top.*veli',           "veli"),
    (r'maarif.*rapor|degerlendirme.*rapor|aylik.*rapor', "rehberlik"),
    (r'rehberlik.*plan|pdr',           "rehberlik"),
    (r'ders.*kitab|kitab.*fen|\d+.*sinif.*kitap|kitap.*\d+.*sinif', "ders_kitabi"),
    (r'yillik.*plan|cerc.*eve.*plan',  "yillik_plan"),
    (r'gunluk.*plan|plan.*gunluk',     "gunluk_plan"),
]

# ── İçerik bazlı anahtar kelimeler (yedek) ──
ICERIK_ANAHTARLARI = {
    "gunluk_plan":  ["günlük plan","ders akışı","kazanım","süre","aşama","etkinlik","öğretmen adı"],
    "yillik_plan":  ["yıllık plan","ünite","hafta","öğretim yılı","kazanım kodu"],
    "sok":          ["şube öğretmenler","şök","toplantı tutanağı","gündem"],
    "zumre":        ["zümre","zümre öğretmenler"],
    "veli":         ["veli toplantı","veli bilgilendirme","velilere"],
    "rehberlik":    ["rehberlik","pdr","rehber öğretmen","bireysel görüşme"],
    "ders_kitabi":  ["ders kitabı","meb yayınları","öğrenci kitabı","alıştırma","etkinlik","sayfa"],
}


def belge_siniflandir(dosya: Path) -> str:
    """Dosya adı ve içeriğinden tür tahmin eder. Gemini kullanmaz."""
    ad = dosya.stem.lower().replace(" ", "_").replace(".", "_")

    # 1. Dosya adından kesin kural
    for pattern, tur in AD_KURALLARI:
        if re.search(pattern, ad):
            return tur

    # 2. İçerik anahtar kelimeleri
    metin = dosya_oku(dosya)
    if not metin:
        return "diger"

    metin_l = metin.lower()
    sayimlar = {}
    for tur, kelimeler in ICERIK_ANAHTARLARI.items():
        s = sum(1 for k in kelimeler if k in metin_l)
        if s > 0:
            sayimlar[tur] = s
    return max(sayimlar, key=sayimlar.get) if sayimlar else "diger"


class BelgeYoneticisi:
    def __init__(self, girdi_klasoru: Path):
        self.girdi      = girdi_klasoru
        self.eski_lokal = girdi_klasoru / "eski_belgeler"
        self.yeni_lokal = girdi_klasoru / "yeni_belgeler"
        self._gecici    = Path(tempfile.mkdtemp())
        self._cache     = {}
        self.eski_lokal.mkdir(parents=True, exist_ok=True)
        self.yeni_lokal.mkdir(parents=True, exist_ok=True)

    def _drive_indir(self, tip: str) -> list[Path]:
        try:
            from drive_okuyucu import drive_klasor_oku, drive_aktif, DRIVE_YENI, DRIVE_ESKI
            if not drive_aktif():
                return []
            klasor_id = DRIVE_YENI if tip == "yeni" else DRIVE_ESKI
            if not klasor_id:
                return []
            return drive_klasor_oku(klasor_id, self._gecici / tip)
        except Exception as e:
            print(f"   ⚠  Drive bağlantısı: {e}")
            return []

    def _tara(self, tip: str) -> dict:
        if tip in self._cache:
            return self._cache[tip]

        drive_dosyalar = self._drive_indir(tip)
        lokal = self.yeni_lokal if tip == "yeni" else self.eski_lokal
        lokal_dosyalar = klasor_tara(lokal)
        tum_dosyalar = drive_dosyalar + lokal_dosyalar

        sonuc = {}
        for dosya in tum_dosyalar:
            tur = belge_siniflandir(dosya)
            sonuc.setdefault(tur, []).append(dosya)
            print(f"   📄 {dosya.name[:50]} → {tur}")

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
        return "\n".join(dosya_oku(d) for d in dosyalar)

    def onceki_tutanak_metni(self, tur: str) -> str:
        dosyalar = self.tur_dosyalari(tur, "eski")
        return "\n".join(dosya_oku(d) for d in dosyalar[-2:])

    def eski_plan_metni(self, sinif_seviyesi: str) -> str:
        """Eski günlük planlardan belirli sınıf seviyesinin örneklerini döndürür."""
        dosyalar = self.tur_dosyalari("gunluk_plan", "eski")
        ilgili = [d for d in dosyalar if sinif_seviyesi in d.name.lower()]
        if not ilgili:
            ilgili = dosyalar[:2]
        return "\n---\n".join(dosya_oku(d) for d in ilgili[:2])

    def ders_kitabi_bolumleri(self, sinif_seviyesi: str, konu: str) -> str:
        """
        İlgili sınıfın ders kitabından konuyla ilgili bölümleri çeker.
        Etkinlik ve değerlendirme sorularını da içerir.
        """
        dosyalar = self.tur_dosyalari("ders_kitabi", "yeni")
        # Sınıf seviyesine göre kitabı bul
        ilgili = [d for d in dosyalar if sinif_seviyesi in d.name.lower()]
        if not ilgili:
            ilgili = dosyalar

        if not ilgili:
            return ""

        konu_anahtar = konu.lower()[:30]
        for kitap in ilgili:
            metin = dosya_oku(kitap)
            if not metin:
                continue
            # Konuyla ilgili bölümleri bul
            satirlar = metin.split("\n")
            ilgili_satirlar = []
            yakalandi = False
            for satir in satirlar:
                if konu_anahtar in satir.lower():
                    yakalandi = True
                if yakalandi:
                    ilgili_satirlar.append(satir)
                    if len(ilgili_satirlar) > 60:
                        break

            if ilgili_satirlar:
                return "\n".join(ilgili_satirlar[:60])

        return ""

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
