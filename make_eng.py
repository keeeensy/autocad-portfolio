"""Две работы уровня рабочей документации: план электрики (ЭОМ) и развёртки кухни/санузла (АИ).

Кухня и санузел описаны один раз (KITCHEN, BATH) в координатах развёртки, и план, и развёртки
строятся из этих данных, поэтому розетки, выводы и мебель на листах совпадают.
Обозначения электрики по ГОСТ 21.210-2014, оформление листа по ГОСТ Р 21.101-2020.
Результат: out/09_kvartira_elektrika.*, out/10_razvertki_kuhnya_sanuzel.*
"""
import math
from collections import Counter

from ezdxf.enums import TextEntityAlignment as A

import make_plans as mp
from make_pro import add_layers, finish

FLAT = mp.PLANS[1]       # двухкомнатная квартира

# ---------------- единая модель кухни и санузла ----------------
# Кухня, развёртка Р1: стена по оси 1 (внутренняя грань x=200), смотрим на запад.
# Координата развёртки u идёт слева направо = вдоль +Y плана, u=0 в углу у стены по оси А (y=200).
K_WALL_X, K_U0 = 200, 200
KITCHEN = {
    "length": 4500,
    "window": (1600, 2800, 900, 2400),                       # u1, u2, низ, верх (окно y=1800...3000)
    "items": [  # (u1, u2, h1, h2, подпись, высота подписи)
        (0, 650, 0, 2000, "Холодильник", 1000),
        (650, 1300, 100, 850, "", 0), (1300, 1900, 100, 850, "ПММ", 475),
        (1900, 2500, 100, 850, "Мойка", 650), (2500, 3200, 100, 850, "", 0),
        (3200, 3800, 100, 850, "Духовой шкаф", 475), (3800, 4400, 100, 850, "", 0),
        (650, 4400, 850, 890, "", 0),                                   # столешница
        (650, 1500, 1500, 2300, "", 0), (2900, 3200, 1500, 2300, "", 0), (3800, 4400, 1500, 2300, "", 0),
        (3200, 3800, 1600, 2300, "Вытяжка", 1950),
    ],
    "tile": [(650, 890, 1600, 1500), (2800, 890, 3200, 1500), (3200, 890, 3800, 1600), (3800, 890, 4400, 1500)],
    # розетки: (u, h, блок, подпись на плане)
    "sockets": [(325, 300, "РОЗЕТКА", ""), (850, 1100, "РОЗЕТКА2", "h=1100"), (1150, 300, "РОЗЕТКА", ""),
                (3300, 300, "РОЗЕТКА", "32А"), (3650, 2200, "РОЗЕТКА", "h=2200"),
                (4100, 1100, "РОЗЕТКА2", "h=1100")],
    # выводы: (код, u, h, диаметр трубы для кружка)   горячая слева, холодная справа
    "outlets": [("Т3", 2125, 500, 0), ("В1", 2275, 500, 0), ("К1 h=400", 2200, 400, 50)],
    "hdims": [325, 850, 1150, 1600, 2200, 2800, 3300, 3650, 4100],
    "vdims": [0, 300, 500, 850, 1100, 1500, 2300, 2700],
    "spots_u": [900, 1300, 3050, 4100],                      # подсветка под верхними шкафами
}
# Санузел, развёртка Р2: стена по оси Б (внутренняя грань y=2460), смотрим на юг.
# u идёт слева направо = вдоль -X плана, u=0 у наружной стены (x=8800).
B_WALL_Y, B_U0 = 2460, 8800
BATH = {
    "length": 3600,
    "items": [(250, 650, 0, 800, "Унитаз", 650), (950, 1550, 780, 850, "Умывальник", 950),
              (1000, 1500, 1150, 1850, "Зеркало", 1500), (1900, 3600, 0, 600, "Ванна 1700х750", 300)],
    "sockets": [(800, 1100, "РОЗЕТКА_IP44", "h=1100")],
    "outlets": [("В1", 150, 200, 0), ("К1", 450, 200, 110), ("Т3", 1175, 600, 0), ("В1", 1325, 600, 0),
                ("К1 h=500", 1250, 500, 50), ("Т3", 2675, 800, 0), ("В1", 2825, 800, 0), ("К1 h=80", 3450, 80, 50)],
    "hdims": [150, 450, 800, 1250, 1900, 2750, 3450],
    "vdims": [0, 200, 600, 800, 1100, 2700],
}
H = 2700


