# 🤖 Eğitim Asistanı Botu

Ders programına, yıllık plana ve takvime göre **tamamen otomatik** çalışan eğitim asistanı.

---

## Ne Yapar?

| Görev | Zaman | Çıktı |
|-------|-------|-------|
| Günlük ders planı | Her akşam 18:00 | Word + Telegram mesajı |
| ŞÖK tutanağı | Her ayın 1'i | Word + Telegram dosyası |
| Zümre tutanağı | Eylül ve Ocak | Word + Telegram dosyası |
| Veli toplantısı tutanağı | Ekim, Şubat, Nisan | Word + Telegram dosyası |
| Rehberlik raporu (6-C) | Her ayın 1'i | Word + Telegram dosyası |
| Web arşivi güncelleme | Her çalışmada | GitHub Pages |

---

## Telegram Mesajı Örneği

```
📚 Yarınki Ders Planı — Salı 24.03.2026
──────────────────────────────
🟩 Ders 1 — 7-A
🕐 Saat     : 08:00
📖 Konu     : Newton'un Hareket Yasaları
🎯 Kazanım  : F.7.2.1.1 — Newton'un hareket yasalarını açıklar.
🖥  Simülasyon: https://phet.colorado.edu/tr/simulations/forces-and-motion-basics
📌 Model    : Maarif Modeli
──────────────────────────────
🔵 Ders 2 — 6-C
🕐 Saat     : 10:00
📖 Konu     : Canlıların Sınıflandırılması
🎯 Kazanım  : F.6.6.1.1 — Hücrenin yapısını açıklar.
──────────────────────────────
📎 2 Word plan dosyası gönderiliyor...
```

---

## Kurulum (1 Kez — 15 Dakika)

### Adım 1 — GitHub Reposu

1. [github.com](https://github.com) → **New repository** → Ad: `egitim-botu` → **Create**
2. Bu klasördeki TÜM dosyaları repoya yükle (sürükle-bırak)

### Adım 2 — Telegram Bot

1. Telegram'da `@BotFather` → `/newbot` → token al
2. Bota bir mesaj at, sonra tarayıcıda aç:
   ```
   https://api.telegram.org/bot<TOKEN>/getUpdates
   ```
3. `"chat":{"id":123456789}` → bu senin **Chat ID**'n

### Adım 3 — GitHub Secrets

**Settings → Secrets and variables → Actions → New repository secret**

| Secret | Değer | Örnek |
|--------|-------|-------|
| `TELEGRAM_BOT_TOKEN` | BotFather token | `7123456789:AAF...` |
| `TELEGRAM_CHAT_ID` | Chat ID | `987654321` |
| `OKUL_ADI` | Okulun adı | `Atatürk Ortaokulu` |
| `OGRETMEN_ADI` | Adın soyadın | `Ayşe Yılmaz` |
| `DERS` | Verdiğin ders | `Fen Bilimleri` |
| `REHBERLIK_SINIF` | Sınıf öğretmenliği | `6-C` |
| `SINIFLAR` | Sınıf listesi (model:maarif veya normal) | `6-C:normal,7-A:maarif,8-B:normal` |

### Adım 4 — Web Arayüzü (GitHub Pages)

1. **Settings → Pages**
2. Source: **Deploy from a branch**
3. Branch: `main`, Folder: `/docs`
4. Save → Birkaç dakika sonra: `https://kullaniciadi.github.io/egitim-botu`

---

## Dosyalarını Ekle

### Ders Programı

`girdi/ders_programi/program.json` dosyasını düzenle:
```json
{
  "Pazartesi": [
    {"saat": "08:00", "sinif": "7-A"},
    {"saat": "10:00", "sinif": "6-C"}
  ],
  "Salı": [...]
}
```
**Ya da Excel:** `ders_programi.xlsx` ekle (Saat | Pazartesi | Salı ... sütunları)

### Yıllık Plan

`girdi/yillik_plan/` klasörüne yükle:
- `maarif/` alt klasörüne Maarif modeli planları
- Ana klasöre normal müfredat planları
- Word (.docx) veya PDF formatında

### Önceki Evraklar (Bot Öğrenir)

`girdi/onceki_evraklar/` klasörüne:
- `sok/` → Eski ŞÖK tutanakları
- `zumre/` → Eski zümre tutanakları
- `veli/` → Eski veli toplantısı evrakları

Bot bunları okuyarak gündem maddelerini öğrenir, yeni tutanaklara ekler.

### Rehberlik Planı

`girdi/rehberlik_plani/` klasörüne yıllık rehberlik planını ekle.

---

## Elle Çalıştırma

**GitHub → Actions → Egitim Asistani Botu → Run workflow**

- `sadece`: `hepsi` / `plan` / `tutanak` / `rehberlik`
- `test_modu`: `true` → Telegram'a göndermez, sadece dosya üretir

---

## Klasör Yapısı

```
egitim-botu/
├── girdi/
│   ├── ders_programi/          ← program.json veya .xlsx
│   ├── yillik_plan/            ← Word/PDF yıllık planlar
│   │   └── maarif/             ← Maarif modeli planlar
│   ├── ders_kitaplari/         ← Ders kitabı PDF'leri
│   ├── onceki_evraklar/        ← Bot bunlardan öğrenir
│   │   ├── sok/
│   │   ├── zumre/
│   │   └── veli/
│   └── rehberlik_plani/
├── cikti/                      ← Bot burada üretir
│   ├── gunluk_planlar/
│   ├── tutanaklar/
│   │   ├── sok/
│   │   ├── zumre/
│   │   └── veli/
│   └── rehberlik/
├── docs/                       ← GitHub Pages web arayüzü
│   ├── index.html
│   └── dosyalar.json           ← Bot günceller
├── scripts/                    ← Tüm Python kodları
└── .github/workflows/bot.yml   ← Otomasyon
```
