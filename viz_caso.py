#!/usr/bin/env python3
"""Demo visual narrado del diagnóstico de causa raíz (caso real anonimizado).

Capacidad 1 - pieza de portafolio narrada.

Presenta el caso de una motobomba de presurización de agua de un hotel (cliente
anonimizado, datos ficticios): una foto ilustrativa del tipo de motor, el
recorrido de la telemetría contra los umbrales del fabricante y la causa raíz
probable, todo acompañado de una voz en off neuronal en español.

Salida:
    assets/rca_demo_caso.mp4          video con narración
    assets/rca_demo_caso.gif          GIF mudo (para el README)
    assets/rca_demo_caso_poster.png   estado final

Uso:
    python viz_caso.py                 # genera datos, narra y renderiza todo
    python viz_caso.py --silent        # sin voz (durations fijas), útil en CI
    python viz_caso.py --voice /ruta/es_MX-claude-high.onnx

Dependencias de render: matplotlib y ffmpeg. Para la narración: piper-tts y un
modelo de voz (`es_MX-claude-high.onnx`); si no está, se descarga al primer uso.
El demo principal (`rca.py`) sigue usando solo la biblioteca estándar; estos
archivos ya vienen versionados en `assets/`, así que para verlos no hace falta
reinstalar nada.
"""

from __future__ import annotations

import argparse
import csv
import random
import shutil
import subprocess
import textwrap
import urllib.request
import wave
from datetime import datetime, timedelta
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.dates as mdates  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402

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
ACCENT = "#1f6feb"

METRICS = ["temperature_c", "vibration_mm_s", "current_a"]
LABELS = {
    "temperature_c": "Temperatura",
    "vibration_mm_s": "Vibración",
    "current_a": "Corriente",
}

DEVICE = "BOMBA-RECALQUE-01"
CASE_CSV = Path("data/caso_bomba_hotel.csv")
PHOTO = Path("assets/motor_trifasico.jpg")
DEFAULT_VOICE = Path.home() / ".cache" / "piper" / "es_MX-ald-medium.onnx"
VOICE_URL = ("https://huggingface.co/rhasspy/piper-voices/resolve/main/"
             "es/es_MX/ald/medium/es_MX-ald-medium.onnx")
VOICE_JSON_URL = VOICE_URL + ".json"
EDGE_VOICE = "es-CU-ManuelNeural"  # masculino, Cuba (requiere edge-tts no bloqueado)

PAUSE = 0.35  # segundos de silencio entre bloques de narración

# rca.py emite texto en ASCII; en pantalla lo mostramos con acentos correctos.
CAUSE_DISPLAY = {
    "Desgaste mecanico del conjunto motor-rodamiento (vibracion + consumo).":
        "Desgaste mecánico del conjunto motor–rodamiento (vibración + consumo).",
    "Deficiencia de refrigeracion o sobrecarga termica sostenida.":
        "Deficiencia de refrigeración o sobrecarga térmica sostenida.",
    "Falla reportada por el variador; revisar el codigo y su historico.":
        "Falla reportada por el variador; revisar el código y su histórico.",
}


def display_cause(cause: str) -> str:
    return CAUSE_DISPLAY.get(cause, cause)



# --------------------------------------------------------------------------- #
# Datos del caso (ficticios, semilla fija)
# --------------------------------------------------------------------------- #
def make_case_data(path: Path, seed: int = 7) -> None:
    """Serie de 24 h (96 puntos cada 15 min) con degradación por la tarde."""
    rng = random.Random(seed)
    start = datetime(2026, 3, 1, 8, 0, 0)
    rows = []
    for i in range(96):
        ts = (start + timedelta(minutes=15 * i)).isoformat(timespec="seconds")
        wear = (i - 48) / 48 if i > 48 else 0
        temp = 55 + 32 * max(wear, 0) + rng.uniform(-1.5, 1.5)
        vib = 2.0 + 6.8 * max(wear, 0) + rng.uniform(-0.25, 0.25)
        cur = 14 + 15.5 * max(wear, 0) + rng.uniform(-0.4, 0.4)
        code = "E02" if i > 80 else "0"
        rows.append({
            "timestamp": ts, "device": DEVICE,
            "temperature_c": f"{temp:.1f}", "vibration_mm_s": f"{vib:.2f}",
            "current_a": f"{cur:.2f}", "error_code": code,
        })
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def load_series(path: Path) -> dict:
    if not path.exists():
        make_case_data(path)
    rows = [r for r in rca.load_rows(path) if r.get("device") == DEVICE]
    times = [datetime.fromisoformat(r["timestamp"]) for r in rows]
    data = {m: [float(r[m]) for r in rows] for m in METRICS}
    return {"times": times, "data": data, "n": len(rows),
            "anomalies": rca.detect(rows)}


