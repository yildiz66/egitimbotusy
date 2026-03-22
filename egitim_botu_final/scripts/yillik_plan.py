"""
Yıllık Plan Okuyucu
===================
Word / Excel / PDF / Görsel → hafta bazlı konu + kazanım.
Tüm okuma işini evrensel_okuyucu yapar.
"""

import re
from pathlib import Path
from datetime import datetime

PHET_ESLESTIRME = {
    "Newton":"https://phet.colorado.edu/tr/simulations/forces-and-motion-basics",
    "Kuvvet":"https://phet.colorado.edu/tr/simulations/forces-and-motion-basics",
    "Elektrik":"https://phet.colorado.edu/tr/simulations/circuit-construction-kit-dc",
    "Devre":"https://phet.colorado.edu/tr/simulations/circuit-construction-kit-dc",
    "Işık":"https://phet.colorado.edu/tr/simulations/bending-light",
    "Ses":"https://phet.colorado.edu/tr/simulations/wave-on-a-string",
    "Basınç":"https://phet.colorado.edu/tr/simulations/fluid-pressure-and-flow",
    "Kimya":"https://phet.colorado.edu/tr/simulations/reactants-products-and-leftovers",
    "Atom":"https://phet.colorado.edu/tr/simulations/build-an-atom",
    "DNA":"https://learn.genetics.utah.edu/content/basics/",
    "Hücre":"https://www.cellsalive.com",
    "Mıknatıs":"https://phet.colorado.edu/tr/simulations/magnets-and-electromagnets",
    "Güneş":"https://phet.colorado.edu/tr/simulations/gravity-and-orbits",
    "Isı":"https://phet.colorado.edu/tr/simulations/states-of-matter",
    "Madde":"https://phet.colorado.edu/tr/simulations/states-of-matter",
}

VARSAYILAN_PLAN = {
    "normal": {
        "6": [
            {"hafta":range(1,4),   "unite":"1. Ünite: Vücudumuzdaki Sistemler","konular":["Sindirim Sistemi","Dolaşım Sistemi","Solunum Sistemi"],"kazanim":"F.6.1.1.1 — Sindirim sisteminin yapısını açıklar."},
            {"hafta":range(4,8),   "unite":"2. Ünite: Kuvvet ve Hareket","konular":["Sürtünme Kuvveti","Kaldırma Kuvveti","Basit Makineler"],"kazanim":"F.6.2.1.1 — Sürtünme kuvvetinin etkilerini açıklar."},
            {"hafta":range(8,12),  "unite":"3. Ünite: Madde ve Isı","konular":["Isı ve Sıcaklık","Genleşme","Hal Değişimi"],"kazanim":"F.6.3.1.1 — Isı ile sıcaklık farkını kavrar."},
            {"hafta":range(12,16), "unite":"4. Ünite: Işık ve Ses","konular":["Işığın Yansıması","Işığın Kırılması","Sesin Özellikleri"],"kazanim":"F.6.4.1.1 — Işığın yansıma yasalarını açıklar."},
            {"hafta":range(16,20), "unite":"5. Ünite: Elektrik","konular":["Statik Elektrik","Elektrik Devreleri","Manyetizma"],"kazanim":"F.6.5.1.1 — Statik elektriği keşfeder."},
            {"hafta":range(20,36), "unite":"6. Ünite: Canlılar Dünyası","konular":["Hücre","Canlıların Sınıflandırılması","Ekosistem"],"kazanim":"F.6.6.1.1 — Hücrenin yapısını açıklar."},
        ],
        "7": [
            {"hafta":range(1,5),   "unite":"1. Ünite: Hücre Bölünmeleri","konular":["Mitoz","Mayoz","Eşeysiz Üreme"],"kazanim":"F.7.1.1.1 — Mitoz bölünmenin evrelerini açıklar."},
            {"hafta":range(5,9),   "unite":"2. Ünite: Kuvvet ve Enerji","konular":["Newton Yasaları","İş-Enerji","Sürtünme"],"kazanim":"F.7.2.1.1 — Newton'un hareket yasalarını açıklar."},
            {"hafta":range(9,13),  "unite":"3. Ünite: Saf Madde ve Karışım","konular":["Element-Bileşik","Karışımlar","Çözünürlük"],"kazanim":"F.7.3.1.1 — Element ve bileşik arasındaki farkı açıklar."},
            {"hafta":range(13,17), "unite":"4. Ünite: Işığın Etkileşimi","konular":["Işığın Soğurulması","Işık ve Renk","Görme"],"kazanim":"F.7.4.1.1 — Işığın madde ile etkileşimini açıklar."},
            {"hafta":range(17,22), "unite":"5. Ünite: Elektrik Devreleri","konular":["Ohm Yasası","Seri-Paralel Devre","Elektrik Enerjisi"],"kazanim":"F.7.5.1.1 — Ohm yasasını açıklar ve uygular."},
            {"hafta":range(22,36), "unite":"6. Ünite: Güneş Sistemi","konular":["Güneş Sistemi","Mevsimler","Ay'ın Hareketleri"],"kazanim":"F.7.6.1.1 — Gezegenlerin özelliklerini karşılaştırır."},
        ],
        "8": [
            {"hafta":range(1,5),   "unite":"1. Ünite: Mevsimler ve İklim","konular":["Dünya'nın Hareketleri","İklim Kuşakları","Küresel Isınma"],"kazanim":"F.8.1.1.1 — Mevsimlerin oluşumunu açıklar."},
            {"hafta":range(5,9),   "unite":"2. Ünite: DNA ve Genetik","konular":["DNA Yapısı","Genetik Şifre","Mutasyon"],"kazanim":"F.8.2.1.1 — DNA'nın yapısını açıklar."},
            {"hafta":range(9,13),  "unite":"3. Ünite: Periyodik Sistem","konular":["Atom Yapısı","Periyodik Tablo","Kimyasal Bağlar"],"kazanim":"F.8.3.1.1 — Periyodik sistemin düzenini açıklar."},
            {"hafta":range(13,17), "unite":"4. Ünite: Basınç","konular":["Katılarda Basınç","Sıvılarda Basınç","Gazlarda Basınç"],"kazanim":"F.8.4.1.1 — Basınç kavramını açıklar ve hesaplar."},
            {"hafta":range(17,22), "unite":"5. Ünite: Ses","konular":["Ses Dalgaları","Ses Şiddeti","Yankı"],"kazanim":"F.8.5.1.1 — Ses dalgalarının özelliklerini açıklar."},
            {"hafta":range(22,36), "unite":"6. Ünite: Manyetizma","konular":["Mıknatıslar","Elektromanyetizma","Transformatör"],"kazanim":"F.8.6.1.1 — Manyetik alanı açıklar."},
        ],
    },
    "maarif": {
        "6": [{"hafta":range(1,36),"unite":"Maarif Modeli","konular":["Lütfen Maarif yıllık planını yükleyin"],"kazanim":"Yıllık plandan alınacak"}],
        "7": [{"hafta":range(1,36),"unite":"Maarif Modeli","konular":["Lütfen Maarif yıllık planını yükleyin"],"kazanim":"Yıllık plandan alınacak"}],
        "8": [{"hafta":range(1,36),"unite":"Maarif Modeli","konular":["Lütfen Maarif yıllık planını yükleyin"],"kazanim":"Yıllık plandan alınacak"}],
    }
}


