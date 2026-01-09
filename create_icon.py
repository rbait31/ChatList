from PIL import Image, ImageDraw

def draw_icon(size):
    """Рисует белого орла на красном фоне."""
    # Создаем RGB изображение с красным фоном
    img = Image.new("RGB", (size, size), (220, 20, 60))  # Crimson - красный фон
    draw = ImageDraw.Draw(img)
    
    # Белый цвет для орла
    white_color = (255, 255, 255)
    
    center_x = size // 2
    center_y = size // 2
    
    # Масштабируем размеры в зависимости от размера иконки
    scale = size / 256.0
    
    # Тело орла (овал, вертикальный)
    body_width = int(60 * scale)
    body_height = int(100 * scale)
    body_x = center_x - body_width // 2
    body_y = center_y - body_height // 2 + int(10 * scale)
    draw.ellipse(
        [body_x, body_y, body_x + body_width, body_y + body_height],
        fill=white_color
    )
    
    # Голова орла (круг)
    head_radius = int(35 * scale)
    head_center_x = center_x
    head_center_y = center_y - int(50 * scale)
    draw.ellipse(
        [
            head_center_x - head_radius,
            head_center_y - head_radius,
            head_center_x + head_radius,
            head_center_y + head_radius
        ],
        fill=white_color
    )
    
    # Клюв (треугольник)
    beak_size = int(15 * scale)
    beak_points = [
        (head_center_x - beak_size // 2, head_center_y - int(10 * scale)),
        (head_center_x + beak_size // 2, head_center_y - int(10 * scale)),
        (head_center_x, head_center_y + int(5 * scale))
    ]
    draw.polygon(beak_points, fill=white_color)
    
    # Левое крыло (эллипс, повернутый)
    wing_width = int(80 * scale)
    wing_height = int(50 * scale)
    wing_x = center_x - int(70 * scale)
    wing_y = center_y - int(20 * scale)
    draw.ellipse(
        [wing_x, wing_y, wing_x + wing_width, wing_y + wing_height],
        fill=white_color
    )
    
    # Правое крыло (эллипс, повернутый)
    wing_x2 = center_x + int(70 * scale) - wing_width
    draw.ellipse(
        [wing_x2, wing_y, wing_x2 + wing_width, wing_y + wing_height],
        fill=white_color
    )
    
    # Хвост (треугольник/трапеция)
    tail_width_top = int(40 * scale)
    tail_width_bottom = int(20 * scale)
    tail_height = int(50 * scale)
    tail_y = center_y + int(40 * scale)
    tail_points = [
        (center_x - tail_width_top // 2, tail_y),
        (center_x + tail_width_top // 2, tail_y),
        (center_x + tail_width_bottom // 2, tail_y + tail_height),
        (center_x - tail_width_bottom // 2, tail_y + tail_height)
    ]
    draw.polygon(tail_points, fill=white_color)
    
    # Левый глаз (маленький черный кружок)
    eye_size = int(8 * scale)
    eye_y = head_center_y - int(5 * scale)
    eye_x_left = head_center_x - int(12 * scale)
    draw.ellipse(
        [
            eye_x_left - eye_size // 2,
            eye_y - eye_size // 2,
            eye_x_left + eye_size // 2,
            eye_y + eye_size // 2
        ],
        fill=(0, 0, 0)  # Черный
    )
    
    # Правый глаз
    eye_x_right = head_center_x + int(12 * scale)
    draw.ellipse(
        [
            eye_x_right - eye_size // 2,
            eye_y - eye_size // 2,
            eye_x_right + eye_size // 2,
            eye_y + eye_size // 2
        ],
        fill=(0, 0, 0)  # Черный
    )
    
    return img

# Размеры иконки
sizes = [(256, 256), (128, 128), (64, 64), (48, 48), (32, 32), (16, 16)]
icons = [draw_icon(s) for s, _ in sizes]

# Изображения уже в RGB режиме, просто убеждаемся
rgb_icons = []
for icon in icons:
    # Убеждаемся, что изображение в RGB режиме (не палитра)
    if icon.mode != "RGB":
        rgb_img = icon.convert("RGB")
    else:
        rgb_img = icon
    rgb_icons.append(rgb_img)

# Сохранение с явным указанием формата и цветов
# ВАЖНО: Изображения уже в RGB режиме с красным фоном, что гарантирует
# сохранение цветов и избегает автоматической конвертации в градации серого
try:
    rgb_icons[0].save(
        "app.ico",
        format="ICO",
        sizes=sizes,
        append_images=rgb_icons[1:]
    )
    print("✅ Иконка 'app.ico' создана!")
    print("   Дизайн: белый орел на красном фоне")
    print("   Цвета: красный фон (Crimson), белый орел")
except Exception as e:
    print(f"❌ Ошибка при сохранении: {e}")
    # Альтернативный способ - сохранить каждое изображение отдельно
    print("Попытка альтернативного метода сохранения...")
    rgb_icons[0].save("app.ico", format="ICO")
    print("✅ Иконка 'app.ico' создана (только один размер)")