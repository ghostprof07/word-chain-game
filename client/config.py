"""
Sunucu adresi ayarı — TEK YERDEN düzenlenir.

Telefonda (Android/iOS) ortam değişkeni olmadığı için, yayına aldığın
sunucunun adresini doğrudan buraya yaz.

Aşamalar:
  1) Masaüstü testi (aynı bilgisayar):  http://127.0.0.1:8000  /  ws://127.0.0.1:8000
  2) Android emülatörü:                 http://10.0.2.2:8000    /  ws://10.0.2.2:8000
  3) Aynı Wi-Fi'deki gerçek telefon:    http://<bilgisayar-ip>:8000 / ws://<bilgisayar-ip>:8000
  4) İnternette yayın (önerilen):       https://seninsunucun.com   /  wss://seninsunucun.com

NOT: Gerçek yayında mutlaka https/wss (güvenli) kullan.
"""
import os

# Varsayılan: masaüstü testi. Telefon derlemesinde aşağıyı kendi sunucunla değiştir.
_VARSAYILAN_HTTP = 'http://127.0.0.1:8000'
_VARSAYILAN_WS = 'ws://127.0.0.1:8000'

# Ortam değişkeni varsa onu kullan (masaüstü/PyCharm testleri için), yoksa varsayılan.
SUNUCU_HTTP = os.environ.get('WC_HTTP', _VARSAYILAN_HTTP)
SUNUCU_WS = os.environ.get('WC_WS', _VARSAYILAN_WS)
