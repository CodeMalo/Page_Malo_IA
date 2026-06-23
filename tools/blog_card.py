"""
blog_card.py — La SEGUNDA imagen del blog (estilo viral, sin API keys).
=======================================================================
Toma 1-2 imágenes de referencia → VS (split comparativo) o single, le pone a
BIX encima, la marca malo_ia y un headline grande con palabras de acento en el
color que le toca a esa publicación (rotación de teoría del color, ver palette.py).

Todo con Pillow: rápido, gratis, controlado y de alta calidad.
"""

from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter, ImageChops

import style, palette


def cutout_green(img, thresh=42):
    """Recorta un fondo chroma verde → devuelve RGBA con BIX sobre transparente.
    1) Key por 'verdura' (g - max(r,b)). 2) Se queda SOLO con la mancha conectada
    al centro (flood) → elimina islas sueltas (un piso/sombra que Gemini agregue).
    3) Despill para sacar el halo verde del borde."""
    img = img.convert("RGB")
    r, g, b = img.split()
    rb_max = ImageChops.lighter(r, b)
    greenness = ImageChops.subtract(g, rb_max)              # 0..255
    alpha = greenness.point(lambda v: 0 if v > thresh else 255)

    # quedarse con el blob conectado al centro (BIX), descartar islas
    w, h = img.size
    mask = alpha.point(lambda v: 255 if v > 20 else 0).convert("RGB")
    seed = (w // 2, int(h * 0.45))
    if mask.getpixel(seed)[0] < 200:                        # si el centro cae en hueco
        for sy in (0.55, 0.35, 0.5):
            cand = (w // 2, int(h * sy))
            if mask.getpixel(cand)[0] >= 200:
                seed = cand; break
    ImageDraw.floodfill(mask, seed, (255, 0, 0), thresh=10)
    mr, mg, mb = mask.split()
    keep = ImageChops.multiply(mr.point(lambda v: 255 if v > 200 else 0),
                               mg.point(lambda v: 255 if v < 60 else 0))
    keep = ImageChops.multiply(keep, mb.point(lambda v: 255 if v < 60 else 0))
    alpha = ImageChops.darker(alpha, keep)                  # 0 fuera del blob de BIX

    # desvanecer la base: mata cualquier piso/sombra pegado a los pies y deja un
    # contacto suave (Gemini casi siempre agrega algo de piso aunque le pidamos que no)
    bbox = alpha.getbbox()
    if bbox:
        y0, y1 = bbox[1], bbox[3]
        bh = max(1, y1 - y0)
        fstart = y1 - int(bh * 0.11)
        ramp = Image.new("L", (1, h), 255); rp = ramp.load()
        for y in range(h):
            if y <= fstart:
                rp[0, y] = 255
            elif y >= y1:
                rp[0, y] = 0
            else:
                rp[0, y] = int(255 * (1 - (y - fstart) / max(1, y1 - fstart)))
        alpha = ImageChops.darker(alpha, ramp.resize((w, h)))

    alpha = alpha.filter(ImageFilter.GaussianBlur(0.6))     # borde apenas suave
    g2 = ImageChops.darker(g, rb_max)                        # despill: g <= max(r,b)
    out = Image.merge("RGB", (r, g2, b)).convert("RGBA")
    out.putalpha(alpha)
    return out

W, H = 1080, 1350           # formato 4:5 (Instagram)
IMG_H = 760                 # alto del área de imagen (arriba)
MARGIN = 70
DARK = (11, 11, 13)
WHITE = (244, 244, 246)
BRAND = "malo_ia"
ROOT = Path(__file__).resolve().parents[1]


# ── helpers de imagen ─────────────────────────────────────────────────────────
def _cover_fit(img, w, h):
    img = img.convert("RGB")
    s = max(w / img.width, h / img.height)
    img = img.resize((max(1, int(img.width * s)), max(1, int(img.height * s))), Image.LANCZOS)
    l, t = (img.width - w) // 2, (img.height - h) // 2
    return img.crop((l, t, l + w, t + h))


def _crop_to_content(img):
    img = img.convert("RGBA")
    bbox = img.split()[3].getbbox()      # recorta al contorno de BIX (alpha)
    return img.crop(bbox) if bbox else img


def _vgrad_rgba(w, h, top_a, bot_a, color):
    base = Image.new("L", (1, h))
    px = base.load()
    for y in range(h):
        t = y / max(h - 1, 1)
        px[0, y] = int(top_a + (bot_a - top_a) * t)
    alpha = base.resize((w, h))
    out = Image.new("RGBA", (w, h), color + (0,))
    out.putalpha(alpha)
    return out


# ── headline con palabras de acento ───────────────────────────────────────────
_STOP = {"a", "an", "the", "of", "in", "on", "to", "and", "or", "for", "is", "it", "s"}


def _accentize(words, accent_rgb):
    """Devuelve [(word, color)]: resalta palabras clave alternadas en el acento."""
    out, flip = [], True
    for w in words:
        key = len(w) >= 3 and w.lower() not in _STOP
        if key:
            out.append((w, accent_rgb if flip else WHITE))
            flip = not flip
        else:
            out.append((w, WHITE))
    return out


def _fit_lines(draw, words_colored, max_w, avail_h):
    """Elige el tamaño de fuente Anton que mejor llena el panel (<=4 líneas)."""
    for size in range(116, 52, -4):
        font = style._font("Anton.ttf", size)
        lines, cur = [], []
        for wc in words_colored:
            test = " ".join(w for w, _ in cur + [wc])
            if cur and draw.textlength(test, font=font) > max_w:
                lines.append(cur); cur = [wc]
            else:
                cur.append(wc)
        if cur:
            lines.append(cur)
        lh = int(size * 1.02)
        if len(lines) <= 4 and len(lines) * lh <= avail_h:
            return font, lines, lh
    # fallback chico
    font = style._font("Anton.ttf", 56)
    return font, [[wc] for wc in words_colored][:4], int(56 * 1.02)


# ── render principal ──────────────────────────────────────────────────────────
def render(title, refs, accent_rgb, out_path, bix_section="blog",
           footer="READ THE FULL POST", card_bg=None, bix_override=None):
    refs = [r for r in (refs or []) if r and Path(r).exists()][:2]
    canvas = Image.new("RGB", (W, H), DARK).convert("RGBA")
    bix_in_bg = False   # si el fondo ya trae a BIX (Gemini), no pegamos el cutout

    # 1) área de imagen: VS (2) / single (1) / fondo Gemini con BIX / gradiente
    if len(refs) >= 2:
        half = W // 2
        canvas.paste(_cover_fit(Image.open(refs[0]), half, IMG_H), (0, 0))
        canvas.paste(_cover_fit(Image.open(refs[1]), W - half, IMG_H), (half, 0))
    elif len(refs) == 1:
        canvas.paste(_cover_fit(Image.open(refs[0]), W, IMG_H), (0, 0))
    elif card_bg and Path(card_bg).exists():
        canvas.paste(_cover_fit(Image.open(card_bg), W, IMG_H), (0, 0))
        bix_in_bg = True
    else:
        g = Image.new("RGB", (1, IMG_H))
        gp = g.load()
        dk = palette.darken(accent_rgb, 0.35)
        for y in range(IMG_H):
            t = y / IMG_H
            gp[0, y] = palette.mix(accent_rgb, dk, t)
        canvas.paste(g.resize((W, IMG_H)), (0, 0))

    # 2) fundido de la imagen hacia el panel oscuro
    scrim = _vgrad_rgba(W, 240, 0, 255, DARK)
    canvas.alpha_composite(scrim, (0, IMG_H - 240))

    draw = ImageDraw.Draw(canvas)

    # 3) divisor + badge VS si hay dos imágenes
    if len(refs) >= 2:
        cx = W // 2
        draw.rectangle([cx - 4, 0, cx + 4, IMG_H], fill=accent_rgb + (255,))
        r = 56
        cy = IMG_H // 2
        draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=DARK + (255,),
                     outline=accent_rgb + (255,), width=8)
        vf = style._font("Anton.ttf", 52)
        vt = "VS"
        vw = draw.textlength(vt, font=vf)
        draw.text((cx - vw / 2, cy - 34), vt, font=vf, fill=WHITE + (255,))

    # 4) BIX abajo a la derecha (solo si el fondo no lo trae ya). Si hay un BIX
    #    generado por Gemini (pose/disfraz del tema) lo usamos; si no, el asset.
    bix_path = bix_override if (bix_override and Path(bix_override).exists()) \
        else style.BIX_COMPANIONS.get(bix_section, style.BIX_DEFAULT)
    if not bix_in_bg and bix_path and Path(bix_path).exists():
        try:
            bix = _crop_to_content(Image.open(bix_path))
            bh = int(IMG_H * 0.62)
            bw = int(bix.width * (bh / bix.height))
            bix = bix.resize((bw, bh), Image.LANCZOS)
            bx, by = W - bw - 24, IMG_H - bh + 26
            shadow = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
            ImageDraw.Draw(shadow).ellipse(
                [bx + bw * 0.12, by + bh * 0.86, bx + bw * 0.9, by + bh * 1.0],
                fill=(0, 0, 0, 120))
            canvas.alpha_composite(shadow.filter(ImageFilter.GaussianBlur(14)))
            canvas.alpha_composite(bix, (bx, by))
        except Exception:
            pass

    # 5) kicker de marca, centrado con líneas
    kf = style._font("Mono.ttf", 30, weight=700)
    kt = " ".join(BRAND.upper())
    kw = draw.textlength(kt, font=kf)
    ky = IMG_H + 30
    draw.text(((W - kw) // 2, ky), kt, font=kf, fill=WHITE + (255,))
    ly = ky + 18
    draw.line([(MARGIN, ly), ((W - kw) // 2 - 26, ly)], fill=WHITE + (200,), width=3)
    draw.line([((W + kw) // 2 + 26, ly), (W - MARGIN, ly)], fill=WHITE + (200,), width=3)

    # 6) headline con acento
    words_colored = _accentize(title.upper().split(), accent_rgb)
    avail_h = H - (IMG_H + 100) - 90
    hf, lines, lh = _fit_lines(draw, words_colored, W - 2 * MARGIN, avail_h)
    y = IMG_H + 96
    for line in lines:
        text = " ".join(w for w, _ in line)
        x = (W - draw.textlength(text, font=hf)) // 2
        for word, col in line:
            draw.text((x, y), word, font=hf, fill=tuple(col) + (255,))
            x += draw.textlength(word + " ", font=hf)
        y += lh

    # 7) footer
    ff = style._font("Mono.ttf", 26, weight=700)
    ft = footer.upper()
    fw = draw.textlength(ft, font=ff)
    draw.text(((W - fw) // 2, H - 64), ft, font=ff, fill=accent_rgb + (255,))

    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    canvas.convert("RGB").save(out_path, quality=93)
    return str(out_path)
