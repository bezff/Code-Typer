"""
Генератор иконки для Code Typer.

Стиль «клавиша»: скруглённый квадрат с толстой серой рамкой-безелем,
белый внутренний фон, по центру две стрелки ← → синего цвета.
"""

import math
import struct
import zlib
from pathlib import Path

ASSETS = Path(__file__).resolve().parent.parent / "assets"

# палитра
OUTER_BG   = (225, 225, 230)   # светло-серый фон снаружи (тень)
BEZEL      = (105, 110, 120)   # тёмно-серая рамка (безель клавиши)
BEZEL_LT   = (140, 145, 155)   # безель посветлее (для верхней части)
INNER_WHITE = (245, 246, 248)  # почти белый внутренний фон
INNER_TOP   = (250, 250, 252)  # чуть светлее сверху (градиент)
ARROW_CLR   = (75, 120, 165)   # грязно-синий для стрелок


def clamp(v, lo=0.0, hi=1.0):
    if v < lo: return lo
    if v > hi: return hi
    return v


def lerp_color(a, b, t):
    t = clamp(t)
    return (int(a[0] + (b[0]-a[0])*t),
            int(a[1] + (b[1]-a[1])*t),
            int(a[2] + (b[2]-a[2])*t))


def alpha_over(dst, src_rgb, src_a):
    """Стандартный alpha compositing поверх RGBA пикселя."""
    dr, dg, db, da_raw = dst
    da = da_raw / 255.0
    sa = clamp(src_a)
    out_a = sa + da * (1 - sa)
    if out_a < 0.001:
        return (0, 0, 0, 0)
    mix = lambda s, d: int((s*sa + d*da*(1-sa)) / out_a)
    return (min(255, mix(src_rgb[0], dr)),
            min(255, mix(src_rgb[1], dg)),
            min(255, mix(src_rgb[2], db)),
            int(min(255, out_a * 255)))


def sdf_rounded_rect(x, y, cx, cy, half_w, half_h, radius):
    """Signed distance до скруглённого прямоугольника."""
    qx = max(abs(x - cx) - half_w + radius, 0.0)
    qy = max(abs(y - cy) - half_h + radius, 0.0)
    return math.sqrt(qx*qx + qy*qy) - radius


def dist_to_segment(x, y, ax, ay, bx, by):
    """Расстояние от точки до отрезка."""
    ex, ey = bx-ax, by-ay
    sqlen = ex*ex + ey*ey
    if sqlen < 1e-8:
        return math.hypot(x-ax, y-ay)
    t = clamp(((x-ax)*ex + (y-ay)*ey) / sqlen)
    return math.hypot(x - (ax + t*ex), y - (ay + t*ey))


def stroke_line(buf, sz, ax, ay, bx, by, width, color):
    """Рисует сглаженную линию заданной толщины."""
    hw = width / 2
    extra = hw + 1.5
    x0 = max(0, int(min(ax, bx) - extra))
    x1 = min(sz-1, int(max(ax, bx) + extra))
    y0 = max(0, int(min(ay, by) - extra))
    y1 = min(sz-1, int(max(ay, by) + extra))

    for row in range(y0, y1+1):
        for col in range(x0, x1+1):
            d = dist_to_segment(col+.5, row+.5, ax, ay, bx, by)
            if d < hw + 1:
                opacity = clamp(hw + .5 - d)
                buf[row][col] = alpha_over(buf[row][col], color, opacity)


def fill_circle(buf, sz, cx, cy, r, color):
    """Рисует залитый круг (для закруглённых концов линий)."""
    extra = r + 1.5
    for row in range(max(0, int(cy-extra)), min(sz, int(cy+extra)+1)):
        for col in range(max(0, int(cx-extra)), min(sz, int(cx+extra)+1)):
            d = math.hypot(col+.5 - cx, row+.5 - cy)
            if d < r + 1:
                buf[row][col] = alpha_over(buf[row][col], color, clamp(r+.5 - d))


