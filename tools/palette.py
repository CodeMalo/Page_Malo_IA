"""
palette.py — Teoría del color para que el grid tome carácter.
=============================================================
Cada publicación recibe un color de acento que "salta" siguiendo teoría del
color: rotación de tono por la proporción áurea (0.618). Eso da una secuencia
de colores máximamente distintos entre sí pero de la MISMA familia (saturación
y luminosidad fijas), así el grid se ve vivo e intencional, no random.

Determinista y con registro persistente (tools/palette_state.json): cada slug
queda fijado a su color, así un rebuild NO recolorea lo viejo; solo lo nuevo
avanza. NO usa ninguna API key.
"""

import json, colorsys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STATE = ROOT / "tools" / "palette_state.json"

# Arranca en un azul "cool" y rota por la proporción áurea.
BASE_HUE = 0.58            # ~210° (azul)
GOLDEN = 0.6180339887      # conjugado áureo → saltos de tono óptimos
SAT = 0.72                 # saturación fija → todos se sienten familia
LUM = 0.56                 # luminosidad fija


def _load():
    try:
        return json.loads(STATE.read_text(encoding="utf-8"))
    except Exception:
        return {"n": 0, "map": {}}


def _save(s):
    try:
        STATE.write_text(json.dumps(s, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception:
        pass


def _rgb_for(idx):
    h = (BASE_HUE + idx * GOLDEN) % 1.0
    r, g, b = colorsys.hls_to_rgb(h, LUM, SAT)
    return (int(r * 255), int(g * 255), int(b * 255))


def to_hex(rgb):
    return "#%02x%02x%02x" % rgb


def assign(slug):
    """Devuelve (rgb, idx) fijo para ese slug. Lo nuevo avanza la secuencia."""
    s = _load()
    if slug in s["map"]:
        idx = s["map"][slug]
    else:
        idx = s["n"]
        s["map"][slug] = idx
        s["n"] = idx + 1
        _save(s)
    return _rgb_for(idx), idx


def darken(rgb, f=0.45):
    return tuple(int(c * f) for c in rgb)


def mix(rgb, other, t):
    return tuple(int(rgb[i] + (other[i] - rgb[i]) * t) for i in range(3))
