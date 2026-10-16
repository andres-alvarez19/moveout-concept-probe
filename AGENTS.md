# MoveOut — instrucciones para agentes

Este repositorio es un **concept probe** de la arquitectura definida en **SDD v0.5** (16-10-2026), subordinado a SRS v2.3 y Contratos API MoveOut v1.6. NO es la aplicación completa.

## Orden de autoridad
1. SRS v2.3: requisitos RF/RNF.
2. Contratos API v1.6: endpoints, esquemas, errores y estados públicos.
3. SDD v0.5: decisiones de diseño, capas, integración y despliegue.
4. Contrato de prueba de concepto aprobado en `contracts/POC-XXX.json`.
5. Este documento y los perfiles de agentes.

Ante ambigüedad o conflicto: **detenerse, describir el bloqueo y solicitar definición**. No inventar contratos, endpoints, permisos privilegiados ni métricas de éxito.

## Flujo de fábrica obligatorio
1. Validar contrato: `python -m factory.cli validate contracts/POC-XXX.json`.
2. Elaborar plan y correspondencia requisitos → componentes → pruebas.
3. Arquitecto define límites y riesgos; desarrollador Android y/o backend implementa cambios mínimos.
4. Integrador verifica interoperabilidad y configuraciones.
5. QA ejecuta controles, registra resultados observables y señala pruebas de dispositivo pendientes.
6. Revisor humano acepta o rechaza con pruebas vinculadas; no se fusiona automáticamente.

Instrucciones detalladas: [docs/AGENT_FACTORY.md](docs/AGENT_FACTORY.md).

## Arquitectura innegociable
- Android **API 29+**. Host Android **Kotlin**; UI **LynxJS + ReactLynx + TypeScript**.
- Comunicación UI ↔ host mediante **Native Modules tipados**, sin entregar SDK Android ni fotogramas a LynxJS.
- Kotlin contiene aplicación, dominio y adaptadores nativos; lógica crítica independiente de pantallas.
- Visión: **MediaPipe Pose Landmarker local**. Ni persistir ni transmitir imágenes o video corporal.
- Almacenamiento Android: **Room/SQLite**; sincronización diferible por **WorkManager** (no monitoreo continuo).
- Backend: **FastAPI/Python/Pydantic**, monolito modular; **SQLAlchemy 2.x, Alembic, PostgreSQL**.
- API: **REST/HTTPS/JSON** bajo `/api/v1` y contratos externos existentes; **no crear rutas públicas nuevas** sin contrato aprobado.
- Infraestructura: **Docker Compose en VPS/Linux**, base de datos no expuesta y proxy TLS.
- Local-first: UUID inmutable por operación, cola durable, reintento idempotente y orden causal evento → intervención → pausa → resultado.
- Ruleta y concesiones definitivas: **exclusivamente backend**; prohibido conceder tiempo offline de forma provisional.
- Verificar permisos del usuario antes de operar y degradar solo la capacidad afectada; no prometer bloqueo irrestricto de otras apps.
- Prohibido introducir secretos reales, tokens, credenciales o datos sensibles en el repositorio, logs o evidencias.

## Reglas de implementación
- Cambios pequeños y trazables al identificador del contrato; no implementar extras ni usar mocks como evidencia física.
- Interfaces/puertos para dependencias externas; aplicar Clean Architecture, tipos explícitos y nombres significativos.
- Pruebas reproducibles con comandos documentados, sin evidencia falsa ni afirmaciones de compilación sin ejecutar.
- Documentar limitaciones y riesgos en `evidence/POC-XXX/` cuando el contrato esté aprobado.
- Antes de entregar: `python -m factory.cli check --all` y `python -m unittest discover -s factory/tests -v`.
- No sobrescribir ni borrar trabajos ajenos; no realizar merge ni desplegar sin aprobación humana.
