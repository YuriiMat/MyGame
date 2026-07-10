import pygame
import time


import math
import random
from collections import deque

pygame.init()

# Вікно
WIDTH, HEIGHT = 1000, 800
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Bob & Robin")

clock = pygame.time.Clock()

# Кольори
BLACK = (0, 0, 0)
RED = (255, 0, 0)
PURPLE = (160, 80, 200)
WHITE = (255, 255, 255)

# Шрифт
font = pygame.font.SysFont(None, 26)

# Хмаринка
bubble_image = pygame.image.load("Cloude4.png").convert_alpha()

# ---- Base ----
BASE_SIZE = 80
base_x = WIDTH // 2 - BASE_SIZE // 2
base_y = HEIGHT // 2 - BASE_SIZE // 2
BASE_COLOR = (0, 200, 0)  # зелений
base_active = False
BASE_MAX_HP = 100
base_hp = BASE_MAX_HP

# Час між хвилями
WAVE_DELAY = 10  # секунд між хвилями
wave_active = False
next_wave_time = time.time()

wave = 1
enemies_per_wave = 5
enemies_spawned = 0

# ---- Enemies ----
ENEMY_SIZE = 30
BASE_ENEMY_SPEED = 2
enemy_speed = BASE_ENEMY_SPEED + wave * 0.3
ENEMY_DAMAGE = 20
ENEMY_SPAWN_TIME = 0.5  # сек
ENEMY_MAX_HP = 30

enemies = []
last_enemy_spawn = time.time()
enemy_attack_timers = {}


# ---- Bob ----
bob_size = 40
bob_x, bob_y = 100, 300
bob_speed = 5
BOB_MAX_HP = 100
bob_hp = BOB_MAX_HP

# ---- Robin ----
robin_size = 40
robin_x, robin_y = 500, 300
robin_speed = 4
robin_active = False
ROBIN_MAX_HP = 80
robin_hp = ROBIN_MAX_HP

DEFENSE_RADIUS = 100

ENEMY_ATTACK_RADIUS = 35
ENEMY_ATTACK_COOLDOWN = 1.0  # сек

MIN_DISTANCE = 40  # мін. дистанція (≈ 1 см)
SLOW_RADIUS = 120  # зона гальмування
WIGGLE_AMPLITUDE = 0.6  # хитання
SIDE_OFFSET = 0.35  # обхід збоку
LAG_CHANCE = 0.01  # шанс "відстати"
LAG_TIME = 0.5  # сек

robin_lag_until = 0

# Для переслідування із запізненням
bob_positions = deque(maxlen=30)  # ≈ 2 клітинки затримки

# Діалог
dialog_state = 0
dialog_start_time = time.time()  # старт гри

# --- UI повідомлення ---
ui_message = ""
ui_message_until = 0


def spawn_enemy():
    side = random.choice(["top", "bottom", "left", "right"])

    if side == "top":
        x = random.randint(0, WIDTH)
        y = -ENEMY_SIZE
    elif side == "bottom":
        x = random.randint(0, WIDTH)
        y = HEIGHT + ENEMY_SIZE
    elif side == "left":
        x = -ENEMY_SIZE
        y = random.randint(0, HEIGHT)
    else:
        x = WIDTH + ENEMY_SIZE
        y = random.randint(0, HEIGHT)

    enemies.append({
        "rect": pygame.Rect(x, y, ENEMY_SIZE, ENEMY_SIZE),
        "hp": ENEMY_MAX_HP,
        "last_attack": 0
    })


