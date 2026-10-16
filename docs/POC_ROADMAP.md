# Matriz inicial de verificaciones técnicas

Esta matriz es **plan de experimentación, no contratos aprobados ni evidencia de éxito**. Se crearán contratos específicos en la siguiente etapa.

| Línea | Componentes SDD | Viabilidad a demostrar | Evidencia mínima |
| --- | --- | --- | --- |
| Host híbrido | C1-P, C1-B, C1-A | APK Android 10+ inicia LynxJS y ejecuta Native Module tipado Kotlin con ida/vuelta y evento | Video o registro instrumentado en dispositivo real; APK y versiones |
| Uso y permisos | C1-OS, C1-D | Consultar UsageStatsManager solo con permiso concedido y reaccionar a revocación | Dispositivo real API 29+, pasos de permisos y log sin datos sensibles |
| Intervenciones | C1-OS, C1-A | Overlay autorizado o degradación a notificación/insistencia cuando el SO no permite limitar | Captura/prueba del sistema operativo, latencia desde detección |
| Visión local | C1-V | CameraX/capa nativa y MediaPipe Pose Landmarker calculan landmarks/resultado derivado sin enviar imágenes | Dispositivo, trazas de red y revisión de almacenamiento |
| Offline | C1-R, C1-S, C1-D | Room persiste UUID y dependencias, WorkManager reconcilia tras reinicio/reconexión | Prueba de caída de red, reinicio, reenvío y ausencia de duplicados |
| API + BD | C2, C3 | FastAPI/Pydantic + SQLAlchemy/Alembic + PostgreSQL con migración, transacción y contrato versionado | Prueba HTTPX/pytest contra PostgreSQL real, migrations up/down cuando proceda |
| Infraestructura | C2, C3 | Docker Compose en Linux, red privada para PostgreSQL, proxy TLS y `/health` contractual | Comandos, logs y comprobación de puertos expuestos |
| Calidad | C1 y C2 | Pruebas RNF-10/08/09/01/02/12/19 de acuerdo con el escenario bajo prueba | Métricas reproducibles y artefactos, sin declarar umbrales cumplidos si no medidos |

Priorizar primero el puente nativo (riesgo R-ARQ-01), restricciones Android (R-ARQ-02) y MediaPipe (R-ARQ-03), luego persistencia/sincronización (R-ARQ-04) y concurrencia transaccional (R-ARQ-05). Los puntos sensibles incluyen Android API 29+, ausencia de acceso privilegiado, privacidad de fotogramas y recompensas exclusivamente validadas por el backend.

**Fuente:** SDD v0.5, secciones 5.2, 6, 7.2, 8.1–8.5, 10.2 y 11.1. SRS v2.3 y Contratos API v1.6 prevalecen en semántica y nombres externos.
