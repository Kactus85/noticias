# 📬 Noticias del Día (RSS) — Guía para dejarlo automático y GRATIS en la nube

Esto deja tu digest enviándose **solo, todos los días a las 7:00 AM de Chile**, a
**antonio@kactusempresa.cl**, sin prender el computador y **sin costo**. Lee feeds
RSS públicos de cada medio (no usa la API de Claude → no necesitas saldo ni clave de
Claude). Corre gratis en GitHub. Toma unos 15 minutos la primera vez.

> Lo único "técnico": subir 3 archivos y pegar 2 claves de tu Gmail. Nada de programar.

---

## Lo que vas a subir (ya está todo en esta carpeta)
- `noticias_del_dia_rss.py` — el programa completo.
- `requirements.txt` — lo que necesita para funcionar.
- `.github/workflows/noticias.yml` — el "robot" que lo corre cada día.

⚠️ **Importante:** la carpeta `.github` empieza con punto y debe mantenerse tal cual.
Si subes los archivos arrastrándolos (paso 3), GitHub respeta las carpetas solo.

---

## Paso 1 — Cuenta en GitHub (si no tienes)
Entra a **https://github.com** y crea una cuenta gratis.

## Paso 2 — Crear un repositorio
1. Arriba a la derecha, **+** → **New repository**.
2. Nombre: por ejemplo `noticias-del-dia`.
3. Marca **Private** (privado).
4. **Create repository**.

## Paso 3 — Subir los archivos
1. **Add file** → **Upload files**.
2. Arrastra los **3 archivos** de esta carpeta (incluida la carpeta `.github`).
   - Si tu computador no te deja arrastrar `.github`, descomprime el ZIP y arrastra
     todo el contenido de la carpeta `noticias-rss`.
3. **Commit changes**.

## Paso 4 — Cargar tus 2 claves de Gmail (en secreto)
1. **Settings** → **Secrets and variables** → **Actions**.
2. **New repository secret**, crea estos dos (el **Name** EXACTO):

   | Name (cópialo igual) | Qué va en el valor |
   |---|---|
   | `GMAIL_USER` | el Gmail que envía, ej. `tucuenta@gmail.com` |
   | `GMAIL_APP_PASSWORD` | la *contraseña de aplicación* de Gmail (16 letras) |

   > La app password se crea en: cuenta Google → Seguridad → Verificación en 2 pasos
   > → Contraseñas de aplicaciones.

## Paso 5 — Probar (ahora mismo)
1. Pestaña **Actions** (si pide habilitarlas, acepta).
2. **Noticias del Día (RSS)** → **Run workflow** → **Run workflow**.
3. Espera 1-2 min y refresca. ✓ verde = **revisa tu correo** en antonio@kactusempresa.cl.
   - ✗ rojo: haz clic para ver el error (casi siempre una clave mal pegada).

## ¡Listo!
Se manda **solo, todos los días a las 7:00 AM de Chile**. No tienes que hacer nada más.

---

## Preguntas frecuentes

**¿De verdad es gratis?** Sí. GitHub Actions es gratis para esto (usa ~1 min al día) y
los feeds RSS son públicos y gratuitos. No hay saldo de API que pagar.

**¿De dónde salen las noticias?** De los feeds RSS de El Mostrador, BioBioChile, BBC
Mundo, The Guardian, The Verge, MIT Technology Review, The Atlantic y The New York Times
(opinión). Son los titulares y resúmenes reales que publica cada medio.

**¿Y si un medio falla un día?** El script es a prueba de fallos: si un feed no responde
o viene vacío, simplemente lo salta y el correo igual se envía con el resto. Nunca llega
roto.

**Quiero cambiar, agregar o quitar fuentes.** Abre `noticias_del_dia_rss.py` y edita las
listas `NEWS_FEEDS`, `MAGAZINE_FEEDS` u `OPINION_FEEDS` del comienzo. Es pegar el nombre
y la URL del feed RSS. Si quieres, te ayudo a sumar medios específicos.

**Cartas al Director / columnistas chilenos puntuales (Peña, Cavallo):** casi no se
publican por RSS, por eso esta versión trae "Opinión" general en vez de columnistas
fijos. Si más adelante quieres esas firmas exactas, ahí sí conviene volver a la versión
con IA (de pago) o a una fuente específica.

**Cambiar la hora o los días:** edita las líneas `cron` en
`.github/workflows/noticias.yml`. Avísame y te lo dejo indicado.

**Puede llegar con unos minutos de atraso** algunos días: es normal en el plan gratis de
GitHub, no es un error.
