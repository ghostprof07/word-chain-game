"""
WORD CHAIN — Kivy ile Yazı Zinciri Oyunu
=========================================
Çalıştırmak için:
    python oyun.py

Gerekli kütüphaneler:
    pip install kivy nltk
    python -c "import nltk; nltk.download('words')"
"""

import random
import string
import os
from kivy.app import App
from kivy.clock import Clock
from kivy.uix.screenmanager import ScreenManager, Screen, FadeTransition
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.graphics import Color, RoundedRectangle
from kivy.metrics import dp

# ── İngilizce sözlük — NLTK dosyasını direkt okur ────────────────────────────
_SOZLUK_DOSYA = os.path.join(
    os.path.expanduser('~'),
    'AppData', 'Roaming', 'nltk_data', 'corpora', 'words', 'en'
)

def _sozluk_yukle():
    if os.path.exists(_SOZLUK_DOSYA):
        with open(_SOZLUK_DOSYA, encoding='utf-8', errors='ignore') as f:
            return set(line.strip().lower() for line in f if line.strip().isalpha())
    # Dosya yoksa internet üzerinden NLTK ile indir
    import nltk
    nltk.download('words', download_dir=os.path.dirname(os.path.dirname(os.path.dirname(_SOZLUK_DOSYA))), quiet=True)
    with open(_SOZLUK_DOSYA, encoding='utf-8', errors='ignore') as f:
        return set(line.strip().lower() for line in f if line.strip().isalpha())

SOZLUK = _sozluk_yukle()

# ── Scrabble harf puanları ────────────────────────────────────────────────────
PUAN = {
    'a':1,'b':3,'c':3,'d':2,'e':1,'f':4,'g':2,'h':4,
    'i':1,'j':8,'k':5,'l':1,'m':3,'n':1,'o':1,'p':3,
    'q':10,'r':1,'s':1,'t':1,'u':1,'v':4,'w':4,'x':8,
    'y':4,'z':10
}

KOYU    = (0.07, 0.07, 0.07, 1)   # arka plan
YESIL   = (0, 0.78, 0.32, 1)
MAVI    = (0, 0.85, 1, 1)
SARI    = (1, 0.84, 0, 1)
KIRMIZI = (1, 0.3, 0.3, 1)
GENC    = (0.15, 0.15, 0.15, 1)   # kart arka planı


def kart(widget, renk=GENC, radius=12):
    """Widget'a yuvarlak arka plan ekler."""
    with widget.canvas.before:
        Color(*renk)
        rect = RoundedRectangle(pos=widget.pos, size=widget.size, radius=[dp(radius)])
    widget.bind(
        pos=lambda *a: setattr(rect, 'pos', widget.pos),
        size=lambda *a: setattr(rect, 'size', widget.size),
    )


def etiket(metin, boyut=15, renk=(1,1,1,1), kalin=False, hizala='center'):
    """Hızlıca Label oluşturur."""
    lbl = Label(
        text=metin, font_size=dp(boyut), color=renk,
        bold=kalin, halign=hizala, valign='middle',
    )
    lbl.bind(size=lambda *a: setattr(lbl, 'text_size', lbl.size))
    return lbl


def buton(metin, renk_bg=YESIL, renk_yazi=(0,0,0,1), boyut=17, callback=None):
    """Yuvarlak köşeli buton oluşturur."""
    btn = Button(
        text=metin, font_size=dp(boyut), bold=True,
        color=renk_yazi,
        background_normal='', background_color=(0,0,0,0),
    )
    kart(btn, renk=renk_bg, radius=14)
    if callback:
        btn.bind(on_press=callback)
    return btn


