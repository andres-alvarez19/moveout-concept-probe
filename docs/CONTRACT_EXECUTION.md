# Guía de implementación y evidencia para la fábrica

## Propósito

Esta guía interpreta operativamente los contratos de PoC, sin sustituir SDD v0.5, SRS v2.3 ni Contratos API MoveOut v1.6. **El software de prueba todavía no existe.** Un contrato validado solo demuestra que sus campos, dependencias y barreras definidas son consistentes.

## Precondiciones de cada ejecución

- Contrato aprobado por revisión humana: `status: "approved"`.
- Rama Git de desarrollo distinta de main, con árbol limpio antes de invocar `run --execute`.
- Acceso autorizado a SRS/SDD/Contratos API vigentes. Actualmente los PDFs originales no están en el repositorio; no reproducirlos públicamente sin revisar autorización y datos identificables.
- Herramientas y recursos reales para los AC: Android Studio/SDK, dispositivo físico Android API 29+ para capacidades nativas, PostgreSQL para backend, Linux+Docker+certificado TLS para infraestructura.
- Los secretos van en variables externas/almacenamiento seguro; nunca en contratos, commits ni evidencias.

## Entrega mínima por contrato

1. **Plan:** identificar AC-XX, módulos SDD, comandos, archivos, permisos y dispositivos requeridos.
2. **Implementación:** código estrictamente necesario y dependencias fijadas en manifiestos. Mantener Clean Architecture.
3. **Pruebas:** cada AC genera un archivo en su `evidence_path`. El archivo debe contener: ID PoC/AC, commit, fecha UTC, sistema/versión, dispositivo o entorno, precondiciones, comandos/pasos ejecutados, resultado esperado, resultado observado, PASS/FAIL/BLOCKED/NOT_RUN, ruta/identificador de evidencia real y limitaciones.
4. **Revisión:** QA ejecuta o verifica independencia de los resultados; los archivos de evidencia existen pero no prueban su autenticidad por sí mismos.
5. **Aceptación humana:** confirmar las pruebas relevantes y registrar decisión de cierre.

## Encadenamiento y responsables de agente

| Contrato | Agentes de código asignados | Alcance particular |
| --- | --- | --- |
| 001 | architect → android → integrator → qa | Host Android y puente Native Module real |
| 002 | architect → android → integrator → qa | UsageStatsManager, permisos y dominio |
| 003 | architect → android → integrator → qa | UI y servicio de intervención independientes |
| 004 | architect → android → integrator → qa | MediaPipe local y ruta sin cámara |
| 005 | architect → android → backend → integrator → qa | Room/WorkManager y APIs de reconciliación |
| 006 | architect → backend → integrator → qa | Autenticación mínima, ingesta y snapshot contractual |
| 007 | architect → backend → integrator → qa | Compose, TLS, red interna y salud |
| 008 | architect → android → backend → integrator → qa | Escenarios de calidad e invariantes de recompensas |

Para obtener instrucciones de agente sin invocarlo: `python -m factory.cli prompt contracts/POC-001.json --role android`.

## Criterios de límites de integración

- **POC-001..004:** no necesitan levantar un backend ni inventar endpoints. Un modelo de evento en tests Kotlin no demuestra monitoreo real. Los tests deben diferenciar fixture y señal real.
- **POC-005:** requiere POC-003 y POC-006; el intercambio HTTP usa #25, #28, #31, #36 y #38 completos. En offline, pausa directa/manual sin nuevos giros y recompensa no confirmada.
- **POC-006:** las rutas #01, #02, #25, #28 corresponden a `/api/v1`; #52 corresponde literalmente a `GET /health` en raíz. Un endpoint incompleto no debe etiquetarse como compatible.
- **POC-007:** acceso HTTPS real del proxy y PostgreSQL no expuesto. Las pruebas internas HTTP entre servicios no reemplazan TLS externo.
- **POC-008:** implementar #39/#40 con backend y transacción atómica; el premio raro es 6/300 (2 %) y cada pausa 49/300; el máximo compartido contabiliza concesiones, no minutos. La carga no demuestra por sí sola disponibilidad mensual.

## Comandos de fábrica

```bash
python -m factory.cli check --all
python -m unittest discover -s factory/tests -v
python -m factory.cli plan contracts/POC-006.json
python -m factory.cli validate contracts/POC-006.json
python -m factory.cli prompt contracts/POC-006.json --role backend
# Solo tras aprobación humana y con CLI Codex instalada:
python -m factory.cli run contracts/POC-006.json --execute
# Solo se utiliza como precontrol de existencia de evidencia, no como aceptación:
python -m factory.cli verify contracts/POC-006.json
```

**No hacer merge automático.** Toda diferencia respecto a las normas o incapacidad técnica se registra como bloqueo o ADR con trazabilidad.
