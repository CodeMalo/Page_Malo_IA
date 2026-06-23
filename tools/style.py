"""
style.py — La identidad visual de malo_ia en un solo lugar.
==========================================================
Acá vive la paleta, las fuentes y BIX (el compañero). Todo lo que genere el
motor (portadas mock o reales) sale de acá, así nunca se nos escapa el estilo.

BIX no se estampa en todo: acompaña. Aparece como guía donde suma (portadas de
guía, cabeceras), con la misma vibra cálida y de "editor de código" de la landing.
"""

import urllib.request
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageFilter

# ── Paleta (copiada tal cual de styles.css :root) ─────────────────────────────
INK        = (42, 37, 33)     # #2a2521
INK_SOFT   = (107, 97, 87)    # #6b6157
CREAM      = (242, 235, 224)  # #f2ebe0
PANEL      = (251, 248, 242)  # #fbf8f2
ORANGE     = (227, 146, 79)   # #e3924f  acento BIX
BLUE       = (140, 189, 217)  # #8cbdd9  hoodie BIX
YELLOW     = (239, 187, 71)   # #efbb47  pop / cierre
NIGHT      = (22, 33, 46)     # #16212e
BORDER     = (230, 221, 207)  # #e6ddcf

# Acento por sección (para que cada apartado tenga su color, sin salirse de BIX)
SECTION_ACCENT = {
    "guias": YELLOW,
    "memes": BLUE,
    "blog":  ORANGE,
}

# ── BIX, el personaje (ancla para el modo real) ───────────────────────────────
BIX_ANCHOR = (
    "Keep this exact character identical to the reference image: a stylized 3D "
    "toy character with a smooth square orange head, thick black square glasses, "
    "a sky-blue zip hoodie with white front panel and yellow zipper, beige pants, "
    "and white sneakers. Same proportions, same colors, same design. "
)

# Imagen de BIX que se usa como compañero en las portadas mock y como
# referencia de estilo en el modo real. Es un asset que ya vive en el sitio.
ROOT = Path(__file__).resolve().parents[1]
BIX_COMPANIONS = {
    "guias": ROOT / "assets" / "s4_bix_present_16x9.png",   # BIX presentando
    "memes": ROOT / "assets" / "s6_bix_wave_16x9.png",      # BIX saludando
    "blog":  ROOT / "assets" / "s3_bix_hand_16x9.png",      # BIX dando la mano
}
BIX_DEFAULT = ROOT / "assets" / "s1_bix_16x9.png"

# ── Fuentes (se bajan solas la primera vez; si no hay red, usa la del sistema) ─
FONTS = ROOT / "tools" / "_fonts"
FONTS.mkdir(exist_ok=True)
_FONT_URLS = {
    "Bricolage.ttf": "https://raw.githubusercontent.com/google/fonts/main/ofl/bricolagegrotesque/BricolageGrotesque%5Bopsz%2Cwdth%2Cwght%5D.ttf",
    "Inter.ttf":     "https://raw.githubusercontent.com/google/fonts/main/ofl/inter/Inter%5Bopsz%2Cwght%5D.ttf",
    "Mono.ttf":      "https://raw.githubusercontent.com/google/fonts/main/ofl/jetbrainsmono/JetBrainsMono%5Bwght%5D.ttf",
    "Anton.ttf":     "https://raw.githubusercontent.com/google/fonts/main/ofl/anton/Anton-Regular.ttf",
}


def _ensure_fonts():
    for name, url in _FONT_URLS.items():
        p = FONTS / name
        if not p.exists():
            try:
                urllib.request.urlretrieve(url, p)
            except Exception as e:
                print(f"  (no se pudo bajar la fuente {name}: {e} — uso la del sistema)")


