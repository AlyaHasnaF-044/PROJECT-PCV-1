import cv2
import pygame
import numpy as np
import math
import random
import sys
import time


WIDTH, HEIGHT = 1280, 720
FPS = 60
CAM_W, CAM_H = 320, 240


GREEN_LOWER = np.array([35, 65, 45], dtype=np.uint8)
GREEN_UPPER = np.array([95, 255, 255], dtype=np.uint8)

BG = (58, 29, 17)
PANEL = (34, 18, 13)
PANEL_2 = (61, 34, 22)
GOLD = (173, 119, 61)
CREAM = (255, 239, 208)
MUTED = (174, 145, 115)
GREEN = (75, 245, 111)
GREEN_DARK = (65, 111, 53)
ORANGE = (255, 145, 48)
RED = (255, 76, 59)
BLUE = (117, 202, 231)


INGREDIENTS = [
    {"id": "egg", "name": "Telur", "icon": "🥚", "color": (255, 218, 112)},
    {"id": "onion", "name": "Bawang", "icon": "🧅", "color": (197, 164, 116)},
    {"id": "rice", "name": "Nasi", "icon": "🍚", "color": (245, 242, 220)},
    {"id": "tomato", "name": "Tomat", "icon": "🍅", "color": (220, 63, 47)},
    {"id": "carrot", "name": "Wortel", "icon": "🥕", "color": (239, 130, 45)},
    {"id": "chili", "name": "Cabai", "icon": "🌶️", "color": (213, 52, 42)},
    {"id": "mushroom", "name": "Jamur", "icon": "🍄", "color": (211, 188, 152)},
]
RECIPES = [
    {"name": "Nasi Goreng Mama", "items": ["egg", "onion", "rice", "carrot"], "points": 300},
    {"name": "Nasi Sayur", "items": ["rice", "carrot", "mushroom"], "points": 250},
    {"name": "Tumis Pedas", "items": ["onion", "chili", "carrot"], "points": 250},
    {"name": "Nasi Telur", "items": ["rice", "egg", "onion"], "points": 250},
    {"name": "Sup Jamur", "items": ["mushroom", "carrot", "onion"], "points": 250},
]

pygame.init()
pygame.display.set_caption("Dapur Mama - Masak Pakai Sarung Tangan Hijau")
screen = pygame.display.set_mode((WIDTH, HEIGHT))
clock = pygame.time.Clock()

FONT = pygame.font.SysFont("segoeui", 20, bold=True)
SMALL = pygame.font.SysFont("segoeui", 14, bold=True)
MED = pygame.font.SysFont("segoeui", 25, bold=True)
BIG = pygame.font.SysFont("segoeui", 38, bold=True)
TITLE = pygame.font.SysFont("segoeui", 42, bold=True)