# ══════════════════════════════════════════════════════════════════════════════
#  1. ANA EKRAN
# ══════════════════════════════════════════════════════════════════════════════
class AnaEkran(Screen):
    """Oyun kurallarını ve "Başla" butonunu gösterir."""

    def __init__(self, **kw):
        super().__init__(**kw)
        kok = BoxLayout(orientation='vertical', padding=dp(28), spacing=dp(14))
        kart(kok, renk=KOYU)

        # Başlık
        kok.add_widget(Label(size_hint_y=None, height=dp(20)))
        baslik = etiket('WORD\nCHAIN', boyut=54, kalin=True, renk=YESIL)
        baslik.size_hint_y = None
        baslik.height = dp(130)
        kok.add_widget(baslik)

        altyazi = etiket(
            'Her kelime bir öncekinin\nson harfiyle başlamalı.',
            boyut=13, renk=(0.6,0.6,0.6,1)
        )
        altyazi.size_hint_y = None
        altyazi.height = dp(50)
        kok.add_widget(altyazi)

        # Kurallar
        for ikon, aciklama in [
            ('🔗  Zincir Kuralı', 'Sonraki kelime bir öncekinin son harfiyle başlar.'),
            ('⏱  20 Saniye',      'Her hamle için 20 sn, toplam 5 dakika.'),
            ('★  Scrabble Puanı', 'Q, Z, X, J gibi nadir harfler daha fazla puan verir.'),
        ]:
            satir = BoxLayout(orientation='vertical', spacing=dp(2),
                              size_hint_y=None, height=dp(62), padding=dp(12))
            kart(satir, renk=GENC)
            satir.add_widget(etiket(ikon, boyut=13, kalin=True, hizala='left'))
            satir.add_widget(etiket(aciklama, boyut=11, renk=(0.55,0.55,0.55,1), hizala='left'))
            kok.add_widget(satir)

        kok.add_widget(Label())  # esnek boşluk

        basla_btn = buton('OYUNU BAŞLAT', callback=self.oyunu_baslat)
        basla_btn.size_hint_y = None
        basla_btn.height = dp(58)
        kok.add_widget(basla_btn)
        kok.add_widget(Label(size_hint_y=None, height=dp(16)))

        self.add_widget(kok)

    def oyunu_baslat(self, *_):
        self.manager.get_screen('oyun').sifirla()
        self.manager.current = 'oyun'