# --------------------------------------------------------------------------- #
# Narración
# --------------------------------------------------------------------------- #
def narration() -> list[dict]:
    return [
        {"key": "intro", "reveal": (0.0, 0.0), "frames": 1,
         "text": "Hola, soy Ronny Díaz López. En este caso te muestro un "
                 "diagnóstico de causa raíz hecho de forma totalmente remota, "
                 "sobre datos anonimizados para proteger al cliente."},
        {"key": "contexto", "reveal": (0.0, 0.0), "frames": 1,
         "text": "Un hotel en Brasil reportó que la bomba de presurización de "
                 "agua se disparaba de forma intermitente, sin una causa aparente."},
        {"key": "remoto", "reveal": (0.0, 0.0), "frames": 1,
         "text": "En lugar de viajar a la instalación, el cliente me compartió "
                 "la telemetría del motor de manera remota."},
        {"key": "ficha", "reveal": (0.0, 0.0), "frames": 1,
         "text": "Es un motor trifásico de inducción, de quince kilovatios, "
                 "trescientos ochenta voltios a sesenta hercios, acoplado a una "
                 "bomba centrífuga de presurización."},
        {"key": "metodo", "reveal": (0.0, 0.15), "frames": 6,
         "text": "Cargué los datos en mi herramienta y fijé los umbrales del "
                 "fabricante: un nivel de aviso y uno crítico para temperatura, "
                 "vibración y corriente."},
        {"key": "herramientas", "reveal": (0.15, 0.32), "frames": 6,
         "silence": 4.5, "text": ""},
        {"key": "deriva", "reveal": (0.32, 0.78), "frames": 16,
         "text": "Durante las primeras horas, todo estuvo dentro de rango. Pero "
                 "la vibración empezó a subir de forma sostenida; y con ella, la "
                 "corriente y la temperatura."},
        {"key": "e02", "reveal": (0.78, 1.0), "frames": 10,
         "text": "La vibración superó los siete coma uno milímetros por segundo, "
                 "la zona de peligro según la norma ISO 10816, y el variador "
                 "reportó el código E02: vibración excesiva."},
        {"key": "causa", "reveal": (1.0, 1.0), "frames": 1,
         "text": "Al correlacionar las tres señales, la causa raíz quedó clara: "
                 "desgaste y desalineación del rodamiento por lubricación "
                 "deficiente. No era una avería eléctrica; el motor se esforzaba "
                 "de más por fricción mecánica."},
        {"key": "acciones", "reveal": (1.0, 1.0), "frames": 1,
         "text": "Recomendé detener el equipo, revisar los rodamientos y la "
                 "alineación, y volver a medir. Con eso, el cliente evitó una "
                 "parada mayor."},
        {"key": "cierre", "reveal": (1.0, 1.0), "frames": 1,
         "text": "Todo el diagnóstico fue remoto, en minutos y con evidencia "
                 "reproducible. Soy Ronny Díaz López; más casos, en mi portafolio."},
    ]


def ensure_voice(model: Path) -> Path:
    if model.exists():
        return model
    model.parent.mkdir(parents=True, exist_ok=True)
    for url, dest in ((VOICE_URL, model), (VOICE_JSON_URL, model.with_suffix(".onnx.json"))):
        print(f"[..] descargando voz {dest.name}")
        urllib.request.urlretrieve(url, dest)
    return model


def _piper_bin() -> str | None:
    found = shutil.which("piper")
    if found:
        return found
    local = Path.home() / ".local" / "bin" / "piper"
    return str(local) if local.exists() else None


def _edge_tts_bin() -> str | None:
    found = shutil.which("edge-tts")
    if found:
        return found
    local = Path.home() / ".local" / "bin" / "edge-tts"
    return str(local) if local.exists() else None


