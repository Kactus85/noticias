#!/usr/bin/env python3
"""
Noticias del Día — versión RSS (100% GRATIS)
Lee feeds RSS públicos de cada medio (sin IA, sin costo), arma el correo
en formato "Briefing" (Dir B) y lo envía a antonio@kactusempresa.cl.
"""

import os
import re
import html
import time
import calendar
import smtplib
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from zoneinfo import ZoneInfo

import feedparser

# ============================================================================
# CONFIGURACIÓN
# ============================================================================

TO_EMAIL = "antonio@kactusempresa.cl"

POR_FEED = 2
POR_SECCION = 6

EXCLUIR_CATS = [
    "deporte", "fútbol", "futbol", "motor", "fórmula", "formula", "tenis",
    "policial", "delincuencia", "crimen", "música", "musica", "cultural",
    "tendencias", "servicios", "toma nota", "farándula", "espectáculo",
]

NEWS_FEEDS = {
    "política": [
        {"name": "El Mercurio (Emol)", "url": "http://rss.emol.com/rss.asp?canal=1"},
        {"name": "La Tercera", "url": "https://www.latercera.com/arc/outboundfeeds/rss/?outputType=xml"},
        {"name": "Ex-Ante", "url": "https://www.ex-ante.cl/feed/"},
        {"name": "El Mostrador", "url": "https://www.elmostrador.cl/feed/"},
        {"name": "El Dínamo", "url": "https://www.eldinamo.cl/feed/"},
        {"name": "The Clinic", "url": "https://www.theclinic.cl/feed/"},
        {"name": "Tele 13 Radio", "url": "https://www.t13.cl/rss/portada"},
        {"name": "BioBioChile", "url": "https://www.biobiochile.cl/static/feed-rss",
         "include": ["chile", "nacional", "política", "gobierno", "senado", "cámara"]},
    ],
    "economía": [
        {"name": "Financial Times", "url": "https://www.ft.com/rss/home"},
        {"name": "Bloomberg", "url": "https://feeds.bloomberg.com/markets/news.rss"},
        {"name": "BioBioChile", "url": "https://www.biobiochile.cl/static/feed-rss",
         "include": ["económic", "economía", "mercado", "dólar", "negocios", "bolsillo"]},
        {"name": "El Mostrador", "url": "https://www.elmostrador.cl/mercados/feed/"},
    ],
    "internacional": [
        {"name": "El Mercurio (Emol)", "url": "http://rss.emol.com/rss.asp?canal=2"},
        {"name": "BBC Mundo", "url": "https://feeds.bbci.co.uk/mundo/rss.xml"},
        {"name": "El País", "url": "https://feeds.elpais.com/mrss-s/pages/ep/site/elpais.com/portada"},
        {"name": "The Guardian", "url": "https://www.theguardian.com/world/rss"},
        {"name": "Semafor", "url": "https://www.semafor.com/rss.xml"},
    ],
    "tecnología": [
        {"name": "El Mercurio (Emol)", "url": "http://rss.emol.com/rss.asp?canal=5"},
        {"name": "MIT Technology Review", "url": "https://www.technologyreview.com/feed/"},
    ],
}

MAGAZINE_FEEDS = [
    {"name": "The Economist", "url": "https://www.economist.com/latest/rss.xml", "topic": "Análisis"},
    {"name": "The Atlantic", "url": "https://www.theatlantic.com/feed/all/", "topic": "Análisis"},
    {"name": "CIPER Chile", "url": "https://www.ciperchile.cl/feed/", "topic": "Reportajes"},
]

OPINION_FEEDS = [
    {"name": "The New York Times", "url": "https://rss.nytimes.com/services/xml/rss/nyt/Opinion.xml"},
    {"name": "The Guardian", "url": "https://www.theguardian.com/commentisfree/rss"},
    {"name": "El Mostrador", "url": "https://www.elmostrador.cl/noticias/opinion/feed/"},
]

