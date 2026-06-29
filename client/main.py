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

from kivy.app import App
from kivy.clock import Clock
from kivy.core.window import Window

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
import settings_store
from i18n import t, dil_ayarla, DILLER

Window.clearcolor = (0.05, 0.05, 0.05, 1)

# ── Colors ────────────────────────────────────────────────────────────────────
KOYU    = (0.07, 0.07, 0.07, 1)
YESIL   = (0, 0.78, 0.32, 1)
MAVI    = (0, 0.85, 1, 1)
SARI    = (1, 0.84, 0, 1)
KIRMIZI = (1, 0.3, 0.3, 1)
GENC    = (0.15, 0.15, 0.15, 1)

# Sözlük (kelime doğrulama) dilleri — sunucudaki ALFABELER ile aynı tutulmalı.
# YENİ SÖZLÜK: buraya kod+ad ekle + sunucuya words_<kod>.txt + ALFABELER.
# Sözlük (kelime doğrulama) dilleri. Şimdilik sadece İngilizce — Türkçe için
# sunucuya words_tr.txt kelime listesi eklenince 'tr': 'Türkçe' geri açılacak.
SOZLUK_DILLERI = {
    'en': 'English',
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
                   hint_text=hint, hint_text_color=(0.3, 0.3, 0.3, 1),
                   background_color=GENC, foreground_color=(1, 1, 1, 1),
                   cursor_color=YESIL, padding=[dp(14), dp(12)], **kw)
    return ti


# ══════════════════════════════════════════════════════════════════════════════
#  1. CONNECT SCREEN
# ══════════════════════════════════════════════════════════════════════════════
class BaglanEkrani(Screen):
    def __init__(self, **kw):
        super().__init__(**kw)
        kok = BoxLayout(orientation='vertical', padding=dp(24), spacing=dp(14))
        kart(kok, renk=KOYU)

        # Üst satır: başlık + ayarlar butonu
        ust = BoxLayout(size_hint_y=None, height=dp(34))
        ust.add_widget(Label())  # esnek boşluk
        ayar_btn = buton('⚙', renk_bg=GENC, renk_yazi=(0.8, 0.8, 0.8, 1), boyut=18,
                         callback=lambda *_: App.get_running_app().ayarlari_ac())
        ayar_btn.size_hint_x = None
        ayar_btn.width = dp(44)
        ust.add_widget(ayar_btn)
        kok.add_widget(ust)

        baslik = etiket('WORD\nCHAIN', boyut=46, kalin=True, renk=YESIL)
        baslik.size_hint_y = None
        baslik.height = dp(110)
        kok.add_widget(baslik)
        kok.add_widget(etiket(t('subtitle'), boyut=14,
                              renk=(0.6, 0.6, 0.6, 1), hizala='center'))

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

        kok.add_widget(buton(t('create_room'), callback=self.oda_olustur))
        kok.add_widget(etiket(t('or'), boyut=12, renk=(0.4, 0.4, 0.4, 1)))

        self.kod_giris = giris_kutusu(t('room_code_hint'),
                                      size_hint_y=None, height=dp(52))
        kok.add_widget(self.kod_giris)
        kok.add_widget(buton(t('join_with_code'), renk_bg=MAVI, callback=self.katil))

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
        kok = BoxLayout(orientation='vertical', padding=dp(28), spacing=dp(16))
        kart(kok, renk=KOYU)

        kok.add_widget(Label())
        kok.add_widget(etiket(t('room_code'), boyut=14, renk=(0.5, 0.5, 0.5, 1)))
        self.kod_lbl = etiket('----', boyut=56, kalin=True, renk=YESIL)
        self.kod_lbl.size_hint_y = None
        self.kod_lbl.height = dp(80)
        kok.add_widget(self.kod_lbl)
        kok.add_widget(etiket(t('share_code'), boyut=13, renk=(0.6, 0.6, 0.6, 1)))

        kok.add_widget(Label(size_hint_y=None, height=dp(20)))
        kok.add_widget(etiket(t('waiting_opponent'), boyut=16, renk=SARI))

        kok.add_widget(Label())
        kok.add_widget(buton(t('cancel'), renk_bg=GENC, renk_yazi=(0.8, 0.8, 0.8, 1),
                             callback=lambda *_: App.get_running_app().odadan_cik()))
        kok.add_widget(Label(size_hint_y=None, height=dp(10)))
        self.add_widget(kok)

    def kodu_ayarla(self, kod):
        self.kod_lbl.text = kod


