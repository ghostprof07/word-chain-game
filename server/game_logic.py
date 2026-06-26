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


def _sozluk_yukle():
    """İngilizce kelime listesini yükler (NLTK words dosyası ya da paket içi yedek)."""
    # Sunucu klasöründeki yerel kelime dosyası
    yerel = os.path.join(os.path.dirname(__file__), 'words_en.txt')
    if os.path.exists(yerel):
        with open(yerel, encoding='utf-8', errors='ignore') as f:
            return set(l.strip().lower() for l in f if l.strip().isalpha())

    # NLTK kullanıcı klasörü (geliştirme makinesinde)
    nltk_dosya = os.path.join(
        os.path.expanduser('~'),
        'AppData', 'Roaming', 'nltk_data', 'corpora', 'words', 'en'
    )
    if os.path.exists(nltk_dosya):
        with open(nltk_dosya, encoding='utf-8', errors='ignore') as f:
            return set(l.strip().lower() for l in f if l.strip().isalpha())

    # Hiçbiri yoksa boş küme (sözlük kontrolü devre dışı kalır)
    return set()


SOZLUK = _sozluk_yukle()


def kelime_puani(kelime):
    return sum(PUAN.get(h, 0) for h in kelime.lower())


# ══════════════════════════════════════════════════════════════════════════════
#  OYUN ODASI
# ══════════════════════════════════════════════════════════════════════════════
class GameRoom:
    """Tek bir oyun odasını ve durumunu temsil eder."""

    TOPLAM_SURE = 300   # toplam 5 dakika
    HAMLE_SURE = 20     # her hamle için saniye

    def __init__(self, oda_kodu):
        self.kod = oda_kodu
        self.oyuncular = {}          # player_id -> {"ad": str, "no": 1|2}
        self.puan = {1: 0, 2: 0}
        self.kullanilan = set()
        self.son_kelime = ''
        self.gerekli_harf = random.choice(string.ascii_lowercase)
        self.siradaki_no = 1         # sıradaki oyuncunun numarası (1 veya 2)
        self.basladi = False
        self.bitti = False
        self.toplam_sure = self.TOPLAM_SURE
        self.hamle_sure = self.HAMLE_SURE
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
            self.toplam_sure = self.TOPLAM_SURE
            self.hamle_sure = self.HAMLE_SURE
            self.son_tik = time.time()
        return no

    def oyuncu_cikar(self, player_id):
        self.oyuncular.pop(player_id, None)

    def oyuncu_adi(self, no):
        for p in self.oyuncular.values():
            if p['no'] == no:
                return p['ad']
        return f'Oyuncu {no}'

    def dolu_mu(self):
        return len(self.oyuncular) >= 2

    # ── Oyun akışı ───────────────────────────────────────────────────────────
    def kelime_oyna(self, player_id, kelime):
        """
        Bir oyuncunun kelime denemesini işler.
        (basari: bool, mesaj: str, puan: int) döndürür.
        """
        if not self.basladi or self.bitti:
            return False, 'Oyun aktif değil.', 0

        oyuncu = self.oyuncular.get(player_id)
        if not oyuncu:
            return False, 'Bu odada değilsin.', 0

        if oyuncu['no'] != self.siradaki_no:
            return False, 'Sıra sende değil!', 0

        kelime = kelime.strip().lower()
        if not kelime or not kelime.isalpha():
            return False, 'Geçersiz kelime.', 0

        if kelime in self.kullanilan:
            return False, 'Bu kelime zaten kullanıldı!', 0

        if kelime[0] != self.gerekli_harf:
            return False, f'"{self.gerekli_harf.upper()}" harfiyle başlamalı!', 0

        if SOZLUK and kelime not in SOZLUK:
            return False, 'Geçerli bir İngilizce kelime değil!', 0

        # ── Başarılı ──
        puan = kelime_puani(kelime)
        self.puan[oyuncu['no']] += puan
        self.kullanilan.add(kelime)
        self.son_kelime = kelime
        self.gerekli_harf = kelime[-1]
        self.siradaki_no = 2 if self.siradaki_no == 1 else 1
        self.hamle_sure = self.HAMLE_SURE   # sırayı geçince hamle süresi sıfırlanır
        return True, f'+{puan} puan!', puan

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
            'oyuncular': {
                str(p['no']): p['ad'] for p in self.oyuncular.values()
            },
            'kazanan': self.kazanan() if self.bitti else None,
        }
