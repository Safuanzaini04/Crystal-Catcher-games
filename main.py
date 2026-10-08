"""Fantasy Quest: Crystal Catcher
(SWC3643 - Python Programming Language)
Developer: Muhammad Safuan Bin Zaini

A wizard catch falling crystals and potions while dodging
dragon fireballs. Survive 60 seconds with at least one life to win.

Controls:  LEFT/RIGHT (or A/D) move | P pause | R restart | ESC menu
Menu:      UP/DOWN + ENTER | L for switches English / Bahasa Melayu
"""
import os
import random
import sys

import pygame

# ----------------------------------------------------------------- settings
WIDTH, HEIGHT, FPS = 800, 600, 60
GAME_SECONDS = 60
START_LIVES = 5
MAX_LIVES = 7
GRAVITY = 380                      # pixels / second^2 (before level scaling)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ASSET_DIR = os.path.join(BASE_DIR, "assets")
SCORE_FILE = os.path.join(BASE_DIR, "highscore.txt")

WHITE, GOLD, RED, GREEN = (255, 255, 255), (255, 215, 80), (255, 90, 90), (120, 230, 140)

# ------------------------------------------------- bilingual text (EN / MS)
TEXT = {
    "en": {
        "title": "FANTASY QUEST", "subtitle": "Crystal Catcher",
        "menu": ["Start", "Instructions", "Exit"],
        "lang_hint": "L: Language - English", "nav_hint": "UP/DOWN to choose, ENTER to select",
        "score": "Score", "best": "Best", "time": "Time", "level": "Level", "lives": "Lives",
        "shield": "Shield ready", "paused": "PAUSED", "paused_hint": "P: resume   R: restart   ESC: menu",
        "win": "YOU WIN!", "lose": "GAME OVER", "new_best": "New high score!",
        "over_hint": "R: play again   ESC: menu", "final": "Final score",
        "ins_title": "How to Play", "back": "Press ENTER or ESC to go back",
        "ins": [
            "Move the wizard with LEFT / RIGHT (or A / D).",
            "Catch crystals (+10) and potions (+25, restores a life).",
            "Missing a crystal or potion costs 1 life.",
            "Fireballs cost 1 life - dodge them!",
            "Shield orb blocks one fireball. Hourglass adds 5 seconds.",
            "Survive 60 seconds with lives left to win.",
            "P = pause, R = restart. Levels get harder every 20 seconds.",
        ],
        "levels": ["Apprentice", "Sorcerer", "Archmage"],
    },
    "ms": {
        "title": "PENCARIAN FANTASI", "subtitle": "Penangkap Kristal",
        "menu": ["Mula", "Arahan", "Keluar"],
        "lang_hint": "L: Bahasa - Melayu", "nav_hint": "ATAS/BAWAH untuk pilih, ENTER untuk teruskan",
        "score": "Skor", "best": "Terbaik", "time": "Masa", "level": "Tahap", "lives": "Nyawa",
        "shield": "Perisai sedia", "paused": "DIJEDA", "paused_hint": "P: sambung   R: mula semula   ESC: menu",
        "win": "ANDA MENANG!", "lose": "TAMAT PERMAINAN", "new_best": "Skor tertinggi baharu!",
        "over_hint": "R: main lagi   ESC: menu", "final": "Skor akhir",
        "ins_title": "Cara Bermain", "back": "Tekan ENTER atau ESC untuk kembali",
        "ins": [
            "Gerakkan ahli sihir dengan KIRI / KANAN (atau A / D).",
            "Tangkap kristal (+10) dan ramuan (+25, pulih 1 nyawa).",
            "Terlepas kristal atau ramuan menyebabkan hilang 1 nyawa.",
            "Bola api menyebabkan hilang 1 nyawa - elakkan!",
            "Orb perisai menahan satu bola api. Jam pasir tambah 5 saat.",
            "Bertahan 60 saat dengan nyawa berbaki untuk menang.",
            "P = jeda, R = mula semula. Tahap makin sukar setiap 20 saat.",
        ],
        "levels": ["Perantis", "Ahli Sihir", "Penyihir Agung"],
    },
}


