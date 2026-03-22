"""
Günlük Plan Üretici
===================
Gemini AI varsa kazanıma özel etkinlik yazar,
yoksa sabit şablonla devam eder.
Maarif / Normal müfredat ayrımı yapılır.
"""

from pathlib import Path
from datetime import datetime
from word_utils import (yeni_belge, baslik_ekle, paragraf_ekle,
                         bolum_basligi, tablo_olustur, imza_tablosu)
from docx.enum.text import WD_ALIGN_PARAGRAPH

GUNLER_TR = {0:"Pazartesi",1:"Salı",2:"Çarşamba",3:"Perşembe",4:"Cuma"}

# Sabit ders akışı (Gemini yokken kullanılır)
DERS_AKISI_SABLON = [
    ("0–5 dk",   "Giriş / Yoklama",     "Yoklama. Önceki konunun kısa tekrarı. Günün kazanımları paylaşılır."),
    ("5–15 dk",  "Motivasyon",           "Konuyla ilgili video, simülasyon veya gerçek yaşam örneği."),
    ("15–35 dk", "Kavram Sunumu",        "Konu tahta/sunu ile anlatılır. Simülasyon sınıfça incelenir."),
    ("35–55 dk", "Etkinlik / Deney",     "Grup etkinliği veya deney. Öğrenciler gözlem formunu doldurur."),
    ("55–65 dk", "Tartışma / Pekiştirme","Bulgular paylaşılır. Kavram haritası oluşturulur."),
    ("65–75 dk", "Ölçme / Değerlendirme","4–5 soruluk çıkış kağıdı uygulanır."),
    ("75–80 dk", "Kapanış / Ödev",       "Kazanımlar özetlenir. Ödev duyurulur."),
]

MAARIF_EK = [
    ("Değerler Eğitimi", "Bu derste ele alınan değer: ___________"),
    ("Maarif Vizyonu",   "Öğrencinin gelişimine katkı: ___________"),
    ("Uygulama Notu",    "Maarif müfredatı gerekliliklerine uygun ek etkinlik planlanmıştır."),
]


