"""
Ana Bot - İki Klasör Sistemi
=============================
girdi/yeni_belgeler/ → Bu yılın planları, ders kitabı, rehberlik
girdi/eski_belgeler/ → Geçmiş yılların tutanakları, evrakları
Bot hangi dosyanın ne olduğunu otomatik anlar.
"""

import sys
import argparse
from pathlib import Path
from datetime import datetime, timedelta

sys.path.insert(0, str(Path(__file__).parent))

import konfig as K
from ders_programi      import DersProgramiOkuyucu
from yillik_plan        import YillikPlanOkuyucu
from plan_uretici       import GunlukPlanUretici
from tutanak_uretici    import TutanakUretici
from rehberlik_uretici  import RehberlikUretici
from belge_yoneticisi   import BelgeYoneticisi
from telegram_bot       import (yarin_bildirimi_gonder, tutanak_bildirimi_gonder,
                                rehberlik_bildirimi_gonder)
import web_guncelle

KONFIG = {
    "okul_adi":        K.OKUL_ADI,
    "ogretmen_adi":    K.OGRETMEN_ADI,
    "ders":            K.DERS,
    "rehberlik_sinif": K.REHBERLIK_SINIF,
}


def isgunu_bul(baslangic):
    t = baslangic
    while t.weekday() >= 5:
        t += timedelta(days=1)
    return t


def calistir(test=False, sadece="hepsi"):
    simdi = datetime.now()
    yarin = isgunu_bul(simdi + timedelta(days=1))

    print("\n" + "="*60)
    print(f"  Egitim Asistani — {simdi.strftime('%d.%m.%Y %H:%M')}")
    print("="*60)

    # Belge yöneticisi — iki klasörü tarar, ne olduğunu anlar
    belgeler = BelgeYoneticisi(Path(__file__).parent.parent / "girdi")
    belgeler.ozet()

    # ── GÜNLÜK PLAN ──
    if sadece in ("hepsi", "plan"):
        gunler = ["Pzt","Sal","Car","Per","Cum","Cmt","Paz"]
        print(f"\n[PLAN] Hedef: {yarin.strftime('%d.%m.%Y')} {gunler[yarin.weekday()]}")

        program  = DersProgramiOkuyucu(K.GIRDI["ders_programi"])
        ham_ders = program.gun_derslerini_al(yarin)

        if not ham_ders:
            print("   Yarin ders yok.")
        else:
            # Yıllık planı yeni belgelerden al
            yillik_metni = belgeler.yillik_plan_metni()
            plan_okuyucu = YillikPlanOkuyucu(
                Path(__file__).parent.parent / "girdi" / "yeni_belgeler"
            )

            # Aynı sınıfı tek plana birleştir — kota tasarrufu
            zengin = []
            goruldu = {}
            for d in ham_ders:
                sinif = d["sinif"]
                if sinif in goruldu:
                    continue
                goruldu[sinif] = True
                model = K.SINIFLAR.get(sinif, "normal")
                bilgi = plan_okuyucu.hafta_bilgisi_al(sinif, model, yarin)
                saat_sayisi = sum(1 for x in ham_ders if x["sinif"] == sinif)
                ilk_saat    = next(x["saat"] for x in ham_ders if x["sinif"] == sinif)
                zengin.append({
                    "sinif":      sinif,
                    "model":      model,
                    "saat":       ilk_saat,
                    "sure":       f"{saat_sayisi * 40} dk ({saat_sayisi} ders saati)",
                    "konu":       bilgi["konu"],
                    "unite":      bilgi.get("unite", ""),
                    "kazanim":    bilgi["kazanim"],
                    "simulasyon": bilgi.get("simulasyon", ""),
                })

            uretici = GunlukPlanUretici(KONFIG,
                Path(__file__).parent.parent / "girdi" / "yeni_belgeler",
                K.CIKTI["gunluk_planlar"])

            dosyalar = []
            for d in zengin:
                sinif    = d["sinif"]
                seviye   = sinif.split("-")[0]
                konu     = d.get("konu", "")

                # Ders kitabından ilgili bölümü çek
                kitap_icerigi = belgeler.ders_kitabi_bolumleri(seviye, konu)
                if kitap_icerigi:
                    print(f"   📖 Ders kitabı bölümü bulundu: {sinif}")

                # Eski planlardan örnek al
                eski_plan = belgeler.eski_plan_metni(seviye)

                # Groq'a hem kitap içeriğini hem eski planı ver
                d["kitap_icerigi"] = kitap_icerigi
                d["eski_plan"]     = eski_plan

                f = uretici.uret(yarin, d)
                dosyalar.append(f)
                print(f"   OK  {f.name}")

            if not test:
                yarin_bildirimi_gonder(yarin, zengin, dosyalar)
            else:
                print("   [TEST] Telegram atlandı.")
                for d in zengin:
                    print(f"      {d['sinif']} {d['saat']} — {d['konu']}")

    # ── TUTANAKLAR ──
    if sadece in ("hepsi", "tutanak") and (simdi.day == 1 or sadece == "tutanak"):
        print("\n[TUTANAK] Aylık kontrol...")

        # Eski belgelerden tutanak geçmişini al
        class EskiEvrakAdaptor:
            def __init__(self, bm):
                self.bm = bm
            def sablon_ogren(self, tur):
                metin = self.bm.onceki_tutanak_metni(tur)
                if not metin:
                    return {}
                from evrak_ogrenici import EvrakOgrenici
                from pathlib import Path
                import tempfile, os
                # Geçici dosya oluştur, EvrakOgrenici okusun
                return {"ozel_gundemler": [], "karar_kaliplari": []}

        from tutanak_uretici import TOPLANTI_META
        uretilen = []
        for tur in TOPLANTI_META:
            alt = K.CIKTI.get(tur, K.CIKTI["gunluk_planlar"].parent / "tutanaklar" / tur)
            alt.mkdir(parents=True, exist_ok=True)
            u = TutanakUretici(KONFIG, K.GIRDI["eski_belgeler"], alt.parent)
            u.cikti_klasoru = alt.parent
            sonuc = u.aylik_kontrol(simdi)
            uretilen.extend(sonuc)

        if uretilen and not test:
            tutanak_bildirimi_gonder(K.AYLAR_TR[simdi.month], uretilen)
        print(f"   OK  {len(uretilen)} tutanak.")

    # ── REHBERLİK ──
    if sadece in ("hepsi", "rehberlik") and (simdi.day == 1 or sadece == "rehberlik"):
        print("\n[REHBERLİK] Aylık kontrol...")
        r = RehberlikUretici(KONFIG, K.CIKTI["rehberlik"],
            Path(__file__).parent.parent / "girdi" / "yeni_belgeler")
        uretilen = r.aylik_kontrol(simdi)
        if uretilen and not test:
            rehberlik_bildirimi_gonder(K.AYLAR_TR[simdi.month], uretilen)
        print(f"   OK  {len(uretilen)} rehberlik raporu.")

    # ── WEB ──
    print("\n[WEB] Guncelleniyor...")
    web_guncelle.main()

    print("\n" + "="*60)
    print("  Tamamlandi!")
    print("="*60 + "\n")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--test",   action="store_true")
    ap.add_argument("--sadece", default="hepsi",
                    choices=["hepsi","plan","tutanak","rehberlik"])
    args = ap.parse_args()
    calistir(test=args.test, sadece=args.sadece)
