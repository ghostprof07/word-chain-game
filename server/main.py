"""
WORD CHAIN — Online Sunucu (FastAPI + WebSocket)
================================================
İki oyuncuyu bir oda kodu üzerinden eşleştirir, oyunu yönetir.

Çalıştırmak için:
    pip install -r requirements.txt
    uvicorn main:app --host 0.0.0.0 --port 8000

İstemciler şuraya bağlanır:
    ws://<sunucu-ip>:8000/ws/<oda_kodu>?ad=<oyuncu_adi>
"""
import asyncio
import json
import random
import string
import uuid

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse

from game_logic import GameRoom

app = FastAPI(title="Word Chain Online")

# Aktif odalar: oda_kodu -> GameRoom
ODALAR: dict[str, GameRoom] = {}
# Bağlantılar: oda_kodu -> {player_id -> WebSocket}
BAGLANTILAR: dict[str, dict[str, WebSocket]] = {}


def yeni_oda_kodu() -> str:
    """Benzersiz 4 haneli oda kodu üretir (örn. 'AB12')."""
    while True:
        kod = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))
        if kod not in ODALAR:
            return kod


async def odaya_yayinla(oda_kodu: str, mesaj: dict):
    """Odadaki tüm oyunculara mesaj gönderir."""
    for ws in list(BAGLANTILAR.get(oda_kodu, {}).values()):
        try:
            await ws.send_text(json.dumps(mesaj))
        except Exception:
            pass


# ── HTTP uçları ───────────────────────────────────────────────────────────────
@app.get("/")
async def kok():
    return {"servis": "Word Chain Online", "aktif_oda": len(ODALAR)}


@app.post("/oda-olustur")
async def oda_olustur(sure: int = 300, hamle: int = 20, dil: str = "en"):
    """
    Yeni bir oda oluşturur ve kodunu döndürür.
    sure:  toplam oyun süresi (saniye) — oda kuran kişi seçer
    hamle: her hamle süresi (saniye)
    dil:   sözlük (kelime doğrulama) dili — oda kuran kişi seçer
    """
    kod = yeni_oda_kodu()
    ODALAR[kod] = GameRoom(kod, toplam_sure=sure, hamle_sure=hamle, dict_lang=dil)
    BAGLANTILAR[kod] = {}
    return JSONResponse({"oda": kod})


# ── Zamanlayıcı görevi ────────────────────────────────────────────────────────
async def sure_dongusu():
    """Her saniye tüm odaların süresini günceller ve durumu yayınlar."""
    while True:
        await asyncio.sleep(1)
        for kod, oda in list(ODALAR.items()):
            if oda.geri_sayim is not None and not oda.basladi and not oda.bitti:
                # Kısa lobi: geri sayımı işle, 0'da oyun başlar.
                basladi_simdi = oda.geri_sayim_tik()
                await odaya_yayinla(kod, oda.durum())
                if basladi_simdi:
                    await odaya_yayinla(kod, {**oda.durum(), 'tip': 'yeni_oyun'})
            elif oda.basladi and not oda.bitti:
                onceki_bitti = oda.bitti
                oda.sure_guncelle()
                # Süre dolduysa ya da her saniye durumu yay
                await odaya_yayinla(kod, oda.durum())
                if oda.bitti and not onceki_bitti:
                    await odaya_yayinla(kod, {**oda.durum(), 'tip': 'oyun_bitti'})


@app.on_event("startup")
async def baslangic():
    asyncio.create_task(sure_dongusu())


# ── WebSocket ucu ─────────────────────────────────────────────────────────────
@app.websocket("/ws/{oda_kodu}")
async def ws_oda(websocket: WebSocket, oda_kodu: str, ad: str = "Oyuncu"):
    await websocket.accept()
    oda_kodu = oda_kodu.upper()

    # Oda yoksa oluştur (doğrudan kodla katılmak isteyenler için)
    if oda_kodu not in ODALAR:
        ODALAR[oda_kodu] = GameRoom(oda_kodu)
        BAGLANTILAR[oda_kodu] = {}

    oda = ODALAR[oda_kodu]
    player_id = uuid.uuid4().hex

    no = oda.oyuncu_ekle(player_id, ad)
    if no is None:
        await websocket.send_text(json.dumps({'tip': 'hata', 'kod': 'room_full'}))
        await websocket.close()
        return

    BAGLANTILAR[oda_kodu][player_id] = websocket

    # İlk bilgilendirme: senin numaran kaç
    await websocket.send_text(json.dumps({
        'tip': 'katildi',
        'oda': oda_kodu,
        'senin_no': no,
        'player_id': player_id,
    }))
    # Odadaki herkese güncel durumu yay
    await odaya_yayinla(oda_kodu, oda.durum())

    try:
        while True:
            ham = await websocket.receive_text()
            try:
                veri = json.loads(ham)
            except json.JSONDecodeError:
                continue

            tip = veri.get('tip')

            if tip == 'kelime':
                kelime = veri.get('kelime', '')
                basari, kod_msg, puan = oda.kelime_oyna(player_id, kelime)
                # Deneme sonucunu sadece denemeyi yapana bildir.
                # 'kod' istemcide kendi diline çevrilir; 'harf' must_start için gerekli.
                await websocket.send_text(json.dumps({
                    'tip': 'kelime_sonuc',
                    'basari': basari,
                    'kod': kod_msg,
                    'puan': puan,
                    'harf': oda.gerekli_harf,
                }))
                # Başarılıysa herkese yeni durumu yay
                if basari:
                    await odaya_yayinla(oda_kodu, oda.durum())

            elif tip == 'sohbet':
                metin = (veri.get('mesaj') or '').strip()[:200]
                if metin and player_id in oda.oyuncular:
                    p = oda.oyuncular[player_id]
                    await odaya_yayinla(oda_kodu, {
                        'tip': 'sohbet',
                        'no': p['no'],
                        'ad': p['ad'],
                        'mesaj': metin,
                    })

            elif tip == 'rematch':
                yeni_basladi = oda.rematch_iste(player_id)
                if yeni_basladi:
                    # İki oyuncu da hazır — yeni oyun başladı, herkese bildir
                    # NOT: spread ÖNCE, tip SONRA — yoksa durum()'un 'tip'i ezer
                    await odaya_yayinla(oda_kodu, {
                        **oda.durum(), 'tip': 'yeni_oyun',
                    })
                else:
                    # Henüz tek taraf istedi — durumu yay (rematch_sayisi güncellensin)
                    await odaya_yayinla(oda_kodu, oda.durum())

            elif tip == 'durum_iste':
                await websocket.send_text(json.dumps(oda.durum()))

    except WebSocketDisconnect:
        pass
    finally:
        # Bağlantıyı ve oyuncuyu temizle
        BAGLANTILAR.get(oda_kodu, {}).pop(player_id, None)
        oda.oyuncu_cikar(player_id)
        await odaya_yayinla(oda_kodu, {
            **oda.durum(),
            'tip': 'oyuncu_ayrildi',
        })
        # Oda boşaldıysa sil
        if not BAGLANTILAR.get(oda_kodu):
            ODALAR.pop(oda_kodu, None)
            BAGLANTILAR.pop(oda_kodu, None)
