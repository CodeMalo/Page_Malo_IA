"""
mm_cover.py — Portada on-brand de Mal Mercado (sin API, sin BIX).
================================================================
Genera una portada 1200x630 (proporción social/OG) con la identidad
Mal Mercado: negro profundo, verde señal, tipografía grande, el logo y
una "cinta" de cotizaciones decorativa. Cero llamadas a modelos: siempre
funciona y siempre queda en marca. Es la portada base; la ilustración
Gemini y el video HyperFrames se agregan como capas encima después.
"""
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

NEGRO = (11, 13, 16)
NEGRO_2 = (17, 21, 24)
VERDE = (62, 240, 140)
GRIS = (120, 132, 140)
BLANCO = (238, 242, 246)

ROOT = Path(__file__).resolve().parents[1]
LOGO = ROOT / "assets" / "malmercado_logo.png"


def _font(size, bold=True):
    """Busca una fuente del sistema; cae a la default de PIL si no hay."""
    candidatos = [
        r"C:\Windows\Fonts\segoeuib.ttf" if bold else r"C:\Windows\Fonts\segoeui.ttf",
        r"C:\Windows\Fonts\arialbd.ttf" if bold else r"C:\Windows\Fonts\arial.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold
        else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ]
    for c in candidatos:
        if Path(c).exists():
            try:
                return ImageFont.truetype(c, size)
            except Exception:
                pass
    return ImageFont.load_default()


def _wrap(draw, text, font, max_w):
    palabras, lineas, actual = text.split(), [], ""
    for p in palabras:
        prueba = (actual + " " + p).strip()
        if draw.textlength(prueba, font=font) <= max_w:
            actual = prueba
        else:
            if actual:
                lineas.append(actual)
            actual = p
    if actual:
        lineas.append(actual)
    return lineas[:4]


def render(title, out_path, kicker="SEÑAL DEL MERCADO", tickers=None):
    W, H = 1200, 630
    img = Image.new("RGB", (W, H), NEGRO)
    d = ImageDraw.Draw(img)

    # Halo verde suave arriba-derecha (glow radial simulado por círculos)
    for r, a in ((520, 10), (400, 14), (260, 18)):
        cap = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        dc = ImageDraw.Draw(cap)
        dc.ellipse([W - r, -r // 2, W + r, r], fill=(62, 240, 140, a))
        img = Image.alpha_composite(img.convert("RGBA"), cap).convert("RGB")
    d = ImageDraw.Draw(img)

    # Cinta de cotizaciones decorativa (arriba)
    cinta = " · ".join((tickers or ["VOO +0.4%", "NVDA +1.2%", "BTC -0.6%", "AAPL +0.8%",
                                     "SOL +3.4%", "USD/MXN 17.45"]))
    fc = _font(20, bold=False)
    d.rectangle([0, 0, W, 46], fill=NEGRO_2)
    d.text((60, 13), cinta, font=fc, fill=GRIS)
    d.rectangle([0, 46, W, 48], fill=VERDE)

    # Kicker
    fk = _font(24, bold=True)
    d.text((60, 96), kicker.upper(), font=fk, fill=VERDE)

    # Título grande, envuelto
    ft = _font(70, bold=True)
    lineas = _wrap(d, title, ft, W - 120)
    y = 150
    for ln in lineas:
        d.text((60, y), ln, font=ft, fill=BLANCO)
        y += 82

    # Marca abajo-izquierda (logo + wordmark)
    marca_y = H - 90
    if LOGO.exists():
        try:
            lg = Image.open(LOGO).convert("RGBA")
            lg.thumbnail((66, 66))
            img.paste(lg, (60, marca_y - 4), lg)
        except Exception:
            pass
    fm = _font(30, bold=True)
    d.text((140, marca_y), "MAL ", font=fm, fill=BLANCO)
    w_mal = d.textlength("MAL ", font=fm)
    d.text((140 + w_mal, marca_y), "MERCADO", font=fm, fill=VERDE)
    fs = _font(18, bold=False)
    d.text((140, marca_y + 40), "El mercado es ruido. Recibe la señal.", font=fs, fill=GRIS)

    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    img.save(out_path, quality=92)
    return str(out_path)


if __name__ == "__main__":
    render("NVIDIA arrastra a los chips: qué dicen las señales esta semana",
           ROOT / "public" / "media" / "mercado" / "_demo.png")
    print("Demo:", ROOT / "public" / "media" / "mercado" / "_demo.png")
