[app]

# Uygulama bilgileri
title = Lexicoil
package.name = lexicoil
package.domain = com.kemalyavuz

# Kaynak klasörü (main.py burada)
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,ttf,txt,wav

# Uygulama ikonu (client/icon.png — gradyan + coil motifi)
icon.filename = %(source.dir)s/icon.png

# Sürüm — Play'e her yüklemede artır (versionCode buradan üretilir)
version = 1.1

# Release çıktısı AAB (Google Play yeni uygulamalar için AAB ister, APK değil).
android.release_artifact = aab

# ── BAĞIMLILIKLAR ─────────────────────────────────────────────────────────────
# kivy: arayüz | websocket-client: online bağlantı | requests: oda oluşturma
# certifi + openssl: https/wss (güvenli bağlantı) için gerekli
requirements = python3,kivy==2.3.1,websocket-client,requests,certifi,openssl

# ── EKRAN ─────────────────────────────────────────────────────────────────────
orientation = portrait
fullscreen = 0

# Açılış (yükleme) ekranı: tam ekran gradyan görsel (coil + LEXICOIL).
# presplash.png 1080x2340 dikey; gradyan zemin. Kenarda bant çıkarsa diye
# presplash_color gradyan-pembe tonunda (koyu yerine, harmanlansın).
presplash.filename = %(source.dir)s/presplash.png
android.presplash_color = #FF4B96

# ── İZİNLER ───────────────────────────────────────────────────────────────────
# INTERNET: online oyun için zorunlu
# ACCESS_NETWORK_STATE: bağlantı durumu kontrolü
android.permissions = INTERNET,ACCESS_NETWORK_STATE

# ── ANDROID API SEVİYELERİ ────────────────────────────────────────────────────
# Play (Haz 2026): yeni uygulamalar API 35 hedeflemeli. 31 Ağu 2026'dan sonra
# API 36 zorunlu olacak — o tarihten önce 36'ya yükselt.
android.api = 35
android.minapi = 24
# SDK lisansını otomatik kabul et (CI'da build-tools kurulumu için ŞART)
android.accept_sdk_license = True
# Tek mimari: derleme hızlı + neredeyse tüm modern telefonlar arm64.
# İhtiyaç olursa armeabi-v7a sonradan eklenir.
android.archs = arm64-v8a

# AndroidX desteği (modern kütüphaneler için)
android.enable_androidx = True

# İnternet trafiği (geliştirme sırasında http; yayında wss/https kullan)
android.allow_backup = True

[buildozer]

# Günlük ayrıntı seviyesi (2 = en ayrıntılı)
log_level = 2
warn_on_root = 1