def simulasyon_bul(konu: str) -> str:
    for anahtar, link in PHET_ESLESTIRME.items():
        if anahtar.lower() in konu.lower():
            return link
    return "https://phet.colorado.edu/tr/simulations"


class YillikPlanOkuyucu:
    def __init__(self, klasor: Path):
        self.klasor = klasor
        self._cache = {}

    def hafta_bilgisi_al(self, sinif: str, model: str, tarih: datetime) -> dict:
        """
        Word / Excel / PDF / Görsel — hepsini evrensel_okuyucu ile okur.
        Dosya yoksa yerleşik plana düşer.
        """
        from evrensel_okuyucu import yillik_plan_oku
        seviye = sinif.split("-")[0]
        hafta_no = tarih.isocalendar()[1]
        egitim_haftasi = max(1, (hafta_no - 36) % 52 + 1) if hafta_no < 36 else hafta_no - 35

        cache_key = f"{model}_{seviye}"
        if cache_key not in self._cache:
            self._cache[cache_key] = yillik_plan_oku(self.klasor, model)

        plan = self._cache[cache_key]
        if plan and egitim_haftasi in plan:
            bilgi = plan[egitim_haftasi]
            konu = bilgi.get("konu", "Genel Tekrar")
            return {
                "unite":     bilgi.get("unite", "—"),
                "konu":      konu,
                "kazanim":   bilgi.get("kazanim", "Yıllık plandan alındı"),
                "simulasyon": simulasyon_bul(konu),
                "model":     model,
                "hafta":     egitim_haftasi,
            }

        # Fallback: yerleşik plan
        plan_listesi = VARSAYILAN_PLAN.get(model, VARSAYILAN_PLAN["normal"]).get(seviye, [])
        for giris in plan_listesi:
            if egitim_haftasi in giris["hafta"]:
                konu_idx = (egitim_haftasi - giris["hafta"].start) % len(giris["konular"])
                konu = giris["konular"][konu_idx]
                return {
                    "unite":     giris["unite"],
                    "konu":      konu,
                    "kazanim":   giris["kazanim"],
                    "simulasyon": simulasyon_bul(konu),
                    "model":     model,
                    "hafta":     egitim_haftasi,
                }
        return {
            "unite":"—","konu":"Genel Tekrar",
            "kazanim":"Kazanım yıllık plandan alınacak",
            "simulasyon":"","model":model,"hafta":egitim_haftasi,
        }
