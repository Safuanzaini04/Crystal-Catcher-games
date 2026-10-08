"""Generates all sprites and sound effects into the assets/ folder.

Run once:  python make_assets.py   (needs Pillow: pip install pillow)
You can replace any file in assets/ with your own art or sounds
(keep the same file names) and the game will use it.
"""
import math
import os
import random
import struct
import wave

from PIL import Image, ImageDraw

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets")
os.makedirs(OUT, exist_ok=True)
S = 4  # supersampling factor for smooth edges


def canvas(w, h):
    img = Image.new("RGBA", (w * S, h * S), (0, 0, 0, 0))
    return img, ImageDraw.Draw(img)


def pts(points):
    return [(x * S, y * S) for x, y in points]


def box(x0, y0, x1, y1):
    return [x0 * S, y0 * S, x1 * S, y1 * S]


def save(img, name, size):
    img.resize(size, Image.LANCZOS).save(os.path.join(OUT, name))


def wizard():
    img, d = canvas(100, 100)
    d.polygon(pts([(22, 100), (78, 100), (68, 55), (32, 55)]), fill=(40, 55, 150))
    d.polygon(pts([(40, 100), (60, 100), (56, 60), (44, 60)]), fill=(70, 90, 190))
    d.ellipse(box(37, 40, 63, 66), fill=(240, 200, 160))
    d.polygon(pts([(38, 56), (62, 56), (50, 86)]), fill=(240, 240, 250))
    d.ellipse(box(44, 48, 48, 52), fill=(30, 30, 30))
    d.ellipse(box(53, 48, 57, 52), fill=(30, 30, 30))
    d.ellipse(box(8, 33, 92, 51), fill=(85, 40, 150))
    d.polygon(pts([(28, 40), (72, 40), (52, 0)]), fill=(115, 55, 190))
    d.ellipse(box(46, 18, 54, 26), fill=(255, 220, 60))
    save(img, "wizard.png", (100, 100))


def crystal():
    img, d = canvas(40, 40)
    d.polygon(pts([(20, 2), (36, 16), (20, 38), (4, 16)]), fill=(60, 200, 240))
    d.polygon(pts([(20, 2), (36, 16), (20, 16)]), fill=(150, 235, 255))
    d.polygon(pts([(20, 16), (36, 16), (20, 38)]), fill=(30, 140, 210))
    d.line(pts([(4, 16), (36, 16)]), fill=(220, 250, 255), width=S)
    save(img, "crystal.png", (40, 40))


def potion():
    img, d = canvas(40, 40)
    d.rectangle(box(16, 4, 24, 12), fill=(230, 230, 240))
    d.rectangle(box(15, 1, 25, 5), fill=(140, 90, 50))
    d.ellipse(box(6, 10, 34, 38), fill=(220, 50, 120))
    d.ellipse(box(11, 16, 18, 24), fill=(255, 160, 200))
    save(img, "potion.png", (40, 40))


def fireball():
    img, d = canvas(44, 56)
    d.polygon(pts([(22, 0), (40, 34), (4, 34)]), fill=(255, 120, 20))
    d.ellipse(box(4, 22, 40, 54), fill=(255, 90, 10))
    d.ellipse(box(11, 30, 33, 50), fill=(255, 200, 40))
    d.ellipse(box(16, 36, 28, 47), fill=(255, 250, 200))
    save(img, "fireball.png", (44, 56))


def shield():
    img, d = canvas(40, 40)
    d.ellipse(box(2, 2, 38, 38), fill=(255, 200, 40))
    d.ellipse(box(7, 7, 33, 33), fill=(70, 130, 230))
    d.polygon(pts([(20, 11), (28, 15), (26, 25), (20, 30), (14, 25), (12, 15)]), fill=(210, 230, 255))
    save(img, "shield.png", (40, 40))


