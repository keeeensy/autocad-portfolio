"""Три «серьёзные» работы для портфолио: план с мебелью, фасад, чертёж детали.

Использует оформление листа из make_plans.py. Результат: out/06..08 *.dxf и *.png
"""
import math

import ezdxf
from ezdxf.enums import TextEntityAlignment as A
from ezdxf.addons.drawing import matplotlib as dm

import make_plans as mp

HOUSE = mp.PLANS[2]          # жилой дом, план 1 этажа


def P(x, y):
    return mp.P(x, y)


def rect(msp, x1, y1, x2, y2, layer, **kw):
    msp.add_lwpolyline([P(x1, y1), P(x2, y1), P(x2, y2), P(x1, y2)], close=True,
                       dxfattribs={"layer": layer, **kw})


def line(msp, x1, y1, x2, y2, layer, **kw):
    msp.add_line(P(x1, y1), P(x2, y2), dxfattribs={"layer": layer, **kw})


def circle(msp, x, y, r, layer):
    msp.add_circle(P(x, y), r / mp.SCALE, dxfattribs={"layer": layer})


def add_layers(doc):
    for name, color in [("Мебель", 6), ("Сантехника", 4), ("Лестница", 7), ("Отметки", 7),
                        ("Разрез", 7), ("Штриховка", 8), ("Контур", 7), ("Тонкие", 7)]:
        if name not in doc.layers:
            doc.layers.add(name, color=color)


# ---------- 1. план с мебелью ----------

def furniture(msp):
    m, s = "Мебель", "Сантехника"
    # спальня (0..6000 x 4800..9000)
    rect(msp, 3200, 6800, 5200, 8800, m); rect(msp, 3300, 8300, 5100, 8750, m)        # кровать + подушки
    rect(msp, 2700, 8300, 3150, 8750, m); rect(msp, 5250, 8300, 5700, 8750, m)        # тумбы
    rect(msp, 200, 5000, 800, 7200, m); line(msp, 500, 5000, 500, 7200, m)            # шкаф
    rect(msp, 1200, 5000, 2700, 5600, m)                                               # стол
    # кухня-гостиная (6000..10200 x 0..9000)
    rect(msp, 9600, 300, 10000, 4200, m)                                               # кухонный гарнитур
    circle(msp, 9800, 1400, 160, s); circle(msp, 9800, 1400, 60, s)                    # мойка
    for cy in (2800, 3300):
        for cx in (9700, 9900):
            circle(msp, cx, cy, 80, m)                                                 # плита
    rect(msp, 7000, 1500, 8400, 2500, m)                                               # обеденный стол
    for cx in (7350, 8050):
        rect(msp, cx - 200, 1050, cx + 200, 1400, m); rect(msp, cx - 200, 2600, cx + 200, 2950, m)
    rect(msp, 6400, 6600, 7200, 8700, m); rect(msp, 7200, 8000, 9400, 8700, m)         # угловой диван
    rect(msp, 7600, 6400, 8800, 7200, m)                                               # журнальный стол
    rect(msp, 9700, 5800, 10000, 7600, m)                                              # ТВ-тумба
    # санузел (0..2400 x 2400..4800)
    rect(msp, 200, 2600, 900, 3300, s)                                                 # душ
    line(msp, 200, 2600, 900, 3300, s); line(msp, 200, 3300, 900, 2600, s)
    msp.add_ellipse(P(1650, 3000), major_axis=(0, 280 / mp.SCALE), ratio=0.65,
                    dxfattribs={"layer": s})                                           # унитаз
    rect(msp, 1450, 2600, 1850, 2720, s)
    rect(msp, 1700, 4100, 2200, 4600, s); circle(msp, 1950, 4350, 120, s)              # раковина
    # котельная (0..2400 x 0..2400)
    circle(msp, 600, 1800, 350, s); text(msp, "Котёл", 600, 1800, 1.8)
    rect(msp, 1500, 300, 2100, 900, s); text(msp, "Бойлер", 1800, 600, 1.6)


def text(msp, s, x, y, h=2.5, align=A.MIDDLE_CENTER, layer="Надписи"):
    mp.text(msp, s, *P(x, y), h, align, layer)


