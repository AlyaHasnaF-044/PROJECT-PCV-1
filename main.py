import cv2
import numpy as np
import pygame
import math
import time
from collections import deque

# Green Chef: first-person cooking prototype
# Controls:
#   Green glove moving left/right: chop carrots
#   Green glove moving in a circle: mix salad
#   Green glove moving up/down: serve salad
#   ESC: quit
#   C: recalibrate HSV color range (follow console prompts)
#   SPACE: skip current stage (testing only)

WIDTH, HEIGHT = 1100, 720
FPS = 30
CAMERA_INDEX = 0

# Initial HSV range for a vivid green glove. Tune for your lighting/glove.
LOWER_GREEN = np.array([35, 55, 45], dtype=np.uint8)
UPPER_GREEN = np.array([95, 255, 255], dtype=np.uint8)

STAGE_NAMES = ["POTONG WORTEL", "ADUK SALAD", "SAJIKAN"]
STAGE_HINTS = [
    "Gerakkan sarung tangan KIRI <-> KANAN",
    "Gerakkan sarung tangan MEMBENTUK LINGKARAN",
    "Gerakkan sarung tangan NAIK <-> TURUN",
]

def clamp(value, low, high):
    return max(low, min(high, value))

def draw_text(surface, text, font, color, pos, center=False):
    image = font.render(text, True, color)
    rect = image.get_rect()
    if center:
        rect.center = pos
    else:
        rect.topleft = pos
    surface.blit(image, rect)

class GreenTracker:
    def __init__(self, camera_index=0):
        self.cap = cv2.VideoCapture(camera_index)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        self.points = deque(maxlen=24)
        self.last_point = None
        self.last_move_time = 0
        self.chop_count = 0
        self.vertical_count = 0
        self.circle_progress = 0.0
        self.circle_angles = deque(maxlen=30)
        self.last_chop_time = 0
        self.last_vertical_time = 0
        self.stage = 0
        self.last_stage_action = 0
        self.preview = None
        self.found = False

    def read(self):
        ok, frame = self.cap.read()
        if not ok:
            return None, None
        frame = cv2.flip(frame, 1)
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        mask = cv2.inRange(hsv, LOWER_GREEN, UPPER_GREEN)
        kernel = np.ones((5, 5), np.uint8)
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel, iterations=2)

        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        point = None
        if contours:
            contour = max(contours, key=cv2.contourArea)
            area = cv2.contourArea(contour)
            if area > 500:
                moments = cv2.moments(contour)
                if moments["m00"] != 0:
                    cx = int(moments["m10"] / moments["m00"])
                    cy = int(moments["m01"] / moments["m00"])
                    point = (cx, cy)
                    self.found = True
                    cv2.circle(frame, point, 12, (0, 0, 255), 3)
                    cv2.drawContours(frame, [contour], -1, (0, 255, 0), 2)
                else:
                    self.found = False
            else:
                self.found = False
        else:
            self.found = False

        if point:
            self.process_point(point)
        else:
            self.last_point = None

        # Preview is useful for adjusting glove and lighting.
        cv2.putText(frame, "GREEN GLOVE: " + ("DETECTED" if self.found else "NOT FOUND"),
                    (12, 28), cv2.FONT_HERSHEY_SIMPLEX, 0.65,
                    (0, 255, 0) if self.found else (0, 0, 255), 2)
        self.preview = frame
        return point, mask

    def process_point(self, point):
        now = time.time()
        x, y = point
        if self.last_point is not None:
            px, py = self.last_point
            dx, dy = x - px, y - py
            # Ignore tiny jitter; glove should travel a visible distance.
            if self.stage == 0:
                # Count a chop on a strong horizontal direction reversal.
                if abs(dx) > 28 and abs(dx) > abs(dy) * 1.25 and now - self.last_chop_time > 0.28:
                    # Count only if previous movement was in the opposite direction.
                    history = list(self.points)
                    if len(history) >= 2:
                        old_dx = history[-1][0] - history[-2][0]
                        if old_dx * dx < 0:
                            self.chop_count += 1
                            self.last_chop_time = now
            elif self.stage == 1:
                # Circular movement: accumulate angular change around recent point cloud center.
                self.circle_angles.append((x, y))
                if len(self.circle_angles) >= 8:
                    pts = np.array(self.circle_angles, dtype=np.float32)
                    center = pts.mean(axis=0)
                    angles = np.unwrap(np.arctan2(pts[:, 1] - center[1], pts[:, 0] - center[0]))
                    delta = abs(float(angles[-1] - angles[0]))
                    radius = np.mean(np.sqrt(np.sum((pts - center) ** 2, axis=1)))
                    if radius > 12 and delta > math.pi * 1.6:
                        self.circle_progress += 1
                        self.circle_angles.clear()
            elif self.stage == 2:
                # Count vertical strokes with direction reversal.
                if abs(dy) > 28 and abs(dy) > abs(dx) * 1.25 and now - self.last_vertical_time > 0.3:
                    history = list(self.points)
                    if len(history) >= 2:
                        old_dy = history[-1][1] - history[-2][1]
                        if old_dy * dy < 0:
                            self.vertical_count += 1
                            self.last_vertical_time = now

        self.points.append((x, y))
        self.last_point = point

    def set_stage(self, stage):
        self.stage = stage
        self.points.clear()
        self.circle_angles.clear()
        self.last_point = None

    def release(self):
        if self.cap:
            self.cap.release()

