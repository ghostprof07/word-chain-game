# 📱 Word Chain — Mobil (iOS / Android) Rehberi

İki kişilik online kelime oyununu telefona kurulabilir hale getirme adımları.

---

## Yapı

```
word_chain_game/
├── server/              Online sunucu (FastAPI) — bir yerde sürekli çalışmalı
├── client/              Telefona kurulacak Kivy uygulaması
│   ├── main.py          Arayüz (mobil uyumlu: dokunmatik, klavye, dikey)
│   ├── network.py       WebSocket bağlantısı
│   ├── config.py        ⭐ SUNUCU ADRESİ burada — telefon için düzenle
│   └── buildozer.spec   Android APK ayarları
└── .github/workflows/
    └── build-android.yml  Bulutta otomatik APK derleme
```

---

## Adım 1 — Sunucuyu internete aç (ZORUNLU)

Telefonlar farklı ağlardan bağlanacağı için sunucu herkesin erişebileceği bir
yerde olmalı. Ücretsiz seçenekler: **Render.com**, **Railway.app**, **Fly.io**.

Özet (Render örneği):
1. `server/` klasörünü bir GitHub deposuna koy
2. Render'da "New Web Service" → depoyu seç
3. Start komutu: `uvicorn main:app --host 0.0.0.0 --port $PORT`
4. Render sana bir adres verir: `https://wordchain-xxxx.onrender.com`

Sonra `client/config.py` içinde:
```python
_VARSAYILAN_HTTP = 'https://wordchain-xxxx.onrender.com'
_VARSAYILAN_WS   = 'wss://wordchain-xxxx.onrender.com'
```

---

## Adım 2 — Android APK üret

Windows'ta Buildozer doğrudan çalışmaz. İki yol:

### A) GitHub Actions (önerilen — Windows'tan çıkmadan)
1. Tüm projeyi bir GitHub deposuna yükle
2. `.github/workflows/build-android.yml` zaten hazır
3. GitHub → **Actions** sekmesi → iş otomatik çalışır
4. Bitince **Artifacts**'tan `wordchain-apk` indir → telefona kur

### B) WSL2 (yerel Linux)
```bash
wsl --install            # Windows'ta bir kez
# Ubuntu içinde:
pip install buildozer cython==0.29.36
cd client && buildozer -v android debug
# APK: client/bin/*.apk
```

---

## Adım 3 — iOS (yalnızca Mac'te)

iOS derlemesi **Mac + Xcode** ister, Windows'ta mümkün değil.
Bir Mac'e erişince:
```bash
pip install kivy-ios
toolchain build python3 kivy
toolchain create WordChain ~/word_chain_game/client
# Çıkan Xcode projesini aç, imzala, cihaza/App Store'a gönder
```
`config.py` yine yayındaki sunucuya işaret etmeli.

---

## Test sırası (önerilen)

1. **Masaüstü** (şu an çalışıyor): PyCharm'da Sunucu + 2 Oyuncu konfigürasyonları
2. **Aynı Wi-Fi telefon**: sunucuyu bilgisayarda çalıştır, `config.py`'a bilgisayarın
   yerel IP'sini yaz (`http://192.168.x.x:8000`), APK'yı telefona kur
3. **İnternet**: sunucuyu Render'a al, `config.py`'ı güncelle, yeniden APK üret
