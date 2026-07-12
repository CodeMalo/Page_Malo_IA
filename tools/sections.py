"""
sections.py — Cada apartado es una función.
===========================================
El motor mira la sección del item y llama a su handler. Cada handler sabe qué
inputs espera ese apartado y devuelve la "tarjeta" lista para content.json.

Para sumar un apartado nuevo en el futuro: escribís una función handle_xxx y la
registrás en HANDLERS. Nada más.

Hoy 'guias' está completo. 'memes' y 'blog' tienen un handler base que ya
publica; los vamos a enriquecer cuando clonemos el flujo.
"""

import json, re, shutil
from pathlib import Path

from PIL import Image
import providers, style, palette, blog_card

ROOT = Path(__file__).resolve().parents[1]
PUBLIC = ROOT / "public"


def _cover_rel(section, slug):
    return f"public/media/{section}/{slug}.png"


def _cta(cfg):
    return cfg.get("lead", {}).get("cta_text", "Get the free guide")


def gen_social(d, kind, title, summary, cfg, content=""):
    """Genera descripciones optimizadas para Facebook e Instagram y las guarda
    como facebook.txt / instagram.txt (para copiar/pegar o mandar por email).
    Es una llamada SEPARADA: recibe el texto YA PUBLICADO (content) para que las
    descripciones reflejen lo que realmente sale en el blog/post.
    Devuelve {'facebook':..., 'instagram':...}."""
    bio = cfg.get("lead", {}).get("bio_link_url", "") or "link in bio"
    def _mock():
        return {
            "facebook": (f"{title}\n\n{summary}\n\nRead the full thing free on our site — and grab "
                         f"our free AI guide for business owners here: {bio}"),
            "instagram": (f"{title}\n\n{summary}\n\nFull post + free guide → link in bio.\n\n"
                          f"#ai #smallbusiness #artificialintelligence #malo_ia #aiforbusiness"),
        }
    soc = providers.write_text(
        system=("You are the malo_ia social copywriter. Audience: small-business owners new to "
                "AI. Warm, plain, no hype, never robotic. Base the posts on the ACTUAL published "
                "text given below — don't invent things it doesn't say. You ALWAYS return a single "
                "valid JSON."),
        prompt=(f"{kind}: {title}\nSummary: {summary}\n"
                f"PUBLISHED text to base the social posts on (this is what readers will see):\n"
                f"{(content or summary)[:5000]}\n"
                f"Free guide (link in bio): {bio}\n\n"
                f'Return ONLY this JSON: {{'
                f'"facebook":"a Facebook post grounded in the published text: 2-4 short friendly '
                f'paragraphs, at most 1-2 emojis, optimized to get clicks, ending by inviting to '
                f'read the full post on the site and to grab the free guide in bio",'
                f'"instagram":"an Instagram caption grounded in the published text: punchy hook, '
                f'short lines, ends pointing to the free guide in bio, then 5-8 relevant hashtags"}}'),
        mock_fn=_mock,
    )
    for k in ("facebook", "instagram"):
        try:
            (d / f"{k}.txt").write_text(soc.get(k, ""), encoding="utf-8")
        except Exception:
            pass
    return soc


# ── GUÍAS / PLANTILLAS ────────────────────────────────────────────────────────
def handle_guias(item, cfg):
    meta, slug, d = item["meta"], item["slug"], item["dir"]
    title = meta.get("title", slug.replace("-", " ").title())
    topic = meta.get("cover_topic", title)

    # 1) Text (Claude or MOCK): pitch + summary + funnel caption
    def _mock():
        return {
            "summary": f"A short, no-nonsense guide on {topic.lower()}.",
            "pitch": (f"Download this template and use it today. {title} explained "
                      f"step by step, with copy-paste examples."),
            "caption": (f"New guide: {title} — free. {_cta(cfg)}. Link in bio."),
        }
    sources = "\n".join(meta.get("sources", []) if isinstance(meta.get("sources"), list) else [])
    txt = providers.write_text(
        system=("You are the malo_ia copywriter: warm, clear, no jargon, no hype, in "
                "English. You ALWAYS return a single valid JSON object, no markdown."),
        prompt=(f"Guide/template titled: {title}\nTopic: {topic}\n"
                f"Sources:\n{sources}\nNotes:\n{item['body'][:1500]}\n\n"
                f'Return ONLY this JSON: {{"summary":"1-2 sentences","pitch":"2-3 sentences '
                f'that invite the reader to download","caption":"a social caption that ends '
                f'by inviting people to the link in bio to grab the free guide"}}'),
        mock_fn=_mock,
    )

    # 2) Portada en estilo malo_ia (BIX de compañero)
    refs = [str(d / r) for r in (meta.get("refs") or []) if (d / r).exists()]
    out_cover = PUBLIC / "media" / "guias" / f"{slug}.png"
    providers.make_image(title, "guias", topic, out_cover, references=refs)

    # 3) El archivo a ofrecer (PDF / presentación) → public/files/
    file_rel = None
    fname = meta.get("file")
    if fname and (d / fname).exists():
        ext = Path(fname).suffix
        dest = PUBLIC / "files" / f"{slug}{ext}"
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(d / fname, dest)
        file_rel = f"public/files/{slug}{ext}"

    return {
        "id": slug, "type": "guias", "title": title,
        "date": meta.get("date", ""),
        "summary": txt.get("summary", ""),
        "pitch": txt.get("pitch", ""),
        "caption": txt.get("caption", ""),
        "cover": _cover_rel("guias", slug),
        "file": file_rel,
        "cta_url": cfg.get("lead", {}).get("free_guide_url", "#"),
        "cta_text": _cta(cfg),
    }