def stairs(msp):
    # холл 2400..6000 x 2400..4800 — марш вдоль стены оси 3
    x1, x2, y1, y2 = 4900, 5900, 2500, 4700
    rect(msp, x1, y1, x2, y2, "Лестница")
    n = 9
    for k in range(1, n):
        y = y1 + (y2 - y1) * k / n
        line(msp, x1, y, x2, y, "Лестница")
    xm = (x1 + x2) / 2
    line(msp, xm, y1 + 150, xm, y2 - 300, "Лестница")
    msp.add_lwpolyline([P(xm - 120, y2 - 500), P(xm, y2 - 250), P(xm + 120, y2 - 500)],
                       dxfattribs={"layer": "Лестница"})
    text(msp, "вверх", x1 - 450, y1 + 1100, 1.8)


def level_mark(msp, x, y, label):
    """Отметка уровня на плане: прямоугольник с текстом."""
    text(msp, label, x, y, 2.2, layer="Отметки")
    w = 850
    rect(msp, x - w, y - 180, x + w, y + 180, "Отметки")


def section_line(msp, y, x_from, x_to, name="1"):
    for x, d in ((x_from, -1), (x_to, 1)):
        msp.add_lwpolyline([P(x, y), P(x + d * 700, y)], dxfattribs={"layer": "Разрез", "const_width": 0.7})
        msp.add_lwpolyline([P(x + d * 350, y), P(x + d * 350, y + 700)], dxfattribs={"layer": "Разрез"})
        msp.add_lwpolyline([P(x + d * 350 - 150, y + 450), P(x + d * 350, y + 700), P(x + d * 350 + 150, y + 450)],
                           dxfattribs={"layer": "Разрез"})
        text(msp, name, x + d * 350 + d * 350, y + 550, 3.5, layer="Разрез")


def axes_three_chains(msp, plan, wall_x=0, wall_y=3):
    """Оси и три цепочки размеров снизу и слева: проёмы, оси, габарит."""
    xs, ys, S = plan["axes_x"], plan["axes_y"], mp.SCALE
    ext = 24 * S
    for i, x in enumerate(xs):
        msp.add_line(P(x, -ext), P(x, ys[-1] + 9 * S), dxfattribs={"layer": "Оси"})
        bx, by = P(x, -ext)
        msp.add_circle((bx, by - 4), 4, dxfattribs={"layer": "Оси", "color": 7, "linetype": "Continuous"})
        mp.text(msp, mp.AXIS_X_LABELS[i], bx, by - 4, 3.5)
    for i, y in enumerate(ys):
        msp.add_line(P(-ext, y), P(xs[-1] + 9 * S, y), dxfattribs={"layer": "Оси"})
        bx, by = P(-ext, y)
        msp.add_circle((bx - 4, by), 4, dxfattribs={"layer": "Оси", "color": 7, "linetype": "Continuous"})
        mp.text(msp, mp.AXIS_Y_LABELS[i], bx - 4, by, 3.5)

    def dim(p1, p2, base, ang):
        msp.add_linear_dim(base=base, p1=p1, p2=p2, angle=ang, dimstyle="ГОСТ",
                           dxfattribs={"layer": "Размеры"}).render()

    def chain(points, fixed, horizontal, level):
        for a, b in zip(points, points[1:]):
            if horizontal:
                dim(P(a, fixed), P(b, fixed), (0, P(0, -level * S)[1]), 0)
            else:
                dim(P(fixed, a), P(fixed, b), (P(-level * S, 0)[0], 0), 90)

    def opening_points(wi, total, coord):
        x1, y1, x2, y2, t = plan["walls"][wi]
        pts = {0 - 200, total + 200}
        for w, c, width, *_ in plan["openings"]:
            if w == wi:
                pos = (x1 + (c if x2 > x1 else -c)) if coord == "x" else (y1 + (c if y2 > y1 else -c))
                pts |= {pos - width / 2, pos + width / 2}
        return sorted(pts)

    if len(pts := opening_points(wall_x, xs[-1], "x")) > 2:
        chain(pts, -200, True, 7)
    chain(xs, 0, True, 13)
    chain([xs[0] - 200, xs[-1] + 200], -200, True, 19)
    if len(pts := opening_points(wall_y, ys[-1], "y")) > 2:
        chain(pts, -200, False, 7)
    chain(ys, 0, False, 13)
    chain([ys[0] - 200, ys[-1] + 200], -200, False, 19)


