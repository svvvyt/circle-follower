import pygame
import zmq
import time
import math
import random

# Инициализация Pygame
pygame.init()

# Определение цветов
WHITE = (255, 255, 255)
RED = (255, 0, 0)

# Размеры экрана
SCREEN_WIDTH = 600
SCREEN_HEIGHT = 400
CIRCLE_RADIUS = 25

# Создание экрана
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Cowabunga")

# Позиция и скорость красного круга
red_circle_pos = [SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2]
RED_CIRCLE_SPEED = 5

# Количество кругов
NUM_CIRCLES = 6

# Позиции и цвета остальных кругов
circle_positions = [
    [random.randint(0, SCREEN_WIDTH - 2 * CIRCLE_RADIUS), random.randint(0, SCREEN_HEIGHT - 2 * CIRCLE_RADIUS)]
    for _ in range(NUM_CIRCLES)
]
circle_colors = [
    (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))
    for _ in range(NUM_CIRCLES)
]

# Настройка ZeroMQ
context = zmq.Context()
socket_pub = context.socket(zmq.PUB)
socket_pub.bind("tcp://*:5555")
socket_sub = context.socket(zmq.SUB)
socket_sub.connect("tcp://localhost:5555")
socket_sub.setsockopt_string(zmq.SUBSCRIBE, '')

# Параметры скорости
LINEAR_SPEED = 3
SPEED_DECREMENT = 0.9
SPEEDS = [LINEAR_SPEED * (SPEED_DECREMENT ** i) for i in range(NUM_CIRCLES)]

# Функция для вычисления направления движения
def compute_velocity(pos, target, speed):
    dx = target[0] - pos[0]
    dy = target[1] - pos[1]
    distance = math.hypot(dx, dy)
    if distance == 0:
        return 0, 0
    vx = (dx / distance) * speed
    vy = (dy / distance) * speed
    return vx, vy

# Основной игровой цикл
running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    # Получение состояния клавиш
    keys = pygame.key.get_pressed()

    # Обновление позиции красного круга
    if keys[pygame.K_LEFT]:
        red_circle_pos[0] -= RED_CIRCLE_SPEED
    if keys[pygame.K_RIGHT]:
        red_circle_pos[0] += RED_CIRCLE_SPEED
    if keys[pygame.K_UP]:
        red_circle_pos[1] -= RED_CIRCLE_SPEED
    if keys[pygame.K_DOWN]:
        red_circle_pos[1] += RED_CIRCLE_SPEED

    # Ограничение перемещения по границам экрана
    red_circle_pos[0] = max(CIRCLE_RADIUS, min(red_circle_pos[0], SCREEN_WIDTH - CIRCLE_RADIUS))
    red_circle_pos[1] = max(CIRCLE_RADIUS, min(red_circle_pos[1], SCREEN_HEIGHT - CIRCLE_RADIUS))

    # Отправка позиции красного круга через ZeroMQ
    socket_pub.send_string(f"{red_circle_pos[0]} {red_circle_pos[1]}")

    # Получение позиции красного круга через ZeroMQ
    try:
        message = socket_sub.recv_string(flags=zmq.NOBLOCK)
        target_pos = list(map(int, message.split()))
    except zmq.Again:
        target_pos = red_circle_pos

    # Обновление позиций остальных кругов
    previous_pos = target_pos
    for i, pos in enumerate(circle_positions):
        speed = SPEEDS[i]  # Использование соответствующей скорости для каждого круга
        vx, vy = compute_velocity(pos, previous_pos, speed)
        pos[0] += vx
        pos[1] += vy
        # Ограничение перемещения по границам экрана
        pos[0] = max(CIRCLE_RADIUS, min(pos[0], SCREEN_WIDTH - CIRCLE_RADIUS))
        pos[1] = max(CIRCLE_RADIUS, min(pos[1], SCREEN_HEIGHT - CIRCLE_RADIUS))
        previous_pos = pos

    # Очистка экрана
    screen.fill(WHITE)

    # Отрисовка остальных кругов
    for pos, color in zip(circle_positions, circle_colors):
        pygame.draw.circle(screen, color, pos, CIRCLE_RADIUS)

    # Отрисовка красного круга
    pygame.draw.circle(screen, RED, red_circle_pos, CIRCLE_RADIUS)

    # Обновление экрана
    pygame.display.flip()

    # Ограничение кадров
    pygame.time.Clock().tick(30)

# Завершение работы Pygame
pygame.quit()
