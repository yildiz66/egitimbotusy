"""
Evrak Öğrenici
==============
Önceki yüklenen evrakları okur (Word/Excel/PDF/Görsel),
gündem maddelerini ve karar kalıplarını öğrenir.
Yeni tutanaklara otomatik olarak ekler.
"""

import re
from pathlib import Path
from evrensel_okuyucu import dosya_oku, klasor_tara


class EvrakOgrenici:
    def __init__(self, evrak_klasoru: Path):
        self.klasor = evrak_klasoru
        self._cache = {}

    def _gundem_cikart(self, metin: str) -> list:
        maddeler = []
        yakalandi = False
        for satir in metin.split("\n"):
            satir = satir.strip()
            if not satir:
                continue
            if re.search(r"gündem|gündem madde", satir, re.IGNORECASE):
                yakalandi = True
                continue
            if yakalandi:
                if re.match(r"^(\d+[\.\-\)]\s+|madde\s+\d+)", satir, re.IGNORECASE):
                    temiz = re.sub(r"^[\d\.\-\)\s]+|^madde\s+\d+[\s\.\-]*", "", satir, flags=re.IGNORECASE).strip()
                    if temiz:
                        maddeler.append(temiz)
                elif len(maddeler) >= 3 and not re.match(r"\w", satir):
                    break
        return maddeler

    def _karar_cikart(self, metin: str) -> list:
        kararlar = []
        for satir in metin.split("\n"):
            satir = satir.strip()
            if re.search(r"kararlaştırıldı|oy birliği|karar verildi", satir, re.IGNORECASE):
                if len(satir) > 20:
                    kararlar.append(satir)
            if len(kararlar) >= 5:
                break
        return kararlar

    def sablon_ogren(self, tur: str) -> dict:
        """Belirli tür için önceki evraklardan şablon öğrenir."""
        if tur in self._cache:
            return self._cache[tur]

        klasor = self.klasor / tur
        if not klasor.exists():
            return {}

        dosyalar = klasor_tara(klasor)
        if not dosyalar:
            return {}

        tum_gundemler = []
        tum_kararlar  = []

        for dosya in dosyalar[-3:]:   # Son 3 evrak yeterli
            metin = dosya_oku(dosya)
            if not metin:
                continue
            tum_gundemler.extend(self._gundem_cikart(metin))
            tum_kararlar.extend(self._karar_cikart(metin))

        sablon = {
            "ozel_gundemler":  list(dict.fromkeys(tum_gundemler)),
            "karar_kaliplari": tum_kararlar[:5],
        }
        self._cache[tur] = sablon
        if sablon["ozel_gundemler"]:
            print(f"   ✓  [{tur}] {len(sablon['ozel_gundemler'])} gündem öğrenildi.")
        return sablon
