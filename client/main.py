"""
WORD CHAIN — Online Mobile Client (Kivy)
=========================================
Two-player online word chain game. UI language: English.

Screens:
    BaglanEkrani  → enter name, create or join a room
    LobiEkrani    → waiting for opponent
    OyunEkrani    → game driven by server state (input locked when not your turn)
    SonucEkrani   → winner + statistics

Run (desktop test):
    pip install kivy websocket-client requests
    python main.py

Server address is set in config.py (SUNUCU_HTTP / SUNUCU_WS).
"""
import os

from kivy.utils import platform

# Window size/position only applies on desktop test.
# On mobile (android/ios) the app opens fullscreen, so these are skipped.
if platform not in ('android', 'ios'):
    from kivy.config import Config
    Config.set('graphics', 'width', os.environ.get('WC_W', '400'))
    Config.set('graphics', 'height', os.environ.get('WC_H', '720'))
    if os.environ.get('WC_LEFT'):
        Config.set('graphics', 'left', os.environ['WC_LEFT'])
    if os.environ.get('WC_TOP'):
        Config.set('graphics', 'top', os.environ['WC_TOP'])

from kivy.app import App
from kivy.clock import Clock
from kivy.core.window import Window

# On mobile keep the input above the soft keyboard
Window.softinput_mode = 'below_target'
from kivy.graphics import Color, RoundedRectangle
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.screenmanager import ScreenManager, Screen, FadeTransition
from kivy.uix.scrollview import ScrollView
from kivy.uix.textinput import TextInput

from network import NetworkClient
from config import SUNUCU_HTTP, SUNUCU_WS

Window.clearcolor = (0.05, 0.05, 0.05, 1)

# ── Colors ────────────────────────────────────────────────────────────────────
KOYU    = (0.07, 0.07, 0.07, 1)
YESIL   = (0, 0.78, 0.32, 1)
MAVI    = (0, 0.85, 1, 1)
SARI    = (1, 0.84, 0, 1)
KIRMIZI = (1, 0.3, 0.3, 1)
GENC    = (0.15, 0.15, 0.15, 1)


# ── Helpers ───────────────────────────────────────────────────────────────────
def kart(widget, renk=GENC, radius=12):
    with widget.canvas.before:
        Color(*renk)
        rect = RoundedRectangle(pos=widget.pos, size=widget.size, radius=[dp(radius)])
    widget.bind(
        pos=lambda *a: setattr(rect, 'pos', widget.pos),
        size=lambda *a: setattr(rect, 'size', widget.size),
    )


def etiket(metin, boyut=15, renk=(1, 1, 1, 1), kalin=False, hizala='center', **kw):
    lbl = Label(text=metin, font_size=dp(boyut), color=renk,
                bold=kalin, halign=hizala, valign='middle', **kw)
    lbl.bind(size=lambda *a: setattr(lbl, 'text_size', lbl.size))
    return lbl


def buton(metin, renk_bg=YESIL, renk_yazi=(0, 0, 0, 1), boyut=17, callback=None):
    btn = Button(text=metin, font_size=dp(boyut), bold=True, color=renk_yazi,
                 background_normal='', background_color=(0, 0, 0, 0))
    kart(btn, renk=renk_bg, radius=14)
    if callback:
        btn.bind(on_press=callback)
    return btn


def giris_kutusu(hint, **kw):
    kw.setdefault('font_size', dp(22))
    ti = TextInput(multiline=False,
                   hint_text=hint, hint_text_color=(0.3, 0.3, 0.3, 1),
                   background_color=GENC, foreground_color=(1, 1, 1, 1),
                   cursor_color=YESIL, padding=[dp(14), dp(12)], **kw)
    return ti


