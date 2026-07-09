"""
WORD CHAIN — Online Mobile Client (Kivy)
=========================================
Two-player online word chain game.

İki AYRI dil ayarı vardır (Ayarlar ekranı):
  • Uygulama Dili (app_lang) → arayüz metinleri (i18n.py)
  • Sözlük Dili   (dict_lang) → kelimelerin doğrulandığı dil (sunucu)

Screens:
    baglan  → enter name, create/join room, open settings
    lobi    → waiting for opponent
    oyun    → game driven by server state
    sonuc   → winner + statistics
    ayarlar → app language + word dictionary

Run (desktop test):
    pip install kivy websocket-client requests
    python main.py
"""
import os

from kivy.utils import platform

if platform not in ('android', 'ios'):
    from kivy.config import Config
    Config.set('graphics', 'width', os.environ.get('WC_W', '400'))
    Config.set('graphics', 'height', os.environ.get('WC_H', '720'))
    if os.environ.get('WC_LEFT'):
        Config.set('graphics', 'left', os.environ['WC_LEFT'])
    if os.environ.get('WC_TOP'):
        Config.set('graphics', 'top', os.environ['WC_TOP'])

from kivy.animation import Animation
from kivy.app import App
from kivy.clock import Clock
from kivy.core.window import Window

# 'pan': klavye açılınca pencere yukarı kayar — giriş kutusu HER cihazda görünür
# kalır ('below_target' bazı Android cihazlarda kaydırmıyordu, kelime yazarken
# görünmüyordu).
Window.softinput_mode = 'pan'
from kivy.graphics import Color, RoundedRectangle, Line, Ellipse
from kivy.graphics.texture import Texture
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.recycleboxlayout import RecycleBoxLayout
from kivy.uix.recycleview import RecycleView
from kivy.uix.screenmanager import ScreenManager, Screen, FadeTransition
from kivy.uix.scrollview import ScrollView
from kivy.uix.textinput import TextInput

from network import NetworkClient
from config import SUNUCU_HTTP, SUNUCU_WS
import settings_store
from i18n import t, dil_ayarla, DILLER

Window.clearcolor = (0.06, 0.05, 0.10, 1)

# ── Colors (canlı gradyan tema) ───────────────────────────────────────────────
KOYU    = (0.09, 0.07, 0.14, 1)   # koyu mor-siyah (kart arkası)
GENC    = (0.17, 0.14, 0.24, 1)   # koyu mor (kart / giriş kutusu)
YESIL   = (0.20, 0.92, 0.55, 1)   # canlı yeşil (kazanma / sıra / oyuncu 1)
MAVI    = (0.28, 0.80, 1.0, 1)    # canlı camgöbeği (oyuncu 2)
SARI    = (1.0, 0.80, 0.30, 1)    # altın (süre / vurgu)
KIRMIZI = (1.0, 0.38, 0.45, 1)    # mercan (kaybetme)
# Marka renkleri — gradyan: mor → pembe → turuncu
MOR     = (0.49, 0.23, 0.93, 1)
PEMBE   = (1.0, 0.27, 0.59, 1)
TURUNCU = (1.0, 0.59, 0.20, 1)
GRADYAN = [MOR, PEMBE, TURUNCU]

# Sözlük (kelime doğrulama) dilleri — sunucudaki ALFABELER/words_<kod>.txt ile
# aynı tutulmalı. YENİ SÖZLÜK: buraya kod+ad ekle + sunucuya words_<kod>.txt +
# game_logic.ALFABELER girdisi.
SOZLUK_DILLERI = {
    'en': 'English',
    'tr': 'Türkçe',
    'de': 'Deutsch',
    'es': 'Español',
    'fr': 'Français',
    'ru': 'Русский',
}


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


def pop_anim(widget, base_dp):
    """Etiketin font'unu kısaca küçültüp out_back ile büyüterek 'pop' efekti."""
    Animation.cancel_all(widget, 'font_size')
    widget.font_size = base_dp * 0.5
    Animation(font_size=base_dp, d=0.22, t='out_back').start(widget)


def buton(metin, renk_bg=YESIL, renk_yazi=(0, 0, 0, 1), boyut=17, callback=None):
    btn = Button(text=metin, font_size=dp(boyut), bold=True, color=renk_yazi,
                 background_normal='', background_color=(0, 0, 0, 0))
    kart(btn, renk=renk_bg, radius=14)
    if callback:
        btn.bind(on_press=callback)
    return btn


def secim_butonu(metin, callback, boyut=14):
    """Rengi sonradan değiştirilebilen seçim butonu (Color referansı saklanır)."""
    btn = Button(text=metin, font_size=dp(boyut), bold=True,
                 color=(0.7, 0.7, 0.7, 1),
                 background_normal='', background_color=(0, 0, 0, 0))
    with btn.canvas.before:
        renk = Color(*GENC)
        rect = RoundedRectangle(pos=btn.pos, size=btn.size, radius=[dp(12)])
    btn.bind(pos=lambda *a: setattr(rect, 'pos', btn.pos),
             size=lambda *a: setattr(rect, 'size', btn.size))
    btn._renk = renk
    if callback:
        btn.bind(on_press=callback)
    return btn


def secim_vurgu(btn, secili, renk_secili=YESIL):
    btn._renk.rgba = renk_secili if secili else GENC
    btn.color = (0, 0, 0, 1) if secili else (0.7, 0.7, 0.7, 1)


def giris_kutusu(hint, **kw):
    kw.setdefault('font_size', dp(22))
    ti = TextInput(multiline=False,
                   hint_text=hint, hint_text_color=(0.45, 0.4, 0.55, 1),
                   background_color=GENC, foreground_color=(1, 1, 1, 1),
                   cursor_color=PEMBE, padding=[dp(14), dp(12)], **kw)
    return ti


# ── Gradyan (canlı tema) ───────────────────────────────────────────────────────
def _renk_ara(renkler, t):
    """0..1 arası t için renk listesinde doğrusal interpolasyon (r,g,b)."""
    t = max(0.0, min(1.0, t))
    seg = t * (len(renkler) - 1)
    i = min(int(seg), len(renkler) - 2)
    f = seg - i
    c0, c1 = renkler[i], renkler[i + 1]
    return tuple(c0[j] + (c1[j] - c0[j]) * f for j in range(3))


def _hex3(c):
    return ''.join(f'{int(max(0, min(1, x)) * 255):02x}' for x in c[:3])


def gradyan_doku(renkler, n=64):
    """Soldan sağa renk geçişli yatay gradyan texture."""
    buf = bytearray()
    for x in range(n):
        r, g, b = _renk_ara(renkler, x / (n - 1))
        buf += bytes((int(r * 255), int(g * 255), int(b * 255), 255))
    tex = Texture.create(size=(n, 1), colorfmt='rgba')
    tex.blit_buffer(bytes(buf), colorfmt='rgba', bufferfmt='ubyte')
    tex.wrap = 'clamp_to_edge'
    return tex


def gradyan_buton(metin, renkler=None, boyut=17, renk_yazi=(1, 1, 1, 1),
                  callback=None, radius=14):
    """Gradyan dolgulu birincil buton."""
    renkler = renkler or GRADYAN
    btn = Button(text=metin, font_size=dp(boyut), bold=True, color=renk_yazi,
                 background_normal='', background_color=(0, 0, 0, 0))
    tex = gradyan_doku(renkler)
    with btn.canvas.before:
        Color(1, 1, 1, 1)
        rect = RoundedRectangle(texture=tex, pos=btn.pos, size=btn.size,
                                radius=[dp(radius)])
    btn.bind(pos=lambda *a: setattr(rect, 'pos', btn.pos),
             size=lambda *a: setattr(rect, 'size', btn.size))
    if callback:
        btn.bind(on_press=callback)
    return btn


def gradyan_baslik(metin, renkler=None, boyut=40, **kw):
    """Her harfi gradyan boyunca renklenen başlık etiketi (markup)."""
    renkler = renkler or GRADYAN
    gorunur = [i for i, c in enumerate(metin) if not c.isspace()]
    parcalar = []
    for i, c in enumerate(metin):
        if c.isspace():
            parcalar.append(c)
            continue
        t = gorunur.index(i) / max(1, len(gorunur) - 1)
        parcalar.append(f'[color=#{_hex3(_renk_ara(renkler, t))}]{c}[/color]')
    lbl = Label(text=''.join(parcalar), markup=True, font_size=dp(boyut),
                bold=True, halign='center', valign='middle', **kw)
    lbl.bind(size=lambda *a: setattr(lbl, 'text_size', lbl.size))
    return lbl


# ── İkonlar (canvas ile çizilir; emoji fontuna ihtiyaç yok, her cihazda çalışır) ─
def ikon_buton(ciz_fn, renk_bg=GENC, callback=None, radius=14):
    """Canvas'a vektörel ikon çizilen buton. ciz_fn(btn) ikonu çizer."""
    btn = Button(background_normal='', background_color=(0, 0, 0, 0))
    kart(btn, renk=renk_bg, radius=radius)
    btn.bind(pos=lambda *a: ciz_fn(btn), size=lambda *a: ciz_fn(btn))
    if callback:
        btn.bind(on_press=callback)
    return btn


