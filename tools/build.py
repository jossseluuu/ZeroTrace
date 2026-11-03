#!/usr/bin/env python3
"""ZeroTrace: genera todas las salidas del repositorio a partir de data/.

Uso:
  python tools/build.py                        regenera ediciones, índices, registro de alertas, RSS e historial
  python tools/build.py --siguiente-foco       propone el foco del día (excluye los de las 7 ediciones anteriores)
  python tools/build.py --ya-notificado CVE…   indica si un CVE ya figura en el registro de alertas

El build se detiene con error si una alerta o un CVE ya notificado vuelve a aparecer en un semáforo.
Sin dependencias externas: solo biblioteca estándar de Python 3.9+.
"""
import base64, hashlib, html, json, random, re, sys
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
BASE_URL = "https://jossseluuu.github.io/ZeroTrace"
TZ = ZoneInfo("Europe/Madrid")
VENTANA_SIN_REPETIR = 7
DIRS = {"es": "ediciones", "en": "editions"}
REGISTRO = {"es": "alertas", "en": "alerts"}

T = {
  "es": {
    "basico": "Básico", "fondo": "A fondo", "nivel": "Nivel de lectura", "tema": "Tema",
    "auto": "Automático", "claro": "Claro", "oscuro": "Oscuro", "imprimir": "Imprimir",
    "otro_idioma": "English", "otro_lang": "en", "archivo": "Ediciones", "registro": "Registro de alertas",
    "semaforo": "Semáforo del día", "afecta": "A quién afecta", "que_hacer": "Qué hacer", "detalle": "Detalle",
    "sin_alertas": "Hoy no hay alertas nuevas.",
    "sin_alertas_txt": "Nada de lo publicado en las últimas horas cumple nuestro criterio: explotación real o impacto amplio en dispositivos de uso común. Las alertas anteriores siguen en el registro.",
    "ver_registro": "Ver todas las alertas notificadas",
    "en2": "En pocas palabras", "esencial": "Lo esencial",
    "riesgo": "Riesgo real", "probabilidad": "Probabilidad", "impacto": "Impacto",
    "como": "Cómo funciona", "ataque": "Así sería un ataque", "atacante": "Qué puede y qué no puede hacer el atacante",
    "puede": "Puede", "no_puede": "No puede",
    "medidas": "Qué hacer", "esfuerzo": "Esfuerzo", "para": "Para", "solo_fondo": "Nivel a fondo",
    "comprobar": "Compruébalo tú", "innecesario": "Lo que no hace falta que hagas",
    "mito": "Mito y realidad", "mito_l": "Lo que se cree", "realidad_l": "Lo que ocurre",
    "tecnico": "Para perfiles técnicos", "glosario": "Glosario", "fuentes": "Fuentes", "min": "min",
    "lectura": "Lectura", "dispositivos": "Dispositivos", "foco": "Foco",
    "buscar": "Buscar por tema o palabra", "buscar_alerta": "Buscar por CVE, producto o palabra",
    "todos_focos": "Todos los focos", "todos": "Todas", "todos_disp": "Todos",
    "sin_resultados": "Ninguna entrada coincide con el filtro. Prueba a quitar alguno.",
    "sin_ediciones": "Todavía no hay ediciones. La primera se publica en los próximos días.",
    "sin_registro": "Todavía no se ha notificado ninguna alerta.",
    "ediciones": "ediciones", "alertas_n": "alertas", "tagline": "Ciberseguridad útil, un concepto al día.",
    "registro_sub": "Todas las alertas publicadas en el semáforo, por fecha. Cada vulnerabilidad aparece una sola vez: el día en que la notificamos.",
    "publicada": "Publicada en la edición del",
    "licencia": "Contenido bajo CC BY 4.0. Código bajo MIT. Sin cookies, sin rastreadores y sin recursos de terceros.",
    "niveles": {"rojo": "Crítico", "amarillo": "Atención", "verde": "Informativo"},
    "niveles_dia": {"rojo": "Día crítico", "amarillo": "Día de atención", "verde": "Día tranquilo"},
    "nota_sem": "El color del día refleja el impacto para el público general. Cada alerta lleva el suyo para las personas a las que afecta.",
    "valores": {"alto": "alto", "medio": "medio", "bajo": "bajo", "todos": "todos", "avanzado": "avanzado", "paranoico": "paranoico"},
    "valores_probabilidad": {"alto": "alta", "medio": "media", "bajo": "baja"},
    "disp": {"smartphone": "Smartphone", "tablet": "Tablet", "portatil": "Portátil", "sobremesa": "Sobremesa",
             "tv": "Smart TV", "wearable": "Wearable", "iot": "IoT", "router": "Router", "servidor": "Servidores",
             "empresa": "Empresa", "todos": "Todos"},
    "feed_desc": "Newsletter diaria de ciberseguridad: un concepto concreto cada día, para principiantes y para quien quiera profundizar.",
    "rss": "RSS", "respuesta": "Ver respuesta",
  },
  "en": {
    "basico": "Basic", "fondo": "Deep dive", "nivel": "Reading level", "tema": "Theme",
    "auto": "Automatic", "claro": "Light", "oscuro": "Dark", "imprimir": "Print",
    "otro_idioma": "Español", "otro_lang": "es", "archivo": "Editions", "registro": "Alert log",
    "semaforo": "Today's status", "afecta": "Who it affects", "que_hacer": "What to do", "detalle": "Details",
    "sin_alertas": "No new alerts today.",
    "sin_alertas_txt": "Nothing published in the last few hours meets our bar: real-world exploitation or broad impact on everyday devices. Earlier alerts are still in the log.",
    "ver_registro": "See every alert we've issued",
    "en2": "In a nutshell", "esencial": "The essentials",
    "riesgo": "Real-world risk", "probabilidad": "Likelihood", "impacto": "Impact",
    "como": "How it works", "ataque": "What an attack looks like", "atacante": "What an attacker can and can't do",
    "puede": "Can", "no_puede": "Can't",
    "medidas": "What to do", "esfuerzo": "Effort", "para": "For", "solo_fondo": "Deep-dive level",
    "comprobar": "Check it yourself", "innecesario": "What you don't need to do",
    "mito": "Myth and reality", "mito_l": "What people think", "realidad_l": "What actually happens",
    "tecnico": "For technical readers", "glosario": "Glossary", "fuentes": "Sources", "min": "min",
    "lectura": "Reading time", "dispositivos": "Devices", "foco": "Focus",
    "buscar": "Search by topic or keyword", "buscar_alerta": "Search by CVE, product, or keyword",
    "todos_focos": "All topics", "todos": "All", "todos_disp": "All",
    "sin_resultados": "Nothing matches this filter. Try removing one.",
    "sin_ediciones": "No editions yet. The first one is coming in the next few days.",
    "sin_registro": "No alerts have been issued yet.",
    "ediciones": "editions", "alertas_n": "alerts", "tagline": "Practical cybersecurity, one concept a day.",
    "registro_sub": "Every alert published in the daily status, by date. Each vulnerability appears only once: on the day we reported it.",
    "publicada": "Published in the edition of",
    "licencia": "Content under CC BY 4.0. Code under MIT. No cookies, no trackers, and no third-party resources.",
    "niveles": {"rojo": "Critical", "amarillo": "Heads-up", "verde": "For your information"},
    "niveles_dia": {"rojo": "Critical day", "amarillo": "Heads-up day", "verde": "Quiet day"},
    "nota_sem": "The day's color reflects the impact on the general public. Each alert has its own color for the people it affects.",
    "valores": {"alto": "high", "medio": "medium", "bajo": "low", "todos": "everyone", "avanzado": "advanced", "paranoico": "paranoid"},
    "disp": {"smartphone": "Smartphone", "tablet": "Tablet", "portatil": "Laptop", "sobremesa": "Desktop",
             "tv": "Smart TV", "wearable": "Wearable", "iot": "IoT", "router": "Router", "servidor": "Servers",
             "empresa": "Workplace", "todos": "All"},
    "feed_desc": "A daily cybersecurity newsletter: one concrete concept a day, for beginners and for those who want to go deeper.",
    "rss": "RSS", "respuesta": "Show answer",
  },
}
ICONOS_DISP = {"smartphone": "📱", "tablet": "📲", "portatil": "💻", "sobremesa": "🖥️", "tv": "📺", "wearable": "⌚",
               "iot": "🏠", "router": "📡", "servidor": "🗄️", "empresa": "🏢", "todos": "🌐"}