# ══════════════════════════════════════════════════════════════════════════════
#  1. CONNECT SCREEN — enter name, create or join a room
# ══════════════════════════════════════════════════════════════════════════════
class BaglanEkrani(Screen):
    def __init__(self, **kw):
        super().__init__(**kw)
        kok = BoxLayout(orientation='vertical', padding=dp(28), spacing=dp(16))
        kart(kok, renk=KOYU)

        kok.add_widget(Label(size_hint_y=None, height=dp(30)))
        baslik = etiket('WORD\nCHAIN', boyut=50, kalin=True, renk=YESIL)
        baslik.size_hint_y = None
        baslik.height = dp(120)
        kok.add_widget(baslik)
        kok.add_widget(etiket('Online — play on two devices', boyut=14,
                              renk=(0.6, 0.6, 0.6, 1), hizala='center'))

        kok.add_widget(Label(size_hint_y=None, height=dp(10)))

        # Name input
        self.ad_giris = giris_kutusu('Your name...', size_hint_y=None, height=dp(54))
        kok.add_widget(self.ad_giris)

        # ── Duration option (chosen by room creator) ──
        self._secili_sure = 300   # default 5 min
        kok.add_widget(etiket('Game duration', boyut=12, renk=(0.5, 0.5, 0.5, 1),
                              hizala='left', size_hint_y=None, height=dp(18)))
        self._sure_satir = BoxLayout(size_hint_y=None, height=dp(44), spacing=dp(8))
        self._sure_butonlar = {}
        for etiket_metin, saniye in [('3 min', 180), ('5 min', 300), ('10 min', 600)]:
            b = self._secim_butonu(etiket_metin,
                                   lambda _b, s=saniye: self._sure_sec(s))
            self._sure_butonlar[saniye] = b
            self._sure_satir.add_widget(b)
        kok.add_widget(self._sure_satir)
        self._sure_sec(300)   # initial highlight

        # Create room button
        kok.add_widget(buton('CREATE ROOM', callback=self.oda_olustur))

        # Separator
        kok.add_widget(etiket('— or —', boyut=12, renk=(0.4, 0.4, 0.4, 1)))

        # Join with room code
        self.kod_giris = giris_kutusu('Room code (e.g. AB12)',
                                      size_hint_y=None, height=dp(54))
        kok.add_widget(self.kod_giris)
        kok.add_widget(buton('JOIN WITH CODE', renk_bg=MAVI, callback=self.katil))

        # Status / error message
        self.durum = etiket('', boyut=13, renk=SARI)
        self.durum.size_hint_y = None
        self.durum.height = dp(30)
        kok.add_widget(self.durum)

        kok.add_widget(Label())
        self.add_widget(kok)

    @property
    def net(self):
        return App.get_running_app().net

    def _ad(self):
        return self.ad_giris.text.strip() or 'Player'

    def _secim_butonu(self, metin, callback):
        """Selectable button whose color can change later (keeps a Color ref)."""
        btn = Button(text=metin, font_size=dp(14), bold=True,
                     color=(0.7, 0.7, 0.7, 1),
                     background_normal='', background_color=(0, 0, 0, 0))
        with btn.canvas.before:
            renk = Color(*GENC)
            rect = RoundedRectangle(pos=btn.pos, size=btn.size, radius=[dp(12)])
        btn.bind(pos=lambda *a: setattr(rect, 'pos', btn.pos),
                 size=lambda *a: setattr(rect, 'size', btn.size))
        btn._renk = renk    # _sure_sec updates this
        btn.bind(on_press=callback)
        return btn

    def _sure_sec(self, saniye):
        """Selects and highlights one of the duration buttons."""
        self._secili_sure = saniye
        for s, b in self._sure_butonlar.items():
            secili = (s == saniye)
            b._renk.rgba = YESIL if secili else GENC
            b.color = (0, 0, 0, 1) if secili else (0.7, 0.7, 0.7, 1)

    def oda_olustur(self, *_):
        self.durum.text = 'Creating room...'
        self.durum.color = SARI

        def geldi(kod):
            if kod:
                App.get_running_app().baglan_ve_gec(kod, self._ad())
            else:
                self.durum.text = 'Could not reach server!'
                self.durum.color = KIRMIZI

        self.net.oda_olustur(geldi, sure=self._secili_sure)

    def katil(self, *_):
        kod = self.kod_giris.text.strip().upper()
        if len(kod) < 3:
            self.durum.text = 'Enter a valid room code.'
            self.durum.color = KIRMIZI
            return
        self.durum.text = 'Connecting...'
        self.durum.color = SARI
        App.get_running_app().baglan_ve_gec(kod, self._ad())


