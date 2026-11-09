<div align="center">

# 🚦 ZeroTrace

**Ciberseguridad útil, un concepto al día.**<br>
**Practical cybersecurity, one concept a day.**

[![Content License: CC BY 4.0](https://img.shields.io/badge/Content-CC_BY_4.0-blue.svg)](LICENSE-CONTENT.md)
[![Code License: MIT](https://img.shields.io/badge/Code-MIT-green.svg)](LICENSE)
[![Python 3.x](https://img.shields.io/badge/Python-3.x_No_Deps-yellow.svg)](tools/)
[![Privacy: Strict CSP](https://img.shields.io/badge/Privacy-Zero_Tracking-brightgreen.svg)](#privacidad--privacy)

[🌐 Leer en español](https://jossseluuu.github.io/ZeroTrace/es/) · [🌐 Read in English](https://jossseluuu.github.io/ZeroTrace/en/)

</div>

---

## 🇪🇸 Español

**ZeroTrace** es una newsletter diaria de ciberseguridad para todos los públicos. Cada edición aborda **un único concepto concreto** enfocado en los dispositivos de uso cotidiano: móviles, tablets, ordenadores, televisores, relojes, routers y la tecnología conectada (IoT). También cubre hábitos digitales, principios de programación segura y protocolos de respuesta a incidentes.

### 💡 ¿Cómo es cada edición?

* 🚦 **Semáforo del Día:** Muestra alertas relevantes sobre vulnerabilidades explotadas o de amplio impacto en dispositivos comunes. Cada alerta se publica una sola vez y se archiva en el [registro de alertas](https://jossseluuu.github.io/ZeroTrace/es/alertas.html).
* 📖 **Dos Niveles de Lectura:**
  * **Básico:** Diseñado para entender el problema y su solución en pocos minutos.
  * **A Fondo:** Explicación algo más técnica del mecanismo, la anatomía del ataque y la sección especializada para perfiles un poco más técnicos.
* ⚖️ **Medidas en su Justa Medida:** Los artículos contienen indicadores explícitos de impacto, esfuerzo o incluso sobre el público objetivo. También se incluye siempre lo que no hace falta hacer para evitar una sobrecarga de trabajo.
* 🔗 **Fuentes Verificables:** Se trata de ser totalmente transparente. Ningún dato o CVE se menciona sin su enlace directo a las fuentes primarias (INCIBE, CCN-CERT, CISA, NIST o fabricantes) desde las que se obtuvo.

---

## 🇺🇸 English

**ZeroTrace** is a daily cybersecurity newsletter for everyone. Each edition covers one concrete concept about everyday devices: phones, tablets, computers, TVs, watches, routers, and smart home tech. It also covers digital habits, secure coding practices, and incident response guides.

### 💡 What each edition looks like

* 🚦 **Today's Status:** Only critical alerts regarding actively exploited flaws or broad-impact vulnerabilities. Published only once and archived in the [alert log](https://jossseluuu.github.io/ZeroTrace/en/alerts.html).
* 📖 **Two Reading Levels:**
  * **Basic:** Clear overview to grasp the concept and take action in just a few minutes.
  * **Deep Dive:** Technical breakdown of the mechanism, attack vector, and dedicated details for technical readers.
* ⚖️ **Right-Sized Advice:** Every action has its impact, effort, and target audience. Includes guidance on what you don't need to do.
* 🔗 **Verifiable Sources:** Full transparency. Every fact or CVE links directly to primary sources (CISA, NIST, FTC, or vendor advisories).

---

## 🔒 Privacidad · Privacy

* 🇪🇸 **Español:** Las páginas no utilizan *cookies*, analíticas, scripts de terceros ni fuentes externas. Cada página implementa una Política de Seguridad de Contenido (CSP) estricta que prohíbe la ejecución de código externo.
* 🇺🇸 **English:** No cookies, no analytics, no third-party scripts, and no external fonts. Every page ships with a strict Content Security Policy (CSP) that only allows its own self-hosted assets.

## 📁 Estructura del repositorio · Repository Structure
```text
.
├── es/         # Ediciones en español (.md y .html), archivo, alertas y RSS
├── en/         # English editions (.md and .html), archive, alerts, and RSS
├── data/       # Contenido fuente: ediciones, alertas, focos e historial
└── tools/      # Generador estático (Python, 0 dependencias) y publicador local
```

## 🛠️ Desarrollo local · Local Development

El sitio utiliza un generador propio escrito en Python estándar (sin librerías ni dependencias externas).

```bash
# Generar sitio web / Build site
python3 tools/build.py
```

---

## 📜 Licencia · License

- Contenido · Content: [CC BY 4.0](LICENSE-CONTENT.md)
- Código y Plantillas · Code & Templates: [MIT](LICENSE)

🛡️ ¿Has encontrado un problema de seguridad en el sitio? / Found a security issue?
Consulta nuestra política de divulgación responsable en [SECURITY.md](SECURITY.md).