# ------------------------------------------------------------- AssetManager
class AssetManager:
    """Loads images and sounds once from assets/ and caches them."""

    def __init__(self):
        self._images, self._sounds = {}, {}
        self.audio_ok = pygame.mixer.get_init() is not None

    def image(self, name, size=None):
        key = (name, size)
        if key not in self._images:
            try:
                img = pygame.image.load(os.path.join(ASSET_DIR, name)).convert_alpha()
                if size:
                    img = pygame.transform.smoothscale(img, size)
            except (pygame.error, FileNotFoundError):      # visible placeholder
                img = pygame.Surface(size or (40, 40), pygame.SRCALPHA)
                img.fill((255, 0, 255))
            self._images[key] = img
        return self._images[key]

    def play(self, name):
        if not self.audio_ok:
            return
        if name not in self._sounds:
            try:
                self._sounds[name] = pygame.mixer.Sound(os.path.join(ASSET_DIR, name))
            except (pygame.error, FileNotFoundError):
                self._sounds[name] = None
        if self._sounds[name]:
            self._sounds[name].play()


# ------------------------------------------------------------------- Player
class Player:
    WIDTH, HEIGHT = 100, 100
    ACCEL, FRICTION, MAX_SPEED = 2600, 2200, 480

    def __init__(self, assets):
        self.image = assets.image("wizard.png", (self.WIDTH, self.HEIGHT))
        self.x = WIDTH / 2
        self.y = HEIGHT - self.HEIGHT - 8
        self.vx = 0.0
        self.shield = False

    @property
    def catch_rect(self):
        return pygame.Rect(self.x - 46, self.y + 2, 92, 46)

    def update(self, dt, keys):
        direction = (keys[pygame.K_RIGHT] or keys[pygame.K_d]) - (keys[pygame.K_LEFT] or keys[pygame.K_a])
        if direction:
            self.vx += direction * self.ACCEL * dt
        elif self.vx:
            drop = self.FRICTION * dt
            self.vx = 0.0 if abs(self.vx) <= drop else self.vx - drop * (1 if self.vx > 0 else -1)
        self.vx = max(-self.MAX_SPEED, min(self.MAX_SPEED, self.vx))
        self.x += self.vx * dt
        half = self.WIDTH / 2
        self.x = max(half, min(WIDTH - half, self.x))

    def draw(self, surface):
        if self.shield:
            aura = pygame.Surface((130, 130), pygame.SRCALPHA)
            pygame.draw.circle(aura, (90, 160, 255, 90), (65, 65), 62)
            pygame.draw.circle(aura, (200, 230, 255, 200), (65, 65), 62, 3)
            surface.blit(aura, (self.x - 65, self.y - 8))
        surface.blit(self.image, (self.x - self.WIDTH / 2, self.y))


# --------------------------------------------------------------------- Item
class Item:
    image_name, size = "crystal.png", (40, 40)
    weight = 10                # spawn weight
    costs_life_on_miss = False

    def __init__(self, assets, x, vy):
        self.image = assets.image(self.image_name, self.size)
        self.x, self.y, self.vy = x, -self.size[1], vy

    @property
    def rect(self):
        return pygame.Rect(self.x - self.size[0] / 2 + 4, self.y + 4, self.size[0] - 8, self.size[1] - 8)

    def update(self, dt, gravity):
        self.vy += gravity * dt            # gravity effect
        self.y += self.vy * dt

    def draw(self, surface):
        surface.blit(self.image, (self.x - self.size[0] / 2, self.y))

    def on_catch(self, game):
        raise NotImplementedError

    def on_miss(self, game):
        if self.costs_life_on_miss:
            game.lose_life(self.x)


class Crystal(Item):
    image_name, weight, costs_life_on_miss = "crystal.png", 55, True

    def on_catch(self, game):
        game.add_score(10, self.x, self.y)
        game.assets.play("catch.wav")