# ══════════════════════════════════════════════════════════════════════════════
#  2. LOBBY SCREEN — waiting for opponent
# ══════════════════════════════════════════════════════════════════════════════
class LobiEkrani(Screen):
    def __init__(self, **kw):
        super().__init__(**kw)
        kok = BoxLayout(orientation='vertical', padding=dp(28), spacing=dp(16))
        kart(kok, renk=KOYU)

        kok.add_widget(Label())
        kok.add_widget(etiket('ROOM CODE', boyut=14, renk=(0.5, 0.5, 0.5, 1)))
        self.kod_lbl = etiket('----', boyut=56, kalin=True, renk=YESIL)
        self.kod_lbl.size_hint_y = None
        self.kod_lbl.height = dp(80)
        kok.add_widget(self.kod_lbl)
        kok.add_widget(etiket('Share this code with your opponent', boyut=13,
                              renk=(0.6, 0.6, 0.6, 1)))

        kok.add_widget(Label(size_hint_y=None, height=dp(20)))
        self.bekle_lbl = etiket('Waiting for opponent...', boyut=16, renk=SARI)
        kok.add_widget(self.bekle_lbl)

        kok.add_widget(Label())
        kok.add_widget(buton('CANCEL', renk_bg=GENC, renk_yazi=(0.8, 0.8, 0.8, 1),
                             callback=lambda *_: App.get_running_app().odadan_cik()))
        kok.add_widget(Label(size_hint_y=None, height=dp(10)))
        self.add_widget(kok)

    def kodu_ayarla(self, kod):
        self.kod_lbl.text = kod


