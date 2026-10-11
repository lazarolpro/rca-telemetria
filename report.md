# Informe de diagnostico y causa raiz

- Registros analizados: **96**
- Anomalias: **27** (criticas: 10, advertencias: 17)
- Dispositivo mas afectado: **MOTOR-01**
- Causa raiz probable: **Desgaste mecanico del conjunto motor-rodamiento (vibracion + consumo).**

## Linea de tiempo de anomalias

| Marca temporal | Equipo | Magnitud | Valor | Severidad | Causa probable |
| --- | --- | --- | --- | --- | --- |
| 2026-03-02T00:30:00 | MOTOR-01 | vibration_mm_s | 4.64 | advertencia | Vibracion alta: revisar alineacion y rodamientos (severidad advertencia) |
| 2026-03-02T01:15:00 | MOTOR-01 | vibration_mm_s | 4.77 | advertencia | Vibracion alta: revisar alineacion y rodamientos (severidad advertencia) |
| 2026-03-02T02:00:00 | MOTOR-01 | vibration_mm_s | 5.38 | advertencia | Vibracion alta: revisar alineacion y rodamientos (severidad advertencia) |
| 2026-03-02T02:45:00 | MOTOR-01 | vibration_mm_s | 5.66 | advertencia | Vibracion alta: revisar alineacion y rodamientos (severidad advertencia) |
| 2026-03-02T02:45:00 | MOTOR-01 | current_a | 23.35 | advertencia | Consumo elevado: revisar carga mecanica y aislamiento (severidad advertencia) |
| 2026-03-02T03:30:00 | MOTOR-01 | vibration_mm_s | 5.83 | advertencia | Vibracion alta: revisar alineacion y rodamientos (severidad advertencia) |
| 2026-03-02T03:30:00 | MOTOR-01 | current_a | 24.39 | advertencia | Consumo elevado: revisar carga mecanica y aislamiento (severidad advertencia) |
| 2026-03-02T04:15:00 | MOTOR-01 | temperature_c | 77.4 | advertencia | Elevacion termica: revisar refrigeracion y carga (severidad advertencia) |
| 2026-03-02T04:15:00 | MOTOR-01 | vibration_mm_s | 6.29 | advertencia | Vibracion alta: revisar alineacion y rodamientos (severidad advertencia) |
| 2026-03-02T04:15:00 | MOTOR-01 | current_a | 25.22 | advertencia | Consumo elevado: revisar carga mecanica y aislamiento (severidad advertencia) |
| 2026-03-02T04:15:00 | MOTOR-01 | error_code | E02 | critica | Vibracion excesiva (desalineacion o desgaste de rodamiento) |
| 2026-03-02T05:00:00 | MOTOR-01 | temperature_c | 75.8 | advertencia | Elevacion termica: revisar refrigeracion y carga (severidad advertencia) |
| 2026-03-02T05:00:00 | MOTOR-01 | vibration_mm_s | 6.85 | advertencia | Vibracion alta: revisar alineacion y rodamientos (severidad advertencia) |
| 2026-03-02T05:00:00 | MOTOR-01 | current_a | 26.5 | advertencia | Consumo elevado: revisar carga mecanica y aislamiento (severidad advertencia) |
| 2026-03-02T05:00:00 | MOTOR-01 | error_code | E02 | critica | Vibracion excesiva (desalineacion o desgaste de rodamiento) |
| 2026-03-02T05:45:00 | MOTOR-01 | temperature_c | 80.9 | advertencia | Elevacion termica: revisar refrigeracion y carga (severidad advertencia) |
| 2026-03-02T05:45:00 | MOTOR-01 | vibration_mm_s | 7.2 | critica | Vibracion alta: revisar alineacion y rodamientos (severidad critica) |
| 2026-03-02T05:45:00 | MOTOR-01 | current_a | 26.66 | advertencia | Consumo elevado: revisar carga mecanica y aislamiento (severidad advertencia) |
| 2026-03-02T05:45:00 | MOTOR-01 | error_code | E02 | critica | Vibracion excesiva (desalineacion o desgaste de rodamiento) |
| 2026-03-02T06:30:00 | MOTOR-01 | temperature_c | 82.5 | advertencia | Elevacion termica: revisar refrigeracion y carga (severidad advertencia) |
| 2026-03-02T06:30:00 | MOTOR-01 | vibration_mm_s | 7.57 | critica | Vibracion alta: revisar alineacion y rodamientos (severidad critica) |
| 2026-03-02T06:30:00 | MOTOR-01 | current_a | 28.16 | critica | Consumo elevado: revisar carga mecanica y aislamiento (severidad critica) |
| 2026-03-02T06:30:00 | MOTOR-01 | error_code | E02 | critica | Vibracion excesiva (desalineacion o desgaste de rodamiento) |
| 2026-03-02T07:15:00 | MOTOR-01 | temperature_c | 83.5 | advertencia | Elevacion termica: revisar refrigeracion y carga (severidad advertencia) |
| 2026-03-02T07:15:00 | MOTOR-01 | vibration_mm_s | 8.22 | critica | Vibracion alta: revisar alineacion y rodamientos (severidad critica) |
| 2026-03-02T07:15:00 | MOTOR-01 | current_a | 28.7 | critica | Consumo elevado: revisar carga mecanica y aislamiento (severidad critica) |
| 2026-03-02T07:15:00 | MOTOR-01 | error_code | E02 | critica | Vibracion excesiva (desalineacion o desgaste de rodamiento) |

## Acciones recomendadas

1. Priorizar el equipo con mayor numero de eventos criticos.
2. Inspeccion mecanica (alineacion, rodamientos, lubricacion).
3. Verificar ventilacion, filtros y curva de carga.
4. Registrar la reparacion y volver a medir para confirmar la causa.

> Evidencia reproducible: `python rca.py --demo` regenera este informe.