def outer_wall_hatch(msp, plan):
    """Штриховка кирпичной кладки поверх наружных стен (ANSI31)."""
    w, h, t = plan["axes_x"][-1], plan["axes_y"][-1], 400
    hatch = msp.add_hatch(color=7, dxfattribs={"layer": "Штриховка"})
    hatch.set_pattern_fill("ANSI31", scale=0.35)
    hatch.paths.add_polyline_path([P(-t / 2, -t / 2), P(w + t / 2, -t / 2), P(w + t / 2, h + t / 2), P(-t / 2, h + t / 2)],
                                  is_closed=True, flags=1)
    hatch.paths.add_polyline_path([P(t / 2, t / 2), P(w - t / 2, t / 2), P(w - t / 2, h - t / 2), P(t / 2, h - t / 2)],
                                  is_closed=True, flags=16)


def build_plan_pro():
    plan = dict(HOUSE, file="06_dom_plan_mebel", title="Жилой дом. План 1 этажа с мебелью",
                sheet="План 1 этажа")
    mp.SCALE = 75
    w, h = plan["axes_x"][-1], plan["axes_y"][-1]
    mp.PLAN_ORIGIN[:] = [75 + (145 - w / 75) / 2, 52 + (200 - h / 75) / 2]
    doc = mp.new_doc(); add_layers(doc)
    msp = doc.modelspace()
    axes_three_chains(msp, plan)
    mp.BRICK_HATCH = True
    mp.draw_walls(msp, plan["walls"], plan["openings"])
    mp.BRICK_HATCH = False
    rows = mp.draw_rooms(msp, plan)
    furniture(msp); stairs(msp)
    level_mark(msp, 8100, 5500, "±0,000")
    section_line(msp, 3600, -1400, 11600)
    mp.draw_sheet(msp, plan, rows, 6)
    finish(doc, plan["file"])


def furniture_1k(msp):
    m, s = "Мебель", "Сантехника"
    # жилая комната 0..6600 x 2700..7500
    rect(msp, 300, 5300, 2300, 7300, m); rect(msp, 400, 6850, 2200, 7250, m)          # кровать
    rect(msp, 2400, 6800, 2850, 7250, m)                                               # тумба
    rect(msp, 6000, 3000, 6400, 5400, m); line(msp, 6200, 3000, 6200, 5400, m)         # шкаф-купе
    rect(msp, 3500, 6700, 5900, 7300, m); rect(msp, 3500, 6100, 3900, 6700, m)         # диван
    rect(msp, 4300, 5500, 5300, 6100, m)                                               # журнальный столик
    rect(msp, 300, 3000, 1700, 3600, m); rect(msp, 800, 3700, 1200, 4100, m)           # стол + стул
    # кухня 3600..6600 x 0..2700
    rect(msp, 6000, 200, 6400, 2500, m)                                                # гарнитур
    circle(msp, 6200, 800, 150, s); circle(msp, 6200, 800, 55, s)                      # мойка
    for cy in (1700, 2100):
        for cx in (6100, 6300):
            circle(msp, cx, cy, 75, m)                                                 # плита
    rect(msp, 4300, 900, 5200, 1700, m)                                                # стол
    rect(msp, 4550, 500, 4950, 850, m); rect(msp, 4550, 1750, 4950, 2100, m)           # стулья
    # коридор 1800..3600 x 0..2700
    rect(msp, 3100, 1000, 3500, 2500, m); line(msp, 3300, 1000, 3300, 2500, m)           # шкаф
    # санузел 0..1800 x 0..2700
    rect(msp, 200, 200, 900, 1900, s)                                                  # ванна
    msp.add_ellipse(P(550, 1050), major_axis=(0, 700 / mp.SCALE), ratio=0.4, dxfattribs={"layer": s})
    msp.add_ellipse(P(1350, 2250), major_axis=(0, 280 / mp.SCALE), ratio=0.65, dxfattribs={"layer": s})  # унитаз
    rect(msp, 1150, 2450, 1550, 2550, s)
    rect(msp, 1100, 200, 1650, 650, s); circle(msp, 1375, 425, 120, s)                 # раковина
    circle(msp, 1450, 1200, 250, s); text(msp, "СМ", 1450, 1200, 1.8)                  # стиральная машина


