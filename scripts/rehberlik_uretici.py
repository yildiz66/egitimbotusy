"""
Rehberlik Rapor Üretici
=======================
6. sınıf sınıf öğretmenliği için
aylık ve dönemlik rehberlik raporlarını üretir.
"""

from pathlib import Path
from datetime import datetime
from word_utils import (yeni_belge, baslik_ekle, paragraf_ekle,
                         bolum_basligi, tablo_olustur, imza_tablosu)
from docx.enum.text import WD_ALIGN_PARAGRAPH

AYLAR_TR = {1:"Ocak",2:"Şubat",3:"Mart",4:"Nisan",5:"Mayıs",6:"Haziran",
            7:"Temmuz",8:"Ağustos",9:"Eylül",10:"Ekim",11:"Kasım",12:"Aralık"}

# Aylık rehberlik etkinlik planı (6. sınıf)
AYLIK_PLAN = {
    9:  {"tema": "Okula Uyum ve Tanışma",         "etkinlikler": ["Kendini tanıtma etkinliği","Sınıf kurallarını oluşturma","Okul ve sınıf gezisi"]},
    10: {"tema": "Zaman Yönetimi ve Çalışma",      "etkinlikler": ["Ders çalışma tekniklerini öğrenme","Program yapma atölyesi","Motivasyon etkinliği"]},
    11: {"tema": "Kişisel Gelişim ve Öz Saygı",    "etkinlikler": ["Güçlü yönlerimi keşfediyorum","Olumlu düşünce egzersizleri","Hedef belirleme çalışması"]},
    12: {"tema": "İletişim Becerileri",             "etkinlikler": ["Etkin dinleme egzersizi","Empati çalışması","Çatışma çözme rol yapma"]},
    1:  {"tema": "Kariyer Farkındalığı",            "etkinlikler": ["Meslekleri tanıyorum","İlgi alanlarımı keşfediyorum","Gelecek planım"]},
    2:  {"tema": "Akran İlişkileri ve Zorbalık",    "etkinlikler": ["Arkadaşlık ve saygı","Zorbalıkla baş etme","Güvenli ortam oluşturma"]},
    3:  {"tema": "Duygusal Zeka",                   "etkinlikler": ["Duygularımı tanıyorum","Öfke yönetimi","Empati geliştirme"]},
    4:  {"tema": "Sağlıklı Yaşam",                  "etkinlikler": ["Sağlıklı beslenme","Ekran süresi farkındalığı","Spor ve hareket"]},
    5:  {"tema": "Değerler Eğitimi ve Kapanış",     "etkinlikler": ["Yıl değerlendirmesi","Değerlerim kimim","Mezuniyet motivasyonu"]},
}

RENK    = "5A1A6A"   # Mor — rehberlik
AC_RENK = "F0E8F8"