def k_plan(u):          # точка на стене кухни в координатах плана
    return K_WALL_X, K_U0 + u


def b_plan(u):
    return B_U0 - u, B_WALL_Y


# ---------------- условные обозначения (ГОСТ 21.210-2014), мм бумаги ----------------

def symbol_blocks(doc):
    def socket(name, stems, filled):
        b = doc.blocks.new(name)                  # плоская сторона к стене, дуга в помещение
        b.add_arc((0, 0), 1.6, 0, 180); b.add_line((-1.6, 0), (1.6, 0))
        xs = [0] if stems == 1 else [-0.55, 0.55]
        for x in xs:
            b.add_line((x, 1.6 if stems == 1 else 1.5), (x, 2.7))
        b.add_line((xs[0] - 0.7, 2.7), (xs[-1] + 0.7, 2.7))          # защитный контакт
        if filled:
            h = b.add_hatch(color=7); e = h.paths.add_edge_path()
            e.add_arc((0, 0), 1.6, 0, 180); e.add_line((-1.6, 0), (1.6, 0))
    socket("РОЗЕТКА", 1, False); socket("РОЗЕТКА2", 2, False); socket("РОЗЕТКА_IP44", 1, True)
    for name, hooks in (("ВЫКЛ1", 1), ("ВЫКЛ2", 2)):
        b = doc.blocks.new(name)                  # кружок, черта под 45°, флажки по числу клавиш
        b.add_circle((0, 1.2), 1.0); b.add_line((0.7, 1.9), (2.6, 3.8))
        for k in range(hooks):
            t = 2.6 - k * 0.8
            b.add_line((t, t + 1.2), (t + 0.8, t + 0.4))
    b = doc.blocks.new("СВЕТИЛЬНИК"); b.add_circle((0, 0), 2.2)
    b = doc.blocks.new("СВЕТИЛЬНИК_IP44"); b.add_circle((0, 0), 2.2)
    h = b.add_hatch(color=7); h.paths.add_edge_path().add_arc((0, 0), 0.9, 0, 360)
    b = doc.blocks.new("ТОЧЕЧНЫЙ"); b.add_circle((0, 0), 1.0); b.add_line((-1.0, 0), (1.0, 0)); b.add_line((0, -1.0), (0, 1.0))
    b = doc.blocks.new("ЩИТ")
    b.add_lwpolyline([(-3, 0), (3, 0), (3, 2.4), (-3, 2.4)], close=True)
    h = b.add_hatch(color=7); h.paths.add_polyline_path([(-3, 0), (3, 0), (3, 2.4)], is_closed=True)


LEGEND = {
    "РОЗЕТКА": "Розетка штепсельная с защитным контактом",
    "РОЗЕТКА2": "Розетка сдвоенная с защитным контактом",
    "РОЗЕТКА_IP44": "Розетка с защитным контактом и крышкой, IP44",
    "ВЫКЛ1": "Выключатель одноклавишный",
    "ВЫКЛ2": "Выключатель двухклавишный",
    "СВЕТИЛЬНИК": "Светильник потолочный",
    "СВЕТИЛЬНИК_IP44": "Светильник потолочный влагозащищённый, IP44",
    "ТОЧЕЧНЫЙ": "Светильник встраиваемый (подсветка)",
    "ЩИТ": "Щит квартирный ЩК",
}


