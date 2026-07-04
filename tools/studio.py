"""
studio.py — malo_ia · estudio de contenido (interfaz)
=====================================================
Una ventanita para subir contenido SIN tocar archivos a mano.

  1) Elegís el apartado: Guías / Videos-Memes / Blog.
  2) Completás los datos y seleccionás los archivos:
       - Memes : pegás el link del video O seleccionás el archivo (video/imagen) + descripción.
       - Guías : seleccionás el PDF/presentación + descripción.
       - Blog  : varias imágenes + varios links de referencia + tu investigación.
  3) Click en "Crear y generar":
       - Arma el item, copia los archivos, genera la portada con Gemini y
         reescribe el texto con Claude, y deja todo listo en public/.
  4) Subís a GitHub con el comando que te muestra abajo.

Correr:   python tools/studio.py
Las API keys se escriben en la ventana y se usan SOLO para esa corrida.
NUNCA se guardan en ningún archivo del proyecto.
"""

import os, re, sys, shutil, subprocess, threading
from datetime import date
from pathlib import Path

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext

SECTIONS = [("Guías y plantillas", "guias"), ("Videos y memes", "memes"), ("Blog", "blog")]
PLATFORMS = ["instagram", "tiktok", "youtube", "facebook"]
VIDEO_EXT = (".mp4", ".mov", ".webm", ".m4v")

# colores de la marca (para que la ventana respire malo_ia)
CREAM, INK, ORANGE, PANEL = "#f2ebe0", "#2a2521", "#e3924f", "#fbf8f2"


def slugify(s):
    s = re.sub(r"[^\w\s-]", "", s.lower()).strip()
    return re.sub(r"[\s_]+", "-", s)[:48] or "item"


