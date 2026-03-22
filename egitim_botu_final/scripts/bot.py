"""
Ana Bot
=======
Her akşam GitHub Actions tarafından çalıştırılır.
  1. Ders programından yarınki dersleri okur
  2. Yıllık plandan konu + kazanım çeker (Maarif / Normal ayrımı)
  3. Her ders için Word planı üretir
  4. Telegram'a mesaj + dosya gönderir
  5. Ayın 1'inde: tutanak + rehberlik raporları üretir
  6. Web arayüzünü (docs/dosyalar.json) günceller
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
from evrak_ogrenici     import EvrakOgrenici
from telegram_bot       import (yarin_bildirimi_gonder, tutanak_bildirimi_gonder,
                                rehberlik_bildirimi_gonder)
import web_guncelle

KONFIG = {
    "okul_adi":        K.OKUL_ADI,
    "ogretmen_adi":    K.OGRETMEN_ADI,
    "ders":            K.DERS,
    "rehberlik_sinif": K.REHBERLIK_SINIF,
}


def isgunu_bul(baslangic: datetime) -> datetime:
    """Hafta sonunu atlayarak sonraki iş gününü döndürür."""
    t = baslangic
    while t.weekday() >= 5:
        t += timedelta(days=1)
    return t


def calistir(test: bool = False, sadece: str = "hepsi"):
    simdi = datetime.now()
    yarin = isgunu_bul(simdi + timedelta(days=1))

    print("\n" + "="*60)
    print(f"  🤖 Eğitim Asistanı — {simdi.strftime('%d.%m.%Y %H:%M')}")
    print("="*60)

    # ── Ortak nesneler ──
    ogrenici = EvrakOgrenici(K.GIRDI["onceki_evraklar"])
    plan_okuyucu = YillikPlanOkuyucu(K.GIRDI["yillik_plan"])

    # ══════════════════════════════════════════════
    # 1. GÜNLÜK PLAN
    # ══════════════════════════════════════════════
    if sadece in ("hepsi", "plan"):
        print(f"\n[PLAN] Hedef gün: {yarin.strftime('%d.%m.%Y %A')}")
        program  = DersProgramiOkuyucu(K.GIRDI["ders_programi"])
        ham_ders = program.gun_derslerini_al(yarin)

        if not ham_ders:
            print("   ℹ  Yarın ders yok.")
        else:
            # Yıllık plandan konu/kazanım ekle
            zengin_dersler = []
            for d in ham_ders:
                sinif = d["sinif"]
                model = K.SINIFLAR.get(sinif, "normal")
                bilgi = plan_okuyucu.hafta_bilgisi_al(sinif, model, yarin)
                zengin_dersler.append({
                    "sinif":     sinif,
                    "model":     model,
                    "saat":      d["saat"],
                    "konu":      bilgi["konu"],
                    "unite":     bilgi.get("unite",""),
                    "kazanim":   bilgi["kazanim"],
                    "simulasyon": bilgi.get("simulasyon",""),
                })

            uretici = GunlukPlanUretici(KONFIG, K.GIRDI["yillik_plan"], K.CIKTI["gunluk_planlar"])
            uretilen_planlar = []
            for d in zengin_dersler:
                dosya = uretici.uret(yarin, d)
                uretilen_planlar.append(dosya)
                print(f"   ✓  {dosya.name}")

            if not test:
                yarin_bildirimi_gonder(yarin, zengin_dersler, uretilen_planlar)
            else:
                print("   [TEST] Telegram atlandı.")
                for d in zengin_dersler:
                    print(f"      {d['sinif']} {d['saat']} — {d['konu']} ({d['model']})")

    # ══════════════════════════════════════════════
    # 2. TUTANAKLAR (Ayın 1'i kontrolü)
    # ══════════════════════════════════════════════
    if sadece in ("hepsi", "tutanak") and (simdi.day == 1 or sadece == "tutanak"):
        print("\n[TUTANAK] Aylık kontrol...")
        t_uretici = TutanakUretici(
            konfig          = KONFIG,
            onceki_evraklar = K.GIRDI["onceki_evraklar"],
            cikti_klasoru   = K.CIKTI["gunluk_planlar"].parent / "tutanaklar",
            evrak_ogrenici  = ogrenici,
        )
        # Her tür için ayrı klasör
        from tutanak_uretici import TOPLANTI_META
        uretilen_tutanaklar = []
        for tur in TOPLANTI_META:
            alt = K.CIKTI[tur] if tur in K.CIKTI else K.CIKTI["gunluk_planlar"].parent / "tutanaklar" / tur
            alt.mkdir(parents=True, exist_ok=True)
            t_uretici.cikti_klasoru = alt.parent
            sonuclar = t_uretici.aylik_kontrol(simdi)
            uretilen_tutanaklar.extend(sonuclar)

        if uretilen_tutanaklar and not test:
            from konfig import AYLAR_TR
            tutanak_bildirimi_gonder(AYLAR_TR[simdi.month], uretilen_tutanaklar)
        print(f"   ✓  {len(uretilen_tutanaklar)} tutanak üretildi.")

    # ══════════════════════════════════════════════
    # 3. REHBERLİK (Ayın 1'i kontrolü)
    # ══════════════════════════════════════════════
    if sadece in ("hepsi", "rehberlik") and (simdi.day == 1 or sadece == "rehberlik"):
        print("\n[REHBERLİK] Aylık kontrol...")
        r_uretici = RehberlikUretici(
            konfig          = KONFIG,
            cikti_klasoru   = K.CIKTI["rehberlik"],
            rehberlik_plani = K.GIRDI["rehberlik_plani"],
        )
        uretilen_rehberlik = r_uretici.aylik_kontrol(simdi)
        if uretilen_rehberlik and not test:
            from konfig import AYLAR_TR
            rehberlik_bildirimi_gonder(AYLAR_TR[simdi.month], uretilen_rehberlik)
        print(f"   ✓  {len(uretilen_rehberlik)} rehberlik raporu üretildi.")

    # ══════════════════════════════════════════════
    # 4. WEB ARAYÜZÜ GÜNCELLE
    # ══════════════════════════════════════════════
    print("\n[WEB] Arayüz güncelleniyor...")
    web_guncelle.main()

    print("\n" + "="*60)
    print("  ✅ Tamamlandı!")
    print("="*60 + "\n")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--test",   action="store_true",  help="Telegram göndermez")
    ap.add_argument("--sadece", default="hepsi",
                    choices=["hepsi","plan","tutanak","rehberlik"],
                    help="Sadece belirli görevi çalıştır")
    args = ap.parse_args()
    calistir(test=args.test, sadece=args.sadece)