# ══════════════════════════════════════════════════════════════════════════════
#  3. GAME SCREEN — updated from server state
# ══════════════════════════════════════════════════════════════════════════════
class OyunEkrani(Screen):
    def __init__(self, **kw):
        super().__init__(**kw)
        self._benim_no = 1

        kok = BoxLayout(orientation='vertical', padding=dp(18), spacing=dp(10))
        kart(kok, renk=KOYU)

        # Top bar
        ust = BoxLayout(size_hint_y=None, height=dp(38))
        self.toplam_lbl = etiket('05:00', boyut=20, kalin=True,
                                 renk=(0.5, 0.5, 0.5, 1), hizala='left')
        self.kelime_lbl = etiket('0 words', boyut=12, renk=(0.4, 0.4, 0.4, 1))
        # Chat button (also shows unread count)
        self.sohbet_btn = buton('💬', renk_bg=MAVI, renk_yazi=(0, 0, 0, 1), boyut=15,
                                callback=lambda *_: App.get_running_app().sohbet_ac())
        self.sohbet_btn.size_hint_x = None
        self.sohbet_btn.width = dp(52)
        cik = buton('QUIT', renk_bg=GENC, renk_yazi=(0.6, 0.6, 0.6, 1), boyut=12,
                    callback=lambda *_: App.get_running_app().odadan_cik())
        cik.size_hint_x = None
        cik.width = dp(60)
        ust.add_widget(self.toplam_lbl)
        ust.add_widget(self.kelime_lbl)
        ust.add_widget(self.sohbet_btn)
        ust.add_widget(cik)
        kok.add_widget(ust)

        # ── WORD CHAIN (top, used words in order) ──
        self.zincir_scroll = ScrollView(size_hint_y=None, height=dp(36),
                                        do_scroll_x=True, do_scroll_y=False,
                                        bar_width=0)
        self.zincir_kutu = BoxLayout(orientation='horizontal', size_hint=(None, None),
                                     height=dp(36), spacing=dp(2), padding=[dp(6), 0])
        self.zincir_kutu.bind(minimum_width=self.zincir_kutu.setter('width'))
        self.zincir_scroll.add_widget(self.zincir_kutu)
        kart(self.zincir_scroll, renk=(0.1, 0.1, 0.1, 1), radius=8)
        kok.add_widget(self.zincir_scroll)
        self._zincir_uzunluk = -1

        # Player cards
        oyuncu_satir = BoxLayout(size_hint_y=None, height=dp(86), spacing=dp(12))
        self.p1_kutu = BoxLayout(orientation='vertical', spacing=dp(4), padding=dp(10))
        kart(self.p1_kutu, renk=GENC)
        self.p1_ad = etiket('Player 1', boyut=11, kalin=True, renk=YESIL)
        self.p1_puan = etiket('0', boyut=34, kalin=True)
        self.p1_kutu.add_widget(self.p1_ad)
        self.p1_kutu.add_widget(self.p1_puan)

        self.p2_kutu = BoxLayout(orientation='vertical', spacing=dp(4), padding=dp(10))
        kart(self.p2_kutu, renk=GENC)
        self.p2_ad = etiket('Player 2', boyut=11, kalin=True, renk=MAVI)
        self.p2_puan = etiket('0', boyut=34, kalin=True)
        self.p2_kutu.add_widget(self.p2_ad)
        self.p2_kutu.add_widget(self.p2_puan)

        oyuncu_satir.add_widget(self.p1_kutu)
        oyuncu_satir.add_widget(self.p2_kutu)
        kok.add_widget(oyuncu_satir)

        # Turn info
        self.tur_lbl = etiket('', boyut=14, renk=(0.6, 0.6, 0.6, 1))
        self.tur_lbl.size_hint_y = None
        self.tur_lbl.height = dp(24)
        kok.add_widget(self.tur_lbl)

        # Big letter
        self.harf_lbl = etiket('?', boyut=72, kalin=True, renk=YESIL)
        self.harf_lbl.size_hint_y = None
        self.harf_lbl.height = dp(110)
        kok.add_widget(self.harf_lbl)

        # Turn timer
        self.hamle_lbl = etiket('20', boyut=24, kalin=True, renk=YESIL)
        self.hamle_lbl.size_hint_y = None
        self.hamle_lbl.height = dp(34)
        kok.add_widget(self.hamle_lbl)

        # Last word
        self.son_lbl = etiket('', boyut=13, renk=(0.4, 0.4, 0.4, 1))
        self.son_lbl.size_hint_y = None
        self.son_lbl.height = dp(22)
        kok.add_widget(self.son_lbl)

        kok.add_widget(Label())

        # Status message
        self.durum_lbl = etiket('', boyut=15, kalin=True, renk=SARI)
        self.durum_lbl.size_hint_y = None
        self.durum_lbl.height = dp(28)
        kok.add_widget(self.durum_lbl)

        # Input
        self.giris = giris_kutusu('Type a word...', size_hint_y=None, height=dp(56),
                                  font_size=dp(26))
        self.giris.bind(on_text_validate=lambda *_: self._gonder())
        kok.add_widget(self.giris)

        # Send
        self.gonder_btn = buton('SEND', callback=lambda *_: self._gonder())
        self.gonder_btn.size_hint_y = None
        self.gonder_btn.height = dp(56)
        kok.add_widget(self.gonder_btn)

        kok.add_widget(Label(size_hint_y=None, height=dp(6)))
        self.add_widget(kok)

    def benim_no_ayarla(self, no):
        self._benim_no = no

    def _gonder(self):
        kelime = self.giris.text.strip().lower()
        self.giris.text = ''
        if kelime:
            App.get_running_app().net.kelime_gonder(kelime)

    # ── Messages from server ─────────────────────────────────────────────────
    def kelime_sonuc(self, basari, mesaj):
        self.durum_lbl.text = mesaj
        self.durum_lbl.color = YESIL if basari else KIRMIZI

    def durum_guncelle(self, d):
        # Time
        m, s = divmod(int(d['toplam_sure']), 60)
        self.toplam_lbl.text = f'{m:02d}:{s:02d}'
        self.kelime_lbl.text = f"{d['kelime_sayisi']} words"

        # Letter
        self.harf_lbl.text = d['gerekli_harf'].upper()

        # Turn timer + color
        t = int(d['hamle_sure'])
        self.hamle_lbl.text = str(t)
        if t > 10:
            self.hamle_lbl.color = YESIL
        elif t > 5:
            self.hamle_lbl.color = SARI
        else:
            self.hamle_lbl.color = KIRMIZI

        # Last word
        self.son_lbl.text = f"Last: {d['son_kelime']}" if d['son_kelime'] else ''

        # Word chain (top)
        self._zincir_guncelle(d.get('zincir', []))

        # Scores + names
        oyuncular = d.get('oyuncular', {})
        self.p1_ad.text = oyuncular.get('1', 'Player 1')
        self.p2_ad.text = oyuncular.get('2', 'Player 2')
        self.p1_puan.text = str(d['puan']['1'])
        self.p2_puan.text = str(d['puan']['2'])

        # Whose turn? — highlight cards, lock/unlock input
        sira = d['siradaki_no']
        benim_sira = (sira == self._benim_no)

        self._kart_vurgu(self.p1_kutu, sira == 1, YESIL)
        self._kart_vurgu(self.p2_kutu, sira == 2, MAVI)

        if benim_sira:
            self.tur_lbl.text = 'YOUR TURN — type a word!'
            self.tur_lbl.color = YESIL
            self.giris.disabled = False
            self.gonder_btn.disabled = False
            self.gonder_btn.opacity = 1
        else:
            ad = oyuncular.get(str(sira), f'Player {sira}')
            self.tur_lbl.text = f'{ad} is playing...'
            self.tur_lbl.color = (0.6, 0.6, 0.6, 1)
            self.giris.disabled = True
            self.gonder_btn.disabled = True
            self.gonder_btn.opacity = 0.4

    def _kart_vurgu(self, kutu, aktif, renk):
        kutu.canvas.before.clear()
        with kutu.canvas.before:
            if aktif:
                Color(renk[0], renk[1], renk[2], 0.18)
            else:
                Color(*GENC)
            RoundedRectangle(pos=kutu.pos, size=kutu.size, radius=[dp(12)])

    def _zincir_guncelle(self, zincir):
        """Updates the word chain at the top (colored by player)."""
        # Redraw only if word count changed (performance)
        if len(zincir) == self._zincir_uzunluk:
            return
        self._zincir_uzunluk = len(zincir)
        self.zincir_kutu.clear_widgets()

        if not zincir:
            bos = Label(text='No words yet', font_size=dp(12),
                        color=(0.35, 0.35, 0.35, 1), size_hint_x=None, width=dp(150))
            self.zincir_kutu.add_widget(bos)
            return

        for i, oge in enumerate(zincir):
            renk = YESIL if oge['no'] == 1 else MAVI
            metin = oge['kelime'] if i == 0 else f"→  {oge['kelime']}"
            lbl = Label(text=metin, font_size=dp(14), bold=True, color=renk,
                        size_hint_x=None)
            lbl.bind(texture_size=lambda inst, val: setattr(inst, 'width', val[0] + dp(8)))
            lbl.texture_update()
            lbl.width = lbl.texture_size[0] + dp(8)
            self.zincir_kutu.add_widget(lbl)

        # Scroll to the latest word
        Clock.schedule_once(lambda dt: setattr(self.zincir_scroll, 'scroll_x', 1), 0)