# ══════════════════════════════════════════════════════════════════════════════
#  3. GAME SCREEN
# ══════════════════════════════════════════════════════════════════════════════
class OyunEkrani(Screen):
    def __init__(self, **kw):
        super().__init__(**kw)
        self._benim_no = 1

        kok = BoxLayout(orientation='vertical', padding=dp(18), spacing=dp(10))
        kart(kok, renk=KOYU)

        ust = BoxLayout(size_hint_y=None, height=dp(38))
        self.toplam_lbl = etiket('05:00', boyut=20, kalin=True,
                                 renk=(0.5, 0.5, 0.5, 1), hizala='left')
        self.kelime_lbl = etiket(t('words_count', n=0), boyut=12,
                                 renk=(0.4, 0.4, 0.4, 1))
        self.sohbet_btn = buton('\U0001F4AC', renk_bg=MAVI, renk_yazi=(0, 0, 0, 1),
                                boyut=15,
                                callback=lambda *_: App.get_running_app().sohbet_ac())
        self.sohbet_btn.size_hint_x = None
        self.sohbet_btn.width = dp(52)
        cik = buton(t('quit'), renk_bg=GENC, renk_yazi=(0.6, 0.6, 0.6, 1), boyut=12,
                    callback=lambda *_: App.get_running_app().odadan_cik())
        cik.size_hint_x = None
        cik.width = dp(64)
        ust.add_widget(self.toplam_lbl)
        ust.add_widget(self.kelime_lbl)
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

        self.harf_lbl = etiket('?', boyut=72, kalin=True, renk=YESIL)
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

    def _gonder(self):
        kelime = self.giris.text.strip().lower()
        self.giris.text = ''
        if kelime:
            App.get_running_app().net.kelime_gonder(kelime)

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

        self.harf_lbl.text = d['gerekli_harf'].upper()

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
        self.p1_puan.text = str(d['puan']['1'])
        self.p2_puan.text = str(d['puan']['2'])

        sira = d['siradaki_no']
        benim_sira = (sira == self._benim_no)
        self._kart_vurgu(self.p1_kutu, sira == 1, YESIL)
        self._kart_vurgu(self.p2_kutu, sira == 2, MAVI)

        if benim_sira:
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

    def _zincir_guncelle(self, zincir):
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
        p1, p2 = d['puan']['1'], d['puan']['2']
        kazanan = d.get('kazanan')
        ayrilan = d.get('ayrilan_ad')

        if ayrilan:
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
        self._kok.add_widget(etiket(yazi, boyut=32, kalin=True, renk=renk))
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

        self._kok.add_widget(etiket(t('words_used'), boyut=12,
                                    renk=(0.5, 0.5, 0.5, 1), size_hint_y=None,
                                    height=dp(18)))
        kelimeler = d.get('kullanilan', [])
        self._kok.add_widget(etiket('  '.join(kelimeler) if kelimeler else '—',
                                    boyut=13, renk=(0.7, 0.7, 0.7, 1)))

        self._rematch_durum = etiket('', boyut=13, kalin=True, renk=SARI,
                                     size_hint_y=None, height=dp(24))
        self._kok.add_widget(self._rematch_durum)

        self._kok.add_widget(Label())

        if not ayrilan:
            self._rematch_btn = buton(t('play_again'),
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

    def _rematch_iste(self):
        App.get_running_app().net.rematch_iste()
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
        self._kok = BoxLayout(orientation='vertical', padding=dp(24), spacing=dp(14))
        kart(self._kok, renk=KOYU)
        self.add_widget(self._kok)
        self.kur()

    def kur(self):
        """Ekranı aktif dile göre (yeniden) oluşturur."""
        self._kok.clear_widgets()
        app = App.get_running_app()

        self._kok.add_widget(Label(size_hint_y=None, height=dp(16)))
        self._kok.add_widget(etiket(t('settings_title'), boyut=24, kalin=True,
                                    renk=YESIL, size_hint_y=None, height=dp(36)))

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

        self._kok.add_widget(Label())
        self._kok.add_widget(buton(t('done'),
                                   callback=lambda *_: App.get_running_app().ana_menuye()))
        self._kok.add_widget(Label(size_hint_y=None, height=dp(10)))

    def _app_dili_sec(self, kod):
        App.get_running_app().app_dili_degistir(kod)

    def _sozluk_dili_sec(self, kod):
        app = App.get_running_app()
        app.sozluk_dili_degistir(kod)
        for k, b in self._sozluk_butonlar.items():
            secim_vurgu(b, k == kod, renk_secili=MAVI)


# ══════════════════════════════════════════════════════════════════════════════
#  APP
# ══════════════════════════════════════════════════════════════════════════════
class WordChainOnlineApp(App):
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

        self.sm = ScreenManager(transition=FadeTransition(duration=0.2))
        self._ekranlari_kur()
        return self.sm

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

    # ── Bağlantı yönetimi ────────────────────────────────────────────────────
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
            self.sm.get_screen('oyun').kelime_sonuc(
                veri['basari'], veri.get('kod', 'invalid'),
                veri.get('harf'), veri.get('puan', 0))

        elif tip == 'yeni_oyun':
            self.sm.get_screen('oyun').durum_guncelle(veri)
            self.sm.current = 'oyun'

        elif tip in ('durum', 'oyuncu_ayrildi'):
            self._durum_isle(veri)

        elif tip == 'oyun_bitti':
            self.sm.get_screen('sonuc').goster(veri, self._benim_no)
            self.sm.current = 'sonuc'

    def _durum_isle(self, d):
        if d.get('basladi') and not d.get('bitti'):
            if self.sm.current in ('lobi', 'ayarlar'):
                self.sm.current = 'oyun'
            if self.sm.current == 'oyun':
                self.sm.get_screen('oyun').durum_guncelle(d)
        elif d.get('bitti'):
            if self.sm.current == 'sonuc':
                self.sm.get_screen('sonuc').guncelle(d)
            else:
                self.sm.get_screen('sonuc').goster(d, self._benim_no)
                self.sm.current = 'sonuc'

    # ── SOHBET ───────────────────────────────────────────────────────────────
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
            btn.text = f'\U0001F4AC {self._okunmamis}' if self._okunmamis else '\U0001F4AC'
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