running = True
while running:
    screen.fill(BLACK)

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    # --- Рух Bob ---
    keys = pygame.key.get_pressed()
    if keys[pygame.K_LEFT]:
        bob_x -= bob_speed
    if keys[pygame.K_RIGHT]:
        bob_x += bob_speed
    if keys[pygame.K_UP]:
        bob_y -= bob_speed
    if keys[pygame.K_DOWN]:
        bob_y += bob_speed

    bob_rect = pygame.Rect(bob_x, bob_y, bob_size, bob_size)

    # Запамʼятовуємо шлях Bob
    bob_positions.append((bob_x, bob_y))

    # --- Robin ---
    robin_rect = pygame.Rect(robin_x, robin_y, robin_size, robin_size)

    bob_x + bob_size // 2
    robin_x + robin_size // 2


    # Перевірка близькості
    if not robin_active and bob_rect.colliderect(robin_rect.inflate(80, 80)):
        dialog_state = 1
        dialog_start_time = time.time()

    # Діалог і активація Robin
    if dialog_state == 1 and time.time() - dialog_start_time > 2:
        dialog_state = 2
        dialog_start_time = time.time()
        robin_active = True
        base_active = True  #  база зʼявляється

    # Початкова хмаринка (2 секунди після старту)
    if dialog_state == 0 and time.time() - dialog_start_time > 2:
        dialog_state = -1  # нейтральний стан, нічого не показує

    if robin_active and len(bob_positions) > 10:

        # іноді Robin "задумується"
        if time.time() < robin_lag_until:
            pass
        else:
            if random.random() < LAG_CHANCE:
                robin_lag_until = time.time() + LAG_TIME

            target_x, target_y = bob_positions[0]

            bob_cx = bob_x + bob_size // 2
            bob_cy = bob_y + bob_size // 2
            robin_cx = robin_x + robin_size // 2
            robin_cy = robin_y + robin_size // 2

            dx = bob_cx - robin_cx
            dy = bob_cy - robin_cy
            distance = math.hypot(dx, dy)

            if distance > MIN_DISTANCE:
                # нормалізований напрямок
                nx = dx / distance
                ny = dy / distance

                # бокове зміщення (перпендикуляр)
                side_x = -ny * SIDE_OFFSET
                side_y = nx * SIDE_OFFSET

                # плавне гальмування
                speed_factor = min(1, (distance - MIN_DISTANCE) / SLOW_RADIUS)
                speed = robin_speed * speed_factor

                # хитання
                wiggle = math.sin(time.time() * 6) * WIGGLE_AMPLITUDE

                robin_x += (nx + side_x) * speed + wiggle
                robin_y += (ny + side_y) * speed - wiggle

