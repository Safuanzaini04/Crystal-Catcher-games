"""
RAGE MARIO

Control:
  Kiri/Kanan atau A/D = gerak
  Space / W / Atas    = lompat
  H = hint (tunjuk jebakan)
  R = restart
"""
import random
import sys
import pygame

pygame.init()
#jump_sound = pygame.mixer.Sound("catch.wav")
W, H = 960, 540
WORLD_W = 3500
screen = pygame.display.set_mode((W, H))
pygame.display.set_caption("RAGE MARIO - Lets Die More :)")
clock = pygame.time.Clock()
font = pygame.font.SysFont(None, 30)
big = pygame.font.SysFont(None, 64)

GROUND_Y = 460

TAUNTS = [
    "Badluck for you",
    "GG skill issues",
    "Boring...Just quit the game",
    "You can do it, or maybe just fall",
    "Die in 3... 2... 1...",
]

SPIKE_TAUNTS = [
    "Ouch! That looks painful",
    "Spikes 1 - You 0",
    "Did you not see the spikes? Really?",
    "Poke poke poke... you're dead",
]


class Plat:
    """kind: solid | runaway | vanish | fake"""

    def __init__(self, x, y, w, h, kind="solid", dx=0, dy=0,
                 trig=170, wait=90, speed=14):
        self.home = pygame.Rect(x, y, w, h)
        self.rect = self.home.copy()
        self.kind = kind
        self.target = (x + dx, y + dy)
        self.trig = trig
        self.wait = wait
        self.speed = speed
        self.state = "idle"
        self.timer = 0

    def reset(self):
        self.rect = self.home.copy()
        self.state = "idle"
        self.timer = 0

    @property
    def solid(self):
        if self.kind == "fake":
            return False
        if self.kind == "vanish" and self.state == "gone":
            return False
        return True

    def _step_to(self, tx, ty):
        """gerak ke (tx,ty), return True kalau dah sampai"""
        for axis, t in (("x", tx), ("y", ty)):
            cur = getattr(self.rect, axis)
            diff = t - cur
            if abs(diff) <= self.speed:
                setattr(self.rect, axis, t)
            else:
                setattr(self.rect, axis, cur + (self.speed if diff > 0 else -self.speed))
        return self.rect.x == tx and self.rect.y == ty

    def update(self, player):
        pr = player.rect
        if self.kind == "runaway":
            if self.state == "idle":
                # lari bila player tengah melayang & dah dekat
                if (not player.on_ground
                        and abs(pr.centerx - self.rect.centerx) < self.trig
                        and pr.bottom <= self.rect.top + 40):
                    self.state = "away"
            elif self.state == "away":
                if self._step_to(*self.target):
                    self.state = "wait"
                    self.timer = self.wait
            elif self.state == "wait":
                self.timer -= 1
                if self.timer <= 0:
                    self.state = "return"
            elif self.state == "return":
                if self._step_to(self.home.x, self.home.y):
                    self.state = "idle"

        elif self.kind == "vanish":
            standing = (pr.bottom == self.rect.top
                        and pr.right > self.rect.left and pr.left < self.rect.right)
            if self.state == "idle" and standing:
                self.state = "warn"
                self.timer = 2 #timer lantai hilang
            elif self.state == "warn":
                self.timer -= 1
                if self.timer <= 0:
                    self.state = "gone"
                    self.timer = 150
            elif self.state == "gone":
                self.timer -= 1
                if self.timer <= 0:
                    self.state = "idle"