ORDEN_NIVEL = {"rojo": 0, "amarillo": 1, "verde": 2}

class ErrorValidacion(Exception):
    pass

# ---------------------------------------------------------------- utilidades
def fecha_larga(iso, lang):
    d = datetime.fromisoformat(iso)
    if lang == "es":
        meses = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto",
                 "septiembre", "octubre", "noviembre", "diciembre"]
        dias = ["lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo"]
        return f"{dias[d.weekday()].capitalize()}, {d.day} de {meses[d.month-1]} de {d.year}"
    return d.strftime("%A, %B ") + f"{d.day}, {d.year}"

def fecha_corta(iso, lang):
    d = datetime.fromisoformat(iso)
    return d.strftime("%d/%m/%Y") if lang == "es" else d.strftime("%m/%d/%Y")

def ih(s, glos=None):
    """Marcado mínimo: **negrita**, *cursiva*, `código`, [[id|término del glosario]]."""
    s = html.escape(s, quote=False)
    s = re.sub(r"`([^`]+)`", r"<code>\1</code>", s)
    s = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", s)
    s = re.sub(r"(?<![*\w])\*([^*]+)\*(?!\w)", r"<em>\1</em>", s)
    def term(m):
        tid, txt = m.group(1), m.group(2)
        if glos and tid in glos:
            return f'<button type="button" class="term" popovertarget="g-{tid}">{txt}</button>'
        return txt
    return re.sub(r"\[\[([\w-]+)\|([^\]]+)\]\]", term, s)

def md(s):
    return re.sub(r"\[\[[\w-]+\|([^\]]+)\]\]", r"\1", s)

def plano(s):
    return re.sub(r"[*`]", "", md(s))

def sha(text):
    return "'sha256-" + base64.b64encode(hashlib.sha256(text.encode()).digest()).decode() + "'"

def titulo_fuente(f, lang):
    return f["titulo"][lang] if isinstance(f["titulo"], dict) else f["titulo"]

def enlace(f, lang="es"):
    return f'<a href="{html.escape(f["url"])}" rel="noopener noreferrer">{html.escape(titulo_fuente(f, lang))}</a>'

def ruta_edicion(lang, fecha):
    return f"{DIRS[lang]}/{fecha[:4]}/{fecha[5:7]}/{fecha}.html"

