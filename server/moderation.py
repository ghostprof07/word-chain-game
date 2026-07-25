"""
Sohbet moderasyonu — küfür/hakaret süzgeci.
==========================================
Apple App Store Kural 1.2 ve Google Play UGC (kullanıcı üretimi içerik)
politikası, sohbet barındıran uygulamalarda ÜÇ şey zorunlu kılıyor:
  1) uygunsuz içeriği süzen bir filtre   -> BU MODÜL
  2) içeriği raporlama mekanizması       -> main.py ('rapor' mesaj tipi)
  3) rahatsız eden kullanıcıyı engelleme -> istemci (client/main.py)

Sohbetin hangi dilde yazıldığı bilinmediğinden TÜM dillerin listeleri
birlikte taranır. Eşleşen kelime yıldızla maskelenir (mesaj tamamen
atılmaz — kullanıcı deneyimi için maskeleme yeterli ve standarttır).

KAÇAMAK (evasion) önlemleri:
  - leet yazım      : f4ck, $ik, @m  -> harfe çevrilir
  - harf tekrarı    : fuuuuck        -> fuck
  - aksan/büyük harf: PİÇ, çüş       -> sadeleştirilir
  - ayraçla bölme   : f.u.c.k, s i k -> "sıkıştırılmış" ikinci tarama

YENİ KELİME EKLEMEK: ilgili dilin kümesine ham haliyle ekle — normalizasyon
hem listeye hem girdiye aynı şekilde uygulandığı için aksanlı/büyük harfli
yazman sorun değil.
"""
import re
import unicodedata

# ── Kelime listeleri ─────────────────────────────────────────────────────────
# NOT: game_logic.YASAKLI oyun SÖZLÜĞÜNDEN çıkarılacak kelimelerdi (oynanamaz).
# Buradaki liste sohbet içindir ve daha geniştir: ağır küfür de kapsanır.
KUFURLER = {
    'en': {
        'nigger', 'nigga', 'negro', 'faggot', 'fag', 'kike', 'spic', 'chink',
        'gook', 'wetback', 'coon', 'tranny', 'dyke', 'cunt', 'retard',
        'fuck', 'fucker', 'fucking', 'motherfucker', 'shit', 'bullshit',
        'bitch', 'whore', 'slut', 'asshole', 'dickhead', 'bastard', 'wanker',
        'twat', 'pussy', 'cock', 'dick', 'penis', 'vagina', 'rape', 'rapist',
        # yaygın kasıtlı yanlış yazımlar (leet çevirisi bunları yakalamaz)
        'fck', 'fuk', 'fcuk', 'phuck', 'fuq', 'biatch', 'azzhole',
    },
    'tr': {
        'orospu', 'oruspu', 'piç', 'yarak', 'yarrak', 'amcık', 'amcik',
        'sik', 'siktir', 'sikeyim', 'sikik', 'ibne', 'pezevenk', 'kaltak',
        'göt', 'gavat', 'amına', 'aq', 'oç', 'sürtük', 'kahpe', 'meme',
        'taşak', 'yavşak', 'şerefsiz', 'puşt', 'gerizekalı', 'salak',
        'aptal', 'mal', 'ananı', 'avradını', 'tecavüz',
    },
    'de': {
        'neger', 'nigger', 'fotze', 'schwuchtel', 'hurensohn', 'kanake',
        'scheisse', 'scheiße', 'arschloch', 'wichser', 'schlampe', 'hure',
        'fick', 'ficken', 'fickt', 'muschi', 'schwanz', 'vergewaltigung',
    },
    'es': {
        'maricon', 'negrata', 'sudaca', 'puta', 'puto', 'mierda', 'joder',
        'cabron', 'gilipollas', 'coño', 'polla', 'chinga', 'chingar',
        'pendejo', 'verga', 'violacion',
    },
    'fr': {
        'negre', 'pede', 'encule', 'pute', 'salope', 'connard', 'connasse',
        'merde', 'putain', 'bite', 'couilles', 'enfoire', 'batard', 'viol',
    },
    'ru': {
        'хуй', 'хуя', 'хуе', 'пизда', 'пизде', 'ебать', 'ебал', 'ебут',
        'пидор', 'пидорас', 'пидарас', 'блядь', 'бляд', 'блять', 'мудак',
        'сука', 'сучка', 'гандон', 'долбоеб', 'уебок', 'изнасилование',
    },
}

# Ayraçlı kaçamak taramasında (f.u.c.k / s i k t i r) aranacak terimler.
# Yalnızca BAŞKA kelimenin içinde masum şekilde geçmeyecek olanlar konur —
# yoksa "assassin" içindeki "ass" gibi yanlış eşleşmeler olur (Scunthorpe
# sorunu). Bu yüzden kısa/genel kelimeler (ass, mal, am, sik...) buraya GİRMEZ.
SIKISTIRILMIS_ARA = {
    'nigger', 'nigga', 'faggot', 'motherfucker', 'fuck', 'cunt', 'whore',
    'asshole', 'bitch', 'orospu', 'amcık', 'yarrak', 'siktir', 'pezevenk',
    'hurensohn', 'arschloch', 'schwuchtel', 'maricon', 'gilipollas',
    'connard', 'salope', 'putain', 'пизда', 'пидорас', 'блядь', 'мудак',
}

