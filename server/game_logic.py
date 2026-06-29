"""
Oyun mantığı — sunucu tarafında çalışır.
Kelime doğrulama, puanlama ve oda (game room) durumunu yönetir.
"""
import os
import random
import string
import time

# ── Scrabble harf puanları ────────────────────────────────────────────────────
PUAN = {
    'a': 1, 'b': 3, 'c': 3, 'd': 2, 'e': 1, 'f': 4, 'g': 2, 'h': 4,
    'i': 1, 'j': 8, 'k': 5, 'l': 1, 'm': 3, 'n': 1, 'o': 1, 'p': 3,
    'q': 10, 'r': 1, 's': 1, 't': 1, 'u': 1, 'v': 4, 'w': 4, 'x': 8,
    'y': 4, 'z': 10,
}


# Desteklenen sözlük dilleri: kod -> başlangıç harfleri alfabesi
# YENİ SÖZLÜK DİLİ EKLEMEK: words_<kod>.txt dosyasını bu klasöre koy + buraya alfabe ekle.
ALFABELER = {
    'en': 'abcdefghijklmnopqrstuvwxyz',
    'tr': 'abcçdefgğhıijklmnoöprsştuüvyz',
}


def _sozluk_yukle_dosya(path):
    with open(path, encoding='utf-8', errors='ignore') as f:
        return set(l.strip().lower() for l in f if l.strip().isalpha())


def _sozlukleri_yukle():
    """Sunucu klasöründeki words_<kod>.txt dosyalarını yükler."""
    d = os.path.dirname(__file__)
    sozlukler = {}
    for kod in ALFABELER:
        p = os.path.join(d, f'words_{kod}.txt')
        if os.path.exists(p):
            sozlukler[kod] = _sozluk_yukle_dosya(p)

    # Geriye dönük: en yoksa geliştirme makinesindeki NLTK'dan yükle
    if 'en' not in sozlukler:
        nltk_dosya = os.path.join(
            os.path.expanduser('~'),
            'AppData', 'Roaming', 'nltk_data', 'corpora', 'words', 'en'
        )
        if os.path.exists(nltk_dosya):
            sozlukler['en'] = _sozluk_yukle_dosya(nltk_dosya)

    return sozlukler


SOZLUKLER = _sozlukleri_yukle()


def sozluk_getir(dil):
    """Verilen dilin sözlük kümesini döndürür (yoksa İngilizce ya da boş)."""
    if dil in SOZLUKLER:
        return SOZLUKLER[dil]
    return SOZLUKLER.get('en', set())


def kelime_puani(kelime):
    return sum(PUAN.get(h, 0) for h in kelime.lower())