# ---------------------------------------------------------------- estilos
CSS = r"""
:root{--paper:#f2f4f7;--surface:#fff;--sunken:#e8ecf2;--ink:#1a2233;--muted:#5a6578;--line:#d9dee6;
--accent:#2445c8;--accent-soft:#e3e8fb;--rojo:#c33b2e;--rojo-soft:#fae6e3;--amarillo:#a86d00;--amarillo-soft:#fbefd6;
--verde:#23855a;--verde-soft:#ddf1e6;--lamp-off:#2b3446;--housing:#1a2233;
--serif:Charter,"Bitstream Charter","Sitka Text",Cambria,Georgia,serif;
--sans:system-ui,-apple-system,"Segoe UI",Roboto,"Helvetica Neue",Arial,sans-serif;
--mono:ui-monospace,"SF Mono","Cascadia Mono",Consolas,monospace;color-scheme:light}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]){--paper:#0f1626;--surface:#172036;--sunken:#1d2740;
--ink:#e7ebf3;--muted:#9aa6bc;--line:#2a3552;--accent:#93a8ff;--accent-soft:#1f2b52;--rojo:#ff8577;--rojo-soft:#3b1c22;
--amarillo:#f2be4e;--amarillo-soft:#3a2d14;--verde:#5fd39a;--verde-soft:#123327;--lamp-off:#243049;--housing:#0a0f1b;color-scheme:dark}}
:root[data-theme="dark"]{--paper:#0f1626;--surface:#172036;--sunken:#1d2740;--ink:#e7ebf3;--muted:#9aa6bc;--line:#2a3552;
--accent:#93a8ff;--accent-soft:#1f2b52;--rojo:#ff8577;--rojo-soft:#3b1c22;--amarillo:#f2be4e;--amarillo-soft:#3a2d14;
--verde:#5fd39a;--verde-soft:#123327;--lamp-off:#243049;--housing:#0a0f1b;color-scheme:dark}
*{box-sizing:border-box}
html{-webkit-text-size-adjust:100%}
body{margin:0;background:var(--paper);color:var(--ink);font:16px/1.55 var(--sans)}
a{color:var(--accent);text-underline-offset:3px}
code{font:.86em var(--mono);background:var(--sunken);padding:.12em .38em;border-radius:4px;white-space:nowrap}
strong{font-weight:650}
.wrap{max-width:1040px;margin:0 auto;padding:0 16px}
.measure{max-width:44rem}
.sr{position:absolute;width:1px;height:1px;overflow:hidden;clip:rect(0 0 0 0);white-space:nowrap}
button:focus-visible,a:focus-visible,input:focus-visible,select:focus-visible{outline:2px solid var(--accent);outline-offset:2px}

/* barra superior */
.topbar{position:sticky;top:0;z-index:20;background:color-mix(in srgb,var(--paper) 90%,transparent);
backdrop-filter:saturate(1.4) blur(10px);border-bottom:1px solid var(--line)}
.topbar .wrap{display:flex;align-items:center;gap:10px;min-height:56px;flex-wrap:wrap;padding-block:6px}
.brand{display:flex;align-items:center;gap:9px;font-weight:800;letter-spacing:-.03em;font-size:1.08rem;color:var(--ink);text-decoration:none;margin-right:auto}
.brand i{display:inline-grid;grid-auto-flow:row;gap:2px;padding:3px;border-radius:5px;background:var(--housing)}
.brand i b{width:5px;height:5px;border-radius:50%;background:var(--lamp-off)}
.brand i b.on{background:var(--amarillo)}
.nav{display:flex;gap:14px;font-size:.88rem;margin-right:6px}
.nav a{color:var(--muted);text-decoration:none}.nav a:hover,.nav a[aria-current]{color:var(--ink)}
.controls{display:flex;gap:6px;align-items:center;flex-wrap:wrap}
.seg{display:inline-flex;border:1px solid var(--line);border-radius:8px;padding:2px;background:var(--surface)}
.seg button{border:0;background:none;color:var(--muted);font:600 .8rem var(--sans);padding:5px 10px;border-radius:6px;cursor:pointer}
.seg button[aria-pressed="true"]{background:var(--ink);color:var(--paper)}
.btn{border:1px solid var(--line);background:var(--surface);color:var(--ink);font:600 .8rem var(--sans);
padding:6px 10px;border-radius:8px;cursor:pointer;text-decoration:none;display:inline-flex;gap:6px;align-items:center}

/* cabecera de la edición */
.hero{display:grid;grid-template-columns:minmax(0,1fr) auto;gap:40px;align-items:center;padding:48px 0 28px}
.hero .date{color:var(--muted);font-size:.92rem;margin:0}
.hero h1{font-size:clamp(2rem,5.2vw,3.3rem);line-height:1.05;letter-spacing:-.035em;font-weight:800;margin:12px 0 14px;text-wrap:balance}
.hero .sub{font:1.2rem/1.5 var(--serif);color:var(--muted);margin:0 0 18px;max-width:38rem;text-wrap:pretty}
.facts{display:flex;flex-wrap:wrap;gap:6px 16px;color:var(--muted);font-size:.88rem;margin:0;padding:0;list-style:none}
.facts li{display:flex;gap:6px;align-items:center}

/* el semáforo: la pieza característica */
.light{display:flex;flex-direction:column;align-items:center;gap:12px}
.housing{background:var(--housing);border-radius:28px;padding:14px;display:grid;gap:12px;
box-shadow:inset 0 0 0 1px rgba(255,255,255,.06),0 18px 40px -18px rgba(10,20,40,.55)}
.lamp{width:46px;height:46px;border-radius:50%;background:var(--lamp-off)}
.lamp.on.rojo{background:radial-gradient(circle at 35% 35%,#ffb3a8,#e0402f 60%,#a5281c);box-shadow:0 0 22px 4px rgba(224,64,47,.55)}
.lamp.on.amarillo{background:radial-gradient(circle at 35% 35%,#ffe7a6,#f0a817 60%,#b97800);box-shadow:0 0 22px 4px rgba(240,168,23,.5)}
.lamp.on.verde{background:radial-gradient(circle at 35% 35%,#b7f5d2,#2fbf78 60%,#1a8150);box-shadow:0 0 22px 4px rgba(47,191,120,.45)}
.light .label{font-weight:700;font-size:.95rem;text-align:center}

/* secciones */
main section{padding:30px 0;border-top:1px solid var(--line)}
main section:first-of-type{border-top:0}
h2{font-size:1.4rem;letter-spacing:-.02em;line-height:1.2;margin:0 0 6px;font-weight:750}
.lede{color:var(--muted);margin:0 0 18px;max-width:44rem}
h3{font-size:1.08rem;letter-spacing:-.01em;margin:24px 0 6px;font-weight:700}
.prose p{font:1.075rem/1.72 var(--serif);margin:0 0 14px;max-width:44rem;text-wrap:pretty}
.deep-tag{display:inline-block;font:600 .72rem var(--sans);color:var(--accent);background:var(--accent-soft);
border-radius:4px;padding:2px 7px;margin-left:8px;vertical-align:3px}
[data-level="basic"] .deep{display:none!important}

/* alertas */
.alertas{display:grid;gap:12px}
.alerta{background:var(--surface);border:1px solid var(--line);border-left:5px solid var(--line);border-radius:6px 12px 12px 6px;padding:16px 20px}
.alerta.rojo{border-left-color:var(--rojo)}.alerta.amarillo{border-left-color:var(--amarillo)}.alerta.verde{border-left-color:var(--verde)}
.alerta header{display:flex;flex-wrap:wrap;gap:6px 12px;align-items:baseline;margin-bottom:8px}
.alerta h3{margin:0;font-size:1.05rem}
.pill{font:700 .72rem var(--sans);padding:2px 8px;border-radius:99px}
.pill.rojo{background:var(--rojo-soft);color:var(--rojo)}.pill.amarillo{background:var(--amarillo-soft);color:var(--amarillo)}
.pill.verde{background:var(--verde-soft);color:var(--verde)}
.alerta dl{display:grid;grid-template-columns:max-content 1fr;gap:4px 14px;margin:0;font-size:.95rem}
.alerta dt{color:var(--muted)}.alerta dd{margin:0}
.cves{display:flex;flex-wrap:wrap;gap:4px}
.src{font-size:.84rem;color:var(--muted);margin:10px 0 0}
.src a{color:var(--muted)}
.calma{background:var(--verde-soft);border-radius:12px;padding:18px 20px}
.calma p{margin:4px 0}
.nota{font-size:.85rem;color:var(--muted);margin:14px 0 0}

/* en pocas palabras */
.resumen{display:grid;grid-template-columns:minmax(0,1.5fr) minmax(0,1fr);gap:32px;align-items:start}
.esencial{background:var(--surface);border:1px solid var(--line);border-radius:12px;padding:18px 20px}
.esencial h3{margin:0 0 10px}
.esencial ul{margin:0;padding:0;list-style:none;display:grid;gap:10px}
.esencial li{padding-left:28px;position:relative;font-weight:600;line-height:1.45}
.esencial li::before{content:"";position:absolute;left:0;top:.2em;width:16px;height:16px;border-radius:50%;
background:var(--verde-soft);box-shadow:inset 0 0 0 5px var(--verde)}
.riesgo{display:grid;grid-template-columns:repeat(auto-fit,minmax(260px,1fr));gap:12px;margin-top:22px}
.medidor{background:var(--surface);border:1px solid var(--line);border-radius:12px;padding:14px 18px}
.medidor .top{display:flex;justify-content:space-between;align-items:center;margin-bottom:8px;font-weight:700}
.barras{display:grid;grid-template-columns:repeat(3,22px);gap:3px}
.barras i{height:8px;border-radius:2px;background:var(--sunken)}
.barras.bajo i:nth-child(-n+1),.barras.medio i:nth-child(-n+2),.barras.alto i{background:var(--ink)}
.medidor p{margin:0;font-size:.93rem;color:var(--muted)}

/* ataque paso a paso (es una secuencia real) */
.pasos-ataque{list-style:none;margin:0;padding:0;counter-reset:p;max-width:44rem}
.pasos-ataque li{counter-increment:p;position:relative;padding:0 0 20px 52px}
.pasos-ataque li::before{content:counter(p);position:absolute;left:0;top:0;width:32px;height:32px;border-radius:50%;
display:grid;place-items:center;font-weight:800;background:var(--surface);border:2px solid var(--rojo);color:var(--rojo)}
.pasos-ataque li:not(:last-child)::after{content:"";position:absolute;left:15px;top:34px;bottom:2px;width:2px;background:var(--line)}
.pasos-ataque strong{display:block;margin-bottom:2px}
.pasos-ataque p{margin:0;font:1rem/1.65 var(--serif)}

.puede{display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:14px}
.puede > div{border-radius:12px;padding:16px 20px}
.puede .si{background:var(--rojo-soft)}.puede .no{background:var(--verde-soft)}
.puede h3{margin:0 0 8px}
.puede ul{margin:0;padding-left:18px;display:grid;gap:6px}

/* medidas */
.medidas{display:grid;gap:14px}
.medida{background:var(--surface);border:1px solid var(--line);border-radius:12px;padding:18px 20px}
.medida h3{margin:0 0 6px}
.badges{display:flex;flex-wrap:wrap;gap:6px;margin:0 0 10px;padding:0;list-style:none}
.badges li{font-size:.78rem;border-radius:4px;padding:2px 8px;background:var(--sunken);color:var(--muted)}
.badges li.alto{background:var(--accent-soft);color:var(--accent);font-weight:650}
.medida > p{margin:0 0 12px;max-width:44rem}
.plataformas{display:grid;gap:10px;grid-template-columns:repeat(auto-fit,minmax(250px,1fr))}
.plataforma{background:var(--sunken);border-radius:8px;padding:10px 14px}
.plataforma h4{margin:0 0 4px;font-size:.84rem;color:var(--muted)}
.plataforma ol{margin:0;padding-left:20px;font-size:.94rem;display:grid;gap:3px}

.filas{display:grid;gap:0;max-width:52rem}
.fila{display:grid;grid-template-columns:minmax(150px,220px) 1fr;gap:18px;padding:14px 0;border-bottom:1px solid var(--line)}
.fila:last-child{border-bottom:0}
.fila h3{margin:0;font-size:1rem}.fila p{margin:0}

.mito{display:grid;gap:12px;grid-template-columns:repeat(auto-fit,minmax(260px,1fr))}
.mito > div{border-radius:12px;padding:16px 20px;background:var(--surface);border:1px solid var(--line)}
.mito h3{margin:0 0 6px;font-size:.9rem;color:var(--muted);font-weight:600}
.mito .creencia p{font:italic 1.15rem/1.5 var(--serif);margin:0}
.mito .hecho{border-color:var(--verde)}

.tecnico{background:var(--surface);border:1px solid var(--line);border-radius:14px;padding:22px 24px;margin-top:6px}
.tecnico h3:first-child{margin-top:0}

/* glosario */
.term{font:inherit;color:inherit;background:none;border:0;padding:0;cursor:help;border-bottom:1.5px dotted var(--accent);line-height:inherit}
[popover].gl-pop{border:1px solid var(--line);background:var(--surface);color:var(--ink);border-radius:12px;
padding:16px 18px;max-width:min(360px,calc(100vw - 32px));box-shadow:0 18px 50px rgba(0,0,0,.3);font-size:.96rem;line-height:1.5}
[popover].gl-pop::backdrop{background:rgba(10,15,27,.2)}
.gl-pop strong{display:block;margin-bottom:4px}
dl.glos{display:grid;grid-template-columns:minmax(140px,220px) 1fr;gap:10px 18px;margin:0;max-width:52rem}
dl.glos dt{font-weight:700}dl.glos dd{margin:0;color:var(--muted)}
.fuentes{padding-left:20px;font-size:.93rem;display:grid;gap:4px}

footer{border-top:1px solid var(--line);margin-top:24px;padding:24px 0 44px;font-size:.84rem;color:var(--muted)}
footer p{margin:4px 0}

/* archivo y registro */
.page-head{padding:44px 0 18px}
.page-head h1{font-size:clamp(2rem,5vw,3rem);letter-spacing:-.035em;line-height:1.05;margin:0 0 10px;font-weight:800}
.page-head p{color:var(--muted);margin:0;max-width:40rem;font:1.1rem/1.5 var(--serif)}
.contadores{display:flex;flex-wrap:wrap;gap:8px;margin:18px 0 0;padding:0;list-style:none}
.contadores li{display:flex;align-items:center;gap:8px;background:var(--surface);border:1px solid var(--line);border-radius:99px;padding:5px 12px 5px 6px;font-size:.88rem}
.dot{width:14px;height:14px;border-radius:50%;flex:none}
.dot.rojo{background:var(--rojo)}.dot.amarillo{background:var(--amarillo)}.dot.verde{background:var(--verde)}
.filters{display:grid;gap:10px;margin:18px 0 8px;grid-template-columns:minmax(0,1fr) auto}
.filters input,.filters select{width:100%;font:inherit;font-size:.95rem;padding:10px 14px;border-radius:10px;
border:1px solid var(--line);background:var(--surface);color:var(--ink)}
.chips{display:flex;gap:6px;flex-wrap:wrap;grid-column:1/-1}
.chips button{border:1px solid var(--line);background:var(--surface);color:var(--muted);border-radius:99px;
padding:5px 12px;font:600 .82rem var(--sans);cursor:pointer;display:inline-flex;gap:6px;align-items:center}
.chips button[aria-pressed="true"]{background:var(--ink);color:var(--paper);border-color:var(--ink)}
.lista{display:grid;gap:12px;padding:0;margin:14px 0;list-style:none}
.lista a.entrada{display:grid;grid-template-columns:auto 1fr;gap:16px;align-items:start;text-decoration:none;color:var(--ink);
background:var(--surface);border:1px solid var(--line);border-radius:12px;padding:16px 18px}
.lista a.entrada:hover{border-color:var(--accent)}
.mini{background:var(--housing);border-radius:10px;padding:5px;display:grid;gap:4px}
.mini b{width:12px;height:12px;border-radius:50%;background:var(--lamp-off)}
.mini b.on.rojo{background:#e0402f}.mini b.on.amarillo{background:#f0a817}.mini b.on.verde{background:#2fbf78}
.lista h2{font-size:1.15rem;margin:2px 0 4px}
.lista p{margin:0;color:var(--muted);font-size:.94rem}
.lista .meta{font-size:.84rem;color:var(--muted);display:flex;gap:6px 14px;flex-wrap:wrap}
.grupo{margin:22px 0 0}
.grupo > h2{font-size:1rem;color:var(--muted);font-weight:650;margin:0 0 10px}
.vacio{color:var(--muted);padding:30px 0}
.langs{display:grid;gap:14px;grid-template-columns:repeat(auto-fit,minmax(240px,1fr));margin:24px 0 40px}
.langs a{display:block;text-decoration:none;color:var(--ink);background:var(--surface);border:1px solid var(--line);border-radius:14px;padding:22px}
.langs a:hover{border-color:var(--accent)}
.langs strong{font-size:1.5rem;display:block}.langs span{color:var(--muted)}

@media (max-width:760px){.hero{grid-template-columns:1fr;gap:22px;padding-top:28px}
.light{flex-direction:row;justify-content:flex-start}.housing{grid-auto-flow:column;border-radius:22px;padding:10px}
.lamp{width:30px;height:30px}.resumen{grid-template-columns:1fr}.fila{grid-template-columns:1fr;gap:4px}
dl.glos{grid-template-columns:1fr;gap:2px}dl.glos dd{margin-bottom:10px}.filters{grid-template-columns:1fr}
.nav{order:3;width:100%}.controls{flex-wrap:nowrap;gap:4px;width:100%}.seg button{padding:5px 8px}.btn{padding:6px 8px}.alerta dl{grid-template-columns:1fr}.alerta dd{margin-bottom:6px}}
@media print{.topbar,.controls,.no-print,[popover],.filters{display:none!important}
:root{--paper:#fff;--surface:#fff;--sunken:#f1f1f1}body{font-size:10.5pt;color:#000}
[data-level="basic"] .deep{display:block!important}
.medida,.alerta,.esencial,.medidor,.puede > div,.mito > div,.tecnico{break-inside:avoid;box-shadow:none}
.lamp.on{box-shadow:none}a{color:#000}.fuentes a::after,.src a::after{content:" (" attr(href) ")";font-size:8.5pt;word-break:break-all}
.term{border:0}main section{padding:14px 0}}
"""