def ciz_ayar_ikonu(btn, renk=(0.85, 0.85, 0.85, 1)):
    """Ayarlar (kaydırıcı/tune) ikonu: 3 yatay çizgi + birer tutamak."""
    btn.canvas.after.clear()
    w, h = btn.width, btn.height
    m = min(w, h)
    x0 = btn.center_x - m * 0.28
    x1 = btn.center_x + m * 0.28
    r = m * 0.085
    with btn.canvas.after:
        for ry, kf in ((0.66, 0.72), (0.5, 0.34), (0.34, 0.62)):
            yy = btn.y + h * ry
            Color(*renk)
            Line(points=[x0, yy, x1, yy], width=dp(1.6))
            kx = x0 + (x1 - x0) * kf
            Color(*GENC)                      # tutamak içi (arka plan rengi)
            Ellipse(pos=(kx - r, yy - r), size=(2 * r, 2 * r))
            Color(*renk)
            Line(circle=(kx, yy, r), width=dp(1.6))


def ciz_sohbet_ikonu(btn, renk=(0, 0, 0, 1)):
    """Konuşma balonu ikonu + okunmamış varsa kırmızı nokta rozeti."""
    btn.canvas.after.clear()
    m = min(btn.width, btn.height)
    bw, bh = m * 0.60, m * 0.46
    x = btn.center_x - bw / 2
    y = btn.center_y - bh / 2 + m * 0.05
    with btn.canvas.after:
        Color(*renk)
        Line(rounded_rectangle=(x, y, bw, bh, m * 0.12), width=dp(1.8))
        Line(points=[x + bw * 0.24, y, x + bw * 0.12, y - m * 0.13,
                     x + bw * 0.42, y], width=dp(1.8))
        dr = m * 0.035
        for k in range(3):
            dx = x + bw * 0.28 + k * bw * 0.22
            Ellipse(pos=(dx - dr, btn.center_y + m * 0.05 - dr),
                    size=(2 * dr, 2 * dr))
        if getattr(btn, '_rozet', False):     # okunmamış mesaj göstergesi
            br = m * 0.13
            Color(*KIRMIZI)
            Ellipse(pos=(btn.right - br * 2.0, btn.top - br * 2.0),
                    size=(2 * br, 2 * br))


class AnlamLabel(Label):
    """[ref=kelime] işaretli metin — kelimeye dokununca anlam penceresi açılır.
    RecycleView viewclass olarak da kullanılır (Factory kaydı aşağıda)."""
    def on_ref_press(self, ref):
        App.get_running_app().anlam_ac(ref)


from kivy.factory import Factory  # noqa: E402  (AnlamLabel tanımından sonra)
Factory.register('AnlamLabel', cls=AnlamLabel)


def ciz_liste_ikonu(btn, renk=(0, 0, 0, 1)):
    """Kelime listesi ikonu: madde imli 3 satır."""
    btn.canvas.after.clear()
    m = min(btn.width, btn.height)
    x0 = btn.center_x - m * 0.26
    x1 = btn.center_x + m * 0.28
    r = m * 0.045
    with btn.canvas.after:
        Color(*renk)
        for ry in (0.66, 0.5, 0.34):
            yy = btn.y + btn.height * ry
            Ellipse(pos=(x0 - r, yy - r), size=(2 * r, 2 * r))
            Line(points=[x0 + m * 0.12, yy, x1, yy], width=dp(1.8))


# ══════════════════════════════════════════════════════════════════════════════
#  1. CONNECT SCREEN
# ══════════════════════════════════════════════════════════════════════════════
class BaglanEkrani(Screen):
    def __init__(self, **kw):
        super().__init__(**kw)
        kok = BoxLayout(orientation='vertical', padding=dp(24), spacing=dp(14))
        kart(kok, renk=KOYU)

        # Üst satır: başlık + ayarlar butonu (telefonda üst köşeye çok
        # yakın olmasın diye ayrıca aşağı kaydırıldı — başparmakla ulaşmak zor)
        kok.add_widget(Label(size_hint_y=None, height=dp(22)))
        ust = BoxLayout(size_hint_y=None, height=dp(34))
        ust.add_widget(Label())  # esnek boşluk
        sss_btn = buton('?', renk_bg=GENC, renk_yazi=(0.85, 0.85, 0.85, 1), boyut=18,
                        callback=lambda *_: App.get_running_app().faq_ac())
        sss_btn.size_hint_x = None
        sss_btn.width = dp(44)
        ust.add_widget(sss_btn)
        ust.add_widget(Label(size_hint_x=None, width=dp(8)))
        ayar_btn = ikon_buton(ciz_ayar_ikonu, renk_bg=GENC,
                              callback=lambda *_: App.get_running_app().ayarlari_ac())
        ayar_btn.size_hint_x = None
        ayar_btn.width = dp(44)
        ust.add_widget(ayar_btn)
        kok.add_widget(ust)

        baslik = gradyan_baslik('LEXICOIL', boyut=40)
        baslik.size_hint_y = None
        baslik.height = dp(96)
        kok.add_widget(baslik)
        kok.add_widget(etiket(t('subtitle'), boyut=14,
                              renk=(0.62, 0.55, 0.72, 1), hizala='center'))

        kok.add_widget(Label(size_hint_y=None, height=dp(6)))

        self.ad_giris = giris_kutusu(t('your_name'), size_hint_y=None, height=dp(52))
        kok.add_widget(self.ad_giris)

        # Süre seçeneği
        self._secili_sure = 300
        kok.add_widget(etiket(t('game_duration'), boyut=12, renk=(0.5, 0.5, 0.5, 1),
                              hizala='left', size_hint_y=None, height=dp(18)))
        sure_satir = BoxLayout(size_hint_y=None, height=dp(42), spacing=dp(8))
        self._sure_butonlar = {}
        for anahtar, saniye in [('dur_3', 180), ('dur_5', 300), ('dur_10', 600)]:
            b = secim_butonu(t(anahtar), lambda _b, s=saniye: self._sure_sec(s))
            self._sure_butonlar[saniye] = b
            sure_satir.add_widget(b)
        kok.add_widget(sure_satir)
        self._sure_sec(300)

        cr_btn = gradyan_buton(t('create_room'), callback=self.oda_olustur)
        cr_btn.size_hint_y = None
        cr_btn.height = dp(54)
        kok.add_widget(cr_btn)
        kok.add_widget(etiket(t('or'), boyut=12, renk=(0.45, 0.4, 0.55, 1)))

        self.kod_giris = giris_kutusu(t('room_code_hint'),
                                      size_hint_y=None, height=dp(52))
        kok.add_widget(self.kod_giris)
        kok.add_widget(buton(t('join_with_code'), renk_bg=MAVI, callback=self.katil))

        kok.add_widget(Label(size_hint_y=None, height=dp(2)))
        solo_btn = buton(t('solo_play'), renk_bg=MOR,
                         callback=lambda *_: self._solo_popup())
        solo_btn.size_hint_y = None
        solo_btn.height = dp(50)
        kok.add_widget(solo_btn)

        self.durum = etiket('', boyut=13, renk=SARI)
        self.durum.size_hint_y = None
        self.durum.height = dp(28)
        kok.add_widget(self.durum)

        kok.add_widget(Label())
        self.add_widget(kok)

    @property
    def net(self):
        return App.get_running_app().net

    def _ad(self):
        return self.ad_giris.text.strip() or t('player')

    def _solo_popup(self):
        """Offline oyun seçimi: İki kişi (tek telefon) + Bota karşı + Antrenman."""
        icerik = BoxLayout(orientation='vertical', spacing=dp(10), padding=dp(16))
        pop = Popup(title=t('solo_title'), content=icerik, size_hint=(0.9, None),
                    height=dp(580), title_color=(1, 1, 1, 1), separator_color=MOR)

        # ── İki kişi — tek telefon (elden ele) ──
        icerik.add_widget(etiket(t('pass_and_play'), boyut=15, kalin=True, renk=TURUNCU,
                                 size_hint_y=None, height=dp(26)))
        p2_giris = giris_kutusu(t('player2_name'), size_hint_y=None, height=dp(46),
                                font_size=dp(16))
        icerik.add_widget(p2_giris)
        ik = buton(t('two_players'), renk_bg=TURUNCU, renk_yazi=(0, 0, 0, 1), boyut=14)
        ik.size_hint_y = None
        ik.height = dp(50)
        ik.bind(on_press=lambda _b: (
            pop.dismiss(), App.get_running_app().iki_kisi_basla(p2_giris.text)))
        icerik.add_widget(ik)

        # ── Bota karşı ──
        icerik.add_widget(etiket(t('vs_bot'), boyut=17, kalin=True, renk=PEMBE,
                                 size_hint_y=None, height=dp(30)))
        icerik.add_widget(etiket(t('difficulty'), boyut=12, renk=(0.6, 0.6, 0.6, 1),
                                 size_hint_y=None, height=dp(20)))
        for kod, etik, renk in (('kolay', t('easy'), YESIL),
                                ('orta', t('medium'), SARI),
                                ('zor', t('hard'), KIRMIZI)):
            b = buton(etik, renk_bg=renk, renk_yazi=(0, 0, 0, 1))
            b.size_hint_y = None
            b.height = dp(50)
            b.bind(on_press=lambda _b, z=kod: (
                pop.dismiss(), App.get_running_app().bota_karsi_basla(z)))
            icerik.add_widget(b)

        # ── Antrenman (solo) ──
        icerik.add_widget(etiket(t('training'), boyut=15, kalin=True, renk=MOR,
                                 size_hint_y=None, height=dp(26)))
        tb = buton(t('training_desc'), renk_bg=GENC, renk_yazi=(0.85, 0.85, 0.85, 1),
                   boyut=13)
        tb.size_hint_y = None
        tb.height = dp(50)
        tb.bind(on_press=lambda _b: (
            pop.dismiss(), App.get_running_app().training_basla()))
        icerik.add_widget(tb)
        icerik.add_widget(Label())
        pop.open()

    def _sure_sec(self, saniye):
        self._secili_sure = saniye
        for s, b in self._sure_butonlar.items():
            secim_vurgu(b, s == saniye)

    def oda_olustur(self, *_):
        self.durum.text = t('creating_room')
        self.durum.color = SARI
        app = App.get_running_app()

        def geldi(kod):
            if kod:
                app.baglan_ve_gec(kod, self._ad())
            else:
                self.durum.text = t('no_server')
                self.durum.color = KIRMIZI

        self.net.oda_olustur(geldi, sure=self._secili_sure,
                             dil=app.ayar['dict_lang'])

    def katil(self, *_):
        kod = self.kod_giris.text.strip().upper()
        if len(kod) < 3:
            self.durum.text = t('invalid_code')
            self.durum.color = KIRMIZI
            return
        self.durum.text = t('connecting')
        self.durum.color = SARI
        App.get_running_app().baglan_ve_gec(kod, self._ad())