def hourglass():
    img, d = canvas(40, 40)
    d.rectangle(box(6, 2, 34, 6), fill=(150, 100, 50))
    d.rectangle(box(6, 34, 34, 38), fill=(150, 100, 50))
    d.polygon(pts([(9, 6), (31, 6), (20, 20)]), fill=(200, 235, 255))
    d.polygon(pts([(20, 20), (9, 34), (31, 34)]), fill=(200, 235, 255))
    d.polygon(pts([(14, 30), (26, 30), (20, 22)]), fill=(240, 200, 80))
    save(img, "hourglass.png", (40, 40))


def heart():
    img, d = canvas(28, 28)
    d.ellipse(box(2, 3, 15, 16), fill=(230, 40, 70))
    d.ellipse(box(13, 3, 26, 16), fill=(230, 40, 70))
    d.polygon(pts([(3, 12), (25, 12), (14, 26)]), fill=(230, 40, 70))
    save(img, "heart.png", (28, 28))


def background():
    w, h = 800, 600
    img = Image.new("RGB", (w, h))
    d = ImageDraw.Draw(img)
    for y in range(h):
        t = y / h
        d.line([(0, y), (w, y)], fill=(int(15 + 70 * t), int(10 + 30 * t), int(50 + 70 * t)))
    rnd = random.Random(7)
    for _ in range(90):
        x, y, r = rnd.randint(0, w), rnd.randint(0, 380), rnd.choice([1, 1, 2])
        d.ellipse([x - r, y - r, x + r, y + r], fill=(255, 255, 230))
    d.ellipse([620, 50, 700, 130], fill=(250, 245, 210))
    d.ellipse([645, 42, 715, 112], fill=(40, 25, 85))
    castle = (18, 12, 40)
    d.polygon([(0, 600), (0, 470), (60, 440), (120, 480), (200, 430), (260, 490), (330, 470),
               (400, 500), (480, 450), (560, 490), (640, 440), (720, 480), (800, 450), (800, 600)], fill=castle)
    d.rectangle([330, 360, 470, 520], fill=castle)
    for tx in (320, 440):
        d.rectangle([tx, 320, tx + 40, 520], fill=castle)
        d.polygon([(tx - 6, 320), (tx + 46, 320), (tx + 20, 270)], fill=castle)
    for wx, wy in ((345, 400), (395, 400), (435, 345), (335, 345)):
        d.rectangle([wx, wy, wx + 10, wy + 18], fill=(250, 210, 90))
    d.rectangle([0, 560, 800, 600], fill=(25, 45, 40))
    img.save(os.path.join(OUT, "background.png"))


RATE = 22050


def write_wav(name, notes, vol=0.45, wave_type="sine"):
    frames = bytearray()
    for freq, dur in notes:
        n = int(RATE * dur)
        for i in range(n):
            t = i / RATE
            env = min(1.0, i / 200) * (1 - i / n)
            if freq == 0:
                v = random.uniform(-1, 1) * 0.5
            elif wave_type == "square":
                v = 1.0 if math.sin(2 * math.pi * freq * t) >= 0 else -1.0
                v *= 0.5
            else:
                v = math.sin(2 * math.pi * freq * t)
            frames += struct.pack("<h", int(32767 * vol * env * v))
    with wave.open(os.path.join(OUT, name), "wb") as f:
        f.setnchannels(1)
        f.setsampwidth(2)
        f.setframerate(RATE)
        f.writeframes(bytes(frames))


def sounds():
    write_wav("catch.wav", [(880, 0.06), (1320, 0.09)])
    write_wav("miss.wav", [(320, 0.10), (220, 0.16)], wave_type="square", vol=0.3)
    write_wav("hit.wav", [(0, 0.05), (140, 0.2)], vol=0.5)
    write_wav("powerup.wav", [(523, 0.07), (659, 0.07), (784, 0.07), (1047, 0.12)])
    write_wav("win.wav", [(523, 0.12), (659, 0.12), (784, 0.12), (1047, 0.3)])
    write_wav("lose.wav", [(400, 0.2), (330, 0.2), (260, 0.2), (180, 0.4)], wave_type="square", vol=0.3)


if __name__ == "__main__":
    for fn in (wizard, crystal, potion, fireball, shield, hourglass, heart, background, sounds):
        fn()
    print("Assets written to", OUT)
