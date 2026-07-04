/* ════════════════════════════════════════════════════════════════
   malo_ia — dynamic content renderer
   Reads public/content.json and builds the "What's new" carousel and
   the navigable sections. No frameworks. Scroll fade-up reveal like the
   landing, and respects prefers-reduced-motion.
   ════════════════════════════════════════════════════════════════ */
(function () {
  "use strict";

  const SECTION_LABELS = {
    guias: "Guides & templates",
    memes: "Videos & memes",
    blog:  "Blog",
    mercado: "Mal Mercado",
  };

  // Tipos que se leen como artículo (abren post.html)
  const isArticle = (t) => t === "blog" || t === "mercado";

  const esc = (s) => String(s == null ? "" : s)
    .replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;");

  function el(html) {
    const t = document.createElement("template");
    t.innerHTML = html.trim();
    return t.content.firstElementChild;
  }

  function sectionPage(cfg, sec) {
    return (cfg.sections && cfg.sections[sec] && cfg.sections[sec].page) || `${sec}.html`;
  }

  // ── Google Analytics 4 (solo si hay ID en site.config.json → analytics.ga4_id) ─
  function track(name, params) { if (window.gtag) window.gtag("event", name, params || {}); }
  function initAnalytics(cfg) {
    const id = cfg.analytics && cfg.analytics.ga4_id;
    if (!id || !/^G-/.test(id)) return;          // sin ID válido, no carga nada
    const s = document.createElement("script");
    s.async = true; s.src = "https://www.googletagmanager.com/gtag/js?id=" + id;
    document.head.appendChild(s);
    window.dataLayer = window.dataLayer || [];
    window.gtag = function () { window.dataLayer.push(arguments); };
    window.gtag("js", new Date());
    window.gtag("config", id);
    // Eventos del embudo (delegados, cubren tarjetas, feed, posts y la landing)
    document.addEventListener("click", (e) => {
      const dl = e.target.closest("a[download]");
      if (dl) return track("download_guide", { link_url: dl.getAttribute("href") });
      const cta = e.target.closest(".lead-cta");
      if (cta) return track("click_lead_cta", { link_url: cta.getAttribute("href") });
      const sb = e.target.closest(".sbtn");
      if (sb) return track("share", { method: (sb.className.match(/sbtn--(\w+)/) || [])[1] || "other" });
      const sec = e.target.closest(".cta-sections a, .section__more");
      if (sec) return track("select_section", { link_url: sec.getAttribute("href") });
    });
  }

  // ── Consentimiento de cookies (GA4 NO carga hasta que aceptan) ──────────────
  function hasGA(cfg) { const id = cfg.analytics && cfg.analytics.ga4_id; return id && /^G-/.test(id); }
  function consentState() { try { return localStorage.getItem("malo_consent"); } catch { return null; } }
  function setConsent(v) { try { localStorage.setItem("malo_consent", v); } catch {} }
  function showConsentBanner(cfg) {
    const bar = el(`
      <div class="cookie-bar" role="dialog" aria-label="Cookie notice">
        <p>We use Google Analytics (cookies) to see how the site is doing. Okay to turn it on?</p>
        <div class="cookie-bar__btns">
          <button class="btn btn--ghost" data-consent="no">Decline</button>
          <button class="btn btn--primary" data-consent="yes">Accept</button>
        </div>
      </div>`);
    document.body.appendChild(bar);
    bar.addEventListener("click", (e) => {
      const b = e.target.closest("[data-consent]");
      if (!b) return;
      setConsent(b.dataset.consent);
      bar.remove();
      if (b.dataset.consent === "yes") initAnalytics(cfg);
    });
  }
  function setupAnalytics(cfg) {
    if (!hasGA(cfg)) return;                    // sin ID, ni banner ni nada
    const c = consentState();
    if (c === "yes") initAnalytics(cfg);        // ya aceptó antes
    else if (c !== "no") showConsentBanner(cfg); // todavía no decidió → preguntar
  }

  // ── Minimal Markdown → HTML (headings, lists, quotes, code, bold/italic/links)
  function mdInline(s) {
    return s
      .replace(/!\[([^\]]*)\]\((\S+?)\)/g, '<img class="prose__img" src="$2" alt="$1">')
      .replace(/`([^`]+)`/g, "<code>$1</code>")
      .replace(/\*\*([^*]+)\*\*/g, "<strong>$1</strong>")
      .replace(/\*([^*]+)\*/g, "<em>$1</em>")
      .replace(/\[([^\]]+)\]\((https?:\/\/[^\s)]+)\)/g, '<a href="$2" target="_blank" rel="noopener">$1</a>');
  }
  function mdToHtml(md) {
    const lines = String(md || "").replace(/\r\n/g, "\n").split("\n");
    const out = []; let i = 0, list = null;
    const closeList = () => { if (list) { out.push(`</${list}>`); list = null; } };
    while (i < lines.length) {
      const ln = lines[i];
      if (/^\s*```/.test(ln)) {
        closeList(); i++; const buf = [];
        while (i < lines.length && !/^\s*```/.test(lines[i])) { buf.push(esc(lines[i])); i++; }
        i++; out.push(`<pre><code>${buf.join("\n")}</code></pre>`); continue;
      }
      let m;
      if ((m = ln.match(/^\s*(#{1,4})\s+(.*)$/))) { closeList(); const lvl = Math.min(Math.max(m[1].length, 2), 3); out.push(`<h${lvl}>${mdInline(esc(m[2]))}</h${lvl}>`); i++; continue; }
      if (/^\s*>\s?/.test(ln)) { closeList(); out.push(`<blockquote>${mdInline(esc(ln.replace(/^\s*>\s?/, "")))}</blockquote>`); i++; continue; }
      if ((m = ln.match(/^\s*[-*]\s+(.*)$/))) { if (list !== "ul") { closeList(); out.push("<ul>"); list = "ul"; } out.push(`<li>${mdInline(esc(m[1]))}</li>`); i++; continue; }
      if ((m = ln.match(/^\s*\d+\.\s+(.*)$/))) { if (list !== "ol") { closeList(); out.push("<ol>"); list = "ol"; } out.push(`<li>${mdInline(esc(m[1]))}</li>`); i++; continue; }
      if (ln.trim() === "") { closeList(); i++; continue; }
      closeList(); const para = [];
      while (i < lines.length && lines[i].trim() !== "" && !/^\s*(#{1,3}\s|[-*]\s|\d+\.\s|>\s?|```)/.test(lines[i])) { para.push(esc(lines[i])); i++; }
      out.push(`<p>${mdInline(para.join(" "))}</p>`);
    }
    closeList();
    return out.join("\n");
  }

  // ── Article share (blog): WhatsApp · Facebook · X · Copy link ───────────────
  function articleShareHTML(item) {
    const url = location.href;
    const txt = item.title;
    const wa = `https://wa.me/?text=${encodeURIComponent(txt + "\n" + url)}`;
    const fb = `https://www.facebook.com/sharer/sharer.php?u=${encodeURIComponent(url)}`;
    const x  = `https://twitter.com/intent/tweet?text=${encodeURIComponent(txt)}&url=${encodeURIComponent(url)}`;
    return [
      `<a class="sbtn sbtn--wa" href="${wa}" target="_blank" rel="noopener">WhatsApp</a>`,
      `<a class="sbtn sbtn--fb" href="${fb}" target="_blank" rel="noopener">Facebook</a>`,
      `<a class="sbtn sbtn--x" href="${x}" target="_blank" rel="noopener">X</a>`,
      `<button class="sbtn sbtn--ig" data-native="${esc(url)}" data-caption="${esc(txt)}">Instagram</button>`,
      `<button class="sbtn sbtn--tt" data-native="${esc(url)}" data-caption="${esc(txt)}">TikTok</button>`,
      `<button class="sbtn sbtn--link" data-native="${esc(url)}" data-caption="${esc(txt)}">Copy link</button>`,
    ].join("");
  }

  // ── Share buttons (WhatsApp · Facebook · X · Instagram · TikTok) ────────────
  // WA/FB/X have web "intent" links. IG/TikTok can't share a link by URL, so
  // they use the phone's native share sheet (navigator.share) and, on desktop,
  // copy the link instead.
  function memeShareHTML(item) {
    const url = item.video_url || location.href;
    const txt = item.summary || item.title;
    const wa = `https://wa.me/?text=${encodeURIComponent(txt + "\n" + url)}`;
    const fb = `https://www.facebook.com/sharer/sharer.php?u=${encodeURIComponent(url)}`;
    const x  = `https://twitter.com/intent/tweet?text=${encodeURIComponent(txt)}&url=${encodeURIComponent(url)}`;
    return [
      `<a class="sbtn sbtn--wa" href="${wa}" target="_blank" rel="noopener">WhatsApp</a>`,
      `<a class="sbtn sbtn--fb" href="${fb}" target="_blank" rel="noopener">Facebook</a>`,
      `<a class="sbtn sbtn--x" href="${x}" target="_blank" rel="noopener">X</a>`,
      `<button class="sbtn sbtn--ig" data-native="${esc(url)}" data-caption="${esc(txt)}">Instagram</button>`,
      `<button class="sbtn sbtn--tt" data-native="${esc(url)}" data-caption="${esc(txt)}">TikTok</button>`,
    ].join("");
  }

  // ── Meme media: the VIDEO plays on the page; if there isn't one, the image ──
  function mediaHTML(item) {
    if (item.video_file) {
      const poster = item.cover ? `poster="${esc(item.cover)}"` : "";
      return `<video class="post__video" controls playsinline preload="metadata" ${poster}><source src="${esc(item.video_file)}"></video>`;
    }
    if (item.cover) return `<div class="post__media"><img src="${esc(item.cover)}" alt="${esc(item.title)}" loading="lazy"></div>`;
    return "";
  }

  // ── 9gag-style post (memes section column) ──────────────────────────────────
  function post(item) {
    const text = item.summary ? `<p class="post__caption">${esc(item.summary)}</p>` : "";
    return el(`
      <article class="post reveal">
        <div class="post__head">
          <span class="card__tag card__tag--memes">${esc(SECTION_LABELS.memes)}</span>
          <h2 class="post__title">${esc(item.title)}</h2>
        </div>
        ${mediaHTML(item)}${text}
        <div class="post__bar">${memeShareHTML(item)}</div>
      </article>`);
  }

  // ── Compact carousel card: just the image + bold title ──────────────────────
  function snap(item, cfg) {
    const href = isArticle(item.type) ? `post.html?id=${encodeURIComponent(item.id)}` : sectionPage(cfg, item.type);
    const cover = item.cover ? `<img class="snap__cover" src="${esc(item.cover)}" alt="${esc(item.title)}" loading="lazy">` : "";
    return el(`
      <a class="snap reveal" href="${esc(href)}" style="--acc:${esc(item.accent || "#e3924f")}">
        ${cover}
        <h3 class="snap__title">${esc(item.title)}</h3>
      </a>`);
  }

  // ── Full card per section type (grids) ──────────────────────────────────────
  function card(item, cfg) {
    const label = SECTION_LABELS[item.type] || item.type;
    const cover = item.cover ? `<img class="card__cover" src="${esc(item.cover)}" alt="${esc(item.title)}" loading="lazy">` : "";
    let actions = "";

    if (item.type === "guias") {
      const dl = item.file ? `<a class="btn btn--primary" href="${esc(item.file)}" download>Download</a>` : "";
      actions = `${dl}<a class="lead-cta" href="${esc(item.cta_url)}" target="_blank" rel="noopener">${esc(item.cta_text)}</a>`;
    } else if (item.type === "memes") {
      actions = memeShareHTML(item);
    } else if (isArticle(item.type)) {
      const label = item.type === "mercado" ? "Leer →" : "Read →";
      actions = `<a class="btn btn--primary" href="post.html?id=${encodeURIComponent(item.id)}">${label}</a>`;
    }

    const text = item.summary ? `<p class="card__text">${esc(item.summary)}</p>` : "";

    return el(`
      <article class="card reveal" style="--acc:${esc(item.accent || "#e3924f")}">
        <span class="card__bar"></span>
        ${cover}
        <div class="card__body">
          <span class="card__tag card__tag--${esc(item.type)}">${esc(label)}</span>
          <h3 class="card__title">${esc(item.title)}</h3>
          ${text}
          <div class="card__actions">${actions}</div>
        </div>
      </article>`);
  }

  // ── Instagram / TikTok: native share sheet, or copy link on desktop ─────────
  function wireActions(root) {
    root.addEventListener("click", async (e) => {
      const nat = e.target.closest("[data-native]");
      if (!nat) return;
      const data = { text: nat.dataset.caption, url: nat.dataset.native || location.href };
      const label = nat.textContent;
      if (navigator.share) { try { await navigator.share(data); } catch {} }
      else {
        try { await navigator.clipboard.writeText(`${data.text}\n${data.url}`); nat.textContent = "Link copied"; }
        catch { nat.textContent = "Couldn't copy"; }
        setTimeout(() => (nat.textContent = label), 1800);
      }
    });
  }

  // ── Fade-up reveal (same language as the landing) ───────────────────────────
  function revealIn(scope) {
    const reduce = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    const els = scope.querySelectorAll(".reveal");
    if (reduce || !("IntersectionObserver" in window)) { els.forEach((x) => x.classList.add("is-in")); return; }
    const io = new IntersectionObserver((entries) => {
      entries.forEach((en) => { if (en.isIntersecting) { en.target.classList.add("is-in"); io.unobserve(en.target); } });
    }, { rootMargin: "0px 0px -8% 0px" });
    els.forEach((x) => io.observe(x));
  }

  // ── Carousel ────────────────────────────────────────────────────────────────
  function buildCarousel(container, items, cfg) {
    const rail = el(`<div class="carousel__rail"></div>`);
    items.forEach((it) => rail.appendChild(snap(it, cfg)));
    const wrap = el(`<div class="carousel"></div>`);
    const prev = el(`<button class="carousel__btn carousel__btn--prev" aria-label="previous">‹</button>`);
    const next = el(`<button class="carousel__btn carousel__btn--next" aria-label="next">›</button>`);
    wrap.append(prev, rail, next);
    container.appendChild(wrap);
    const step = () => Math.min(rail.clientWidth * 0.9, 380);
    prev.onclick = () => rail.scrollBy({ left: -step(), behavior: "smooth" });
    next.onclick = () => rail.scrollBy({ left: step(), behavior: "smooth" });
  }

  // ── Boot ────────────────────────────────────────────────────────────────────
  async function init() {
    const body = document.body;
    const view = body.dataset.view;           // "home" | "section"
    let data;
    try {
      const res = await fetch("public/content.json", { cache: "no-cache" });
      data = await res.json();
    } catch (e) {
      const fb = document.querySelector("[data-fallback]");
      if (fb) fb.innerHTML = `<div class="empty">No content published yet. Run <code>python tools/build.py</code> and push.</div>`;
      return;
    }
    const cfg = data.config || {};
    const items = data.items || [];
    setupAnalytics(cfg);

    if (view === "post") {
      const id = new URLSearchParams(location.search).get("id");
      const item = items.find((x) => x.id === id) || null;
      const root = document.querySelector("#malo-article");
      if (!item) { root.innerHTML = `<div class="empty">Post not found.</div>`; return; }
      document.title = `${item.title} — ${item.type === "mercado" ? "Mal Mercado" : "malo_ia"}`;
      const cover = item.cover ? `<img class="article__cover" src="${esc(item.cover)}" alt="${esc(item.title)}">` : "";
      const meta = [item.date, item.read_min ? `${item.read_min} min read` : ""].filter(Boolean).join(" · ");
      const sources = (item.sources || []).length
        ? `<div class="article__sources"><h3>Sources</h3><ul>${item.sources.map((s) => `<li><a href="${esc(s)}" target="_blank" rel="noopener">${esc(s)}</a></li>`).join("")}</ul></div>` : "";
      root.innerHTML = `
        <p class="section__eyebrow">${esc(meta)}</p>
        <h1 class="article__title">${esc(item.title)}</h1>
        ${cover}
        <div class="prose">${mdToHtml(item.body)}</div>
        ${sources}
        <div class="article__share"><span class="article__sharelabel">Share</span>${articleShareHTML(item)}</div>`;
      // Tus imágenes ORIGINALES, tejidas dentro del artículo (además de la portada Gemini)
      const imgs = item.images || [];
      if (imgs.length) {
        const prose = root.querySelector(".prose");
        const ps = prose.querySelectorAll(":scope > p");
        const fig = (src) => `<figure class="prose__fig"><img src="${esc(src)}" alt="" loading="lazy"></figure>`;
        if (ps.length) {
          const gap = Math.max(1, Math.floor(ps.length / (imgs.length + 1)));
          imgs.forEach((src, i) => {
            const idx = Math.min(ps.length - 1, (i + 1) * gap - 1);
            ps[idx].insertAdjacentHTML("afterend", fig(src));
          });
        } else {
          prose.insertAdjacentHTML("beforeend", imgs.map(fig).join(""));
        }
      }
      wireActions(root);
      return;
    }

    if (view === "section") {
      const sec = body.dataset.section;
      const mine = items.filter((i) => i.type === sec);
      const grid = document.querySelector("#malo-grid");
      if (!mine.length) { grid.innerHTML = `<div class="empty">Nothing here yet. Coming soon!</div>`; return; }
      if (sec === "memes") {                       // memes section = 9gag feed
        grid.className = "feed";
        mine.forEach((it) => grid.appendChild(post(it)));
      } else {                                      // guides / blog = grid
        mine.forEach((it) => grid.appendChild(card(it, cfg)));
      }
      wireActions(grid);
      revealIn(grid);
      return;
    }

    // HOME: "What's new" carousel + a preview of each section
    const car = document.querySelector("#malo-carousel");
    if (car) {
      const max = (cfg.carousel && cfg.carousel.max_items) || 8;
      if (items.length) buildCarousel(car, items.slice(0, max), cfg);
      else car.innerHTML = `<div class="empty">No content yet. Run the engine and push.</div>`;
    }
    const prev = document.querySelector("#malo-previews");
    if (prev) {
      ["mercado", "guias", "memes", "blog"].forEach((sec) => {
        const mine = items.filter((i) => i.type === sec).slice(0, 3);
        if (!mine.length) return;
        const page = sectionPage(cfg, sec);
        const block = el(`
          <section class="section reveal">
            <div class="section__head section__head--row">
              <div>
                <p class="section__eyebrow">section</p>
                <h2 class="section__title">${esc(SECTION_LABELS[sec])}</h2>
              </div>
              <a class="section__more" href="${esc(page)}">View all →</a>
            </div>
            <div class="grid"></div>
          </section>`);
        const grid = block.querySelector(".grid");
        mine.forEach((it) => grid.appendChild(card(it, cfg)));
        prev.appendChild(block);
        wireActions(grid);
      });
    }
    revealIn(document.body);
  }

  if (document.readyState !== "loading") init();
  else document.addEventListener("DOMContentLoaded", init);
})();