# ══════════════════════════════════════════════════════════════════════════════
#  4. RESULT SCREEN
# ══════════════════════════════════════════════════════════════════════════════
class SonucEkrani(Screen):
    def __init__(self, **kw):
        super().__init__(**kw)
        self._kok = BoxLayout(orientation='vertical', padding=dp(24), spacing=dp(14))
        kart(self._kok, renk=KOYU)
        self.add_widget(self._kok)

    def goster(self, d, benim_no):
        self._kok.clear_widgets()
        self._benim_no = benim_no
        p1, p2 = d['puan']['1'], d['puan']['2']
        kazanan = d.get('kazanan')
        ayrilan = d.get('ayrilan_ad')

        # Different heading if opponent left
        if ayrilan:
            ust_yazi, ust_renk = 'GAME OVER', (0.5, 0.5, 0.5, 1)
            yazi, renk = 'OPPONENT LEFT', SARI
        else:
            ust_yazi, ust_renk = 'GAME OVER', (0.5, 0.5, 0.5, 1)
            if kazanan == 0 or kazanan is None:
                yazi, renk = 'DRAW!', SARI
            elif kazanan == benim_no:
                yazi, renk = 'YOU WON! 🎉', YESIL
            else:
                yazi, renk = 'YOU LOST', KIRMIZI

        self._kok.add_widget(Label(size_hint_y=None, height=dp(16)))
        self._kok.add_widget(etiket(ust_yazi, boyut=13, renk=ust_renk))
        self._kok.add_widget(etiket(yazi, boyut=32, kalin=True, renk=renk))
        if ayrilan:
            self._kok.add_widget(etiket(f'{ayrilan} left the game', boyut=13,
                                        renk=(0.6, 0.6, 0.6, 1)))

        oyuncular = d.get('oyuncular', {})
        kutular = BoxLayout(size_hint_y=None, height=dp(100), spacing=dp(14))
        for no, c in [(1, YESIL), (2, MAVI)]:
            kutu = BoxLayout(orientation='vertical', spacing=dp(4), padding=dp(12))
            kart(kutu, renk=GENC)
            kutu.add_widget(etiket(oyuncular.get(str(no), f'Player {no}'),
                                   boyut=11, kalin=True, renk=c))
            kutu.add_widget(etiket(str(d['puan'][str(no)]), boyut=42, kalin=True))
            kutu.add_widget(etiket('pts', boyut=12, renk=(0.5, 0.5, 0.5, 1)))
            kutular.add_widget(kutu)
        self._kok.add_widget(kutular)

        toplam = p1 + p2
        sayi = d['kelime_sayisi']
        ort = f'{toplam/sayi:.1f}' if sayi else '0'
        istat = BoxLayout(size_hint_y=None, height=dp(64), padding=dp(12))
        kart(istat, renk=GENC)
        for deger, ad in [(str(sayi), 'Words'), (str(toplam), 'Total'), (ort, 'Avg')]:
            k = BoxLayout(orientation='vertical')
            k.add_widget(etiket(deger, boyut=24, kalin=True))
            k.add_widget(etiket(ad, boyut=10, renk=(0.5, 0.5, 0.5, 1)))
            istat.add_widget(k)
        self._kok.add_widget(istat)

        self._kok.add_widget(etiket('Words Used', boyut=12,
                                    renk=(0.5, 0.5, 0.5, 1), size_hint_y=None,
                                    height=dp(18)))
        kelimeler = d.get('kullanilan', [])
        self._kok.add_widget(etiket('  '.join(kelimeler) if kelimeler else '—',
                                    boyut=13, renk=(0.7, 0.7, 0.7, 1)))

        # Rematch waiting message
        self._rematch_durum = etiket('', boyut=13, kalin=True, renk=SARI,
                                     size_hint_y=None, height=dp(24))
        self._kok.add_widget(self._rematch_durum)

        self._kok.add_widget(Label())

        # Buttons: no rematch if opponent left, only main menu
        if not ayrilan:
            self._rematch_btn = buton('🔄 PLAY AGAIN',
                                      callback=lambda *_: self._rematch_iste())
            self._rematch_btn.size_hint_y = None
            self._rematch_btn.height = dp(54)
            self._kok.add_widget(self._rematch_btn)
        else:
            self._rematch_btn = None

        self._kok.add_widget(buton('MAIN MENU', renk_bg=GENC,
                                   renk_yazi=(0.8, 0.8, 0.8, 1),
                                   callback=lambda *_: App.get_running_app().odadan_cik()))
        self._kok.add_widget(Label(size_hint_y=None, height=dp(12)))

    def _rematch_iste(self):
        """Sends a rematch request and switches to waiting state."""
        App.get_running_app().net.rematch_iste()
        self._rematch_durum.text = 'Waiting for opponent...'
        if self._rematch_btn:
            self._rematch_btn.disabled = True
            self._rematch_btn.opacity = 0.5

    def guncelle(self, d):
        """Updates rematch state / opponent-left while result screen is open."""
        # If opponent left, redraw the screen (to remove rematch button)
        if d.get('ayrilan_ad') and getattr(self, '_rematch_btn', None):
            self.goster(d, self._benim_no)
            return
        sayi = d.get('rematch_sayisi', 0)
        if sayi == 1 and hasattr(self, '_rematch_durum'):
            # Opponent may have requested; inform if my button is still active
            if self._rematch_btn and not self._rematch_btn.disabled:
                self._rematch_durum.text = 'Opponent wants a rematch!'
                self._rematch_durum.color = YESIL


