#!/usr/bin/env python3
"""Demo visual animado del diagnóstico de causa raíz (RCA).

Capacidad 1 - pieza visual de portafolio.

Reproduce, cuadro a cuadro, cómo la herramienta recorre la telemetría de un
equipo, marca las anomalías contra los umbrales del fabricante y desemboca en la
causa raíz probable. Sale como video (mp4), GIF (para el README) y un póster PNG
(estado final).

Uso:
    python viz.py                 # genera assets/rca_demo.mp4, .gif y _poster.png
    python viz.py --device MOTOR-01 --fps 24

Requiere matplotlib y ffmpeg SOLO para regenerar el visual; el demo principal
(rca.py) sigue usando únicamente la biblioteca estándar. Los archivos ya
renderizados quedan versionados en assets/, así que para verlos no hace falta
reinstalar nada.
"""

from __future__ import annotations

import argparse
from datetime import datetime
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.dates as mdates  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.animation import FFMpegWriter, FuncAnimation, PillowWriter  # noqa: E402

import rca  # noqa: E402

BG = "#0d1117"
PANEL = "#161b22"
GRID = "#30363d"
TXT = "#e6edf3"
DIM = "#8b949e"
CYAN = "#2aa9e0"
WARN = "#d29922"
CRIT = "#f85149"
OK = "#3fb950"

METRICS = ["temperature_c", "vibration_mm_s", "current_a"]
LABELS = {
    "temperature_c": "Temperatura",
    "vibration_mm_s": "Vibración",
    "current_a": "Corriente",
}


def _series(device: str, path: Path) -> dict:
    if not path.exists():
        rca.make_sample(path)
    rows = [r for r in rca.load_rows(path) if r.get("device") == device]
    times = [datetime.fromisoformat(r["timestamp"]) for r in rows]
    data: dict[str, list[float]] = {m: [float(r[m]) for r in rows] for m in METRICS}
    return {"times": times, "data": data, "n": len(rows),
            "anomalies": rca.detect(rows)}


def build_figure(device: str, series: dict):
    times = series["times"]
    fig, axes = plt.subplots(
        3, 1, figsize=(12.8, 7.2), dpi=100, sharex=True,
        gridspec_kw={"hspace": 0.32, "left": 0.08, "right": 0.97,
                     "top": 0.86, "bottom": 0.11},
    )
    fig.patch.set_facecolor(BG)

    fig.text(0.08, 0.945, "Diagnóstico de causa raíz", color=TXT,
             fontsize=21, fontweight="bold", ha="left", va="center")
    fig.text(0.08, 0.905, f"Telemetría en vivo · {device}", color=DIM,
             fontsize=11.5, ha="left", va="center")
    counter = fig.text(0.97, 0.925, "", color=TXT, fontsize=12, ha="right",
                       va="center", family="monospace")

    lines = {}
    warn_sc = {}
    crit_sc = {}
    playheads = {}
    for ax, metric in zip(axes, METRICS):
        spec = rca.THRESHOLDS[metric]
        ax.set_facecolor(PANEL)
        for spine in ax.spines.values():
            spine.set_color(GRID)
        ax.tick_params(colors=DIM, labelsize=9)
        ax.grid(True, color=GRID, linewidth=0.6, alpha=0.5)
        ax.axhline(spec["warn"], color=WARN, ls="--", lw=1.1, alpha=0.9)
        ax.axhline(spec["crit"], color=CRIT, ls="--", lw=1.1, alpha=0.9)
        ax.text(times[-1], spec["warn"], f" aviso {spec['warn']:g}{spec['unit']}",
                color=WARN, fontsize=7.5, va="bottom", ha="right")
        ax.text(times[-1], spec["crit"], f" crítico {spec['crit']:g}{spec['unit']}",
                color=CRIT, fontsize=7.5, va="top", ha="right")
        ax.set_ylabel(f"{LABELS[metric]} ({spec['unit']})", color=TXT, fontsize=10.5)

        (ln,) = ax.plot([], [], color=CYAN, lw=2.0, solid_capstyle="round")
        lines[metric] = ln
        warn_sc[metric] = ax.scatter([], [], s=42, color=WARN, zorder=5,
                                     edgecolors=BG, linewidths=0.8)
        crit_sc[metric] = ax.scatter([], [], s=64, color=CRIT, zorder=6,
                                     edgecolors=BG, linewidths=0.8)
        playheads[metric] = ax.axvline(times[0], color=CYAN, lw=0.9, alpha=0.5)

    axes[-1].xaxis.set_major_formatter(mdates.DateFormatter("%d %b\n%H:%M"))
    axes[-1].xaxis.set_major_locator(mdates.HourLocator(interval=4))
    for lbl in axes[-1].get_xticklabels():
        lbl.set_color(DIM)

    footer = fig.text(0.5, 0.028, "pytest en verde · python rca.py --demo regenera el informe",
                      color=DIM, fontsize=9, ha="center", va="center")
    return fig, axes, lines, warn_sc, crit_sc, playheads, counter, footer