class Studio(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("malo_ia · estudio de contenido")
        self.configure(bg=CREAM)
        self.geometry("760x820")
        self.minsize(620, 560)                 # se adapta al tamaño de su ventana
        self.ROOT = self._resolve_root()       # portátil: corre desde cualquier lado
        self.CONTENT = self.ROOT / "content"
        self.section = tk.StringVar(value="guias")
        self.files = {}            # archivos seleccionados (rutas absolutas)
        self.plat_vars = {}
        self._build()

    def _resolve_root(self):
        """Encuentra la carpeta del sitio (la que tiene site.config.json)."""
        env = os.environ.get("MALO_SITE", "").strip()
        if env and (Path(env) / "site.config.json").exists():
            return Path(env)
        here = Path(__file__).resolve().parents[1]
        if (here / "site.config.json").exists():
            return here
        messagebox.showinfo("Elegí la carpeta del sitio",
                            "Seleccioná la carpeta 'malo-ia-site' (la que tiene site.config.json).")
        chosen = filedialog.askdirectory(title="Carpeta del sitio malo-ia-site")
        if chosen and (Path(chosen) / "site.config.json").exists():
            return Path(chosen)
        if chosen:
            messagebox.showwarning("Carpeta inválida",
                                   "Esa carpeta no tiene site.config.json. Uso la ubicación por defecto.")
        return here

    # ── UI ────────────────────────────────────────────────────────────────────
    def _build(self):
        pad = {"padx": 14, "pady": 4}
        wrap = tk.Frame(self, bg=CREAM); wrap.pack(fill="both", expand=True, padx=8, pady=8)

        tk.Label(wrap, text="› malo_ia · estudio de contenido", bg=CREAM, fg=INK,
                 font=("Consolas", 15, "bold")).pack(anchor="w", **pad)

        # Keys
        keys = tk.LabelFrame(wrap, text="API keys (no se guardan)", bg=CREAM, fg=INK)
        keys.pack(fill="x", **pad)
        self.gemini = self._entry(keys, "GEMINI_API_KEY (imágenes):", os.environ.get("GEMINI_API_KEY", ""), show="•")
        self.claude = self._entry(keys, "ANTHROPIC_API_KEY (texto/blog):", os.environ.get("ANTHROPIC_API_KEY", ""), show="•")

        # Email del pack social (opcional) — pide las credenciales, NO se guardan
        mail = tk.LabelFrame(wrap, text="Email del pack social (opcional · no se guarda)", bg=CREAM, fg=INK)
        mail.pack(fill="x", **pad)
        self.gmail_user = self._entry(mail, "GMAIL_USER:", os.environ.get("GMAIL_USER", ""))
        self.gmail_pass = self._entry(mail, "GMAIL_APP_PASSWORD:", os.environ.get("GMAIL_APP_PASSWORD", ""), show="•")
        self.email_to = self._entry(mail, "EMAIL_DESTINO:", os.environ.get("EMAIL_DESTINO", ""))
        self.email_var = tk.BooleanVar(value=False)
        tk.Checkbutton(mail, text="Enviarme el pack (captions FB/IG + imágenes) al generar",
                       variable=self.email_var, bg=CREAM, fg=INK, selectcolor=PANEL,
                       activebackground=CREAM).pack(anchor="w", padx=10, pady=2)

        # Apartado
        sec = tk.Frame(wrap, bg=CREAM); sec.pack(fill="x", **pad)
        tk.Label(sec, text="Apartado:", bg=CREAM, fg=INK, font=("Segoe UI", 10, "bold")).pack(side="left")
        for label, val in SECTIONS:
            tk.Radiobutton(sec, text=label, variable=self.section, value=val, bg=CREAM, fg=INK,
                           selectcolor=PANEL, activebackground=CREAM,
                           command=self._refresh_section).pack(side="left", padx=6)

        # Comunes
        self.title_e = self._entry(wrap, "Título:", "")
        self.topic_e = self._entry(wrap, "Tema para la portada (opcional):", "")
        self.publish_e = self._entry(wrap, "Publicar el (opcional, AAAA-MM-DD):", "")

        tk.Label(wrap, text="Descripción / investigación:", bg=CREAM, fg=INK).pack(anchor="w", padx=14)
        self.body_t = scrolledtext.ScrolledText(wrap, height=6, font=("Segoe UI", 10))
        self.body_t.pack(fill="x", padx=14, pady=4)

        # Frame específico por apartado
        self.specific = tk.LabelFrame(wrap, text="Datos del apartado", bg=CREAM, fg=INK)
        self.specific.pack(fill="x", **pad)

        # Acciones
        actions = tk.Frame(wrap, bg=CREAM); actions.pack(fill="x", **pad)
        self.publish = tk.BooleanVar(value=True)
        tk.Checkbutton(actions, text="Publicar ya (si no, queda en borrador)", variable=self.publish,
                       bg=CREAM, fg=INK, selectcolor=PANEL, activebackground=CREAM).pack(side="left")
        tk.Button(actions, text="Abrir carpeta del sitio", command=self._open_folder).pack(side="right", padx=4)
        self.go_btn = tk.Button(actions, text="Crear y generar", command=self._on_go,
                                bg=INK, fg=CREAM, font=("Segoe UI", 10, "bold"), padx=12)
        self.go_btn.pack(side="right", padx=4)

        # Log
        tk.Label(wrap, text="Salida:", bg=CREAM, fg=INK).pack(anchor="w", padx=14)
        self.log = scrolledtext.ScrolledText(wrap, height=9, font=("Consolas", 9), bg="#1c1c20", fg="#e8e8ea")
        self.log.pack(fill="both", expand=True, padx=14, pady=4)

        self._refresh_section()

    def _entry(self, parent, label, value="", show=None):
        f = tk.Frame(parent, bg=parent["bg"]); f.pack(fill="x", padx=10, pady=3)
        tk.Label(f, text=label, bg=parent["bg"], fg=INK, width=28, anchor="w").pack(side="left")
        e = tk.Entry(f, show=show); e.insert(0, value); e.pack(side="left", fill="x", expand=True)
        return e

    def _file_row(self, parent, label, key, multiple=False):
        f = tk.Frame(parent, bg=parent["bg"]); f.pack(fill="x", padx=10, pady=4)
        lbl = tk.Label(f, text="(ninguno)", bg=parent["bg"], fg="#6b6157", anchor="w")
        def pick():
            if multiple:
                paths = filedialog.askopenfilenames()
                if paths:
                    self.files[key] = list(paths)
                    lbl.config(text=f"{len(paths)} archivo(s)")
            else:
                p = filedialog.askopenfilename()
                if p:
                    self.files[key] = p
                    lbl.config(text=Path(p).name)
        tk.Button(f, text=label, command=pick).pack(side="left")
        lbl.pack(side="left", padx=8)

    def _refresh_section(self):
        for w in self.specific.winfo_children():
            w.destroy()
        self.files.clear()
        sec = self.section.get()
        if sec == "memes":
            self.video_url_e = self._entry(self.specific, "Link del video (TikTok/IG/YT):", "")
            self._file_row(self.specific, "Seleccionar video o imagen…", "meme")
            pf = tk.Frame(self.specific, bg=CREAM); pf.pack(fill="x", padx=10, pady=4)
            tk.Label(pf, text="Plataformas:", bg=CREAM, fg=INK).pack(side="left")
            self.plat_vars = {}
            for p in PLATFORMS:
                v = tk.BooleanVar(value=(p in ("instagram", "tiktok")))
                self.plat_vars[p] = v
                tk.Checkbutton(pf, text=p, variable=v, bg=CREAM, fg=INK, selectcolor=PANEL,
                               activebackground=CREAM).pack(side="left")
        elif sec == "guias":
            self._file_row(self.specific, "Seleccionar PDF / presentación…", "guide")
        elif sec == "blog":
            self._file_row(self.specific, "Agregar imágenes (varias)…", "images", multiple=True)
            tk.Label(self.specific, text="Links de referencia (uno por línea):", bg=CREAM, fg=INK).pack(anchor="w", padx=10)
            self.sources_t = scrolledtext.ScrolledText(self.specific, height=4, font=("Segoe UI", 10))
            self.sources_t.pack(fill="x", padx=10, pady=4)

    # ── Lógica ──────────────────────────────────────────────────────────────────
    def _logln(self, s):
        self.log.insert("end", s + "\n"); self.log.see("end"); self.update_idletasks()

    def _open_folder(self):
        try:
            os.startfile(self.ROOT)            # Windows
        except Exception:
            self._logln(f"Carpeta: {self.ROOT}")

    def _build_md(self, section, slug, data, files):
        L = ["---", f"title: {data['title']}", f"date: {date.today().isoformat()}",
             f"status: {'published' if self.publish.get() else 'draft'}",
             f"cover_topic: {data['topic'] or data['title']}"]
        if data.get("publish"):
            L.append(f"publish: {data['publish']}")
        if section == "memes":
            if data["video_url"]: L.append(f"video_url: {data['video_url']}")
            if files.get("video"): L.append(f"video: {files['video']}")
            if files.get("thumbnail"): L.append(f"thumbnail: {files['thumbnail']}")
            L.append("platforms:")
            for p, v in self.plat_vars.items():
                if v.get():
                    L.append(f"  - {p}")
        elif section == "guias":
            if files.get("file"): L.append(f"file: {files['file']}")
        elif section == "blog":
            L.append("sources:")
            for s in data["sources"]:
                L.append(f"  - {s}")
            L.append("refs:")
            for r in files.get("refs", []):
                L.append(f"  - {r}")
        L += ["---", data["body"].strip(), ""]
        return "\n".join(L)

    def _on_go(self):
        title = self.title_e.get().strip()
        if not title:
            messagebox.showwarning("Falta el título", "Poné un título.")
            return
        self.go_btn.config(state="disabled")
        threading.Thread(target=self._run, args=(title,), daemon=True).start()

    def _run(self, title):
        try:
            section = self.section.get()
            slug = f"{date.today().isoformat()}-{slugify(title)}"
            d = self.CONTENT / section / slug
            d.mkdir(parents=True, exist_ok=True)
            files = {}

            # copiar archivos seleccionados a la carpeta del item
            if section == "memes" and self.files.get("meme"):
                src = Path(self.files["meme"]); ext = src.suffix.lower()
                if ext in VIDEO_EXT:
                    shutil.copy2(src, d / f"video{ext}"); files["video"] = f"video{ext}"
                else:
                    shutil.copy2(src, d / f"thumb{ext}"); files["thumbnail"] = f"thumb{ext}"
            if section == "guias" and self.files.get("guide"):
                src = Path(self.files["guide"]); ext = src.suffix.lower()
                shutil.copy2(src, d / f"guide{ext}"); files["file"] = f"guide{ext}"
            if section == "blog" and self.files.get("images"):
                refs = []
                for i, img in enumerate(self.files["images"], 1):
                    ext = Path(img).suffix.lower(); name = f"img{i}{ext}"
                    shutil.copy2(img, d / name); refs.append(name)
                files["refs"] = refs

            data = {
                "title": title,
                "topic": self.topic_e.get().strip(),
                "publish": self.publish_e.get().strip(),
                "body": self.body_t.get("1.0", "end").strip(),
                "video_url": getattr(self, "video_url_e", None).get().strip() if section == "memes" else "",
                "sources": [l.strip() for l in self.sources_t.get("1.0", "end").splitlines() if l.strip()] if section == "blog" else [],
            }
            (d / "item.md").write_text(self._build_md(section, slug, data, files), encoding="utf-8")
            self._logln(f"✓ item creado: content/{section}/{slug}/item.md")

            # generar (build.py) en subproceso, con las keys como variables de entorno
            env = os.environ.copy()
            g, c = self.gemini.get().strip(), self.claude.get().strip()
            if g: env["GEMINI_API_KEY"] = g
            if c: env["ANTHROPIC_API_KEY"] = c
            env["PYTHONIOENCODING"] = "utf-8"
            self._logln(f"→ generando ({'Gemini' if g else 'mock'} imágenes · {'Claude' if c else 'mock'} texto)…\n")
            proc = subprocess.Popen([sys.executable, str(self.ROOT / "tools" / "build.py")],
                                    cwd=str(self.ROOT), env=env, stdout=subprocess.PIPE,
                                    stderr=subprocess.STDOUT, text=True, encoding="utf-8")
            for line in proc.stdout:
                self._logln(line.rstrip())
            proc.wait()
            if proc.returncode == 0:
                self._logln("\n✓ Listo. Para publicar en GitHub:")
                self._logln('   git add -A && git commit -m "nuevo contenido" && git push')
                if self.email_var.get():
                    self._send_email(section, slug, d)
            else:
                self._logln(f"\n✗ El generador terminó con error (código {proc.returncode}).")
        except Exception as e:
            self._logln(f"✗ Error: {e}")
        finally:
            self.go_btn.config(state="normal")

    def _send_email(self, section, slug, d):
        try:
            sys.path.insert(0, str(self.ROOT / "tools"))
            import notify
            parts = []
            for fn, label in [("facebook.txt", "FACEBOOK"), ("instagram.txt", "INSTAGRAM"),
                              ("caption.txt", "CAPTION (IG / TikTok)")]:
                fp = d / fn
                if fp.exists():
                    parts.append(f"=== {label} ===\n{fp.read_text(encoding='utf-8')}")
            body = "\n\n".join(parts) or "(sin captions)"
            atts = []
            cover = self.ROOT / "public" / "media" / section / f"{slug}.png"
            if cover.exists():
                atts.append(str(cover))
            if section == "blog":
                card = self.ROOT / "public" / "media" / "blog" / f"{slug}-card.png"
                if card.exists():
                    atts.append(str(card))          # la segunda imagen (card viral)
                imgd = self.ROOT / "public" / "media" / "blog" / slug
                if imgd.exists():
                    atts += [str(p) for p in sorted(imgd.glob("*")) if p.is_file()]
            self._logln("→ enviando email…")
            notify.send_pack(self.gmail_user.get().strip(), self.gmail_pass.get().strip(),
                             self.email_to.get().strip(),
                             f"malo_ia · {section} · {slug}", body, atts)
            self._logln(f"✓ Email enviado a {self.email_to.get().strip()}")
        except Exception as e:
            self._logln(f"✗ No se pudo enviar el email: {e}")


if __name__ == "__main__":
    Studio().mainloop()




