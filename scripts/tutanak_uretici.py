"""
Tutanak Üretici
===============
Gemini AI varsa gündem + kararları doldurur,
yoksa önceki evraklardan öğrendikleriyle doldurur.
"""

from pathlib import Path
from datetime import datetime
from word_utils import (yeni_belge, baslik_ekle, paragraf_ekle,
                         bolum_basligi, tablo_olustur, imza_tablosu)
from docx.enum.text import WD_ALIGN_PARAGRAPH

AYLAR_TR = {1:"Ocak",2:"Şubat",3:"Mart",4:"Nisan",5:"Mayıs",6:"Haziran",
            7:"Temmuz",8:"Ağustos",9:"Eylül",10:"Ekim",11:"Kasım",12:"Aralık"}
GUNLER_TR = {0:"Pazartesi",1:"Salı",2:"Çarşamba",3:"Perşembe",4:"Cuma",5:"Cumartesi",6:"Pazar"}

TOPLANTI_META = {
    "sok": {
        "tam_ad":"Şube Öğretmenler Kurulu (ŞÖK) Toplantısı",
        "kisaltma":"ŞÖK", "renk":"1A3A5C", "ac_renk":"E8F0F8",
        "aylar":[9,10,11,12,1,2,3,4,5],
        "gundem":[
            "Öğrencilerin akademik durumlarının değerlendirilmesi",
            "Devam-devamsızlık durumlarının gözden geçirilmesi",
            "Davranış ve disiplin konularının görüşülmesi",
            "Başarısız öğrenciler için alınacak önlemler",
            "Dilek ve öneriler",
        ],
    },
    "zumre": {
        "tam_ad":"Zümre Öğretmenler Kurulu Toplantısı",
        "kisaltma":"Zümre", "renk":"1A4A2A", "ac_renk":"E8F4ED",
        "aylar":[9, 1],
        "gundem":[
            "Bir önceki toplantı kararlarının değerlendirilmesi",
            "Yıllık planların incelenmesi ve güncellenmesi",
            "Ortak sınav ve ölçme-değerlendirme planlaması",
            "Öğretim yöntem ve tekniklerinin görüşülmesi",
            "Dilek ve öneriler",
        ],
    },
    "veli": {
        "tam_ad":"Veli Toplantısı",
        "kisaltma":"Veli", "renk":"4A1A3A", "ac_renk":"F4E8F0",
        "aylar":[10, 2, 4],
        "gundem":[
            "Dönem akademik başarı durumunun aktarılması",
            "Devam-devamsızlık bilgilendirmesi",
            "Ödev ve ders çalışma alışkanlıkları",
            "Okul-aile iş birliğinin güçlendirilmesi",
            "Veli görüş ve önerileri",
        ],
    },
}


