import os
import copy
import random
import pygame


CATEGORIES = {
    "fruits":  {"name": "Фрукты",    "items": ["1f34e", "1f34c", "1f347", "1f353", "1f349"]},
    "animals": {"name": "Животные",  "items": ["1f436", "1f431", "1f43c", "1f98a", "1f438"]},
    "sport":   {"name": "Спорт",     "items": ["26bd", "1f3c0", "1f3be", "1f3d0", "1f3c8"]},
    "sweets":  {"name": "Сладости",  "items": ["1f369", "1f36d", "1f36b", "1f9c1", "1f366"]},
    "travel":  {"name": "Транспорт", "items": ["1f697", "1f6b2", "2708", "1f682", "1f680"]},
    "clothes": {"name": "Одежда",    "items": ["1f457", "1f455", "1f9e2", "1f45f", "1f9e3"]},
    "music":   {"name": "Музыка",    "items": ["1f3b8", "1f3b9", "1f941", "1f3ba", "1f3bb"]},
    "weather": {"name": "Погода",    "items": ["2600", "1f308", "26c4", "26a1", "2601"]},
}
STAR_IMAGE = "2b50"

# ---------- Размеры и координаты ----------
WIDTH = 900
HEIGHT = 780
CARD_W = 100
CARD_H = 130
IMG_SIZE = 64

COLUMN_X = [60, 225, 390, 555, 720]   # x для 5 столбцов (и для ячеек)
TOP_Y = 70                              # колода и открытая карта
FOUNDATION_Y = 230                      # ячейки категорий
TABLEAU_Y = 400                         # столбцы
STOCK_X = 720
WASTE_X = 555
DOWN_OFFSET = 20                        # сдвиг для карт рубашкой вверх
UP_OFFSET = 30                          # сдвиг для открытых карт

# ---------- Цвета ----------
BG = (32, 110, 60)
PAPER = (245, 238, 220)
FRAME = (120, 150, 170)
CAT_FRAME = (200, 120, 40)
BACK = (235, 130, 40)
BACK_DARK = (200, 90, 30)
SLOT = (25, 85, 45)
TEXT = (60, 40, 30)
WHITE = (255, 255, 255)
BLUE = (40, 100, 255)
GREEN = (120, 255, 120)

pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Stamp Solitaire")
font = pygame.font.SysFont("Arial", 18, bold=True)
small_font = pygame.font.SysFont("Arial", 15, bold=True)
big_font = pygame.font.SysFont("Arial", 54, bold=True)

new_game_rect = pygame.Rect(60, 15, 130, 38)
undo_rect = pygame.Rect(205, 15, 90, 38)
hint_rect = pygame.Rect(310, 15, 90, 38)


# ---------- Загрузка картинок ----------
IMAGES = {}


def find_images_folder():
    """Ищет папку images рядом с game.py или в папке, откуда запущена игра."""
    here = os.path.dirname(os.path.abspath(__file__))
    for folder in [os.path.join(here, "images"), os.path.join(os.getcwd(), "images")]:
        if os.path.isdir(folder):
            return folder
    print("ВНИМАНИЕ: не нашла папку images. Положи её рядом с файлом:", here)
    return os.path.join(here, "images")


def load_images():
    folder = find_images_folder()
    names = [STAR_IMAGE]
    for cat in CATEGORIES.values():
        names += cat["items"]
    for name in names:
        path = os.path.join(folder, name + ".png")
        try:
            image = pygame.image.load(path).convert_alpha()
            IMAGES[name] = pygame.transform.smoothscale(image, (IMG_SIZE, IMG_SIZE))
        except (pygame.error, FileNotFoundError):
            print("Не нашла картинку:", path)


load_images()


# =====================================================================
#  ЛОГИКА ИГРЫ (здесь нет рисования, только данные и правила)
# =====================================================================

def make_card(kind, cat, img):
    # kind: "item" (картинка) или "category" (карта-категория)
    return {"kind": kind, "cat": cat, "img": img, "face_up": False}


def new_game():
    items = []
    category_cards = []
    for key, cat in CATEGORIES.items():
        category_cards.append(make_card("category", key, STAR_IMAGE))
        for img in cat["items"]:
            items.append(make_card("item", key, img))
    random.shuffle(items)

    # Раздаём столбцы: 2, 3, 4, 5, 6 карт. Последняя карта открыта.
    tableau = []
    for size in [2, 3, 4, 5, 6]:
        column = []
        for _ in range(size):
            column.append(items.pop())
        column[-1]["face_up"] = True
        tableau.append(column)

    # Остальные картинки и все категории идут в колоду
    stock = items + category_cards
    random.shuffle(stock)

    return {
        "tableau": tableau,
        "stock": stock,
        "waste": [],
        # 4 ячейки: какая категория и сколько уже собрано
        "slots": [{"cat": None, "count": 0, "top": None} for _ in range(4)],
        "moves": 0,
        "message": "",
    }


