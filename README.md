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
- Informe del caso en PDF: [`assets/informe_caso_rca.pdf`](assets/informe_caso_rca.pdf)
- Documento fuente: [`caso_residencial_veredas_plaza.md`](caso_residencial_veredas_plaza.md)
- Locución: **Ronny Díaz López** (voz masculina en español).

Regenerar (opcional; requiere `matplotlib`, `ffmpeg` y `piper-tts`):

```bash
python viz_caso.py --input data/caso_bomba_hotel.csv   # video + gif + póster
python make_pdf.py                                     # informe PDF
```

> La voz preferida es `es-CU-ManuelNeural` vía `edge-tts` (masculina, Cuba); si el
> servicio externo no está disponible, el script cae automáticamente a la voz
> offline masculina `es_ES-davefx-medium` (Piper), que se descarga al primer uso.
> La foto del motor es `VEM_motor_Zwickau.png` (ilustrativa), **CC BY-SA 4.0**
> (VEM motors GmbH, Wikimedia Commons); ninguna marca comercial aparece en el video.

## Demo visual (telemetría genérica)

![Demostración del diagnóstico de causa raíz](assets/rca_demo.gif)

La animación recorre la telemetría, marca las anomalías contra los umbrales del
fabricante y cierra con la causa raíz probable. Video completo:
[`assets/rca_demo.mp4`](assets/rca_demo.mp4).

Regenerar el visual (opcional; requiere `matplotlib` y `ffmpeg`):

```bash
python viz.py
```

> El demo principal (`rca.py`) sigue usando solo la biblioteca estándar. El visual
> es una capa de presentación; sus archivos quedan versionados en `assets/`.

## Cómo ejecutar

```bash
python rca.py --demo                       # genera datos de ejemplo + report.md
python rca.py --input data/telemetry_sample.csv --out report.md
python rca.py --input data.csv --json       # salida para pipelines
python -m pytest -q                         # pruebas
```

## Evidencia que produce

- `data/telemetry_sample.csv` — datos deterministas (semilla fija).
- `data/caso_bomba_hotel.csv` — telemetría del caso del hotel (ficticia, semilla fija).
- `report.md`, `report_caso.md` — informes con causa raíz probable y acciones.
- `assets/rca_demo.mp4`, `rca_demo.gif`, `rca_poster.png` — demo visual animado.
- `assets/rca_demo_caso.mp4` (narrado), `rca_demo_caso.gif`, `rca_demo_caso_poster.png` — videocaso.
- `assets/informe_caso_rca.pdf` — informe del caso (RCA, motor y plan de acción).
- `pytest` en verde.

## Stack

Python 3 (solo biblioteca estándar). Sin dependencias externas.

## Por qué le importa a la empresa

Responde a la necesidad de **resolver errores por la causa raíz** y no por el
síntoma: cada diagnóstico deja un informe auditable y repetible.