# ---------------------------------------------------------------- scripts (se autorizan por hash en la CSP)
JS_COMUN = r"""
(function(){
  var d=document.documentElement;
  function get(k){try{return localStorage.getItem(k)}catch(e){return null}}
  function set(k,v){try{localStorage.setItem(k,v)}catch(e){}}
  function tema(t){if(t==="light"||t==="dark"){d.setAttribute("data-theme",t)}else{d.removeAttribute("data-theme")}
    document.querySelectorAll("[data-theme-btn]").forEach(function(b){b.setAttribute("aria-pressed",String(b.getAttribute("data-theme-btn")===(t||"auto")))})}
  tema(get("zt-theme")||"auto");
  document.querySelectorAll("[data-theme-btn]").forEach(function(b){b.addEventListener("click",function(){
    var t=b.getAttribute("data-theme-btn");set("zt-theme",t);tema(t)})});
  document.querySelectorAll("[data-print]").forEach(function(b){b.addEventListener("click",function(){window.print()})});
  window.ZT={get:get,set:set};
})();
"""

JS_EDICION = r"""
(function(){
  var b=document.body;
  function nivel(n){b.setAttribute("data-level",n);
    document.querySelectorAll("[data-level-btn]").forEach(function(x){x.setAttribute("aria-pressed",String(x.getAttribute("data-level-btn")===n))})}
  nivel(window.ZT.get("zt-level")==="deep"?"deep":"basic");
  document.querySelectorAll("[data-level-btn]").forEach(function(x){x.addEventListener("click",function(){
    var n=x.getAttribute("data-level-btn");window.ZT.set("zt-level",n);nivel(n)})});
  if(!HTMLElement.prototype.hasOwnProperty("popover")){document.querySelectorAll(".term").forEach(function(t){
    t.addEventListener("click",function(){nivel("deep");var g=document.getElementById("glosario");if(g)g.scrollIntoView()})})}
})();
"""

JS_FILTRO = r"""
(function(){
  var q=document.getElementById("q"),sel=document.getElementById("sel"),vacio=document.getElementById("vacio"),
      items=[].slice.call(document.querySelectorAll("[data-text]")),grupos=[].slice.call(document.querySelectorAll(".grupo")),chip="todos";
  document.querySelectorAll("[data-chip]").forEach(function(b){b.addEventListener("click",function(){chip=b.getAttribute("data-chip");
    document.querySelectorAll("[data-chip]").forEach(function(x){x.setAttribute("aria-pressed",String(x===b))});filtrar()})});
  function filtrar(){var t=(q.value||"").toLowerCase().trim(),s=sel?sel.value:"",n=0;
    items.forEach(function(li){var ok=(!t||li.getAttribute("data-text").indexOf(t)>-1)&&(!s||li.getAttribute("data-sel")===s)&&
      (chip==="todos"||(" "+li.getAttribute("data-chip")+" ").indexOf(" "+chip+" ")>-1);li.hidden=!ok;if(ok)n++});
    grupos.forEach(function(g){g.hidden=!g.querySelector("[data-text]:not([hidden])")});vacio.hidden=n>0}
  if(!items.length){return}
  q.addEventListener("input",filtrar);if(sel)sel.addEventListener("change",filtrar);
})();
"""

FAVICON = ('<link rel="icon" href="data:image/svg+xml,%3Csvg xmlns=%27http://www.w3.org/2000/svg%27 viewBox=%270 0 32 32%27%3E'
           '%3Crect x=%279%27 width=%2714%27 height=%2732%27 rx=%277%27 fill=%27%231a2233%27/%3E'
           '%3Ccircle cx=%2716%27 cy=%277%27 r=%274%27 fill=%27%23e0402f%27/%3E%3Ccircle cx=%2716%27 cy=%2716%27 r=%274%27 fill=%27%23f0a817%27/%3E'
           '%3Ccircle cx=%2716%27 cy=%2725%27 r=%274%27 fill=%27%232fbf78%27/%3E%3C/svg%3E">')

