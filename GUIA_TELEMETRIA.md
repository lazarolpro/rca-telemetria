# Guía práctica: telemetría real y herramientas del demo RCA

Esta guía explica, paso a paso y con ejemplos, **qué mide** un diagnóstico de causa
raíz, **con qué herramientas** se hace y **cómo se obtiene la telemetría real** de un
motor como el del caso (`BOMBA-RECALQUE-01`, Residencial Veredas Plaza, Goiânia).
Sirve para explicarlo en una entrevista o a un cliente.

---

## 1. Qué es "telemetría" aquí

Telemetría = **mediciones de un equipo, con marca de tiempo, transmitidas desde donde
está el equipo hacia donde se analizan**. En este caso, cuatro señales:

| Señal | Qué mide | Unidad | Por qué importa |
| --- | --- | --- | --- |
| Temperatura | Calor del motor / cojinete | °C | Sube por fricción, falta de ventilación o sobrecarga |
| Vibración | Oscilación mecánica (RMS) | mm/s | Sube por desalineación, desbalance o rodamiento dañado |
| Corriente | Consumo eléctrico por fase | A | Sube por carga mecánica excesiva o falla de aislamiento |
| Código de error | Estado del variador (VFD) | — | Reporta el disparo: sobrecalentamiento, vibración, sobrecorriente |

La clave del método: **una sola señal engaña; tres correlacionadas dan la causa raíz.**

---

## 2. De dónde salen los datos reales (arquitectura de adquisición)

```
[ Motor + Bomba ]
   │  sensores
   ▼
[ Sensores ]──►[ Variador (VFD) / PLC ]──►[ Gateway / Datalogger ]──►[ Historiador ]──► CSV
   │                    │                        │                        │
   │                    │                        │                        └─ InfluxDB / TimescaleDB / PI / SCADA
   │                    │                        └─ Modbus, OPC-UA, MQTT
   │                    └─ registra corriente, par, fallas
   └─ PT100 (temperatura), acelerómetro (vibración), TC (corriente)
```

### 2.1 Sensores (qué se instala en el motor)

| Señal | Sensor típico | Montaje | Salida |
| --- | --- | --- | --- |
| Temperatura de bobinado | **PT100** (RTD 3 hilos) | Embebido en el estator (viene con el motor) | 4–20 mA / Modbus |
| Temperatura de cojinete | PT100 o termopar tipo K | Carcasa del cojinete | 4–20 mA |
| Vibración | **Acelerómetro piezoeléctrico (IEPE)** o transmisor de velocidad | Base del cojinete (atornillado/imán) | mV/g (IEPE) o 4–20 mA |
| Corriente | **Transformador de corriente (TC/CT)** o pinza | Alrededor de una fase | 4–20 mA / Modbus |
| Tensión / fallas | El propio **VFD** ya las mide | Integrado | Modbus / OPC-UA |

> Para tendencia (este demo) basta la **velocidad de vibración en mm/s RMS** (norma
> ISO 10816 / ISO 20816). Para diagnóstico fino se usa el **espectro** (FFT), que
> requiere muestreo a kHz y un analizador de vibraciones.

### 2.2 Adquisición y transporte

- **VFD (variador de frecuencia):** además de gobernar la bomba, ya expone corriente,
  par, tensión del bus DC y códigos de falla. Se lee por **Modbus RTU/TCP** u **OPC-UA**.
- **PLC:** si hay varios sensores, un PLC (Siemens S7, WEG, Allen-Bradley) los agrupa.
- **Gateway / datalogger:** un equipo (Raspberry Pi, Advantech, Teltonika) que lee por
  Modbus/OPC-UA y **publica por MQTT** a un broker.
- **Historiador (base de series de tiempo):** InfluxDB, TimescaleDB, OSIsoft PI o el
  propio SCADA (Ignition, Elipse, iFIX) que guarda cada medición con su timestamp.

### 2.3 Frecuencia de muestreo vs. intervalo de registro

- Vibración para FFT: 1–25 kHz (no es lo de este demo).
- Tendencia (lo que usa el demo): **una muestra cada 15 minutos**.
- Temperatura/corriente: cada 1–60 s si se quiere tiempo real; el demo usa 15 min.

---

## 3. El contrato de datos: el CSV

El demo consume un **CSV** con estas columnas (una fila = una medición en el tiempo):