# ══════════════════════════════════════════════════════════════════════════════
#  2. OYUN EKRANI
# ══════════════════════════════════════════════════════════════════════════════
class OyunEkrani(Screen):

    TOPLAM_SURE = 300   # 5 dakika
    HAMLE_SURE  = 20    # her hamle için

    def sifirla(self):
        """Yeni oyun için tüm değerleri başa alır."""
        self._toplam_sure = self.TOPLAM_SURE
        self._hamle_sure  = self.HAMLE_SURE
        self._siradaki    = 1           # hangi oyuncu
        self._puan        = {1: 0, 2: 0}
        self._kullanilan  = set()
        self._son_kelime  = ''
        # Rastgele başlangıç harfi
        self._gerekli_harf = random.choice(string.ascii_lowercase)

        # UI güncelle
        self._harf_lbl.text  = self._gerekli_harf.upper()
        self._tur_lbl.text   = 'OYUNCU 1 başlar'
        self._p1_puan.text   = '0'
        self._p2_puan.text   = '0'
        self._son_lbl.text   = ''
        self._durum_lbl.text = 'Oyun başladı!'
        self._durum_lbl.color = SARI
        self._giris.text      = ''
        self._bar_guncelle()
        self._p1_kart_guncelle(aktif=True)
        self._p2_kart_guncelle(aktif=False)

        # Zamanlayıcıyı başlat
        if hasattr(self, '_timer') and self._timer:
            self._timer.cancel()
        self._timer = Clock.schedule_interval(self._tik, 1)

    # ── Arayüz oluşturma ─────────────────────────────────────────────────────

    def __init__(self, **kw):
        super().__init__(**kw)

        # Varsayılan değerler (sifirla() çağrılmadan önce)
        self._toplam_sure = self.TOPLAM_SURE
        self._hamle_sure  = self.HAMLE_SURE
        self._siradaki    = 1
        self._puan        = {1: 0, 2: 0}
        self._kullanilan  = set()
        self._son_kelime  = ''
        self._gerekli_harf = 'a'
        self._timer       = None

        kok = BoxLayout(orientation='vertical', padding=dp(18), spacing=dp(10))
        kart(kok, renk=KOYU)

        # ── Üst çubuk (süre + kelime sayısı + çık) ──
        ust = BoxLayout(size_hint_y=None, height=dp(38))
        self._toplam_lbl = etiket('05:00', boyut=20, kalin=True, renk=(0.5,0.5,0.5,1), hizala='left')
        self._kelime_lbl = etiket('0 kelime', boyut=12, renk=(0.4,0.4,0.4,1))
        cik_btn = buton('ÇIKIŞ', renk_bg=(0.2,0.2,0.2,1), renk_yazi=(0.6,0.6,0.6,1),
                         boyut=12, callback=self._cikis)
        cik_btn.size_hint_x = None
        cik_btn.width = dp(70)
        ust.add_widget(self._toplam_lbl)
        ust.add_widget(self._kelime_lbl)
        ust.add_widget(cik_btn)
        kok.add_widget(ust)

        # ── Oyuncu kartları ──
        oyuncu_satir = BoxLayout(size_hint_y=None, height=dp(90), spacing=dp(12))

        self._p1_kutu = BoxLayout(orientation='vertical', spacing=dp(4), padding=dp(10))
        self._p1_baslik = etiket('OYUNCU 1', boyut=10, kalin=True, renk=YESIL)
        self._p1_puan   = etiket('0', boyut=36, kalin=True)
        self._p1_kutu.add_widget(self._p1_baslik)
        self._p1_kutu.add_widget(self._p1_puan)

        self._p2_kutu = BoxLayout(orientation='vertical', spacing=dp(4), padding=dp(10))
        self._p2_baslik = etiket('OYUNCU 2', boyut=10, kalin=True, renk=MAVI)
        self._p2_puan   = etiket('0', boyut=36, kalin=True)
        self._p2_kutu.add_widget(self._p2_baslik)
        self._p2_kutu.add_widget(self._p2_puan)

        self._p1_rect = None  # canvas nesneleri sonra oluşacak
        self._p2_rect = None

        oyuncu_satir.add_widget(self._p1_kutu)
        oyuncu_satir.add_widget(self._p2_kutu)
        kok.add_widget(oyuncu_satir)

        # Kartların arka planı Clock ile çizilir (pos/size hazır olduktan sonra)
        Clock.schedule_once(self._kart_arkaplan_yap, 0)

        # ── Tur bilgisi ──
        self._tur_lbl = etiket('OYUNCU 1 başlar', boyut=13, renk=(0.6,0.6,0.6,1))
        self._tur_lbl.size_hint_y = None
        self._tur_lbl.height = dp(22)
        kok.add_widget(self._tur_lbl)

        # ── Büyük harf göstergesi ──
        self._harf_lbl = etiket('A', boyut=72, kalin=True, renk=YESIL)
        self._harf_lbl.size_hint_y = None
        self._harf_lbl.height = dp(100)
        kok.add_widget(self._harf_lbl)

        # ── Hamle zamanlayıcısı ──
        self._hamle_lbl = etiket('20', boyut=28, kalin=True, renk=YESIL)
        self._hamle_lbl.size_hint_y = None
        self._hamle_lbl.height = dp(38)

        # İlerleme çubuğu (basit bir BoxLayout + canvas)
        self._bar_satir = BoxLayout(size_hint_y=None, height=dp(8))
        kok.add_widget(self._bar_satir)
        kok.add_widget(self._hamle_lbl)
        Clock.schedule_once(self._bar_arkaplan_yap, 0)

        # ── Son kelime ──
        self._son_lbl = etiket('', boyut=13, renk=(0.4,0.4,0.4,1))
        self._son_lbl.size_hint_y = None
        self._son_lbl.height = dp(22)
        kok.add_widget(self._son_lbl)

        kok.add_widget(Label())  # esnek boşluk

        # ── Durum mesajı ──
        self._durum_lbl = etiket('Oyun başladı!', boyut=15, kalin=True, renk=SARI)
        self._durum_lbl.size_hint_y = None
        self._durum_lbl.height = dp(28)
        kok.add_widget(self._durum_lbl)

        # ── Metin girişi ──
        self._giris = TextInput(
            multiline=False, font_size=dp(28),
            size_hint_y=None, height=dp(58),
            hint_text='Kelime yaz…',
            hint_text_color=(0.3,0.3,0.3,1),
            background_color=GENC,
            foreground_color=(1,1,1,1),
            cursor_color=YESIL,
            padding=[dp(16), dp(14)],
        )
        self._giris.bind(on_text_validate=lambda *_: self._gonder())
        kok.add_widget(self._giris)

        # ── Gönder butonu ──
        gonder_btn = buton('GÖNDER', callback=lambda *_: self._gonder())
        gonder_btn.size_hint_y = None
        gonder_btn.height = dp(58)
        kok.add_widget(gonder_btn)

        kok.add_widget(Label(size_hint_y=None, height=dp(8)))

        self.add_widget(kok)

    def _kart_arkaplan_yap(self, *_):
        """Oyuncu kutularına yuvarlak arka plan ekler."""
        kart(self._p1_kutu, renk=YESIL[:-1] + (0.15,))
        kart(self._p2_kutu, renk=GENC)

    def _bar_arkaplan_yap(self, *_):
        """Zamanlayıcı çubuğunu çizer."""
        with self._bar_satir.canvas.before:
            Color(1, 1, 1, 0.08)
            self._bar_arkaplan = RoundedRectangle(
                pos=self._bar_satir.pos,
                size=self._bar_satir.size,
                radius=[dp(4)]
            )
            Color(*YESIL)
            self._bar_on = RoundedRectangle(
                pos=self._bar_satir.pos,
                size=self._bar_satir.size,
                radius=[dp(4)]
            )
        self._bar_satir.bind(
            pos=lambda *_: self._bar_guncelle(),
            size=lambda *_: self._bar_guncelle(),
        )

    def _bar_guncelle(self):
        """Çubuğun doluluk oranını ve rengini günceller."""
        if not hasattr(self, '_bar_on'):
            return
        oran = max(0.0, self._hamle_sure / self.HAMLE_SURE)
        self._bar_arkaplan.pos  = self._bar_satir.pos
        self._bar_arkaplan.size = self._bar_satir.size
        self._bar_on.pos  = self._bar_satir.pos
        self._bar_on.size = (self._bar_satir.width * oran, self._bar_satir.height)
        # Renk: yeşil → sarı → kırmızı
        if self._hamle_sure > 10:
            self._hamle_lbl.color = YESIL
        elif self._hamle_sure > 5:
            self._hamle_lbl.color = SARI
        else:
            self._hamle_lbl.color = KIRMIZI

    def _p1_kart_guncelle(self, aktif):
        with self._p1_kutu.canvas.before:
            self._p1_kutu.canvas.before.clear()
            Color(*(YESIL[:-1] + (0.18,)) if aktif else GENC)
            RoundedRectangle(pos=self._p1_kutu.pos,
                              size=self._p1_kutu.size, radius=[dp(12)])

    def _p2_kart_guncelle(self, aktif):
        with self._p2_kutu.canvas.before:
            self._p2_kutu.canvas.before.clear()
            Color(*(MAVI[:-1] + (0.18,)) if aktif else GENC)
            RoundedRectangle(pos=self._p2_kutu.pos,
                              size=self._p2_kutu.size, radius=[dp(12)])

    # ── Zamanlayıcı ──────────────────────────────────────────────────────────

    def _tik(self, dt):
        self._toplam_sure -= 1
        self._hamle_sure  -= 1

        # Üst çubuk
        m, s = divmod(self._toplam_sure, 60)
        self._toplam_lbl.text = f'{m:02d}:{s:02d}'
        self._kelime_lbl.text = f'{len(self._kullanilan)} kelime'

        # Hamle çubuğu
        self._hamle_lbl.text = str(self._hamle_sure)
        self._bar_guncelle()

        if self._toplam_sure <= 0 or self._hamle_sure <= 0:
            self._timer.cancel()
            self._oyun_bitti()

    # ── Kelime gönderme ───────────────────────────────────────────────────────

    def _gonder(self):
        kelime = self._giris.text.strip().lower()
        self._giris.text = ''

        if not kelime or not kelime.isalpha():
            return

        # Daha önce kullanıldı mı?
        if kelime in self._kullanilan:
            self._hata('Bu kelime zaten kullanıldı!')
            return

        # Doğru harfle mi başlıyor?
        if kelime[0] != self._gerekli_harf:
            self._hata(f'"{self._gerekli_harf.upper()}" harfiyle başlamalı!')
            return

        # İngilizce sözlükte var mı?
        if kelime not in SOZLUK:
            self._hata('Geçerli bir İngilizce kelime değil!')
            return

        # ── Başarılı ──
        puan = sum(PUAN.get(h, 0) for h in kelime)
        self._puan[self._siradaki] += puan
        self._kullanilan.add(kelime)
        self._son_kelime    = kelime
        self._gerekli_harf  = kelime[-1]  # bir sonraki harfi belirle

        # Arayüzü güncelle
        self._harf_lbl.text = self._gerekli_harf.upper()
        self._son_lbl.text  = f'Son kelime: {kelime}'
        self._durum_lbl.text  = f'+{puan} puan!'
        self._durum_lbl.color = YESIL
        self._p1_puan.text = str(self._puan[1])
        self._p2_puan.text = str(self._puan[2])

        # Sırayı değiştir
        self._siradaki   = 2 if self._siradaki == 1 else 1
        self._hamle_sure = self.HAMLE_SURE
        self._tur_lbl.text = f'OYUNCU {self._siradaki} — kelime yaz'
        self._p1_kart_guncelle(aktif=self._siradaki == 1)
        self._p2_kart_guncelle(aktif=self._siradaki == 2)
        self._bar_guncelle()
        self._hamle_lbl.text = str(self._hamle_sure)

    def _hata(self, mesaj):
        self._durum_lbl.text  = mesaj
        self._durum_lbl.color = KIRMIZI

    def _cikis(self, *_):
        if self._timer:
            self._timer.cancel()
        self.manager.current = 'ana'

    def _oyun_bitti(self):
        sonuc = self.manager.get_screen('sonuc')
        sonuc.goster(self._puan, self._kullanilan)
        self.manager.current = 'sonuc'


