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

    import os, hashlib
    regen = os.environ.get("MALO_REGEN", "") in ("1", "true", "True")
    lead_sig = json.dumps(cfg.get("lead", {}), sort_keys=True)

    def _item_hash(it):
        h = hashlib.sha256()
        h.update((it["dir"] / "item.md").read_bytes())
        for f in sorted(it["dir"].glob("*")):
            if f.is_file() and f.name not in ("item.md", ".cache.json"):
                h.update(f"{f.name}:{f.stat().st_size}".encode())
        h.update(lead_sig.encode())
        return h.hexdigest()[:16]

    today = datetime.now().strftime("%Y-%m-%d")
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
        # Caché: si el item no cambió, reusamos lo generado (no re-llama a Claude/
        # Gemini ni pisa texto real). Forzá regeneración con MALO_REGEN=1.
        # Generamos/cacheamos SIEMPRE (así lo programado queda pre-renderizado y el
        # build diario lo puede publicar sin keys ni pisar nada).
        cache_f = it["dir"] / ".cache.json"
        ih = _item_hash(it)
        card = None
        if cache_f.exists() and not regen:
            try:
                c = json.loads(cache_f.read_text(encoding="utf-8"))
                if c.get("hash") == ih:
                    card = c.get("card")
            except Exception:
                pass
        if card is None:
            print(f"  → {it['section']}/{it['slug']} (generando)")
            card = handler(it, cfg)
            card.setdefault("accent", palette.to_hex(palette.assign(card["id"])[0]))
            try:
                cache_f.write_text(json.dumps({"hash": ih, "card": card}, ensure_ascii=False), encoding="utf-8")
            except Exception:
                pass
        # Calendario: solo APARECE en el sitio si la fecha ya llegó.
        pub = str(meta.get("publish", "")).strip()
        if pub and pub > today:
            print(f"  · {it['section']}/{it['slug']} — programado para {pub} (listo, esperando)")
            continue
        print(f"  ✓ {it['section']}/{it['slug']}")
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
