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

## Cómo ejecutar

```bash
python rca.py --demo                       # genera datos de ejemplo + report.md
python rca.py --input data/telemetry_sample.csv --out report.md
python rca.py --input data.csv --json       # salida para pipelines
python -m pytest -q                         # pruebas
```

## Evidencia que produce

- `data/telemetry_sample.csv` — datos deterministas (semilla fija).
- `report.md` — informe con causa raíz probable y acciones.
- `pytest` en verde.

## Stack

Python 3 (solo biblioteca estándar). Sin dependencias externas.

## Por qué le importa a la empresa

Responde a la necesidad de **resolver errores por la causa raíz** y no por el
síntoma: cada diagnóstico deja un informe auditable y repetible.