```csv
timestamp,device,temperature_c,vibration_mm_s,current_a,error_code
2026-03-01T08:00:00,BOMBA-RECALQUE-01,55.2,2.05,14.12,0
2026-03-01T08:15:00,BOMBA-RECALQUE-01,55.9,2.11,13.89,0
...
2026-03-02T07:45:00,BOMBA-RECALQUE-01,89.4,8.60,27.80,E02
```

Ese CSV se obtiene exportándolo del historiador/SCADA, o de un **datalogger** que
guarda las lecturas. En el demo los datos son **ficticios (semilla fija)** para
proteger al cliente; en un caso real, es la exportación cruda del sistema.

---

## 4. Las herramientas del demo y cómo se usan

| Herramienta | Para qué | Cómo se usa |
| --- | --- | --- |
| **Python 3 (solo stdlib)** | Análisis RCA (`rca.py`) | `python rca.py --input data.csv --out report.md` |
| **pandas + matplotlib** | Visualización (`viz_caso.py`) | `python viz_caso.py` |
| **ffmpeg** | Video, GIF y audio | Lo invoca `viz_caso.py`; o directo: `ffmpeg -i in.wav -codec:a libmp3lame -b:a 192k out.mp3` |
| **piper-tts / edge-tts** | Voz en off | `echo "texto" \| piper -m es_ES-davefx-medium.onnx -f out.wav` |
| **pytest** | Pruebas | `python -m pytest -q` |
| **git + GitHub Actions** | Versión y CI | `git push`; CI corre pytest + `rca.py --demo` |

### 4.1 Comandos del análisis (lo que demuestras en vivo)

```bash
# 1) Generar datos de ejemplo + informe
python rca.py --demo

# 2) Analizar un CSV real y escribir el informe
python rca.py --input data/caso_bomba_hotel.csv --out report_caso.md

# 3) Salida JSON (para integrar con un dashboard o pipeline)
python rca.py --input data/caso_bomba_hotel.csv --json

# 4) Pruebas
python -m pytest -q
```

### 4.2 Cómo decide el diagnóstico (`rca.py`)

1. **Umbrales por magnitud** (`THRESHOLDS`) — en real vienen de la **hoja de datos del
   fabricante**, no se inventan:

   | Magnitud | Aviso | Crítico |
   | --- | --- | --- |
   | Temperatura | 75 °C | 90 °C |
   | Vibración | 4,5 mm/s | 7,1 mm/s |
   | Corriente | 22 A | 28 A |

2. **Severidad** por valor: `normal` → `advertencia` → `crítica`.
3. **Códigos del variador** (`E01…E04`) → causa probable catalogada.
4. **Causa raíz probable** por correlación: si hay crítica de vibración **y** corriente
   → *desgaste mecánico del conjunto motor–rodamiento*; si es temperatura → *problema
   de refrigeración*; si es solo código → *falla reportada por el variador*.

---

## 5. Ejemplo práctico A — correr el demo (5 minutos)

```bash
git clone https://github.com/lazarolpro/rca-telemetria && cd rca-telemetria
python rca.py --demo                 # crea data/telemetry_sample.csv y report.md
python rca.py --input data/caso_bomba_hotel.csv --out report_caso.md
cat report_caso.md                   # informe con causa raíz y acciones
python -m pytest -q                  # 4 passed
```

Resultado esperado: 90 anomalías (29 críticas), dispositivo `BOMBA-RECALQUE-01`,
causa **desgaste mecánico del conjunto motor–rodamiento**.

---

## 6. Ejemplo práctico B — telemetría REAL en un motor de bombeo

### 6.1 Lista de materiales (aprox.)

| Ítem | Ejemplo | Función |
| --- | --- | --- |
| Motor | WEG W22 IR3 Premium 7,5 HP 4P B3 IP55 | Accionamiento |
| Variador (VFD) | WEG CFW500 / Schneider ATV / Siemens G120 | Control + lectura de corriente/fallas |
| PT100 | RTD 3 hilos, embebido en estator | Temperatura de bobinado |
| Acelerómetro | IEPE + transmisor 4–20 mA (mm/s) | Vibración en cojinete |
| TC (CT) | 3× transformador de corriente 4–20 mA | Corriente por fase |
| Gateway | Raspberry Pi + Node-RED/Modbus | Recolectar y publicar (MQTT) |
| Historiador | InfluxDB + Grafana | Guardar series y graficar |

