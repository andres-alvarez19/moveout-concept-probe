# Hoja de ruta de contratos PoC — MoveOut

Los contratos operativos están en `contracts/POC-001.json` a `POC-008.json`. Actualmente son **borradores técnicos sujetos a aprobación**, no evidencias de viabilidad.

| PoC | Tecnología / capacidad a demostrar | Componentes SDD | Riesgo | Entorno mínimo |
| --- | --- | --- | --- | --- |
| POC-001 | Kotlin Android Host + LynxJS/ReactLynx + Native Modules tipados | C1-P, C1-B, C1-A | R-ARQ-01 | APK sobre Android físico API 29+ |
| POC-002 | UsageStatsManager, permiso y motor local Kotlin | C1-OS, C1-D | R-ARQ-02 | Android físico con permisos concedidos/revocados |
| POC-003 | Notificación/overlay autorizado, estado local y latencia <=2s | C1-OS, C1-A | R-ARQ-02 | Android físico; pruebas de denegación/revocación |
| POC-004 | CameraX/capa nativa + MediaPipe Pose Landmarker local, fallback manual | C1-V, C1-B | R-ARQ-03 | Cámara Android; inspección de tráfico y almacenamiento |
| POC-005 | Room/SQLite, WorkManager, cola con UUID y orden causal | C1-R, C1-S, C2/C3 | R-ARQ-04 | Android + PostgreSQL + caída/reinicio/reconexión |
| POC-006 | FastAPI/Pydantic, SQLAlchemy/Alembic, PostgreSQL, contratos REST | C2, C3 | R-ARQ-04 | PostgreSQL real y suite HTTPX/pytest |
| POC-007 | Docker Compose/Linux, proxy TLS, PostgreSQL privado, /health | C2, C3 | Riesgo de despliegue | Host Linux con Docker + TLS comprobable |
| POC-008 | Q-01..Q-07, carga 50 usuarios, privacy, ruleta y recompensa atómica | C1/C2/C3 | R-ARQ-05 y RNF | Android físico + PostgreSQL + herramientas de carga |

## Dependencias

```text
POC-001 ─→ POC-002 ─→ POC-003 ────┐
       └─→ POC-004 ────────────────┤
POC-006 ─→ POC-007 ────────────────┤→ POC-008
       └─────────┐                │
                 └─→ POC-005 ─────┘
POC-003 ────────────→ POC-005
```

Una planificación topológica válida es **001, 006, 002, 004, 003, 007, 005, 008**. También pueden realizarse ramas paralelas de Android y backend.

## Puertas de aceptación

- **LynxJS–Kotlin:** comunicación real bidireccional y gestión de ciclo de vida, no WebView/mock presentado como integración nativa.
- **Android:** no presuponer que el SO deja monitorear, restringir apps o ejecutar servicios irrestrictamente; evidenciar modos degradados.
- **MediaPipe:** procesar video/fotogramas solo localmente; transmitir únicamente resultados derivados.
- **Offline:** eventos, intervenciones, pausa y resultado guardados con UUID y origen temporal; WorkManager solo sincronización diferible.
- **API:** endpoints exactamente según Contratos API v1.6. Caso especial: #52 GET /health está fuera de `/api/v1`.
- **Recompensas:** 6/300 rare prize, 49/300 por cada uno de seis tipos; backend controla elegibilidad, idempotencia, día lógico y cupo transaccional.
- **Calidad:** RNF-10 p95 <=1s bajo 50 usuarios y evaluación <=500ms; intervención local <=2s. RNF-11 solo verificable mediante observación mensual real.

Las pruebas QA registrarán evidencia genuina en `evidence/POC-XXX/`; pasar el validador de contratos no significa pasar el PoC.

Fuentes normativas: SDD v0.5, especialmente §§4-8 y 10-11; SRS v2.3; Contratos API v1.6. No se incluyen copias completas de los PDFs en el repositorio público.
