"""
Ders Programı Okuyucu
=====================
Word / Excel / PDF / Görsel (fotoğraf) her formattan okur.
Evrensel okuyucuyu kullanır.
"""

from pathlib import Path
from datetime import datetime
from evrensel_okuyucu import program_oku

GUNLER_TR = ["Pazartesi","Salı","Çarşamba","Perşembe","Cuma","Cumartesi","Pazar"]

ORNEK_PROGRAM = {
    "Pazartesi": [{"saat":"08:00","sinif":"7-A"},{"saat":"10:00","sinif":"6-C"}],
    "Salı":      [{"saat":"08:00","sinif":"8-B"},{"saat":"11:00","sinif":"6-C"}],
    "Çarşamba":  [{"saat":"09:00","sinif":"7-A"},{"saat":"11:00","sinif":"8-B"}],
    "Perşembe":  [{"saat":"08:00","sinif":"6-C"},{"saat":"10:00","sinif":"7-A"}],
    "Cuma":      [{"saat":"09:00","sinif":"8-B"}],
}


class DersProgramiOkuyucu:
    def __init__(self, klasor: Path):
        self.klasor = klasor
        self.program = program_oku(klasor) or ORNEK_PROGRAM

    def gun_derslerini_al(self, tarih: datetime) -> list:
        gun = GUNLER_TR[tarih.weekday()]
        return self.program.get(gun, [])