def draw_kitchen(screen, font, big_font, stage, progress, score, glove_point=None):
    # Color palette
    cream = (245, 232, 205)
    dark = (54, 44, 38)
    wood = (151, 94, 55)
    wood_light = (190, 131, 77)
    green = (80, 157, 83)
    orange = (239, 135, 46)
    white = (255, 250, 238)
    red = (190, 67, 54)

    screen.fill(cream)
    # Back wall and tiled backsplash
    pygame.draw.rect(screen, (231, 215, 185), (0, 0, WIDTH, 390))
    for x in range(0, WIDTH, 90):
        pygame.draw.line(screen, (218, 198, 166), (x, 0), (x, 390), 2)
    for y in range(0, 390, 65):
        pygame.draw.line(screen, (218, 198, 166), (0, y), (WIDTH, y), 2)

    # Window
    pygame.draw.rect(screen, (105, 165, 191), (60, 55, 235, 170), border_radius=12)
    pygame.draw.rect(screen, (246, 239, 212), (168, 55, 10, 170))
    pygame.draw.rect(screen, (246, 239, 212), (60, 135, 235, 10))
    pygame.draw.rect(screen, (106, 153, 102), (60, 185, 235, 40))

    # Shelf + jars
    pygame.draw.rect(screen, dark, (720, 100, 300, 14), border_radius=5)
    for i, col in enumerate([(220, 178, 107), (202, 99, 70), (110, 155, 94)]):
        pygame.draw.rect(screen, (248, 239, 215), (750 + i*78, 48, 48, 52), border_radius=7)
        pygame.draw.rect(screen, col, (756 + i*78, 66, 36, 28), border_radius=4)
        pygame.draw.rect(screen, dark, (747 + i*78, 42, 54, 8), border_radius=3)

    # Counter in perspective
    pygame.draw.polygon(screen, wood, [(0, 360), (WIDTH, 360), (WIDTH, 720), (0, 720)])
    pygame.draw.polygon(screen, wood_light, [(0, 360), (WIDTH, 360), (WIDTH, 410), (0, 410)])
    for y in range(440, HEIGHT, 60):
        pygame.draw.line(screen, (128, 77, 46), (0, y), (WIDTH, y), 2)

    # Cutting board
    board = pygame.Rect(90, 420, 480, 225)
    pygame.draw.rect(screen, (110, 66, 42), board, border_radius=22)
    pygame.draw.rect(screen, (221, 173, 111), board.inflate(-14, -14), border_radius=18)

    # Carrots and chopped slices
    if stage == 0:
        pygame.draw.line(screen, orange, (155, 520), (430, 565), 30)
        pygame.draw.circle(screen, (250, 176, 74), (155, 520), 15)
        for i in range(min(progress, 8)):
            cx = 205 + i*35
            cy = 500 + i*7
            pygame.draw.ellipse(screen, (247, 143, 49), (cx, cy, 24, 20))
            pygame.draw.ellipse(screen, (255, 194, 95), (cx+5, cy+4, 13, 11))
        draw_text(screen, "WORTEL", font, dark, (235, 610), center=True)
    else:
        # chopped vegetables in a little pile
        for i in range(16):
            cx = 190 + (i % 5) * 45
            cy = 485 + (i // 5) * 35 + (i % 2) * 5
            pygame.draw.ellipse(screen, orange if i % 3 else green, (cx, cy, 28, 20))
        draw_text(screen, "BAHAN SIAP", font, dark, (330, 610), center=True)

    # Bowl/pan on right
    bowl_center = (810, 535)
    pygame.draw.ellipse(screen, (88, 61, 47), (650, 425, 330, 210))
    pygame.draw.ellipse(screen, (218, 224, 220), (665, 430, 300, 180))
    pygame.draw.ellipse(screen, (250, 250, 241), (680, 438, 270, 155))
    if stage >= 1:
        for i in range(18):
            angle = i * 2.399
            cx = int(bowl_center[0] + math.cos(angle) * (35 + (i%4)*16))
            cy = int(bowl_center[1] + math.sin(angle) * (20 + (i%3)*10))
            col = orange if i % 3 else green
            pygame.draw.ellipse(screen, col, (cx, cy, 24, 15))
    else:
        draw_text(screen, "MANGKUK", font, dark, (810, 535), center=True)

    # Plate appears for serving stage
    if stage == 2 or stage >= 3:
        pygame.draw.ellipse(screen, (95, 67, 48), (835, 500, 205, 150))
        pygame.draw.ellipse(screen, white, (845, 492, 190, 145))
        pygame.draw.ellipse(screen, (210, 221, 200), (862, 507, 156, 115))
        for i in range(min(progress, 10)):
            cx = 890 + (i % 4) * 28
            cy = 530 + (i // 4) * 25
            pygame.draw.ellipse(screen, orange if i%2 else green, (cx, cy, 26, 16))

    # HUD panel
    pygame.draw.rect(screen, (48, 43, 39), (20, 18, 550, 112), border_radius=16)
    draw_text(screen, "GREEN CHEF  |  FIRST-PERSON KITCHEN", font, (245, 235, 215), (38, 30))
    draw_text(screen, STAGE_NAMES[min(stage, 2)] if stage < 3 else "RESEP SELESAI",
              big_font, (255, 190, 83), (38, 58))
    if stage < 3:
        draw_text(screen, STAGE_HINTS[stage], font, white, (38, 96))
    draw_text(screen, f"SKOR  {score}", big_font, dark, (WIDTH-200, 28))

    # Progress bar
    pygame.draw.rect(screen, (75, 56, 43), (WIDTH-360, 85, 320, 22), border_radius=10)
    pygame.draw.rect(screen, green, (WIDTH-356, 89, int(312*clamp(progress/8, 0, 1)), 14), border_radius=7)

    # Hand cursor mapped from camera to game view
    if glove_point:
        gx = int(glove_point[0] * WIDTH / 640)
        gy = int(glove_point[1] * HEIGHT / 480)
        pygame.draw.circle(screen, (20, 70, 30), (gx, gy), 25, 5)
        pygame.draw.circle(screen, (65, 220, 90), (gx, gy), 18, 3)
        pygame.draw.circle(screen, (245, 255, 235), (gx, gy), 5)

    if stage >= 3:
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((35, 30, 24, 170))
        screen.blit(overlay, (0, 0))
        draw_text(screen, "SALAD SELESAI!", big_font, (255, 224, 139), (WIDTH//2, HEIGHT//2-35), center=True)
        draw_text(screen, "Kamu berhasil menyajikan salad wortel.", font, white, (WIDTH//2, HEIGHT//2+12), center=True)
        draw_text(screen, "Tekan R untuk bermain lagi  |  ESC untuk keluar", font, white,
                  (WIDTH//2, HEIGHT//2+55), center=True)

def main():
    pygame.init()
    pygame.display.set_caption("Green Chef - OpenCV Cooking Prototype")
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    clock = pygame.time.Clock()
    font = pygame.font.SysFont("arial", 22)
    big_font = pygame.font.SysFont("arial", 30, bold=True)

    tracker = GreenTracker(CAMERA_INDEX)
    stage = 0
    score = 0
    stage_target = [8, 3, 6]
    stage_started = time.time()
    previous_action_count = 0
    running = True
    last_glove_point = None

    if not tracker.cap.isOpened():
        print("ERROR: Webcam tidak dapat dibuka. Coba ubah CAMERA_INDEX menjadi 1.")
        tracker.release()
        pygame.quit()
        return

    print("Green Chef berjalan. Pastikan sarung tangan hijau terlihat jelas oleh webcam.")
    print("Jika deteksi tidak stabil, ubah LOWER_GREEN dan UPPER_GREEN di bagian atas main.py.")

    try:
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        running = False
                    elif event.key == pygame.K_SPACE and stage < 3:
                        # Convenience for testing the visuals without completing gestures.
                        stage += 1
                        tracker.set_stage(stage)
                        stage_started = time.time()
                        previous_action_count = 0
                    elif event.key == pygame.K_r:
                        stage = 0
                        score = 0
                        tracker.chop_count = 0
                        tracker.vertical_count = 0
                        tracker.circle_progress = 0
                        tracker.set_stage(0)
                        stage_started = time.time()
                        previous_action_count = 0

            point, mask = tracker.read()
            if point:
                last_glove_point = point

            if stage == 0:
                current_count = tracker.chop_count
            elif stage == 1:
                current_count = int(tracker.circle_progress)
            elif stage == 2:
                current_count = tracker.vertical_count
            else:
                current_count = 0

            if stage < 3 and current_count >= stage_target[stage]:
                score += 100
                stage += 1
                tracker.set_stage(stage)
                stage_started = time.time()
                previous_action_count = 0

            draw_kitchen(screen, font, big_font, stage,
                         current_count if stage < 3 else 8, score, last_glove_point)
            pygame.display.flip()

            # Camera debug window (press Q in this window to close only the preview).
            if tracker.preview is not None:
                cv2.imshow("Green Glove Tracking - press Q to hide preview", tracker.preview)
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    cv2.destroyWindow("Green Glove Tracking - press Q to hide preview")

            clock.tick(FPS)
    finally:
        tracker.release()
        cv2.destroyAllWindows()
        pygame.quit()

if __name__ == "__main__":
    main()