def items_needed(cat):
    return len(CATEGORIES[cat]["items"])


def get_source_cards(state, source):
    """Какие карты мы берём. source = ("waste",) или ("col", номер, индекс_карты)."""
    if source[0] == "waste":
        return state["waste"][-1:]
    _, col, index = source
    return state["tableau"][col][index:]


def can_move(state, source, target):
    """Можно ли переложить source на target.
    target = ("slot", номер) или ("col", номер)."""
    cards = get_source_cards(state, source)
    if not cards:
        return False
    first = cards[0]

    if target[0] == "slot":
        slot = state["slots"][target[1]]
        if first["kind"] == "category":
            return slot["cat"] is None and len(cards) == 1
        return slot["cat"] == first["cat"]

    # target — столбец
    col = target[1]
    if source[0] == "col" and source[1] == col:
        return False
    if first["kind"] == "category":
        return False          # категории только в ячейки
    column = state["tableau"][col]
    if not column:
        return True           # на пустой столбец можно любую картинку
    top = column[-1]
    return top["face_up"] and top["kind"] == "item" and top["cat"] == first["cat"]


def do_move(state, source, target):
    """Перекладывает карты. Перед вызовом проверь can_move."""
    cards = get_source_cards(state, source)

    # Убираем карты с прежнего места
    if source[0] == "waste":
        state["waste"].pop()
    else:
        _, col, index = source
        del state["tableau"][col][index:]
        column = state["tableau"][col]
        if column and not column[-1]["face_up"]:
            column[-1]["face_up"] = True     # открываем следующую карту

    # Кладём на новое место
    if target[0] == "slot":
        slot = state["slots"][target[1]]
        if cards[0]["kind"] == "category":
            slot["cat"] = cards[0]["cat"]
            slot["count"] = 0
            slot["top"] = None
        else:
            slot["count"] += len(cards)
            slot["top"] = cards[-1]["img"]
            if slot["count"] >= items_needed(slot["cat"]):
                state["message"] = "Собрано: " + CATEGORIES[slot["cat"]]["name"] + "!"
                slot["cat"] = None
                slot["count"] = 0
                slot["top"] = None
    else:
        for card in cards:
            card["face_up"] = True
            state["tableau"][target[1]].append(card)

    state["moves"] += 1


def click_stock(state):
    """Открыть карту из колоды или вернуть открытые карты назад."""
    if state["stock"]:
        card = state["stock"].pop()
        card["face_up"] = True
        state["waste"].append(card)
    elif state["waste"]:
        while state["waste"]:
            card = state["waste"].pop()
            card["face_up"] = False
            state["stock"].append(card)
    else:
        return False
    state["moves"] += 1
    return True


def all_sources(state):
    sources = []
    if state["waste"]:
        sources.append(("waste",))
    for col in range(5):
        column = state["tableau"][col]
        for index in range(len(column)):
            if column[index]["face_up"]:
                sources.append(("col", col, index))
                break          # берём всю открытую группу целиком
    return sources


def find_hint(state):
    """Ищет полезный ход. Возвращает (source, target) или None."""
    targets = [("slot", i) for i in range(4)] + [("col", c) for c in range(5)]
    for source in all_sources(state):
        for target in targets:
            if not can_move(state, source, target):
                continue
            # Бесполезно переносить целый столбец на пустое место
            if source[0] == "col" and source[2] == 0 and target[0] == "col":
                continue
            return source, target
    return None


def is_won(state):
    if state["stock"] or state["waste"]:
        return False
    for column in state["tableau"]:
        if column:
            return False
    return True


# =====================================================================
#  РИСОВАНИЕ
# =====================================================================

def column_offsets(column):
    """Y-координата каждой карты в столбце. Длинные столбцы сжимаются."""
    ys = []
    y = TABLEAU_Y
    space = HEIGHT - 20 - CARD_H - TABLEAU_Y
    total = 0
    for card in column[:-1]:
        total += UP_OFFSET if card["face_up"] else DOWN_OFFSET
    scale = 1.0
    if total > space and total > 0:
        scale = space / total
    for card in column:
        ys.append(int(y))
        y += (UP_OFFSET if card["face_up"] else DOWN_OFFSET) * scale
    return ys


def draw_perforation(x, y, w, h):
    """Зубчики по краю, как у почтовой марки."""
    for px in range(x + 6, x + w, 12):
        pygame.draw.circle(screen, BG, (px, y), 3)
        pygame.draw.circle(screen, BG, (px, y + h), 3)
    for py in range(y + 6, y + h, 12):
        pygame.draw.circle(screen, BG, (x, py), 3)
        pygame.draw.circle(screen, BG, (x + w, py), 3)


