# Contratos de pruebas de concepto — MoveOut

## Objetivo

Ocho contratos técnicos versionados contra SDD v0.5, SRS v2.3 y Contratos API MoveOut v1.6. **No modifican ni reemplazan las especificaciones normativas.** Cada contrato define una hipótesis concreta y evidencia falsable.

| ID | Contrato | Dependencias | Criterios AC |
| --- | --- | --- | --- |
| POC-001 | Native Host Kotlin + UI LynxJS + Native Module | — | 5 |
| POC-002 | Uso y permisos Android | 001 | 5 |
| POC-003 | Overlays e intervención local | 002 | 5 |
| POC-004 | MediaPipe local + fallback manual | 001 | 5 |
| POC-005 | Cola offline causal e integración | 003, 006 | 7 |
| POC-006 | FastAPI y PostgreSQL contratados | — | 7 |
| POC-007 | Docker Compose / HTTPS / Linux | 006 | 6 |
| POC-008 | QA integral + concurrencia transaccional | 003, 004, 005, 007 | 8 |

**Total: 48 criterios de aceptación.** Los contratos permanecen en `status: "draft"` hasta que una persona revise el PR y autorice el contenido. No cambiar a `approved` automáticamente ni tratar el CI verde como aprobación.

## Campos

- `id`, `title`, `objective`: identidad e hipótesis a comprobar.
- `components`: identificadores C1/C2/C3 del SDD para asignación de agentes.
- `traceability`: secciones/ADR del SDD, RF/RNF/OTR de SRS y numerales de Contratos API v1.6, únicamente si aplican.
- `depends_on`: contratos cuya capacidad se necesita antes de este PoC (grafo acíclico).
- `privacy`: prohibición de persistir/transmitir video o fotogramas corporales.
- `environment`: requiere Android real y/o PostgreSQL real para aceptación.
- `acceptance`: `AC-XX`, escenario, método `automated|integration|device|manual`, resultado esperado observable y ruta de reporte bajo `evidence/POC-XXX/`.

Los archivos `evidence_path` **son destinos futuros, no pruebas generadas**. No fabricar salidas ni guardar contraseñas, tokens o imágenes corporales.

## Revisión y aprobación

1. Comparar cada `objective`, `traceability`, endpoint, estado y error con las fuentes normativas.
2. Confirmar recursos para las pruebas exigidas: Android 10+/API29, dispositivo físico, cámara, permiso Usage Access, Docker/Linux, PostgreSQL y HTTPS cuando aplique.
3. Revisar dependencias y alcance; reducirlo por decisión humana si el PoC se vuelve demasiado grande, sin falsificar contratos API.
4. Aprobar por pull request; actualizar `status` a `approved` mediante un commit revisado.
5. Crear rama por PoC, ejecutar `validate`, `plan`, la implementación y ensayos observables; registrar pruebas.
6. QA valida cada AC con PASA/FALLA/BLOQUEADO/NO EJECUTADO y revisión humana final.

Usar:
```bash
python -m factory.cli check --all
python -m factory.cli plan contracts/POC-001.json
```

### Orden práctico

Las pruebas pueden ejecutarse en paralelo por ramas: `POC-001` y `POC-006` no dependen de otras. Posteriormente `002` y `004`; luego `003` y `007`; después `005`; por último `008`. **El número no equivale al orden de ejecución**.

### Límites de las evidencias

- Native Bridge, UsageStats, permisos, overlays y MediaPipe requieren dispositivo real, no fixtures como prueba de compatibilidad.
- PostgreSQL significa PostgreSQL real para pruebas de integración, no SQLite.
- API #52 es `GET /health` en raíz (no `/api/v1/health`).
- Los contratos nombran las rutas públicas existentes: nunca crear nuevas sin revisión.
- RNF-11 (>=99 % mensual) requiere seguimiento de periodo; una prueba de despliegue no demuestra ese indicador.
- La ausencia de fuentes normativas accesibles al ejecutor es un bloqueo a resolver antes de implementar.