# ══════════════════════════════════════════════════════════════════════════════
#  OYUN ODASI
# ══════════════════════════════════════════════════════════════════════════════
class GameRoom:
    """Tek bir oyun odasını ve durumunu temsil eder."""

    def __init__(self, oda_kodu, toplam_sure=300, hamle_sure=20, dict_lang='en'):
        self.kod = oda_kodu
        # Süre seçeneği: oda kuran kişi belirler (saniye)
        self.varsayilan_toplam = int(toplam_sure)
        self.varsayilan_hamle = int(hamle_sure)
        # Sözlük (kelime doğrulama) dili — oda kuran kişi seçer
        self.dict_lang = dict_lang if dict_lang in SOZLUKLER else 'en'
        self.sozluk = sozluk_getir(self.dict_lang)
        self.alfabe = ALFABELER.get(self.dict_lang, ALFABELER['en'])
        self.oyuncular = {}          # player_id -> {"ad": str, "no": 1|2}
        self._yeni_oyun_durumu()
        # Rematch (tekrar oyna) isteyen oyuncuların id'leri
        self.rematch_isteyenler = set()
        # Bir oyuncu oyun ortasında ayrıldıysa adı burada tutulur
        self.ayrilan_ad = None

    def _yeni_oyun_durumu(self):
        """Yeni bir oyunun başlangıç değerlerini kurar (oyuncuları korur)."""
        self.puan = {1: 0, 2: 0}
        self.kullanilan = set()
        self.zincir = []            # sıralı: [{"kelime": str, "no": 1|2, "puan": int}]
        self.son_kelime = ''
        self.gerekli_harf = random.choice(self.alfabe)
        self.siradaki_no = 1
        self.basladi = False
        self.bitti = False
        self.toplam_sure = self.varsayilan_toplam
        self.hamle_sure = self.varsayilan_hamle
        self.son_tik = time.time()

    # ── Oyuncu yönetimi ──────────────────────────────────────────────────────
    def oyuncu_ekle(self, player_id, ad):
        """Odaya oyuncu ekler. Numarayı (1 veya 2) döndürür, dolu ise None."""
        if player_id in self.oyuncular:
            return self.oyuncular[player_id]['no']
        if len(self.oyuncular) >= 2:
            return None
        no = 1 if not self.oyuncular else 2
        self.oyuncular[player_id] = {'ad': ad, 'no': no}
        if len(self.oyuncular) == 2:
            self.basladi = True
            # Oyun gerçekten şimdi başlıyor — zamanlayıcıyı baştan kur
            # (lobby'de geçen bekleme süresi orta oyuna sayılmasın)
            self.toplam_sure = self.varsayilan_toplam
            self.hamle_sure = self.varsayilan_hamle
            self.son_tik = time.time()
        return no

    def oyuncu_cikar(self, player_id):
        ayrilan = self.oyuncular.pop(player_id, None)
        # Oyun ortasında ayrılma: oyunu bitir, kalan oyuncuya bildir
        if ayrilan and self.basladi and not self.bitti:
            self.ayrilan_ad = ayrilan['ad']
            self.bitti = True
        self.rematch_isteyenler.discard(player_id)

    def oyuncu_adi(self, no):
        for p in self.oyuncular.values():
            if p['no'] == no:
                return p['ad']
        return f'Player {no}'

    def dolu_mu(self):
        return len(self.oyuncular) >= 2

    # ── Rematch (tekrar oyna) ────────────────────────────────────────────────
    def rematch_iste(self, player_id):
        """
        Oyuncu yeniden oynamak istediğini bildirir.
        İki oyuncu da isteyince yeni oyun başlar. (yeni_basladi: bool) döndürür.
        """
        if player_id not in self.oyuncular:
            return False
        self.rematch_isteyenler.add(player_id)
        # İki oyuncu da hazır ve oda dolu mu?
        if self.dolu_mu() and len(self.rematch_isteyenler) >= 2:
            self._yeni_oyun_durumu()
            self.rematch_isteyenler.clear()
            self.ayrilan_ad = None
            self.basladi = True
            self.son_tik = time.time()
            return True
        return False

    # ── Oyun akışı ───────────────────────────────────────────────────────────
    def kelime_oyna(self, player_id, kelime):
        """
        Bir oyuncunun kelime denemesini işler.
        (basari: bool, kod: str, puan: int) döndürür.
        kod = istemcinin kendi dilinde çevireceği mesaj anahtarı.
        """
        if not self.basladi or self.bitti:
            return False, 'not_active', 0

        oyuncu = self.oyuncular.get(player_id)
        if not oyuncu:
            return False, 'not_in_room', 0

        if oyuncu['no'] != self.siradaki_no:
            return False, 'not_your_turn', 0

        kelime = kelime.strip().lower()
        if not kelime or not kelime.isalpha():
            return False, 'invalid', 0

        if kelime in self.kullanilan:
            return False, 'already_used', 0

        if kelime[0] != self.gerekli_harf:
            return False, 'must_start', 0

        if self.sozluk and kelime not in self.sozluk:
            return False, 'not_valid', 0

        # ── Success ──
        puan = kelime_puani(kelime)
        self.puan[oyuncu['no']] += puan
        self.kullanilan.add(kelime)
        self.zincir.append({'kelime': kelime, 'no': oyuncu['no'], 'puan': puan})
        self.son_kelime = kelime
        self.gerekli_harf = kelime[-1]
        self.siradaki_no = 2 if self.siradaki_no == 1 else 1
        self.hamle_sure = self.varsayilan_hamle   # reset turn timer when turn passes
        return True, 'points', puan

    def sure_guncelle(self):
        """Gerçek zamana göre süreleri düşürür. Süre bittiyse oyunu bitirir."""
        if not self.basladi or self.bitti:
            return
        simdi = time.time()
        gecen = simdi - self.son_tik
        if gecen >= 1.0:
            azalt = int(gecen)
            self.son_tik = simdi
            self.toplam_sure -= azalt
            self.hamle_sure -= azalt
            if self.toplam_sure <= 0 or self.hamle_sure <= 0:
                self.bitti = True

    def kazanan(self):
        if self.puan[1] > self.puan[2]:
            return 1
        if self.puan[2] > self.puan[1]:
            return 2
        return 0   # beraberlik

    def durum(self):
        """İstemciye gönderilecek tam oyun durumu (JSON uyumlu sözlük)."""
        return {
            'tip': 'durum',
            'oda': self.kod,
            'basladi': self.basladi,
            'bitti': self.bitti,
            'gerekli_harf': self.gerekli_harf,
            'son_kelime': self.son_kelime,
            'siradaki_no': self.siradaki_no,
            'puan': {'1': self.puan[1], '2': self.puan[2]},
            'toplam_sure': max(0, self.toplam_sure),
            'hamle_sure': max(0, self.hamle_sure),
            'kelime_sayisi': len(self.kullanilan),
            'kullanilan': sorted(self.kullanilan),
            'zincir': self.zincir,           # sıralı oynanış (üstte göstermek için)
            'oyuncular': {
                str(p['no']): p['ad'] for p in self.oyuncular.values()
            },
            'kazanan': self.kazanan() if self.bitti else None,
            'ayrilan_ad': self.ayrilan_ad,   # rakip ayrıldıysa adı
            'rematch_sayisi': len(self.rematch_isteyenler),
            'dict_lang': self.dict_lang,     # aktif sözlük dili
        }