def furniture_banya(msp):
    m, s = "Мебель", "Сантехника"
    # парная 0..2400 x 1800..4800: полки в два яруса и печь-каменка
    rect(msp, 100, 4100, 2300, 4700, m); rect(msp, 100, 3500, 2300, 4100, m)
    for x in range(400, 2300, 300):
        line(msp, x, 3500, x, 4700, m)
    rect(msp, 1500, 1950, 2250, 2700, s); line(msp, 1500, 1950, 2250, 2700, s); line(msp, 1500, 2700, 2250, 1950, s)
    text(msp, "Печь", 1875, 2850, 1.8)
    # моечная 0..2400 x 0..1800
    rect(msp, 100, 100, 900, 900, s); line(msp, 100, 100, 900, 900, s); line(msp, 100, 900, 900, 100, s)  # душ
    rect(msp, 1300, 100, 2300, 500, m)                                                  # лавка
    # комната отдыха 2400..6000 x 0..4800
    rect(msp, 3400, 2000, 5000, 2900, m)                                                # стол
    rect(msp, 3400, 1500, 5000, 1850, m); rect(msp, 3400, 3050, 5000, 3400, m)          # лавки
    rect(msp, 5300, 300, 5900, 2300, m)                                                 # диван
    rect(msp, 2600, 4200, 3800, 4700, m)                                                # шкаф


def build_furnished(idx, file, title, furn, scale, level_xy, section_y=None, stairs_on=False):
    plan = dict(mp.PLANS[idx], file=file, title=title)
    mp.SCALE = scale
    w, h = plan["axes_x"][-1], plan["axes_y"][-1]
    mp.PLAN_ORIGIN[:] = [75 + (145 - w / scale) / 2, 52 + (200 - h / scale) / 2]
    doc = mp.new_doc(); add_layers(doc)
    msp = doc.modelspace()
    axes_three_chains(msp, plan)
    mp.BRICK_HATCH = True
    mp.draw_walls(msp, plan["walls"], plan["openings"])
    mp.BRICK_HATCH = False
    rows = mp.draw_rooms(msp, plan)
    furn(msp)
    if stairs_on:
        stairs(msp)
    level_mark(msp, *level_xy, "±0,000")
    if section_y is not None:
        section_line(msp, section_y, -1400, w + 1400)
    mp.draw_sheet(msp, plan, rows, idx + 1)
    finish(doc, file)


# ---------- 2. фасад ----------