def draw_back(x, y):
    pygame.draw.rect(screen, BACK, (x, y, CARD_W, CARD_H))
    for i in range(0, CARD_H, 16):
        pygame.draw.rect(screen, BACK_DARK, (x + 8, y + i + 4, CARD_W - 16, 6))
    draw_perforation(x, y, CARD_W, CARD_H)


def draw_image(name, x, y):
    if name in IMAGES:
        screen.blit(IMAGES[name], (x, y))
    else:
        text = small_font.render(name, True, TEXT)
        screen.blit(text, (x, y + 20))


def draw_face(card, x, y, highlight=None):
    if card["kind"] == "category":
        pygame.draw.rect(screen, (255, 215, 90), (x, y, CARD_W, CARD_H))
        pygame.draw.rect(screen, CAT_FRAME, (x + 6, y + 6, CARD_W - 12, CARD_H - 12), 3)
        draw_image(STAR_IMAGE, x + 18, y + 14)
        name = small_font.render(CATEGORIES[card["cat"]]["name"], True, TEXT)
        screen.blit(name, (x + (CARD_W - name.get_width()) // 2, y + 84))
        need = small_font.render("x" + str(items_needed(card["cat"])), True, TEXT)
        screen.blit(need, (x + 70, y + 10))
    else:
        pygame.draw.rect(screen, PAPER, (x, y, CARD_W, CARD_H))
        pygame.draw.rect(screen, FRAME, (x + 6, y + 6, CARD_W - 12, CARD_H - 12), 2)
        draw_image(card["img"], x + 18, y + 30)
    draw_perforation(x, y, CARD_W, CARD_H)
    if highlight:
        pygame.draw.rect(screen, highlight, (x - 4, y - 4, CARD_W + 8, CARD_H + 8), 4)


def draw_slot_outline(x, y, label=""):
    pygame.draw.rect(screen, SLOT, (x, y, CARD_W, CARD_H), border_radius=6)
    if label == "star":
        # Полупрозрачная звезда в пустой ячейке
        if STAR_IMAGE in IMAGES:
            star = IMAGES[STAR_IMAGE].copy()
            star.set_alpha(70)
            screen.blit(star, (x + 18, y + 33))
    elif label:
        text = small_font.render(label, True, (90, 150, 110))
        screen.blit(text, (x + (CARD_W - text.get_width()) // 2, y + 55))


def draw_button(rect, label, color):
    pygame.draw.rect(screen, color, rect, border_radius=8)
    text = font.render(label, True, WHITE)
    screen.blit(text, (rect.x + (rect.w - text.get_width()) // 2, rect.y + 9))


def draw_everything(state, selected, hint):
    screen.fill(BG)

    draw_button(new_game_rect, "New Game", BLUE)
    draw_button(undo_rect, "Undo", (180, 100, 40))
    draw_button(hint_rect, "Hint", (60, 140, 80))
    moves = font.render("Ходы: " + str(state["moves"]), True, WHITE)
    screen.blit(moves, (430, 24))

    hint_source = hint[0] if hint else None
    hint_target = hint[1] if hint else None

    # Колода
    if state["stock"]:
        draw_back(STOCK_X, TOP_Y)
        count = font.render(str(len(state["stock"])), True, WHITE)
        screen.blit(count, (STOCK_X + CARD_W - 30, TOP_Y + 6))
    else:
        draw_slot_outline(STOCK_X, TOP_Y, "↻" if state["waste"] else "")

    # Открытая карта из колоды
    if state["waste"]:
        light = None
        if selected == ("waste",):
            light = BLUE
        elif hint_source == ("waste",):
            light = GREEN
        draw_face(state["waste"][-1], WASTE_X, TOP_Y, light)

    # Ячейки категорий
    for i in range(4):
        x = COLUMN_X[i]
        slot = state["slots"][i]
        light = GREEN if hint_target == ("slot", i) else None
        if slot["cat"] is None:
            draw_slot_outline(x, FOUNDATION_Y, "★")
        else:
            cat = slot["cat"]
            top_card = {"kind": "category", "cat": cat, "img": STAR_IMAGE}
            if slot["top"]:
                top_card = {"kind": "item", "cat": cat, "img": slot["top"]}
            draw_face(top_card, x, FOUNDATION_Y)
            label = CATEGORIES[cat]["name"] + " " + str(slot["count"]) + "/" + str(items_needed(cat))
            text = small_font.render(label, True, WHITE)
            pygame.draw.rect(screen, (170, 70, 40), (x - 5, FOUNDATION_Y - 24, CARD_W + 10, 22), border_radius=5)
            screen.blit(text, (x + (CARD_W - text.get_width()) // 2, FOUNDATION_Y - 22))
        if light:
            pygame.draw.rect(screen, light, (x - 4, FOUNDATION_Y - 4, CARD_W + 8, CARD_H + 8), 4)

    # Столбцы
    for col in range(5):
        x = COLUMN_X[col]
        column = state["tableau"][col]
        if not column:
            draw_slot_outline(x, TABLEAU_Y)
            if hint_target == ("col", col):
                pygame.draw.rect(screen, GREEN, (x - 4, TABLEAU_Y - 4, CARD_W + 8, CARD_H + 8), 4)
        ys = column_offsets(column)
        for index in range(len(column)):
            card = column[index]
            if not card["face_up"]:
                draw_back(x, ys[index])
                continue
            light = None
            if selected and selected[0] == "col" and selected[1] == col and index >= selected[2]:
                light = BLUE
            elif hint_source and hint_source[0] == "col" and hint_source[1] == col and index >= hint_source[2]:
                light = GREEN
            elif hint_target == ("col", col) and index == len(column) - 1:
                light = GREEN
            draw_face(card, x, ys[index], light)

    if state["message"]:
        text = font.render(state["message"], True, (255, 240, 150))
        screen.blit(text, (60, FOUNDATION_Y + CARD_H + 10))

    if is_won(state):
        text = big_font.render("Победа!", True, (255, 240, 150))
        screen.blit(text, ((WIDTH - text.get_width()) // 2, 560))

    pygame.display.flip()


# =====================================================================
#  КЛИКИ МЫШКОЙ: что находится под курсором
# =====================================================================

def what_is_clicked(state, mx, my):
    """Возвращает ("stock",), ("waste",), ("slot", i), ("col", col, index)
    или ("col_empty", col). None — если мимо."""
    if STOCK_X <= mx <= STOCK_X + CARD_W and TOP_Y <= my <= TOP_Y + CARD_H:
        return ("stock",)
    if WASTE_X <= mx <= WASTE_X + CARD_W and TOP_Y <= my <= TOP_Y + CARD_H:
        return ("waste",)
    for i in range(4):
        x = COLUMN_X[i]
        if x <= mx <= x + CARD_W and FOUNDATION_Y <= my <= FOUNDATION_Y + CARD_H:
            return ("slot", i)
    for col in range(5):
        x = COLUMN_X[col]
        if not (x <= mx <= x + CARD_W):
            continue
        column = state["tableau"][col]
        if not column:
            if TABLEAU_Y <= my <= TABLEAU_Y + CARD_H:
                return ("col_empty", col)
            continue
        ys = column_offsets(column)
        # Идём снизу вверх: нижняя карта лежит поверх остальных
        for index in range(len(column) - 1, -1, -1):
            if ys[index] <= my <= ys[index] + CARD_H:
                return ("col", col, index)
    return None


# =====================================================================
#  ГЛАВНЫЙ ЦИКЛ
# =====================================================================

def main():
    state = new_game()
    history = []        # копии прошлых состояний для Undo
    selected = None     # что выбрано: ("waste",) или ("col", col, index)
    hint = None
    clock = pygame.time.Clock()
    running = True

    def save():
        history.append(copy.deepcopy(state))

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            if event.type != pygame.MOUSEBUTTONDOWN:
                continue
            mx, my = event.pos
            hint = None
            state["message"] = ""

            if new_game_rect.collidepoint(mx, my):
                state = new_game()
                history = []
                selected = None
                continue
            if undo_rect.collidepoint(mx, my):
                if history:
                    state = history.pop()
                selected = None
                continue
            if hint_rect.collidepoint(mx, my):
                selected = None
                hint = find_hint(state)
                if hint is None:
                    if state["stock"] or state["waste"]:
                        state["message"] = "Открой карту из колоды"
                    else:
                        state["message"] = "Ходов нет. Попробуй Undo"
                continue

            clicked = what_is_clicked(state, mx, my)
            if clicked is None:
                selected = None
                continue

            if clicked[0] == "stock":
                save()
                if not click_stock(state):
                    history.pop()
                selected = None
                continue

            # Если что-то уже выбрано — пробуем переложить
            if selected is not None:
                target = None
                if clicked[0] == "slot":
                    target = clicked
                elif clicked[0] in ("col", "col_empty"):
                    target = ("col", clicked[1])
                if target and can_move(state, selected, target):
                    save()
                    do_move(state, selected, target)
                    selected = None
                    continue

            # Иначе выбираем карту (если она открыта)
            if clicked[0] == "waste" and state["waste"]:
                selected = None if selected == ("waste",) else ("waste",)
            elif clicked[0] == "col":
                _, col, index = clicked
                if state["tableau"][col][index]["face_up"]:
                    new_sel = ("col", col, index)
                    # Берём всю группу открытых карт, если кликнули выше её начала
                    selected = None if selected == new_sel else new_sel
                else:
                    selected = None
            else:
                selected = None

        draw_everything(state, selected, hint)
        clock.tick(60)

    pygame.quit()


main()