# malo_ia — sitio + motor de contenido

La landing de siempre, ahora con **3 apartados navegables** (Guías, Videos/Memes, Blog)
y un **carrusel "Lo nuevo"**. Vos creás un archivo por item, corrés el motor (Claude
escribe, Gemini dibuja **en el estilo de la página, con BIX de compañero**) y hacés push.

## ⚠️ Seguridad — leé esto primero
- Las API keys van **siempre** por variable de entorno o secret de GitHub. **Nunca** en el repo.
- Las keys que tenías escritas en los `*_factory.py` quedaron expuestas: **rotalas** (generalas de nuevo).
- `.gitignore` ya bloquea `.env` y secretos. La carpeta `public/` **sí** se sube (es lo que se sirve).

## La forma fácil: la interfaz (estudio)
```bash
cd malo-ia-site
python tools/studio.py
```
Se abre una ventana donde:
1. Pegás tus API keys (Gemini para imágenes, Claude para texto) — **no se guardan**.
2. Elegís el apartado y completás:
   - **Memes**: link del video O seleccionás el archivo (video/imagen) + descripción.
   - **Guías**: seleccionás el PDF/presentación + descripción.
   - **Blog**: varias imágenes + varios links + tu investigación.
3. Click en **"Crear y generar"** → arma el item, genera la portada (Gemini) y
   reescribe el texto (Claude), y deja todo listo en `public/`.
4. Subís a GitHub con el comando que te muestra (abajo).

## La forma manual (consola), si preferís
```bash
python tools/new_item.py guias "Mi guía de prompts"   # crea la plantilla
#   → editás el item.md, ponés el PDF, status: published
python tools/build.py                                  # genera (usa las keys del entorno)
git add -A && git commit -m "nueva guía" && git push
```
GitHub Pages se actualiza solo en ~1 minuto.

## Modo MOCK vs real (auto-detecta por key)
El motor mira qué keys tenés en el entorno y decide pieza por pieza:
- **Imágenes** → Gemini si está `GEMINI_API_KEY` (o `GOOGLE_API_KEY`); si no, portada de relleno.
- **Texto** → Claude si está `ANTHROPIC_API_KEY`; si no, texto de ejemplo.

```powershell
# PowerShell — solo seteás las keys que tengas (sin MALO_REAL)
$env:GEMINI_API_KEY="AIza..."        # imágenes reales
$env:ANTHROPIC_API_KEY="sk-ant-..."  # (opcional) texto real
python tools/build.py
```
Instalá antes: `pip install -r tools/requirements.txt`

**Flags útiles:**
- `MALO_REGEN=1` → regenera las portadas que ya existen (por defecto NO las toca: solo crea las que faltan, así el build es rápido y barato a medida que crece el contenido).
- `MALO_MOCK=1` → fuerza todo a relleno aunque tengas keys (para probar).

## Cómo cargás cada apartado (inputs distintos)
- **Guías** (`content/guias/<slug>/`): `item.md` + el **PDF/presentación** (`file: guia.pdf`).
  → portada + pitch + botón **Descargar** + CTA a la guía gratis.
- **Videos/Memes** (`content/memes/<slug>/`): `item.md` con `video_url` y `platforms`, refs opcionales.
  → portada + **caption con CTA al link del bio → guía gratis** + botones Compartir / Copiar caption.
- **Blog** (`content/blog/<slug>/`): `item.md` con tu investigación de Perplexity, `sources` y `refs`.
  → portada + resumen. (El cuerpo completo del post lo enriquecemos en la próxima vuelta.)

> El motor **detecta el tipo por la carpeta** y aplica el formato. Cada apartado es una
> función en `tools/sections.py` (`handle_guias`, `handle_memes`, `handle_blog`).

## El embudo vista → página → lead
Cada video lleva un **caption** generado que termina invitando al **link del bio → guía gratis**.
El link sale de `site.config.json` → `lead.free_guide_url`. Completá ese valor (y `bio_link_url`).

## Config — `site.config.json`
Ahí viven: el link de la guía gratis, las redes, los labels de cada sección y cuántos items
muestra el carrusel. Editalo y volvé a buildear.

## El estilo (no se toca por accidente)
Todo lo visual vive en `tools/style.py`: la paleta exacta de la landing, las fuentes y
`BIX_ANCHOR` (la descripción del personaje). Las portadas mock y los prompts reales salen de ahí.

## Estructura
```
malo-ia-site/
├── index.html · guias.html · memes.html · blog.html   # páginas (las 3 navegables)
├── styles.css (landing) · app.css (componentes nuevos)
├── main.js (GSAP landing) · app.js (carrusel + secciones)
├── site.config.json
├── content/<seccion>/<slug>/item.md   ← lo que vos creás
├── public/                            ← GENERADO (se sube): content.json, media/, files/
└── tools/  build.py · new_item.py · sections.py · providers.py · content.py · style.py
```

## Probar local (con server, para que cargue content.json)
```bash
python -m http.server 5173 --directory malo-ia-site
# abrí http://localhost:5173
```
(Abrir el HTML con doble clic no funciona: `fetch` necesita http.)

## Subir a GitHub Pages
Repo → Settings → Pages → Deploy from a branch → `main` / `(root)`.
El sitio queda en `https://TU-USUARIO.github.io/TU-REPO/`.

## Analítica — Google Analytics 4 (medir visitas y descargas)
1. En [analytics.google.com](https://analytics.google.com): creá una propiedad → flujo de datos **Web** con la URL de tu sitio → copiá el **Measurement ID** (`G-XXXXXXXXXX`).
2. Pegalo en `site.config.json`:
   ```json
   "analytics": { "ga4_id": "G-XXXXXXXXXX" }
   ```
3. `python tools/build.py` (lo hornea en content.json) y `git push`.

Qué vas a ver en GA4:
- **Visitas**: Realtime + Reports → Engagement.
- **Eventos del embudo** (Reports → Engagement → Events): `download_guide`, `click_lead_cta`, `share`, `select_section`, además de `page_view`.
- Para tus números de validación: marcá `download_guide` y `click_lead_cta` como **Key events** (Admin → Events → "Mark as key event").

Notas: los bloqueadores de anuncios no se cuentan (~10-30% menos), y para visitantes de la UE en teoría corresponde un aviso de cookies. Si lo dejás vacío (`""`), no carga nada.

## Nube (opcional)
`.github/workflows/build.yml` puede generar todo al hacer push. Está **desactivado** por
defecto (`if: false`). Para activarlo, seguí las instrucciones que tiene adentro.
