# -*- coding: utf-8 -*-
"""
iOS uygulama ikonu setini client/icon.png'den üretir.
=====================================================
kivy-ios'un oluşturduğu Xcode projesine kopyalanmak üzere bir
`AppIcon.appiconset` klasörü hazırlar (PNG'ler + Contents.json).

Çalıştırmak:  python ios/make_ios_assets.py
Çıktı:        ios/AppIcon.appiconset/

NOT: iOS ikonlarında saydamlık (alpha) YASAK — App Store reddeder.
Bu yüzden RGBA görseller koyu zemine düzleştirilir.
"""
import json
import os

from PIL import Image

BURASI = os.path.dirname(os.path.abspath(__file__))
KAYNAK = os.path.join(BURASI, '..', 'client', 'icon.png')
HEDEF = os.path.join(BURASI, 'AppIcon.appiconset')

# Marka gradyanının koyu ucu — alpha düzleştirmede zemin olarak kullanılır.
ZEMIN = (26, 11, 46)

# (boyut_pt, ölçek, idiom) — iPhone + iPad + App Store pazarlama ikonu
IKONLAR = [
    (20, 2, 'iphone'), (20, 3, 'iphone'),
    (29, 2, 'iphone'), (29, 3, 'iphone'),
    (40, 2, 'iphone'), (40, 3, 'iphone'),
    (60, 2, 'iphone'), (60, 3, 'iphone'),
    (20, 1, 'ipad'), (20, 2, 'ipad'),
    (29, 1, 'ipad'), (29, 2, 'ipad'),
    (40, 1, 'ipad'), (40, 2, 'ipad'),
    (76, 1, 'ipad'), (76, 2, 'ipad'),
    (83.5, 2, 'ipad'),
    (1024, 1, 'ios-marketing'),
]


def main():
    os.makedirs(HEDEF, exist_ok=True)
    kaynak = Image.open(KAYNAK)

    # Alpha kanalını koyu zemine düzleştir (App Store şartı)
    if kaynak.mode in ('RGBA', 'LA', 'P'):
        kaynak = kaynak.convert('RGBA')
        zemin = Image.new('RGB', kaynak.size, ZEMIN)
        zemin.paste(kaynak, mask=kaynak.split()[-1])
        kaynak = zemin
    else:
        kaynak = kaynak.convert('RGB')

    girdiler = []
    yazilan = set()
    for pt, olcek, idiom in IKONLAR:
        px = int(round(pt * olcek))
        ad = f'icon-{px}.png'
        if ad not in yazilan:
            kaynak.resize((px, px), Image.LANCZOS).save(
                os.path.join(HEDEF, ad), 'PNG')
            yazilan.add(ad)
        boyut = f'{pt:g}x{pt:g}'
        girdiler.append({
            'size': boyut,
            'idiom': idiom,
            'filename': ad,
            'scale': f'{olcek}x',
        })

    with open(os.path.join(HEDEF, 'Contents.json'), 'w', encoding='utf-8') as f:
        json.dump({'images': girdiler,
                   'info': {'version': 1, 'author': 'xcode'}}, f, indent=2)

    print(f'{len(yazilan)} PNG + Contents.json -> {HEDEF}')


if __name__ == '__main__':
    main()
