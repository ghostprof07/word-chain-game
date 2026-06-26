[app]

# Uygulama bilgileri
title = Word Chain
package.name = wordchain
package.domain = com.kemalyavuz

# Kaynak klasörü (main.py burada)
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,ttf

# Sürüm
version = 1.0

# ── BAĞIMLILIKLAR ─────────────────────────────────────────────────────────────
# kivy: arayüz | websocket-client: online bağlantı | requests: oda oluşturma
# certifi + openssl: https/wss (güvenli bağlantı) için gerekli
requirements = python3,kivy==2.3.1,websocket-client,requests,certifi,openssl

# ── EKRAN ─────────────────────────────────────────────────────────────────────
orientation = portrait
fullscreen = 0

# Açılış ekranı rengi (koyu)
android.presplash_color = #0D0D0D

# ── İZİNLER ───────────────────────────────────────────────────────────────────
# INTERNET: online oyun için zorunlu
# ACCESS_NETWORK_STATE: bağlantı durumu kontrolü
android.permissions = INTERNET,ACCESS_NETWORK_STATE

# ── ANDROID API SEVİYELERİ ────────────────────────────────────────────────────
android.api = 34
android.minapi = 24
android.ndk = 25b
android.archs = arm64-v8a,armeabi-v7a

# AndroidX desteği (modern kütüphaneler için)
android.enable_androidx = True

# İnternet trafiği (geliştirme sırasında http; yayında wss/https kullan)
android.allow_backup = True

[buildozer]

# Günlük ayrıntı seviyesi (2 = en ayrıntılı)
log_level = 2
warn_on_root = 1
