"""
Ağ katmanı — sunucuyla WebSocket bağlantısını yönetir.
Kivy ana iş parçacığını bloke etmemek için bağlantı ayrı bir thread'de çalışır;
gelen mesajlar Clock ile ana thread'e güvenli şekilde iletilir.
"""
import json
import threading

import requests
import websocket  # websocket-client paketi
from kivy.clock import Clock

# Android'de websocket-client sistem CA sertifikalarını bulamaz; certifi'nin
# paketlenmiş CA listesini kullanırız (wss el sıkışması için zorunlu).
try:
    import certifi
    _CA_BUNDLE = certifi.where()
except Exception:
    _CA_BUNDLE = None


class NetworkClient:
    def __init__(self, sunucu_http, sunucu_ws):
        """
        sunucu_http: 'http://10.0.2.2:8000' gibi (oda oluşturmak için)
        sunucu_ws:   'ws://10.0.2.2:8000'   gibi (oyun bağlantısı için)
        """
        self.http = sunucu_http.rstrip('/')
        self.ws_base = sunucu_ws.rstrip('/')
        self.ws = None
        self._thread = None
        self.on_message = None   # callback(dict) — ana thread'de çalışır
        self.on_open = None
        self.on_close = None
        self.bagli = False

    # ── Sunucuyu uyandır (cold start'ı gizle) ─────────────────────────────────
    def uyandir(self):
        """
        Render free tier sunucusu uykudaysa arka planda uyandırır.
        Uygulama açılışında çağrılır; kullanıcı adını yazana kadar sunucu
        uyanmış olur, böylece 'oda oluştur' anında yanıt verir.
        """
        def _run():
            try:
                requests.get(f'{self.http}/', timeout=60)
            except Exception:
                pass
        threading.Thread(target=_run, daemon=True).start()

    # ── Oda oluşturma (HTTP) ──────────────────────────────────────────────────
    def oda_olustur(self, callback, sure=300, hamle=20, dil='en'):
        """
        Sunucudan yeni oda kodu ister (seçilen süre + sözlük diliyle).
        callback(kod_veya_None) ana thread'de çağrılır.
        """
        def _run():
            kod = None
            # Render free tier uykudan ~50-60sn'de uyanir; ilk istek uzun surebilir.
            # Bu yuzden uzun timeout + bir kez yeniden deneme (cold start'i kurtarir).
            for _deneme in range(2):
                try:
                    r = requests.post(
                        f'{self.http}/oda-olustur',
                        params={'sure': sure, 'hamle': hamle, 'dil': dil},
                        timeout=60,
                    )
                    kod = r.json().get('oda')
                    break
                except Exception:
                    kod = None
            Clock.schedule_once(lambda dt: callback(kod), 0)
        threading.Thread(target=_run, daemon=True).start()

    # ── Odaya bağlanma (WebSocket) ────────────────────────────────────────────
    def baglan(self, oda_kodu, ad):
        url = f'{self.ws_base}/ws/{oda_kodu}?ad={ad}'

        def _on_message(_ws, mesaj):
            try:
                veri = json.loads(mesaj)
            except json.JSONDecodeError:
                return
            if self.on_message:
                Clock.schedule_once(lambda dt: self.on_message(veri), 0)

        def _on_open(_ws):
            self.bagli = True
            if self.on_open:
                Clock.schedule_once(lambda dt: self.on_open(), 0)

        def _on_close(_ws, *args):
            self.bagli = False
            if self.on_close:
                Clock.schedule_once(lambda dt: self.on_close(), 0)

        def _on_error(_ws, hata):
            self.bagli = False

        self.ws = websocket.WebSocketApp(
            url,
            on_message=_on_message,
            on_open=_on_open,
            on_close=_on_close,
            on_error=_on_error,
        )
        run_kwargs = {'ping_interval': 20, 'ping_timeout': 10}
        # wss bağlantısında CA paketini açıkça ver (özellikle Android için).
        if self.ws_base.startswith('wss') and _CA_BUNDLE:
            run_kwargs['sslopt'] = {'ca_certs': _CA_BUNDLE}
        self._thread = threading.Thread(
            target=self.ws.run_forever,
            kwargs=run_kwargs,
            daemon=True,
        )
        self._thread.start()

    # ── Kelime gönderme ───────────────────────────────────────────────────────
    def kelime_gonder(self, kelime):
        if self.ws and self.bagli:
            try:
                self.ws.send(json.dumps({'tip': 'kelime', 'kelime': kelime}))
            except Exception:
                pass

    # ── Tekrar oyna (rematch) isteği ──────────────────────────────────────────
    def rematch_iste(self):
        if self.ws and self.bagli:
            try:
                self.ws.send(json.dumps({'tip': 'rematch'}))
            except Exception:
                pass

    # ── Sohbet mesajı gönderme ────────────────────────────────────────────────
    def sohbet_gonder(self, mesaj):
        if self.ws and self.bagli:
            try:
                self.ws.send(json.dumps({'tip': 'sohbet', 'mesaj': mesaj}))
            except Exception:
                pass

    def kapat(self):
        if self.ws:
            try:
                self.ws.close()
            except Exception:
                pass
        self.bagli = False