# ══════════════════════════════════════════════════════════════════════════════
#  2. LOBBY SCREEN
# ══════════════════════════════════════════════════════════════════════════════
class LobiEkrani(Screen):
    def __init__(self, **kw):
        super().__init__(**kw)
        kok = BoxLayout(orientation='vertical', padding=dp(28), spacing=dp(14))
        kart(kok, renk=KOYU)

        kok.add_widget(Label(size_hint_y=None, height=dp(10)))
        kok.add_widget(etiket(t('room_code'), boyut=14, renk=(0.5, 0.5, 0.5, 1),
                              size_hint_y=None, height=dp(20)))
        self.kod_lbl = etiket('----', boyut=56, kalin=True, renk=YESIL)
        self.kod_lbl.size_hint_y = None
        self.kod_lbl.height = dp(80)
        kok.add_widget(self.kod_lbl)
        self.alt_bilgi = etiket(t('share_code'), boyut=13, renk=(0.6, 0.6, 0.6, 1),
                                size_hint_y=None, height=dp(20))
        kok.add_widget(self.alt_bilgi)

        kok.add_widget(Label(size_hint_y=None, height=dp(14)))

        # Dinamik orta alan: bekleme  ↔  hazır+geri sayım+chat
        self._orta = BoxLayout(orientation='vertical', spacing=dp(8))
        kok.add_widget(self._orta)

        kok.add_widget(buton(t('cancel'), renk_bg=GENC, renk_yazi=(0.8, 0.8, 0.8, 1),
                             callback=lambda *_: App.get_running_app().odadan_cik()))
        kok.add_widget(Label(size_hint_y=None, height=dp(10)))
        self.add_widget(kok)
        self._hazir_kuruldu = False
        self._bekleme_goster()

    def kodu_ayarla(self, kod):
        self.kod_lbl.text = kod
        self._bekleme_goster()

    def _bekleme_goster(self):
        """Tek başına rakip bekleme durumu."""
        self._hazir_kuruldu = False
        self.alt_bilgi.text = t('share_code')
        self._orta.clear_widgets()
        self._orta.add_widget(Label())
        self._orta.add_widget(etiket(t('waiting_opponent'), boyut=16, renk=SARI,
                                     size_hint_y=None, height=dp(28)))
        self._orta.add_widget(Label())

    def hazir_guncelle(self, d):
        """İkisi de katıldı: isimler + geri sayım + chat (kısa lobi)."""
        oyuncular = d.get('oyuncular', {})
        n = d.get('geri_sayim')
        n = max(0, n) if n is not None else 0
        if not self._hazir_kuruldu:
            self._hazir_kuruldu = True
            self.alt_bilgi.text = ''
            self._orta.clear_widgets()
            self._orta.add_widget(Label(size_hint_y=None, height=dp(4)))
            isimler = BoxLayout(size_hint_y=None, height=dp(40), spacing=dp(6))
            isimler.add_widget(etiket(oyuncular.get('1', f"{t('player')} 1"),
                                      boyut=17, kalin=True, renk=YESIL))
            isimler.add_widget(etiket('vs', boyut=13, renk=(0.5, 0.5, 0.5, 1),
                                      size_hint_x=None, width=dp(34)))
            isimler.add_widget(etiket(oyuncular.get('2', f"{t('player')} 2"),
                                      boyut=17, kalin=True, renk=MAVI))
            self._orta.add_widget(isimler)
            self._orta.add_widget(etiket(t('get_ready'), boyut=15,
                                         renk=(0.6, 0.6, 0.6, 1),
                                         size_hint_y=None, height=dp(22)))
            self._geri_lbl = etiket(t('starting_in', n=n), boyut=18, kalin=True,
                                    renk=SARI, size_hint_y=None, height=dp(30))
            self._orta.add_widget(self._geri_lbl)
            self._orta.add_widget(Label(size_hint_y=None, height=dp(6)))
            chat = ikon_buton(ciz_sohbet_ikonu, renk_bg=MAVI,
                              callback=lambda *_: App.get_running_app().sohbet_ac())
            chat.size_hint = (None, None)
            chat.width = dp(60)
            chat.height = dp(48)
            chat.pos_hint = {'center_x': 0.5}
            self._orta.add_widget(chat)
            self._orta.add_widget(etiket(t('lobby_chat_hint'), boyut=11,
                                         renk=(0.45, 0.45, 0.45, 1),
                                         size_hint_y=None, height=dp(16)))
            self._orta.add_widget(Label())
        else:
            # Sadece geri sayım sayısını güncelle (her saniye).
            self._geri_lbl.text = t('starting_in', n=n)


