# MoveOut Concept Probe

**Fábrica agéntica contract-first para demostrar la viabilidad de la arquitectura MoveOut.**

Este repositorio se destina a experimentos reproducibles, no a desplegar el producto completo. La primera entrega incorpora los agentes, el orquestador y los controles. **Todavía no se han creado contratos de PoC ni software móvil/backend.**

## Referencias normativas

- **SDD MoveOut v0.5** (16-10-2026): arquitectura y decisiones ADR-0001 a ADR-0006.
- **SRS MoveOut v2.3** (15-10-2026): requisitos RF/RNF.
- **Contratos API MoveOut v1.6** (15-10-2026): rutas y formatos públicos; nunca inventar endpoints.

Documentación: [instrucciones para agentes](AGENTS.md), [manual de fábrica](docs/AGENT_FACTORY.md) y [matriz inicial de capacidades por demostrar](docs/POC_ROADMAP.md).

## Uso

Requiere Python 3.11+ y Git; para ejecución autónoma opcional se necesita Codex CLI instalado y autenticado externamente.

```bash
python -m factory.cli check --all
python -m unittest discover -s factory/tests -v
```

Cuando exista y se apruebe un contrato en `contracts/`:

```bash
python -m factory.cli validate contracts/POC-001.json
python -m factory.cli plan contracts/POC-001.json
python -m factory.cli prompt contracts/POC-001.json --role android
# Opcional: en rama local limpia, con Codex CLI disponible y contrato approved
python -m factory.cli run contracts/POC-001.json --execute
python -m factory.cli verify contracts/POC-001.json
```

**Importante:** `verify` comprueba la presencia de archivos de evidencia; **no certifica su autenticidad ni los criterios de aceptación**. Las pruebas físicas y la aceptación humana siguen siendo obligatorias. CI valida fábrica y contratos; no certifica compatibilidad Android, resultados MediaPipe, backend ni VPS.

## Estructura

- `.github/agents/`: agentes especializados utilizables en GitHub Copilot.
- `AGENTS.md`: instrucciones transversales de codificación/arquitectura.
- `factory/`: CLI, validación de contratos, composición de prompts, runner y tests.
- `factory/templates/`: plantilla **no aprobada**, no es un PoC.
- `contracts/`: entrada de contratos funcionales de la siguiente fase.
- `docs/POC_ROADMAP.md`: mapa de hipótesis técnicas y evidencia esperada.
- `evidence/POC-XXX/`: solo cuando exista un contrato, se almacenan reportes y enlaces a artefactos pertinentes, sin video corporal ni secretos.

## Garantías y límites

La automatización no habilita por sí sola permisos Android, acceso a datos de otras aplicaciones, integración nativa LynxJS–Kotlin ni detección MediaPipe. Cada capacidad deberá implementarse y probarse con la plataforma especificada. No se realiza despliegue ni merge automático.
