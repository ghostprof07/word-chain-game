"""
Ayarları (uygulama dili + sözlük dili) JSON dosyasında saklar.
Uygulama yeniden açılınca seçimler korunur.
"""
import json
import os

VARSAYILAN = {
    'app_lang': 'en',   # arayüz dili
    'dict_lang': 'en',  # oyun sözlüğü (kelime doğrulama) dili
    'best': {},         # antrenman en iyi skorları: {dict_lang: skor}
    'stats': {},        # istatistikler: games/wins/losses/draws/words/best_word
}


def _dosya(dizin):
    return os.path.join(dizin, 'wordchain_settings.json')


def _varsayilan():
    # dict değerleri (best) için taze kopya — paylaşılan mutable default olmasın
    return {k: (dict(v) if isinstance(v, dict) else v) for k, v in VARSAYILAN.items()}


def yukle(dizin):
    """Ayarları okur; yoksa varsayılanı döndürür."""
    try:
        with open(_dosya(dizin), encoding='utf-8') as f:
            veri = json.load(f)
        ayar = _varsayilan()
        ayar.update({k: veri[k] for k in VARSAYILAN if k in veri})
        return ayar
    except Exception:
        return _varsayilan()


def kaydet(dizin, ayar):
    """Ayarları yazar."""
    try:
        with open(_dosya(dizin), 'w', encoding='utf-8') as f:
            json.dump(ayar, f)
    except Exception:
        pass
