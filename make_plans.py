"""Генерирует 5 чертежей планов в DXF (открываются в AutoCAD) и PNG для портфолио.

Чертёж строится на листе A3 в миллиметрах бумаги, план в масштабе 1:100
(размерный стиль показывает реальные размеры через DIMLFAC=100).
"""
import sys
from pathlib import Path

import ezdxf
from ezdxf.enums import TextEntityAlignment as A
from ezdxf.addons.drawing import matplotlib as dm

OUT = Path(__file__).parent / "out"
SCALE = 100           # масштаб текущего плана, подбирается в build() из 1:50 / 1:75 / 1:100
PLAN_ORIGIN = [45, 60]  # левый нижний угол плана на листе, мм бумаги


# ---------- описание планов (реальные мм) ----------
# walls: (x1, y1, x2, y2, толщина) по осевой линии стены
# openings: (индекс стены, центр от начала стены, ширина, "window"/"door", сторона распахивания ±1, петли "start"/"end")
# rooms: (№, название, x1, y1, x2, y2) в координатах осей — площадь считается по чистым размерам

PLANS = [
    {
        "file": "01_kvartira_1k", "title": "Квартира однокомнатная. План",
        "sheet": "План квартиры", "axes_x": [0, 1800, 3600, 6600], "axes_y": [0, 2700, 7500],
        "walls": [(0, 0, 6600, 0, 400), (6600, 0, 6600, 7500, 400), (6600, 7500, 0, 7500, 400), (0, 7500, 0, 0, 400),
                  (0, 2700, 6600, 2700, 200), (1800, 0, 1800, 2700, 100), (3600, 0, 3600, 2700, 200)],
        "openings": [(0, 2700, 900, "door", 1, "start"), (6, 1900, 800, "door", -1, "end"),
                     (5, 1800, 700, "door", -1, "start"), (4, 2700, 900, "door", 1, "start"),
                     (2, 1700, 1500, "window", 1, ""), (2, 4900, 1500, "window", 1, ""),
                     (1, 1350, 1200, "window", 1, "")],
        "rooms": [(1, "Жилая комната", 0, 2700, 6600, 7500), (2, "Кухня", 3600, 0, 6600, 2700),
                  (3, "Коридор", 1800, 0, 3600, 2700), (4, "Санузел", 0, 0, 1800, 2700)],
    },
    {
        "file": "02_kvartira_2k", "title": "Квартира двухкомнатная. План",
        "sheet": "План квартиры", "axes_x": [0, 3300, 5100, 9000], "axes_y": [0, 2400, 4800, 9000],
        "walls": [(0, 0, 9000, 0, 400), (9000, 0, 9000, 9000, 400), (9000, 9000, 0, 9000, 400), (0, 9000, 0, 0, 400),
                  (3300, 0, 3300, 9000, 200), (5100, 0, 5100, 9000, 200), (0, 4800, 3300, 4800, 200),
                  (5100, 4800, 9000, 4800, 200), (5100, 2400, 9000, 2400, 120)],
        "openings": [(0, 4200, 900, "door", 1, "start"), (4, 1500, 800, "door", 1, "end"),
                     (4, 6900, 800, "door", 1, "start"), (5, 6900, 800, "door", -1, "end"),
                     (5, 3600, 700, "door", -1, "start"), (5, 1200, 700, "door", -1, "end"),
                     (2, 1900, 1500, "window", 1, ""), (2, 7100, 1500, "window", 1, ""),
                     (3, 1500, 1500, "window", 1, ""), (3, 6600, 1200, "window", 1, ""),
                     (1, 3600, 900, "window", 1, "")],
        "rooms": [(1, "Жилая комната", 0, 4800, 3300, 9000), (2, "Жилая комната", 5100, 4800, 9000, 9000),
                  (3, "Кухня", 0, 0, 3300, 4800), (4, "Коридор", 3300, 0, 5100, 9000),
                  (5, "Санузел", 5100, 2400, 9000, 4800), (6, "Кладовая", 5100, 0, 9000, 2400)],
    },
    {
        "file": "03_dom_plan_1_etazha", "title": "Жилой дом. План 1 этажа",
        "sheet": "План 1 этажа", "axes_x": [0, 2400, 6000, 10200], "axes_y": [0, 2400, 4800, 9000],
        "walls": [(0, 0, 10200, 0, 400), (10200, 0, 10200, 9000, 400), (10200, 9000, 0, 9000, 400), (0, 9000, 0, 0, 400),
                  (2400, 0, 2400, 4800, 200), (6000, 0, 6000, 9000, 250), (0, 4800, 6000, 4800, 250),
                  (0, 2400, 2400, 2400, 120)],
        "openings": [(0, 4200, 1000, "door", 1, "start"), (4, 1200, 800, "door", -1, "end"),
                     (4, 3600, 800, "door", -1, "start"), (5, 2400, 900, "door", 1, "start"),
                     (6, 4200, 900, "door", 1, "end"), (7, 1200, 700, "door", -1, "start"),
                     (1, 2000, 1500, "window", 1, ""), (1, 6600, 1800, "window", 1, ""),
                     (2, 2100, 1500, "window", 1, ""), (2, 7600, 1500, "window", 1, ""),
                     (3, 2200, 1500, "window", 1, ""), (0, 8100, 1500, "window", 1, "")],
        "rooms": [(1, "Тамбур", 2400, 0, 6000, 2400), (2, "Санузел", 0, 2400, 2400, 4800),
                  (3, "Котельная", 0, 0, 2400, 2400), (4, "Холл с лестницей", 2400, 2400, 6000, 4800),
                  (5, "Спальня", 0, 4800, 6000, 9000), (6, "Кухня-гостиная", 6000, 0, 10200, 9000)],
    },
    {
        "file": "04_dom_plan_2_etazha", "title": "Жилой дом. План 2 этажа",
        "sheet": "План 2 этажа", "axes_x": [0, 3600, 6600, 10200], "axes_y": [0, 3000, 5000, 9000],
        "walls": [(0, 0, 10200, 0, 400), (10200, 0, 10200, 9000, 400), (10200, 9000, 0, 9000, 400), (0, 9000, 0, 0, 400),
                  (3600, 0, 3600, 9000, 200), (6600, 0, 6600, 9000, 200), (0, 5000, 3600, 5000, 200),
                  (6600, 5000, 10200, 5000, 200), (3600, 3000, 6600, 3000, 120)],
        "openings": [(4, 2000, 800, "door", 1, "start"), (4, 7000, 800, "door", 1, "end"),
                     (5, 2000, 800, "door", -1, "end"), (5, 7000, 800, "door", -1, "start"),
                     (8, 1500, 700, "door", 1, "start"),
                     (0, 1800, 1500, "window", 1, ""), (0, 8400, 1500, "window", 1, ""),
                     (2, 1800, 1500, "window", 1, ""), (2, 8400, 1500, "window", 1, ""),
                     (2, 5100, 1200, "window", 1, ""), (1, 2500, 1200, "window", 1, "")],
        "rooms": [(1, "Спальня", 0, 0, 3600, 5000), (2, "Спальня", 0, 5000, 3600, 9000),
                  (3, "Санузел", 3600, 0, 6600, 3000), (4, "Холл", 3600, 3000, 6600, 9000),
                  (5, "Детская", 6600, 0, 10200, 5000), (6, "Кабинет", 6600, 5000, 10200, 9000)],
    },
    {
        "file": "05_banya", "title": "Баня с комнатой отдыха. План",
        "sheet": "План бани", "axes_x": [0, 2400, 6000], "axes_y": [0, 1800, 4800],
        "walls": [(0, 0, 6000, 0, 200), (6000, 0, 6000, 4800, 200), (6000, 4800, 0, 4800, 200), (0, 4800, 0, 0, 200),
                  (2400, 0, 2400, 4800, 150), (0, 1800, 2400, 1800, 150)],
        "openings": [(0, 4200, 900, "door", 1, "start"), (4, 900, 700, "door", -1, "start"),
                     (5, 1200, 700, "door", 1, "end"), (2, 1200, 600, "window", 1, ""),
                     (2, 4200, 1200, "window", 1, ""), (1, 2400, 1200, "window", 1, "")],
        "rooms": [(1, "Парная", 0, 1800, 2400, 4800), (2, "Моечная", 0, 0, 2400, 1800),
                  (3, "Комната отдыха", 2400, 0, 6000, 4800)],
    },
]