def make_animation(device: str, series: dict, step: int = 5, hold: int = 55):
    times = series["times"]
    data = series["data"]
    n = series["n"]
    fig, axes, lines, warn_sc, crit_sc, playheads, counter, footer = build_figure(device, series)

    # Índices de anomalías por métrica, según los umbrales del propio rca.
    warn_idx = {m: [] for m in METRICS}
    crit_idx = {m: [] for m in METRICS}
    for m in METRICS:
        spec = rca.THRESHOLDS[m]
        for i, v in enumerate(data[m]):
            if v >= spec["crit"]:
                crit_idx[m].append(i)
            elif v >= spec["warn"]:
                warn_idx[m].append(i)

    reveal = (n - 1) * step
    total = reveal + hold
    cause = rca.probable_root_cause(series["anomalies"])
    rc_artists: list = []

    def frame(i: int) -> None:
        idx = min(i // step, n - 1) if i < reveal else n - 1
        for m in METRICS:
            xs = times[: idx + 1]
            ys = data[m][: idx + 1]
            lines[m].set_data(xs, ys)
            w = [k for k in warn_idx[m] if k <= idx]
            c = [k for k in crit_idx[m] if k <= idx]
            warn_sc[m].set_offsets([(mdates.date2num(times[k]), data[m][k]) for k in w]
                                   or [(0, 0)])
            crit_sc[m].set_offsets([(mdates.date2num(times[k]), data[m][k]) for k in c]
                                   or [(0, 0)])
            if not w:
                warn_sc[m].set_visible(False)
            else:
                warn_sc[m].set_visible(True)
            if not c:
                crit_sc[m].set_visible(False)
            else:
                crit_sc[m].set_visible(True)
            playheads[m].set_xdata([times[idx], times[idx]])
            axes[METRICS.index(m)].set_xlim(times[0], times[-1])

        nw = sum(1 for m in METRICS for k in warn_idx[m] if k <= idx)
        nc = sum(1 for m in METRICS for k in crit_idx[m] if k <= idx)
        counter.set_text(f"anomalías {nw + nc:02d}   críticas {nc:02d}")

        for art in rc_artists:
            art.remove()
        rc_artists.clear()
        if i >= reveal:
            box = fig.text(
                0.5, 0.60, f"Causa raíz probable:\n{cause}",
                color=TXT, fontsize=15, ha="center", va="center", fontweight="bold",
                bbox=dict(boxstyle="round,pad=0.6", facecolor="#1f6feb",
                          edgecolor=CYAN, alpha=0.92),
            )
            rc_artists.append(box)
        return []

    anim = FuncAnimation(fig, frame, frames=total, interval=1000 / 24, blit=False)
    return fig, anim, total, reveal


def render(device: str, series: dict, outdir: Path, fps: int) -> None:
    outdir.mkdir(parents=True, exist_ok=True)
    fig, anim, total, reveal = make_animation(device, series)

    mp4 = outdir / "rca_demo.mp4"
    anim.save(mp4, writer=FFMpegWriter(fps=fps, bitrate=4200))
    print(f"[ok] {mp4}")

    gif = outdir / "rca_demo.gif"
    anim.save(gif, writer=PillowWriter(fps=15), dpi=62)
    print(f"[ok] {gif}")

    poster = outdir / "rca_poster.png"
    anim._func(reveal)  # estado final
    fig.savefig(poster, dpi=100, facecolor=BG)
    print(f"[ok] {poster}")
    plt.close(fig)


def main() -> int:
    parser = argparse.ArgumentParser(description="Demo visual animado del RCA")
    parser.add_argument("--device", default="MOTOR-01")
    parser.add_argument("--input", type=Path, default=Path("data/telemetry_sample.csv"))
    parser.add_argument("--outdir", type=Path, default=Path("assets"))
    parser.add_argument("--fps", type=int, default=24)
    args = parser.parse_args()

    series = _series(args.device, args.input)
    if series["n"] < 2:
        print(f"[error] sin datos para el equipo {args.device}")
        return 1
    render(args.device, series, args.outdir, args.fps)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
