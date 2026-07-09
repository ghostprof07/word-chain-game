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
    'de': 'Deutsch',
    'es': 'Español',
    'fr': 'Français',
    'ru': 'Русский',
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
        'solo_play': 'PLAY OFFLINE',
        'solo_title': 'PLAY OFFLINE',
        'two_players': 'TWO PLAYERS — ONE PHONE',
        'pass_and_play': 'Pass & Play',
        'player2_name': 'Player 2 name...',
        'turn_of': '{name}, your turn — type a word!',
        'won_name': '{name} WON!',
        'all_words': 'All Words',
        'search_word': 'Search word...',
        'vs_bot': 'vs Bot',
        'training': 'Training',
        'training_desc': 'Chain as long as you can',
        'difficulty': 'Difficulty',
        'easy': 'Easy', 'medium': 'Medium', 'hard': 'Hard',
        'bot': 'Bot',
        'best_score': 'Best: {n}',
        'statistics': 'Statistics',
        'games': 'Games', 'wins': 'Wins', 'losses': 'Losses', 'draws': 'Draws',
        'win_rate': 'Win rate', 'words_played': 'Words played',
        'best_word': 'Best word', 'reset': 'Reset', 'sound': 'Sound',
        'how_to_play': 'How to Play?',
        'faq_text': (
            '[b]Which words are accepted?[/b]\n'
            '• Every word must start with the shown letter — the last '
            'letter of the previous word.\n'
            '• Words are checked against the selected dictionary language; '
            'only words of that language are valid.\n'
            '• The dictionary contains base (dictionary) forms — proper '
            'names and most inflected forms are not accepted.\n'
            '• Each word can be used only once per game.\n'
            '• Offensive words are not accepted.\n\n'
            '[b]Scoring & time[/b]\n'
            '• Rare letters score more points.\n'
            '• If your turn timer runs out, you lose — regardless of score.\n'
            '• When total time ends, the higher score wins.\n'
            '• Leaving mid-game counts as a loss.\n\n'
            '[b]Letters & accents[/b]\n'
            '• You can type without accents (é → e).\n'
            '• Turkish: a word ending in ğ chains to g.\n'
            '• Russian: ё = е; endings ь/ъ/ы skip '
            'back one letter.'
        ),
        'settings': 'Settings',
        'creating_room': 'Creating room...\n(first connect may take up to a minute)',
        'no_server': 'Could not reach server!',
        'invalid_code': 'Enter a valid room code.',
        'connecting': 'Connecting...',
        'room_code': 'ROOM CODE',
        'share_code': 'Share this code with your opponent',
        'waiting_opponent': 'Waiting for opponent...',
        'get_ready': 'Get ready!',
        'starting_in': 'Starting in {n}...',
        'lobby_chat_hint': 'Say hi before you start',
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
        'solo_play': 'OFFLINE OYNA',
        'solo_title': 'OFFLINE OYUN',
        'two_players': 'İKİ KİŞİ — TEK TELEFON',
        'pass_and_play': 'Elden Ele',
        'player2_name': '2. oyuncunun adı...',
        'turn_of': '{name}, sıra sende — kelime yaz!',
        'won_name': '{name} KAZANDI!',
        'all_words': 'Tüm Kelimeler',
        'search_word': 'Kelime ara...',
        'vs_bot': 'Bot\'a Karşı',
        'training': 'Antrenman',
        'training_desc': 'Zinciri olabildiğince uzat',
        'difficulty': 'Zorluk',
        'easy': 'Kolay', 'medium': 'Orta', 'hard': 'Zor',
        'bot': 'Bot',
        'best_score': 'En iyi: {n}',
        'statistics': 'İstatistikler',
        'games': 'Oyun', 'wins': 'Galibiyet', 'losses': 'Mağlubiyet', 'draws': 'Beraberlik',
        'win_rate': 'Kazanma %', 'words_played': 'Oynanan kelime',
        'best_word': 'En iyi kelime', 'reset': 'Sıfırla', 'sound': 'Ses',
        'how_to_play': 'Nasıl Oynanır?',
        'faq_text': (
            '[b]Hangi kelimeler kabul edilir?[/b]\n'
            '• Her kelime, gösterilen harfle — yani önceki kelimenin son '
            'harfiyle — başlamalıdır.\n'
            '• Kelimeler seçili sözlük diline göre denetlenir; yalnızca o '
            'dilin kelimeleri geçerlidir.\n'
            '• Sözlükte kelimelerin temel (sözlük) halleri vardır — özel '
            'isimler ve çoğu çekimli hal kabul edilmez.\n'
            '• Bir kelime oyunda yalnızca bir kez kullanılabilir.\n'
            '• Hakaret içeren kelimeler kabul edilmez.\n\n'
            '[b]Puan ve süre[/b]\n'
            '• Nadir harfler daha çok puan getirir.\n'
            '• Hamle süreniz dolarsa puandan bağımsız kaybedersiniz.\n'
            '• Toplam süre bitince yüksek puanlı kazanır.\n'
            '• Oyun ortasında çıkmak mağlubiyet sayılır.\n\n'
            '[b]Harfler ve aksanlar[/b]\n'
            '• Aksansız yazabilirsiniz (é → e).\n'
            '• Türkçe: ğ ile biten kelimeden sonra g ile başlanır.\n'
            '• Rusça: ё = е; sondaki ь/ъ/ы bir önceki harfe atlanır.'
        ),
        'settings': 'Ayarlar',
        'creating_room': 'Oda oluşturuluyor...\n(ilk bağlantı bir dakika sürebilir)',
        'no_server': 'Sunucuya ulaşılamadı!',
        'invalid_code': 'Geçerli bir oda kodu gir.',
        'connecting': 'Bağlanılıyor...',
        'room_code': 'ODA KODU',
        'share_code': 'Bu kodu rakibinle paylaş',
        'waiting_opponent': 'Rakip bekleniyor...',
        'get_ready': 'Hazır ol!',
        'starting_in': '{n} saniye içinde başlıyor...',
        'lobby_chat_hint': 'Başlamadan selam ver',
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
    # ── Almanca ──
    'de': {
        'subtitle': 'Online — auf zwei Geräten spielen',
        'your_name': 'Dein Name...',
        'game_duration': 'Spieldauer',
        'dur_3': '3 Min', 'dur_5': '5 Min', 'dur_10': '10 Min',
        'create_room': 'RAUM ERSTELLEN',
        'or': '— oder —',
        'room_code_hint': 'Raumcode (z.B. AB12)',
        'join_with_code': 'MIT CODE BEITRETEN',
        'solo_play': 'OFFLINE SPIELEN',
        'solo_title': 'OFFLINE SPIELEN',
        'two_players': 'ZWEI SPIELER — EIN HANDY',
        'pass_and_play': 'Abwechselnd spielen',
        'player2_name': 'Name von Spieler 2...',
        'turn_of': '{name}, du bist dran — tippe ein Wort!',
        'won_name': '{name} HAT GEWONNEN!',
        'all_words': 'Alle Wörter',
        'search_word': 'Wort suchen...',
        'vs_bot': 'Gegen Bot',
        'training': 'Training',
        'training_desc': 'Verkette so lange du kannst',
        'difficulty': 'Schwierigkeit',
        'easy': 'Leicht', 'medium': 'Mittel', 'hard': 'Schwer',
        'bot': 'Bot',
        'best_score': 'Beste: {n}',
        'statistics': 'Statistiken',
        'games': 'Spiele', 'wins': 'Siege', 'losses': 'Niederlagen', 'draws': 'Unentschieden',
        'win_rate': 'Siegquote', 'words_played': 'Wörter gespielt',
        'best_word': 'Bestes Wort', 'reset': 'Zurücksetzen', 'sound': 'Ton',
        'how_to_play': 'Wie spielt man?',
        'faq_text': (
            '[b]Welche Wörter werden akzeptiert?[/b]\n'
            '• Jedes Wort muss mit dem angezeigten Buchstaben beginnen — dem '
            'letzten Buchstaben des vorherigen Wortes.\n'
            '• Wörter werden gegen die gewählte Wörterbuchsprache geprüft; '
            'nur Wörter dieser Sprache sind gültig.\n'
            '• Das Wörterbuch enthält Grundformen — Eigennamen und die '
            'meisten gebeugten Formen werden nicht akzeptiert.\n'
            '• Jedes Wort kann pro Spiel nur einmal verwendet werden.\n'
            '• Beleidigende Wörter werden nicht akzeptiert.\n\n'
            '[b]Punkte & Zeit[/b]\n'
            '• Seltene Buchstaben bringen mehr Punkte.\n'
            '• Läuft deine Zugzeit ab, verlierst du — unabhängig vom Stand.\n'
            '• Endet die Gesamtzeit, gewinnt die höhere Punktzahl.\n'
            '• Wer das Spiel vorzeitig verlässt, verliert.\n\n'
            '[b]Buchstaben & Akzente[/b]\n'
            '• Du kannst ohne Umlaute tippen (ä → a, ß → ss).\n'
            '• Türkisch: Ein Wort, das auf ğ endet, wird mit g fortgesetzt.\n'
            '• Russisch: ё = е; Endungen ь/ъ/ы springen einen Buchstaben zurück.'
        ),
        'settings': 'Einstellungen',
        'creating_room': 'Raum wird erstellt...\n(erste Verbindung kann bis zu einer Minute dauern)',
        'no_server': 'Server nicht erreichbar!',
        'invalid_code': 'Gib einen gültigen Raumcode ein.',
        'connecting': 'Verbinde...',
        'room_code': 'RAUMCODE',
        'share_code': 'Teile diesen Code mit deinem Gegner',
        'waiting_opponent': 'Warte auf Gegner...',
        'get_ready': 'Macht euch bereit!',
        'starting_in': 'Start in {n}...',
        'lobby_chat_hint': 'Sag Hallo vor dem Start',
        'cancel': 'ABBRECHEN',
        'quit': 'VERLASSEN',
        'words_count': '{n} Wörter',
        'no_words_yet': 'Noch keine Wörter',
        'player': 'Spieler',
        'your_turn': 'DU BIST DRAN — tippe ein Wort!',
        'is_playing': '{name} ist am Zug...',
        'last': 'Letztes: {word}',
        'type_word': 'Wort eingeben...',
        'send': 'SENDEN',
        'game_over': 'SPIEL VORBEI',
        'draw': 'UNENTSCHIEDEN!',
        'you_won': 'GEWONNEN!',
        'you_lost': 'VERLOREN',
        'opponent_left': 'GEGNER GING',
        'left_game': '{name} hat das Spiel verlassen',
        'pts': 'Pkt',
        'words': 'Wörter', 'total': 'Gesamt', 'avg': 'Ø',
        'words_used': 'Verwendete Wörter',
        'play_again': 'NOCHMAL SPIELEN',
        'main_menu': 'HAUPTMENÜ',
        'opponent_wants_rematch': 'Gegner will eine Revanche!',
        'connection_lost': 'Verbindung verloren.',
        'error': 'Fehler!',
        'room_full': 'Raum ist voll!',
        'chat': 'Chat',
        'type_message': 'Nachricht eingeben...',
        'settings_title': 'EINSTELLUNGEN',
        'app_language': 'App-Sprache',
        'app_language_desc': 'Sprache der Oberfläche',
        'word_dictionary': 'Wörterbuch',
        'word_dictionary_desc': 'Sprache zur Wortprüfung',
        'done': 'FERTIG',
        'msg_not_active': 'Spiel ist nicht aktiv.',
        'msg_not_in_room': 'Du bist nicht in diesem Raum.',
        'msg_not_your_turn': 'Du bist nicht dran!',
        'msg_invalid': 'Ungültiges Wort.',
        'msg_already_used': 'Dieses Wort wurde schon benutzt!',
        'msg_must_start': 'Muss mit "{letter}" beginnen!',
        'msg_not_valid': 'Kein gültiges Wort!',
        'msg_points': '+{points} Pkt!',
    },
    # ── İspanyolca ──
    'es': {
        'subtitle': 'En línea — juega en dos dispositivos',
        'your_name': 'Tu nombre...',
        'game_duration': 'Duración del juego',
        'dur_3': '3 min', 'dur_5': '5 min', 'dur_10': '10 min',
        'create_room': 'CREAR SALA',
        'or': '— o —',
        'room_code_hint': 'Código de sala (ej. AB12)',
        'join_with_code': 'UNIRSE CON CÓDIGO',
        'solo_play': 'JUGAR SIN CONEXIÓN',
        'solo_title': 'JUGAR SIN CONEXIÓN',
        'two_players': 'DOS JUGADORES — UN MÓVIL',
        'pass_and_play': 'Pasar y jugar',
        'player2_name': 'Nombre del jugador 2...',
        'turn_of': '{name}, tu turno — ¡escribe una palabra!',
        'won_name': '¡GANÓ {name}!',
        'all_words': 'Todas las palabras',
        'search_word': 'Buscar palabra...',
        'vs_bot': 'vs Bot',
        'training': 'Entrenamiento',
        'training_desc': 'Encadena todo lo que puedas',
        'difficulty': 'Dificultad',
        'easy': 'Fácil', 'medium': 'Medio', 'hard': 'Difícil',
        'bot': 'Bot',
        'best_score': 'Mejor: {n}',
        'statistics': 'Estadísticas',
        'games': 'Partidas', 'wins': 'Victorias', 'losses': 'Derrotas', 'draws': 'Empates',
        'win_rate': '% Victorias', 'words_played': 'Palabras jugadas',
        'best_word': 'Mejor palabra', 'reset': 'Reiniciar', 'sound': 'Sonido',
        'how_to_play': '¿Cómo se juega?',
        'faq_text': (
            '[b]¿Qué palabras se aceptan?[/b]\n'
            '• Cada palabra debe empezar por la letra mostrada — la última '
            'letra de la palabra anterior.\n'
            '• Las palabras se comprueban con el idioma de diccionario '
            'elegido; solo valen palabras de ese idioma.\n'
            '• El diccionario contiene formas base — los nombres propios y '
            'la mayoría de formas flexionadas no se aceptan.\n'
            '• Cada palabra solo puede usarse una vez por partida.\n'
            '• No se aceptan palabras ofensivas.\n\n'
            '[b]Puntos y tiempo[/b]\n'
            '• Las letras raras dan más puntos.\n'
            '• Si se agota tu tiempo de turno, pierdes — sin importar la '
            'puntuación.\n'
            '• Al acabar el tiempo total, gana la puntuación más alta.\n'
            '• Abandonar a mitad de partida cuenta como derrota.\n\n'
            '[b]Letras y acentos[/b]\n'
            '• Puedes escribir sin tildes (é → e); la ñ se conserva.\n'
            '• Turco: una palabra que termina en ğ continúa con g.\n'
            '• Ruso: ё = е; las terminaciones ь/ъ/ы saltan una letra atrás.'
        ),
        'settings': 'Ajustes',
        'creating_room': 'Creando sala...\n(la primera conexión puede tardar un minuto)',
        'no_server': '¡No se pudo conectar al servidor!',
        'invalid_code': 'Introduce un código válido.',
        'connecting': 'Conectando...',
        'room_code': 'CÓDIGO DE SALA',
        'share_code': 'Comparte este código con tu rival',
        'waiting_opponent': 'Esperando al rival...',
        'get_ready': '¡Preparados!',
        'starting_in': 'Empieza en {n}...',
        'lobby_chat_hint': 'Saluda antes de empezar',
        'cancel': 'CANCELAR',
        'quit': 'SALIR',
        'words_count': '{n} palabras',
        'no_words_yet': 'Aún no hay palabras',
        'player': 'Jugador',
        'your_turn': '¡TU TURNO — escribe una palabra!',
        'is_playing': '{name} está jugando...',
        'last': 'Última: {word}',
        'type_word': 'Escribe una palabra...',
        'send': 'ENVIAR',
        'game_over': 'FIN DEL JUEGO',
        'draw': '¡EMPATE!',
        'you_won': '¡GANASTE!',
        'you_lost': 'PERDISTE',
        'opponent_left': 'EL RIVAL SE FUE',
        'left_game': '{name} dejó el juego',
        'pts': 'pts',
        'words': 'Palabras', 'total': 'Total', 'avg': 'Prom',
        'words_used': 'Palabras usadas',
        'play_again': 'JUGAR DE NUEVO',
        'main_menu': 'MENÚ PRINCIPAL',
        'opponent_wants_rematch': '¡El rival quiere la revancha!',
        'connection_lost': 'Conexión perdida.',
        'error': '¡Error!',
        'room_full': '¡La sala está llena!',
        'chat': 'Chat',
        'type_message': 'Escribe un mensaje...',
        'settings_title': 'AJUSTES',
        'app_language': 'Idioma de la app',
        'app_language_desc': 'Idioma de la interfaz',
        'word_dictionary': 'Diccionario',
        'word_dictionary_desc': 'Idioma para validar palabras',
        'done': 'LISTO',
        'msg_not_active': 'El juego no está activo.',
        'msg_not_in_room': 'No estás en esta sala.',
        'msg_not_your_turn': '¡No es tu turno!',
        'msg_invalid': 'Palabra no válida.',
        'msg_already_used': '¡Esta palabra ya se usó!',
        'msg_must_start': '¡Debe empezar con "{letter}"!',
        'msg_not_valid': '¡No es una palabra válida!',
        'msg_points': '¡+{points} pts!',
    },
    # ── Fransızca ──
    'fr': {
        'subtitle': 'En ligne — jouez sur deux appareils',
        'your_name': 'Ton nom...',
        'game_duration': 'Durée de la partie',
        'dur_3': '3 min', 'dur_5': '5 min', 'dur_10': '10 min',
        'create_room': 'CRÉER UN SALON',
        'or': '— ou —',
        'room_code_hint': 'Code du salon (ex. AB12)',
        'join_with_code': 'REJOINDRE AVEC CODE',
        'solo_play': 'JOUER HORS LIGNE',
        'solo_title': 'JOUER HORS LIGNE',
        'two_players': 'DEUX JOUEURS — UN TÉLÉPHONE',
        'pass_and_play': 'Tour à tour',
        'player2_name': 'Nom du joueur 2...',
        'turn_of': '{name}, à toi — écris un mot !',
        'won_name': '{name} A GAGNÉ !',
        'all_words': 'Tous les mots',
        'search_word': 'Chercher un mot...',
        'vs_bot': 'vs Bot',
        'training': 'Entraînement',
        'training_desc': 'Enchaîne le plus longtemps possible',
        'difficulty': 'Difficulté',
        'easy': 'Facile', 'medium': 'Moyen', 'hard': 'Difficile',
        'bot': 'Bot',
        'best_score': 'Meilleur : {n}',
        'statistics': 'Statistiques',
        'games': 'Parties', 'wins': 'Victoires', 'losses': 'Défaites', 'draws': 'Nuls',
        'win_rate': '% Victoires', 'words_played': 'Mots joués',
        'best_word': 'Meilleur mot', 'reset': 'Réinitialiser', 'sound': 'Son',
        'how_to_play': 'Comment jouer ?',
        'faq_text': (
            '[b]Quels mots sont acceptés ?[/b]\n'
            '• Chaque mot doit commencer par la lettre affichée — la '
            'dernière lettre du mot précédent.\n'
            '• Les mots sont vérifiés selon la langue du dictionnaire '
            'choisie ; seuls les mots de cette langue sont valides.\n'
            '• Le dictionnaire contient les formes de base — les noms '
            'propres et la plupart des formes fléchies sont refusés.\n'
            '• Chaque mot ne peut être joué qu\'une fois par partie.\n'
            '• Les mots offensants sont refusés.\n\n'
            '[b]Points et temps[/b]\n'
            '• Les lettres rares rapportent plus de points.\n'
            '• Si votre temps de tour expire, vous perdez — quel que soit '
            'le score.\n'
            '• À la fin du temps total, le meilleur score gagne.\n'
            '• Quitter en cours de partie compte comme une défaite.\n\n'
            '[b]Lettres et accents[/b]\n'
            '• Vous pouvez écrire sans accents (é → e).\n'
            '• Turc : un mot finissant par ğ enchaîne sur g.\n'
            '• Russe : ё = е ; les finales ь/ъ/ы reculent d\'une lettre.'
        ),
        'settings': 'Paramètres',
        'creating_room': 'Création du salon...\n(la première connexion peut prendre une minute)',
        'no_server': 'Serveur injoignable !',
        'invalid_code': 'Entre un code valide.',
        'connecting': 'Connexion...',
        'room_code': 'CODE DU SALON',
        'share_code': 'Partage ce code avec ton adversaire',
        'waiting_opponent': 'En attente de l’adversaire...',
        'get_ready': 'Préparez-vous !',
        'starting_in': 'Début dans {n}...',
        'lobby_chat_hint': 'Dis bonjour avant de commencer',
        'cancel': 'ANNULER',
        'quit': 'QUITTER',
        'words_count': '{n} mots',
        'no_words_yet': 'Pas encore de mots',
        'player': 'Joueur',
        'your_turn': 'À TON TOUR — écris un mot !',
        'is_playing': '{name} joue...',
        'last': 'Dernier : {word}',
        'type_word': 'Écris un mot...',
        'send': 'ENVOYER',
        'game_over': 'PARTIE TERMINÉE',
        'draw': 'ÉGALITÉ !',
        'you_won': 'TU AS GAGNÉ !',
        'you_lost': 'TU AS PERDU',
        'opponent_left': 'ADVERSAIRE PARTI',
        'left_game': '{name} a quitté la partie',
        'pts': 'pts',
        'words': 'Mots', 'total': 'Total', 'avg': 'Moy',
        'words_used': 'Mots utilisés',
        'play_again': 'REJOUER',
        'main_menu': 'MENU PRINCIPAL',
        'opponent_wants_rematch': 'L’adversaire veut une revanche !',
        'connection_lost': 'Connexion perdue.',
        'error': 'Erreur !',
        'room_full': 'Le salon est plein !',
        'chat': 'Chat',
        'type_message': 'Écris un message...',
        'settings_title': 'PARAMÈTRES',
        'app_language': 'Langue de l’app',
        'app_language_desc': 'Langue de l’interface',
        'word_dictionary': 'Dictionnaire',
        'word_dictionary_desc': 'Langue de validation des mots',
        'done': 'TERMINÉ',
        'msg_not_active': 'La partie n’est pas active.',
        'msg_not_in_room': 'Tu n’es pas dans ce salon.',
        'msg_not_your_turn': 'Ce n’est pas ton tour !',
        'msg_invalid': 'Mot invalide.',
        'msg_already_used': 'Ce mot a déjà été utilisé !',
        'msg_must_start': 'Doit commencer par "{letter}" !',
        'msg_not_valid': 'Mot non valide !',
        'msg_points': '+{points} pts !',
    },
    # ── Rusça ──
    'ru': {
        'subtitle': 'Онлайн — играйте на двух устройствах',
        'your_name': 'Твоё имя...',
        'game_duration': 'Длительность игры',
        'dur_3': '3 мин', 'dur_5': '5 мин', 'dur_10': '10 мин',
        'create_room': 'СОЗДАТЬ КОМНАТУ',
        'or': '— или —',
        'room_code_hint': 'Код комнаты (напр. AB12)',
        'join_with_code': 'ВОЙТИ ПО КОДУ',
        'solo_play': 'ИГРАТЬ ОФЛАЙН',
        'solo_title': 'ИГРАТЬ ОФЛАЙН',
        'two_players': 'ДВА ИГРОКА — ОДИН ТЕЛЕФОН',
        'pass_and_play': 'По очереди',
        'player2_name': 'Имя игрока 2...',
        'turn_of': '{name}, твой ход — введи слово!',
        'won_name': '{name} ПОБЕДИЛ!',
        'all_words': 'Все слова',
        'search_word': 'Поиск слова...',
        'vs_bot': 'Против бота',
        'training': 'Тренировка',
        'training_desc': 'Стройте цепочку как можно дольше',
        'difficulty': 'Сложность',
        'easy': 'Легко', 'medium': 'Средне', 'hard': 'Сложно',
        'bot': 'Бот',
        'best_score': 'Рекорд: {n}',
        'statistics': 'Статистика',
        'games': 'Игры', 'wins': 'Победы', 'losses': 'Поражения', 'draws': 'Ничьи',
        'win_rate': '% Побед', 'words_played': 'Сыграно слов',
        'best_word': 'Лучшее слово', 'reset': 'Сбросить', 'sound': 'Звук',
        'how_to_play': 'Как играть?',
        'faq_text': (
            '[b]Какие слова принимаются?[/b]\n'
            '• Каждое слово должно начинаться с показанной буквы — '
            'последней буквы предыдущего слова.\n'
            '• Слова проверяются по выбранному языку словаря; '
            'засчитываются только слова этого языка.\n'
            '• Словарь содержит начальные формы — имена собственные и '
            'большинство словоформ не принимаются.\n'
            '• Каждое слово можно сыграть только один раз за игру.\n'
            '• Оскорбительные слова не принимаются.\n\n'
            '[b]Очки и время[/b]\n'
            '• Редкие буквы приносят больше очков.\n'
            '• Если время хода истекло, вы проигрываете — независимо от '
            'счёта.\n'
            '• Когда общее время заканчивается, побеждает больший счёт.\n'
            '• Выход из игры засчитывается как поражение.\n\n'
            '[b]Буквы[/b]\n'
            '• ё = е.\n'
            '• Если слово заканчивается на ь/ъ/ы, берётся предыдущая '
            'буква.\n'
            '• Турецкий: слово на ğ продолжается с g.'
        ),
        'settings': 'Настройки',
        'creating_room': 'Создание комнаты...\n(первое подключение может занять минуту)',
        'no_server': 'Сервер недоступен!',
        'invalid_code': 'Введите правильный код.',
        'connecting': 'Подключение...',
        'room_code': 'КОД КОМНАТЫ',
        'share_code': 'Поделись этим кодом с соперником',
        'waiting_opponent': 'Ожидание соперника...',
        'get_ready': 'Приготовьтесь!',
        'starting_in': 'Старт через {n}...',
        'lobby_chat_hint': 'Поздоровайся перед началом',
        'cancel': 'ОТМЕНА',
        'quit': 'ВЫЙТИ',
        'words_count': 'Слов: {n}',
        'no_words_yet': 'Пока нет слов',
        'player': 'Игрок',
        'your_turn': 'ТВОЙ ХОД — введи слово!',
        'is_playing': '{name} играет...',
        'last': 'Последнее: {word}',
        'type_word': 'Введите слово...',
        'send': 'ОТПРАВИТЬ',
        'game_over': 'ИГРА ОКОНЧЕНА',
        'draw': 'НИЧЬЯ!',
        'you_won': 'ТЫ ПОБЕДИЛ!',
        'you_lost': 'ТЫ ПРОИГРАЛ',
        'opponent_left': 'СОПЕРНИК ВЫШЕЛ',
        'left_game': '{name} покинул игру',
        'pts': 'очк',
        'words': 'Слова', 'total': 'Всего', 'avg': 'Сред',
        'words_used': 'Использованные слова',
        'play_again': 'ИГРАТЬ СНОВА',
        'main_menu': 'ГЛАВНОЕ МЕНЮ',
        'opponent_wants_rematch': 'Соперник хочет реванш!',
        'connection_lost': 'Соединение потеряно.',
        'error': 'Ошибка!',
        'room_full': 'Комната заполнена!',
        'chat': 'Чат',
        'type_message': 'Введите сообщение...',
        'settings_title': 'НАСТРОЙКИ',
        'app_language': 'Язык приложения',
        'app_language_desc': 'Язык интерфейса',
        'word_dictionary': 'Словарь',
        'word_dictionary_desc': 'Язык проверки слов',
        'done': 'ГОТОВО',
        'msg_not_active': 'Игра не активна.',
        'msg_not_in_room': 'Вы не в этой комнате.',
        'msg_not_your_turn': 'Не твой ход!',
        'msg_invalid': 'Недопустимое слово.',
        'msg_already_used': 'Это слово уже использовано!',
        'msg_must_start': 'Должно начинаться на "{letter}"!',
        'msg_not_valid': 'Не настоящее слово!',
        'msg_points': '+{points} очк!',
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
