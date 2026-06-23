"""
new_item.py — Crea la carpeta de un item nuevo, ya con su plantilla.
====================================================================
    python tools/new_item.py guias "Mi guía de prompts"
    python tools/new_item.py memes "El meme del lunes"
    python tools/new_item.py blog  "Qué es un agente de IA"

Crea content/<seccion>/<fecha-slug>/item.md listo para completar.
"""

import sys, re
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

TEMPLATES = {
    "guias": """---
title: {title}
date: {date}
status: draft
cover_topic: {title}
file: guia.pdf
refs:
sources:
---
Notas internas para la portada/copy (no se publican tal cual).
Poné el PDF o la presentación en esta misma carpeta y nombralo igual que 'file'.
""",
    "memes": """---
title: {title}
date: {date}
status: draft
cover_topic: {title}
video:
video_url:
platforms:
  - instagram
  - tiktok
thumbnail:
refs:
---
Descripción / contexto del meme o video (lo usa Claude para el caption).
- 'video': (opcional) un .mp4 en esta carpeta → se reproduce EN la página.
- 'video_url': el link al video publicado (TikTok/IG/YT), usado para compartir.
- 'thumbnail': (opcional) imagen del meme / frame para mostrar si no hay 'video'.
  Si dejás los dos vacíos, Gemini genera una portada en estilo malo_ia.
""",
    "blog": """---
title: {title}
date: {date}
status: draft
cover_topic: {title}
sources:
refs:
---
Acá va tu investigación (Perplexity), el material y las ideas.
Claude lo usa para escribir el post final.
""",
}


def slugify(s):
    s = re.sub(r"[^\w\s-]", "", s.lower()).strip()
    return re.sub(r"[\s_]+", "-", s)[:48]


def main():
    if len(sys.argv) < 3 or sys.argv[1] not in TEMPLATES:
        print("Uso: python tools/new_item.py <guias|memes|blog> \"Título\"")
        sys.exit(1)
    section, title = sys.argv[1], " ".join(sys.argv[2:])
    today = date.today().isoformat()
    slug = f"{today}-{slugify(title)}"
    d = ROOT / "content" / section / slug
    if d.exists():
        print(f"Ya existe: {d}"); sys.exit(1)
    d.mkdir(parents=True)
    (d / "item.md").write_text(TEMPLATES[section].format(title=title, date=today), encoding="utf-8")
    print(f"Creado: {(d / 'item.md').relative_to(ROOT)}")
    print("Completalo, cambiá status a 'published' y corré: python tools/build.py")


if __name__ == "__main__":
    main()