def _font(name, size, weight=None):
    _ensure_fonts()
    try:
        f = ImageFont.truetype(str(FONTS / name), size)
        if weight is not None:
            # Las fuentes variables exponen ejes en distinto orden; probamos por
            # nombre (Bold/ExtraBold) y, si no, fijamos el eje 'wght' que toque.
            try:
                axes = f.get_variation_axes()
                vals = [weight if (ax.get("name", b"").decode(errors="ignore").lower() == "weight"
                                   or ax.get("axis", b"") == b"wght") else
                        ax.get("default", 0) for ax in axes]
                f.set_variation_by_axes(vals)
            except Exception:
                try: f.set_variation_by_axes([weight])
                except Exception: pass
        return f
    except Exception:
        return ImageFont.load_default()


# ── Helpers de dibujo ─────────────────────────────────────────────────────────
def _vgrad(w, h, top, bot):
    base = Image.new("RGB", (1, h)); px = base.load()
    for y in range(h):
        t = y / max(h - 1, 1)
        px[0, y] = tuple(int(top[i] + (bot[i] - top[i]) * t) for i in range(3))
    return base.resize((w, h))


def _wrap(draw, text, font, max_w):
    words, lines, cur = text.split(), [], []
    for word in words:
        test = " ".join(cur + [word])
        if cur and draw.textlength(test, font=font) > max_w:
            lines.append(" ".join(cur)); cur = [word]
        else:
            cur.append(word)
    if cur: lines.append(" ".join(cur))
    return lines


def _bix_companion(section):
    path = BIX_COMPANIONS.get(section, BIX_DEFAULT)
    if not Path(path).exists():
        path = BIX_DEFAULT
    try:
        return Image.open(path).convert("RGBA")
    except Exception:
        return None


# ── Portada en estilo malo_ia (modo MOCK) ─────────────────────────────────────
def make_cover(title, section="guias", kicker=None, size=(1280, 720), out_path=None):
    """
    Dibuja una portada 16:9 con la vibra de la landing: fondo crema, ventana de
    'editor de código' con sus puntitos, acento de la sección y BIX de compañero
    asomándose en la esquina. Es el placeholder del modo MOCK; en modo real esto
    lo reemplaza Gemini con el mismo brief de estilo.
    """
    W, H = size
    accent = SECTION_ACCENT.get(section, ORANGE)
    kicker = (kicker or section).lower()

    canvas = _vgrad(W, H, PANEL, CREAM).convert("RGBA")
    d = ImageDraw.Draw(canvas)

    # marco de "editor"
    m = int(W * 0.055)
    d.rounded_rectangle([m, m, W - m, H - m], radius=22, fill=PANEL + (255,),
                        outline=BORDER + (255,), width=2)
    # barra superior con los 3 puntitos (naranja / azul / amarillo)
    bar_y = m + 46
    d.line([(m, bar_y), (W - m, bar_y)], fill=BORDER + (255,), width=2)
    for i, c in enumerate((ORANGE, BLUE, YELLOW)):
        d.ellipse([m + 26 + i * 24, m + 18, m + 26 + i * 24 + 13, m + 31],
                  fill=c + (255,))
    d.text((m + 120, m + 16), f"malo_ia · {section}", font=_font("Mono.ttf", 22),
           fill=INK_SOFT + (255,))

    # bloque de acento (la "barra de color" de la sección)
    pad = m + 56
    d.rounded_rectangle([pad, bar_y + 46, pad + 70, bar_y + 58], radius=6,
                        fill=accent + (255,))
    # kicker mono
    d.text((pad, bar_y + 74), f"// {kicker}", font=_font("Mono.ttf", 26),
           fill=INK_SOFT + (255,))

    # título display, con palabras de acento simuladas (primera línea remarcada)
    tf = _font("Bricolage.ttf", 70, weight=800)
    max_w = int(W * 0.62)
    lines = _wrap(d, title, tf, max_w)[:4]
    y = bar_y + 120
    for i, ln in enumerate(lines):
        d.text((pad, y), ln, font=tf, fill=(INK if i else INK) + (255,))
        y += int(70 * 1.06)
    # subrayado de acento bajo la primera línea
    if lines:
        w0 = int(d.textlength(lines[0], font=tf))
        d.rounded_rectangle([pad, bar_y + 120 + int(70 * 1.06) - 6,
                             pad + min(w0, max_w), bar_y + 120 + int(70 * 1.06)],
                            radius=4, fill=accent + (160,))

    # BIX compañero asomándose por la derecha
    bix = _bix_companion(section)
    if bix is not None:
        bw = int(W * 0.30)
        bh = int(bix.height * (bw / bix.width))
        bix = bix.resize((bw, bh), Image.LANCZOS)
        shadow = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
        sd = ImageDraw.Draw(shadow)
        sx, sy = W - m - bw + int(bw * 0.10), H - m - bh + int(bh * 0.06)
        sd.ellipse([sx + bw * 0.18, sy + bh * 0.82, sx + bw * 0.86, sy + bh * 0.98],
                   fill=(0, 0, 0, 60))
        shadow = shadow.filter(ImageFilter.GaussianBlur(10))
        canvas = Image.alpha_composite(canvas, shadow)
        canvas.alpha_composite(bix, (sx, sy))

    canvas = canvas.convert("RGB")
    if out_path:
        Path(out_path).parent.mkdir(parents=True, exist_ok=True)
        canvas.save(out_path, quality=92)
    return canvas