class Spike:
    """Duri atas tanah.
    kind = "static" : sentiasa nampak, terlanggar terus mati
    kind = "pop"    : tersembunyi, tiba2 naik bila di-activate()
    kind = "slide"  : nampak biasa, tapi lari ke depan (dx) bila player melompat dekat
    """
    FULL_H = 30

    def __init__(self, x, w, kind="static", dx=0, trig=200, speed=14):
        self.home_x = x
        self.x = x
        self.w = w
        self.kind = kind
        self.target_x = x + dx
        self.trig = trig      # jarak player untuk trigger
        self.speed = speed    # kelajuan gerak (px/frame)
        self.reset()

    def reset(self):
        self.x = self.home_x
        self.moving = False
        self.active = self.kind in ("static", "slide")
        self.h = self.FULL_H if self.active else 0

    def activate(self):
        self.active = True

    def update(self, player=None):
        if self.kind == "pop":
            if self.active and self.h < self.FULL_H:
                self.h = min(self.h + 10, self.FULL_H)

        elif self.kind == "slide" and player is not None:
            pr = player.rect
            # trigger: player tengah melayang, masih di sebelah kiri duri, dan dah dekat
            if (not self.moving and self.x == self.home_x
                    and not player.on_ground
                    and pr.centerx < self.x
                    and abs(pr.centerx - (self.x + self.w / 2)) < self.trig):
                self.moving = True

            if self.moving:
                if self.x < self.target_x:
                    self.x = min(self.x + self.speed, self.target_x)
                else:
                    self.x = max(self.x - self.speed, self.target_x)
                if self.x == self.target_x:
                    self.moving = False

    @property
    def hitbox(self):
        # hitbox dikecilkan sikit supaya adil
        if self.h < 12:
            return None
        return pygame.Rect(self.x + 4, GROUND_Y - self.h + 6, self.w - 8, self.h - 6)

    def draw(self, cam, hint=False):
        if self.h > 0:
            n = max(1, self.w // 20)
            tw = self.w / n
            for i in range(n):
                pts = [
                    (self.x + i * tw - cam, GROUND_Y),
                    (self.x + (i + 1) * tw - cam, GROUND_Y),
                    (self.x + (i + 0.5) * tw - cam, GROUND_Y - self.h),
                ]
                pygame.draw.polygon(screen, (205, 205, 215), pts)
                pygame.draw.polygon(screen, (60, 60, 70), pts, 2)
        elif hint:
            pygame.draw.rect(screen, (255, 0, 0),
                             (self.x - cam, GROUND_Y - self.FULL_H, self.w, self.FULL_H), 2)


class Player:
    def __init__(self):
        self.rect = pygame.Rect(60, 380, 32, 44)
        self.vx = 0.0
        self.vy = 0.0
        self.on_ground = False

    def update(self, keys, plats):
        self.vx = 0
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            self.vx = -5
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            self.vx = 5
        if (keys[pygame.K_SPACE] or keys[pygame.K_w] or keys[pygame.K_UP]) and self.on_ground:
            self.vy = -14
            self.on_ground = False
            #jump_sound.play()

        self.vy = min(self.vy + 0.6, 16)
        solids = [p.rect for p in plats if p.solid]

        self.rect.x += round(self.vx)
        self.rect.x = max(0, min(self.rect.x, WORLD_W - self.rect.w))
        for s in solids:
            if self.rect.colliderect(s):
                if self.vx > 0:
                    self.rect.right = s.left
                elif self.vx < 0:
                    self.rect.left = s.right

        self.rect.y += round(self.vy)
        self.on_ground = False
        for s in solids:
            if self.rect.colliderect(s):
                if self.vy > 0:
                    self.rect.bottom = s.top
                    self.on_ground = True
                elif self.vy < 0:
                    self.rect.top = s.bottom
                self.vy = 0


def build_level():
    return [
        Plat(0, GROUND_Y, 700, 100),
        # batu umpan: lari jatuh bila kau melompat dekat
        Plat(780, 440, 100, 20, "runaway", dy=300, trig=170),
        Plat(900, GROUND_Y, 200, 100),
        # lantai palsu - nampak macam tanah, tapi kosong
        Plat(1100, GROUND_Y, 100, 100, "fake"),
        Plat(1200, GROUND_Y, 300, 100),
        # lompat atas batu
        Plat(1560, 400, 90, 20),
        Plat(1660, 350, 90, 20, "vanish"),
        Plat(1800, GROUND_Y, 200, 100),
        # tanah yang lari -> lubang muncul tempat kau mendarat
        Plat(2000, GROUND_Y, 200, 100, "runaway", dx=-200, trig=230, wait=120, speed=16),
        Plat(2200, GROUND_Y, 1300, 100),
    ]


def build_spikes():
    return [
        # duri biasa (sentiasa nampak) - kena lompat
        Spike(1320, 60, "slide", dx=-100),   # 1320 -> 1390 bila player lompat
        Spike(2400, 90),
        # duri pop-up dekat pintu sebenar (tersembunyi dulu)
        Spike(3200, 70, "pop"),
        Spike(3290, 50, "pop"),
    ]


CHECKPOINTS = [0, 900, 1800, 2200, 3000]
FAKE_DOOR = pygame.Rect(2650, GROUND_Y - 70, 50, 70)
POP_TRIGGER_DIST = 220  # jarak player ke pintu sebenar untuk duri muncul


class Game:
    def __init__(self):
        self.reset()

    def reset(self):
        self.plats = build_level()
        self.spikes = build_spikes()
        self.player = Player()
        self.cp = 0
        self.deaths = 0
        self.msg = "Lets Win...or maybe fall :)"
        self.msg_t = 180
        self.hint = False
        self.won = False
        self.door = pygame.Rect(3250, GROUND_Y - 70, 50, 70)
        self.door_target_x = self.door.x
        self.door_shy_done = False

    def say(self, text, t=150):
        self.msg, self.msg_t = text, t

    def respawn(self, x=None, taunt=None):
        for p in self.plats:
            p.reset()
        for s in self.spikes:
            s.reset()
        pl = self.player
        pl.rect.topleft = ((x if x is not None else self.cp + 30), 380)
        pl.vx = pl.vy = 0
        self.say(taunt or random.choice(TAUNTS))

    def update(self, keys):
        if self.won:
            return
        pl = self.player
        pl.update(keys, self.plats)
        for p in self.plats:
            p.update(pl)

        for c in CHECKPOINTS:
            if pl.on_ground and pl.rect.x > c + 20:
                self.cp = max(self.cp, c)

        if pl.rect.top > H + 100:
            self.deaths += 1
            self.respawn()

        # pintu palsu -> hantar balik ke checkpoint 1800
        if pl.rect.colliderect(FAKE_DOOR):
            self.deaths += 1
            self.respawn(1850, "HAHAHAHA GG FAKE DOOR")

        # pintu sebenar malu-malu: lari sekali bila kau dekat
        if (not self.door_shy_done
                and abs(pl.rect.centerx - self.door.centerx) < 140):
            self.door_shy_done = True
            self.door_target_x = self.door.x + 200
        if self.door.x < self.door_target_x:
            self.door.x = min(self.door.x + 12, self.door_target_x)

        # selepas pintu lari, duri tiba2 muncul bila player dekat pintu
        if (self.door_shy_done
                and abs(pl.rect.centerx - self.door.centerx) < POP_TRIGGER_DIST):
            for s in self.spikes:
                if s.kind == "pop":
                    s.activate()

        # duri: terlanggar terus mati
        for s in self.spikes:
            s.update(pl)  # <- dulu s.update()
            hb = s.hitbox
            if hb and pl.rect.colliderect(hb):
                self.deaths += 1
                self.respawn(taunt=random.choice(SPIKE_TAUNTS))
                break

        if pl.rect.colliderect(self.door):
            self.won = True

        if self.msg_t > 0:
            self.msg_t -= 1

    def draw(self):
        pl = self.player
        cam = max(0, min(pl.rect.centerx - W // 3, WORLD_W - W))
        screen.fill((110, 190, 255))

        # awan ringkas
        for i in range(12):
            cx = (i * 330 - cam * 0.4) % (WORLD_W) - 100
            pygame.draw.ellipse(screen, (255, 255, 255), (cx, 60 + (i % 3) * 40, 120, 40))

        for p in self.plats:
            if p.kind == "vanish" and p.state == "gone":
                continue
            r = p.rect.move(-cam, 0)
            is_ground = p.home.y == GROUND_Y
            col = (110, 70, 30) if is_ground else (150, 100, 50)
            if p.kind == "vanish" and p.state == "warn" and (p.timer // 4) % 2 == 0:
                col = (200, 160, 100)
            if self.hint and p.kind != "solid":
                col = (220, 40, 40) if p.kind != "fake" else (255, 120, 200)
            pygame.draw.rect(screen, col, r)
            if is_ground:
                pygame.draw.rect(screen, (60, 180, 60), (r.x, r.y, r.w, 12))
            else:
                pygame.draw.rect(screen, (60, 180, 60), (r.x, r.y, r.w, 6))

        # duri
        for s in self.spikes:
            s.draw(cam, self.hint)

        # pintu palsu & sebenar (sama rupa!)
        for d, label in ((FAKE_DOOR, "EXIT"), (self.door, "EXIT")):
            r = d.move(-cam, 0)
            pygame.draw.rect(screen, (90, 50, 20), r)
            pygame.draw.rect(screen, (250, 220, 90), (r.right - 14, r.centery, 6, 6))
            t = font.render(label, True, (255, 255, 255))
            screen.blit(t, (r.x + 5, r.y - 22))
            if self.hint and d is FAKE_DOOR:
                screen.blit(font.render("PALSU", True, (255, 0, 0)), (r.x, r.y - 44))

        # player
        pr = pl.rect.move(-cam, 0)
        pygame.draw.rect(screen, (220, 40, 40), pr)
        pygame.draw.rect(screen, (255, 210, 170), (pr.x + 4, pr.y + 4, pr.w - 8, 16))
        pygame.draw.rect(screen, (0, 0, 0), (pr.x + 18, pr.y + 8, 5, 5))

        # HUD
        screen.blit(font.render(f"Mati: {self.deaths}", True, (0, 0, 0)), (12, 10))
        screen.blit(font.render("R = restart", True, (0, 0, 0)), (12, 36))
        if self.msg_t > 0:
            t = font.render(self.msg, True, (0, 0, 0))
            screen.blit(t, (W // 2 - t.get_width() // 2, 90))

        if self.won:
            screen.blit(big.render("omg you win T_T", True, (255, 255, 0)), (W // 2 - 110, 190))
            t = font.render(f"Mati {self.deaths} kali. Tekan R untuk main semula", True, (0, 0, 0))
            screen.blit(t, (W // 2 - t.get_width() // 2, 260))


def main():
    game = Game()
    while True:
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if e.type == pygame.KEYDOWN:
                if e.key == pygame.K_r:
                    game.reset()
                elif e.key == pygame.K_h:
                    game.hint = not game.hint
        game.update(pygame.key.get_pressed())
        game.draw()
        pygame.display.flip()
        clock.tick(60)


if __name__ == "__main__":
    main()