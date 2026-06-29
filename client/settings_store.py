"""
Ayarları (uygulama dili + sözlük dili) JSON dosyasında saklar.
Uygulama yeniden açılınca seçimler korunur.
"""
import json
import os

VARSAYILAN = {
    'app_lang': 'en',   # arayüz dili
    'dict_lang': 'en',  # oyun sözlüğü (kelime doğrulama) dili
}


def _dosya(dizin):
    return os.path.join(dizin, 'wordchain_settings.json')


def yukle(dizin):
    """Ayarları okur; yoksa varsayılanı döndürür."""
    try:
        with open(_dosya(dizin), encoding='utf-8') as f:
            veri = json.load(f)
        ayar = dict(VARSAYILAN)
        ayar.update({k: veri[k] for k in VARSAYILAN if k in veri})
        return ayar
    except Exception:
        return dict(VARSAYILAN)


def kaydet(dizin, ayar):
    """Ayarları yazar."""
    try:
        with open(_dosya(dizin), 'w', encoding='utf-8') as f:
            json.dump(ayar, f)
    except Exception:
        pass