### 6.2 Montaje (resumen)

1. PT100 y TC se conectan al **VFD/PLC** (entradas analógicas o Modbus).
2. El acelerómetro se **atornilla a la carcasa del cojinete** (no sobre pintura).
3. El gateway lee por **Modbus** los registros de corriente, temperatura y falla del VFD,
   y la vibración por su entrada 4–20 mA.
4. El gateway publica por **MQTT** a InfluxDB; Grafana muestra la tendencia.
5. Para analizar con esta herramienta: **exportar el rango de fechas a CSV** con las
   columnas del punto 3.

### 6.3 Ajustar los umbrales al fabricante (obligatorio en real)

En `rca.py` se cambian los valores por los de la placa/hoja de datos. Para un motor de
**7,5 HP (5,5 kW), 380 V, 4 polos**, la corriente a plena carga (FLA) es ≈ **11,5 A**:

```python
THRESHOLDS = {
    "temperature_c":  {"warn": 75.0, "crit": 90.0, "unit": "C"},
    "vibration_mm_s": {"warn": 4.5,  "crit": 7.1,  "unit": "mm/s"},  # ISO 10816 zona C/D
    "current_a":      {"warn": 9.0,  "crit": 12.0, "unit": "A"},     # ~78% y ~104% de FLA
}
```

> ⚠️ **Coherencia pendiente:** el CSV del demo actual llega a ~28 A, que corresponde a
> un motor de **~20 CV (15 kW)**, no al de 7,5 HP del video. Para que todo cuadre hay
> que **reescalar la corriente** del caso (de ~5 A a ~11,5 A) y ajustar los umbrales a
> 9/12 A, o bien documentar que el equipo es mayor. Se recomienda corregirlo antes de
> presentar el caso.

---

## 7. Ejemplo práctico C — interpretar el informe

Del `report_caso.md`:

- **Registros / anomalías:** cuántas mediciones y cuántas fuera de rango.
- **Dispositivo más afectado:** dónde concentrar el esfuerzo.
- **Causa raíz probable:** la hipótesis que explica el patrón.
- **Línea de tiempo:** el orden en que aparecieron las anomalías (vibración primero,
  luego corriente y temperatura → firma de desgaste mecánico).
- **Acciones recomendadas:** inspección mecánica, verificar ventilación/carga, y
  **volver a medir para confirmar** (cerrar el ciclo).

Regla de oro: **el informe no "arregla" nada; prioriza y justifica** con evidencia
reproducible. La reparación la valida una segunda medición.

---

## 8. Cómo explicarlo en una entrevista (guion de 2 minutos)

> "Cuando un equipo se dispara, lo normal es cambiar piezas hasta que 'algo funcione'.
> Yo hago lo contrario: trabajo sobre la **telemetría** —temperatura, vibración y
> corriente— con marca de tiempo. Con los **umbrales del fabricante** detecto qué se
> salió de rango y **correlaciono** las señales: si vibración y corriente suben juntas,
> es desgaste mecánico; si sube solo la temperatura, es refrigeración. Todo eso lo hago
> **en remoto**, con un CSV exportado del sistema del cliente, y entrego un **informe
> de causa raíz reproducible**. En este caso real, un hotel en Goiânia, el diagnóstico
> remoto evitó una parada mayor. La herramienta es **Python sin dependencias**, y todo
> el caso está en mi GitHub con datos anonimizados."

Puntos que puedes mostrar en vivo: `rca.py --demo`, el `report_caso.md`, el video
narrado y el PDF del caso.

---

## 9. Glosario

- **RCA:** *Root Cause Analysis*, análisis de causa raíz.
- **VFD:** *Variable Frequency Drive*, variador de frecuencia.
- **PT100:** sensor de temperatura (RTD) de 100 Ω a 0 °C.
- **IEPE:** interfaz de acelerómetro piezoeléctrico (salida mV/g).
- **TC/CT:** transformador de corriente.
- **Modbus / OPC-UA / MQTT:** protocolos industriales de comunicación.
- **Historiador:** base de datos de series de tiempo (InfluxDB, PI, etc.).
- **ISO 10816/20816:** norma de evaluación de vibración en máquinas.
- **FLA:** *Full Load Amps*, corriente a plena carga (de la placa del motor).
