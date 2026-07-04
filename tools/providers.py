"""
providers.py — Claude escribe, Gemini dibuja.
=============================================
Una sola puerta para los dos modelos, con modo MOCK para probar sin keys.

  MOCK=True  -> texto de ejemplo + portada de relleno en estilo malo_ia.
  MOCK=False -> Claude (ANTHROPIC_API_KEY) y Gemini (GEMINI_API_KEY) reales.

Las keys SIEMPRE por variable de entorno. Nunca en el repo.
"""

import os, json, re
from pathlib import Path

import style

# Modo automático por presencia de keys (cada pieza por su lado):
#   - Imágenes con Gemini si hay GEMINI_API_KEY / GOOGLE_API_KEY.
#   - Texto con Claude si hay ANTHROPIC_API_KEY.
#   - Si falta una, esa pieza queda en MOCK.
# MALO_MOCK=1 fuerza todo a MOCK. MALO_REGEN=1 regenera portadas que ya existen.
_GEMINI_KEY = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
_ANTHROPIC_KEY = os.environ.get("ANTHROPIC_API_KEY")
_FORCE_MOCK = os.environ.get("MALO_MOCK", "") in ("1", "true", "True")
_REGEN = os.environ.get("MALO_REGEN", "") in ("1", "true", "True")

TEXT_MOCK = _FORCE_MOCK or not _ANTHROPIC_KEY
IMAGE_MOCK = _FORCE_MOCK or not _GEMINI_KEY

CLAUDE_MODEL = "claude-sonnet-4-6"
GEMINI_IMAGE_MODEL = "gemini-2.5-flash-image"


# ── TEXTO (Claude) ────────────────────────────────────────────────────────────
def _escape_ctrl_in_strings(s):
    """Escapa saltos de línea/tabs/CR que estén DENTRO de un string JSON (causa
    típica de que el JSON de un modelo no parsee con texto largo)."""
    out, instr, esc = [], False, False
    for ch in s:
        if esc:
            out.append(ch); esc = False; continue
        if ch == "\\":
            out.append(ch); esc = True; continue
        if ch == '"':
            instr = not instr; out.append(ch); continue
        if instr and ch in "\n\r\t":
            out.append({"\n": "\\n", "\r": "\\r", "\t": "\\t"}[ch]); continue
        out.append(ch)
    return "".join(out)


def _loads_lenient(raw, mock_fn):
    """Parsea el JSON del modelo de forma tolerante. NUNCA lanza: si todo falla,
    devuelve los campos que pueda rescatar, o el mock."""
    raw = (raw or "").strip()
    if raw.startswith("```"):
        raw = raw[3:]
        if raw[:4].lower() == "json":
            raw = raw[4:]
        if raw.rstrip().endswith("```"):
            raw = raw.rsplit("```", 1)[0]
    a, b = raw.find("{"), raw.rfind("}")
    cand = raw[a:b + 1] if (a != -1 and b > a) else raw
    for attempt in (cand, _escape_ctrl_in_strings(cand)):
        try:
            return json.loads(attempt)
        except Exception:
            pass
    # último recurso: rescatar "clave":"valor" tolerando saltos de línea
    fields = {}
    for m in re.finditer(r'"(\w+)"\s*:\s*"((?:\\.|[^"\\])*)"',
                         _escape_ctrl_in_strings(cand), re.DOTALL):
        try:
            fields[m.group(1)] = json.loads('"' + m.group(2) + '"')
        except Exception:
            fields[m.group(1)] = m.group(2)
    return fields or (mock_fn() if mock_fn else {"_raw": raw})


def write_text(system, prompt, mock_fn):
    """Devuelve un dict (JSON) escrito por Claude. Sin key de Claude usa mock_fn().
    Parseo robusto: nunca rompe el build aunque el modelo devuelva un JSON sucio."""
    if TEXT_MOCK:
        return mock_fn()
    try:
        from anthropic import Anthropic
        client = Anthropic()  # toma ANTHROPIC_API_KEY del entorno
        msg = client.messages.create(
            model=CLAUDE_MODEL, max_tokens=4096, system=system,
            messages=[{"role": "user", "content": prompt}],
        )
        raw = "".join(b.text for b in msg.content if b.type == "text").strip()
        return _loads_lenient(raw, mock_fn)
    except Exception as e:
        print(f"  (Claude falló: {e} — uso texto de relleno)")
        return mock_fn()


