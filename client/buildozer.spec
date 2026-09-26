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
version = 1.6

# Release çıktısı AAB (Google Play yeni uygulamalar için AAB ister, APK değil).
android.release_artifact = aab

# ── BAĞIMLILIKLAR ─────────────────────────────────────────────────────────────
# kivy: arayüz | websocket-client: online bağlantı | requests: oda oluşturma
# certifi + openssl: https/wss (güvenli bağlantı) için gerekli
# charset-normalizer 3.5+ PyPI'da Android wheel'i (cp314) yayınlıyor; p4a onu seçip
# "not a supported wheel" ile kırılıyor → saf-Python 3.4.5'e sabitlendi (2026-09).
requirements = python3,kivy==2.3.1,websocket-client,requests,certifi,openssl,charset-normalizer==3.4.5

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
# Play kuralı: 31 Ağu 2026'dan sonra güncelleme yayınlamak için API 36
# (Android 16) hedeflemek ZORUNLU. Bu yüzden 35→36'ya yükseltildi.
android.api = 36
android.minapi = 24
# API 36 hedefleyen uygulamalarda Android 16 "predictive back"i zorunlu açıyor:
# KEYCODE_BACK artık gönderilmiyor → Kivy geri tuşunu hiç görmüyor, sistem
# uygulamayı arka plana atıyordu (popup/ekran geri mantığı ölüydü). Google'ın
# geçici opt-out'u: <application android:enableOnBackInvokedCallback="false">.
# İleride kaldırılırsa OnBackInvokedCallback (pyjnius) ile ele alınmalı.
android.extra_manifest_application_arguments = ./android_application_attrs.xml
# SDK lisansını otomatik kabul et (CI'da build-tools kurulumu için ŞART)
android.accept_sdk_license = True
# Tek mimari: derleme hızlı + neredeyse tüm modern telefonlar arm64.
# İhtiyaç olursa armeabi-v7a sonradan eklenir.
android.archs = arm64-v8a

# AndroidX desteği (modern kütüphaneler için)
android.enable_androidx = True

# İnternet trafiği (geliştirme sırasında http; yayında wss/https kullan)
android.allow_backup = True

# ── python-for-android SÜRÜMÜ ─────────────────────────────────────────────────
# p4a 2026.05.09 (master) PyPI'daki Android wheel'lerini seçip kuramıyor
# ("charset_normalizer-3.5.1-cp314-...-android_24_arm64_v8a.whl is not a
# supported wheel") ve requirements'taki sürüm sabitlemesini yok sayıyor.
# Düzeltme develop'ta (kivy/python-for-android#3366, 2026-08-24); resmi sürüm
# çıkınca master'a dönülebilir. Tekrarlanabilirlik için commit sabit.
p4a.branch = develop
p4a.commit = e772ad93f20a61c0bbe1cf8955e073cfb41062e1

[buildozer]

# Günlük ayrıntı seviyesi (2 = en ayrıntılı)
log_level = 2
warn_on_root = 1