# ---------------- 9. план расположения электроустановочных изделий ----------------

OTHER_SOCKETS = [  # (блок, x, y, направление в помещение, подпись)
    ("РОЗЕТКА", 1900, 4700, 270, ""),                                          # кухня, у стола
    ("РОЗЕТКА2", 200, 5500, 0, ""), ("РОЗЕТКА", 3200, 5600, 180, ""),           # жилая 1
    ("РОЗЕТКА2", 3000, 8800, 270, "ТВ"), ("РОЗЕТКА", 1600, 4900, 90, ""),
    ("РОЗЕТКА2", 5200, 5600, 0, ""), ("РОЗЕТКА2", 8800, 5500, 180, "h=700"),     # жилая 2
    ("РОЗЕТКА", 8800, 7300, 180, ""), ("РОЗЕТКА", 5600, 8800, 270, ""),
    ("РОЗЕТКА", 3400, 3000, 0, ""), ("РОЗЕТКА", 5000, 5500, 180, ""),           # коридор
    ("РОЗЕТКА_IP44", 7900, 4700, 270, "h=1000 СМ"),                             # санузел, стиральная машина
]
SWITCHES = [  # (блок, x, y, направление, светильники) — со стороны ручки двери
    ("ВЫКЛ2", 3200, 900, 180, [(1700, 2450), "spots"]),
    ("ВЫКЛ1", 3200, 7450, 180, [(1700, 6850)]),
    ("ВЫКЛ2", 5200, 6350, 0, [(7000, 6850)]),
    ("ВЫКЛ1", 5000, 4100, 180, [(7000, 3580)]),
    ("ВЫКЛ1", 5000, 700, 180, [(7000, 1270)]),
    ("ВЫКЛ1", 4820, 200, 90, [(4200, 2500), (4200, 6500)]),
]
LAMPS = [("СВЕТИЛЬНИК", 1700, 2450), ("СВЕТИЛЬНИК", 1700, 6850), ("СВЕТИЛЬНИК", 7000, 6850),
         ("СВЕТИЛЬНИК_IP44", 7000, 3580), ("СВЕТИЛЬНИК", 7000, 1270), ("СВЕТИЛЬНИК", 4200, 2500),
         ("СВЕТИЛЬНИК", 4200, 6500)]


def underlay_furniture(msp):
    P = mp.P
    def r(x1, y1, x2, y2):
        msp.add_lwpolyline([P(x1, y1), P(x2, y1), P(x2, y2), P(x1, y2)], close=True,
                           dxfattribs={"layer": "Мебель", "color": 9})
    for u1, u2, h1, h2, *_ in KITCHEN["items"]:        # кухня по развёртке: низ глубиной 600, холодильник 650
        if h1 < 850 and h2 <= 2000:
            depth = 650 if u1 == 0 else 600
            r(K_WALL_X, K_U0 + u1, K_WALL_X + depth, K_U0 + u2)
    r(1200, 2000, 2400, 3000)                                    # обеденный стол
    for u1, u2, h1, h2, label, _ in BATH["items"]:                # санузел по развёртке
        if label.startswith("Ванна"):
            r(B_U0 - u2, B_WALL_Y, B_U0 - u1, B_WALL_Y + 750)
        elif label in ("Унитаз", "Умывальник"):
            r(B_U0 - u2, B_WALL_Y, B_U0 - u1, B_WALL_Y + (700 if label == "Унитаз" else 450))
    r(8100, 4100, 8700, 4700)                                    # стиральная машина
    r(400, 6300, 2000, 8400)                                     # кровать
    r(5300, 7400, 6000, 8700); r(7700, 5100, 8700, 5900)         # диван, стол


ROOM_LABEL = {3: (2500, 4300)}      # кухня: подпись правее, чтобы не мешать розеткам