# ══════════════════════════════════════════════════════════════════════════════
#  APP
# ══════════════════════════════════════════════════════════════════════════════
class WordChainOnlineApp(App):
    def build(self):
        self.net = NetworkClient(SUNUCU_HTTP, SUNUCU_WS)
        self.net.on_message = self._mesaj_geldi
        self.net.on_close = self._baglanti_koptu
        self._benim_no = 1
        self._oda_kodu = None
        # Chat state
        self._sohbet = []            # [{'no':int, 'ad':str, 'mesaj':str}]
        self._sohbet_popup = None
        self._sohbet_kutu = None     # message list inside the popup
        self._okunmamis = 0

        self.sm = ScreenManager(transition=FadeTransition(duration=0.2))
        self.sm.add_widget(BaglanEkrani(name='baglan'))
        self.sm.add_widget(LobiEkrani(name='lobi'))
        self.sm.add_widget(OyunEkrani(name='oyun'))
        self.sm.add_widget(SonucEkrani(name='sonuc'))
        return self.sm

    # ── Connection management ────────────────────────────────────────────────
    def baglan_ve_gec(self, oda_kodu, ad):
        self._oda_kodu = oda_kodu
        self.net.baglan(oda_kodu, ad)
        self.sm.get_screen('lobi').kodu_ayarla(oda_kodu)
        self.sm.current = 'lobi'

    def odadan_cik(self):
        self.net.kapat()
        self.ana_menuye()

    def ana_menuye(self):
        self.sm.current = 'baglan'

    def _baglanti_koptu(self):
        if self.sm.current not in ('sonuc', 'baglan'):
            self.sm.get_screen('baglan').durum.text = 'Connection lost.'
            self.sm.get_screen('baglan').durum.color = KIRMIZI
            self.sm.current = 'baglan'

    # ── Routing of server messages ───────────────────────────────────────────
    def _mesaj_geldi(self, veri):
        tip = veri.get('tip')

        if tip == 'katildi':
            self._benim_no = veri['senin_no']
            self.sm.get_screen('oyun').benim_no_ayarla(self._benim_no)

        elif tip == 'hata':
            ekran = self.sm.get_screen('baglan')
            ekran.durum.text = veri.get('mesaj', 'Error!')
            ekran.durum.color = KIRMIZI
            self.sm.current = 'baglan'

        elif tip == 'sohbet':
            self._sohbet_geldi(veri)

        elif tip == 'kelime_sonuc':
            self.sm.get_screen('oyun').kelime_sonuc(veri['basari'], veri['mesaj'])

        elif tip == 'yeni_oyun':
            # Rematch accepted — both players go to the new round
            self.sm.get_screen('oyun').durum_guncelle(veri)
            self.sm.current = 'oyun'

        elif tip in ('durum', 'oyuncu_ayrildi'):
            self._durum_isle(veri)

        elif tip == 'oyun_bitti':
            self.sm.get_screen('sonuc').goster(veri, self._benim_no)
            self.sm.current = 'sonuc'

    def _durum_isle(self, d):
        # If both players are in, go to the game
        if d.get('basladi') and not d.get('bitti'):
            if self.sm.current == 'lobi':
                self.sm.current = 'oyun'
            if self.sm.current == 'oyun':
                self.sm.get_screen('oyun').durum_guncelle(d)
        elif d.get('bitti'):
            if self.sm.current == 'sonuc':
                # Already on result screen — update rematch/leave state
                self.sm.get_screen('sonuc').guncelle(d)
            else:
                self.sm.get_screen('sonuc').goster(d, self._benim_no)
                self.sm.current = 'sonuc'

    # ── CHAT ─────────────────────────────────────────────────────────────────
    @staticmethod
    def _hex(renk):
        return ''.join(f'{int(c * 255):02x}' for c in renk[:3])

    def _sohbet_geldi(self, veri):
        """A chat message arrived from the server."""
        m = {'no': veri.get('no'), 'ad': veri.get('ad', '?'),
             'mesaj': veri.get('mesaj', '')}
        self._sohbet.append(m)
        if self._sohbet_popup is not None:
            self._sohbet_satir_ekle(m)
        else:
            self._okunmamis += 1
            self._sohbet_rozet_guncelle()

    def _sohbet_rozet_guncelle(self):
        try:
            btn = self.sm.get_screen('oyun').sohbet_btn
            btn.text = f'💬 {self._okunmamis}' if self._okunmamis else '💬'
        except Exception:
            pass

    def _sohbet_satir_ekle(self, m):
        if self._sohbet_kutu is None:
            return
        renk = YESIL if m.get('no') == 1 else MAVI
        satir = Label(
            text=f"[color=#{self._hex(renk)}][b]{m['ad']}[/b][/color]: {m['mesaj']}",
            markup=True, font_size=dp(14), color=(0.9, 0.9, 0.9, 1),
            size_hint_y=None, halign='left', valign='top')
        satir.bind(width=lambda i, w: setattr(i, 'text_size', (w, None)))
        satir.bind(texture_size=lambda i, ts: setattr(i, 'height', ts[1] + dp(4)))
        self._sohbet_kutu.add_widget(satir)

    def sohbet_ac(self):
        """Opens the chat window."""
        self._okunmamis = 0
        self._sohbet_rozet_guncelle()

        icerik = BoxLayout(orientation='vertical', spacing=dp(8), padding=dp(8))
        scroll = ScrollView()
        self._sohbet_kutu = BoxLayout(orientation='vertical', size_hint_y=None,
                                      spacing=dp(6), padding=[0, dp(4)])
        self._sohbet_kutu.bind(minimum_height=self._sohbet_kutu.setter('height'))
        scroll.add_widget(self._sohbet_kutu)
        icerik.add_widget(scroll)

        for m in self._sohbet:
            self._sohbet_satir_ekle(m)

        alt = BoxLayout(size_hint_y=None, height=dp(50), spacing=dp(8))
        giris = giris_kutusu('Type a message...', font_size=dp(16))
        gonder = buton('SEND', renk_bg=MAVI, boyut=14)
        gonder.size_hint_x = None
        gonder.width = dp(90)

        def _gonder(*_):
            t = giris.text.strip()
            giris.text = ''
            if t:
                self.net.sohbet_gonder(t)
            giris.focus = True

        giris.bind(on_text_validate=_gonder)
        gonder.bind(on_press=_gonder)
        alt.add_widget(giris)
        alt.add_widget(gonder)
        icerik.add_widget(alt)

        self._sohbet_popup = Popup(
            title='Chat', content=icerik, size_hint=(0.92, 0.8),
            title_color=(1, 1, 1, 1), separator_color=MAVI)

        def _kapandi(*_):
            self._sohbet_popup = None
            self._sohbet_kutu = None

        self._sohbet_popup.bind(on_dismiss=_kapandi)
        self._sohbet_popup.open()
        Clock.schedule_once(lambda dt: setattr(scroll, 'scroll_y', 0), 0.1)

    def on_stop(self):
        self.net.kapat()


if __name__ == '__main__':
    WordChainOnlineApp().run()