TOTAL_SHEETS = 10
BRICK_HATCH = False
SHEET_HEADER = "П-01-2026-АР"
WALL_HATCH_COLOR = 8
AXIS_X_LABELS = "123456789"
AXIS_Y_LABELS = "АБВГДЕЖИК"


# ---------- оформление документа ----------

def new_doc():  # noqa: C901
    doc = ezdxf.new("R2010", setup=True)
    doc.units = ezdxf.units.MM
    doc.header["$LTSCALE"] = 0.25
    doc.styles.new("GOST", dxfattribs={"font": "isocpeur.ttf", "width": 0.9})
    for name, color, lt, lw in [("Оси", 1, "DASHDOT", 18), ("Стены", 8, "Continuous", 50),
                                ("Проемы", 5, "Continuous", 25), ("Размеры", 7, "Continuous", 18),
                                ("Надписи", 7, "Continuous", 25), ("Помещения", 7, "Continuous", 18),
                                ("Рамка", 7, "Continuous", 50), ("Штамп", 7, "Continuous", 25)]:
        doc.layers.add(name, color=color, linetype=lt, lineweight=lw)
    doc.dimstyles.new("ГОСТ", dxfattribs={
        "dimtsz": 1.0, "dimtxt": 2.5, "dimexe": 1.5, "dimexo": 1.5, "dimlfac": SCALE, "dimdec": 0,
        "dimgap": 0.8, "dimtad": 1, "dimtxsty": "GOST", "dimdle": 1.5, "dimclrd": 7, "dimclre": 7, "dimclrt": 7})
    window = doc.blocks.new("ОКНО")          # длина 1, толщина 1, центр по оси стены
    for y in (-0.5, 0.5, -0.12, 0.12):
        window.add_line((0, y), (1, y))
    window.add_line((0, -0.5), (0, 0.5))
    window.add_line((1, -0.5), (1, 0.5))
    door = doc.blocks.new("ДВЕРЬ")           # петля в (0,0), проём вдоль +X, полотно по +Y
    door.add_line((0, 0), (0, 1))
    door.add_arc((0, 0), 1, 0, 90)
    return doc