# ══════════════════════════════════════════════════════════════════════════════
#  3. GAME SCREEN
# ══════════════════════════════════════════════════════════════════════════════
class OyunEkrani(Screen):
    def __init__(self, **kw):
        super().__init__(**kw)
        self._benim_no = 1
        self._hotseat = False

        kok = BoxLayout(orientation='vertical', padding=dp(18), spacing=dp(10))
        kart(kok, renk=KOYU)

        # Üst butonlar durum çubuğunun (saat/pil) altında kalmasın — bazı
        # cihazlarda pencere çentik alanına taşıyor, basılamıyordu.
        kok.add_widget(Label(size_hint_y=None, height=dp(26)))
        ust = BoxLayout(size_hint_y=None, height=dp(44))
        self.toplam_lbl = etiket('05:00', boyut=20, kalin=True,
                                 renk=(0.5, 0.5, 0.5, 1), hizala='left')
        self.kelime_lbl = etiket(t('words_count', n=0), boyut=12,
                                 renk=(0.4, 0.4, 0.4, 1))
        self.liste_btn = ikon_buton(ciz_liste_ikonu, renk_bg=MOR,
                                    callback=lambda *_: self._kelime_listesi())
        self.liste_btn.size_hint_x = None
        self.liste_btn.width = dp(52)
        self.sohbet_btn = ikon_buton(ciz_sohbet_ikonu, renk_bg=MAVI,
                                     callback=lambda *_: App.get_running_app().sohbet_ac())
        self.sohbet_btn.size_hint_x = None
        self.sohbet_btn.width = dp(52)
        cik = buton(t('quit'), renk_bg=GENC, renk_yazi=(0.6, 0.6, 0.6, 1), boyut=12,
                    callback=lambda *_: App.get_running_app().odadan_cik())
        cik.size_hint_x = None
        cik.width = dp(64)
        ust.add_widget(self.toplam_lbl)
        ust.add_widget(self.kelime_lbl)
        ust.add_widget(self.liste_btn)
        ust.add_widget(self.sohbet_btn)
        ust.add_widget(cik)
        kok.add_widget(ust)

        # Kelime zinciri
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
        self._zincir_son = []

        oyuncu_satir = BoxLayout(size_hint_y=None, height=dp(86), spacing=dp(12))
        self.p1_kutu = BoxLayout(orientation='vertical', spacing=dp(4), padding=dp(10))
        kart(self.p1_kutu, renk=GENC)
        self.p1_ad = etiket(f"{t('player')} 1", boyut=11, kalin=True, renk=YESIL)
        self.p1_puan = etiket('0', boyut=34, kalin=True)
        self.p1_kutu.add_widget(self.p1_ad)
        self.p1_kutu.add_widget(self.p1_puan)

        self.p2_kutu = BoxLayout(orientation='vertical', spacing=dp(4), padding=dp(10))
        kart(self.p2_kutu, renk=GENC)
        self.p2_ad = etiket(f"{t('player')} 2", boyut=11, kalin=True, renk=MAVI)
        self.p2_puan = etiket('0', boyut=34, kalin=True)
        self.p2_kutu.add_widget(self.p2_ad)
        self.p2_kutu.add_widget(self.p2_puan)

        oyuncu_satir.add_widget(self.p1_kutu)
        oyuncu_satir.add_widget(self.p2_kutu)
        kok.add_widget(oyuncu_satir)

        self.tur_lbl = etiket('', boyut=14, renk=(0.6, 0.6, 0.6, 1))
        self.tur_lbl.size_hint_y = None
        self.tur_lbl.height = dp(24)
        kok.add_widget(self.tur_lbl)

        self.harf_lbl = etiket('?', boyut=72, kalin=True, renk=PEMBE)
        self.harf_lbl.size_hint_y = None
        self.harf_lbl.height = dp(110)
        kok.add_widget(self.harf_lbl)

        self.hamle_lbl = etiket('20', boyut=24, kalin=True, renk=YESIL)
        self.hamle_lbl.size_hint_y = None
        self.hamle_lbl.height = dp(34)
        kok.add_widget(self.hamle_lbl)

        self.son_lbl = etiket('', boyut=13, renk=(0.4, 0.4, 0.4, 1))
        self.son_lbl.size_hint_y = None
        self.son_lbl.height = dp(22)
        kok.add_widget(self.son_lbl)

        kok.add_widget(Label())

        self.durum_lbl = etiket('', boyut=15, kalin=True, renk=SARI)
        self.durum_lbl.size_hint_y = None
        self.durum_lbl.height = dp(28)
        kok.add_widget(self.durum_lbl)

        self.giris = giris_kutusu(t('type_word'), size_hint_y=None, height=dp(56),
                                  font_size=dp(26))
        self.giris.bind(on_text_validate=lambda *_: self._gonder())
        kok.add_widget(self.giris)

        self.gonder_btn = buton(t('send'), callback=lambda *_: self._gonder())
        self.gonder_btn.size_hint_y = None
        self.gonder_btn.height = dp(56)
        kok.add_widget(self.gonder_btn)

        kok.add_widget(Label(size_hint_y=None, height=dp(6)))
        self.add_widget(kok)

    def benim_no_ayarla(self, no):
        self._benim_no = no

    def sohbet_goster(self, goster):
        """Sohbet butonunu göster/gizle (offline modda rakip olmadığı için gizli)."""
        self.sohbet_btn.opacity = 1 if goster else 0
        self.sohbet_btn.disabled = not goster

    def training_mode(self, aktif):
        """Solo antrenmanda rakip (P2) kutusunu gizle, P1 tüm satırı kaplasın."""
        self.p2_kutu.size_hint_x = 0.001 if aktif else 1
        self.p2_kutu.opacity = 0 if aktif else 1

    def hotseat_mode(self, aktif):
        """İki kişi — tek telefon (elden ele): giriş her turda açık kalır,
        sıradaki oyuncunun adı gösterilir."""
        self._hotseat = aktif

    def _gonder(self):
        kelime = self.giris.text.strip().lower()
        self.giris.text = ''
        if kelime:
            App.get_running_app().kelime_gonder(kelime)

    def kelime_sonuc(self, basari, kod, harf, puan):
        if kod == 'points':
            mesaj = t('msg_points', points=puan)
        elif kod == 'must_start':
            mesaj = t('msg_must_start', letter=(harf or '').upper())
        else:
            mesaj = t('msg_' + kod)
        self.durum_lbl.text = mesaj
        self.durum_lbl.color = YESIL if basari else KIRMIZI

    def durum_guncelle(self, d):
        m, s = divmod(int(d['toplam_sure']), 60)
        self.toplam_lbl.text = f'{m:02d}:{s:02d}'
        self.kelime_lbl.text = t('words_count', n=d['kelime_sayisi'])

        yeni_harf = d['gerekli_harf'].upper()
        if yeni_harf != self.harf_lbl.text:   # harf değişti -> pop
            self.harf_lbl.text = yeni_harf
            pop_anim(self.harf_lbl, dp(72))

        tt = int(d['hamle_sure'])
        self.hamle_lbl.text = str(tt)
        if tt > 10:
            self.hamle_lbl.color = YESIL
        elif tt > 5:
            self.hamle_lbl.color = SARI
        else:
            self.hamle_lbl.color = KIRMIZI

        self.son_lbl.text = t('last', word=d['son_kelime']) if d['son_kelime'] else ''

        self._zincir_guncelle(d.get('zincir', []))

        oyuncular = d.get('oyuncular', {})
        self.p1_ad.text = oyuncular.get('1', f"{t('player')} 1")
        self.p2_ad.text = oyuncular.get('2', f"{t('player')} 2")
        for lbl, yeni in ((self.p1_puan, str(d['puan']['1'])),
                          (self.p2_puan, str(d['puan']['2']))):
            if yeni != lbl.text:        # puan değişti -> pop
                lbl.text = yeni
                pop_anim(lbl, dp(34))

        sira = d['siradaki_no']
        benim_sira = (sira == self._benim_no)
        self._kart_vurgu(self.p1_kutu, sira == 1, YESIL)
        self._kart_vurgu(self.p2_kutu, sira == 2, MAVI)

        if self._hotseat:
            # Elden ele: telefon iki oyuncunun elinde — giriş hep açık,
            # sıradaki oyuncunun adı kendi rengiyle gösterilir.
            ad = oyuncular.get(str(sira), f"{t('player')} {sira}")
            self.tur_lbl.text = t('turn_of', name=ad)
            self.tur_lbl.color = YESIL if sira == 1 else MAVI
            self.giris.disabled = False
            self.gonder_btn.disabled = False
            self.gonder_btn.opacity = 1
        elif benim_sira:
            self.tur_lbl.text = t('your_turn')
            self.tur_lbl.color = YESIL
            self.giris.disabled = False
            self.gonder_btn.disabled = False
            self.gonder_btn.opacity = 1
        else:
            ad = oyuncular.get(str(sira), f"{t('player')} {sira}")
            self.tur_lbl.text = t('is_playing', name=ad)
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

    def _kelime_listesi(self):
        App.get_running_app().kelime_listesi_ac(self._zincir_son)

    def _zincir_guncelle(self, zincir):
        self._zincir_son = zincir
        if len(zincir) == self._zincir_uzunluk:
            return
        self._zincir_uzunluk = len(zincir)
        self.zincir_kutu.clear_widgets()

        if not zincir:
            bos = Label(text=t('no_words_yet'), font_size=dp(12),
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
        if d.get('mod') == 'training':
            self._goster_training(d)
            return
        p1, p2 = d['puan']['1'], d['puan']['2']
        kazanan = d.get('kazanan')
        ayrilan = d.get('ayrilan_ad')

        if d.get('mod') == 'hotseat' and kazanan not in (0, None):
            # Elden ele: "sen kazandın" yerine kazananın adı gösterilir.
            ad = d.get('oyuncular', {}).get(str(kazanan), f"{t('player')} {kazanan}")
            yazi = t('won_name', name=ad)
            renk = YESIL if kazanan == 1 else MAVI
        elif ayrilan:
            # Rakip oyundan ayrıldı -> ayrılan kaybeder, kalan oyuncu kazanır.
            yazi, renk = t('you_won'), YESIL
        elif kazanan == 0 or kazanan is None:
            yazi, renk = t('draw'), SARI
        elif kazanan == benim_no:
            yazi, renk = t('you_won'), YESIL
        else:
            yazi, renk = t('you_lost'), KIRMIZI

        self._kok.add_widget(Label(size_hint_y=None, height=dp(16)))
        self._kok.add_widget(etiket(t('game_over'), boyut=13, renk=(0.5, 0.5, 0.5, 1)))
        baslik_lbl = etiket(yazi, boyut=32, kalin=True, renk=renk)
        self._kok.add_widget(baslik_lbl)
        baslik_lbl.font_size = dp(12)        # büyüyerek gelsin
        Animation(font_size=dp(32), d=0.32, t='out_back').start(baslik_lbl)
        if ayrilan:
            self._kok.add_widget(etiket(t('left_game', name=ayrilan), boyut=13,
                                        renk=(0.6, 0.6, 0.6, 1)))

        oyuncular = d.get('oyuncular', {})
        # Kutu yüksekliği + sabit isim/pts yükseklikleri: büyük puan sayısı
        # esnek orta alanı doldurur, hiçbir cihazda kırpılmadan tam görünür.
        kutular = BoxLayout(size_hint_y=None, height=dp(120), spacing=dp(14))
        for no, c in [(1, YESIL), (2, MAVI)]:
            kutu = BoxLayout(orientation='vertical', spacing=dp(2), padding=dp(10))
            kart(kutu, renk=GENC)
            kutu.add_widget(etiket(oyuncular.get(str(no), f"{t('player')} {no}"),
                                   boyut=12, kalin=True, renk=c,
                                   size_hint_y=None, height=dp(20)))
            kutu.add_widget(etiket(str(d['puan'][str(no)]), boyut=40, kalin=True))
            kutu.add_widget(etiket(t('pts'), boyut=12, renk=(0.5, 0.5, 0.5, 1),
                                   size_hint_y=None, height=dp(16)))
            kutular.add_widget(kutu)
        self._kok.add_widget(kutular)

        toplam = p1 + p2
        sayi = d['kelime_sayisi']
        ort = f'{toplam/sayi:.1f}' if sayi else '0'
        istat = BoxLayout(size_hint_y=None, height=dp(64), padding=dp(12))
        kart(istat, renk=GENC)
        for deger, ad in [(str(sayi), t('words')), (str(toplam), t('total')),
                          (ort, t('avg'))]:
            k = BoxLayout(orientation='vertical')
            k.add_widget(etiket(deger, boyut=24, kalin=True))
            k.add_widget(etiket(ad, boyut=10, renk=(0.5, 0.5, 0.5, 1)))
            istat.add_widget(k)
        self._kok.add_widget(istat)

        zincir = d.get('zincir', [])
        kl_btn = buton(f"{t('words_used')} ({len(zincir)})", renk_bg=MOR, boyut=14,
                       callback=lambda *_:
                       App.get_running_app().kelime_listesi_ac(zincir))
        kl_btn.size_hint_y = None
        kl_btn.height = dp(46)
        self._kok.add_widget(kl_btn)

        self._rematch_durum = etiket('', boyut=13, kalin=True, renk=SARI,
                                     size_hint_y=None, height=dp(24))
        self._kok.add_widget(self._rematch_durum)

        self._kok.add_widget(Label())

        if not ayrilan:
            self._rematch_btn = gradyan_buton(t('play_again'),
                                              callback=lambda *_: self._rematch_iste())
            self._rematch_btn.size_hint_y = None
            self._rematch_btn.height = dp(54)
            self._kok.add_widget(self._rematch_btn)
        else:
            self._rematch_btn = None

        self._kok.add_widget(buton(t('main_menu'), renk_bg=GENC,
                                   renk_yazi=(0.8, 0.8, 0.8, 1),
                                   callback=lambda *_: App.get_running_app().odadan_cik()))
        self._kok.add_widget(Label(size_hint_y=None, height=dp(12)))

    def _goster_training(self, d):
        """Solo antrenman sonucu: skor + en iyi skor."""
        app = App.get_running_app()
        skor = d['puan']['1']
        eniyi = app.en_iyi(d.get('dict_lang', 'en'))

        self._kok.add_widget(Label(size_hint_y=None, height=dp(16)))
        self._kok.add_widget(etiket(t('game_over'), boyut=13, renk=(0.5, 0.5, 0.5, 1),
                                    size_hint_y=None, height=dp(20)))
        self._kok.add_widget(etiket(t('training'), boyut=22, kalin=True, renk=PEMBE,
                                    size_hint_y=None, height=dp(34)))
        skor_lbl = etiket(str(skor), boyut=64, kalin=True, renk=YESIL,
                          size_hint_y=None, height=dp(92))
        self._kok.add_widget(skor_lbl)
        skor_lbl.font_size = dp(20)
        Animation(font_size=dp(64), d=0.35, t='out_back').start(skor_lbl)
        self._kok.add_widget(etiket(t('pts'), boyut=13, renk=(0.5, 0.5, 0.5, 1),
                                    size_hint_y=None, height=dp(20)))
        self._kok.add_widget(etiket(t('best_score', n=eniyi), boyut=16, kalin=True,
                                    renk=SARI, size_hint_y=None, height=dp(30)))

        self._kok.add_widget(Label(size_hint_y=None, height=dp(10)))
        zincir = d.get('zincir', [])
        kl_btn = buton(f"{t('words_used')} ({len(zincir)})", renk_bg=MOR, boyut=14,
                       callback=lambda *_:
                       App.get_running_app().kelime_listesi_ac(zincir))
        kl_btn.size_hint_y = None
        kl_btn.height = dp(46)
        self._kok.add_widget(kl_btn)

        self._kok.add_widget(Label())
        self._rematch_btn = gradyan_buton(t('play_again'),
                                          callback=lambda *_: self._rematch_iste())
        self._rematch_btn.size_hint_y = None
        self._rematch_btn.height = dp(54)
        self._kok.add_widget(self._rematch_btn)
        self._kok.add_widget(buton(t('main_menu'), renk_bg=GENC,
                                   renk_yazi=(0.8, 0.8, 0.8, 1),
                                   callback=lambda *_: App.get_running_app().odadan_cik()))
        self._kok.add_widget(Label(size_hint_y=None, height=dp(12)))

    def _rematch_iste(self):
        app = App.get_running_app()
        if app.offline:
            app.rematch_iste()          # offline: anında yeni oyun
            return
        app.net.rematch_iste()
        self._rematch_durum.text = t('waiting_opponent')
        if self._rematch_btn:
            self._rematch_btn.disabled = True
            self._rematch_btn.opacity = 0.5

    def guncelle(self, d):
        if d.get('ayrilan_ad') and getattr(self, '_rematch_btn', None):
            self.goster(d, self._benim_no)
            return
        sayi = d.get('rematch_sayisi', 0)
        if sayi == 1 and hasattr(self, '_rematch_durum'):
            if self._rematch_btn and not self._rematch_btn.disabled:
                self._rematch_durum.text = t('opponent_wants_rematch')
                self._rematch_durum.color = YESIL


# ══════════════════════════════════════════════════════════════════════════════
#  5. SETTINGS SCREEN — App Language + Word Dictionary (two sections)
# ══════════════════════════════════════════════════════════════════════════════
class AyarlarEkrani(Screen):
    def __init__(self, **kw):
        super().__init__(**kw)
        dis = BoxLayout(orientation='vertical', padding=dp(16), spacing=dp(10))
        kart(dis, renk=KOYU)
        # Kaydırılabilir içerik (dil sayısı arttıkça taşmasın diye)
        scroll = ScrollView(do_scroll_x=False)
        self._kok = BoxLayout(orientation='vertical', spacing=dp(10),
                              padding=[dp(8), dp(8)], size_hint_y=None)
        self._kok.bind(minimum_height=self._kok.setter('height'))
        scroll.add_widget(self._kok)
        dis.add_widget(scroll)
        # Sabit DONE butonu — liste uzasa da her zaman erişilebilir kalır
        done_btn = buton(t('done'), boyut=15,
                         callback=lambda *_: App.get_running_app().ana_menuye())
        done_btn.size_hint = (None, None)
        done_btn.height = dp(44)
        done_btn.width = dp(200)
        done_btn.pos_hint = {'center_x': 0.5}
        dis.add_widget(done_btn)
        dis.add_widget(Label(size_hint_y=None, height=dp(8)))
        self.add_widget(dis)
        self.kur()

    def kur(self):
        """Ekranı aktif dile göre (yeniden) oluşturur."""
        self._kok.clear_widgets()
        app = App.get_running_app()

        self._kok.add_widget(Label(size_hint_y=None, height=dp(16)))
        self._kok.add_widget(etiket(t('settings_title'), boyut=24, kalin=True,
                                    renk=YESIL, size_hint_y=None, height=dp(36)))

        # ── İstatistikler + Ses (yan yana) ──
        ust_satir = BoxLayout(size_hint_y=None, height=dp(46), spacing=dp(8))
        ist_btn = buton(t('statistics'), renk_bg=MOR, boyut=14,
                        callback=lambda *_: self._istatistik_popup())
        ust_satir.add_widget(ist_btn)
        self._ses_btn = secim_butonu(t('sound'), lambda _b: self._ses_toggle(), boyut=14)
        secim_vurgu(self._ses_btn, app.ayar.get('sound', True))
        ust_satir.add_widget(self._ses_btn)
        self._kok.add_widget(ust_satir)

        # ── Nasıl Oynanır / SSS + Tüm Kelimeler (sözlük tarayıcı) ──
        alt_satir = BoxLayout(size_hint_y=None, height=dp(46), spacing=dp(8))
        sss_btn = buton(t('how_to_play'), renk_bg=TURUNCU, boyut=14,
                        callback=lambda *_: app.faq_ac())
        alt_satir.add_widget(sss_btn)
        sozluk_btn = buton(t('all_words'), renk_bg=MAVI, boyut=14,
                           callback=lambda *_: app.sozluk_ac())
        alt_satir.add_widget(sozluk_btn)
        self._kok.add_widget(alt_satir)
        self._kok.add_widget(Label(size_hint_y=None, height=dp(8)))

        # ── BÖLÜM 1: Uygulama Dili ──
        self._kok.add_widget(etiket(t('app_language'), boyut=15, kalin=True,
                                    hizala='left', size_hint_y=None, height=dp(24)))
        self._kok.add_widget(etiket(t('app_language_desc'), boyut=11,
                                    renk=(0.5, 0.5, 0.5, 1), hizala='left',
                                    size_hint_y=None, height=dp(16)))
        self._app_butonlar = {}
        for kod, ad in DILLER.items():
            b = secim_butonu(ad, lambda _b, k=kod: self._app_dili_sec(k), boyut=15)
            b.size_hint_y = None
            b.height = dp(46)
            secim_vurgu(b, kod == app.ayar['app_lang'])
            self._app_butonlar[kod] = b
            self._kok.add_widget(b)

        self._kok.add_widget(Label(size_hint_y=None, height=dp(8)))

        # ── BÖLÜM 2: Sözlük (kelime doğrulama) ──
        self._kok.add_widget(etiket(t('word_dictionary'), boyut=15, kalin=True,
                                    hizala='left', size_hint_y=None, height=dp(24)))
        self._kok.add_widget(etiket(t('word_dictionary_desc'), boyut=11,
                                    renk=(0.5, 0.5, 0.5, 1), hizala='left',
                                    size_hint_y=None, height=dp(16)))
        self._sozluk_butonlar = {}
        for kod, ad in SOZLUK_DILLERI.items():
            b = secim_butonu(ad, lambda _b, k=kod: self._sozluk_dili_sec(k), boyut=15)
            b.size_hint_y = None
            b.height = dp(46)
            secim_vurgu(b, kod == app.ayar['dict_lang'], renk_secili=MAVI)
            self._sozluk_butonlar[kod] = b
            self._kok.add_widget(b)

        self._kok.add_widget(Label(size_hint_y=None, height=dp(8)))

    def _app_dili_sec(self, kod):
        App.get_running_app().app_dili_degistir(kod)

    def _sozluk_dili_sec(self, kod):
        app = App.get_running_app()
        app.sozluk_dili_degistir(kod)
        for k, b in self._sozluk_butonlar.items():
            secim_vurgu(b, k == kod, renk_secili=MAVI)

    def _ses_toggle(self):
        app = App.get_running_app()
        yeni = not app.ayar.get('sound', True)
        app.ayar['sound'] = yeni
        app.sesler.acik = yeni
        settings_store.kaydet(app.user_data_dir, app.ayar)
        secim_vurgu(self._ses_btn, yeni)
        if yeni:
            app.sesler.cal('success')   # açınca örnek ses

    def _istatistik_popup(self):
        app = App.get_running_app()
        st = app.istatistik()
        g = st.get('games', 0)
        w, l, dr = st.get('wins', 0), st.get('losses', 0), st.get('draws', 0)
        oran = f'{round(100 * w / g)}%' if g else '—'
        satirlar = [
            (t('games'), g), (t('wins'), w), (t('losses'), l), (t('draws'), dr),
            (t('win_rate'), oran), (t('words_played'), st.get('words', 0)),
            (t('best_word'), st.get('best_word', 0)),
        ]
        icerik = BoxLayout(orientation='vertical', spacing=dp(2), padding=dp(14))
        for ad, deger in satirlar:
            satir = BoxLayout(size_hint_y=None, height=dp(36))
            satir.add_widget(etiket(ad, boyut=14, renk=(0.7, 0.7, 0.7, 1), hizala='left'))
            satir.add_widget(etiket(str(deger), boyut=17, kalin=True, hizala='right'))
            icerik.add_widget(satir)
        pop = Popup(title=t('statistics'), content=icerik, size_hint=(0.88, None),
                    height=dp(430), title_color=(1, 1, 1, 1), separator_color=MOR)
        icerik.add_widget(Label(size_hint_y=None, height=dp(6)))
        rb = buton(t('reset'), renk_bg=GENC, renk_yazi=(0.85, 0.85, 0.85, 1), boyut=13)
        rb.size_hint_y = None
        rb.height = dp(42)

        def _sifirla(*_):
            app.ayar['stats'] = {}
            settings_store.kaydet(app.user_data_dir, app.ayar)
            pop.dismiss()
        rb.bind(on_press=_sifirla)
        icerik.add_widget(rb)
        pop.open()


# ══════════════════════════════════════════════════════════════════════════════
#  SES — efektleri yükler ve çalar (sustur ayarına saygı duyar)
# ══════════════════════════════════════════════════════════════════════════════
class Sesler:
    def __init__(self):
        self._sesler = {}
        self.acik = True
        try:
            from kivy.core.audio import SoundLoader
            d = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'sounds')
            for ad in ('success', 'error', 'win', 'lose'):
                s = SoundLoader.load(os.path.join(d, ad + '.wav'))
                if s:
                    self._sesler[ad] = s
        except Exception:
            pass

    def cal(self, ad):
        if not self.acik:
            return
        s = self._sesler.get(ad)
        if not s:
            return
        try:
            s.stop()
            s.play()
        except Exception:
            pass