def pagina(lang, titulo, desc, cuerpo, js, body_attrs="", alt=None, feed=None):
    script = JS_COMUN + js
    csp = (f"default-src 'none'; style-src {sha(CSS)}; script-src {sha(script)}; img-src data:; "
           "base-uri 'none'; form-action 'none'")
    extra = ""
    if alt:
        extra += f'<link rel="alternate" hreflang="{T[lang]["otro_lang"]}" href="{alt}">\n'
    if feed:
        extra += f'<link rel="alternate" type="application/rss+xml" title="ZeroTrace" href="{feed}">\n'
    return f"""<!doctype html>
<html lang="{'es-ES' if lang == 'es' else 'en-US'}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta http-equiv="Content-Security-Policy" content="{csp}">
<meta name="referrer" content="no-referrer">
<meta name="description" content="{html.escape(desc)}">
<title>{html.escape(titulo)}</title>
{FAVICON}
{extra}<style>{CSS}</style>
</head>
<body{body_attrs}>
{cuerpo}
<script>{script}</script>
</body>
</html>
"""

def marca(nivel="amarillo"):
    return "".join(f'<b class="on"></b>' if n == nivel else "<b></b>" for n in ("rojo", "amarillo", "verde"))

def topbar(lang, raiz, otro_href, con_nivel, actual=""):
    t = T[lang]
    nivel = ""
    if con_nivel:
        nivel = (f'<div class="seg" role="group" aria-label="{t["nivel"]}">'
                 f'<button type="button" data-level-btn="basic" aria-pressed="true">{t["basico"]}</button>'
                 f'<button type="button" data-level-btn="deep" aria-pressed="false">{t["fondo"]}</button></div>')
    cur = lambda k: ' aria-current="page"' if actual == k else ""
    return f"""<div class="topbar"><div class="wrap">
<a class="brand" href="{raiz}index.html"><i aria-hidden="true">{marca()}</i>ZeroTrace</a>
<nav class="nav" aria-label="ZeroTrace"><a href="{raiz}index.html"{cur('archivo')}>{t['archivo']}</a>
<a href="{raiz}{REGISTRO[lang]}.html"{cur('registro')}>{t['registro']}</a></nav>
<div class="controls">{nivel}
<div class="seg" role="group" aria-label="{t['tema']}">
<button type="button" data-theme-btn="auto" aria-pressed="true" title="{t['auto']}">A<span class="sr"> {t['auto']}</span></button>
<button type="button" data-theme-btn="light" aria-pressed="false" title="{t['claro']}">☀︎<span class="sr"> {t['claro']}</span></button>
<button type="button" data-theme-btn="dark" aria-pressed="false" title="{t['oscuro']}">☾<span class="sr"> {t['oscuro']}</span></button></div>
<button type="button" class="btn" data-print title="{t['imprimir']}">⎙<span class="sr"> {t['imprimir']}</span></button>
<a class="btn" href="{otro_href}" hreflang="{t['otro_lang']}">{t['otro_idioma']}</a>
</div></div></div>"""

def pie(lang, raiz):
    t = T[lang]
    return (f'<footer><div class="wrap"><p>ZeroTrace · <a href="{raiz}index.html">{t["archivo"]}</a> · '
            f'<a href="{raiz}{REGISTRO[lang]}.html">{t["registro"]}</a> · <a href="{raiz}feed.xml">{t["rss"]}</a></p>'
            f'<p>{t["licencia"]}</p></div></footer>')

# ---------------------------------------------------------------- bloques
def alerta_html(a, lang, glos, con_publicada=None):
    t = T[lang]
    x = a[lang]
    cves = "".join(f"<code>{c}</code>" for c in a["cves"])
    fuentes = " · ".join(enlace(f, lang) for f in a["fuentes"])
    pub = ""
    if con_publicada:
        pub = f'<p class="src">{t["publicada"]} <a href="{con_publicada}">{fecha_corta(a["fecha"], lang)}</a></p>'
    return f"""<article class="alerta {a['nivel']}" id="{a['id']}">
<header><span class="pill {a['nivel']}">{t['niveles'][a['nivel']]}</span><h3>{ih(x['titulo'], glos)}</h3></header>
<dl><dt>{t['afecta']}</dt><dd>{ih(x['afecta'], glos)}</dd>
<dt>{t['que_hacer']}</dt><dd>{ih(x['accion'], glos)}</dd>
<dt class="deep">{t['detalle']}</dt><dd class="deep">{ih(x['detalle'], glos)}<div class="cves">{cves}</div></dd></dl>
<p class="src">{fuentes}</p>{pub}</article>"""