# Шкала життя Боба і Робіна
    def draw_character_hp(x, y, hp, max_hp):
        width = 40
        height = 6
        ratio = max(0, hp / max_hp)

        pygame.draw.rect(screen, (60, 60, 60), (x, y - 10, width, height))
        pygame.draw.rect(screen, (0, 200, 0), (x, y - 10, width * ratio, height))


    def in_defense_radius(px, py, enemy_rect):
        dx = px - enemy_rect.centerx
        dy = py - enemy_rect.centery
        return math.hypot(dx, dy) < DEFENSE_RADIUS

    # --- База ---
    def draw_base_hp():
        BAR_WIDTH = 200
        BAR_HEIGHT = 20
        x = 20
        y = 20

        ratio = base_hp / BASE_MAX_HP

        pygame.draw.rect(screen, (80, 80, 80), (x, y, BAR_WIDTH, BAR_HEIGHT))
        pygame.draw.rect(screen, (0, 200, 0), (x, y, BAR_WIDTH * ratio, BAR_HEIGHT))
        pygame.draw.rect(screen, WHITE, (x, y, BAR_WIDTH, BAR_HEIGHT), 2)

        text = font.render("Base HP", True, WHITE)
        screen.blit(text, (x, y - 22))

    if base_active:
        pygame.draw.rect(
            screen,
            BASE_COLOR,
            (base_x, base_y, BASE_SIZE, BASE_SIZE)
        )
        draw_base_hp()




    now = time.time()

    # старт нової хвилі
    if base_active and not wave_active and now >= next_wave_time:
        wave_active = True
        enemies_spawned = 0

        ui_message = f"Wave {wave}"
        ui_message_until = now + 3  # показувати 3 секунди

        #  одразу 3 вороги
        for _ in range(3):
            spawn_enemy()
            enemies_spawned += 1
        last_enemy_spawn = now

    if wave_active and enemies_spawned < enemies_per_wave:
        if now - last_enemy_spawn > ENEMY_SPAWN_TIME:
            spawn_enemy()
            enemies_spawned += 1
            last_enemy_spawn = now

    # Завершення хвилі
    if wave_active and enemies_spawned >= enemies_per_wave and not enemies:
        wave_active = False
        wave += 1
        enemies_per_wave += 3
        next_wave_time = now + WAVE_DELAY

        ui_message = "Wave cleared!"
        ui_message_until = now + 3

    if ui_message and now < ui_message_until:
        text = font.render(ui_message, True, WHITE)
        rect = text.get_rect(center=(WIDTH // 2, 60))
        screen.blit(text, rect)



    # --- Логіка ворогів ---
    base_rect = pygame.Rect(base_x, base_y, BASE_SIZE, BASE_SIZE)

    for enemy in enemies[:]:
        rect = enemy["rect"]

        #  рух до бази
        rect = enemy["rect"]

        dx = base_rect.centerx - rect.centerx
        dy = base_rect.centery - rect.centery
        dist = math.hypot(dx, dy)

        if dist != 0:
            rect.x += (dx / dist) * BASE_ENEMY_SPEED
            rect.y += (dy / dist) * BASE_ENEMY_SPEED

        # атака Bob
        if math.hypot(rect.centerx - (bob_x + bob_size // 2),
                        rect.centery - (bob_y + bob_size // 2)) < ENEMY_ATTACK_RADIUS:

            if now - enemy["last_attack"] > ENEMY_ATTACK_COOLDOWN:
                bob_hp -= ENEMY_DAMAGE
                enemy["last_attack"] = now


        # атака Robin
        elif math.hypot(rect.centerx - (robin_x + robin_size // 2),
                        rect.centery - (robin_y + robin_size // 2)) < ENEMY_ATTACK_RADIUS:

            if now - enemy["last_attack"] > ENEMY_ATTACK_COOLDOWN:
                robin_hp -= ENEMY_DAMAGE
                enemy["last_attack"] = now

        # Удар по базі
        elif rect.colliderect(base_rect):
            base_hp -= ENEMY_DAMAGE
            enemies.remove(enemy)
            continue
        # Захист Bob / Robin (нанесення урону ворогу)
        if in_defense_radius(bob_x + bob_size // 2, bob_y + bob_size // 2, rect) \
                or in_defense_radius(robin_x + robin_size // 2, robin_y + robin_size // 2, rect):
            enemy["hp"] -= 10   # урон героя
        # смерть ворога
        if enemy["hp"] <= 0:
            enemies.remove(enemy)
            continue

        # малювання ворога
        pygame.draw.rect(screen, (255, 120, 0), rect)
        # HP ворога
        hp_ratio = enemy["hp"] / ENEMY_MAX_HP
        pygame.draw.rect(screen, (255, 0, 0),
                         (rect.x, rect.y - 6, ENEMY_SIZE * hp_ratio, 4))

    # --- Спавн ворогів ---
    if base_active and enemies_spawned < enemies_per_wave:
        if time.time() - last_enemy_spawn > ENEMY_SPAWN_TIME:
            spawn_enemy()
            enemies_spawned += 1
            last_enemy_spawn = time.time()

    if enemies_spawned >= enemies_per_wave and not enemies:
        wave += 1
        enemies_spawned = 0
        enemies_per_wave += 3

    if wave_active and enemies_spawned < enemies_per_wave:
        if now - last_enemy_spawn > ENEMY_SPAWN_TIME:
            spawn_enemy()
            enemies_spawned += 1
            last_enemy_spawn = now



    if base_hp <= 0:
        running = False
        print("GAME OVER")

    if wave > 5:
        running = False
        print("YOU WIN!")


   # Sounds of game
    #pygame.mixer.init()

  #  hit_sound = pygame.mixer.Sound("hit.wav")
   # enemy_die_sound = pygame.mixer.Sound("enemy_die.wav")

   # hit_sound.play()
   # enemy_die_sound.play()

    # --- Малювання персонажів ---
    pygame.draw.rect(screen, RED, bob_rect)
    pygame.draw.rect(screen, PURPLE, (robin_x, robin_y, robin_size, robin_size))

    draw_character_hp(bob_x, bob_y, bob_hp, BOB_MAX_HP)
    draw_character_hp(robin_x, robin_y, robin_hp, ROBIN_MAX_HP)

    # --- Хмаринки ---
    def draw_bubble(text, x, y):
        bubble_rect = bubble_image.get_rect()
        bubble_rect.midbottom = (x, y - 10)
        text_surface = font.render(text, True, WHITE)
        text_rect = text_surface.get_rect(center=bubble_rect.center)
        screen.blit(bubble_image, bubble_rect)
        screen.blit(text_surface, text_rect)


    if dialog_state == 0:
        draw_bubble("Ну, в добру путь!", bob_x + bob_size // 2, bob_y)

    if dialog_state == 1:
        draw_bubble("ks ks ks", bob_x + bob_size // 2, bob_y)

    if dialog_state == 2 and time.time() - dialog_start_time < 4:
        draw_bubble("I'm in!", robin_x + robin_size // 2, robin_y)


# Перемога/Програш
    game_state = "game"  # game / win / lose
    if base_hp <= 0:
        game_state = "lose"

    if game_state == "lose":
        text = font.render("GAME OVER", True, (255, 0, 0))
        rect = text.get_rect(center=(WIDTH // 2, HEIGHT // 2))
        screen.blit(text, rect)

    if wave > 5:
        game_state = "win"

    if game_state == "win":
        text = font.render("YOU WIN!", True, (0, 255, 0))
        rect = text.get_rect(center=(WIDTH // 2, HEIGHT // 2))
        screen.blit(text, rect)

    pygame.display.flip()
    clock.tick(60)

pygame.quit()