# ══════════════════════════════════════════════════════════════════════════════
#  OFFLINE MOTOR — Bota karşı (sunucu yerine yerel oyun + bot + zamanlayıcı)
# ══════════════════════════════════════════════════════════════════════════════
class OfflineMotor:
    """
    Yerel GameRoom + bot + zamanlayıcıyı çalıştırır; sunucuyla AYNI mesaj
    sözlüklerini app._mesaj_geldi'ye besler — böylece tüm oyun/sonuç ekranı
    kodu aynen yeniden kullanılır. İnternet/sunucu gerektirmez.
    """
    def __init__(self, app, oda, bot, zorluk, training=False, hotseat=False):
        self.app = app
        self.oda = oda
        self.bot = bot
        self.zorluk = zorluk
        self.training = training   # True: solo antrenman (rakip yok)
        self.hotseat = hotseat     # True: iki kişi — tek telefon (elden ele)
        self._timer = None
        self._bot_ev = None

    def _yolla(self, d):
        """Mesajı app'e iletir; antrenman/elden-ele modunda 'mod' bayrağı ekler."""
        if self.training:
            d = {**d, 'mod': 'training'}
        elif self.hotseat:
            d = {**d, 'mod': 'hotseat'}
        self.app._mesaj_geldi(d)

    def basla(self):
        self.oda._oyunu_baslat()
        self.app._benim_no = 1
        oyun = self.app.sm.get_screen('oyun')
        oyun.benim_no_ayarla(1)
        oyun.training_mode(self.training)
        oyun.hotseat_mode(self.hotseat)
        self._yolla({**self.oda.durum(), 'tip': 'yeni_oyun'})
        self._timer = Clock.schedule_interval(self._tik, 1)

    def gonder(self, kelime):
        """İnsanın kelime denemesi (elden elede: sıradaki oyuncu adına)."""
        if self.oda.bitti:
            return
        if self.hotseat:
            pid = 'p1' if self.oda.siradaki_no == 1 else 'p2'
        else:
            pid = 'human'
        basari, kod, puan = self.oda.kelime_oyna(pid, kelime)
        self._yolla({'tip': 'kelime_sonuc', 'basari': basari,
                     'kod': kod, 'puan': puan, 'harf': self.oda.gerekli_harf})
        if basari:
            if self.training:
                self.oda.siradaki_no = 1   # solo: sıra hep sende kalır
            self._yolla({**self.oda.durum(), 'tip': 'durum'})
            if self.bot and not self.oda.bitti and self.oda.siradaki_no == 2:
                self._bot_planla()

    def _bot_planla(self):
        self._bot_iptal()
        self._bot_ev = Clock.schedule_once(lambda dt: self._bot_oyna(),
                                           self.bot.gecikme())

    def _bot_oyna(self):
        self._bot_ev = None
        if self.oda.bitti or self.oda.siradaki_no != 2:
            return
        kelime = self.bot.kelime_sec()
        if not kelime:
            return   # bulamadı (çok nadir) -> süresi dolar
        basari, _kod, _puan = self.oda.kelime_oyna('bot', kelime)
        if basari:
            self._yolla({**self.oda.durum(), 'tip': 'durum'})

    def _tik(self, dt):
        if self.oda.bitti:
            self.dur()
            return
        self.oda.sure_guncelle()
        if self.oda.bitti:
            if self.training:   # antrenman: en iyi skoru güncelle
                self.app.en_iyi_guncelle(self.oda.dict_lang, self.oda.puan[1])
            self._yolla({**self.oda.durum(), 'tip': 'oyun_bitti'})
            self.dur()
        else:
            self._yolla({**self.oda.durum(), 'tip': 'durum'})

    def tekrar(self):
        """Tekrar oyna (offline) — yeni oyunu hemen başlatır."""
        self.dur()
        self.oda._yeni_oyun_durumu()
        self.oda._oyunu_baslat()
        oyun = self.app.sm.get_screen('oyun')
        oyun.benim_no_ayarla(1)
        oyun.training_mode(self.training)
        oyun.hotseat_mode(self.hotseat)
        self._yolla({**self.oda.durum(), 'tip': 'yeni_oyun'})
        self._timer = Clock.schedule_interval(self._tik, 1)

    def _bot_iptal(self):
        if self._bot_ev:
            self._bot_ev.cancel()
            self._bot_ev = None

    def dur(self):
        if self._timer:
            self._timer.cancel()
            self._timer = None
        self._bot_iptal()