def view_marker(msp, x, y, ang, label):
    """Маркер развёртки: стрелка взгляда на стену и её номер (ГОСТ 21.501)."""
    cx, cy = mp.P(x, y)
    dx, dy = math.cos(math.radians(ang)), math.sin(math.radians(ang))
    tip = (cx + dx * 5, cy + dy * 5)
    left = (cx - dy * 1.6, cy + dx * 1.6); right = (cx + dy * 1.6, cy - dx * 1.6)
    h = msp.add_hatch(color=7, dxfattribs={"layer": "Разрез"})
    h.paths.add_polyline_path([tip, left, right], is_closed=True)
    msp.add_circle((cx - dx * 3, cy - dy * 3), 3.2, dxfattribs={"layer": "Разрез"})
    mp.text(msp, label, cx - dx * 3, cy - dy * 3, 2.2, layer="Разрез")


def build_electrics():
    plan = dict(FLAT, file="09_kvartira_elektrika", title="Квартира двухкомнатная",
                sheet="План расположения ЭУИ и светильников")
    mp.SCALE = 75
    mp.SHEET_HEADER = "П-01-2026-ЭОМ"
    mp.WALL_HATCH_COLOR = 9                     # архитектурная подоснова тонкая и светлая
    w, h = plan["axes_x"][-1], plan["axes_y"][-1]
    mp.PLAN_ORIGIN[:] = [70 + (150 - w / 75) / 2, 50 + (200 - h / 75) / 2]
    doc = mp.new_doc(); add_layers(doc); symbol_blocks(doc)
    doc.layers.get("Проемы").color = 8
    doc.layers.add("Электрика", color=1)
    doc.layers.add("Связи", color=1, linetype="DASHED")
    msp = doc.modelspace()
    mp.draw_axes_and_dims(msp, plan)
    mp.draw_walls(msp, plan["walls"], plan["openings"])
    mp.WALL_HATCH_COLOR = 8
    underlay_furniture(msp)
    count = Counter()

    def put(block, x, y, ang, label=""):
        msp.add_blockref(block, mp.P(x, y), dxfattribs={"layer": "Электрика", "rotation": ang - 90})
        count[block] += 1
        if label:
            dx, dy = math.cos(math.radians(ang)), math.sin(math.radians(ang))
            px, py = mp.P(x, y)
            off = 7.0 if abs(dx) > 0.5 else 5.5
            mp.text(msp, label, px + dx * off, py + dy * off + (1.8 if abs(dx) > 0.5 else 0), 1.6, layer="Электрика")

    for u, hgt, block, label in KITCHEN["sockets"]:
        put(block, *k_plan(u), 0, label)
    for u, hgt, block, label in BATH["sockets"]:
        put(block, *b_plan(u), 90, label)
    for block, x, y, ang, label in OTHER_SOCKETS:
        put(block, x, y, ang, label)
    for block, x, y in LAMPS:
        put(block, x, y, 90)
    spots = [(K_WALL_X + 200, K_U0 + u) for u in KITCHEN["spots_u"]]
    for x, y in spots:
        put("ТОЧЕЧНЫЙ", x, y, 90)
    for block, x, y, ang, targets in SWITCHES:
        put(block, x, y, ang)
        sx, sy = mp.P(x, y)
        for tgt in targets:
            tx, ty = spots[-1] if tgt == "spots" else tgt
            ex, ey = mp.P(tx, ty)
            mx, my = (sx + ex) / 2 + (ey - sy) * 0.15, (sy + ey) / 2 - (ex - sx) * 0.15
            pts = [((1 - t) ** 2 * sx + 2 * (1 - t) * t * mx + t * t * ex,
                    (1 - t) ** 2 * sy + 2 * (1 - t) * t * my + t * t * ey) for t in (k / 16 for k in range(17))]
            msp.add_lwpolyline(pts, dxfattribs={"layer": "Связи", "linetype": "DASHED", "ltscale": 0.6})
            if tgt == "spots":
                for a, b in zip(spots, spots[1:]):
                    msp.add_line(mp.P(*a), mp.P(*b), dxfattribs={"layer": "Связи", "linetype": "DASHED", "ltscale": 0.6})
    put("ЩИТ", 3400, 600, 0)                 # глухой участок стены коридора, не в проёме кухни
    view_marker(msp, 1100, 1400, 180, "Р1")
    view_marker(msp, 7700, 3650, 270, "Р2")
    for num, name, x1, y1, x2, y2 in plan["rooms"]:      # номер и наименование помещения
        cx, cy = mp.P(*ROOM_LABEL.get(num, ((x1 + x2) / 2, y2 - 500)))
        msp.add_circle((cx, cy), 2.6, dxfattribs={"layer": "Помещения"})
        mp.text(msp, str(num), cx, cy, 2.5, layer="Помещения")
        mp.text(msp, name, cx, cy - 4.5, 1.8, layer="Помещения")
    # таблица условных обозначений
    ex, ey = 288, 262
    mp.text(msp, "Условные обозначения", ex + 60, ey + 6, 3.5)
    rows = [k for k in LEGEND if count[k]]
    L = lambda a, b, c, d: msp.add_line((a, b), (c, d), dxfattribs={"layer": "Штамп"})
    for k in range(len(rows) + 2):
        L(ex, ey - 8 * k, ex + 120, ey - 8 * k)
    for c in (0, 15, 105, 120):
        L(ex + c, ey, ex + c, ey - 8 * (len(rows) + 1))
    for cx, s in ((7.5, "Обозн."), (60, "Наименование"), (112.5, "Кол.")):
        mp.text(msp, s, ex + cx, ey - 4, 2.5)
    for i, k in enumerate(rows, 1):
        y = ey - 8 * i - 4
        msp.add_blockref(k, (ex + 7.5, y - 1.3), dxfattribs={"layer": "Электрика"})
        mp.text(msp, LEGEND[k], ex + 17, y, 2.2, A.MIDDLE_LEFT)
        mp.text(msp, str(count[k]), ex + 112.5, y, 2.5)
    notes = ["1. Обозначения по ГОСТ 21.210-2014. ЭУИ скрытой установки.",
             "2. Высота установки от чистого пола до центра изделия: розетки 300,",
             "    выключатели 900, ЩК 1700 мм. Иные высоты указаны на плане.",
             "3. В санузле изделия IP44, вне зон 0, 1, 2 (0,6 м от ванны),",
             "    группы через УЗО 30 мА.",
             "4. Розетка 32А для варочной панели и духового шкафа: отдельная линия.",
             "5. Кабель ВВГнг(А)-LS: розетки 3х2,5, освещение 3х1,5, плита 3х6.",
             "6. Связь выключателей со светильниками показана условно.",
             "7. Развёртки Р1, Р2 см. лист 10."]
    ny = ey - 8 * (len(rows) + 1) - 9
    mp.text(msp, "Примечания", ex, ny, 3.0, A.MIDDLE_LEFT)
    for i, s in enumerate(notes):
        mp.text(msp, s, ex, ny - 6 - 4.6 * i, 2.1, A.MIDDLE_LEFT)
    mp.draw_sheet(msp, plan, [], 9)
    mp.text(msp, "План расположения электроустановочных изделий и светильников  М 1:75",
            mp.PLAN_ORIGIN[0] + w / 75 / 2, mp.PLAN_ORIGIN[1] + h / 75 + 24, 4.0)
    finish(doc, plan["file"])


