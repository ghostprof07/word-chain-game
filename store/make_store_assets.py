from PIL import Image, ImageDraw, ImageFont
import math, os, kivy

STORE = r"C:\Users\yavuzkemal\Desktop\word_chain_game\store"
os.makedirs(STORE, exist_ok=True)
ICON = r"C:\Users\yavuzkemal\Desktop\word_chain_game\client\icon.png"
FP = os.path.join(os.path.dirname(kivy.__file__), 'data', 'fonts', 'Roboto-Bold.ttf')
FPR = os.path.join(os.path.dirname(kivy.__file__), 'data', 'fonts', 'Roboto-Regular.ttf')

C = [(124, 58, 237), (255, 70, 150), (255, 150, 50)]
def lerp(a, b, t): return tuple(int(a[i] + (b[i]-a[i])*t) for i in range(3))
def grad(t):
    t = max(0., min(1., t)); seg = t*(len(C)-1); i = min(int(seg), len(C)-2); f = seg-i
    return lerp(C[i], C[i+1], f)

# 1) 512x512 ikon (Play listeleme ikonu)
Image.open(ICON).convert('RGB').resize((512, 512), Image.LANCZOS).save(
    os.path.join(STORE, 'icon_512.png'))

# 2) Feature graphic 1024x500
W, H = 1024, 500
gw, gh = 128, 63
sm = Image.new('RGB', (gw, gh)); px = sm.load()
for y in range(gh):
    for x in range(gw):
        px[x, y] = grad((x/(gw-1) + y/(gh-1)) / 2)
img = sm.resize((W, H), Image.BICUBIC).convert('RGBA')
d = ImageDraw.Draw(img)

# beyaz coil (sol)
cx, cy = W*0.22, H*0.5
stroke = H*0.075; turns = 2.35; r_max = H*0.30; r_min = H*0.05
steps = 1200; tmax = turns*2*math.pi; rad = stroke/2
for s in range(steps+1):
    th = tmax*s/steps; r = r_min + (r_max-r_min)*(s/steps)
    d.ellipse([cx+r*math.cos(th)-rad, cy+r*math.sin(th)-rad,
               cx+r*math.cos(th)+rad, cy+r*math.sin(th)+rad], fill=(255, 255, 255, 255))

# LEXICOIL + slogan (sag)
fb = ImageFont.truetype(FP, int(H*0.20))
d.text((W*0.42, H*0.30), "LEXICOIL", font=fb, fill=(255, 255, 255, 255))
fr = ImageFont.truetype(FPR, int(H*0.075))
d.text((W*0.425, H*0.56), "Word chain  -  online & solo", font=fr, fill=(255, 255, 255, 230))

img.convert('RGB').save(os.path.join(STORE, 'feature_graphic.png'))
print("yazildi: icon_512.png, feature_graphic.png ->", STORE)