class Potion(Item):
    image_name, weight, costs_life_on_miss = "potion.png", 18, True

    def on_catch(self, game):
        game.add_score(25, self.x, self.y)
        game.lives = min(MAX_LIVES, game.lives + 1)
        game.assets.play("powerup.wav")


class Fireball(Item):
    image_name, size = "fireball.png", (44, 56)
    weight = 0                 # chosen by Level.hazard_chance instead

    def on_catch(self, game):
        if game.player.shield:
            game.player.shield = False
            game.popup("Blocked!", self.x, self.y, GOLD)
            game.assets.play("powerup.wav")
        else:
            game.lose_life(self.x, hit=True)


class ShieldOrb(Item):
    image_name, weight = "shield.png", 7

    def on_catch(self, game):
        game.player.shield = True
        game.popup("Shield!", self.x, self.y, (150, 200, 255))
        game.assets.play("powerup.wav")


class Hourglass(Item):
    image_name, weight = "hourglass.png", 8

    def on_catch(self, game):
        game.elapsed = max(0.0, game.elapsed - 5)
        game.popup("+5s", self.x, self.y, GREEN)
        game.assets.play("powerup.wav")


# -------------------------------------------------------------------- Level
class Level:

    def __init__(self, number, spawn_interval, start_speed, hazard_chance, gravity_scale):
        self.number = number
        self.spawn_interval = spawn_interval
        self.start_speed = start_speed
        self.hazard_chance = hazard_chance
        self.gravity_scale = gravity_scale


LEVELS = [Level(1, 1.00, 60, 0.20, 1.0), Level(2, 0.75, 90, 0.30, 1.25), Level(3, 0.55, 120, 0.38, 1.5)]
LEVEL_SECONDS = GAME_SECONDS // len(LEVELS)
GOOD_TYPES = [Crystal, Potion, ShieldOrb, Hourglass]


# ------------------------------------------------------------- FloatingText
class FloatingText:
    def __init__(self, text, x, y, color, font):
        self.image = font.render(text, True, color)
        self.x, self.y, self.life = x, y, 0.9

    def update(self, dt):
        self.y -= 50 * dt
        self.life -= dt

    def draw(self, surface):
        surface.blit(self.image, self.image.get_rect(center=(self.x, self.y)))