# ---------------- 10. развёртки ----------------

def build_elevations():
    mp.SCALE = 25
    mp.SHEET_HEADER = "П-01-2026-АИ"
    doc = mp.new_doc(); add_layers(doc); symbol_blocks(doc)
    doc.layers.add("Плитка", color=9); doc.layers.add("Выводы", color=5); doc.layers.add("Электрика", color=1)
    msp = doc.modelspace()

    def elevation(ox, oy, data, title, window=None, tile=None):
        length = data["length"]
        E = lambda u, z: (ox + u / 25, oy + z / 25)
        def rect(u1, z1, u2, z2, layer="Контур", **kw):
            msp.add_lwpolyline([E(u1, z1), E(u2, z1), E(u2, z2), E(u1, z2)], close=True,
                               dxfattribs={"layer": layer, **kw})
        rect(0, 0, length, H, lineweight=50)
        msp.add_line(E(-250, 0), E(length + 250, 0), dxfattribs={"layer": "Контур", "lineweight": 70})
        # плитка: стена целиком (санузел) или зоны фартука, с вырезами под сантехнику
        hatch = msp.add_hatch(color=9, dxfattribs={"layer": "Плитка"})
        hatch.set_pattern_fill("NET", scale=2.3)
        zones = tile or [(0, 0, length, H)]
        for u1, z1, u2, z2 in zones:
            hatch.paths.add_polyline_path([E(u1, z1), E(u2, z1), E(u2, z2), E(u1, z2)], is_closed=True, flags=1)
        if not tile:
            for u1, u2, z1, z2, label, _ in data["items"]:
                hatch.paths.add_polyline_path([E(u1, z1), E(u2, z1), E(u2, z2), E(u1, z2)], is_closed=True, flags=16)
        if window:
            u1, u2, z1, z2 = window
            rect(u1, z1, u2, z2, lineweight=35)
            rect(u1 + 60, z1 + 60, u2 - 60, z2 - 60)
            msp.add_line(E((u1 + u2) / 2, z1 + 60), E((u1 + u2) / 2, z2 - 60), dxfattribs={"layer": "Контур"})
            rect(u1 - 50, z1 - 40, u2 + 50, z1, lineweight=35)                       # подоконник
            mp.text(msp, "Окно", *E((u1 + u2) / 2 - 300, z1 + 900), 2.0)
            msp.add_linear_dim(base=(E(u2, 0)[0] + 4, 0), p1=E(u2, z1), p2=E(u2, z2), angle=90, dimstyle="ГОСТ",
                               dxfattribs={"layer": "Размеры"}).render()
        for u1, u2, z1, z2, label, lz in data["items"]:
            rect(u1, z1, u2, z2, "Мебель", color=7, lineweight=35)
            if label:
                mp.text(msp, label, *E((u1 + u2) / 2, lz), 1.9)
        for code, u, z, d in data["outlets"]:
            cx, cy = E(u, z)
            msp.add_circle((cx, cy), max(d / 25 / 2, 0.9), dxfattribs={"layer": "Выводы"})
            mp.text(msp, code, cx, cy + 2.6, 1.7, A.MIDDLE_CENTER, "Выводы")
        for u, z, block, _ in data["sockets"]:
            n = 2 if block == "РОЗЕТКА2" else 1
            wdt = 80 if n == 1 else 150
            rect(u - wdt / 2, z - 40, u + wdt / 2, z + 40, "Электрика", color=1)
            for k in range(n):
                msp.add_circle(E(u - (n - 1) * 35 + k * 70, z), 0.9, dxfattribs={"layer": "Электрика", "color": 1})
            if block == "РОЗЕТКА_IP44":
                mp.text(msp, "IP44", *E(u, z + 120), 1.6, layer="Электрика")
        # высоты справа, привязки снизу
        bx = E(length, 0)[0] + 6
        for a, b in zip(data["vdims"], data["vdims"][1:]):
            msp.add_linear_dim(base=(bx, 0), p1=E(length, a), p2=E(length, b), angle=90, dimstyle="ГОСТ",
                               dxfattribs={"layer": "Размеры"}).render()
        msp.add_linear_dim(base=(bx + 7, 0), p1=E(length, 0), p2=E(length, H), angle=90, dimstyle="ГОСТ",
                           dxfattribs={"layer": "Размеры"}).render()
        xs = sorted({0, length, *data["hdims"]})
        for a, b in zip(xs, xs[1:]):
            msp.add_linear_dim(base=(0, oy - 6), p1=E(a, 0), p2=E(b, 0), angle=0, dimstyle="ГОСТ",
                               dxfattribs={"layer": "Размеры"}).render()
        msp.add_linear_dim(base=(0, oy - 13), p1=E(0, 0), p2=E(length, 0), angle=0, dimstyle="ГОСТ",
                           dxfattribs={"layer": "Размеры"}).render()
        # отметки уровня пола и потолка слева (ГОСТ 21.101)
        for z, lbl in ((0, "±0,000"), (H, "+2,700")):
            x0, y0 = E(0, z)
            msp.add_line((x0 - 16, y0), (x0, y0), dxfattribs={"layer": "Отметки"})
            msp.add_lwpolyline([(x0 - 11.5, y0 + 2.2), (x0 - 9.5, y0), (x0 - 7.5, y0 + 2.2)], close=True,
                               dxfattribs={"layer": "Отметки"})
            mp.text(msp, lbl, x0 - 9.5, y0 + 4.2, 2.2, layer="Отметки")
        mp.text(msp, title, *E(length / 2, H + 250), 3.5)

    elevation(45, 164, KITCHEN, "Развёртка Р1. Кухня (пом. 3), стена по оси 1   М 1:25",
              window=KITCHEN["window"], tile=KITCHEN["tile"])
    elevation(45, 22, BATH, "Развёртка Р2. Санузел (пом. 5), стена по оси Б   М 1:25")
    # обозначения и примечания справа от развёрток
    lx, ly = 250, 270
    mp.text(msp, "Обозначения", lx, ly, 3.2, A.MIDDLE_LEFT)
    legend = [("Т3", "Водопровод горячей воды, Ø15 (подвод слева)"),
              ("В1", "Водопровод холодной воды, Ø15 (подвод справа)"),
              ("К1", "Канализация бытовая: Ø50, унитаз Ø110"),
              ("IP44", "Розетка с крышкой, вне зон 0-2, через УЗО 30 мА")]
    for i, (code, s) in enumerate(legend):
        mp.text(msp, code, lx, ly - 7 - 5.5 * i, 2.5, A.MIDDLE_LEFT)
        mp.text(msp, s, lx + 11, ly - 7 - 5.5 * i, 2.2, A.MIDDLE_LEFT)
    notes = ["1. Высоты выводов от чистого пола до оси трубы,",
             "    розеток до центра изделия.",
             "2. Привязки по горизонтали от левого угла развёртки.",
             "3. Межосевое расстояние выводов Т3/В1 150 мм.",
             "4. ПММ подключить к выводам мойки через тройник",
             "    и к сифону мойки.",
             "5. Фартук кухни: керамогранит 600х300, h=890...1500.",
             "6. Санузел: плитка 300х300 на всю высоту.",
             "7. Розетки и выключатели см. лист 9 (ЭОМ)."]
    mp.text(msp, "Примечания", lx, ly - 36, 3.2, A.MIDDLE_LEFT)
    for i, s in enumerate(notes):
        mp.text(msp, s, lx, ly - 43 - 4.8 * i, 2.2, A.MIDDLE_LEFT)
    plan = {"title": "Квартира двухкомнатная", "sheet": "Развёртки Р1, Р2", "axes_x": [0], "axes_y": [0]}
    mp.draw_sheet(msp, plan, [], 10)
    finish(doc, "10_razvertki_kuhnya_sanuzel")


if __name__ == "__main__":
    import sys
    todo = sys.argv[1:] or ["el", "razv"]
    if "el" in todo:
        build_electrics()
    if "razv" in todo:
        build_elevations()
