"""
Arayüz dili (UI i18n) — uygulama metinlerini çoklu dilde tutar.

YENİ DİL EKLEMEK:
  1) DILLER sözlüğüne dil kodunu + görünen adını ekle (örn. 'de': 'Deutsch')
  2) CEVIRILER sözlüğüne o dil için tüm anahtarların çevirisini ekle
  (Sözlük/kelime doğrulama dili AYRI — bkz. sunucu tarafı.)

Kullanım:
  from i18n import t, dil_ayarla
  dil_ayarla('tr');  t('create_room')  -> 'ODA OLUŞTUR'
"""

# Arayüzde seçilebilecek diller: kod -> görünen ad
DILLER = {
    'en': 'English',
    'tr': 'Türkçe',
}

CEVIRILER = {
    # ── İngilizce ──
    'en': {
        'subtitle': 'Online — play on two devices',
        'your_name': 'Your name...',
        'game_duration': 'Game duration',
        'dur_3': '3 min', 'dur_5': '5 min', 'dur_10': '10 min',
        'create_room': 'CREATE ROOM',
        'or': '— or —',
        'room_code_hint': 'Room code (e.g. AB12)',
        'join_with_code': 'JOIN WITH CODE',
        'settings': 'Settings',
        'creating_room': 'Creating room...\n(first connect may take up to a minute)',
        'no_server': 'Could not reach server!',
        'invalid_code': 'Enter a valid room code.',
        'connecting': 'Connecting...',
        'room_code': 'ROOM CODE',
        'share_code': 'Share this code with your opponent',
        'waiting_opponent': 'Waiting for opponent...',
        'cancel': 'CANCEL',
        'quit': 'QUIT',
        'words_count': '{n} words',
        'no_words_yet': 'No words yet',
        'player': 'Player',
        'your_turn': 'YOUR TURN — type a word!',
        'is_playing': '{name} is playing...',
        'last': 'Last: {word}',
        'type_word': 'Type a word...',
        'send': 'SEND',
        'game_over': 'GAME OVER',
        'draw': 'DRAW!',
        'you_won': 'YOU WON!',
        'you_lost': 'YOU LOST',
        'opponent_left': 'OPPONENT LEFT',
        'left_game': '{name} left the game',
        'pts': 'pts',
        'words': 'Words', 'total': 'Total', 'avg': 'Avg',
        'words_used': 'Words Used',
        'play_again': 'PLAY AGAIN',
        'main_menu': 'MAIN MENU',
        'opponent_wants_rematch': 'Opponent wants a rematch!',
        'connection_lost': 'Connection lost.',
        'error': 'Error!',
        'room_full': 'Room is full!',
        'chat': 'Chat',
        'type_message': 'Type a message...',
        # Ayarlar ekranı
        'settings_title': 'SETTINGS',
        'app_language': 'App Language',
        'app_language_desc': 'Language of the interface',
        'word_dictionary': 'Word Dictionary',
        'word_dictionary_desc': 'Language used to validate words',
        'done': 'DONE',
        # Sunucudan gelen kelime sonucu kodları
        'msg_not_active': 'Game is not active.',
        'msg_not_in_room': 'You are not in this room.',
        'msg_not_your_turn': 'Not your turn!',
        'msg_invalid': 'Invalid word.',
        'msg_already_used': 'This word was already used!',
        'msg_must_start': 'Must start with "{letter}"!',
        'msg_not_valid': 'Not a valid word!',
        'msg_points': '+{points} pts!',
    },
    # ── Türkçe ──
    'tr': {
        'subtitle': 'Online — iki cihazda oyna',
        'your_name': 'Adın...',
        'game_duration': 'Oyun süresi',
        'dur_3': '3 dk', 'dur_5': '5 dk', 'dur_10': '10 dk',
        'create_room': 'ODA OLUŞTUR',
        'or': '— veya —',
        'room_code_hint': 'Oda kodu (örn. AB12)',
        'join_with_code': 'KODLA KATIL',
        'settings': 'Ayarlar',
        'creating_room': 'Oda oluşturuluyor...\n(ilk bağlantı bir dakika sürebilir)',
        'no_server': 'Sunucuya ulaşılamadı!',
        'invalid_code': 'Geçerli bir oda kodu gir.',
        'connecting': 'Bağlanılıyor...',
        'room_code': 'ODA KODU',
        'share_code': 'Bu kodu rakibinle paylaş',
        'waiting_opponent': 'Rakip bekleniyor...',
        'cancel': 'İPTAL',
        'quit': 'ÇIK',
        'words_count': '{n} kelime',
        'no_words_yet': 'Henüz kelime yok',
        'player': 'Oyuncu',
        'your_turn': 'SIRA SENDE — kelime yaz!',
        'is_playing': '{name} oynuyor...',
        'last': 'Son: {word}',
        'type_word': 'Kelime yaz...',
        'send': 'GÖNDER',
        'game_over': 'OYUN BİTTİ',
        'draw': 'BERABERLİK!',
        'you_won': 'KAZANDIN!',
        'you_lost': 'KAYBETTİN',
        'opponent_left': 'RAKİP AYRILDI',
        'left_game': '{name} oyundan ayrıldı',
        'pts': 'puan',
        'words': 'Kelime', 'total': 'Toplam', 'avg': 'Ort',
        'words_used': 'Kullanılan Kelimeler',
        'play_again': 'TEKRAR OYNA',
        'main_menu': 'ANA MENÜ',
        'opponent_wants_rematch': 'Rakip tekrar oynamak istiyor!',
        'connection_lost': 'Bağlantı koptu.',
        'error': 'Hata!',
        'room_full': 'Oda dolu!',
        'chat': 'Sohbet',
        'type_message': 'Mesaj yaz...',
        'settings_title': 'AYARLAR',
        'app_language': 'Uygulama Dili',
        'app_language_desc': 'Arayüzün dili',
        'word_dictionary': 'Sözlük',
        'word_dictionary_desc': 'Kelimelerin doğrulandığı dil',
        'done': 'TAMAM',
        'msg_not_active': 'Oyun aktif değil.',
        'msg_not_in_room': 'Bu odada değilsin.',
        'msg_not_your_turn': 'Sıra sende değil!',
        'msg_invalid': 'Geçersiz kelime.',
        'msg_already_used': 'Bu kelime zaten kullanıldı!',
        'msg_must_start': '"{letter}" harfiyle başlamalı!',
        'msg_not_valid': 'Geçerli bir kelime değil!',
        'msg_points': '+{points} puan!',
    },
}

_aktif = 'en'


def dil_ayarla(kod):
    global _aktif
    if kod in CEVIRILER:
        _aktif = kod


def aktif_dil():
    return _aktif


def t(anahtar, **kw):
    """Anahtarın aktif dildeki karşılığını döndürür; {param} alanlarını doldurur."""
    metin = CEVIRILER.get(_aktif, CEVIRILER['en']).get(anahtar)
    if metin is None:
        metin = CEVIRILER['en'].get(anahtar, anahtar)
    if kw:
        try:
            metin = metin.format(**kw)
        except Exception:
            pass
    return metin