# ------------------------------------------------------------- GameManager
class GameManager:

    def __init__(self):
        pygame.init()
        try:
            pygame.mixer.init()
        except pygame.error:
            print("Audio unavailable - running without sound.")
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("Fantasy Quest: Crystal Catcher")
        self.clock = pygame.time.Clock()
        self.assets = AssetManager()
        self.bg = self.assets.image("background.png", (WIDTH, HEIGHT))
        self.heart = self.assets.image("heart.png", (28, 28))
        self.fonts = {k: pygame.font.SysFont("arial", s, bold=b)
                      for k, (s, b) in {"big": (56, True), "mid": (30, True), "small": (22, False), "tiny": (18, False)}.items()}
        self.lang, self.state, self.menu_index = "en", "menu", 0
        self.high_score = self.load_high_score()
        self.reset()

    # ---- helpers
    def t(self, key):
        return TEXT[self.lang][key]

    def load_high_score(self):
        try:
            with open(SCORE_FILE) as f:
                return int(f.read().strip())
        except (OSError, ValueError):
            return 0

    def save_high_score(self):
        try:
            with open(SCORE_FILE, "w") as f:
                f.write(str(self.high_score))
        except OSError:
            pass

    def text(self, msg, font, color, center=None, topleft=None, topright=None):
        img = self.fonts[font].render(msg, True, color)
        shadow = self.fonts[font].render(msg, True, (0, 0, 0))
        rect = img.get_rect(center=center) if center else img.get_rect(topleft=topleft) if topleft else img.get_rect(topright=topright)
        self.screen.blit(shadow, rect.move(2, 2))
        self.screen.blit(img, rect)

    def reset(self):
        self.player = Player(self.assets)
        self.items, self.popups = [], []
        self.score, self.lives, self.elapsed = 0, START_LIVES, 0.0
        self.level_index, self.spawn_timer = 0, 1.0
        self.won, self.new_best, self.flash = False, False, 0.0

    @property
    def level(self):
        return LEVELS[self.level_index]

    # ---- game rules
    def add_score(self, points, x, y):
        self.score += points
        self.popup("+%d" % points, x, y, GOLD)

    def lose_life(self, x, hit=False):
        self.lives -= 1
        self.flash = 0.25
        self.assets.play("hit.wav" if hit else "miss.wav")
        self.popup("-1", x, HEIGHT - 120, RED)

    def popup(self, msg, x, y, color):
        self.popups.append(FloatingText(msg, x, y, color, self.fonts["small"]))

    def spawn(self):
        lvl = self.level
        x = random.randint(30, WIDTH - 30)
        vy = lvl.start_speed * random.uniform(0.8, 1.3)
        if random.random() < lvl.hazard_chance:
            self.items.append(Fireball(self.assets, x, vy))
        else:
            cls = random.choices(GOOD_TYPES, weights=[c.weight for c in GOOD_TYPES])[0]
            self.items.append(cls(self.assets, x, vy))

    def end_game(self, won):
        self.won, self.state = won, "over"
        self.assets.play("win.wav" if won else "lose.wav")
        if self.score > self.high_score:
            self.high_score, self.new_best = self.score, True
            self.save_high_score()

    def update_play(self, dt):
        self.player.update(dt, pygame.key.get_pressed())
        self.elapsed += dt
        self.level_index = max(self.level_index, min(int(self.elapsed // LEVEL_SECONDS), len(LEVELS) - 1))
        self.spawn_timer -= dt
        if self.spawn_timer <= 0:
            self.spawn()
            self.spawn_timer = self.level.spawn_interval * random.uniform(0.7, 1.2)
        catcher = self.player.catch_rect
        for item in self.items[:]:
            item.update(dt, GRAVITY * self.level.gravity_scale)
            if item.rect.colliderect(catcher):               # collision detection
                item.on_catch(self)
                self.items.remove(item)
            elif item.y > HEIGHT - 20:
                item.on_miss(self)
                self.items.remove(item)
        for p in self.popups[:]:
            p.update(dt)
            if p.life <= 0:
                self.popups.remove(p)
        self.flash = max(0.0, self.flash - dt)
        if self.lives <= 0:
            self.end_game(False)
        elif self.elapsed >= GAME_SECONDS:
            self.end_game(True)

    # ---- input
    def on_key(self, key):
        if key == pygame.K_l and self.state in ("menu", "instructions"):
            self.lang = "ms" if self.lang == "en" else "en"
        elif self.state == "menu":
            if key == pygame.K_UP:
                self.menu_index = (self.menu_index - 1) % 3
            elif key == pygame.K_DOWN:
                self.menu_index = (self.menu_index + 1) % 3
            elif key in (pygame.K_RETURN, pygame.K_SPACE):
                if self.menu_index == 0:
                    self.reset()
                    self.state = "playing"
                elif self.menu_index == 1:
                    self.state = "instructions"
                else:
                    self.quit()
        elif self.state == "instructions":
            if key in (pygame.K_RETURN, pygame.K_ESCAPE, pygame.K_BACKSPACE):
                self.state = "menu"
        else:                                              # playing / paused / over
            if key == pygame.K_r:
                self.reset()
                self.state = "playing"
            elif key == pygame.K_ESCAPE:
                self.state = "menu"
            elif key == pygame.K_p and self.state in ("playing", "paused"):
                self.state = "paused" if self.state == "playing" else "playing"

    # ---- drawing
    def draw_play(self):
        self.screen.blit(self.bg, (0, 0))
        for item in self.items:
            item.draw(self.screen)
        self.player.draw(self.screen)
        for p in self.popups:
            p.draw(self.screen)
        if self.flash > 0:
            veil = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            veil.fill((255, 0, 0, int(120 * self.flash / 0.25)))
            self.screen.blit(veil, (0, 0))
        self.draw_hud()

    def draw_hud(self):
        left = max(0, GAME_SECONDS - self.elapsed)
        self.text("%s: %d" % (self.t("score"), self.score), "mid", WHITE, topleft=(14, 8))
        self.text("%s: %d" % (self.t("best"), max(self.high_score, self.score)), "tiny", GOLD, topleft=(16, 46))
        self.text("%s: %d" % (self.t("time"), left + 0.99), "mid", WHITE if left > 10 else RED, topright=(WIDTH - 14, 8))
        name = TEXT[self.lang]["levels"][self.level_index]
        self.text("%s %d - %s" % (self.t("level"), self.level.number, name), "tiny", WHITE, topright=(WIDTH - 16, 46))
        for i in range(self.lives):
            self.screen.blit(self.heart, (WIDTH / 2 - 100 + i * 30, 10))
        if self.player.shield:
            self.text(self.t("shield"), "tiny", (150, 200, 255), center=(WIDTH / 2, 56))

    def draw_overlay(self, alpha=150):
        veil = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        veil.fill((0, 0, 0, alpha))
        self.screen.blit(veil, (0, 0))

    def draw_menu(self):
        self.screen.blit(self.bg, (0, 0))
        self.draw_overlay(90)
        self.text(self.t("title"), "big", GOLD, center=(WIDTH / 2, 110))
        self.text(self.t("subtitle"), "mid", WHITE, center=(WIDTH / 2, 165))
        self.screen.blit(self.player.image, self.player.image.get_rect(center=(WIDTH / 2, 255)))
        for i, label in enumerate(self.t("menu")):
            selected = i == self.menu_index
            self.text(("> %s <" if selected else "%s") % label, "mid", GOLD if selected else WHITE,
                      center=(WIDTH / 2, 345 + i * 52))
        self.text(self.t("lang_hint"), "small", WHITE, center=(WIDTH / 2, 540))
        self.text(self.t("nav_hint"), "tiny", (200, 200, 200), center=(WIDTH / 2, 572))

    def draw_instructions(self):
        self.screen.blit(self.bg, (0, 0))
        self.draw_overlay(170)
        self.text(self.t("ins_title"), "big", GOLD, center=(WIDTH / 2, 70))
        for i, line in enumerate(self.t("ins")):
            self.text(line, "small", WHITE, center=(WIDTH / 2, 150 + i * 40))
        for i, cls in enumerate([Crystal, Potion, Fireball, ShieldOrb, Hourglass]):
            img = self.assets.image(cls.image_name, cls.size)
            self.screen.blit(img, img.get_rect(center=(210 + i * 95, 465)))
        self.text(self.t("lang_hint"), "tiny", WHITE, center=(WIDTH / 2, 530))
        self.text(self.t("back"), "small", GOLD, center=(WIDTH / 2, 565))

    def draw(self):
        if self.state == "menu":
            self.draw_menu()
        elif self.state == "instructions":
            self.draw_instructions()
        else:
            self.draw_play()
            if self.state == "paused":
                self.draw_overlay()
                self.text(self.t("paused"), "big", WHITE, center=(WIDTH / 2, 270))
                self.text(self.t("paused_hint"), "small", GOLD, center=(WIDTH / 2, 330))
            elif self.state == "over":
                self.draw_overlay(170)
                self.text(self.t("win" if self.won else "lose"), "big", GREEN if self.won else RED, center=(WIDTH / 2, 230))
                self.text("%s: %d" % (self.t("final"), self.score), "mid", WHITE, center=(WIDTH / 2, 300))
                if self.new_best:
                    self.text(self.t("new_best"), "mid", GOLD, center=(WIDTH / 2, 345))
                self.text(self.t("over_hint"), "small", GOLD, center=(WIDTH / 2, 410))

    # ---- main loop
    def quit(self):
        pygame.quit()
        sys.exit()

    def run(self):
        while True:
            dt = min(self.clock.tick(FPS) / 1000.0, 0.05)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.quit()
                elif event.type == pygame.KEYDOWN:
                    self.on_key(event.key)
            if self.state == "playing":
                self.update_play(dt)
            self.draw()
            pygame.display.flip()


if __name__ == "__main__":
    GameManager().run()
