# Fábrica agéntica — MoveOut

## Propósito y alcance
Orquestar pruebas de concepto contract-first para verificar que la tecnología del SDD v0.5 es viable en condiciones observables. **La fábrica no prueba por sí sola que el producto sea viable**: registra qué ensayos se ejecutaron, en qué dispositivo/entorno, con qué resultados y qué quedó pendiente. Esta primera etapa instala la fábrica, no los contratos de implementación.

## Pipeline
```text
Contrato aprobado (JSON)
   ↓ validación sintáctica + reglas de arquitectura + dependencias
Arquitecto → plan, fronteras y riesgos
   ↓
Android / Backend → código mínimo ejecutable (según componentes)
   ↓
Integrador → puente, red, persistencia, migraciones, configuración
   ↓
QA → pruebas automatizadas + evidencia manual/dispositivo
   ↓
Revisión humana → aceptar/rechazar el PoC
```

Perfiles reutilizables de GitHub Copilot: `.github/agents/*.agent.md`. `AGENTS.md` incorpora reglas también para asistentes de codificación que respeten esa convención. La CLI arma los prompts y, si hay Codex CLI instalado y autenticado, puede ejecutar secuencialmente los perfiles de la fábrica en una rama local. **La creación de prompts y planes no invoca un modelo por sí sola**.

## Contrato de entrada
- Ubicación: `contracts/POC-XXX.json`; el directorio comienza sin contratos aprobados.
- Esquema: `factory/contract.schema.json`; ejemplo de estructura: `factory/templates/contract.template.json`.
- Identidad, objetivo, componentes del SDD, trazabilidad SDD/SRS/API, criterios de aceptación medibles y rutas de evidencia.
- Dependencias entre contratos deben existir y formar un grafo acíclico.
- Para visión por cámara y adaptadores Android, exigir prueba real en dispositivo.
- Las operaciones con video/cámara siempre declaran expresamente prohibiciones de persistencia y transferencia.

## CLI (Python 3.11+, solo biblioteca estándar)
```bash
python -m factory.cli check --all
python -m factory.cli validate contracts/POC-001.json
python -m factory.cli plan contracts/POC-001.json
python -m factory.cli prompt contracts/POC-001.json --role android
python -m factory.cli verify contracts/POC-001.json
python -m factory.cli run contracts/POC-001.json --execute
```
- `check --all`: verifica estructura y todos los contratos existentes; **si no hay contratos, solo valida la fábrica**.
- `validate`: valida contrato y dependencias, sin declarar PoC ejecutado.
- `plan`: calcula roles de implementación, integración y QA.
- `prompt`: emite el prompt de un agente, sin ejecutarlo.
- `verify`: comprueba las rutas de evidencias y controles estáticos. Los criterios `device`/`manual` **requieren revisión humana** aunque exista archivo de evidencia.
- `run --execute`: exige Git en una rama no principal, árbol limpio, CLI `codex` disponible y autenticación configurada fuera del repositorio; ejecuta arquitecto → implementadores → integrador → QA, sin auto-merge. No ejecuta automáticamente las pruebas de Android/backend; estas se deben documentar y registrar como evidencia. **El agente puede modificar archivos**; revisar `git diff` antes de conservarlos.

## Gate de cierre
El estado `demostrado` requiere: criterios cumplidos, registro del comando o pasos, artefactos observables, plataforma real cuando corresponda, commit/revisión asociada y aceptación humana. Una ejecución de la fábrica o un test de esquema exitoso equivale solo a `infraestructura verificada`.

## Revisión de tecnologías y privacidad
- No simular permisos, cámara, overlays, trabajo en segundo plano o puente LynxJS–Kotlin como demostración de compatibilidad Android.
- No inferir que WorkManager ejecuta monitoreo continuo.
- Enviar al backend solo resultados derivados, nunca cuadros de cámara.
- Ninguna API adicional se añade sin contrato API aprobado.
- Las versiones se fijan en manifests/locks cuando se incorporen los proyectos, no en este documento.
- Documentar cualquier imposibilidad técnica mediante un ADR y vincularla al contrato.

## Sistemas de agentes soportados
Los perfiles Markdown son compatibles con la estructura de agentes personalizados de GitHub Copilot. La ejecución por `codex exec` requiere instalar y autenticar la herramienta; las integraciones cloud y sus planes no se habilitan por agregar archivos. No se proporcionan claves ni credenciales en el repositorio.
