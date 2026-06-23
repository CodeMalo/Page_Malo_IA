/* ════════════════════════════════════════════════════════════════
   Malo IA — animaciones de scroll (GSAP + ScrollTrigger)
   Todo es progresivo: si algo falla o el usuario pide menos
   movimiento, la página se ve bien igual (estática).
   ════════════════════════════════════════════════════════════════ */

(function () {
  const reduce = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  const hasGSAP = window.gsap && window.ScrollTrigger;

  // Sin GSAP o con movimiento reducido: mostramos todo y salimos.
  if (!hasGSAP || reduce) {
    document.querySelectorAll('[data-anim]').forEach(el => el.classList.add("is-in"));
    return;
  }

  gsap.registerPlugin(ScrollTrigger);

  /* ── Revelados suaves (eyebrows, títulos, figuras) ── */
  gsap.utils.toArray('[data-anim="up"]').forEach(el => {
    gsap.fromTo(el, { y: 26, opacity: 0 }, {
      y: 0, opacity: 1, duration: 0.7, ease: "power2.out",
      scrollTrigger: { trigger: el, start: "top 85%" }
    });
  });

  /* ── Hero: entrada del editor al cargar ── */
  const editor = document.querySelector('[data-anim="hero-editor"]');
  if (editor) {
    gsap.fromTo(editor, { y: 30, opacity: 0, scale: 0.985 },
      { y: 0, opacity: 1, scale: 1, duration: 0.9, ease: "power3.out", delay: 0.1 });
  }

  /* ── Parallax de fondos (se mueven más lento que el scroll) ── */
  gsap.utils.toArray('[data-parallax]').forEach(bg => {
    gsap.fromTo(bg, { yPercent: -8 }, {
      yPercent: 8, ease: "none",
      scrollTrigger: { trigger: bg.closest(".scene"), start: "top bottom", end: "bottom top", scrub: true }
    });
  });

  /* ── S2 · El ruido: parallax suave SIN pin (el scroll fluye normal) ── */
  const noise = document.querySelector('[data-pin="noise"]');
  if (noise) {
    const bg = noise.querySelector('[data-depth="bg"]');
    const char = noise.querySelector('[data-depth="char"]');
    const copy = noise.querySelector('.copy');
    if (bg) gsap.fromTo(bg, { yPercent: -5, scale: 1.06 }, {
      yPercent: 5, ease: "none",
      scrollTrigger: { trigger: "#s2", start: "top bottom", end: "bottom top", scrub: true }
    });
    if (char) gsap.fromTo(char, { scale: 0.9, opacity: 0.6, y: 18 }, {
      scale: 1, opacity: 1, y: 0, ease: "power1.out",
      scrollTrigger: { trigger: "#s2", start: "top 78%", end: "center center", scrub: 1 }
    });
    if (copy) gsap.fromTo(copy, { opacity: 0, y: 22 }, {
      opacity: 1, y: 0, ease: "power1.out",
      scrollTrigger: { trigger: "#s2", start: "top 72%", end: "center center", scrub: 1 }
    });
  }

  /* ── S4 · Lo que aprendes: scroll horizontal de tarjetas ── */
  const track = document.querySelector('[data-track]');
  if (track) {
    const distance = () => track.scrollWidth - window.innerWidth + 40;
    gsap.to(track, {
      x: () => -distance(), ease: "none",
      scrollTrigger: {
        trigger: "#s4", start: "top top", end: () => "+=" + distance(),
        pin: true, scrub: 1, invalidateOnRefresh: true
      }
    });
  }

  /* ── S5 · El cambio: wipe que revela el "después" ── */
  const ba = document.querySelector('[data-beforeafter]');
  if (ba) {
    gsap.fromTo(ba.querySelector('.ba--after'),
      { clipPath: "inset(0 0 0 100%)" },
      { clipPath: "inset(0 0 0 0%)", ease: "none",
        scrollTrigger: { trigger: "#s5", start: "top 70%", end: "center center", scrub: 1 } });
  }

  /* Recalcular medidas cuando todo cargó (imágenes incluidas) */
  window.addEventListener("load", () => ScrollTrigger.refresh());
})();