# ============================================================================
# LECTURA DE FEEDS
# ============================================================================

_feed_cache = {}


def _get_feed(url):
    if url not in _feed_cache:
        try:
            _feed_cache[url] = feedparser.parse(url)
        except Exception as e:
            print(f"  No se pudo leer {url}: {e}")
            _feed_cache[url] = None
    return _feed_cache[url]


def _clean(texto, n=200):
    if not texto:
        return ""
    t = re.sub(r"<[^>]+>", "", texto)
    t = html.unescape(t)
    t = re.sub(r"\s+", " ", t).strip()
    for marca in ("Continua leyendo", "The post", "Leer más", "[…]", "[...]"):
        i = t.find(marca)
        if i > 40:
            t = t[:i].strip()
    if len(t) > n:
        t = t[:n].rsplit(" ", 1)[0].rstrip(".,;:") + "…"
    return t


def _tiempo_relativo(entry):
    st = entry.get("published_parsed") or entry.get("updated_parsed")
    if not st:
        return ""
    segs = time.time() - calendar.timegm(st)
    if segs < 0:
        return "Recién"
    if segs < 3600:
        m = int(segs // 60)
        return f"Hace {max(m, 1)} min"
    if segs < 86400:
        return f"Hace {int(segs // 3600)} h"
    d = int(segs // 86400)
    return "Ayer" if d == 1 else f"Hace {d} días"


def _categorias(entry):
    tags = entry.get("tags") or []
    return [(t.get("term") or "").lower() for t in tags]


def _pasa_filtro(entry, include):
    cats = _categorias(entry)
    if any(any(x in c for x in EXCLUIR_CATS) for c in cats):
        return False
    if include:
        if not any(any(inc in c for inc in include) for c in cats):
            return False
    return True


def leer_entradas(conf, limite=POR_FEED):
    feed = _get_feed(conf["url"])
    if not feed or not getattr(feed, "entries", None):
        return []
    include = conf.get("include")
    out = []
    for e in feed.entries:
        if include is not None and not _pasa_filtro(e, include):
            continue
        if include is None and not _pasa_filtro(e, None):
            if conf.get("name") in ("BioBioChile", "El Mostrador"):
                continue
        titulo = _clean(e.get("title", ""), 110)
        if not titulo:
            continue
        out.append({
            "title": titulo,
            "summary": _clean(e.get("summary", "") or e.get("description", ""), 200),
            "url": e.get("link", "#"),
            "time": _tiempo_relativo(e),
            "author": _clean(e.get("author", ""), 60),
        })
        if len(out) >= limite:
            break
    return out

# ============================================================================
# GENERADOR DEL CORREO — formato "Briefing"
# ============================================================================

SANS = "-apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, Arial, sans-serif"

SECTION_COLORS = {
    "política": "#1f3a5f", "economía": "#1f6b4a", "internacional": "#8a3b2e",
    "tecnología": "#4b3a78", "Análisis & Revistas": "#2d2d2d",
    "Opinión": "#8a6d2f", "Cartas al Director": "#2f6d6d",
}
_DEFAULT_COLOR = "#1f3a5f"


def _fecha_es():
    s = datetime.now(ZoneInfo("America/Santiago")).strftime('%A, %d de %B de %Y')
    repl = {'Monday': 'Lunes', 'Tuesday': 'Martes', 'Wednesday': 'Miércoles',
            'Thursday': 'Jueves', 'Friday': 'Viernes', 'Saturday': 'Sábado', 'Sunday': 'Domingo',
            'January': 'enero', 'February': 'febrero', 'March': 'marzo', 'April': 'abril',
            'May': 'mayo', 'June': 'junio', 'July': 'julio', 'August': 'agosto',
            'September': 'septiembre', 'October': 'octubre', 'November': 'noviembre', 'December': 'diciembre'}
    for en, es in repl.items():
        s = s.replace(en, es)
    return s[:1].upper() + s[1:]


def _item_row(num, color, kicker, secondary, tiempo, title, body, url):
    n = f"{num:02d}"
    bits = [b for b in (kicker, secondary, tiempo) if b]
    meta = " &middot; ".join(bits)
    return (
        f'<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="margin:16px 0;"><tr>'
        f'<td valign="top" width="48" style="font:300 24px/1 {SANS};color:#cfcfcf;padding:2px 14px 0 0;">{n}</td>'
        f'<td valign="top">'
        f'<div style="font:700 16.5px/1.38 {SANS};letter-spacing:-0.2px;color:#141414;margin:0 0 5px;">{title}</div>'
        f'<div style="font:14px/1.55 {SANS};color:#666;margin:0 0 8px;">{body}</div>'
        f'<div style="font:12px/1.4 {SANS};color:#9a9a9a;">{meta}'
        f'&nbsp;&nbsp;&nbsp;<a href="{url}" style="font-weight:600;color:{color};text-decoration:none;">Leer &rarr;</a>'
        f'</div></td></tr></table>'
    )


def _section_block(label, entries):
    if not entries:
        return ""
    color = SECTION_COLORS.get(label, _DEFAULT_COLOR)
    htmlx = (
        f'<div style="margin:32px 0 4px;">'
        f'<span style="display:inline-block;width:9px;height:9px;border-radius:50%;background:{color};"></span>'
        f'<span style="font:700 12px/1 {SANS};letter-spacing:2.5px;text-transform:uppercase;'
        f'color:#111;margin-left:9px;vertical-align:2px;">{label}</span></div>'
    )
    for i, e in enumerate(entries):
        htmlx += _item_row(i + 1, color, e.get("kicker", ""), e.get("secondary", ""),
                           e.get("time", ""), e.get("title", ""), e.get("body", ""), e.get("url", "#"))
        if i < len(entries) - 1:
            htmlx += '<div style="border-top:1px solid #eee;margin:0 0 0 62px;"></div>'
    return htmlx


def generate_email_html(news_by_section, opinion_groups, magazine_groups):
    fuentes_set, fuentes_order = set(), []

    def _track(name):
        if name and name not in fuentes_set:
            fuentes_set.add(name)
            fuentes_order.append(name)

    body = ""
    for section, items in news_by_section.items():
        entries = []
        for it in items:
            _track(it["kicker"])
            entries.append({"kicker": it["kicker"], "time": it.get("time", ""),
                            "title": it["title"], "body": it["body"], "url": it["url"]})
        body += _section_block(section, entries)

    mag_entries = []
    for g in magazine_groups:
        _track(g["name"])
        for it in g["items"]:
            mag_entries.append({"kicker": g["name"], "secondary": g.get("topic", ""),
                                "title": it["title"], "body": it["summary"], "url": it["url"]})
    body += _section_block("Análisis & Revistas", mag_entries)

    op_entries = []
    for g in opinion_groups:
        _track(g["name"])
        for it in g["items"]:
            op_entries.append({"kicker": it.get("author") or g["name"], "secondary": g["name"],
                               "title": it["title"], "body": it["summary"], "url": it["url"]})
    body += _section_block("Opinión", op_entries)

    fecha = _fecha_es()
    fuentes = " &middot; ".join(fuentes_order) if fuentes_order else "—"

    return f"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Noticias del Día</title>
</head>
<body style="margin:0;padding:0;background:#ffffff;">
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="max-width:640px;margin:0 auto;background:#ffffff;">
  <tr><td style="padding:36px 36px 22px;border-bottom:2px solid #111;">
    <table role="presentation" width="100%"><tr>
      <td valign="bottom"><div style="font:800 23px/1 {SANS};letter-spacing:-0.6px;color:#111;">Noticias del Día</div></td>
      <td valign="bottom" align="right"><div style="font:600 11px/1.4 {SANS};letter-spacing:1.5px;text-transform:uppercase;color:#999;">{fecha}</div></td>
    </tr></table>
  </td></tr>
  <tr><td style="padding:6px 36px 30px;">{body}</td></tr>
  <tr><td style="border-top:2px solid #111;padding:24px 36px;">
    <div style="font:700 11px/1.4 {SANS};letter-spacing:1.5px;text-transform:uppercase;color:#111;">Noticias del Día &middot; 7:00 AM</div>
    <div style="font:11px/1.7 {SANS};color:#9a9a9a;margin:8px 0 0;">Fuentes: {fuentes}</div>
  </td></tr>
</table>
</body>
</html>"""


def send_email(to_email, subject, html_content):
    try:
        gmail_user = os.environ.get("GMAIL_USER")
        gmail_password = os.environ.get("GMAIL_APP_PASSWORD")
        if not gmail_user or not gmail_password:
            print("Faltan credenciales de Gmail (GMAIL_USER / GMAIL_APP_PASSWORD).")
            return False
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = gmail_user
        msg["To"] = to_email
        msg.attach(MIMEText(html_content, "html"))
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(gmail_user, gmail_password)
            server.sendmail(gmail_user, to_email, msg.as_string())
        print(f"Correo enviado a {to_email}")
        return True
    except Exception as e:
        print(f"Error enviando el correo: {e}")
        return False

# ============================================================================
# CANDADO DE HORARIO + EJECUCIÓN
# ============================================================================

def _should_send_now():
    if not os.environ.get("ENFORCE_SCHEDULE"):
        return True
    try:
        return datetime.now(ZoneInfo("America/Santiago")).hour == 7
    except Exception:
        return True


def generate_daily_digest():
    print("Generando Noticias del Día (RSS, gratis)...\n")

    news_by_section = {}
    for section, feeds in NEWS_FEEDS.items():
        por_feed = []
        for f in feeds:
            print(f"  {section} · {f['name']}...", end=" ", flush=True)
            entradas = leer_entradas(f)
            por_feed.append([{"kicker": f["name"], "time": e["time"],
                              "title": e["title"], "body": e["summary"], "url": e["url"]}
                             for e in entradas])
            print(f"OK ({len(entradas)})")
        items, ronda = [], 0
        while any(len(lst) > ronda for lst in por_feed):
            for lst in por_feed:
                if len(lst) > ronda:
                    items.append(lst[ronda])
            ronda += 1
        news_by_section[section] = items[:POR_SECCION]

    magazine_groups = []
    print()
    for f in MAGAZINE_FEEDS:
        print(f"  {f['name']}...", end=" ", flush=True)
        entradas = leer_entradas(f, limite=2)
        magazine_groups.append({"name": f["name"], "topic": f.get("topic", ""), "items": entradas})
        print(f"OK ({len(entradas)})")

    opinion_groups = []
    print()
    for f in OPINION_FEEDS:
        print(f"  {f['name']}...", end=" ", flush=True)
        entradas = leer_entradas(f, limite=2)
        opinion_groups.append({"name": f["name"], "items": entradas})
        print(f"OK ({len(entradas)})")

    print("\nGenerando HTML...", end=" ", flush=True)
    html_content = generate_email_html(news_by_section, opinion_groups, magazine_groups)
    print("OK")

    with open("noticias_del_dia.html", "w", encoding="utf-8") as fh:
        fh.write(html_content)

    total = sum(len(v) for v in news_by_section.values())
    if total == 0:
        print("Ningún feed entregó noticias. No se envía correo.")
        return

    print("\nEnviando...")
    send_email(TO_EMAIL, f"Noticias del Día — {_fecha_es()}", html_content)


if __name__ == "__main__":
    if _should_send_now():
        generate_daily_digest()
    else:
        ahora = datetime.now(ZoneInfo("America/Santiago")).strftime("%H:%M")
        print(f"Son las {ahora} en Chile, no es la hora de envío (7:00 AM). Saltando.")