def build_facade():
    mp.SCALE = 75
    W, t = 10200, 400
    L0, L1, L2, ridge = 0, 3000, 6000, 8600
    mp.PLAN_ORIGIN[:] = [75 + (145 - W / 75) / 2, 75]
    doc = mp.new_doc(); add_layers(doc)
    msp = doc.modelspace()
    xl, xr = -t / 2, W + t / 2
    # земля
    line(msp, -1500, -600, W + 1500, -600, "Контур", lineweight=70)
    g = msp.add_hatch(color=8, dxfattribs={"layer": "Штриховка"})
    g.set_pattern_fill("EARTH", scale=0.15)
    g.paths.add_polyline_path([P(-1500, -600), P(W + 1500, -600), P(W + 1500, -1100), P(-1500, -1100)], is_closed=True)
    # цоколь и стены
    rect(msp, xl, -600, xr, 0, "Контур", lineweight=50)
    c = msp.add_hatch(color=8, dxfattribs={"layer": "Штриховка"})
    c.set_pattern_fill("AR-B816", scale=0.012)
    c.paths.add_polyline_path([P(xl, -600), P(xr, -600), P(xr, 0), P(xl, 0)], is_closed=True)
    rect(msp, xl, 0, xr, L2, "Контур", lineweight=50)
    line(msp, xl, L1, xr, L1, "Тонкие")
    # отделка: имитация бруса (горизонтальные линии)
    siding = msp.add_hatch(color=8, dxfattribs={"layer": "Штриховка"})
    siding.set_pattern_fill("LINE", scale=0.84)
    siding.paths.add_polyline_path([P(xl, 0), P(xr, 0), P(xr, L2), P(xl, L2)], is_closed=True)
    # кровля с выносом 600
    msp.add_lwpolyline([P(xl - 600, L2 - 250), P(W / 2, ridge), P(xr + 600, L2 - 250)], dxfattribs={"layer": "Контур", "lineweight": 50})
    msp.add_lwpolyline([P(xl - 600, L2 - 250), P(xl - 600, L2 - 450), P(W / 2, ridge - 200), P(xr + 600, L2 - 450), P(xr + 600, L2 - 250)],
                       dxfattribs={"layer": "Контур"})
    roof = msp.add_hatch(color=8, dxfattribs={"layer": "Штриховка"})
    roof.set_pattern_fill("AR-RSHKE", scale=0.01)
    roof.paths.add_polyline_path([P(xl - 600, L2 - 250), P(W / 2, ridge), P(xr + 600, L2 - 250)], is_closed=True)
    # окна (как на плане 1 и 2 этажа, стена по оси А)
    def window(cx, y0, w, hgt):
        rect(msp, cx - w / 2, y0, cx + w / 2, y0 + hgt, "Проемы", color=7)
        rect(msp, cx - w / 2 + 70, y0 + 70, cx + w / 2 - 70, y0 + hgt - 70, "Проемы", color=7)
        bg = msp.add_hatch(color=254, dxfattribs={"layer": "Проемы"})
        bg.paths.add_polyline_path([P(cx - w / 2 + 70, y0 + 70), P(cx + w / 2 - 70, y0 + 70),
                                    P(cx + w / 2 - 70, y0 + hgt - 70), P(cx - w / 2 + 70, y0 + hgt - 70)], is_closed=True)
        line(msp, cx, y0 + 70, cx, y0 + hgt - 70, "Проемы", color=7)
        line(msp, cx - w / 2 + 70, y0 + hgt * 0.68, cx + w / 2 - 70, y0 + hgt * 0.68, "Проемы", color=7)
        rect(msp, cx - w / 2 - 80, y0 - 60, cx + w / 2 + 80, y0, "Проемы", color=7)   # отлив
    for cx in (8100,):
        window(cx, 900, 1500, 1500)
    for cx in (1800, 8400):
        window(cx, L1 + 900, 1500, 1500)
    # входная дверь и козырёк
    rect(msp, 3700, 0, 4700, 2200, "Проемы", color=7)
    rect(msp, 3780, 0, 4620, 2120, "Проемы", color=7)
    circle(msp, 4520, 1050, 40, "Проемы")
    msp.add_lwpolyline([P(3300, 2550), P(5100, 2550), P(5100, 2450), P(3300, 2450)], close=True, dxfattribs={"layer": "Контур"})
    for x in (3400, 5000):
        line(msp, x, 2450, x, 0, "Тонкие")
    rect(msp, 3300, -600, 5100, -150, "Контур")                                         # крыльцо
    for k in (1, 2):
        line(msp, 3300 - k * 300, -600 + k * 150, 5100 + k * 300, -600 + k * 150, "Тонкие") if False else None
    # отметки уровней справа
    def level(y, label):
        x = xr + 1400
        line(msp, xr + 200, y, x + 900, y, "Отметки")
        msp.add_lwpolyline([P(x - 150, y + 260), P(x, y), P(x + 150, y + 260)], close=True, dxfattribs={"layer": "Отметки"})
        text(msp, label, x + 700, y + 330, 2.5, A.MIDDLE_CENTER, "Отметки")
    for y, lbl in ((L0, "±0,000"), (-600, "-0,600"), (L1, "+3,000"), (L2, "+6,000"), (ridge, "+8,600")):
        level(y, lbl)
    # оси 1 и 4
    for i, x in ((0, 0), (3, W)):
        msp.add_line(P(x, -1100), P(x, -2300), dxfattribs={"layer": "Оси"})
        bx, by = P(x, -2300)
        msp.add_circle((bx, by - 4), 4, dxfattribs={"layer": "Оси", "color": 7, "linetype": "Continuous"})
        mp.text(msp, mp.AXIS_X_LABELS[i], bx, by - 4, 3.5)
    msp.add_linear_dim(base=(0, P(0, -1600)[1]), p1=P(0, -1100), p2=P(W, -1100), angle=0, dimstyle="ГОСТ",
                       dxfattribs={"layer": "Размеры"}).render()
    plan = {"title": "Жилой дом. Фасад 1-4", "sheet": "Фасад 1-4", "axes_x": [0, W], "axes_y": [0, ridge]}
    mp.draw_sheet(msp, plan, [], 7)
    mp.text(msp, "Фасад 1-4  М 1:75", P(W / 2, 0)[0], P(0, ridge)[1] + 18, 5)
    mp.text(msp, "Отделка стен: имитация бруса, цоколь: облицовочный кирпич, кровля: гибкая черепица",
            P(W / 2, 0)[0], 30, 2.5)
    finish(doc, "07_dom_fasad")


