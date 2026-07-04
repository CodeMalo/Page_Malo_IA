"""
mm_reel.py — Reel vertical 9:16 animado por post (Mal Mercado).
==============================================================
Genera un HTML autocontenido por artículo: una pieza de motion design en la
identidad Mal Mercado (negro + verde señal) que anima título, categoría, la
ilustración del post, una cinta de tickers y un cierre con la marca + CTA.

Se GRABA abriendo el HTML en pantalla completa (F11) y capturando con
Win+Alt+R (Game Bar) u OBS a 1080x1920. El ciclo dura ~15s en loop.

Nota: HyperFrames (export MP4 automático) requiere Node.js; cuando esté
instalado se cablea el skill. Esto entrega el reel HOY, sin instalar nada.
"""
import html
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REELS = ROOT / "public" / "reels"


def _plantilla(title, category, summary, tickers, ilustracion, url):
    t = html.escape(title)
    cat = html.escape((category or "MERCADOS").upper())
    sub = html.escape(summary or "")
    cinta = " · ".join(tickers) if tickers else "VOO · NVDA · BTC · AAPL · SOL · USD/MXN"
    # El reel vive en public/reels/; la ilustración en public/media/mercado/ →
    # ruta relativa correcta = quitar el prefijo "public/" y anteponer "../".
    ilus = ("../" + ilustracion[len("public/"):]) if ilustracion and ilustracion.startswith("public/") else (ilustracion or "")
    return f"""<!DOCTYPE html>
<html lang="es"><head><meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Reel — {t}</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@500;700&family=JetBrains+Mono:wght@500;700&display=swap" rel="stylesheet">
<style>
:root{{--neg:#07090d;--verde:#3ef08c;--gris:#8b95a3;--txt:#eef2f6;}}
*{{margin:0;padding:0;box-sizing:border-box}}
body{{background:#000;display:grid;place-items:center;min-height:100vh;font-family:"Space Grotesk",sans-serif}}
.stage{{width:min(56.25vh,100vw);aspect-ratio:9/16;background:var(--neg);position:relative;overflow:hidden;color:var(--txt)}}
.stage::before{{content:"";position:absolute;inset:0;z-index:0;background:
  radial-gradient(420px 320px at 80% 8%,rgba(139,123,255,.16),transparent 70%),
  radial-gradient(520px 380px at 12% 96%,rgba(62,240,140,.12),transparent 70%)}}
.marca-top{{position:absolute;top:5%;left:8%;z-index:3;font-family:"JetBrains Mono",monospace;
  font-size:clamp(11px,1.5vh,15px);letter-spacing:.24em;color:var(--txt)}}
.marca-top b{{color:var(--verde)}}
.cinta{{position:absolute;top:0;left:0;right:0;z-index:2;overflow:hidden;padding:.5rem 0;
  border-bottom:1px solid rgba(255,255,255,.08);opacity:0;animation:aparece .6s ease 1s forwards}}
.cinta div{{display:flex;gap:2rem;width:max-content;white-space:nowrap;animation:desliza 18s linear infinite;
  font-family:"JetBrains Mono",monospace;font-size:clamp(10px,1.3vh,13px);color:var(--gris)}}
@keyframes desliza{{to{{transform:translateX(-50%)}}}}
.ilus{{position:absolute;top:15%;left:0;right:0;height:42%;z-index:1;background-size:cover;background-position:center;
  opacity:0;animation:aparece 1.2s ease .3s forwards;
  -webkit-mask-image:linear-gradient(180deg,transparent,#000 22%,#000 72%,transparent);
  mask-image:linear-gradient(180deg,transparent,#000 22%,#000 72%,transparent)}}
.cuerpo{{position:absolute;top:56%;left:8%;right:8%;z-index:3}}
.cat{{font-family:"JetBrains Mono",monospace;font-size:clamp(11px,1.6vh,15px);letter-spacing:.2em;
  color:var(--verde);opacity:0;animation:sube .7s ease .5s forwards}}
h1{{font-weight:700;font-size:clamp(24px,4.3vh,44px);line-height:1.12;letter-spacing:-.02em;margin:.6rem 0}}
h1 .l{{display:block;overflow:hidden}}
h1 .l span{{display:inline-block;transform:translateY(110%);animation:reveal .9s cubic-bezier(.19,1,.22,1) forwards}}
h1 .l:nth-child(2) span{{animation-delay:.12s}}h1 .l:nth-child(3) span{{animation-delay:.24s}}
h1 .l:nth-child(4) span{{animation-delay:.36s}}
.sub{{color:var(--gris);font-size:clamp(13px,1.9vh,18px);line-height:1.5;opacity:0;animation:sube .8s ease 1s forwards}}
.cierre{{position:absolute;bottom:6%;left:8%;right:8%;z-index:3;display:flex;justify-content:space-between;
  align-items:flex-end;opacity:0;animation:sube .8s ease 1.5s forwards}}
.cierre .m{{font-weight:700;font-size:clamp(16px,2.3vh,24px)}}.cierre .m b{{color:var(--verde)}}
.cierre .cta{{font-family:"JetBrains Mono",monospace;font-size:clamp(10px,1.4vh,13px);color:var(--gris);text-align:right}}
.cierre .cta b{{color:var(--verde);display:block}}
@keyframes reveal{{to{{transform:translateY(0)}}}}
@keyframes sube{{from{{opacity:0;transform:translateY(14px)}}to{{opacity:1;transform:none}}}}
@keyframes aparece{{to{{opacity:1}}}}
@media (prefers-reduced-motion:reduce){{*{{animation:none!important;opacity:1!important}}h1 .l span{{transform:none}}}}
</style></head>
<body>
<div class="stage">
  <div class="cinta"><div>{html.escape(cinta)} · {html.escape(cinta)}</div></div>
  <div class="marca-top">MAL <b>MERCADO</b></div>
  {'<div class="ilus" style="background-image:url(' + html.escape(ilus) + ')"></div>' if ilus else ''}
  <div class="cuerpo">
    <p class="cat">{cat}</p>
    <h1>{''.join(f'<span class="l"><span>{html.escape(w)}</span></span>' for w in _corta(title))}</h1>
    <p class="sub">{sub}</p>
  </div>
  <div class="cierre">
    <span class="m">MAL <b>MERCADO</b></span>
    <span class="cta">El mercado es ruido.<b>Recibe la señal.</b></span>
  </div>
</div>
</body></html>"""


def _corta(title, max_lineas=4):
    """Parte el título en líneas cortas para el reveal cinético."""
    palabras, lineas, act = title.split(), [], ""
    for p in palabras:
        if len((act + " " + p).strip()) <= 18:
            act = (act + " " + p).strip()
        else:
            lineas.append(act)
            act = p
    if act:
        lineas.append(act)
    return lineas[:max_lineas]


def render(card):
    """card = el dict del post (de content.json). Escribe public/reels/<id>.html."""
    ilus = (card.get("images") or [None])[0]
    out = REELS / f"{card['id']}.html"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(_plantilla(
        card["title"], card.get("category", "Mercados"), card.get("summary", ""),
        card.get("tags") or [], ilus, card.get("id")), encoding="utf-8")
    return f"public/reels/{card['id']}.html"


if __name__ == "__main__":
    d = json.loads((ROOT / "public" / "content.json").read_text(encoding="utf-8"))
    for c in [i for i in d["items"] if i["type"] == "mercado"]:
        print("reel:", render(c))