class TutanakUretici:
    def __init__(self, konfig, onceki_evraklar, cikti_klasoru, evrak_ogrenici=None):
        self.konfig          = konfig
        self.onceki_evraklar = onceki_evraklar
        self.cikti_klasoru   = cikti_klasoru
        self.ogrenici        = evrak_ogrenici
        self.cikti_klasoru.mkdir(parents=True, exist_ok=True)

    def _gundemleri_al(self, tur: str, ay_adi: str, yil: int,
                        onceki_metin: str) -> list:
        """Gemini → öğrenilmiş → varsayılan sıralamasıyla gündem alır."""
        # 1. Gemini
        try:
            from gemini_ai import tutanak_doldur
            ai = tutanak_doldur(tur, ay_adi, yil, onceki_metin)
            if ai and "gundem_maddeleri" in ai:
                print(f"   🤖 Gemini gündem doldurdu: {tur}")
                return [(m["madde"], m["karar"]) for m in ai["gundem_maddeleri"]]
        except Exception:
            pass

        # 2. Önceki evraklardan öğrenilmiş
        gundemler = []
        if self.ogrenici:
            sablon = self.ogrenici.sablon_ogren(tur)
            gundemler = [(m, "") for m in sablon.get("ozel_gundemler", [])]

        # 3. Varsayılan
        if not gundemler:
            gundemler = [(m, "") for m in TOPLANTI_META[tur]["gundem"]]

        return gundemler[:6]

    def aylik_kontrol(self, tarih: datetime) -> list:
        ay, yil = tarih.month, tarih.year
        uretilen = []
        for tur, meta in TOPLANTI_META.items():
            if ay not in meta["aylar"]:
                continue
            alt = self.cikti_klasoru / tur
            alt.mkdir(exist_ok=True)
            dosya_adi = f"Tutanak_{meta['kisaltma']}_{yil}_{ay:02d}.docx"
            dosya_yolu = alt / dosya_adi
            if dosya_yolu.exists():
                print(f"   ℹ  {dosya_adi} zaten var.")
                continue
            self._uret(tarih, tur, dosya_yolu)
            uretilen.append(dosya_yolu)
            print(f"   ✓  {dosya_adi}")
        return uretilen

    def _uret(self, tarih: datetime, tur: str, dosya_yolu: Path):
        meta     = TOPLANTI_META[tur]
        ay_adi   = AYLAR_TR[tarih.month]
        gun_adi  = GUNLER_TR[tarih.weekday()]
        yil_donem = f"{tarih.year}-{tarih.year+1} {'1.' if tarih.month >= 9 else '2.'} Dönem"

        # Önceki tutanaktan metin çek
        onceki_metin = ""
        if self.ogrenici:
            try:
                from evrensel_okuyucu import klasor_tara, dosya_oku
                klasor = self.onceki_evraklar / tur
                if klasor.exists():
                    dosyalar = klasor_tara(klasor)
                    if dosyalar:
                        onceki_metin = dosya_oku(dosyalar[-1])
            except Exception:
                pass

        gundemler = self._gundemleri_al(tur, ay_adi, tarih.year, onceki_metin)

        doc = yeni_belge()

        paragraf_ekle(doc, "T.C.", boyut=10, hizalama=WD_ALIGN_PARAGRAPH.CENTER)
        paragraf_ekle(doc, "MİLLÎ EĞİTİM BAKANLIĞI", boyut=10, hizalama=WD_ALIGN_PARAGRAPH.CENTER)
        paragraf_ekle(doc, self.konfig["okul_adi"].upper(), boyut=11, kalin=True, hizalama=WD_ALIGN_PARAGRAPH.CENTER)
        baslik_ekle(doc, meta["tam_ad"].upper(), boyut=13, renk=meta["renk"])

        tablo_olustur(doc,
            basliklar=["Alan","Bilgi","Alan","Bilgi"],
            satirlar=[
                ["Toplantı",  f"{ay_adi} {tarih.year} — {meta['kisaltma']}", "Tarih",    tarih.strftime("%d.%m.%Y") + f" {gun_adi}"],
                ["Yer",       "Öğretmenler Odası",                            "Saat",     "14:00"],
                ["Okul",      self.konfig["okul_adi"],                        "Öğretmen", self.konfig["ogretmen_adi"]],
                ["Dönem",     yil_donem,                                      "Tür",      meta["kisaltma"]],
            ],
            baslik_rengi=meta["renk"], satir_renkleri=(meta["ac_renk"],"FFFFFF")
        )
        paragraf_ekle(doc, "", sonra=4)

        # Gündem (AI veya öğrenilmiş)
        bolum_basligi(doc, "GÜNDEM MADDELERİ", renk=meta["renk"])
        tablo_olustur(doc,
            basliklar=["No","Gündem Maddesi","Karar / Açıklama"],
            satirlar=[[str(i+1), m, k] for i,(m,k) in enumerate(gundemler)],
            baslik_rengi=meta["renk"], satir_renkleri=(meta["ac_renk"],"FFFFFF")
        )
        paragraf_ekle(doc, "", sonra=4)

        bolum_basligi(doc, "ALINAN KARARLAR", renk=meta["renk"])
        tablo_olustur(doc,
            basliklar=["Karar No","Karar İçeriği","Sorumlu / Süre"],
            satirlar=[[str(i+1),"",""] for i in range(4)],
            baslik_rengi=meta["renk"], satir_renkleri=(meta["ac_renk"],"FFFFFF")
        )
        paragraf_ekle(doc, "", sonra=4)

        bolum_basligi(doc, "KATILIMCI VE İMZA LİSTESİ", renk=meta["renk"])
        tablo_olustur(doc,
            basliklar=["Adı Soyadı","Branş / Görev","Okul","İmza"],
            satirlar=[["","",self.konfig["okul_adi"],""] for _ in range(6)],
            baslik_rengi=meta["renk"], satir_renkleri=(meta["ac_renk"],"FFFFFF")
        )
        paragraf_ekle(doc, "", sonra=6)

        imza_tablosu(doc, ["Tutanağı Yazan","Toplantı Başkanı","Okul Müdürü"], renk=meta["renk"])
        doc.save(dosya_yolu)