class GunlukPlanUretici:
    def __init__(self, konfig: dict, yillik_plan_klasoru: Path, cikti_klasoru: Path):
        self.konfig = konfig
        self.yillik_plan_klasoru = yillik_plan_klasoru
        self.cikti_klasoru = cikti_klasoru
        self.cikti_klasoru.mkdir(parents=True, exist_ok=True)

    def _gemini_den_al(self, sinif, konu, kazanim, model) -> dict:
        """Gemini'den ders akışı ve etkinlikleri alır. Başarısız olursa {} döner."""
        try:
            from gemini_ai import gunluk_plan_olustur
            return gunluk_plan_olustur(sinif, self.konfig["ders"], konu, kazanim, model) or {}
        except Exception:
            return {}

    def uret(self, tarih: datetime, ders_bilgisi: dict) -> Path:
        sinif     = ders_bilgisi["sinif"]
        model     = ders_bilgisi.get("model", "normal")
        konu      = ders_bilgisi.get("konu", "Genel Tekrar")
        unite     = ders_bilgisi.get("unite", "—")
        kazanim   = ders_bilgisi.get("kazanim", "Yıllık plandan alınacak")
        saat      = ders_bilgisi.get("saat", "08:00")
        sim_link  = ders_bilgisi.get("simulasyon", "")
        gun_adi   = GUNLER_TR.get(tarih.weekday(), "")
        yil_donem = f"{tarih.year}-{tarih.year+1} {'1.' if tarih.month >= 9 else '2.'} Dönem"

        # ── Gemini'den akıllı içerik al ──
        ai = self._gemini_den_al(sinif, konu, kazanim, model)
        if ai:
            ders_akisi = [(d["sure"], d["asama"], d["etkinlik"])
                          for d in ai.get("ders_akisi", [])] or DERS_AKISI_SABLON
            sim_link   = ai.get("simulasyon", sim_link) or sim_link
            materyal   = ai.get("materyal", "Ders kitabı, çalışma kağıdı")
            odev       = ai.get("odev", "Kitap ilgili bölüm soruları")
            deg_sorular = ai.get("degerlendirme_sorulari", [])
            ai_notu    = "✓ Gemini AI"
        else:
            ders_akisi  = DERS_AKISI_SABLON
            materyal    = "Ders kitabı, çalışma kağıdı"
            odev        = "Kitap ilgili bölüm soruları"
            deg_sorular = []
            ai_notu     = "Şablon"

        # ── Renk teması ──
        if model == "maarif":
            ana_renk, ac_renk, model_etiket = "1A4A2A", "E8F4ED", "MAALİF MODELİ"
        else:
            ana_renk, ac_renk, model_etiket = "1A3A5C", "E8F0F8", "NORMAL MÜFREDAT"

        doc = yeni_belge()

        # ── Başlık ──
        paragraf_ekle(doc, "T.C.", boyut=10, hizalama=WD_ALIGN_PARAGRAPH.CENTER)
        paragraf_ekle(doc, "MİLLÎ EĞİTİM BAKANLIĞI", boyut=10, hizalama=WD_ALIGN_PARAGRAPH.CENTER)
        paragraf_ekle(doc, self.konfig["okul_adi"].upper(), boyut=11, kalin=True, hizalama=WD_ALIGN_PARAGRAPH.CENTER)
        baslik_ekle(doc, "GÜNLÜK DERS PLANI", boyut=15, renk=ana_renk)
        paragraf_ekle(doc, f"[ {model_etiket} ]  —  {ai_notu}", boyut=9,
                      renk=ana_renk, hizalama=WD_ALIGN_PARAGRAPH.CENTER, sonra=6)

        # ── Genel Bilgiler ──
        tablo_olustur(doc,
            basliklar=["Alan", "Bilgi", "Alan", "Bilgi"],
            satirlar=[
                ["Okul",     self.konfig["okul_adi"],      "Tarih",      tarih.strftime("%d.%m.%Y") + f" {gun_adi}"],
                ["Öğretmen", self.konfig["ogretmen_adi"],  "Sınıf",      sinif],
                ["Ders",     self.konfig["ders"],           "Saat",       f"{saat}  (80 dk)"],
                ["Ünite",    unite,                         "Konu",       konu],
                ["Dönem",    yil_donem,                     "Model",      model_etiket],
            ],
            baslik_rengi=ana_renk, satir_renkleri=(ac_renk, "FFFFFF")
        )
        paragraf_ekle(doc, "", sonra=4)

        # ── Kazanımlar ──
        bolum_basligi(doc, "KAZANIMLAR", renk=ana_renk)
        tablo_olustur(doc,
            basliklar=["Kazanım Kodu", "Kazanım İfadesi"],
            satirlar=[[kazanim.split("—")[0].strip() if "—" in kazanim else "—", kazanim]],
            baslik_rengi=ana_renk, satir_renkleri=(ac_renk, "FFFFFF")
        )
        paragraf_ekle(doc, "", sonra=4)

        # ── Araç-Gereç ──
        bolum_basligi(doc, "ARAÇ-GEREÇ VE KAYNAKLAR", renk=ana_renk)
        tablo_olustur(doc,
            basliklar=["Kaynak", "Açıklama"],
            satirlar=[
                ["Ders Kitabı",   f"MEB {sinif[0]}. Sınıf {self.konfig['ders']} Ders Kitabı"],
                ["Simülasyon",    sim_link or "phet.colorado.edu/tr"],
                ["EBA",           "eba.gov.tr — konuya ait video ve etkinlik"],
                ["Materyal",      materyal],
            ],
            baslik_rengi=ana_renk, satir_renkleri=(ac_renk, "FFFFFF")
        )
        paragraf_ekle(doc, "", sonra=4)

        # ── Ders Akışı (AI veya şablon) ──
        bolum_basligi(doc, "DERS AKIŞI", renk=ana_renk)
        tablo_olustur(doc,
            basliklar=["Süre", "Aşama", "Etkinlik / Açıklama"],
            satirlar=[[s, a, e] for s, a, e in ders_akisi],
            baslik_rengi=ana_renk, satir_renkleri=(ac_renk, "FFFFFF")
        )
        paragraf_ekle(doc, "", sonra=4)

        # ── Maarif ek bölüm ──
        if model == "maarif":
            bolum_basligi(doc, "MAALİF MODELİ — EK GEREKLİLİKLER", renk=ana_renk)
            tablo_olustur(doc,
                basliklar=["Başlık", "İçerik"],
                satirlar=[[b, i] for b, i in MAARIF_EK],
                baslik_rengi=ana_renk, satir_renkleri=(ac_renk, "FFFFFF")
            )
            paragraf_ekle(doc, "", sonra=4)

        # ── Ölçme Değerlendirme ──
        bolum_basligi(doc, "ÖLÇME VE DEĞERLENDİRME", renk=ana_renk)
        sorular = deg_sorular or ["Çıkış kağıdı soruları eklenecek."]
        tablo_olustur(doc,
            basliklar=["Yöntem", "Açıklama"],
            satirlar=[
                ["Çıkış Kağıdı",   " / ".join(sorular[:3]) if sorular else "—"],
                ["Gözlem Formu",   "Deney/etkinlik sırasında doldurulan tablo"],
                ["Sözlü Katılım",  "Tartışma aşamasında değerlendirme"],
                ["Ödev",           odev],
            ],
            baslik_rengi=ana_renk, satir_renkleri=(ac_renk, "FFFFFF")
        )
        paragraf_ekle(doc, "", sonra=6)

        # ── İmza ──
        imza_tablosu(doc, ["Hazırlayan Öğretmen", "Okul Müdürü Onayı"], renk=ana_renk)

        # ── Kaydet ──
        sinif_kisa = sinif.replace("-", "").replace("/", "")
        konu_kisa  = konu[:20].replace(" ", "_")
        dosya_adi  = f"GunlukPlan_{tarih.strftime('%Y%m%d')}_{sinif_kisa}_{konu_kisa}.docx"
        dosya_yolu = self.cikti_klasoru / dosya_adi
        doc.save(dosya_yolu)
        return dosya_yolu
