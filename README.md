# Capa 1 — Diagnóstico y soporte técnico (causa raíz)

[![CI](https://github.com/lazarolpro/rca-telemetria/actions/workflows/ci.yml/badge.svg)](https://github.com/lazarolpro/rca-telemetria/actions/workflows/ci.yml)
[`lazarolpro/rca-telemetria`](https://github.com/lazarolpro/rca-telemetria) · parte del [portafolio de 6 capacidades](https://github.com/lazarolpro/portafolio)

**Capacidad demostrada:** diagnosticar fallas por causa raíz sobre telemetría
real de un equipo, en lugar de tratar síntomas.

## Problema real

En soporte técnico el tiempo se pierde interpretando a mano registros dispersos.
Sin un método, se cambian piezas hasta que "algo funciona" y la falla vuelve.
Esta herramienta convierte telemetría cruda en un **informe de causa raíz**
accionable y reproducible.

## Qué hace

- Lee un CSV de telemetría (temperatura, vibración, corriente, código de error).
- Detecta anomalías contra umbrales de fabricante (aviso / crítico).
- Clasifica la causa probable y prioriza el equipo más afectado.
- Emite un informe Markdown con línea de tiempo y acciones recomendadas.

## Videocaso narrado — caso real anonimizado (hotel en Goiânia, Brasil)

![Videocaso: diagnóstico remoto de causa raíz](assets/rca_demo_caso.gif)

Recorrido **narrado** de un caso real: la motobomba de presurización de agua del
hotel **Residencial Veredas Plaza** (nombre ficticio; datos anonimizados) deriva en
vibración, corriente y temperatura hasta disparar. La herramienta correlaciona las
tres señales y entrega la causa raíz, todo de forma remota.

- Video con voz en off: [`assets/rca_demo_caso.mp4`](assets/rca_demo_caso.mp4)
- Locución: **Ing. Ronny Díaz López** (voz masculina en español).

> La foto del motor es `VEM_motor_Zwickau.png` (ilustrativa), **CC BY-SA 4.0**
> (VEM motors GmbH, Wikimedia Commons); ninguna marca comercial aparece en el video.

## Demo visual (telemetría genérica)

![Demostración del diagnóstico de causa raíz](assets/rca_demo.gif)

La animación recorre la telemetría, marca las anomalías contra los umbrales del
fabricante y cierra con la causa raíz probable. Video completo:
[`assets/rca_demo.mp4`](assets/rca_demo.mp4).

## Evidencia que produce

- `data/telemetry_sample.csv` — datos deterministas (semilla fija).
- `data/caso_bomba_hotel.csv` — telemetría del caso del hotel (ficticia, semilla fija).
- `report.md`, `report_caso.md` — informes con causa raíz probable y acciones.
- `assets/rca_demo.mp4`, `rca_demo.gif`, `rca_poster.png` — demo visual animado.
- `assets/rca_demo_caso.mp4` (narrado), `rca_demo_caso.gif`, `rca_demo_caso_poster.png` — videocaso.
- `pytest` en verde.

## Stack

Python 3 (solo biblioteca estándar). Sin dependencias externas.

## Por qué le importa a la empresa

Responde a la necesidad de **resolver errores por la causa raíz** y no por el
síntoma: cada diagnóstico deja un informe auditable y repetible.
