"""
content.py — Lee los items que vos creás.
=========================================
Cada item es una carpeta dentro de content/<seccion>/<slug>/ con un item.md:

    ---
    title: Mi guía de prompts
    date: 2026-06-21
    status: published        # draft = no se publica todavía
    file: guia.pdf           # (guías) el PDF/presentación a ofrecer
    cover_topic: prompts para principiantes   # pista para la portada
    refs:                    # (opcional) imágenes tuyas de referencia
      - refs/captura1.png
    sources:                 # (opcional) links de fuentes
      - https://...
    ---
    Texto libre opcional (markdown). Para blog es el cuerpo; para guías, notas.

No usa PyYAML a propósito: parser mínimo para no depender de nada.
"""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTENT = ROOT / "content"
SECTIONS = ("guias", "memes", "blog")


def _parse_frontmatter(text):
    """Devuelve (meta:dict, body:str). Soporta strings y listas (- item)."""
    meta, body = {}, text
    if text.lstrip().startswith("---"):
        rest = text.lstrip()[3:]
        end = rest.find("\n---")
        if end != -1:
            fm, body = rest[:end], rest[end + 4:]
            key = None
            for line in fm.splitlines():
                if not line.strip():
                    continue
                if line.lstrip().startswith("- ") and key:
                    meta.setdefault(key, [])
                    if isinstance(meta[key], list):
                        meta[key].append(line.lstrip()[2:].strip())
                    continue
                if ":" in line:
                    k, v = line.split(":", 1)
                    key, v = k.strip(), v.strip()
                    if v == "":
                        meta[key] = []          # lista que viene en líneas siguientes
                    else:
                        meta[key] = v.strip('"').strip("'")
    return meta, body.strip()


def load_items(section=None):
    """Lista todos los items (de una sección o de todas)."""
    items = []
    secs = [section] if section else SECTIONS
    for sec in secs:
        base = CONTENT / sec
        if not base.exists():
            continue
        for d in sorted(base.iterdir()):
            md = d / "item.md"
            if not d.is_dir() or not md.exists():
                continue
            meta, body = _parse_frontmatter(md.read_text(encoding="utf-8"))
            meta.setdefault("type", sec)
            items.append({
                "section": sec,
                "slug": d.name,
                "dir": d,
                "meta": meta,
                "body": body,
            })
    return items
