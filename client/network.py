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

    # ── Oda oluşturma (HTTP) ──────────────────────────────────────────────────
    def oda_olustur(self, callback, sure=300, hamle=20, dil='en'):
        """
        Sunucudan yeni oda kodu ister (seçilen süre + sözlük diliyle).
        callback(kod_veya_None) ana thread'de çağrılır.
        """
        def _run():
            try:
                r = requests.post(
                    f'{self.http}/oda-olustur',
                    params={'sure': sure, 'hamle': hamle, 'dil': dil},
                    timeout=8,
                )
                kod = r.json().get('oda')
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
        self._thread = threading.Thread(
            target=self.ws.run_forever,
            kwargs={'ping_interval': 20, 'ping_timeout': 10},
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
