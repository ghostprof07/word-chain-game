"""İki oyuncuyu simüle eden hızlı entegrasyon testi."""
import json
import time
import threading
import requests
import websocket

HTTP = "http://127.0.0.1:8000"
WS = "ws://127.0.0.1:8000"

mesajlar = {1: [], 2: []}


def dinle(no, oda, ad):
    def on_message(ws, m):
        veri = json.loads(m)
        mesajlar[no].append(veri)
        if veri.get('tip') == 'katildi':
            print(f"[Oyuncu {no}] katıldı, numara={veri['senin_no']}")
    ws = websocket.WebSocketApp(f"{WS}/ws/{oda}?ad={ad}", on_message=on_message)
    t = threading.Thread(target=ws.run_forever, daemon=True)
    t.start()
    return ws


# Oda oluştur
oda = requests.post(f"{HTTP}/oda-olustur").json()['oda']
print(f"Oda: {oda}")

ws1 = dinle(1, oda, "Ahmet")
time.sleep(0.5)
ws2 = dinle(2, oda, "Mehmet")
time.sleep(1)

# Son durumu bul
def son_durum(no):
    for m in reversed(mesajlar[no]):
        if m.get('tip') in ('durum',):
            return m
    return None

d = son_durum(1)
print(f"Oyun başladı mı: {d['basladi']}, gerekli harf: {d['gerekli_harf'].upper()}")

# Oyuncu 1 sırada mı? doğru harfle başlayan kelime gönder
harf = d['gerekli_harf']

# Sözlükten o harfle başlayan bir kelime bul
with open("words_en.txt", encoding="utf-8") as f:
    kelimeler = [w.strip().lower() for w in f if w.strip().isalpha()]
ornek = next(w for w in kelimeler if w.startswith(harf) and len(w) > 3)

print(f"Oyuncu 1 '{ornek}' gönderiyor...")
ws1.send(json.dumps({'tip': 'kelime', 'kelime': ornek}))
time.sleep(1)

# Sonucu kontrol et
for m in reversed(mesajlar[1]):
    if m.get('tip') == 'kelime_sonuc':
        print(f"Sonuç: başarı={m['basari']}, mesaj={m['mesaj']}, puan={m['puan']}")
        break

# Yeni durum: sıra oyuncu 2'ye geçti mi?
d2 = son_durum(2)
print(f"Yeni sıra: Oyuncu {d2['siradaki_no']}, yeni harf: {d2['gerekli_harf'].upper()}")
print(f"Puanlar: {d2['puan']}")

# Yanlış harfle deneme (oyuncu 2)
yanlis = next(w for w in kelimeler if not w.startswith(d2['gerekli_harf']) and len(w) > 3)
print(f"Oyuncu 2 yanlış harfle '{yanlis}' deniyor...")
ws2.send(json.dumps({'tip': 'kelime', 'kelime': yanlis}))
time.sleep(1)
for m in reversed(mesajlar[2]):
    if m.get('tip') == 'kelime_sonuc':
        print(f"Beklenen ret: başarı={m['basari']}, mesaj={m['mesaj']}")
        break

print("\n✓ Test tamamlandı.")