def edicion_html(e, alertas, focos, twin):
    lang, t = e["idioma"], T[e["idioma"]]
    g = e.get("glosario", {})
    h = lambda s: ih(s, g)
    foco = focos[e["foco"]]
    raiz = "../../../"
    sem = e["semaforo"]
    nivel = sem["nivel"]
    lamparas = "".join(f'<div class="lamp {n}{" on" if n == nivel else ""}"></div>' for n in ("rojo", "amarillo", "verde"))

    if sem["alertas"]:
        lista = "".join(alerta_html(alertas[i], lang, g) for i in sem["alertas"])
        bloque_sem = f'<div class="alertas">{lista}</div><p class="nota">{t["nota_sem"]} <a href="{raiz}{REGISTRO[lang]}.html">{t["ver_registro"]}</a>.</p>'
    else:
        bloque_sem = (f'<div class="calma"><p><strong>{t["sin_alertas"]}</strong></p><p>{t["sin_alertas_txt"]}</p>'
                      f'<p><a href="{raiz}{REGISTRO[lang]}.html">{t["ver_registro"]}</a></p></div>')

    basico = "".join(f"<p>{h(p)}</p>" for p in e["basico"]["parrafos"])
    esencial = "".join(f"<li>{h(x)}</li>" for x in e["basico"]["esencial"])
    r = e["riesgo"]
    medidores = "".join(f"""<div class="medidor"><div class="top"><span>{t[k]}: {t.get('valores_' + k, t['valores'])[r[k]['nivel']]}</span>
<span class="barras {r[k]['nivel']}" aria-hidden="true"><i></i><i></i><i></i></span></div><p>{h(r[k]['texto'])}</p></div>"""
                        for k in ("probabilidad", "impacto"))
    fondo = "".join(f"<h3>{h(s['titulo'])}</h3>" + "".join(f"<p>{h(p)}</p>" for p in s["parrafos"]) for s in e["fondo"])
    ataque = "".join(f"<li><strong>{h(p['titulo'])}</strong><p>{h(p['texto'])}</p></li>" for p in e["ataque"])
    puede = "".join(f"<li>{h(x)}</li>" for x in e["atacante"]["puede"])
    no_puede = "".join(f"<li>{h(x)}</li>" for x in e["atacante"]["no_puede"])

    medidas = ""
    v = t["valores"]
    for m in e["medidas"]:
        plats = "".join(f'<div class="plataforma"><h4>{html.escape(k)}</h4><ol>' + "".join(f"<li>{h(x)}</li>" for x in pasos) + "</ol></div>"
                        for k, pasos in m["pasos"].items())
        deep = m["para"] in ("avanzado", "paranoico")
        tag = f'<span class="deep-tag">{t["solo_fondo"]}</span>' if deep else ""
        medidas += f"""<article class="medida{' deep' if deep else ''}"><h3>{h(m['titulo'])}{tag}</h3>
<ul class="badges"><li class="{m['impacto']}">{t['impacto']}: {v[m['impacto']]}</li><li>{t['esfuerzo']}: {v[m['esfuerzo']]}</li>
<li>⏱ {html.escape(m['tiempo'])}</li><li>{t['para']}: {v[m['para']]}</li></ul>
<p>{h(m['texto'])}</p><div class="plataformas">{plats}</div></article>"""

    comprobar = "".join(f'<div class="fila"><h3>{h(c["titulo"])}</h3><p>{h(c["texto"])}</p></div>' for c in e["comprobar"])
    innecesario = "".join(f'<div class="fila"><h3>{h(c["titulo"])}</h3><p>{h(c["texto"])}</p></div>' for c in e["innecesario"])
    mi = e["mito"]
    tecnico = "".join(f"<h3>{h(s['titulo'])}</h3>" + "".join(f"<p>{h(p)}</p>" for p in s["parrafos"]) for s in e["tecnico"])
    glos_dl = "".join(f"<dt>{html.escape(x[0])}</dt><dd>{html.escape(x[1])}</dd>" for x in g.values())
    pops = "".join(f'<div popover id="g-{k}" class="gl-pop"><strong>{html.escape(x[0])}</strong>{html.escape(x[1])}</div>' for k, x in g.items())
    fuentes = "".join(f"<li>{enlace(f)}</li>" for f in e["fuentes"])
    disp = "".join(f"<li>{ICONOS_DISP[d]} {t['disp'][d]}</li>" for d in e["dispositivos"])

    cuerpo = topbar(lang, raiz, twin, True) + f"""
<main class="wrap">
<header class="hero">
<div><p class="date">{fecha_larga(e['fecha'], lang)} · {foco['icono']} {foco[lang]}</p>
<h1>{h(e['titulo'])}</h1><p class="sub">{h(e['subtitulo'])}</p>
<ul class="facts"><li>{t['lectura']}: {e['lectura']['basico']} {t['min']} · {t['fondo']}: {e['lectura']['fondo']} {t['min']}</li>{disp}</ul></div>
<div class="light" role="img" aria-label="{t['semaforo']}: {t['niveles_dia'][nivel]}"><div class="housing">{lamparas}</div>
<div class="label">{t['niveles_dia'][nivel]}</div></div>
</header>

<section aria-labelledby="s-sem"><h2 id="s-sem">{t['semaforo']}</h2>{bloque_sem}</section>

<section aria-labelledby="s-b"><h2 id="s-b">{t['en2']}</h2>
<div class="resumen"><div class="prose">{basico}</div>
<aside class="esencial"><h3>{t['esencial']}</h3><ul>{esencial}</ul></aside></div>
<h3>{t['riesgo']}</h3><div class="riesgo">{medidores}</div></section>

<section class="deep" aria-labelledby="s-c"><h2 id="s-c">{t['como']}</h2><div class="prose">{fondo}</div></section>

<section class="deep" aria-labelledby="s-a"><h2 id="s-a">{t['ataque']}</h2><ol class="pasos-ataque">{ataque}</ol></section>

<section class="deep" aria-labelledby="s-p"><h2 id="s-p">{t['atacante']}</h2>
<div class="puede"><div class="si"><h3>{t['puede']}</h3><ul>{puede}</ul></div><div class="no"><h3>{t['no_puede']}</h3><ul>{no_puede}</ul></div></div></section>

<section aria-labelledby="s-m"><h2 id="s-m">{t['medidas']}</h2><div class="medidas">{medidas}</div></section>

<section aria-labelledby="s-v"><h2 id="s-v">{t['comprobar']}</h2><div class="filas">{comprobar}</div></section>

<section class="innecesario" aria-labelledby="s-n"><h2 id="s-n">{t['innecesario']}</h2><div class="filas">{innecesario}</div></section>

<section aria-labelledby="s-mi"><h2 id="s-mi">{t['mito']}</h2>
<div class="mito"><div class="creencia"><h3>{t['mito_l']}</h3><p>{h(mi['mito'])}</p></div>
<div class="hecho"><h3>{t['realidad_l']}</h3><p>{h(mi['realidad'])}</p><p class="src">{enlace(mi['fuente'])}</p></div></div></section>

<section class="deep" aria-labelledby="s-t"><h2 id="s-t">{t['tecnico']}</h2><div class="tecnico prose">{tecnico}</div></section>

<section class="deep" id="glosario" aria-labelledby="s-g"><h2 id="s-g">{t['glosario']}</h2><dl class="glos">{glos_dl}</dl></section>

<section aria-labelledby="s-s"><h2 id="s-s">{t['fuentes']}</h2><ol class="fuentes">{fuentes}</ol></section>
</main>
{pie(lang, raiz)}
{pops}"""
    return pagina(lang, f"{plano(e['titulo'])} · ZeroTrace", plano(e["subtitulo"]), cuerpo, JS_EDICION,
                  body_attrs=f' data-level="basic"', alt=twin, feed=f"{raiz}feed.xml")

# ---------------------------------------------------------------- Markdown
def alerta_md(a, lang):
    t, x = T[lang], a[lang]
    return [f"### {t['niveles'][a['nivel']]}: {md(x['titulo'])}", "",
            f"- **{t['afecta']}:** {md(x['afecta'])}",
            f"- **{t['que_hacer']}:** {md(x['accion'])}",
            f"- **{t['detalle']}:** {md(x['detalle'])}",
            f"- **CVE:** " + ", ".join(f"`{c}`" for c in a["cves"]),
            "- " + " · ".join(f"[{titulo_fuente(f, lang)}]({f['url']})" for f in a["fuentes"]), ""]

def edicion_md(e, alertas, focos):
    lang, t = e["idioma"], T[e["idioma"]]
    foco, sem, v = focos[e["foco"]], e["semaforo"], T[e["idioma"]]["valores"]
    cves = sorted({c for i in sem["alertas"] for c in alertas[i]["cves"]})
    L = ["---", f"fecha: {e['fecha']}", f"idioma: {'es-ES' if lang == 'es' else 'en-US'}", f"foco: {e['foco']}",
         f"concepto: {e['concepto']}", f"titulo: \"{plano(e['titulo'])}\"", f"dispositivos: [{', '.join(e['dispositivos'])}]",
         f"semaforo: {sem['nivel']}", f"alertas: [{', '.join(sem['alertas'])}]", f"cves: [{', '.join(cves)}]",
         f"lectura_min: {{basico: {e['lectura']['basico']}, fondo: {e['lectura']['fondo']}}}", "---", "",
         f"# {md(e['titulo'])}", "", f"> {md(e['subtitulo'])}", "",
         f"{fecha_larga(e['fecha'], lang)} · {foco['icono']} {foco[lang]} · {t['lectura']}: {e['lectura']['basico']} {t['min']} "
         f"({t['fondo']}: {e['lectura']['fondo']} {t['min']})", "",
         f"## {t['semaforo']}: {t['niveles_dia'][sem['nivel']]}", ""]
    if sem["alertas"]:
        for i in sem["alertas"]:
            L += alerta_md(alertas[i], lang)
        L += [f"_{t['nota_sem']}_ [{t['ver_registro']}](../../../{REGISTRO[lang]}.md)", ""]
    else:
        L += [f"**{t['sin_alertas']}** {t['sin_alertas_txt']}", ""]
    L += [f"## {t['en2']}", ""] + [md(p) + "\n" for p in e["basico"]["parrafos"]]
    L += [f"**{t['esencial']}**", ""] + [f"- {md(x)}" for x in e["basico"]["esencial"]] + [""]
    r = e["riesgo"]
    L += [f"**{t['riesgo']}**", "", f"- **{t['probabilidad']}: {t.get('valores_probabilidad', v)[r['probabilidad']['nivel']]}.** {md(r['probabilidad']['texto'])}",
          f"- **{t['impacto']}: {v[r['impacto']['nivel']]}.** {md(r['impacto']['texto'])}", ""]
    L += [f"## {t['como']}", ""]
    for s in e["fondo"]:
        L += [f"### {md(s['titulo'])}", ""] + [md(p) + "\n" for p in s["parrafos"]]
    L += [f"## {t['ataque']}", ""] + [f"{i}. **{md(p['titulo'])}.** {md(p['texto'])}" for i, p in enumerate(e["ataque"], 1)] + [""]
    L += [f"## {t['atacante']}", "", f"**{t['puede']}**", ""] + [f"- {md(x)}" for x in e["atacante"]["puede"]]
    L += ["", f"**{t['no_puede']}**", ""] + [f"- {md(x)}" for x in e["atacante"]["no_puede"]] + [""]
    L += [f"## {t['medidas']}", ""]
    for m in e["medidas"]:
        L += [f"### {md(m['titulo'])}", "", f"`{t['impacto']}: {v[m['impacto']]}` `{t['esfuerzo']}: {v[m['esfuerzo']]}` "
              f"`⏱ {m['tiempo']}` `{t['para']}: {v[m['para']]}`", "", md(m["texto"]), ""]
        for k, pasos in m["pasos"].items():
            L += [f"**{k}**", ""] + [f"{i}. {md(p)}" for i, p in enumerate(pasos, 1)] + [""]
    L += [f"## {t['comprobar']}", ""] + [f"- **{md(c['titulo'])}.** {md(c['texto'])}" for c in e["comprobar"]] + [""]
    L += [f"## {t['innecesario']}", ""] + [f"- **{md(c['titulo'])}.** {md(c['texto'])}" for c in e["innecesario"]] + [""]
    mi = e["mito"]
    L += [f"## {t['mito']}", "", f"- **{t['mito_l']}:** {md(mi['mito'])}",
          f"- **{t['realidad_l']}:** {md(mi['realidad'])} ([{mi['fuente']['titulo']}]({mi['fuente']['url']}))", ""]
    L += [f"## {t['tecnico']}", ""]
    for s in e["tecnico"]:
        L += [f"### {md(s['titulo'])}", ""] + [md(p) + "\n" for p in s["parrafos"]]
    L += [f"## {t['glosario']}", ""] + [f"- **{x[0]}:** {x[1]}" for x in e["glosario"].values()] + [""]
    L += [f"## {t['fuentes']}", ""] + [f"1. [{f['titulo']}]({f['url']})" for f in e["fuentes"]] + [""]
    L += ["---", "", f"<sub>ZeroTrace · {t['licencia']}</sub>", ""]
    return "\n".join(L)