# ---------- 3. чертёж детали ----------

def build_flange():
    mp.SCALE = 1
    mp.SHEET_HEADER = "КД.001.001"
    doc = mp.new_doc(); add_layers(doc)
    doc.dimstyles.get("ГОСТ").dxf.dimlfac = 1
    doc.dimstyles.get("ГОСТ").dxf.dimtsz = 0
    doc.dimstyles.get("ГОСТ").dxf.dimasz = 2.5
    msp = doc.modelspace()
    K = "Контур"
    D, Dh, d0, dc, H, h1, dhub = 160, 125, 70, 18, 28, 14, 95   # наружный Ø, Ø окружности отверстий, Ø отв., Ø крепёж., толщины, ступица
    cx, cy = 115, 170          # главный вид (вид слева — круг)
    msp.add_circle((cx, cy), D / 2, dxfattribs={"layer": K, "lineweight": 50})
    msp.add_circle((cx, cy), dhub / 2, dxfattribs={"layer": K, "lineweight": 50})
    msp.add_circle((cx, cy), d0 / 2, dxfattribs={"layer": K, "lineweight": 50})
    msp.add_circle((cx, cy), Dh / 2, dxfattribs={"layer": "Оси"})
    for k in range(4):
        a = math.radians(45 + 90 * k)
        hx, hy = cx + Dh / 2 * math.cos(a), cy + Dh / 2 * math.sin(a)
        msp.add_circle((hx, hy), dc / 2, dxfattribs={"layer": K, "lineweight": 50})
        msp.add_line((hx - 12, hy), (hx + 12, hy), dxfattribs={"layer": "Оси"})
        msp.add_line((hx, hy - 12), (hx, hy + 12), dxfattribs={"layer": "Оси"})
    msp.add_line((cx - D / 2 - 8, cy), (cx + D / 2 + 8, cy), dxfattribs={"layer": "Оси"})
    msp.add_line((cx, cy - D / 2 - 8), (cx, cy + D / 2 + 8), dxfattribs={"layer": "Оси"})
    # линия разреза А-А
    for y, d in ((cy + D / 2 + 14, 1), (cy - D / 2 - 14, -1)):
        msp.add_lwpolyline([(cx, y), (cx, y + d * 10)], dxfattribs={"layer": "Разрез", "const_width": 0.7})
        msp.add_lwpolyline([(cx, y + d * 5), (cx - 9, y + d * 5)], dxfattribs={"layer": "Разрез"})
        msp.add_lwpolyline([(cx - 5, y + d * 5 + 2), (cx - 9, y + d * 5), (cx - 5, y + d * 5 - 2)], dxfattribs={"layer": "Разрез"})
        mp.text(msp, "А", cx - 13, y + d * 5, 5)
    # разрез А-А (справа): профиль фланца со ступицей
    sx, sy = 235, cy
    def X(v): return sx + v
    prof = [(0, -D / 2), (h1, -D / 2), (h1, -dhub / 2), (H, -dhub / 2), (H, -d0 / 2 - 0), (0, -d0 / 2)]
    for sign in (1, -1):
        pts = [(X(x), sy + sign * y * -1) for x, y in prof]
        pts = [(X(x), sy - sign * y) for x, y in prof]
        msp.add_lwpolyline(pts, close=True, dxfattribs={"layer": K, "lineweight": 50})
        hz = msp.add_hatch(color=7, dxfattribs={"layer": "Штриховка"})
        hz.set_pattern_fill("ANSI31", scale=0.6)
        hz.paths.add_polyline_path(pts, is_closed=True)
    # отверстия крепежа в разрезе (верх и низ на окружности Dh — в сечении по А-А попадают проекции)
    for sign in (1, -1):
        yc = sy + sign * Dh / 2 * math.cos(math.radians(45))
        msp.add_line((X(-6), yc), (X(h1 + 6), yc), dxfattribs={"layer": "Оси"})
    msp.add_line((X(-10), sy), (X(H + 10), sy), dxfattribs={"layer": "Оси"})
    mp.text(msp, "А-А", X(H / 2), sy + D / 2 + 14, 5)
    # кромки отверстия Ø70 (видимые линии внутри разреза)
    for xv in (0, H):
        msp.add_line((X(xv), sy - d0 / 2), (X(xv), sy + d0 / 2), dxfattribs={"layer": K, "lineweight": 50})
    # фаски
    for sign in (1, -1):
        msp.add_line((X(H - 2), sy - sign * dhub / 2), (X(H), sy - sign * (dhub / 2 - 2)), dxfattribs={"layer": K})
    # размеры
    def dimv(y1, y2, x, txt):
        msp.add_linear_dim(base=(x, 0), p1=(X(0), y1), p2=(X(0), y2), angle=90, dimstyle="ГОСТ", text=txt,
                           dxfattribs={"layer": "Размеры"}).render()
    def dimh(x1, x2, y, txt="<>"):
        msp.add_linear_dim(base=(0, y), p1=(X(x1), sy - D / 2 if x2 == h1 else sy - dhub / 2), p2=(X(x2), sy - D / 2 if x2 == h1 else sy - dhub / 2), angle=0, dimstyle="ГОСТ", text=txt,
                           dxfattribs={"layer": "Размеры"}).render()
    dimv(sy - D / 2, sy + D / 2, X(-30), "%%c160h11")
    dimv(sy - dhub / 2, sy + dhub / 2, X(H + 22), "%%c95")
    dimv(sy - d0 / 2, sy + d0 / 2, X(H + 12), "%%c70H7")
    dimh(0, H, sy - D / 2 - 14)
    dimh(0, h1, sy - D / 2 - 6)
    msp.add_diameter_dim(center=(cx, cy), radius=Dh / 2, angle=200, dimstyle="ГОСТ", text="%%c125",
                         dxfattribs={"layer": "Размеры"}).render()
    hx, hy = cx + Dh / 2 * math.cos(math.radians(45)), cy + Dh / 2 * math.sin(math.radians(45))
    msp.add_diameter_dim(center=(hx, hy), radius=dc / 2, angle=45, dimstyle="ГОСТ", text="4 отв. %%c18",
                         dxfattribs={"layer": "Размеры"}).render()
    # шероховатость в правом верхнем углу
    mp.text(msp, "Ra 6,3 (√)", 395, 270, 3.5, A.MIDDLE_RIGHT)
    # технические требования
    for i, s in enumerate(["1. *Размеры для справок.", "2. Неуказанные предельные отклонения: H14, h14, ±IT14/2.",
                           "3. Острые кромки притупить R0,5.", "4. Покрытие: Хим. Окс. прм."]):
        mp.text(msp, s, 300, 132 - 6 * i, 2.8, A.MIDDLE_LEFT)
    mp.text(msp, "Технические требования", 300, 141, 3.5, A.MIDDLE_LEFT)
    mp.SCALE = 1
    plan = {"title": "Фланец. Сталь 45 ГОСТ 1050-2013", "sheet": "Фланец", "axes_x": [0], "axes_y": [0]}
    mp.draw_sheet(msp, plan, [], 8)
    finish(doc, "08_flanec")


def finish(doc, name):
    mp.OUT.mkdir(exist_ok=True)
    doc.saveas(mp.OUT / f"{name}.dxf")
    dm.qsave(doc.modelspace(), str(mp.OUT / f"{name}.png"), bg="#FFFFFF", dpi=150, size_inches=(16.54, 11.69))
    print("ok", name)


if __name__ == "__main__":
    import sys
    todo = sys.argv[1:] or ["plan", "facade", "flange"]
    if "1k" in todo:
        build_furnished(0, "01_kvartira_1k", "Квартира однокомнатная. План с мебелью", furniture_1k, 50, (2700, 4600), 1350)
    if "banya" in todo:
        build_furnished(4, "05_banya", "Баня с комнатой отдыха. План", furniture_banya, 50, (4200, 3900), 3300)
    if "plan" in todo:
        build_plan_pro()
    if "facade" in todo:
        build_facade()
    if "flange" in todo:
        build_flange()