def card_brief(topic_hint=""):
    """Brief para la SEGUNDA imagen (card viral) cuando NO hay fotos de referencia:
    BIX de protagonista, pose dinámica, vertical, con el tercio inferior despejado
    para el texto."""
    return (
        f"{BIX_ANCHOR}"
        f"Dynamic vertical hero of BIX as the STAR of the scene: confident, expressive, "
        f"energetic pose, reacting to the topic, looking toward the viewer. Cinematic soft "
        f"3D toy render, warm cream-to-peach background with depth and soft bokeh, friendly "
        f"dramatic lighting, a few floating themed props around him. Keep the LOWER THIRD "
        f"darker and simple (room for a headline). Tall 4:5 vertical composition. "
        f"Topic/context: {topic_hint}. No text, no letters, no logos."
    )


def bix_brief(topic_hint=""):
    """Brief para generar a BIX en POSE/DISFRAZ según el tema, sobre fondo chroma
    verde para poder recortarlo y pegarlo sobre tus fotos (VS/single)."""
    return (
        f"{BIX_ANCHOR}"
        f"Show BIX full body, expressive, in a POSE and a small COSTUME, prop or gesture "
        f"that reacts to the topic (dress him up / give him an accessory that fits it). "
        f"Keep him 100% recognizable as the same character. Soft 3D toy render, consistent "
        f"lighting. He is FLOATING with empty space around him — NO ground, NO floor, NO "
        f"shadow, NO reflection under or behind him. BACKGROUND: one perfectly flat, uniform, "
        f"solid chroma-key GREEN (#00ee00) that fills the ENTIRE frame edge to edge (including "
        f"under and behind him) and NOTHING else, so he can be cut out cleanly. Center him "
        f"with margin around. Topic/context: {topic_hint}. No text, no letters."
    )


def style_brief(section, topic_hint=""):
    """Brief de estilo que se le pasa a Gemini en modo real (para que pegue con la web)."""
    accent = {"guias": "warm yellow", "memes": "sky blue", "blog": "warm orange"}.get(section, "warm orange")
    return (
        f"{BIX_ANCHOR}"
        f"Editorial cover illustration in the 'malo_ia' brand style: warm cream paper "
        f"background (#f2ebe0), soft 3D toy aesthetic, cozy and friendly, subtle 'code "
        f"editor window' framing, {accent} accent. BIX appears as a friendly companion/"
        f"guide, not the main subject. Clean, lots of breathing room, 16:9. "
        f"Topic: {topic_hint}. No text, no letters in the image."
    )
