"""
build.py — El motor. Corré esto y la página se actualiza.
=========================================================
    cd malo-ia-site
    python tools/build.py            # modo MOCK (sin keys, para probar)
    MALO_REAL=1 python tools/build.py   # modo real (Claude + Gemini)

Qué hace:
  1. Lee tu site.config.json.
  2. Recorre content/<seccion>/<slug>/ y arma cada item con su handler.
  3. Genera lo que falte (portada con BIX, textos, copia de PDFs).
  4. Escribe public/content.json → la página lo lee y se arma sola.

Después: git add -A && git commit -m "nuevo contenido" && git push
"""

import json, sys
from datetime import datetime, timezone
from pathlib import Path

# La consola de Windows usa cp1252 y rompe con acentos/flechas. Forzamos UTF-8.
try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass

sys.path.insert(0, str(Path(__file__).resolve().parent))  # para importar los módulos de tools/

import content, sections, providers, palette

ROOT = Path(__file__).resolve().parents[1]


def main():
    cfg = json.loads((ROOT / "site.config.json").read_text(encoding="utf-8"))
    txt = "MOCK" if providers.TEXT_MOCK else "Claude"
    img = "MOCK" if providers.IMAGE_MOCK else "Gemini"
    print(f"== build malo-ia-site · texto={txt} · imágenes={img} ==")

    items = content.load_items()
    cards = []
    for it in items:
        meta = it["meta"]
        if str(meta.get("status", "published")).lower() == "draft":
            print(f"  · {it['section']}/{it['slug']} — draft, salteado")
            continue
        handler = sections.HANDLERS.get(it["section"])
        if not handler:
            print(f"  ! sección desconocida: {it['section']}")
            continue
        print(f"  → {it['section']}/{it['slug']}")
        card = handler(it, cfg)
        # color de teoría del color para CADA publicación (así el grid salta y
        # toma carácter). Estable por slug; el blog ya trae el suyo.
        card.setdefault("accent", palette.to_hex(palette.assign(card["id"])[0]))
        cards.append(card)

    # más nuevo primero (por fecha; si empata, por slug)
    cards.sort(key=lambda c: (c.get("date", ""), c.get("id", "")), reverse=True)

    out = {
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "config": cfg,
        "items": cards,
    }
    dest = ROOT / "public" / "content.json"
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nListo: {len(cards)} item(s) → {dest.relative_to(ROOT)}")
    print("Ahora: git add -A && git commit -m \"nuevo contenido\" && git push")


if __name__ == "__main__":
    main()
