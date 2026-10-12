#!/usr/bin/env python3
"""Diagnostico de causa raiz (RCA) sobre telemetria de equipo.

Capacidad 1 - Soporte tecnico / analisis de causa raiz.

Lee un CSV de telemetria de un equipo industrial (temperatura, vibracion,
corriente y codigo de error), detecta anomalias contra umbrales, clasifica la
falla probable y emite un informe Markdown con la linea de tiempo y las acciones
recomendadas.

Uso:
    python rca.py --demo            # genera datos de ejemplo y el informe
    python rca.py --input data/telemetry_sample.csv --out report.md
    python rca.py --input data.csv --json   # salida JSON (para pipelines)

Solo usa la biblioteca estandar de Python 3.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import random
from collections import defaultdict
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from pathlib import Path

# Umbrales de alarma por magnitud. En un banco real vendrian de la hoja de datos
# del fabricante; aqui son valores didacticos y centralizados a proposito.
# Motor de referencia: WEG W22 IR3 Premium 7,5 cv (5,5 kW), 380 V, 4 polos,
# 60 Hz -> corriente a plena carga (FLA) ~= 11 A.
THRESHOLDS = {
    "temperature_c": {"warn": 75.0, "crit": 90.0, "unit": "C"},
    "vibration_mm_s": {"warn": 4.5, "crit": 7.1, "unit": "mm/s"},
    "current_a": {"warn": 10.0, "crit": 12.0, "unit": "A"},
}

# Mapa de codigos de error -> causa probable. Ampliable por el equipo de soporte.
ERROR_CODES = {
    "0": None,
    "E01": "Sobrecalentamiento del motor (ventilacion o rodamiento)",
    "E02": "Vibracion excesiva (desalineacion o desgaste de rodamiento)",
    "E03": "Sobrecorriente (carga mecanica o cortocircuito parcial)",
    "E04": "Fallo de comunicacion con el variador",
}

METRICS = list(THRESHOLDS.keys())


@dataclass
class Anomaly:
    timestamp: str
    device: str
    kind: str
    value: float | str
    severity: str
    cause: str


def _severity(value: float, spec: dict) -> str:
    if value >= spec["crit"]:
        return "critica"
    if value >= spec["warn"]:
        return "advertencia"
    return "normal"


def load_rows(path: Path) -> list[dict]:
    rows = []
    with path.open(newline="", encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            rows.append(row)
    return rows


def detect(rows: list[dict]) -> list[Anomaly]:
    out: list[Anomaly] = []
    for row in rows:
        ts = row.get("timestamp", "")
        dev = row.get("device", "desconocido")
        for metric, spec in THRESHOLDS.items():
            raw = row.get(metric, "")
            if raw in ("", None):
                continue
            try:
                value = float(raw)
            except ValueError:
                continue
            sev = _severity(value, spec)
            if sev == "normal":
                continue
            cause = _classify(metric, sev)
            out.append(Anomaly(ts, dev, metric, value, sev, cause))
        code = (row.get("error_code") or "0").strip()
        if code and code != "0":
            out.append(Anomaly(ts, dev, "error_code", code, "critica",
                               ERROR_CODES.get(code, f"Codigo {code} no catalogado")))
    return out


def _classify(metric: str, severity: str) -> str:
    base = {
        "temperature_c": "Elevacion termica: revisar refrigeracion y carga",
        "vibration_mm_s": "Vibracion alta: revisar alineacion y rodamientos",
        "current_a": "Consumo elevado: revisar carga mecanica y aislamiento",
    }[metric]
    return f"{base} (severidad {severity})"


def summarize(anomalies: list[Anomaly]) -> dict:
    by_device: dict[str, int] = defaultdict(int)
    by_kind: dict[str, int] = defaultdict(int)
    by_sev: dict[str, int] = defaultdict(int)
    for a in anomalies:
        by_device[a.device] += 1
        by_kind[a.kind] += 1
        by_sev[a.severity] += 1
    top = max(by_device.items(), key=lambda kv: kv[1])[0] if by_device else None
    crit = by_sev.get("critica", 0)
    return {
        "total": len(anomalies),
        "criticas": crit,
        "advertencias": by_sev.get("advertencia", 0),
        "dispositivo_mas_afectado": top,
        "por_tipo": dict(by_kind),
        "por_dispositivo": dict(by_device),
    }


def probable_root_cause(anomalies: list[Anomaly]) -> str:
    kinds = {a.kind for a in anomalies if a.severity == "critica"}
    if {"vibration_mm_s", "current_a"} & kinds:
        return "Desgaste mecanico del conjunto motor-rodamiento (vibracion + consumo)."
    if "temperature_c" in kinds:
        return "Deficiencia de refrigeracion o sobrecarga termica sostenida."
    if "error_code" in kinds:
        return "Falla reportada por el variador; revisar el codigo y su historico."
    return "Sin causa critica unica: patron dentro de tolerancias con avisos aislados."


def render_report(rows: list[dict], anomalies: list[Anomaly]) -> str:
    s = summarize(anomalies)
    lines = [
        "# Informe de diagnostico y causa raiz",
        "",
        f"- Registros analizados: **{len(rows)}**",
        f"- Anomalias: **{s['total']}** (criticas: {s['criticas']}, advertencias: {s['advertencias']})",
        f"- Dispositivo mas afectado: **{s['dispositivo_mas_afectado'] or 'ninguno'}**",
        f"- Causa raiz probable: **{probable_root_cause(anomalies)}**",
        "",
        "## Linea de tiempo de anomalias",
        "",
        "| Marca temporal | Equipo | Magnitud | Valor | Severidad | Causa probable |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for a in anomalies[:50]:
        lines.append(f"| {a.timestamp} | {a.device} | {a.kind} | {a.value} | {a.severity} | {a.cause} |")
    lines += [
        "",
        "## Acciones recomendadas",
        "",
        "1. Priorizar el equipo con mayor numero de eventos criticos.",
        "2. Inspeccion mecanica (alineacion, rodamientos, lubricacion).",
        "3. Verificar ventilacion, filtros y curva de carga.",
        "4. Registrar la reparacion y volver a medir para confirmar la causa.",
        "",
        "> Evidencia reproducible: `python rca.py --demo` regenera este informe.",
    ]
    return "\n".join(lines) + "\n"


def make_sample(path: Path, seed: int = 42) -> None:
    rng = random.Random(seed)
    start = datetime(2026, 3, 1, 8, 0, 0)
    devices = ["MOTOR-01", "BOMBA-02", "COMP-03"]
    rows = []
    for i in range(96):
        ts = (start + timedelta(minutes=15 * i)).isoformat(timespec="seconds")
        dev = devices[i % len(devices)]
        # Degradacion progresiva en MOTOR-01 a partir de la mitad de la serie.
        wear = (i - 48) / 48 if (i > 48 and dev == "MOTOR-01") else 0
        temp = 55 + 30 * max(wear, 0) + rng.uniform(-2, 2)
        vib = 2.0 + 6.5 * max(wear, 0) + rng.uniform(-0.3, 0.3)
        cur = 8.0 + 4.6 * max(wear, 0) + rng.uniform(-0.3, 0.3)
        code = "0"
        if dev == "MOTOR-01" and i > 80:
            code = "E02"
        rows.append({
            "timestamp": ts, "device": dev,
            "temperature_c": f"{temp:.1f}", "vibration_mm_s": f"{vib:.2f}",
            "current_a": f"{cur:.2f}", "error_code": code,
        })
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def main() -> int:
    parser = argparse.ArgumentParser(description="RCA sobre telemetria de equipo")
    parser.add_argument("--input", type=Path, default=Path("data/telemetry_sample.csv"))
    parser.add_argument("--out", type=Path, default=Path("report.md"))
    parser.add_argument("--demo", action="store_true", help="genera datos de ejemplo y el informe")
    parser.add_argument("--json", action="store_true", help="emite el resumen en JSON")
    args = parser.parse_args()

    if args.demo:
        make_sample(args.input)
        print(f"[ok] datos de ejemplo en {args.input}")

    rows = load_rows(args.input)
    anomalies = detect(rows)

    if args.json:
        print(json.dumps({
            "resumen": summarize(anomalies),
            "causa_raiz_probable": probable_root_cause(anomalies),
            "anomalias": [asdict(a) for a in anomalies],
        }, ensure_ascii=False, indent=2))
        return 0

    args.out.write_text(render_report(rows, anomalies), encoding="utf-8")
    s = summarize(anomalies)
    print(f"[ok] informe en {args.out} — {s['total']} anomalias "
          f"({s['criticas']} criticas) en {len(rows)} registros")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