# ── MEMES / VIDEOS ────────────────────────────────────────────────────────────
def handle_memes(item, cfg):
    meta, slug, d = item["meta"], item["slug"], item["dir"]
    title = meta.get("title", slug.replace("-", " ").title())
    topic = meta.get("cover_topic", title)
    lead = cfg.get("lead", {})
    bio = lead.get("bio_link_url", "")
    platforms = meta.get("platforms", []) if isinstance(meta.get("platforms"), list) else []

    # 1) Funnel caption (Claude or MOCK): ALWAYS closes by sending to bio → guide
    def _mock():
        return {
            "summary": f"{title} — watch the clip.",
            "caption": (f"{title}\n\n"
                        f"If AI feels overwhelming, I've got you: a free guide to get "
                        f"started without the mess.\n"
                        f"It's in the link in my bio. Grab it and start today.\n\n"
                        f"#malo_ia #ai #artificialintelligence"),
        }
    txt = providers.write_text(
        system=("You are the malo_ia social copywriter (IG/TikTok): warm, no hype, in "
                "English. You ALWAYS return a single valid JSON object."),
        prompt=(f"Video/meme: {title}\nTopic: {topic}\nNotes: {item['body'][:800]}\n"
                f"Free guide (link in bio): {bio or 'link in bio'}\n\n"
                f'Return ONLY this JSON: {{"summary":"1 sentence for the website card",'
                f'"caption":"a 2-4 line IG/TikTok caption that ALWAYS ends by explicitly '
                f'inviting people to the link in bio to grab the free guide, with 3 to 5 '
                f'hashtags at the end"}}'),
        mock_fn=_mock,
    )

    # 2) Portada: si subiste un thumbnail/frame del video lo usamos; si no, Gemini
    #    genera una en estilo malo_ia (azul, BIX de compañero).
    out_cover = PUBLIC / "media" / "memes" / f"{slug}.png"
    thumb = meta.get("thumbnail")
    if thumb and (d / thumb).exists():
        out_cover.parent.mkdir(parents=True, exist_ok=True)
        try:
            Image.open(d / thumb).convert("RGB").save(out_cover, quality=92)
        except Exception:
            shutil.copy2(d / thumb, out_cover)
    else:
        refs = [str(d / r) for r in (meta.get("refs") or []) if (d / r).exists()]
        providers.make_image(title, "memes", topic, out_cover, references=refs)

    # 3) Video propio (mp4/webm) para reproducir EN la página, si lo subiste.
    video_rel = None
    vfile = meta.get("video")
    if vfile and (d / vfile).exists():
        ext = Path(vfile).suffix.lower()
        dest = PUBLIC / "media" / "memes" / f"{slug}{ext}"
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(d / vfile, dest)
        video_rel = f"public/media/memes/{slug}{ext}"

    # 4) El caption (con el CTA al bio → guía) se guarda SOLO para que vos lo
    #    copies al postear el video. No se muestra en la web (allí va el resumen).
    caption = txt.get("caption", "")
    try:
        (d / "caption.txt").write_text(caption, encoding="utf-8")
    except Exception:
        pass

    # Descripciones FB/IG — llamada separada, con la descripción del video como input
    social = gen_social(d, "video/meme", title, txt.get("summary", ""), cfg, content=item["body"])

    return {
        "id": slug, "type": "memes", "title": title, "date": meta.get("date", ""),
        "summary": txt.get("summary", ""),
        "caption": caption,                 # queda en el JSON por si lo necesitás
        "social": social,
        "cover": _cover_rel("memes", slug),
        "video_file": video_rel,            # mp4 local → se reproduce inline
        "video_url": meta.get("video_url", ""),
        "platforms": platforms,
    }


