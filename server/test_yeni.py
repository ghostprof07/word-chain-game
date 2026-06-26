"""Yeni özellikleri test eder: süre seçeneği, kelime zinciri sırası, rematch, ayrılma."""
import json, time, threading, requests, websocket

HTTP = "http://127.0.0.1:8000"
WS = "ws://127.0.0.1:8000"
mesaj = {1: [], 2: []}
ws_ref = {}

def dinle(no, oda, ad):
    def om(w, m): mesaj[no].append(json.loads(m))
    w = websocket.WebSocketApp(f"{WS}/ws/{oda}?ad={ad}", on_message=om)
    threading.Thread(target=w.run_forever, daemon=True).start()
    ws_ref[no] = w
    return w

def son(no, tip='durum'):
    for m in reversed(mesaj[no]):
        if m.get('tip') == tip:
            return m
    return None

# 1) SÜRE SEÇENEĞİ — 3 dk (180 sn) oda
oda = requests.post(f"{HTTP}/oda-olustur", params={'sure': 180, 'hamle': 15}).json()['oda']
print(f"[1] Oda olusturuldu: {oda}")
dinle(1, oda, "Ahmet"); time.sleep(0.8)
dinle(2, oda, "Mehmet"); time.sleep(1.5)
d = son(1)
assert d['basladi'], "Oyun baslamadi"
print(f"    Toplam sure: {d['toplam_sure']} (180 bekleniyor), hamle: {d['hamle_sure']} (15 bekleniyor)")
assert d['toplam_sure'] <= 180 and d['toplam_sure'] > 170, "Sure secimi calismadi"
assert d['hamle_sure'] <= 15, "Hamle suresi calismadi"
print("    ✓ Süre seçeneği çalışıyor")

# 2) KELİME ZİNCİRİ SIRASI
harf = d['gerekli_harf']
with open("words_en.txt", encoding="utf-8") as f:
    kelimeler = [w.strip().lower() for w in f if w.strip().isalpha()]
k1 = next(w for w in kelimeler if w.startswith(harf) and len(w) > 3)
ws_ref[1].send(json.dumps({'tip': 'kelime', 'kelime': k1})); time.sleep(0.8)
d = son(2)
k2 = next(w for w in kelimeler if w.startswith(d['gerekli_harf']) and len(w) > 3 and w != k1)
ws_ref[2].send(json.dumps({'tip': 'kelime', 'kelime': k2})); time.sleep(0.8)
d = son(1)
zincir = d['zincir']
print(f"    Zincir: {[(z['kelime'], z['no']) for z in zincir]}")
assert len(zincir) == 2, "Zincir uzunlugu yanlis"
assert zincir[0]['kelime'] == k1 and zincir[0]['no'] == 1, "Zincir sirasi/oyuncu yanlis"
assert zincir[1]['kelime'] == k2 and zincir[1]['no'] == 2, "Zincir 2. eleman yanlis"
print("    ✓ Kelime zinciri sırası ve oyuncu bilgisi doğru")

# 3) REMATCH — once oyunu bitir (toplam sure dolana kadar beklemek yerine ayrilma disinda
#    rematch'i test etmek icin: iki taraf da rematch istesin)
#    Once oyunu yapay bitirelim: rematch sadece bitti durumunda mantikli ama sunucu
#    her halükarda iki istek gelince yeni oyun baslatir.
ws_ref[1].send(json.dumps({'tip': 'rematch'})); time.sleep(0.5)
d1 = son(1)
print(f"    Tek taraf rematch sonrasi rematch_sayisi: {d1['rematch_sayisi']} (1 bekleniyor)")
ws_ref[2].send(json.dumps({'tip': 'rematch'})); time.sleep(0.8)
yeni = son(1, 'yeni_oyun')
assert yeni is not None, "yeni_oyun mesaji gelmedi"
assert yeni['kelime_sayisi'] == 0, "Yeni oyunda kelimeler sifirlanmadi"
assert yeni['puan']['1'] == 0 and yeni['puan']['2'] == 0, "Puanlar sifirlanmadi"
print("    ✓ Rematch çalışıyor — yeni oyun sıfırdan başladı")

# 4) AYRILMA — oyuncu 1 baglantiyi kapatir
ws_ref[1].close(); time.sleep(1.2)
ayril = son(2, 'oyuncu_ayrildi')
print(f"    Ayrilma mesaji: ayrilan_ad={ayril['ayrilan_ad'] if ayril else None}, bitti={ayril['bitti'] if ayril else None}")
assert ayril is not None, "oyuncu_ayrildi mesaji gelmedi"
assert ayril['ayrilan_ad'] == 'Ahmet', "Ayrilan oyuncu adi yanlis"
assert ayril['bitti'], "Ayrilinca oyun bitmeli"
print("    ✓ Bağlantı kopması yönetimi çalışıyor")

print("\n=== TUM YENI OZELLIKLER BASARILI ===")