def render_icon(sz):
    """Отрисовка иконки sz×sz — клавиша с двумя стрелками."""
    buf = [[(0,0,0,0)]*sz for _ in range(sz)]

    mid = sz / 2

    # внешний скруглённый прямоугольник (безель)
    outer_pad = sz * 0.07
    outer_rnd = sz * 0.20
    outer_hw = mid - outer_pad
    outer_hh = mid - outer_pad

    # внутренний скруглённый прямоугольник (белая «клавиша»)
    inner_pad = sz * 0.14
    inner_rnd = sz * 0.15
    inner_hw = mid - inner_pad
    inner_hh = mid - inner_pad

    # рисуем фон, безель, внутреннюю область
    for y in range(sz):
        for x in range(sz):
            fx, fy = x+.5, y+.5

            # внешний прямоугольник — безель
            d_out = sdf_rounded_rect(fx, fy, mid, mid, outer_hw, outer_hh, outer_rnd)
            if d_out < 1.0:
                fill_a = clamp(.5 - d_out)
                # градиент по вертикали: сверху чуть светлее
                t = clamp((fy - outer_pad) / (sz - 2*outer_pad))
                bezel = lerp_color(BEZEL_LT, BEZEL, t * 0.7)
                buf[y][x] = (bezel[0], bezel[1], bezel[2], int(fill_a * 255))

            # внутренний прямоугольник — белая область
            d_in = sdf_rounded_rect(fx, fy, mid, mid, inner_hw, inner_hh, inner_rnd)
            if d_in < 1.0:
                fill_a = clamp(.5 - d_in)
                # лёгкий вертикальный градиент на белом
                t = clamp((fy - inner_pad) / (sz - 2*inner_pad))
                white = lerp_color(INNER_TOP, INNER_WHITE, t * 0.5)
                buf[y][x] = alpha_over(buf[y][x], white, fill_a)

    # стрелки ← →
    # параметры
    thick = max(2.0, sz * 0.045)   # толщина линий стрелок
    cap = thick * 0.5              # закруглённые концы
    arrow_h = sz * 0.09            # высота наконечника (полу-размах по Y)
    arrow_w = sz * 0.08            # глубина наконечника по X
    shaft_len = sz * 0.14          # длина «палки» стрелки
    gap = sz * 0.03                # зазор между стрелками

    cy = mid  # стрелки по центру по вертикали

    # ← левая стрелка
    l_tip = mid - gap - shaft_len - arrow_w   # кончик наконечника
    l_base = l_tip + arrow_w                   # основание наконечника / начало shaft
    l_end = l_base + shaft_len                 # конец shaft

    # палка
    stroke_line(buf, sz, l_base, cy, l_end, cy, thick, ARROW_CLR)
    fill_circle(buf, sz, l_end, cy, cap, ARROW_CLR)

    # наконечник ←: две линии от кончика к верху и низу
    stroke_line(buf, sz, l_tip, cy, l_base, cy - arrow_h, thick, ARROW_CLR)
    stroke_line(buf, sz, l_tip, cy, l_base, cy + arrow_h, thick, ARROW_CLR)
    fill_circle(buf, sz, l_tip, cy, cap, ARROW_CLR)
    fill_circle(buf, sz, l_base, cy - arrow_h, cap, ARROW_CLR)
    fill_circle(buf, sz, l_base, cy + arrow_h, cap, ARROW_CLR)

    # → правая стрелка
    r_tip = mid + gap + shaft_len + arrow_w
    r_base = r_tip - arrow_w
    r_start = r_base - shaft_len

    # палка
    stroke_line(buf, sz, r_start, cy, r_base, cy, thick, ARROW_CLR)
    fill_circle(buf, sz, r_start, cy, cap, ARROW_CLR)

    # наконечник →
    stroke_line(buf, sz, r_tip, cy, r_base, cy - arrow_h, thick, ARROW_CLR)
    stroke_line(buf, sz, r_tip, cy, r_base, cy + arrow_h, thick, ARROW_CLR)
    fill_circle(buf, sz, r_tip, cy, cap, ARROW_CLR)
    fill_circle(buf, sz, r_base, cy - arrow_h, cap, ARROW_CLR)
    fill_circle(buf, sz, r_base, cy + arrow_h, cap, ARROW_CLR)

    return buf


def shrink(src, src_sz, dst_sz):
    """Box-фильтр для уменьшения. Ничего хитрого, просто усреднение."""
    k = src_sz / dst_sz
    out = [[(0,0,0,0)]*dst_sz for _ in range(dst_sz)]
    for dy in range(dst_sz):
        for dx in range(dst_sz):
            r_sum = g_sum = b_sum = a_sum = 0.0
            cnt = 0
            sy0, sy1 = int(dy*k), min(src_sz, int((dy+1)*k))
            sx0, sx1 = int(dx*k), min(src_sz, int((dx+1)*k))
            for sy in range(sy0, sy1):
                for sx in range(sx0, sx1):
                    pr, pg, pb, pa = src[sy][sx]
                    r_sum += pr; g_sum += pg; b_sum += pb; a_sum += pa
                    cnt += 1
            if cnt:
                out[dy][dx] = (int(r_sum/cnt), int(g_sum/cnt),
                               int(b_sum/cnt), int(a_sum/cnt))
    return out


# --- PNG / ICO ---