# ---------------------------------------------------------------- archivo de ediciones
def mini(nivel):
    return '<span class="mini" aria-hidden="true">' + "".join(
        f'<b class="on {n}"></b>' if n == nivel else "<b></b>" for n in ("rojo", "amarillo", "verde")) + "</span>"

def indice_html(lang, eds, focos):
    t = T[lang]
    items = ""
    for e in eds:
        f = focos[e["foco"]]
        texto = html.escape((plano(e["titulo"]) + " " + plano(e["subtitulo"]) + " " + f[lang]).lower())
        disp = " ".join(f"{ICONOS_DISP[d]} {t['disp'][d]}" for d in e["dispositivos"])
        items += f"""<li data-sel="{e['foco']}" data-chip="{' '.join(e['dispositivos'])}" data-text="{texto}">
<a class="entrada" href="{ruta_edicion(lang, e['fecha'])}">{mini(e['semaforo']['nivel'])}<div>
<div class="meta"><span>{fecha_larga(e['fecha'], lang)}</span><span>{f['icono']} {f[lang]}</span></div>
<h2>{ih(e['titulo'])}</h2><p>{ih(e['subtitulo'])}</p><div class="meta"><span>{disp}</span></div></div></a></li>"""
    opciones = "".join(f'<option value="{k}">{x["icono"]} {x[lang]}</option>' for k, x in focos.items())
    disp_base = ["smartphone", "tablet", "portatil", "sobremesa", "tv", "wearable", "iot", "router"]
    chips = f'<button type="button" data-chip="todos" aria-pressed="true">{t["todos_disp"]}</button>' + "".join(
        f'<button type="button" data-chip="{d}" aria-pressed="false">{ICONOS_DISP[d]} {t["disp"][d]}</button>' for d in disp_base)
    otro = f"../{t['otro_lang']}/index.html"
    cuerpo = topbar(lang, "", otro, False, "archivo") + f"""
<main class="wrap">
<header class="page-head"><h1>ZeroTrace</h1><p>{t['tagline']}</p></header>
<div class="filters no-print">
<input id="q" type="search" placeholder="{t['buscar']}" aria-label="{t['buscar']}" autocomplete="off">
<select id="sel" aria-label="{t['foco']}"><option value="">{t['todos_focos']}</option>{opciones}</select>
<div class="chips" role="group" aria-label="{t['dispositivos']}">{chips}</div></div>
<ul class="lista">{items}</ul><p id="vacio" class="vacio" hidden>{t['sin_resultados']}</p>{'' if eds else f'<p class="vacio">{t["sin_ediciones"]}</p>'}
</main>
{pie(lang, '')}"""
    return pagina(lang, f"ZeroTrace · {t['archivo']}", t["tagline"], cuerpo, JS_FILTRO, alt=otro, feed="feed.xml")

# ---------------------------------------------------------------- registro de alertas
def registro_html(lang, lista, focos):
    t = T[lang]
    cuenta = {n: sum(1 for a in lista if a["nivel"] == n) for n in ("rojo", "amarillo", "verde")}
    contadores = "".join(f'<li><span class="dot {n}"></span>{cuenta[n]} · {t["niveles"][n]}</li>' for n in ("rojo", "amarillo", "verde"))
    chips = f'<button type="button" data-chip="todos" aria-pressed="true">{t["todos"]}</button>' + "".join(
        f'<button type="button" data-chip="{n}" aria-pressed="false"><span class="dot {n}"></span>{t["niveles"][n]}</button>'
        for n in ("rojo", "amarillo", "verde"))
    grupos, por_fecha = "", {}
    for a in lista:
        por_fecha.setdefault(a["fecha"], []).append(a)
    for fecha in sorted(por_fecha, reverse=True):
        filas = ""
        for a in sorted(por_fecha[fecha], key=lambda a: ORDEN_NIVEL[a["nivel"]]):
            texto = html.escape(" ".join([plano(a[lang]["titulo"]), plano(a[lang]["afecta"]), plano(a[lang]["detalle"])] + a["cves"]).lower())
            filas += f'<div data-chip="{a["nivel"]}" data-text="{texto}">' + alerta_html(
                a, lang, None, con_publicada=ruta_edicion(lang, a["fecha"])) + "</div>"
        grupos += f'<section class="grupo" aria-label="{fecha_larga(fecha, lang)}"><h2>{fecha_larga(fecha, lang)}</h2><div class="alertas">{filas}</div></section>'
    otro = f"../{t['otro_lang']}/{REGISTRO[t['otro_lang']]}.html"
    cuerpo = topbar(lang, "", otro, False, "registro") + f"""
<main class="wrap">
<header class="page-head"><h1>{t['registro']}</h1><p>{t['registro_sub']}</p>
<ul class="contadores">{contadores}</ul></header>
<div class="filters no-print"><input id="q" type="search" placeholder="{t['buscar_alerta']}" aria-label="{t['buscar_alerta']}" autocomplete="off">
<div class="chips" role="group" aria-label="{t['semaforo']}">{chips}</div></div>
{grupos}<p id="vacio" class="vacio" hidden>{t['sin_resultados']}</p>{'' if lista else f'<p class="vacio">{t["sin_registro"]}</p>'}
</main>
{pie(lang, '')}"""
    return pagina(lang, f"{t['registro']} · ZeroTrace", t["registro_sub"], cuerpo, JS_FILTRO, alt=otro, feed="feed.xml")

def registro_md(lang, lista):
    t = T[lang]
    L = [f"# {t['registro']}", "", t["registro_sub"], "",
         "| " + " | ".join([("Fecha" if lang == "es" else "Date"), ("Nivel" if lang == "es" else "Level"),
                            ("Alerta" if lang == "es" else "Alert"), "CVE"]) + " |", "|---|---|---|---|"]
    for a in sorted(lista, key=lambda a: (a["fecha"], -ORDEN_NIVEL[a["nivel"]]), reverse=True):
        L.append(f"| [{fecha_corta(a['fecha'], lang)}]({ruta_edicion(lang, a['fecha']).replace('.html', '.md')}) | "
                 f"{t['niveles'][a['nivel']]} | {plano(a[lang]['titulo'])} | {', '.join(a['cves'])} |")
    return "\n".join(L + ["", f"<sub>ZeroTrace · {t['licencia']}</sub>", ""])