def P(x, y):
    """Реальные мм плана -> мм бумаги."""
    return PLAN_ORIGIN[0] + x / SCALE, PLAN_ORIGIN[1] + y / SCALE


def text(msp, s, x, y, h=3.5, align=A.MIDDLE_CENTER, layer="Надписи"):
    msp.add_text(s, height=h, dxfattribs={"style": "GOST", "layer": layer}).set_placement((x, y), align=align)


# ---------- стены и проёмы ----------

def draw_walls(msp, walls, openings):
    for i, (x1, y1, x2, y2, t) in enumerate(walls):
        if t == 0:
            continue
        length = abs(x2 - x1) + abs(y2 - y1)
        dx, dy = ((x2 > x1) - (x2 < x1), (y2 > y1) - (y2 < y1))
        nx, ny = -dy, dx
        gaps = sorted((c - w / 2, c + w / 2) for wi, c, w, *_ in openings if wi == i)
        start, pieces = -t / 2, []
        for a, b in gaps:
            pieces.append((start, a))
            start = b
        pieces.append((start, length + t / 2))
        for a, b in pieces:
            if b <= a:
                continue
            pts = [(x1 + dx * s + nx * o, y1 + dy * s + ny * o) for s, o in
                   ((a, -t / 2), (b, -t / 2), (b, t / 2), (a, t / 2))]
            hatch = msp.add_hatch(color=WALL_HATCH_COLOR, dxfattribs={"layer": "Стены"})
            if BRICK_HATCH and t >= 380:          # наружные стены: штриховка кладки
                hatch.dxf.color = 7
                hatch.set_pattern_fill("ANSI31", scale=0.35)
            hatch.paths.add_polyline_path([P(*p) for p in pts], is_closed=True)
            msp.add_lwpolyline([P(*p) for p in pts], close=True, dxfattribs={"layer": "Стены", "color": 7})
        for wi, c, w, kind, side, hinge in (o for o in openings if o[0] == i):
            ang = {(1, 0): 0, (0, 1): 90, (-1, 0): 180, (0, -1): 270}[(dx, dy)]
            if kind == "window":
                cx, cy = x1 + dx * (c - w / 2), y1 + dy * (c - w / 2)
                msp.add_blockref("ОКНО", P(cx, cy), dxfattribs={
                    "xscale": w / SCALE, "yscale": t / SCALE, "rotation": ang, "layer": "Проемы"})
            else:
                s0 = c - w / 2 if hinge == "start" else c + w / 2
                hx, hy = x1 + dx * s0 + nx * side * t / 2, y1 + dy * s0 + ny * side * t / 2
                sx = w / SCALE if hinge == "start" else -w / SCALE
                msp.add_blockref("ДВЕРЬ", P(hx, hy), dxfattribs={
                    "xscale": sx, "yscale": side * w / SCALE, "rotation": ang, "layer": "Проемы"})


