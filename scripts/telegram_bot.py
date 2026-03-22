"""
Telegram Bildirimi
==================
Yarınki dersleri mesaj olarak atar,
Word dosyalarını doğrudan Telegram'a gönderir.
"""

import os
import requests
from pathlib import Path
from datetime import datetime

GUNLER_TR = {0:"Pazartesi",1:"Salı",2:"Çarşamba",3:"Perşembe",4:"Cuma",5:"Cumartesi",6:"Pazar"}

def _token():   return os.getenv("TELEGRAM_BOT_TOKEN","")
def _chat():    return os.getenv("TELEGRAM_CHAT_ID","")


def mesaj_gonder(metin: str) -> bool:
    if not _token() or not _chat():
        print("   ⚠  Telegram token/chat eksik — mesaj atlanıyor.")
        return False
    r = requests.post(
        f"https://api.telegram.org/bot{_token()}/sendMessage",
        data={"chat_id": _chat(), "text": metin, "parse_mode": "HTML"},
        timeout=15,
    )
    ok = r.status_code == 200
    print(f"   {'✓' if ok else '✗'}  Telegram mesaj: {r.status_code}")
    return ok


def dosya_gonder(dosya: Path, aciklama: str = "") -> bool:
    if not _token() or not _chat():
        return False
    if not dosya.exists():
        print(f"   ✗  Dosya yok: {dosya}")
        return False
    with open(dosya, "rb") as f:
        r = requests.post(
            f"https://api.telegram.org/bot{_token()}/sendDocument",
            data={"chat_id": _chat(), "caption": aciklama},
            files={"document": (dosya.name, f)},
            timeout=30,
        )
    ok = r.status_code == 200
    print(f"   {'✓' if ok else '✗'}  Dosya gönderildi: {dosya.name}")
    return ok


def yarin_bildirimi_gonder(yarin: datetime, dersler: list, dosyalar: list):
    gun = GUNLER_TR[yarin.weekday()]

    satirlar = [
        f"📚 <b>Yarınki Ders Planı — {gun} {yarin.strftime('%d.%m.%Y')}</b>",
        "──────────────────────────────",
    ]
    for i, d in enumerate(dersler, 1):
        model_ikon = "🟩" if d.get("model") == "maarif" else "🔵"
        satirlar += [
            f"\n{model_ikon} <b>Ders {i} — {d['sinif']}</b>",
            f"🕐 Saat     : {d['saat']}",
            f"📖 Konu     : {d.get('konu','—')}",
            f"🎯 Kazanım  : {d.get('kazanim','—')}",
        ]
        if d.get("simulasyon"):
            satirlar.append(f"🖥  Simülasyon: {d['simulasyon']}")
        if d.get("model") == "maarif":
            satirlar.append("📌 Model    : Maarif Modeli")
        satirlar.append("──────────────────────────────")

    satirlar.append(f"\n📎 {len(dosyalar)} Word plan dosyası gönderiliyor...")
    mesaj_gonder("\n".join(satirlar))

    for dosya in dosyalar:
        sinif_kisa = dosya.stem.split("_")[2] if len(dosya.stem.split("_")) > 2 else ""
        dosya_gonder(dosya, f"📄 Günlük Plan — {sinif_kisa}")


def tutanak_bildirimi_gonder(ay_adi: str, dosyalar: list):
    satirlar = [
        f"📋 <b>{ay_adi} Ayı Tutanakları Hazırlandı</b>",
        "──────────────────────────────",
    ]
    for d in dosyalar:
        tur = d.parent.name.upper()
        satirlar.append(f"✅ {tur} tutanağı şablonu oluşturuldu")
    satirlar.append("\n📎 Tutanaklar gönderiliyor...")
    mesaj_gonder("\n".join(satirlar))
    for d in dosyalar:
        dosya_gonder(d, f"📋 {d.stem}")


def rehberlik_bildirimi_gonder(ay_adi: str, dosyalar: list):
    if not dosyalar:
        return
    satirlar = [
        f"💛 <b>{ay_adi} Rehberlik Raporu Hazırlandı</b>",
        "──────────────────────────────",
    ]
    for d in dosyalar:
        satirlar.append(f"✅ {d.stem} oluşturuldu")
    mesaj_gonder("\n".join(satirlar))
    for d in dosyalar:
        dosya_gonder(d, f"💛 Rehberlik — {d.stem}")
