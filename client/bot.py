"""
Offline bot — gerekli harfle başlayan, kullanılmamış geçerli bir kelime seçer.
Zorluk seviyesi hem düşünme süresini hem kelime kalitesini hem de bazen
'bulamama' (pas) olasılığını belirler. Sözlük (game_logic.GameRoom.sozluk)
zaten doğrulama için yüklü olduğundan bot ek veri gerektirmez.
"""
import random

from game_logic import kelime_puani

ZORLUKLAR = ('kolay', 'orta', 'zor')


class Bot:
    def __init__(self, oda, zorluk='orta'):
        self.oda = oda
        self.zorluk = zorluk if zorluk in ZORLUKLAR else 'orta'
        # Başlangıç harfine göre indeks — her hamlede hızlı aday bulmak için.
        self._index = {}
        for w in oda.sozluk:
            if w:
                self._index.setdefault(w[0], []).append(w)

    def gecikme(self):
        """Botun 'düşünme' süresi (saniye) — zorluğa göre."""
        return {
            'kolay': random.uniform(4.5, 8.0),
            'orta': random.uniform(2.5, 5.0),
            'zor': random.uniform(1.2, 3.0),
        }[self.zorluk]

    def kelime_sec(self):
        """Gerekli harfle başlayan, kullanılmamış bir kelime döndürür; yoksa None."""
        adaylar = [w for w in self._index.get(self.oda.gerekli_harf, ())
                   if w not in self.oda.kullanilan]
        if not adaylar:
            return None
        if self.zorluk == 'zor':
            adaylar.sort(key=lambda w: kelime_puani(w, self.oda.dict_lang) + len(w), reverse=True)
            return random.choice(adaylar[:25])
        if self.zorluk == 'kolay':
            kisa = sorted(adaylar, key=len)[:200]
            return random.choice(kisa)
        return random.choice(adaylar)