def _silence_wav(path: Path, seconds: float, rate: int = 22050) -> None:
    with wave.open(str(path), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(rate)
        w.writeframes(b"\x00" * int(rate * 2 * seconds))


def _fallback_durations(segments: list[dict]) -> list[float]:
    out = []
    for seg in segments:
        if seg.get("silence"):
            out.append(float(seg["silence"]))
        elif seg["frames"] > 1:
            out.append(seg["frames"] * 1.1)
        else:
            out.append(6.0)
    return out


def _concat(parts: list[Path], workdir: Path) -> Path:
    narration_wav = workdir / "narracion.wav"
    with wave.open(str(parts[0])) as first:
        params = first.getparams()
    gap = b"\x00" * int(params.sampwidth * params.nchannels * params.framerate * PAUSE)
    with wave.open(str(narration_wav), "wb") as out:
        out.setparams(params)
        for i, wav in enumerate(parts):
            with wave.open(str(wav)) as w:
                out.writeframes(w.readframes(w.getnframes()))
            if i < len(parts) - 1:
                out.writeframes(gap)
    return narration_wav


def _run_piper(segments, model: Path, workdir: Path, piper: str):
    model = ensure_voice(model)
    parts, durations = [], []
    for i, seg in enumerate(segments):
        wav = workdir / f"seg{i:02d}.wav"
        if not seg["text"].strip():
            _silence_wav(wav, float(seg.get("silence", 5.0)))
        else:
            proc = subprocess.run(
                [piper, "-m", str(model), "-f", str(wav), "--noise-scale", "0.4", "--length-scale", "0.95", "--noise-w-scale", "0.4"],
                input=seg["text"], text=True, capture_output=True,
            )
            if proc.returncode != 0 or not wav.exists():
                raise RuntimeError(f"piper falló en {seg['key']}: {proc.stderr}")
        with wave.open(str(wav)) as w:
            durations.append(w.getnframes() / w.getframerate())
        parts.append(wav)
    return durations, _concat(parts, workdir)


def _run_edge(segments, workdir: Path, voice: str, edge: str):
    parts, durations = [], []
    for i, seg in enumerate(segments):
        wav = workdir / f"seg{i:02d}.wav"
        if not seg["text"].strip():
            _silence_wav(wav, float(seg.get("silence", 5.0)))
        else:
            mp3 = workdir / f"seg{i:02d}.mp3"
            proc = subprocess.run(
                [edge, "--voice", voice, "--text", seg["text"],
                 "--write-media", str(mp3)],
                text=True, capture_output=True,
            )
            if proc.returncode != 0 or not mp3.exists() or mp3.stat().st_size == 0:
                raise RuntimeError(f"edge-tts falló en {seg['key']}")
            subprocess.run(
                ["ffmpeg", "-y", "-i", str(mp3), "-ar", "22050", "-ac", "1", str(wav)],
                check=True, capture_output=True,
            )
        with wave.open(str(wav)) as w:
            durations.append(w.getnframes() / w.getframerate())
        parts.append(wav)
    return durations, _concat(parts, workdir)


def synthesize(segments: list[dict], model: Path, workdir: Path, silent: bool,
               engine: str = "auto", edge_voice: str = EDGE_VOICE):
    """Devuelve la duración de cada bloque y, si hay voz, el WAV concatenado.

    engine: "auto" prueba edge-tts (voz cubana) y cae a piper; "edge"/"piper"
    fuerzan un motor; silencioso no narra.
    """
    workdir.mkdir(parents=True, exist_ok=True)
    if silent:
        return _fallback_durations(segments), None

    edge = _edge_tts_bin()
    if engine in ("auto", "edge") and edge is not None:
        try:
            return _run_edge(segments, workdir, edge_voice, edge)
        except Exception as exc:  # noqa: BLE001
            if engine == "edge":
                raise
            print(f"[..] edge-tts no disponible ({exc}); uso Piper")

    piper = _piper_bin()
    if piper is None:
        print("[..] sin motor de voz; genero el video sin narración")
        return _fallback_durations(segments), None
    return _run_piper(segments, model, workdir, piper)


# --------------------------------------------------------------------------- #
# Figura
# --------------------------------------------------------------------------- #
def build_figure(series: dict):
    fig = plt.figure(figsize=(12.8, 7.2), dpi=100, facecolor=BG)
    gs = fig.add_gridspec(
        3, 2, width_ratios=[1.75, 1.0],
        left=0.065, right=0.975, top=0.80, bottom=0.15,
        hspace=0.42, wspace=0.10,
    )
    axes = [fig.add_subplot(gs[i, 0]) for i in range(3)]
    axp = fig.add_subplot(gs[:, 1])
    axes[0].sharex(axes[1])
    axes[1].sharex(axes[2])

    times = series["times"]
    fig.text(0.065, 0.948, "Diagnóstico remoto de causa raíz", color=TXT,
             fontsize=20, fontweight="bold", ha="left", va="center")
    fig.text(0.975, 0.948, "Ronny Díaz López", color=TXT, fontsize=12.5,
             ha="right", va="center", fontweight="bold")
    fig.text(0.975, 0.900, "ingeniería eléctrica de aplicación", color=DIM,
             fontsize=9.5, ha="right", va="center")
    fig.text(0.065, 0.890,
             "Telemetría en vivo · BOMBA-RECALQUE-01 · motobomba de presurización "
             "de agua · Residencial Veredas Plaza · Goiânia, Goiás, Brasil · WEG W22 IR3 Premium 7,5 HP (5,5 kW) · TFVE/IC411 · IP55 · S1 · Clase F · hierro fundido FC-200",
             color=DIM, fontsize=9.5, ha="left", va="center")
    fig.text(0.065, 0.876,
             "Motor de inducción trifásico WEG W22 IR3 Premium (jaula de ardilla) · 7,5 HP (5,5 kW) · "
             "380 V · 60 Hz · 4 polos · ~1745 rpm · montaje B3 · TFVE/IC411 · IP55 · S1 · Clase F · hierro fundido FC-200",
             color=DIM, fontsize=9, ha="left", va="center")
    fig.text(0.065, 0.062, "Evidencia reproducible:  python rca.py --input data/caso_bomba_hotel.csv",
             color=DIM, fontsize=8.5, ha="left", va="center")
    fig.text(0.065, 0.028,
             "Foto: ThreePhaseMotor.jpg · dominio público (Wikimedia Commons, LorenzoMignanelli) · datos ficticios anonimizados",
             color=DIM, fontsize=7.5, ha="left", va="center")

    lines, warn_sc, crit_sc = {}, {}, {}
    for ax, metric in zip(axes, METRICS):
        spec = rca.THRESHOLDS[metric]
        lo = min(series["data"][metric])
        hi = max(max(series["data"][metric]), spec["crit"])
        span = max(hi - lo, 1.0)
        ax.set_ylim(lo - 0.12 * span, hi + 0.18 * span)
        ax.set_xlim(times[0], times[-1])
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
        ax.set_ylabel(f"{LABELS[metric]} ({spec['unit']})", color=TXT, fontsize=10)
        (ln,) = ax.plot([], [], color=CYAN, lw=2.0, solid_capstyle="round")
        lines[metric] = ln
        warn_sc[metric] = ax.scatter([], [], s=40, color=WARN, zorder=5,
                                     edgecolors=BG, linewidths=0.8)
        crit_sc[metric] = ax.scatter([], [], s=60, color=CRIT, zorder=6,
                                     edgecolors=BG, linewidths=0.8)
    axes[-1].xaxis.set_major_formatter(mdates.DateFormatter("%d %b\n%H:%M"))
    axes[-1].xaxis.set_major_locator(mdates.HourLocator(interval=4))
    for lbl in axes[-1].get_xticklabels():
        lbl.set_color(DIM)

    axp.set_xlim(0, 1)
    axp.set_ylim(0, 1)
    axp.axis("off")

    return fig, {"axes": axes, "axp": axp, "lines": lines, "warn": warn_sc,
                 "crit": crit_sc, "times": times, "series": series,
                 "overlays": []}


def _clear_overlays(fig, artist):
    for art in artist["overlays"]:
        art.remove()
    artist["overlays"].clear()


def _panel(artist, blocks, photo_box=(0.0, 1.0, 0.58, 0.985)):
    axp = artist["axp"]
    axp.cla()
    axp.set_xlim(0, 1)
    axp.set_ylim(0, 1)
    axp.axis("off")
    if PHOTO.exists():
        img = plt.imread(str(PHOTO))
        axp.imshow(img, extent=photo_box, aspect="auto", zorder=1)
        axp.add_patch(plt.Rectangle((photo_box[0], photo_box[2]),
                                    photo_box[1] - photo_box[0],
                                    photo_box[3] - photo_box[2],
                                    fill=False, edgecolor=GRID, lw=1.0, zorder=2))
    for blk in blocks:
        text = textwrap.fill(blk["t"], width=42) if blk.get("wrap", True) else blk["t"]
        axp.text(blk.get("x", 0.04), blk["y"], text, color=blk.get("c", TXT),
                 fontsize=blk.get("s", 10), ha=blk.get("ha", "left"),
                 va=blk.get("va", "top"), fontweight=blk.get("w", "normal"),
                 family=blk.get("f", "sans-serif"), zorder=3)


def _panel_blocks(key: str, cause: str) -> list[dict]:
    if key == "intro":
        return [
            {"t": "VIDEOCASO", "y": 0.52, "s": 9, "c": ACCENT, "w": "bold"},
            {"t": "Diagnóstico de causa raíz", "y": 0.47, "s": 15, "w": "bold"},
            {"t": "Totalmente remoto, sobre datos anonimizados.", "y": 0.40,
             "s": 10, "c": DIM},
            {"t": "Sistema hidráulico de un hotel · bomba de presurización de agua.",
             "y": 0.30, "s": 10},
        ]
    if key == "contexto":
        return [
            {"t": "Síntoma reportado", "y": 0.52, "s": 12, "c": WARN, "w": "bold"},
            {"t": "La bomba se dispara de forma intermitente, sin causa aparente.",
             "y": 0.45, "s": 11},
            {"t": "Sin avería eléctrica evidente.", "y": 0.35, "s": 10, "c": DIM},
        ]
    if key == "remoto":
        return [
            {"t": "Diagnóstico 100 % remoto", "y": 0.52, "s": 12, "c": OK, "w": "bold"},
            {"t": "El cliente comparte la telemetría del motor (CSV).",
             "y": 0.45, "s": 11},
            {"t": "Sin acceso físico a la planta.", "y": 0.35, "s": 10, "c": DIM},
        ]
    if key == "ficha":
        return [
            {"t": "Ficha del equipo", "y": 0.52, "s": 12, "c": CYAN, "w": "bold"},
            {"t": "Motor de inducción trifásico", "y": 0.45, "s": 11},
            {"t": "15 kW (20 CV) · 380 V · 60 Hz", "y": 0.38, "s": 11},
            {"t": "4 polos · ~1745 rpm · montaje B3 · TFVE/IC411 · IP55 · S1 · Clase F · hierro fundido FC-200", "y": 0.31, "s": 11},
            {"t": "Acoplado a bomba centrífuga", "y": 0.24, "s": 11},
        ]
    if key == "metodo":
        return [
            {"t": "Método", "y": 0.52, "s": 12, "c": CYAN, "w": "bold"},
            {"t": "Umbrales del fabricante: aviso y crítico.",
             "y": 0.45, "s": 11},
            {"t": "Temperatura · Vibración · Corriente", "y": 0.36,
             "s": 10.5, "c": DIM},
        ]
    if key == "herramientas":
        return [
            {"t": "Herramientas y software", "y": 0.52, "s": 12, "c": ACCENT,
             "w": "bold"},
            {"t": "• Python · análisis de datos y telemetría", "y": 0.45, "s": 10.5},
            {"t": "• Normas técnicas (ISO 10816) y hojas de datos del fabricante",
             "y": 0.37, "s": 10.5},
            {"t": "• Umbrales configurables · reporte automático (Markdown / JSON)",
             "y": 0.29, "s": 10.5},
            {"t": "Sin exponer la implementación interna.", "y": 0.20, "s": 9,
             "c": DIM},
        ]
    if key == "deriva":
        return [
            {"t": "Deriva sostenida", "y": 0.52, "s": 12, "c": WARN, "w": "bold"},
            {"t": "Vibración, corriente y temperatura suben juntas.",
             "y": 0.45, "s": 11},
        ]
    if key == "e02":
        return [
            {"t": "Umbral superado", "y": 0.52, "s": 12, "c": CRIT, "w": "bold"},
            {"t": "Vibración en zona de peligro (ISO 10816).", "y": 0.45,
             "s": 11},
            {"t": "El variador reporta E02: vibración excesiva.", "y": 0.36,
             "s": 10.5, "c": CRIT},
        ]
    if key == "causa":
        return [
            {"t": "Causa raíz probable", "y": 0.52, "s": 12, "c": ACCENT, "w": "bold"},
            {"t": cause, "y": 0.44, "s": 11.5},
            {"t": "No es avería eléctrica: es sobreesfuerzo mecánico.",
             "y": 0.22, "s": 10, "c": DIM},
        ]
    if key == "acciones":
        return [
            {"t": "Acciones recomendadas", "y": 0.52, "s": 12, "c": OK, "w": "bold"},
            {"t": "1.  Detener el equipo.", "y": 0.44, "s": 11},
            {"t": "2.  Revisar rodamientos y alineación.", "y": 0.36, "s": 11},
            {"t": "3.  Volver a medir para confirmar.", "y": 0.28, "s": 11},
        ]
    # cierre
    return [
        {"t": "Ronny Díaz López", "y": 0.50, "s": 17, "w": "bold"},
        {"t": "Diagnóstico remoto, en minutos.", "y": 0.40, "s": 11},
        {"t": "Evidencia reproducible · datos anonimizados.", "y": 0.33,
         "s": 10, "c": DIM},
        {"t": "github.com/lazarolpro", "y": 0.25, "s": 10.5, "c": CYAN},
    ]


def draw(fig, artist, state: dict, cause: str) -> None:
    series = artist["series"]
    times, data, n = series["times"], series["data"], series["n"]
    reveal = state["reveal"]
    idx = int(round(reveal * (n - 1)))

    for m in METRICS:
        spec = rca.THRESHOLDS[m]
        artist["lines"][m].set_data(times[: idx + 1], data[m][: idx + 1])
        w = [k for k, v in enumerate(data[m][: idx + 1]) if v >= spec["warn"]]
        c = [k for k, v in enumerate(data[m][: idx + 1]) if v >= spec["crit"]]
        w = [k for k in w if data[m][k] < spec["crit"]]
        artist["warn"][m].set_offsets(
            [(mdates.date2num(times[k]), data[m][k]) for k in w] or [(0, 0)])
        artist["warn"][m].set_visible(bool(w))
        artist["crit"][m].set_offsets(
            [(mdates.date2num(times[k]), data[m][k]) for k in c] or [(0, 0)])
        artist["crit"][m].set_visible(bool(c))

    _panel(artist, _panel_blocks(state["key"], cause))

    _clear_overlays(fig, artist)
    if state["key"] == "e02" and reveal > 0.9:
        artist["overlays"].append(fig.text(
            0.355, 0.60, "E02", color=BG, fontsize=15, fontweight="bold",
            ha="center", va="center",
            bbox=dict(boxstyle="round,pad=0.4", facecolor=CRIT, edgecolor=BG)))
        artist["overlays"].append(fig.text(
            0.355, 0.545, "vibración excesiva", color=CRIT, fontsize=10,
            ha="center", va="center", fontweight="bold"))
    if state["key"] == "causa":
        artist["overlays"].append(fig.text(
            0.355, 0.5, "Causa raíz probable", color=TXT, fontsize=16,
            fontweight="bold", ha="center", va="center",
            bbox=dict(boxstyle="round,pad=0.6", facecolor=ACCENT,
                      edgecolor=CYAN, alpha=0.95)))


# --------------------------------------------------------------------------- #
# Render
# --------------------------------------------------------------------------- #
def render_frames(fig, artist, segments: list[dict], durations: list[float],
                  outdir: Path, cause: str) -> list[tuple[Path, float]]:
    outdir.mkdir(parents=True, exist_ok=True)
    timeline: list[tuple[Path, float]] = []
    for seg, dur in zip(segments, durations):
        frames = max(1, seg["frames"])
        total = dur + (PAUSE if seg is not segments[-1] else 0.0)
        r0, r1 = seg["reveal"]
        for j in range(frames):
            reveal = r0 + (r1 - r0) * (j / (frames - 1) if frames > 1 else 0.0)
            draw(fig, artist, {"key": seg["key"], "reveal": reveal}, cause)
            png = outdir / f"frame_{seg['key']}_{j:02d}.png"
            fig.savefig(png, dpi=100, facecolor=BG)
            timeline.append((png, total / frames))
    return timeline


def encode_video(timeline: list[tuple[Path, float]], fps: int, out: Path) -> None:
    listing = out.parent / "frames_concat.txt"
    lines = []
    for png, dur in timeline:
        lines.append(f"file '{png.resolve()}'")
        lines.append(f"duration {dur:.3f}")
    lines.append(f"file '{timeline[-1][0].resolve()}'")  # repetir el último
    listing.write_text("\n".join(lines) + "\n", encoding="utf-8")
    subprocess.run(
        ["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(listing),
         "-vf", f"fps={fps},format=yuv420p", "-c:v", "libx264", "-crf", "20",
         "-preset", "medium", "-movflags", "+faststart", str(out)],
        check=True, capture_output=True,
    )
    print(f"[ok] {out}")


def mux_audio(video: Path, narration_wav: Path, out: Path) -> None:
    subprocess.run(
        ["ffmpeg", "-y", "-i", str(video), "-i", str(narration_wav),
         "-c:v", "copy", "-c:a", "aac", "-b:a", "128k", "-shortest", str(out)],
        check=True, capture_output=True,
    )
    print(f"[ok] {out}")


def make_gif(video: Path, out: Path, seconds: int = 22) -> None:
    palette = out.parent / "_palette.png"
    vf = "fps=10,scale=640:-1:flags=lanczos"
    subprocess.run(
        ["ffmpeg", "-y", "-t", str(seconds), "-i", str(video),
         "-vf", f"{vf},palettegen", str(palette)],
        check=True, capture_output=True)
    subprocess.run(
        ["ffmpeg", "-y", "-t", str(seconds), "-i", str(video), "-i", str(palette),
         "-lavfi", f"{vf}[x];[x][1:v]paletteuse", str(out)],
        check=True, capture_output=True)
    palette.unlink(missing_ok=True)
    print(f"[ok] {out}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Demo visual narrado del RCA")
    parser.add_argument("--input", type=Path, default=CASE_CSV)
    parser.add_argument("--outdir", type=Path, default=Path("assets"))
    parser.add_argument("--fps", type=int, default=24)
    parser.add_argument("--silent", action="store_true", help="sin voz en off")
    parser.add_argument("--voice", type=Path, default=DEFAULT_VOICE,
                        help="modelo Piper de respaldo (masculino)")
    parser.add_argument("--tts", choices=["auto", "edge", "piper"], default="auto",
                        help="motor de voz: edge (cubana), piper (offline) o auto")
    parser.add_argument("--edge-voice", default=EDGE_VOICE)
    args = parser.parse_args()

    series = load_series(args.input)
    cause = display_cause(rca.probable_root_cause(series["anomalies"]))
    print(f"[..] {series['n']} registros · causa raíz: {cause}")

    segments = narration()
    durations, narration_wav = synthesize(segments, args.voice, Path("build"),
                                          args.silent, args.tts, args.edge_voice)
    print(f"[..] narración: {sum(durations):.1f} s en {len(segments)} bloques")

    fig, artist = build_figure(series)
    timeline = render_frames(fig, artist, segments, durations, Path("build/frames"), cause)

    narrated = args.outdir / "rca_demo_caso.mp4"
    silent = Path("build/rca_demo_caso_silent.mp4")
    encode_video(timeline, args.fps, silent)
    if narration_wav is not None:
        mux_audio(silent, narration_wav, narrated)
    else:
        shutil.copyfile(silent, narrated)
        print(f"[ok] {narrated} (sin audio)")
    make_gif(narrated, args.outdir / "rca_demo_caso.gif")

    draw(fig, artist, {"key": "causa", "reveal": 1.0}, cause)
    fig.savefig(args.outdir / "rca_demo_caso_poster.png", dpi=100, facecolor=BG)
    print(f"[ok] {args.outdir / 'rca_demo_caso_poster.png'}")
    plt.close(fig)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