# ── IMAGEN (Gemini) ───────────────────────────────────────────────────────────
def make_image(title, section, topic_hint, out_path, references=None, brief=None):
    """
    Genera la portada en out_path. En MOCK dibuja el placeholder de estilo.
    En real le pasa a Gemini el brief (o el de estilo por defecto) + BIX como
    referencia + las imágenes que vos hayas subido (references).
    """
    out_path = Path(out_path)
    # Idempotente: si la portada ya existe, no la regeneramos (rápido y barato
    # a medida que crece el contenido). Forzá con MALO_REGEN=1.
    if out_path.exists() and not _REGEN:
        return str(out_path)
    if IMAGE_MOCK:
        style.make_cover(title, section=section, out_path=str(out_path))
        return str(out_path)

    from io import BytesIO
    from google import genai
    from google.genai import types
    from PIL import Image

    client = genai.Client()  # toma GEMINI_API_KEY / GOOGLE_API_KEY del entorno
    contents = []
    # BIX como referencia de estilo (el compañero)
    refs = list(references or [])
    bix = style.BIX_COMPANIONS.get(section, style.BIX_DEFAULT)
    if Path(bix).exists():
        refs.insert(0, str(bix))
    for r in refs:
        if r and Path(r).exists():
            mime = "image/png" if str(r).lower().endswith(".png") else "image/jpeg"
            contents.append(types.Part.from_bytes(data=Path(r).read_bytes(), mime_type=mime))

    contents.append(brief or style.style_brief(section, topic_hint))
    resp = client.models.generate_content(
        model=GEMINI_IMAGE_MODEL, contents=contents,
        config=types.GenerateContentConfig(response_modalities=["IMAGE"]),
    )
    for part in resp.candidates[0].content.parts:
        inline = getattr(part, "inline_data", None)
        if inline and inline.data:
            out_path.parent.mkdir(parents=True, exist_ok=True)
            Image.open(BytesIO(inline.data)).convert("RGB").save(out_path, quality=92)
            return str(out_path)
    raise RuntimeError("Gemini no devolvió imagen.")


def make_illustration(brief, out_path):
    """Ilustración editorial con Gemini (Nano Banana) a partir de un brief de
    texto. SIN referencias, SIN BIX (es para Mal Mercado, no malo_ia). En MOCK
    (sin GEMINI_API_KEY) devuelve None: el build sigue sin ilustración y el caché
    la incorpora cuando corras con key."""
    out_path = Path(out_path)
    if out_path.exists() and not _REGEN:
        return str(out_path)
    if IMAGE_MOCK:
        return None

    from io import BytesIO
    from google import genai
    from google.genai import types
    from PIL import Image

    client = genai.Client()
    resp = client.models.generate_content(
        model=GEMINI_IMAGE_MODEL, contents=[brief],
        config=types.GenerateContentConfig(response_modalities=["IMAGE"]),
    )
    for part in resp.candidates[0].content.parts:
        inline = getattr(part, "inline_data", None)
        if inline and inline.data:
            out_path.parent.mkdir(parents=True, exist_ok=True)
            Image.open(BytesIO(inline.data)).convert("RGB").save(out_path, quality=92)
            return str(out_path)
    return None


def make_bix(topic_hint, out_path):
    """Genera a BIX en pose/disfraz del tema (Gemini), lo recorta del chroma verde
    y lo guarda como PNG con transparencia. Devuelve la ruta, o None en MOCK
    (ahí el caller usa el cutout estático del asset)."""
    out_path = Path(out_path)
    if out_path.exists() and not _REGEN:
        return str(out_path)
    if IMAGE_MOCK:
        return None

    from io import BytesIO
    from google import genai
    from google.genai import types
    from PIL import Image
    import blog_card

    client = genai.Client()
    contents = []
    bix = style.BIX_DEFAULT
    if Path(bix).exists():
        contents.append(types.Part.from_bytes(data=Path(bix).read_bytes(), mime_type="image/png"))
    contents.append(style.bix_brief(topic_hint))
    resp = client.models.generate_content(
        model=GEMINI_IMAGE_MODEL, contents=contents,
        config=types.GenerateContentConfig(response_modalities=["IMAGE"]),
    )
    for part in resp.candidates[0].content.parts:
        inline = getattr(part, "inline_data", None)
        if inline and inline.data:
            sprite = blog_card.cutout_green(Image.open(BytesIO(inline.data)))
            out_path.parent.mkdir(parents=True, exist_ok=True)
            sprite.save(out_path)
            return str(out_path)
    raise RuntimeError("Gemini no devolvió imagen para BIX.")