# ── BLOG ──────────────────────────────────────────────────────────────────────
def handle_blog(item, cfg):
    meta, slug, d = item["meta"], item["slug"], item["dir"]
    title = meta.get("title", slug.replace("-", " ").title())
    topic = meta.get("cover_topic", title)
    sources = meta.get("sources", []) if isinstance(meta.get("sources"), list) else []

    # 1) El post completo (Claude) a partir de tu investigación + fuentes.
    #    En MOCK usa tu investigación cruda como cuerpo (Markdown).
    def _mock():
        body = item["body"] or f"(Pegá tu investigación de Perplexity en el item.md. "
        body += "\n\nEn modo real, Claude la convierte en el post final.)"
        return {"summary": f"{title}: what you need to know, explained calmly.",
                "body": item["body"] or body}
    txt = providers.write_text(
        system=(
            "You are the malo_ia blog writer. Audience: small-business owners with ZERO AI "
            "knowledge — busy, practical, a little intimidated by tech. Voice: warm, "
            "plain-spoken and encouraging, like a friend explaining things over coffee. No "
            "jargon, no hype, never words like 'unlock / leverage / revolutionary'. Never "
            "sound like a robot or generic AI filler. Add REAL, practical value with concrete "
            "examples a business owner can use today. Light, natural SEO: weave the main topic "
            "and related terms in naturally and write a clear, keyword-aware summary — but "
            "readability ALWAYS beats keyword stuffing. Don't invent statistics. "
            "You ALWAYS return a single valid JSON object, no markdown fences."
        ),
        prompt=(
            f"Write a genuinely useful blog post for malo_ia.\n"
            f"Working title: {title}\nTopic: {topic}\n"
            f"Reference links:\n{chr(10).join(sources) or '(none)'}\n"
            f"My research / notes — rewrite, fix, structure and EXPAND this into a real post, "
            f"adding value:\n{item['body'][:6000]}\n\n"
            f'Return ONLY this JSON: {{'
            f'"summary":"a 1-2 sentence hook that also works as an SEO meta description (~155 chars)",'
            f'"body":"the full post in Markdown for total beginners: a short relatable intro, then '
            f'## subheadings, short paragraphs, a bullet list or two and at least one concrete '
            f'example, ending with a short friendly takeaway. Do NOT repeat the title as an H1."}}'
        ),
        mock_fn=_mock,
    )

    body_md = txt.get("body") or item["body"]
    read_min = max(1, round(len(re.findall(r"\w+", body_md)) / 200))

    # 2) Portada (Gemini) usando tus imágenes de referencia + estilo BIX.
    refs = [str(d / r) for r in (meta.get("refs") or []) if (d / r).exists()]
    providers.make_image(title, "blog", topic, PUBLIC / "media" / "blog" / f"{slug}.png", references=refs)

    # 3) Las imágenes ORIGINALES también van al post (además de la portada Gemini):
    #    se copian a public/ y se muestran dentro del artículo.
    images = []
    img_dir = PUBLIC / "media" / "blog" / slug
    for r in (meta.get("refs") or []):
        src = d / r
        if src.exists():
            img_dir.mkdir(parents=True, exist_ok=True)
            dest = img_dir / Path(r).name
            shutil.copy2(src, dest)
            images.append(f"public/media/blog/{slug}/{Path(r).name}")

    # 4) Descripciones FB/IG — LLAMADA SEPARADA, con el post YA ESCRITO como input
    social = gen_social(d, "blog post", title, txt.get("summary", ""), cfg, content=body_md)

    # 5) SEGUNDA imagen: card viral (VS/single + BIX) con el color que le toca a
    #    esta publicación (teoría del color, ver palette.py). Sin API keys.
    accent, _idx = palette.assign(slug)
    ref_paths = [str(d / r) for r in (meta.get("refs") or []) if (d / r).exists()]
    # Si NO hay fotos de referencia, Gemini genera a BIX de PROTAGONISTA (pose
    # dinámica, vertical) como fondo de la card — en vez de un gradiente plano.
    card_bg = None
    bix_override = None
    if not ref_paths:
        bg_path = PUBLIC / "media" / "blog" / f"{slug}-cardbg.png"
        try:
            providers.make_image(title, "blog", topic, bg_path, brief=style.card_brief(topic))
            card_bg = str(bg_path)
        except Exception as e:
            print(f"  (no se pudo generar el fondo de la card: {e})")
    else:
        # Con tus fotos: Gemini genera a BIX en pose/disfraz del tema (recortado)
        try:
            bix_override = providers.make_bix(topic, PUBLIC / "media" / "blog" / f"{slug}-bix.png")
        except Exception as e:
            print(f"  (no se pudo generar BIX del tema: {e})")
    card_rel = None
    try:
        blog_card.render(title, ref_paths, accent,
                         PUBLIC / "media" / "blog" / f"{slug}-card.png",
                         card_bg=card_bg, bix_override=bix_override)
        card_rel = f"public/media/blog/{slug}-card.png"
    except Exception as e:
        print(f"  (no se pudo generar la card: {e})")

    return {
        "id": slug, "type": "blog", "title": title, "date": meta.get("date", ""),
        "summary": txt.get("summary", ""),
        "cover": _cover_rel("blog", slug),
        "card": card_rel,
        "accent": palette.to_hex(accent),
        "body": body_md,
        "images": images,
        "sources": sources,
        "read_min": read_min,
        "social": social,
    }


HANDLERS = {
    "guias": handle_guias,
    "memes": handle_memes,
    "blog":  handle_blog,
}