class RehberlikUretici:
    def __init__(self, konfig: dict, cikti_klasoru: Path, rehberlik_plani: Path):
        self.konfig         = konfig
        self.cikti_klasoru  = cikti_klasoru
        self.rehberlik_plani = rehberlik_plani
        self.cikti_klasoru.mkdir(parents=True, exist_ok=True)

    def aylik_kontrol(self, tarih: datetime) -> list:
        """Bu ay için rehberlik raporu yoksa üretir."""
        ay  = tarih.month
        yil = tarih.year
        if ay not in AYLIK_PLAN:
            return []
        dosya_adi = f"Rehberlik_{self.konfig['rehberlik_sinif'].replace('-','')}_{yil}_{ay:02d}.docx"
        dosya_yolu = self.cikti_klasoru / dosya_adi
        if dosya_yolu.exists():
            print(f"   ℹ  {dosya_adi} zaten var.")
            return []
        self.aylik_rapor(tarih)
        return [dosya_yolu]

    def aylik_rapor(self, tarih: datetime) -> Path:
        ay     = tarih.month
        ay_adi = AYLAR_TR.get(ay, "")
        plan   = AYLIK_PLAN.get(ay, {"tema": "Genel", "etkinlikler": []})
        sinif  = self.konfig.get("rehberlik_sinif", "6-C")
        yil_donem = f"{tarih.year}-{tarih.year+1} {'1.' if ay >= 9 else '2.'} Dönem"

        doc = yeni_belge()

        paragraf_ekle(doc, "T.C.", boyut=10, hizalama=WD_ALIGN_PARAGRAPH.CENTER)
        paragraf_ekle(doc, "MİLLÎ EĞİTİM BAKANLIĞI", boyut=10, hizalama=WD_ALIGN_PARAGRAPH.CENTER)
        paragraf_ekle(doc, self.konfig["okul_adi"].upper(), boyut=11, kalin=True, hizalama=WD_ALIGN_PARAGRAPH.CENTER)
        baslik_ekle(doc, f"REHBERLİK AYLIK RAPORU — {ay_adi.upper()} {tarih.year}", boyut=13, renk=RENK)

        tablo_olustur(doc,
            basliklar=["Alan","Bilgi","Alan","Bilgi"],
            satirlar=[
                ["Sınıf Öğretmeni", self.konfig["ogretmen_adi"], "Sınıf",      sinif],
                ["Okul",            self.konfig["okul_adi"],      "Dönem",      yil_donem],
                ["Ay",              f"{ay_adi} {tarih.year}",     "Tema",       plan["tema"]],
            ],
            baslik_rengi=RENK, satir_renkleri=(AC_RENK, "FFFFFF")
        )
        paragraf_ekle(doc, "", sonra=4)

        # Aylık etkinlikler
        bolum_basligi(doc, "AYLIK ETKİNLİKLER", renk=RENK)
        tablo_olustur(doc,
            basliklar=["No","Etkinlik Adı","Uygulama Tarihi","Sonuç / Gözlem"],
            satirlar=[[str(i+1), e, "", ""] for i, e in enumerate(plan["etkinlikler"])],
            baslik_rengi=RENK, satir_renkleri=(AC_RENK, "FFFFFF")
        )
        paragraf_ekle(doc, "", sonra=4)

        # Öğrenci takip tablosu
        bolum_basligi(doc, "GENEL SINIF DURUMU", renk=RENK)
        tablo_olustur(doc,
            basliklar=["Konu","Değerlendirme","Açıklama"],
            satirlar=[
                ["Genel Uyum Durumu",       "İyi / Orta / Gelişmeli", ""],
                ["Akademik Motivasyon",      "İyi / Orta / Gelişmeli", ""],
                ["Sosyal İlişkiler",         "İyi / Orta / Gelişmeli", ""],
                ["Dikkat Gerektiren Durum",  "Var / Yok",              ""],
                ["Veli ile İletişim",        "Yapıldı / Planlandı",    ""],
            ],
            baslik_rengi=RENK, satir_renkleri=(AC_RENK, "FFFFFF")
        )
        paragraf_ekle(doc, "", sonra=4)

        # Bireysel takip gerektiren öğrenciler
        bolum_basligi(doc, "BİREYSEL TAKİP GEREKTİREN ÖĞRENCİLER", renk=RENK)
        tablo_olustur(doc,
            basliklar=["Öğrenci No","Durum","Yapılan Görüşme","Alınan Önlem"],
            satirlar=[["","","",""] for _ in range(4)],
            baslik_rengi=RENK, satir_renkleri=(AC_RENK, "FFFFFF")
        )
        paragraf_ekle(doc, "", sonra=4)

        # Notlar
        bolum_basligi(doc, "ÖĞRETMEN NOTLARI / SONRAKİ AY PLANI", renk=RENK)
        for _ in range(4):
            paragraf_ekle(doc, "___________________________________________________________________", boyut=10, sonra=6)

        paragraf_ekle(doc, "", sonra=6)
        imza_tablosu(doc, ["Sınıf Öğretmeni", "Okul Rehber Öğretmeni", "Okul Müdürü"], renk=RENK)

        dosya_adi  = f"Rehberlik_{sinif.replace('-','')}_{tarih.year}_{ay:02d}.docx"
        dosya_yolu = self.cikti_klasoru / dosya_adi
        doc.save(dosya_yolu)
        return dosya_yolu