def wall_half(walls, x1, y1, x2, y2):
    """Половина толщины стены, лежащей на отрезке границы помещения."""
    best = 0
    for wx1, wy1, wx2, wy2, t in walls:
        if x1 == x2 == wx1 == wx2 and max(min(y1, y2), min(wy1, wy2)) < min(max(y1, y2), max(wy1, wy2)):
            best = max(best, t / 2)
        if y1 == y2 == wy1 == wy2 and max(min(x1, x2), min(wx1, wx2)) < min(max(x1, x2), max(wx1, wx2)):
            best = max(best, t / 2)
    return best


def draw_rooms(msp, plan):
    rows = []
    for num, name, x1, y1, x2, y2 in plan["rooms"]:
        l = wall_half(plan["walls"], x1, y1, x1, y2)
        r = wall_half(plan["walls"], x2, y1, x2, y2)
        b = wall_half(plan["walls"], x1, y1, x2, y1)
        t = wall_half(plan["walls"], x1, y2, x2, y2)
        area = (x2 - x1 - l - r) * (y2 - y1 - b - t) / 1e6
        rows.append((num, name, area))
        cx, cy = P(x1 + l + 5 * SCALE, y2 - t - 5 * SCALE)            # номер в кружке у угла помещения
        msp.add_circle((cx, cy), 2.6, dxfattribs={"layer": "Помещения"})
        text(msp, str(num), cx, cy, 2.5, layer="Помещения")
        mx, my = P((x1 + x2) / 2, (y1 + y2) / 2)
        text(msp, f"{area:.1f}".replace(".", ","), mx, my, 3.0, layer="Помещения")
    return rows


# ---------- оси и размеры ----------

def draw_axes_and_dims(msp, plan):
    xs, ys = plan["axes_x"], plan["axes_y"]
    ext = 18 * SCALE
    for i, x in enumerate(xs):
        a, b = P(x, -ext), P(x, ys[-1] + 9 * SCALE)
        msp.add_line(a, b, dxfattribs={"layer": "Оси"})
        bx, by = P(x, -ext)
        msp.add_circle((bx, by - 4), 4, dxfattribs={"layer": "Оси", "color": 7, "linetype": "Continuous"})
        text(msp, AXIS_X_LABELS[i], bx, by - 4, 3.5)
    for i, y in enumerate(ys):
        a, b = P(-ext, y), P(xs[-1] + 9 * SCALE, y)
        msp.add_line(a, b, dxfattribs={"layer": "Оси"})
        bx, by = P(-ext, y)
        msp.add_circle((bx - 4, by), 4, dxfattribs={"layer": "Оси", "color": 7, "linetype": "Continuous"})
        text(msp, AXIS_Y_LABELS[i], bx - 4, by, 3.5)
    dim = lambda p1, p2, base, ang: msp.add_linear_dim(
        base=base, p1=p1, p2=p2, angle=ang, dimstyle="ГОСТ", dxfattribs={"layer": "Размеры"}).render()
    y_chain, y_total = P(0, -7 * SCALE)[1], P(0, -13 * SCALE)[1]
    for a, b in zip(xs, xs[1:]):
        dim(P(a, 0), P(b, 0), (0, y_chain), 0)
    dim(P(xs[0], 0), P(xs[-1], 0), (0, y_total), 0)
    x_chain, x_total = P(-7 * SCALE, 0)[0], P(-13 * SCALE, 0)[0]
    for a, b in zip(ys, ys[1:]):
        dim(P(0, a), P(0, b), (x_chain, 0), 90)
    dim(P(0, ys[0]), P(0, ys[-1]), (x_total, 0), 90)


