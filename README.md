# MoveOut Concept Probe

**Fábrica agéntica contract-first para verificar la viabilidad tecnológica de MoveOut.** El objetivo es producir pruebas de concepto pequeñas, medibles y reproducibles, no desarrollar de golpe el sistema completo.

## Fuente de verdad

1. **SRS MoveOut v2.3** (15-10-2026): requisitos RF/RNF y restricciones del producto.
2. **Contratos API MoveOut v1.6** (15-10-2026): rutas, esquemas, estados y códigos de error.
3. **SDD MoveOut v0.5** (16-10-2026): decisiones arquitectónicas, tecnologías y ADR-0001 a ADR-0006.
4. **Contratos de PoC** en `contracts/POC-XXX.json`: alcance técnico y criterios de prueba.

Los documentos normativos completos no están incluidos en este repositorio público. **Antes de pedir a un agente que implemente APIs o decisiones no transcritas, proporcionar acceso autorizado a esas fuentes y no inventar información faltante.** No publicar PDFs con datos de personas sin revisar su contenido y permisos.

## Contratos técnicos definidos

| ID | Objetivo | Dependencias |
| --- | --- | --- |
| [POC-001](contracts/POC-001.json) | Host Kotlin, LynxJS/ReactLynx y Native Module tipado | Ninguna |
| [POC-002](contracts/POC-002.json) | Permisos y UsageStatsManager Android | 001 |
| [POC-003](contracts/POC-003.json) | Intervención local, overlay y degradación | 002 |
| [POC-004](contracts/POC-004.json) | MediaPipe Pose Landmarker local y pausa sin cámara | 001 |
| [POC-005](contracts/POC-005.json) | Room/WorkManager y reconciliación causal offline | 003, 006 |
| [POC-006](contracts/POC-006.json) | FastAPI, PostgreSQL, Alembic e API contractual | Ninguna |
| [POC-007](contracts/POC-007.json) | Docker Compose/Linux, red privada, proxy TLS | 006 |
| [POC-008](contracts/POC-008.json) | Verificación integral, latencias, privacidad, recompensas concurrentes | 003, 004, 005, 007 |

**Los ocho contratos están en `draft` hasta aprobación humana** y no implican código Android/backend ni resultados de prueba ejecutados.

## Ejecutar controles

Requiere Python 3.11+ y Git.

```bash
python -m factory.cli check --all
python -m unittest discover -s factory/tests -v

python -m factory.cli validate contracts/POC-001.json
python -m factory.cli plan contracts/POC-001.json
python -m factory.cli prompt contracts/POC-001.json --role android
python -m factory.cli verify contracts/POC-001.json
```

`verify` solo confirma que existen archivos de evidencia; **no demuestra que las pruebas cumplan su aceptación**. En esta etapa no debe devolver éxito de evidencias, ya que no se han ejecutado los PoC.

Cuando un contrato quede aprobado, en una rama local limpia y con Codex CLI instalado/autenticado externamente:

```bash
python -m factory.cli run contracts/POC-001.json --execute
```

Los agentes son optativos y requieren entorno real para build/test; su runner **no instala dependencias, no valida física automáticamente, no hace merge ni despliega**.

## Instrucciones

- [Instrucciones globales para agentes](AGENTS.md)
- [Flujo de la fábrica](docs/AGENT_FACTORY.md)
- [Matriz de contratos y riesgos](docs/POC_ROADMAP.md)
- [Guía de ejecución de PoC](docs/CONTRACT_EXECUTION.md)
- [Reglas para revisar/aprobar contratos](contracts/README.md)

**Importante:** `/health` es una ruta pública excepcional en la raíz según contrato API #52; los demás endpoints de API indicados utilizan `/api/v1`. Las recompensas definitivas requieren validación del backend; la cámara y MediaPipe siempre se procesan localmente.