# ══════════════════════════════════════════════════════════════════════════════
#  APP
# ══════════════════════════════════════════════════════════════════════════════
class WordChainOnlineApp(App):
    title = 'Lexicoil'

    def build(self):
        # Ayarları yükle ve uygulama dilini uygula
        self.ayar = settings_store.yukle(self.user_data_dir)
        dil_ayarla(self.ayar['app_lang'])

        self.net = NetworkClient(SUNUCU_HTTP, SUNUCU_WS)
        self.net.uyandir()   # Render uyuyorsa arka planda uyandır (cold start'ı gizle)
        self.net.on_message = self._mesaj_geldi
        self.net.on_close = self._baglanti_koptu
        self._benim_no = 1
        self._oda_kodu = None
        self._sohbet = []
        self._sohbet_popup = None
        self._sohbet_kutu = None
        self._okunmamis = 0
        self.offline = None   # offline (bota karşı/antrenman) motoru; yoksa online
        self._oyun_kayitli = False   # bu oyun istatistiğe kaydedildi mi (tek sefer)
        self.sesler = Sesler()
        self.sesler.acik = self.ayar.get('sound', True)

        self.sm = ScreenManager(transition=FadeTransition(duration=0.2))
        self._ekranlari_kur()
        # Android geri tuşu (ESC=27): uygulamadan çıkmak yerine ekranlar arası geri git
        Window.bind(on_keyboard=self._geri_tusu)
        return self.sm

    def _geri_tusu(self, window, key, *args):
        """Android geri tuşu / ESC — ekrana göre geri gider; ana ekranda çıkışa izin verir."""
        if key != 27:
            return False
        # Açık bir popup (sohbet / zorluk) varsa onu kapatması için Kivy'ye bırak
        from kivy.uix.modalview import ModalView
        if any(isinstance(w, ModalView) for w in window.children):
            return False
        cur = self.sm.current
        if cur == 'ayarlar':
            self.ana_menuye()
            return True            # olayı tüket -> uygulama kapanmaz
        if cur in ('lobi', 'oyun', 'sonuc'):
            self.odadan_cik()
            return True
        return False               # 'baglan' (ana ekran): çıkışa izin ver

    def _ekranlari_kur(self):
        """Ekranları (yeniden) oluşturur — dil değişince çağrılır."""
        self.sm.clear_widgets()
        self.sm.add_widget(BaglanEkrani(name='baglan'))
        self.sm.add_widget(LobiEkrani(name='lobi'))
        self.sm.add_widget(OyunEkrani(name='oyun'))
        self.sm.add_widget(SonucEkrani(name='sonuc'))
        self.sm.add_widget(AyarlarEkrani(name='ayarlar'))

    # ── Ayarlar ──────────────────────────────────────────────────────────────
    def ayarlari_ac(self):
        self.sm.current = 'ayarlar'

    def app_dili_degistir(self, kod):
        dil_ayarla(kod)
        self.ayar['app_lang'] = kod
        settings_store.kaydet(self.user_data_dir, self.ayar)
        # Tüm ekranları yeni dilde yeniden kur, ayarlarda kal
        self._ekranlari_kur()
        self.sm.current = 'ayarlar'

    def sozluk_dili_degistir(self, kod):
        self.ayar['dict_lang'] = kod
        settings_store.kaydet(self.user_data_dir, self.ayar)

    # ── SSS ve sözlük tarayıcı (ana ekran + ayarlardan erişilir) ─────────────
    def faq_ac(self):
        """Nasıl Oynanır / SSS — kural ve kabul edilen kelime açıklaması."""
        icerik = BoxLayout(orientation='vertical', padding=dp(12))
        scroll = ScrollView(do_scroll_x=False)
        lbl = Label(text=t('faq_text'), markup=True, font_size=dp(14),
                    color=(0.9, 0.9, 0.9, 1), size_hint_y=None,
                    halign='left', valign='top')
        lbl.bind(width=lambda inst, w: setattr(inst, 'text_size', (w, None)))
        lbl.bind(texture_size=lambda inst, ts: setattr(inst, 'height', ts[1] + dp(8)))
        scroll.add_widget(lbl)
        icerik.add_widget(scroll)
        Popup(title=t('how_to_play'), content=icerik, size_hint=(0.92, 0.85),
              title_color=(1, 1, 1, 1), separator_color=TURUNCU).open()

    def sozluk_ac(self):
        """Seçili sözlük dilindeki TÜM geçerli kelimeleri arama kutusuyla listeler.
        47 bin+ satır için RecycleView (yalnızca görünen satırlar çizilir)."""
        from game_logic import sozluk_getir   # lazy: ilk açılışta yüklenir
        dil = self.ayar['dict_lang']
        kelimeler = sorted(sozluk_getir(dil))

        icerik = BoxLayout(orientation='vertical', spacing=dp(8), padding=dp(10))
        ara = giris_kutusu(t('search_word'), size_hint_y=None, height=dp(46),
                           font_size=dp(17))
        icerik.add_widget(ara)
        sayi_lbl = etiket(t('words_count', n=len(kelimeler)), boyut=11,
                          renk=(0.5, 0.5, 0.5, 1), size_hint_y=None, height=dp(18))
        icerik.add_widget(sayi_lbl)
        icerik.add_widget(etiket(t('tap_for_meaning'), boyut=10,
                                 renk=(0.45, 0.4, 0.55, 1),
                                 size_hint_y=None, height=dp(16)))

        rv = RecycleView(do_scroll_x=False, bar_width=dp(4))
        rv.viewclass = 'AnlamLabel'
        yerlesim = RecycleBoxLayout(orientation='vertical', size_hint_y=None,
                                    default_size=(None, dp(30)),
                                    default_size_hint=(1, None))
        yerlesim.bind(minimum_height=yerlesim.setter('height'))
        rv.add_widget(yerlesim)
        icerik.add_widget(rv)

        def _goster(liste):
            rv.data = [{'text': f'[ref={w}]{w}[/ref]', 'markup': True,
                        'font_size': dp(16),
                        'color': (0.88, 0.88, 0.88, 1)} for w in liste]
            sayi_lbl.text = t('words_count', n=len(liste))
            rv.scroll_y = 1

        def _filtrele(_inst, metin):
            q = metin.strip().lower()
            _goster([w for w in kelimeler if w.startswith(q)] if q else kelimeler)

        ara.bind(text=_filtrele)
        _goster(kelimeler)

        Popup(title=f"{t('all_words')} — {SOZLUK_DILLERI.get(dil, dil)}",
              content=icerik, size_hint=(0.94, 0.9),
              title_color=(1, 1, 1, 1), separator_color=MAVI).open()

    def kelime_listesi_ac(self, zincir):
        """Oynanan tüm kelimeleri (kim, kaç puan) kaydırılabilir popup'ta
        gösterir — oyun içinden ve sonuç ekranından açılır."""
        zincir = zincir or []
        icerik = BoxLayout(orientation='vertical', spacing=dp(6), padding=dp(10))
        scroll = ScrollView()
        kutu = BoxLayout(orientation='vertical', size_hint_y=None,
                         spacing=dp(4), padding=[0, dp(4)])
        kutu.bind(minimum_height=kutu.setter('height'))
        scroll.add_widget(kutu)
        icerik.add_widget(scroll)

        if zincir:
            kutu.add_widget(etiket(t('tap_for_meaning'), boyut=10,
                                   renk=(0.45, 0.4, 0.55, 1), hizala='left',
                                   size_hint_y=None, height=dp(16)))
        else:
            kutu.add_widget(Label(text=t('no_words_yet'), font_size=dp(14),
                                  color=(0.5, 0.5, 0.5, 1),
                                  size_hint_y=None, height=dp(30)))
        for i, oge in enumerate(zincir, start=1):
            renk = YESIL if oge.get('no') == 1 else MAVI
            kelime = oge.get('kelime', '')
            satir = BoxLayout(size_hint_y=None, height=dp(30))
            sol = AnlamLabel(text=f"{i}. [ref={kelime}]{kelime}[/ref]",
                             markup=True, font_size=dp(16),
                             bold=True, color=renk, halign='left', valign='middle')
            sol.bind(size=lambda inst, *_: setattr(inst, 'text_size', inst.size))
            sag = Label(text=f"+{oge.get('puan', 0)}", font_size=dp(14),
                        color=(0.7, 0.7, 0.7, 1), size_hint_x=None, width=dp(52),
                        halign='right', valign='middle')
            sag.bind(size=lambda inst, *_: setattr(inst, 'text_size', inst.size))
            satir.add_widget(sol)
            satir.add_widget(sag)
            kutu.add_widget(satir)

        pop = Popup(title=f"{t('words_used')} ({len(zincir)})", content=icerik,
                    size_hint=(0.92, 0.8), title_color=(1, 1, 1, 1),
                    separator_color=MOR)
        pop.open()
        # En son oynanan kelime altta — oraya kaydır
        Clock.schedule_once(lambda dt: setattr(scroll, 'scroll_y', 0), 0.1)

    # ── Kelime anlamı ────────────────────────────────────────────────────────
    def anlam_ac(self, kelime):
        """Kelimenin anlamını gösterir: tr=TDK, en=dictionaryapi.dev (uygulama
        içi popup); diğer dillerde Wiktionary sayfası tarayıcıda açılır."""
        kelime = (kelime or '').strip()
        if not kelime:
            return
        dil = self.ayar['dict_lang']
        if dil not in ('tr', 'en'):
            self._tarayici_ac(f'https://{dil}.wiktionary.org/wiki/{kelime}')
            return

        icerik = BoxLayout(orientation='vertical', padding=dp(12))
        scroll = ScrollView(do_scroll_x=False)
        lbl = Label(text=t('loading'), font_size=dp(15),
                    color=(0.9, 0.9, 0.9, 1), size_hint_y=None,
                    halign='left', valign='top')
        lbl.bind(width=lambda inst, w: setattr(inst, 'text_size', (w, None)))
        lbl.bind(texture_size=lambda inst, ts: setattr(inst, 'height', ts[1] + dp(8)))
        scroll.add_widget(lbl)
        icerik.add_widget(scroll)
        Popup(title=kelime, content=icerik, size_hint=(0.9, 0.6),
              title_color=(1, 1, 1, 1), separator_color=YESIL).open()

        def _arka_plan():
            metin = self._anlam_getir(kelime, dil)
            Clock.schedule_once(lambda dt: setattr(lbl, 'text', metin))

        import threading
        threading.Thread(target=_arka_plan, daemon=True).start()

    @staticmethod
    def _anlam_getir(kelime, dil):
        """Anlamı çevrimiçi sözlükten çeker (arka plan thread'inde çalışır)."""
        import requests
        try:
            satirlar = []
            if dil == 'tr':
                r = requests.get('https://sozluk.gov.tr/gts',
                                 params={'ara': kelime}, timeout=8,
                                 headers={'User-Agent': 'Mozilla/5.0 (Lexicoil)'})
                veri = r.json()
                if isinstance(veri, list):
                    for madde in veri:
                        for a in madde.get('anlamlarListe') or []:
                            anlam = (a.get('anlam') or '').strip()
                            if anlam:
                                satirlar.append(anlam)
            else:   # en
                r = requests.get('https://api.dictionaryapi.dev/api/v2/entries/en/'
                                 + kelime, timeout=8)
                veri = r.json()
                if isinstance(veri, list):
                    for giris in veri:
                        for m in giris.get('meanings') or []:
                            tur = m.get('partOfSpeech') or ''
                            for tanim in m.get('definitions') or []:
                                d = (tanim.get('definition') or '').strip()
                                if d:
                                    satirlar.append(f'({tur}) {d}' if tur else d)
            if not satirlar:
                return t('no_definition')
            satirlar = satirlar[:8]   # en fazla 8 anlam — popup taşmasın
            return '\n\n'.join(f'{i}. {s}' for i, s in enumerate(satirlar, 1))
        except Exception:
            return t('definition_error')

    @staticmethod
    def _tarayici_ac(url):
        """URL'yi cihazın tarayıcısında açar (Android'de Intent ile)."""
        if platform == 'android':
            try:
                from jnius import autoclass
                Intent = autoclass('android.content.Intent')
                Uri = autoclass('android.net.Uri')
                intent = Intent(Intent.ACTION_VIEW, Uri.parse(url))
                autoclass('org.kivy.android.PythonActivity').mActivity \
                    .startActivity(intent)
                return
            except Exception:
                pass
        import webbrowser
        webbrowser.open(url)

    # ── Kelime gönderme (online ya da offline'a yönlendirir) ──────────────────
    def kelime_gonder(self, kelime):
        if self.offline:
            self.offline.gonder(kelime)
        else:
            self.net.kelime_gonder(kelime)

    def rematch_iste(self):
        if self.offline:
            self.offline.tekrar()
        else:
            self.net.rematch_iste()

    # ── Offline: Bota karşı ──────────────────────────────────────────────────
    def bota_karsi_basla(self, zorluk):
        from game_logic import GameRoom   # lazy: sözlük ilk burada yüklenir
        from bot import Bot
        baglan = self.sm.get_screen('baglan')
        ad = baglan._ad() or t('player')
        oda = GameRoom('LOCAL', toplam_sure=baglan._secili_sure, hamle_sure=20,
                       dict_lang=self.ayar['dict_lang'])
        oda.oyuncu_ekle('human', ad)
        oda.oyuncu_ekle('bot', t('bot'))
        self.offline = OfflineMotor(self, oda, Bot(oda, zorluk), zorluk)
        self.sm.get_screen('oyun').sohbet_goster(False)   # offline: sohbet yok
        self.offline.basla()

    # ── Offline: İki kişi — tek telefon (elden ele) ──────────────────────────
    def iki_kisi_basla(self, ad2):
        from game_logic import GameRoom   # lazy: sözlük ilk burada yüklenir
        baglan = self.sm.get_screen('baglan')
        ad1 = baglan._ad() or t('player')
        ad2 = (ad2 or '').strip() or f"{t('player')} 2"
        oda = GameRoom('LOCAL', toplam_sure=baglan._secili_sure, hamle_sure=20,
                       dict_lang=self.ayar['dict_lang'])
        oda.oyuncu_ekle('p1', ad1)
        oda.oyuncu_ekle('p2', ad2)
        self.offline = OfflineMotor(self, oda, None, None, hotseat=True)
        self.sm.get_screen('oyun').sohbet_goster(False)   # offline: sohbet yok
        self.offline.basla()

    # ── Offline: Antrenman (solo) ────────────────────────────────────────────
    def training_basla(self):
        from game_logic import GameRoom   # lazy
        baglan = self.sm.get_screen('baglan')
        oda = GameRoom('LOCAL', toplam_sure=baglan._secili_sure, hamle_sure=20,
                       dict_lang=self.ayar['dict_lang'])
        oda.oyuncu_ekle('human', baglan._ad() or t('player'))   # tek oyuncu
        self.offline = OfflineMotor(self, oda, None, None, training=True)
        self.sm.get_screen('oyun').sohbet_goster(False)
        self.offline.basla()

    def en_iyi(self, dil):
        return self.ayar.get('best', {}).get(dil, 0)

    def en_iyi_guncelle(self, dil, skor):
        best = self.ayar.setdefault('best', {})
        if skor > best.get(dil, 0):
            best[dil] = skor
            settings_store.kaydet(self.user_data_dir, self.ayar)

    # ── İstatistik ───────────────────────────────────────────────────────────
    def istatistik(self):
        return self.ayar.setdefault('stats', {})

    def _oyun_bitti_ses(self, d):
        """Oyun sonucu sesini çalar (kazandın -> win, kaybettin -> lose)."""
        if d.get('mod') in ('training', 'hotseat') or d.get('ayrilan_ad'):
            self.sesler.cal('win')
            return
        kz = d.get('kazanan')
        if kz == self._benim_no:
            self.sesler.cal('win')
        elif kz not in (0, None):
            self.sesler.cal('lose')

    def _istatistik_kaydet(self, d):
        """Oyun bitince (bir kez) istatistiği günceller — son durumdan hesaplanır."""
        if self._oyun_kayitli:
            return
        self._oyun_kayitli = True
        self._oyun_bitti_ses(d)
        if d.get('mod') == 'hotseat':
            return   # elden ele: iki oyuncu da yerel — kişisel istatistik tutulmaz
        st = self.istatistik()
        zincir = d.get('zincir', [])
        benim = [z for z in zincir if z.get('no') == self._benim_no]
        st['words'] = st.get('words', 0) + len(benim)
        en_iyi_kelime = max((z.get('puan', 0) for z in benim), default=0)
        if en_iyi_kelime > st.get('best_word', 0):
            st['best_word'] = en_iyi_kelime
        if d.get('mod') != 'training':   # antrenmanda galip/mağlup yok
            st['games'] = st.get('games', 0) + 1
            if d.get('ayrilan_ad'):                       # rakip ayrıldı -> kazandın
                st['wins'] = st.get('wins', 0) + 1
            else:
                kz = d.get('kazanan')
                if kz == self._benim_no:
                    st['wins'] = st.get('wins', 0) + 1
                elif kz in (0, None):
                    st['draws'] = st.get('draws', 0) + 1
                else:
                    st['losses'] = st.get('losses', 0) + 1
        settings_store.kaydet(self.user_data_dir, self.ayar)

    # ── Bağlantı yönetimi ────────────────────────────────────────────────────
    def baglan_ve_gec(self, oda_kodu, ad):
        self._offline_temizle()
        self._sohbet_sifirla()   # yeni oda: önceki oyunun mesajları taşınmasın
        self.sm.get_screen('oyun').sohbet_goster(True)
        self.sm.get_screen('oyun').training_mode(False)   # online: rakip görünür
        self.sm.get_screen('oyun').hotseat_mode(False)
        self._oda_kodu = oda_kodu
        self.net.baglan(oda_kodu, ad)
        self.sm.get_screen('lobi').kodu_ayarla(oda_kodu)
        self.sm.current = 'lobi'

    def _offline_temizle(self):
        if self.offline:
            self.offline.dur()
            self.offline = None

    def odadan_cik(self):
        if self.offline:
            self._offline_temizle()
        else:
            self.net.kapat()
        self.ana_menuye()

    def ana_menuye(self):
        self.sm.current = 'baglan'

    def _baglanti_koptu(self):
        if self.sm.current not in ('sonuc', 'baglan', 'ayarlar'):
            ekran = self.sm.get_screen('baglan')
            ekran.durum.text = t('connection_lost')
            ekran.durum.color = KIRMIZI
            self.sm.current = 'baglan'

    # ── Sunucu mesajları ─────────────────────────────────────────────────────
    def _mesaj_geldi(self, veri):
        tip = veri.get('tip')

        if tip == 'katildi':
            self._benim_no = veri['senin_no']
            self.sm.get_screen('oyun').benim_no_ayarla(self._benim_no)

        elif tip == 'hata':
            ekran = self.sm.get_screen('baglan')
            ekran.durum.text = t(veri.get('kod', 'error'))
            ekran.durum.color = KIRMIZI
            self.sm.current = 'baglan'

        elif tip == 'sohbet':
            self._sohbet_geldi(veri)

        elif tip == 'kelime_sonuc':
            self.sesler.cal('success' if veri['basari'] else 'error')
            self.sm.get_screen('oyun').kelime_sonuc(
                veri['basari'], veri.get('kod', 'invalid'),
                veri.get('harf'), veri.get('puan', 0))

        elif tip == 'yeni_oyun':
            self._oyun_kayitli = False   # yeni oyun -> istatistik bayrağını sıfırla
            self.sm.get_screen('oyun').durum_guncelle(veri)
            self.sm.current = 'oyun'

        elif tip in ('durum', 'oyuncu_ayrildi'):
            self._durum_isle(veri)

        elif tip == 'oyun_bitti':
            self._istatistik_kaydet(veri)
            self.sm.get_screen('sonuc').goster(veri, self._benim_no)
            self.sm.current = 'sonuc'

    def _durum_isle(self, d):
        if d.get('bitti'):
            if self.sm.current == 'sonuc':
                self.sm.get_screen('sonuc').guncelle(d)
            else:
                self._istatistik_kaydet(d)
                self.sm.get_screen('sonuc').goster(d, self._benim_no)
                self.sm.current = 'sonuc'
        elif d.get('basladi'):
            if self.sm.current in ('lobi', 'ayarlar'):
                self._oyun_kayitli = False   # oyun başladı -> bayrağı sıfırla
                self.sm.current = 'oyun'
            if self.sm.current == 'oyun':
                self.sm.get_screen('oyun').durum_guncelle(d)
        elif d.get('geri_sayim') is not None:
            # İkisi de katıldı: kısa lobi geri sayımı (chat açık).
            if self.sm.current in ('lobi', 'ayarlar'):
                self.sm.current = 'lobi'
            self.sm.get_screen('lobi').hazir_guncelle(d)

    # ── SOHBET ───────────────────────────────────────────────────────────────
    def _sohbet_sifirla(self):
        """Chat geçmişini, okunmamış rozetini ve açık popup'ı temizler."""
        self._sohbet = []
        self._okunmamis = 0
        if self._sohbet_popup is not None:
            self._sohbet_popup.dismiss()   # on_dismiss popup/kutu referanslarını sıfırlar
        self._sohbet_rozet_guncelle()

    @staticmethod
    def _hex(renk):
        return ''.join(f'{int(c * 255):02x}' for c in renk[:3])

    def _sohbet_geldi(self, veri):
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
            btn._rozet = self._okunmamis > 0    # okunmamış varsa kırmızı nokta
            ciz_sohbet_ikonu(btn)               # ikonu rozetle yeniden çiz
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
        giris = giris_kutusu(t('type_message'), font_size=dp(16))
        gonder = buton(t('send'), renk_bg=MAVI, boyut=14)
        gonder.size_hint_x = None
        gonder.width = dp(90)

        def _gonder(*_):
            metin = giris.text.strip()
            giris.text = ''
            if metin:
                self.net.sohbet_gonder(metin)
            giris.focus = True

        giris.bind(on_text_validate=_gonder)
        gonder.bind(on_press=_gonder)
        alt.add_widget(giris)
        alt.add_widget(gonder)
        icerik.add_widget(alt)

        self._sohbet_popup = Popup(
            title=t('chat'), content=icerik, size_hint=(0.92, 0.8),
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