# ---------------------------------------------------------------- RSS y portada
def feed_xml(lang, eds, alertas, focos):
    t = T[lang]
    base = f"{BASE_URL}/{lang}/"
    items = ""
    for e in eds[:30]:
        url = base + ruta_edicion(lang, e["fecha"])
        d = datetime.fromisoformat(e["fecha"]).replace(hour=7, minute=40, tzinfo=TZ)
        resumen = plano(e["subtitulo"])
        if e["semaforo"]["alertas"]:
            resumen += " — " + " | ".join(f"{t['niveles'][alertas[i]['nivel']]}: {plano(alertas[i][lang]['titulo'])}" for i in e["semaforo"]["alertas"])
        items += f"""  <item>
    <title>{html.escape(plano(e['titulo']))}</title>
    <link>{url}</link>
    <guid isPermaLink="true">{url}</guid>
    <pubDate>{d.strftime('%a, %d %b %Y %H:%M:%S %z')}</pubDate>
    <category>{html.escape(focos[e['foco']][lang])}</category>
    <description>{html.escape(resumen)}</description>
  </item>
"""
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom">
<channel>
  <title>ZeroTrace ({lang.upper()})</title>
  <link>{base}</link>
  <atom:link href="{base}feed.xml" rel="self" type="application/rss+xml"/>
  <description>{html.escape(t['feed_desc'])}</description>
  <language>{'es-ES' if lang == 'es' else 'en-US'}</language>
  <lastBuildDate>{datetime.now(TZ).strftime('%a, %d %b %Y %H:%M:%S %z')}</lastBuildDate>
{items}</channel>
</rss>
"""

def portada_html():
    cuerpo = """<main class="wrap"><header class="page-head"><h1>ZeroTrace</h1>
<p>Ciberseguridad útil, un concepto al día.<br>Practical cybersecurity, one concept a day.</p></header>
<div class="langs"><a href="es/index.html" hreflang="es" lang="es"><strong>Español</strong><span>Leer en español</span></a>
<a href="en/index.html" hreflang="en" lang="en"><strong>English</strong><span>Read in English</span></a></div></main>
<footer><div class="wrap"><p>CC BY 4.0 · MIT · Sin cookies ni rastreadores. No cookies or trackers.</p></div></footer>"""
    return pagina("es", "ZeroTrace", "Ciberseguridad útil, un concepto al día. Practical cybersecurity, one concept a day.", cuerpo, "")

# ---------------------------------------------------------------- datos, validación e historial
def cargar():
    focos = json.loads((DATA / "focos.json").read_text(encoding="utf-8"))
    lista = json.loads((DATA / "alertas.json").read_text(encoding="utf-8"))
    eds = [json.loads(p.read_text(encoding="utf-8")) for p in sorted((DATA / "ediciones").glob("*.json"))]
    return focos, lista, eds

def validar(focos, lista, eds):
    err = []
    ids, cve_de = {}, {}
    for a in lista:
        if a["id"] in ids:
            err.append(f"Alerta duplicada en el registro: {a['id']}")
        ids[a["id"]] = a
        for c in a["cves"]:
            if c in cve_de:
                err.append(f"{c} ya se notificó en la alerta {cve_de[c]} y vuelve a aparecer en {a['id']}")
            cve_de.setdefault(c, a["id"])
        for lang in ("es", "en"):
            if lang not in a:
                err.append(f"La alerta {a['id']} no tiene versión '{lang}'")
    usos = {}
    por_fecha = {}
    for e in eds:
        if e["foco"] not in focos:
            err.append(f"{e['fecha']}.{e['idioma']}: foco desconocido '{e['foco']}'")
        por_fecha.setdefault(e["fecha"], {})[e["idioma"]] = e
        for i in e["semaforo"]["alertas"]:
            if i not in ids:
                err.append(f"{e['fecha']}.{e['idioma']}: la alerta '{i}' no existe en data/alertas.json")
                continue
            usos.setdefault(i, set()).add(e["fecha"])
            if ids[i]["fecha"] != e["fecha"]:
                err.append(f"{e['fecha']}.{e['idioma']}: la alerta '{i}' ya se notificó el {ids[i]['fecha']} y no puede repetirse")
    for i, fechas in usos.items():
        if len(fechas) > 1:
            err.append(f"La alerta '{i}' aparece en más de una edición: {', '.join(sorted(fechas))}")
    for fecha, langs in por_fecha.items():
        if set(langs) != {"es", "en"}:
            err.append(f"{fecha}: falta la versión {'en' if 'es' in langs else 'es'}")
        elif langs["es"]["semaforo"]["alertas"] != langs["en"]["semaforo"]["alertas"] or langs["es"]["foco"] != langs["en"]["foco"]:
            err.append(f"{fecha}: las versiones ES y EN no tienen el mismo foco o las mismas alertas")
    if err:
        raise ErrorValidacion("\n".join("  ✗ " + x for x in err))
    return ids

def historial(eds_es):
    orden = sorted(eds_es, key=lambda e: e["fecha"], reverse=True)
    conceptos = {}
    for e in sorted(eds_es, key=lambda e: e["fecha"]):
        conceptos.setdefault(e["foco"], []).append({"fecha": e["fecha"], "concepto": e["concepto"]})
    return {
        "actualizado": datetime.now(TZ).isoformat(timespec="seconds"),
        "regla": f"El foco de cada día se elige al azar entre los que no aparezcan en las {VENTANA_SIN_REPETIR} ediciones anteriores.",
        "focos_recientes": [e["foco"] for e in orden[:VENTANA_SIN_REPETIR]],
        "conceptos_por_foco": conceptos,
        "ediciones": [{"fecha": e["fecha"], "foco": e["foco"], "concepto": e["concepto"],
                       "semaforo": e["semaforo"]["nivel"], "alertas": e["semaforo"]["alertas"]} for e in orden],
    }

def escribir(ruta, texto):
    ruta.parent.mkdir(parents=True, exist_ok=True)
    ruta.write_text(texto, encoding="utf-8", newline="\n")
    print("  ·", ruta.relative_to(ROOT).as_posix())

def build():
    focos, lista, eds = cargar()
    alertas = validar(focos, lista, eds)
    por_lang = {"es": [], "en": []}
    for e in eds:
        por_lang[e["idioma"]].append(e)
    print("Validación correcta. Generando:")
    for lang, ls in por_lang.items():
        ls.sort(key=lambda e: e["fecha"], reverse=True)
        otro = T[lang]["otro_lang"]
        for e in ls:
            y, m = e["fecha"][:4], e["fecha"][5:7]
            carpeta = ROOT / lang / DIRS[lang] / y / m
            twin = f"../../../../{otro}/{ruta_edicion(otro, e['fecha'])}"
            escribir(carpeta / f"{e['fecha']}.md", edicion_md(e, alertas, focos))
            escribir(carpeta / f"{e['fecha']}.html", edicion_html(e, alertas, focos, twin))
        escribir(ROOT / lang / "index.html", indice_html(lang, ls, focos))
        escribir(ROOT / lang / f"{REGISTRO[lang]}.html", registro_html(lang, lista, focos))
        escribir(ROOT / lang / f"{REGISTRO[lang]}.md", registro_md(lang, lista))
        escribir(ROOT / lang / "feed.xml", feed_xml(lang, ls, alertas, focos))
    escribir(ROOT / "index.html", portada_html())
    escribir(DATA / "historial.json", json.dumps(historial(por_lang["es"]), ensure_ascii=False, indent=2) + "\n")

def siguiente_foco():
    focos, lista, eds = cargar()
    h = historial([e for e in eds if e["idioma"] == "es"])
    candidatos = [f for f in focos if f not in h["focos_recientes"]]
    elegido = random.SystemRandom().choice(candidatos)
    print(json.dumps({"foco": elegido, "excluidos": h["focos_recientes"],
                      "conceptos_ya_tratados": [c["concepto"] for c in h["conceptos_por_foco"].get(elegido, [])]},
                     ensure_ascii=False, indent=2))

def ya_notificado(cves):
    _, lista, _ = cargar()
    for c in cves:
        hit = next((a for a in lista if c.upper() in a["cves"]), None)
        print(f"{c}: " + (f"YA NOTIFICADO el {hit['fecha']} en {hit['id']}" if hit else "no notificado"))

if __name__ == "__main__":
    try:
        if "--siguiente-foco" in sys.argv:
            siguiente_foco()
        elif "--ya-notificado" in sys.argv:
            ya_notificado(sys.argv[sys.argv.index("--ya-notificado") + 1:])
        else:
            build()
    except ErrorValidacion as ex:
        print("La validación ha fallado; no se ha generado nada:\n" + str(ex), file=sys.stderr)
        sys.exit(1)