# ══════════════════════════════════════════════════════════════════════════════
#  3. SONUÇ EKRANI
# ══════════════════════════════════════════════════════════════════════════════
class SonucEkrani(Screen):

    def __init__(self, **kw):
        super().__init__(**kw)
        self._kok = BoxLayout(orientation='vertical', padding=dp(24), spacing=dp(14))
        kart(self._kok, renk=KOYU)
        self.add_widget(self._kok)

    def goster(self, puan, kullanilan):
        """Sonuç ekranını doldurur."""
        self._kok.clear_widgets()
        p1, p2 = puan[1], puan[2]

        # Kazanan
        if p1 > p2:
            kazan_yazi, kazan_renk = 'OYUNCU 1 KAZANDI!', YESIL
        elif p2 > p1:
            kazan_yazi, kazan_renk = 'OYUNCU 2 KAZANDI!', MAVI
        else:
            kazan_yazi, kazan_renk = 'BERABERLİK!', SARI

        self._kok.add_widget(Label(size_hint_y=None, height=dp(20)))
        self._kok.add_widget(etiket('OYUN BİTTİ', boyut=13, renk=(0.5,0.5,0.5,1)))
        self._kok.add_widget(etiket(kazan_yazi, boyut=34, kalin=True, renk=kazan_renk))

        # İki oyuncu kutusu
        kutular = BoxLayout(size_hint_y=None, height=dp(110), spacing=dp(14))
        for num, renk in [(1, YESIL), (2, MAVI)]:
            kutu = BoxLayout(orientation='vertical', spacing=dp(4), padding=dp(12))
            kart(kutu, renk=GENC)
            kutu.add_widget(etiket(f'OYUNCU {num}', boyut=11, kalin=True, renk=renk))
            kutu.add_widget(etiket(str(puan[num]), boyut=46, kalin=True))
            kutu.add_widget(etiket('puan', boyut=12, renk=(0.5,0.5,0.5,1)))
            kutular.add_widget(kutu)
        self._kok.add_widget(kutular)

        # İstatistikler
        toplam = p1 + p2
        sayi   = len(kullanilan)
        ort    = f'{toplam/sayi:.1f}' if sayi else '0'
        istat  = BoxLayout(size_hint_y=None, height=dp(72), padding=dp(12))
        kart(istat, renk=GENC)
        for deger, ad in [(str(sayi), 'Kelime'), (str(toplam), 'Toplam'), (ort, 'Ort/kelime')]:
            kutu = BoxLayout(orientation='vertical')
            kutu.add_widget(etiket(deger, boyut=26, kalin=True))
            kutu.add_widget(etiket(ad, boyut=10, renk=(0.5,0.5,0.5,1)))
            istat.add_widget(kutu)
        self._kok.add_widget(istat)

        # Kullanılan kelimeler
        self._kok.add_widget(etiket('Kullanılan Kelimeler', boyut=12, renk=(0.5,0.5,0.5,1)))
        kelimeler_lbl = etiket(
            '  '.join(sorted(kullanilan)) if kullanilan else '—',
            boyut=13, renk=(0.7,0.7,0.7,1)
        )
        self._kok.add_widget(kelimeler_lbl)

        self._kok.add_widget(Label())  # esnek boşluk

        # Tekrar oyna butonu
        btn = buton('TEKRAR OYNA', callback=self._tekrar)
        btn.size_hint_y = None
        btn.height = dp(58)
        self._kok.add_widget(btn)
        self._kok.add_widget(Label(size_hint_y=None, height=dp(16)))

    def _tekrar(self, *_):
        self.manager.get_screen('oyun').sifirla()
        self.manager.current = 'oyun'


# ══════════════════════════════════════════════════════════════════════════════
#  UYGULAMA
# ══════════════════════════════════════════════════════════════════════════════
class YaziZinciriApp(App):
    def build(self):
        sm = ScreenManager(transition=FadeTransition(duration=0.2))
        sm.add_widget(AnaEkran(name='ana'))
        sm.add_widget(OyunEkrani(name='oyun'))
        sm.add_widget(SonucEkrani(name='sonuc'))
        return sm


if __name__ == '__main__':
    YaziZinciriApp().run()