def encode_png(pixels, size):
    raw = b""
    for row in pixels:
        raw += b"\x00"
        for r, g, b, a in row:
            raw += struct.pack("BBBB", r, g, b, a)

    def chunk(tag, data):
        body = tag + data
        return struct.pack(">I", len(data)) + body + struct.pack(">I", zlib.crc32(body) & 0xFFFFFFFF)

    hdr = struct.pack(">IIBBBBB", size, size, 8, 6, 0, 0, 0)
    return b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", hdr) + chunk(b"IDAT", zlib.compress(raw)) + chunk(b"IEND", b"")


def pack_ico(images):
    """images — список (size, png_bytes). Пакуем всё в один .ico."""
    count = len(images)
    hdr = struct.pack("<HHH", 0, 1, count)
    data_offset = 6 + count * 16
    directory = b""
    blob = b""
    for size, png in images:
        w = 0 if size >= 256 else size
        h = 0 if size >= 256 else size
        directory += struct.pack("<BBBBHHII", w, h, 0, 0, 1, 32, len(png), data_offset)
        blob += png
        data_offset += len(png)
    return hdr + directory + blob


ICON_SIZES = (256, 48, 32, 16)


def decode_png(path):
    """Читаем PNG файл и возвращаем (width, height, pixels)."""
    data = path.read_bytes()
    pos = 8
    idat_chunks = []
    width = height = 0
    while pos < len(data):
        length = struct.unpack('>I', data[pos:pos+4])[0]
        tag = data[pos+4:pos+8]
        chunk_data = data[pos+8:pos+8+length]
        if tag == b'IHDR':
            width, height = struct.unpack('>II', chunk_data[:8])
        elif tag == b'IDAT':
            idat_chunks.append(chunk_data)
        elif tag == b'IEND':
            break
        pos += 12 + length

    raw = zlib.decompress(b''.join(idat_chunks))
    buf = [[(0,0,0,0)] * width for _ in range(height)]
    prev_row = bytes(width * 4)
    offset = 0
    for y in range(height):
        filt = raw[offset]; offset += 1
        row_bytes = bytearray(raw[offset:offset + width * 4]); offset += width * 4

        def _paeth(a, b, c):
            p = a + b - c
            pa, pb, pc = abs(p - a), abs(p - b), abs(p - c)
            if pa <= pb and pa <= pc: return a
            return b if pb <= pc else c

        if filt == 1:
            for i in range(len(row_bytes)):
                row_bytes[i] = (row_bytes[i] + (row_bytes[i-4] if i >= 4 else 0)) & 0xFF
        elif filt == 2:
            for i in range(len(row_bytes)):
                row_bytes[i] = (row_bytes[i] + prev_row[i]) & 0xFF
        elif filt == 3:
            for i in range(len(row_bytes)):
                a = row_bytes[i-4] if i >= 4 else 0
                row_bytes[i] = (row_bytes[i] + (a + prev_row[i]) // 2) & 0xFF
        elif filt == 4:
            for i in range(len(row_bytes)):
                a = row_bytes[i-4] if i >= 4 else 0
                row_bytes[i] = (row_bytes[i] + _paeth(a, prev_row[i], prev_row[i-4] if i >= 4 else 0)) & 0xFF

        for x in range(width):
            buf[y][x] = (row_bytes[x*4], row_bytes[x*4+1], row_bytes[x*4+2], row_bytes[x*4+3])
        prev_row = bytes(row_bytes)
    return width, height, buf


def upscale_nearest(src, src_sz, dst_sz):
    """Nearest-neighbor увеличение."""
    out = [[(0,0,0,0)] * dst_sz for _ in range(dst_sz)]
    for y in range(dst_sz):
        for x in range(dst_sz):
            out[y][x] = src[y * src_sz // dst_sz][x * src_sz // dst_sz]
    return out


def ensure_icon():
    """Генерируем иконки из icon.png если их ещё нет. Возвращает путь к .ico."""
    ASSETS.mkdir(parents=True, exist_ok=True)
    ico = ASSETS / "icon.ico"

    if ico.exists() and all((ASSETS / f"icon_{s}.png").exists() for s in ICON_SIZES):
        return ico

    src_path = ASSETS / "icon.png"
    if src_path.exists():
        src_w, src_h, src_buf = decode_png(src_path)
        big = upscale_nearest(src_buf, src_w, 256) if src_w < 256 else src_buf
        big_sz = 256 if src_w < 256 else src_w
    else:
        big = render_icon(256)
        big_sz = 256

    parts = []
    for s in ICON_SIZES:
        px = big if s == big_sz else shrink(big, big_sz, s)
        png_data = encode_png(px, s)
        (ASSETS / f"icon_{s}.png").write_bytes(png_data)
        parts.append((s, png_data))

    ico.write_bytes(pack_ico(parts))
    return ico
