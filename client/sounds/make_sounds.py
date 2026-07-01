"""Oyun ses efektlerini sentezler (telif derdi yok). 16-bit mono WAV."""
import wave, struct, math, os

SR = 22050
OUT = os.path.dirname(os.path.abspath(__file__))


def _yaz(ad, ornekler):
    path = os.path.join(OUT, ad)
    with wave.open(path, 'w') as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(b''.join(
            struct.pack('<h', int(max(-1.0, min(1.0, s)) * 32767)) for s in ornekler))


def nota(freq, sure, vol=0.5, kare=False):
    n = int(SR * sure)
    out = []
    for i in range(n):
        t = i / SR
        zarf = math.exp(-3.4 * t / sure)               # sönüm
        atak = min(1.0, i / (SR * 0.004))               # tık olmasın
        w = math.sin(2 * math.pi * freq * t)
        if kare:
            w = 1.0 if w >= 0 else -1.0
        out.append(vol * zarf * atak * w)
    return out


# success: yükselen iki ton (geçerli kelime)
_yaz('success.wav', nota(660, 0.07, 0.5) + nota(990, 0.11, 0.5))
# error: kısa alçak vızıltı (geçersiz)
_yaz('error.wav', nota(160, 0.16, 0.4, kare=True))
# win: yükselen arpej
_yaz('win.wav', nota(523, 0.09) + nota(659, 0.09) + nota(784, 0.09) + nota(1047, 0.18))
# lose: alçalan iki ton
_yaz('lose.wav', nota(392, 0.14, 0.45) + nota(294, 0.22, 0.45))

print('Sesler uretildi:', [f for f in os.listdir(OUT) if f.endswith('.wav')])