# ---------- лист: рамка, штамп, экспликация ----------

def draw_sheet(msp, plan, rows, sheet_no):
    msp.add_lwpolyline([(0, 0), (420, 0), (420, 297), (0, 297)], close=True, dxfattribs={"layer": "Рамка", "lineweight": 18})
    msp.add_lwpolyline([(20, 5), (415, 5), (415, 292), (20, 292)], close=True, dxfattribs={"layer": "Рамка"})
    # штамп по форме 3 ГОСТ Р 21.101-2020, 185 x 55
    x0, y0 = 230, 5
    L = lambda a, b, c, d: msp.add_line((a, b), (c, d), dxfattribs={"layer": "Штамп"})
    msp.add_lwpolyline([(x0, y0), (415, y0), (415, y0 + 55), (x0, y0 + 55)], close=True, dxfattribs={"layer": "Рамка"})
    for k in range(1, 11):
        L(x0, y0 + 5 * k, x0 + 65, y0 + 5 * k)
    for dx in (10, 20, 30, 40, 55):          # Изм. 10, Кол.уч 10, Лист 10, № док. 10, Подп. 15, Дата 10
        L(x0 + dx, y0 + 25, x0 + dx, y0 + 55)
    for dx in (20, 40, 55):                  # нижние строки: должность 20, фамилия 20, подпись 15, дата 10
        L(x0 + dx, y0, x0 + dx, y0 + 25)
    msp.add_line((x0 + 65, y0), (x0 + 65, y0 + 55), dxfattribs={"layer": "Рамка"})
    L(x0 + 65, y0 + 40, 415, y0 + 40)        # графа 1: обозначение документа
    L(x0 + 65, y0 + 25, 415, y0 + 25)        # графа 2: наименование объекта
    L(x0 + 135, y0, x0 + 135, y0 + 25)       # графа 4 (70) | стадия, лист, листов, организация (50)
    L(x0 + 135, y0 + 20, 415, y0 + 20)
    L(x0 + 135, y0 + 15, 415, y0 + 15)
    for dx in (150, 165):
        L(x0 + dx, y0 + 15, x0 + dx, y0 + 25)
    for cx, s in zip((5, 15, 25, 35, 47.5, 60), ("Изм.", "Кол.уч", "Лист", "№ док.", "Подп.", "Дата")):
        text(msp, s, x0 + cx, y0 + 27.5, 1.8)
    for i, (role, who) in enumerate([("Разраб.", "Сайкин Б.А."), ("Пров.", ""), ("", ""),
                                     ("Н. контр.", ""), ("Утв.", "")]):
        text(msp, role, x0 + 1, y0 + 22.5 - 5 * i, 1.8, A.MIDDLE_LEFT)
        text(msp, who, x0 + 21, y0 + 22.5 - 5 * i, 1.8, A.MIDDLE_LEFT)
    text(msp, SHEET_HEADER, x0 + 125, y0 + 47.5, 3.5)
    text(msp, plan["title"], x0 + 125, y0 + 32.5, 3.0)
    text(msp, plan["sheet"], x0 + 100, y0 + 15, 2.5)          # графа 4 в две строки
    text(msp, f"М 1:{SCALE}", x0 + 100, y0 + 8.5, 2.5)
    for dx, s in ((142.5, "Стадия"), (157.5, "Лист"), (175, "Листов")):
        text(msp, s, x0 + dx, y0 + 22.5, 1.8)
    for dx, s in ((142.5, "Р"), (157.5, str(sheet_no)), (175, str(TOTAL_SHEETS))):
        text(msp, s, x0 + dx, y0 + 17.5, 2.5)
    text(msp, "keeeensy.github.io", x0 + 160, y0 + 7.5, 2.5)
    # дополнительные графы на поле подшивки
    for (y1, y2), s in (((5, 30), "Инв. № подл."), ((30, 65), "Подп. и дата"), ((65, 90), "Взам. инв. №")):
        msp.add_lwpolyline([(8, y1), (20, y1), (20, y2), (8, y2)], close=True, dxfattribs={"layer": "Рамка"})
        msp.add_line((13, y1), (13, y2), dxfattribs={"layer": "Штамп"})
        msp.add_text(s, height=1.8, dxfattribs={"style": "GOST", "layer": "Надписи", "rotation": 90}).set_placement(
            (10.5, (y1 + y2) / 2), align=A.MIDDLE_CENTER)
    if not rows:
        return
    # экспликация помещений
    ex, ey = 300, 70 + 8 * (len(rows) + 1)
    text(msp, "Экспликация помещений", ex + 55, ey + 5, 3.5)
    cols = [0, 10, 80, 110]
    hdr = ["№", "Наименование", "Площадь, м²"]
    for k in range(len(rows) + 2):
        L(ex, ey - 8 * k, ex + 110, ey - 8 * k)
    for c in cols:
        L(ex + c, ey, ex + c, ey - 8 * (len(rows) + 1))
    for j, h in enumerate(hdr):
        text(msp, h, ex + (cols[j] + cols[j + 1]) / 2, ey - 4, 2.5)
    for k, (num, name, area) in enumerate(rows, 1):
        y = ey - 8 * k - 4
        text(msp, str(num), ex + 5, y, 2.5)
        text(msp, name, ex + 12, y, 2.5, A.MIDDLE_LEFT)
        text(msp, f"{area:.1f}".replace(".", ","), ex + 95, y, 2.5)
    total = sum(r[2] for r in rows)
    text(msp, f"Итого: {total:.1f} м²".replace(".", ","), ex + 108, ey - 8 * (len(rows) + 1) - 5, 2.5, A.MIDDLE_RIGHT)
    # заголовок плана
    w = plan["axes_x"][-1] / SCALE
    text(msp, f"{plan['sheet']}  М 1:{SCALE}", PLAN_ORIGIN[0] + w / 2, PLAN_ORIGIN[1] + plan["axes_y"][-1] / SCALE + 22, 5)


def build(plan, sheet_no):
    global SCALE
    w, h = plan["axes_x"][-1], plan["axes_y"][-1]
    SCALE = next(sc for sc in (50, 75, 100) if w / sc <= 150 and h / sc <= 175)
    PLAN_ORIGIN[0] = 60 + (160 - w / SCALE) / 2
    PLAN_ORIGIN[1] = 40 + (205 - h / SCALE) / 2
    doc = new_doc()
    msp = doc.modelspace()
    draw_axes_and_dims(msp, plan)
    draw_walls(msp, plan["walls"], plan["openings"])
    rows = draw_rooms(msp, plan)
    draw_sheet(msp, plan, rows, sheet_no)
    OUT.mkdir(exist_ok=True)
    doc.saveas(OUT / f"{plan['file']}.dxf")
    dm.qsave(msp, str(OUT / f"{plan['file']}.png"), bg="#FFFFFF", dpi=150, size_inches=(16.54, 11.69))
    print("ok", plan["file"])


if __name__ == "__main__":
    only = sys.argv[1:]
    for n, plan in enumerate(PLANS, 1):
        if not only or plan["file"] in only:
            build(plan, n)