# Rakam/sembolle harf taklidi (leet). Hepsi TEK karaktere eşlenir ki
# metnin uzunluğu değişmesin — maskeleme konumları kaymasın.
_LEET = str.maketrans({
    '4': 'a', '@': 'a', '3': 'e', '€': 'e', '1': 'i', '!': 'i', '|': 'i',
    '0': 'o', '5': 's', '$': 's', '7': 't', '8': 'b', '9': 'g', '+': 't',
})

# Aksan sadeleştirmede taban harfi olmayan özel harfler.
_OZEL = {'ß': 'ss', 'œ': 'oe', 'æ': 'ae', 'ı': 'i', 'ø': 'o', 'đ': 'd'}

# Harf dizileri (rakam/altçizgi hariç) — Kiril, Türkçe, aksanlı harfleri kapsar.
_KELIME = re.compile(r'[^\W\d_]+', re.UNICODE)


def _sadelestir(metin: str) -> str:
    """Aksanları taban harfe indirir, özel harfleri açar (ß->ss, ı->i).

    NOT: tüm metne birden uygulanır — karakter karakter yapılırsa Türkçe
    'İ'.lower() sonucu ortaya çıkan TEK BAŞINA birleşik nokta (U+0307)
    temizlenemez ve 'PİÇ' gibi yazımlar süzgeçten kaçar. Buradaki çıktı
    yalnızca KARŞILAŞTIRMA içindir; uzunluğun değişmesi sorun değil
    (maskeleme konumları ham metin üzerinden hesaplanır)."""
    for k, v in _OZEL.items():
        metin = metin.replace(k, v)
    ayrik = unicodedata.normalize('NFD', metin)
    return ''.join(c for c in ayrik if unicodedata.category(c) != 'Mn')


def _tekrar_kis(metin: str) -> str:
    """Arka arkaya tekrar eden harfleri teke indirir: fuuuck -> fuck."""
    return re.sub(r'(.)\1+', r'\1', metin)


def _normalize(metin: str) -> str:
    """Karşılaştırma biçimi — hem listeye hem girdiye AYNI şekilde uygulanır."""
    return _tekrar_kis(_sadelestir(metin.lower()))


def _liste_hazirla():
    """Tüm dillerin kelimelerini tek bir normalize edilmiş kümede toplar."""
    kume = set()
    for kelimeler in KUFURLER.values():
        for k in kelimeler:
            n = _normalize(k)
            if n:
                kume.add(n)
    return kume


_YASAK = _liste_hazirla()
_YASAK_SIKISTIRILMIS = {_normalize(k) for k in SIKISTIRILMIS_ARA}


def temizle(metin: str):
    """
    Küfür/hakaret içeren kelimeleri yıldızla maskeler.

    Döner: (temizlenmis_metin, filtrelendi_mi)
      filtrelendi_mi=True ise mesajda en az bir uygunsuz kelime yakalandı
      (raporlama/loglama için sunucu tarafında kullanılır).
    """
    if not metin:
        return metin, False

    # Leet çevirisi 1:1 olduğu için karakter konumları korunur — maskeyi
    # ORİJİNAL metne aynı konumlardan uygulayabiliriz.
    leet = metin.translate(_LEET)

    karakterler = list(metin)
    filtrelendi = False

    # 1) Kelime kelime tarama
    for m in _KELIME.finditer(leet):
        if _normalize(m.group()) in _YASAK:
            for i in range(m.start(), m.end()):
                karakterler[i] = '*'
            filtrelendi = True

    if filtrelendi:
        return ''.join(karakterler), True

    # 2) Ayraçla bölünmüş kaçamak taraması: "f.u.c.k", "s i k t i r".
    #    Mesajın TAMAMINI birleştirmek yanlış eşleşme üretir (ör. "kof uçkur"
    #    -> "kofuckur" içinde "fuck" geçer). Bu yüzden yalnızca ARDIŞIK KISA
    #    parçalar (<=2 harf) birleştirilir — kaçamağın tipik imzası budur.
    parcalar = [m for m in _KELIME.finditer(leet)]
    i = 0
    while i < len(parcalar):
        if len(parcalar[i].group()) > 2:
            i += 1
            continue
        j = i
        while j + 1 < len(parcalar) and len(parcalar[j + 1].group()) <= 2:
            j += 1
        if j > i:   # en az iki kısa parça yan yana
            birlesik = _normalize(''.join(p.group() for p in parcalar[i:j + 1]))
            if any(y and y in birlesik for y in _YASAK_SIKISTIRILMIS):
                for k in range(parcalar[i].start(), parcalar[j].end()):
                    karakterler[k] = '*'
                filtrelendi = True
        i = j + 1

    return ''.join(karakterler), filtrelendi


def uygunsuz_mu(metin: str) -> bool:
    """Sadece kontrol — mesaj uygunsuz içerik barındırıyor mu?"""
    return temizle(metin)[1]