def draw_text(surface, text, font, color, center, shadow=False):
    if shadow:
        sh = font.render(text, True, (0, 0, 0))
        surface.blit(sh, (center[0] - sh.get_width() // 2 + 1, center[1] - sh.get_height() // 2 + 3))
    img = font.render(text, True, color)
    surface.blit(img, (center[0] - img.get_width() // 2, center[1] - img.get_height() // 2))

def rounded(surface, color, rect, radius=12, width=0):
    pygame.draw.rect(surface, color, rect, width=width, border_radius=radius)

def draw_background():
    screen.fill(BG)
    
    for y in range(0, 526, 4):
        t = y / 526
        col = (int(71 - 29*t), int(39 - 20*t), int(24 - 11*t))
        pygame.draw.line(screen, col, (0, y), (WIDTH, y), 4)
    # Tiled wall
    for x in range(0, WIDTH, 57):
        pygame.draw.line(screen, (93, 58, 39), (x, 0), (x, 526), 1)
    for y in range(20, 526, 57):
        pygame.draw.line(screen, (91, 57, 39), (0, y), (WIDTH, y), 1)
    # Countertop
    pygame.draw.rect(screen, (101, 58, 32), (0, 526, WIDTH, HEIGHT-526))
    pygame.draw.line(screen, (138, 88, 54), (0, 526), (WIDTH, 526), 4)
    pygame.draw.rect(screen, (74, 42, 25), (0, 532, WIDTH, HEIGHT-532))
    # Counter lower soft highlights
    pygame.draw.line(screen, (84, 49, 29), (0, 650), (WIDTH, 650), 2)

def draw_top_bar(score, seconds, order_index):
    rounded(screen, (28, 15, 11), (12, 8, WIDTH-24, 90), 18)
    pygame.draw.rect(screen, (127, 83, 46), (12, 8, WIDTH-24, 90), 2, border_radius=18)
    screen.blit(SMALL.render("SKOR", True, (255, 199, 128)), (25, 17))
    screen.blit(BIG.render(str(score), True, (255, 255, 245)), (24, 31))
    # Timer bar
    bx, by, bw, bh = 438, 27, 405, 16
    rounded(screen, (70, 54, 45), (bx, by, bw, bh), 10)
    frac = max(0, min(1, seconds / 60))
    rounded(screen, (73, 211, 111), (bx, by, int(bw*frac), bh), 10)
    draw_text(screen, f"{max(0, int(seconds))}s", SMALL, CREAM, (bx+bw//2, 55))
    screen.blit(SMALL.render(f"PESANAN {order_index+1}", True, (255, 199, 128)), (WIDTH-110, 17))
    for i in range(4):
        cx = WIDTH-127 + i*30
        pygame.draw.circle(screen, (127, 98, 72), (cx, 53), 13, 2)
        if i == order_index % 4:
            pygame.draw.circle(screen, (255, 222, 116), (cx, 53), 14, 3)

def draw_ingredient_icon(ing, center, radius=29, selected=False, wrong=False, scale=1):
    x, y = center
    # drop shadow and plate
    pygame.draw.ellipse(screen, (39, 21, 13), (x-radius, y-radius+7, radius*2, radius*2))
    pygame.draw.circle(screen, (225, 211, 187), (x, y), radius)
    pygame.draw.circle(screen, (250, 244, 229), (x, y-2), radius-3)
    # A simple, asset-free icon built from shapes and a tiny label.
    kind = ing["id"]
    if kind == "egg":
        pygame.draw.ellipse(screen, (255, 255, 242), (x-13, y-17, 26, 34))
        pygame.draw.circle(screen, (255, 188, 48), (x, y), 7)
    elif kind == "onion":
        pygame.draw.ellipse(screen, (203, 180, 143), (x-11, y-13, 22, 27))
        for dx in (-5, 0, 5):
            pygame.draw.arc(screen, (160, 133, 99), (x-11+dx, y-10, 22, 22), -1.2, 1.2, 2)
        pygame.draw.line(screen, (112, 177, 76), (x, y-14), (x, y-22), 3)
    elif kind == "rice":
        pygame.draw.ellipse(screen, (255, 255, 243), (x-14, y-7, 28, 15))
        pygame.draw.line(screen, (196, 192, 172), (x-7, y-2), (x+7, y+3), 2)
    elif kind == "tomato":
        pygame.draw.circle(screen, (223, 48, 43), (x, y), 12)
        pygame.draw.line(screen, (65, 145, 61), (x, y-11), (x-2, y-18), 3)
        pygame.draw.polygon(screen, (65, 145, 61), [(x, y-10), (x+9, y-14), (x+3, y-6)])
    elif kind == "carrot":
        pygame.draw.polygon(screen, (236, 128, 39), [(x-8, y-12), (x+10, y-9), (x+2, y+16)])
        pygame.draw.line(screen, (70, 154, 66), (x-2, y-11), (x-5, y-19), 3)
        pygame.draw.line(screen, (70, 154, 66), (x+1, y-10), (x+5, y-17), 3)
    elif kind == "chili":
        pygame.draw.arc(screen, (211, 49, 39), (x-15, y-12, 29, 29), 0.2, 4.8, 9)
        pygame.draw.line(screen, (58, 147, 63), (x-7, y-13), (x-8, y-20), 3)
    elif kind == "mushroom":
        pygame.draw.ellipse(screen, (230, 225, 205), (x-12, y-3, 24, 14))
        pygame.draw.ellipse(screen, (192, 177, 146), (x-10, y-12, 20, 15))
    if selected:
        pygame.draw.circle(screen, GREEN, (x, y), radius+7, 3)
        pygame.draw.circle(screen, (74, 130, 56), (x, y), radius+15, 2)
    if wrong:
        pygame.draw.circle(screen, (255, 95, 72), (x, y), radius+4, 4)
        pygame.draw.line(screen, RED, (x-12, y-12), (x+12, y+12), 5)
        pygame.draw.line(screen, RED, (x+12, y-12), (x-12, y+12), 5)

def draw_pan(ingredients_added):
    # stove
    rounded(screen, (43, 24, 17), (495, 565, 290, 52), 15)
    for i in range(5):
        cx = 540 + i*50
        pygame.draw.ellipse(screen, (239, 78, 29), (cx-20, 578, 40, 19))
        pygame.draw.ellipse(screen, (255, 165, 41), (cx-18, 578, 36, 8))
    # pan shadow + rim + inside
    pygame.draw.ellipse(screen, (36, 34, 39), (536, 405, 208, 156))
    pygame.draw.ellipse(screen, (117, 118, 130), (526, 393, 228, 164))
    pygame.draw.ellipse(screen, (42, 43, 51), (532, 399, 216, 153))
    pygame.draw.ellipse(screen, (110, 91, 70), (551, 417, 178, 118))
    pygame.draw.ellipse(screen, (124, 103, 80), (562, 426, 156, 98))
    # ingredients already in pan as tiny dots/shapes
    for i, iid in enumerate(ingredients_added):
        ing = next((a for a in INGREDIENTS if a["id"] == iid), INGREDIENTS[0])
        px = 605 + (i%3)*27
        py = 464 + (i//3)*18
        pygame.draw.circle(screen, ing["color"], (px, py), 7)

def draw_finished_food(recipe):
    """Draw a plated finished dish without requiring an image asset."""
    # Card behind the dish
    rounded(screen, (39, 21, 15), (390, 155, 500, 420), 24)
    pygame.draw.rect(screen, (147, 101, 53), (390, 155, 500, 420), 2, border_radius=24)
    draw_text(screen, "PESANAN SELESAI!", TITLE, (255, 204, 131), (640, 205))
    # Plate and rim
    pygame.draw.ellipse(screen, (20, 15, 13), (500, 260, 280, 190))
    pygame.draw.ellipse(screen, (230, 221, 203), (492, 248, 296, 190))
    pygame.draw.ellipse(screen, (255, 249, 230), (505, 260, 270, 166))
    pygame.draw.ellipse(screen, (218, 205, 180), (523, 275, 234, 137))
    # Food mound / fried rice base
    pygame.draw.ellipse(screen, (196, 142, 70), (548, 295, 184, 98))
    pygame.draw.ellipse(screen, (218, 166, 84), (558, 301, 164, 82))
    # Colorful ingredient pieces on the dish
    palette = {
        "egg": (255, 208, 75), "onion": (224, 202, 164), "rice": (248, 238, 211),
        "tomato": (220, 56, 42), "carrot": (247, 130, 35), "chili": (195, 45, 36),
        "mushroom": (186, 151, 112)
    }
    for i, item in enumerate(recipe["items"]):
        x = 575 + (i % 4) * 38
        y = 322 + (i // 4) * 29 + (i % 2) * 4
        color = palette.get(item, (240, 200, 100))
        pygame.draw.ellipse(screen, color, (x-10, y-7, 22, 15))
        pygame.draw.ellipse(screen, tuple(min(255, c+35) for c in color), (x-7, y-6, 12, 5))
        if item in ("carrot", "chili"):
            pygame.draw.line(screen, (69, 139, 57), (x+4, y-8), (x+9, y-13), 2)
    draw_text(screen, recipe["name"], MED, CREAM, (640, 466))
    draw_text(screen, "+300 BONUS!  •  LANJUT KE PESANAN BERIKUTNYA", SMALL, (153, 245, 154), (640, 510))


def draw_avatar(mood="neutral", t=0.0):
    """Draw Mama with a clearly changing happy/angry/neutral expression."""
    # Tiny movement makes the reaction easier to notice.
    bounce = int(3 * math.sin(t * 8)) if mood == "happy" else 0
    shake = int(3 * math.sin(t * 28)) if mood == "angry" else 0
    x, y = 49 + shake, 610 - bounce

    # Body and face
    pygame.draw.ellipse(screen, (210, 73, 55), (x-31, y+18, 64, 48))
    pygame.draw.circle(screen, (240, 194, 153), (x, y), 34)
    # Chef hat
    pygame.draw.ellipse(screen, (255, 247, 226), (x-30, y-39, 60, 22))
    pygame.draw.circle(screen, (255, 247, 226), (x-18, y-43), 14)
    pygame.draw.circle(screen, (255, 247, 226), (x, y-49), 17)
    pygame.draw.circle(screen, (255, 247, 226), (x+18, y-43), 14)
    pygame.draw.line(screen, (208, 188, 158), (x-29, y-30), (x+29, y-30), 3)

    eye_color = (55, 34, 25)
    if mood == "angry":
        pygame.draw.arc(screen, eye_color, (x-23, y-13, 15, 13), 0.1, math.pi-0.1, 3)
        pygame.draw.arc(screen, eye_color, (x+8, y-13, 15, 13), 0.1, math.pi-0.1, 3)
        pygame.draw.arc(screen, (160, 48, 37), (x-14, y+1, 28, 22), 0, math.pi, 4)
        pygame.draw.circle(screen, (245, 126, 117), (x-24, y+8), 5)
        pygame.draw.circle(screen, (245, 126, 117), (x+24, y+8), 5)
    elif mood == "happy":
        
        pygame.draw.line(screen, eye_color, (x-22, y-15), (x-7, y-9), 4)
        pygame.draw.line(screen, eye_color, (x+7, y-9), (x+22, y-15), 4)
        pygame.draw.line(screen, eye_color, (x-17, y-3), (x-8, y-3), 4)
        pygame.draw.line(screen, eye_color, (x+8, y-3), (x+17, y-3), 4)
        pygame.draw.arc(screen, (133, 52, 40), (x-13, y+13, 26, 17), math.pi, 2*math.pi, 4)
       
        pygame.draw.line(screen, (220, 75, 60), (x-29, y+5), (x-22, y+9), 3)
        pygame.draw.line(screen, (220, 75, 60), (x+22, y+9), (x+29, y+5), 3)
    else:
        pygame.draw.circle(screen, eye_color, (x-14, y-7), 3)
        pygame.draw.circle(screen, eye_color, (x+14, y-7), 3)
        pygame.draw.line(screen, (133, 52, 40), (x-9, y+12), (x+9, y+12), 3)

def draw_camera_preview(frame, tracked):
    x, y, w, h = WIDTH-140, HEIGHT-106, 126, 92
    rounded(screen, (21, 18, 14), (x-4, y-4, w+8, h+8), 12)
    pygame.draw.rect(screen, GREEN if tracked else (115, 91, 59), (x-4, y-4, w+8, h+8), 2, border_radius=12)
    if frame is not None:
        try:
            small = cv2.resize(frame, (w, h))
            rgb = cv2.cvtColor(small, cv2.COLOR_BGR2RGB)
            surf = pygame.surfarray.make_surface(np.transpose(rgb, (1, 0, 2)))
            screen.blit(surf, (x, y))
        except Exception:
            rounded(screen, (46, 38, 30), (x, y, w, h), 6)
    else:
        rounded(screen, (46, 38, 30), (x, y, w, h), 6)
        draw_text(screen, "KAMERA OFF", SMALL, CREAM, (x+w//2, y+h//2))
    draw_text(screen, "HIJAU" if tracked else "CARI WARNA HIJAU", SMALL,
              GREEN if tracked else (255, 190, 113), (x+w//2, y+h-10))

def draw_button(text, rect, color, text_color=CREAM):
    rounded(screen, color, rect, 14)
    pygame.draw.rect(screen, (145, 100, 61), rect, 2, border_radius=14)
    draw_text(screen, text, FONT, text_color, (rect[0]+rect[2]//2, rect[1]+rect[3]//2))

def draw_intro():
    
    shade = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    shade.fill((0, 0, 0, 185))
    screen.blit(shade, (0, 0))
    card = (410, 42, 460, 636)
    rounded(screen, (42, 22, 15), card, 25)
    pygame.draw.rect(screen, (147, 101, 53), card, 2, border_radius=25)
   
    rounded(screen, (25, 105, 164), (594, 61, 84, 130), 12)
    pygame.draw.rect(screen, (242, 199, 133), (594, 61, 84, 130), 2, border_radius=12)
    mini = [("🥬", 615, 84), ("🥕", 656, 84), ("🌭", 615, 122), ("🐷", 656, 122),
            ("🥔", 615, 160), ("🧅", 656, 160)]
    for emoji, x, y in mini:
        draw_text(screen, emoji, MED, CREAM, (x, y))
    draw_text(screen, "DAPUR MAMA", TITLE, (255, 204, 131), (640, 240))
    draw_text(screen, "With OPEN CV", MED, CREAM, (640, 282))
    instructions = [
        "1. Nyalakan kamera, hadapkan sarung tangan hijau.",
        "2. Gerakkan tangan → kursor ikut bergerak.",
        "3. Ambil bahan bergaris hijau, masukkan ke wajan.",
        "4. Setelah semua bahan masuk, putar tangan untuk mengaduk.",
        "5. Makanan jadi akan muncul, lalu lanjut ke pesanan berikutnya.",
        "6. Kejar skor dan selesaikan pesanan sebanyak mungkin sebelum waktu habis.",
    ]
    for i, line in enumerate(instructions):
        screen.blit(SMALL.render(line, True, (231, 213, 186)), (435, 342+i*27))
    draw_button("MULAI MASAK", (436, 575, 408, 57), ORANGE, (50, 26, 14))
    draw_text(screen, "Rekor: 0", SMALL, (197, 173, 147), (640, 651))

def main():
    cap = None
    try:
        cap = cv2.VideoCapture(0)
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, CAM_W)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, CAM_H)
    except Exception:
        cap = None

    camera_frame = None
    cursor = [WIDTH//2, HEIGHT//2]
    smooth_cursor = [WIDTH//2, HEIGHT//2]
    tracked = False
    mask = None
    started = False
    game_over = False
    score = 0
    remaining = 60.0
    order_index = 0
    completed_orders = 0
    current_recipe = random.choice(RECIPES)
    order_completed_until = 0.0
    added = []
    wrong_feedback_until = 0
    avatar_mood = "neutral"
    avatar_mood_until = 0.0
    drop_history = []  
    message = "Ambil bahan bergaris hijau"
    message_until = 0
    selected_ingredient = None
    held_ingredient = None
    
    available_ingredients = [item["id"] for item in INGREDIENTS]
    random.shuffle(available_ingredients)
    last_stir_angle = None
    stir_total = 0.0
    stirred = False
    last_time = time.time()
    running = True

   
    positions = [
        (58, 180), (350, 180), (492, 180), (680, 180),
        (866, 180), (974, 180), (1118, 180)
    ]
    ingredient_order = available_ingredients[:]

    def randomize_ingredient_positions():
       
        nonlocal ingredient_order
        ingredient_order = available_ingredients[:]
        random.shuffle(ingredient_order)

    def consume_ingredient(item_id):
       
        nonlocal ingredient_order
        if item_id in available_ingredients:
            available_ingredients.remove(item_id)
        randomize_ingredient_positions()

    def drop_item(item_id, now):
        
        nonlocal score, message, message_until, wrong_feedback_until, avatar_mood, avatar_mood_until
        correct = item_id in current_recipe["items"] and item_id not in added
        drop_history.append((item_id, correct))
        if correct:
            added.append(item_id)
            score += 100
            message = "Benar! Mama senang! +100 poin"
            avatar_mood = "happy"
        else:
            score -= 50
            wrong_feedback_until = now + 0.7
            message = "Salah bahan! Mama marah! -50 poin"
            avatar_mood = "angry"
        message_until = now + 1.4
        avatar_mood_until = now + 1.6
        consume_ingredient(item_id)

    def return_last_item():
        
        nonlocal score, message, message_until, avatar_mood, avatar_mood_until, selected_ingredient
        if not drop_history:
            message = "Belum ada bahan yang bisa dikembalikan"
            message_until = time.time() + 1.2
            return
        item_id, was_correct = drop_history.pop()
        if was_correct:
            if item_id in added:
                added.remove(item_id)
            score -= 100
            message = "Bahan benar dikembalikan: -100 poin"
        else:
            score += 50  # reverse the -50 penalty for the wrong ingredient
            message = "Bahan salah dikembalikan: +50 poin"
        if item_id not in available_ingredients:
            available_ingredients.append(item_id)
        randomize_ingredient_positions()
        selected_ingredient = None
        avatar_mood = "neutral"
        avatar_mood_until = time.time() + 0.5
        message_until = time.time() + 1.4

    while running:
        dt = clock.tick(FPS) / 1000.0
        now = time.time()
        if started and not game_over and order_completed_until <= now:
            remaining -= dt
            if remaining <= 0:
                remaining = 0
                game_over = True

        
        if started and order_completed_until and now >= order_completed_until and not game_over:
            order_completed_until = 0.0
            order_index += 1
            current_recipe = random.choice(RECIPES)
            added = []
            drop_history.clear()
            selected_ingredient = None
            available_ingredients = [item["id"] for item in INGREDIENTS]
            random.shuffle(available_ingredients)
            randomize_ingredient_positions()
            last_stir_angle = None
            stir_total = 0.0
            stirred = False
            message = "Pesanan baru! Ambil bahan yang menyala hijau"
            message_until = now + 2.0

    
        if cap is not None and cap.isOpened():
            ok, frame = cap.read()
            if ok:
                frame = cv2.flip(frame, 1)
                camera_frame = frame.copy()
                hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
                mask = cv2.inRange(hsv, GREEN_LOWER, GREEN_UPPER)
                kernel = np.ones((5, 5), np.uint8)
                mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
                mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
                contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
                if contours:
                    largest = max(contours, key=cv2.contourArea)
                    if cv2.contourArea(largest) > 250:
                        M = cv2.moments(largest)
                        if M["m00"] > 0:
                            # Convert webcam coordinates into game coordinates.
                            tx = int((M["m10"] / M["m00"]) / frame.shape[1] * WIDTH)
                            ty = int((M["m01"] / M["m00"]) / frame.shape[0] * HEIGHT)
                            # Smooth movement to reduce jitter.
                            smooth_cursor[0] = int(smooth_cursor[0]*0.65 + tx*0.35)
                            smooth_cursor[1] = int(smooth_cursor[1]*0.65 + ty*0.35)
                            tracked = True
                        else:
                            tracked = False
                    else:
                        tracked = False
                else:
                    tracked = False
            else:
                tracked = False
        else:
            tracked = False

        cursor = smooth_cursor[:]
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                elif event.key == pygame.K_BACKSPACE and started and not game_over:
                    return_last_item()
                elif event.key == pygame.K_SPACE and not started:
                    started = True
                elif event.key == pygame.K_r:
                    # Reset current order/game
                    started, game_over = True, False
                    score, remaining, order_index = 0, 60.0, 0
                    completed_orders = 0
                    current_recipe = random.choice(RECIPES)
                    order_completed_until = 0.0
                    added, held_ingredient = [], None
                    drop_history.clear()
                    selected_ingredient = None
                    available_ingredients = [item["id"] for item in INGREDIENTS]
                    random.shuffle(available_ingredients)
                    randomize_ingredient_positions()
                    stir_total, stirred = 0.0, False
                elif event.key == pygame.K_RETURN and game_over:
                    started, game_over = True, False
                    score, remaining, order_index = 0, 60.0, 0
                    completed_orders = 0
                    current_recipe = random.choice(RECIPES)
                    order_completed_until = 0.0
                    added, held_ingredient = [], None
                    drop_history.clear()
                    selected_ingredient = None
                    available_ingredients = [item["id"] for item in INGREDIENTS]
                    random.shuffle(available_ingredients)
                    randomize_ingredient_positions()
                    stir_total, stirred = 0.0, False
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mx, my = event.pos
                if not started:
                    if 436 <= mx <= 844 and 575 <= my <= 632:
                        started = True
                elif game_over:
                    if 436 <= mx <= 844 and 575 <= my <= 632:
                        started, game_over = True, False
                        score, remaining, order_index = 0, 60.0, 0
                        added, held_ingredient = [], None
                        drop_history.clear()
                        selected_ingredient = None
                        available_ingredients = [item["id"] for item in INGREDIENTS]
                        random.shuffle(available_ingredients)
                        randomize_ingredient_positions()
                        stir_total, stirred = 0.0, False
                else:
                    
                    cursor = [mx, my]
                    for i, (px, py) in enumerate(positions):
                        if i < len(ingredient_order) and math.dist((mx, my), (px, py)) < 38 and selected_ingredient is None:
                            selected_ingredient = ingredient_order[i]
                            break
                    if selected_ingredient and 530 <= mx <= 750 and 390 <= my <= 565:
                        item = selected_ingredient
                        drop_item(item, now)
                        selected_ingredient = None
                    if 550 <= mx <= 730 and 310 <= my <= 355:
                        return_last_item()

        
        if started and not game_over and order_completed_until <= now and tracked:
            cx, cy = cursor
            
            if selected_ingredient is None:
                for i, (px, py) in enumerate(positions):
                    if i < len(ingredient_order) and math.dist((cx, cy), (px, py)) < 33:
                        selected_ingredient = ingredient_order[i]
                        message = "Bawa bahan ke wajan"
                        message_until = now + 1.0
                        break
            if selected_ingredient:
                
                if 525 <= cx <= 755 and 390 <= cy <= 560:
                    item = selected_ingredient
                    drop_item(item, now)
                    selected_ingredient = None
         
            if all(item in added for item in current_recipe["items"]) and not stirred:
                dx, dy = cx-640, cy-475
                radius = math.hypot(dx, dy)
                if 48 < radius < 145:
                    angle = math.atan2(dy, dx)
                    if last_stir_angle is not None:
                        delta = (angle-last_stir_angle+math.pi) % (2*math.pi)-math.pi
                        stir_total += abs(delta)
                    last_stir_angle = angle
                    if stir_total >= math.pi*4:
                        stirred = True
                        score += current_recipe["points"]
                        completed_orders += 1
                        order_completed_until = now + 3.0
                        message = "Masakan selesai!"
                        message_until = order_completed_until

      
        draw_background()
        draw_top_bar(score, remaining, order_index)
        if message_until > now and started and not game_over:
            rounded(screen, (29, 48, 29), (555, 105, 170, 38), 19)
            pygame.draw.rect(screen, (76, 130, 64), (555, 105, 170, 38), 2, border_radius=19)
            draw_text(screen, message, FONT, (197, 235, 194), (640, 124))
        else:
            prompt = (f"Resep: {current_recipe['name']} — ambil bahan yang dibutuhkan"
                      if not all(item in added for item in current_recipe["items"])
                      else ("Putar tangan di atas wajan" if not stirred else "Masakan selesai!"))
            rounded(screen, (29, 48, 29), (500, 105, 280, 38), 19)
            pygame.draw.rect(screen, (76, 130, 64), (500, 105, 280, 38), 2, border_radius=19)
            draw_text(screen, prompt, FONT, (197, 235, 194), (640, 124))

    
        for i, iid in enumerate(ingredient_order):
            if i >= len(positions):
                break
            ing = next(a for a in INGREDIENTS if a["id"] == iid)
            
            selected = (iid in current_recipe["items"] and iid not in added and started and not game_over and order_completed_until <= now)
            wrong = now < wrong_feedback_until and iid not in current_recipe["items"]
            draw_ingredient_icon(ing, positions[i], 28, selected, wrong)

       
        button_rect = (560, 315, 160, 38)
        enabled = len(drop_history) > 0
        draw_button("↶  KEMBALIKAN", button_rect, (35, 43, 48) if enabled else (57, 47, 39), BLUE if enabled else (111, 100, 88))
      

        
        if selected_ingredient and started and not game_over:
            held = next((a for a in INGREDIENTS if a["id"] == selected_ingredient), None)
            if held:
                draw_ingredient_icon(held, cursor, 22, selected=False, wrong=False)

        draw_pan(added)
        draw_avatar(avatar_mood if now < avatar_mood_until else "neutral", now)
        draw_camera_preview(camera_frame, tracked)

       
        if tracked and started and not game_over:
            cx, cy = cursor
            pygame.draw.circle(screen, (65, 122, 47), (cx, cy), 78, 2)
            pygame.draw.circle(screen, GREEN, (cx, cy), 50, 3)
            pygame.draw.arc(screen, (218, 255, 215), (cx-58, cy-58, 116, 116), 0.4, 1.8, 4)
            pygame.draw.circle(screen, (240, 255, 226), (cx, cy), 5)

        if not started:
            draw_intro()
        elif order_completed_until > now and not game_over:
            shade = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            shade.fill((0, 0, 0, 175))
            screen.blit(shade, (0, 0))
            draw_finished_food(current_recipe)
            draw_text(screen, f"Skor: {score}     Pesanan selesai: {completed_orders}", FONT, CREAM, (640, 550))
        elif game_over:
            shade = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            shade.fill((0, 0, 0, 180))
            screen.blit(shade, (0, 0))
            rounded(screen, (42, 22, 15), (390, 215, 500, 290), 24)
            pygame.draw.rect(screen, (147, 101, 53), (390, 215, 500, 290), 2, border_radius=24)
            draw_text(screen, "WAKTU HABIS!", TITLE, (255, 204, 131), (640, 275))
            draw_text(screen, f"Skor akhir: {score}", MED, CREAM, (640, 330))
            draw_text(screen, f"Pesanan selesai: {completed_orders}", FONT, CREAM, (640, 370))
            draw_button("MAIN LAGI", (500, 405, 280, 56), ORANGE, (50, 26, 14))
            draw_text(screen, "Tekan Enter atau klik Main Lagi", SMALL, CREAM, (640, 478))

        pygame.display.flip()

    if cap is not None:
        cap.release()
    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
