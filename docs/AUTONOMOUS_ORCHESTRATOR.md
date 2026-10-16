# Ejecución autónoma coordinada de los ocho contratos

## Qué automatiza

`python -m factory.cli run-all --execute` crea un checkpoint en `.factory/orchestrator-state.json` y recorre los contratos en orden topológico. Invoca roles Codex (architect, android/backend, integrator, qa) uno por uno, y guarda el checkpoint **después de cada rol**. Ante fallo/timeout conserva el error y permite `--resume`. Tras terminar todos los roles de un contrato, queda en estado **review**. El orquestador permite implementar el código de los ocho contratos progresivamente, pero **no puede declarar superadas pruebas de dispositivo físico ni certificar los 48 criterios sin observación real y aceptación humana**.

### Comandos

```bash
# 1. Fusionar contratos a main y crear rama de trabajo limpia
git checkout main && git pull
git checkout -b feat/moveout-poc-implementation
# 2. Revisar los contratos, sus fuentes normativas y cambiar draft -> approved mediante PR aprobado
python -m factory.cli check --all
python -m factory.cli plan-all
# 3. Con Codex CLI instalada y autenticada
python -m factory.cli run-all --execute
# 4. Ver progreso y corregir bloqueos
python -m factory.cli orchestrator-status
python -m factory.cli run-all --resume
# 5. SOLO tras revisar realmente todos los AC y sus evidencias:
python -m factory.cli accept POC-001 --reviewed-by "revisor-responsable"
# 6. Reanudar hasta los ocho contratos aceptados
python -m factory.cli run-all --resume
```

`run-all` devuelve código **3** mientras quede algún contrato sin aceptar: ese resultado es normal y no significa que Codex no haya generado código. El estado **accepted** solo se obtiene mediante la orden humana `accept` y la presencia de todas las evidencias previstas, nunca por un archivo vacío ni por el éxito del proceso Codex. La existencia de archivos no verifica su contenido: quien invoca `accept` asume explícitamente la responsabilidad de revisar los resultados.

## Precauciones

- Los ocho contratos de referencia están en `draft`. El orquestador **no los aprueba automáticamente**. Bloquea cada contrato no aprobado.
- No inventa pruebas de Android, acceso a cámara, certificados TLS o métricas. Dispositivo Android físico, PostgreSQL y entorno Linux/TLS deben proporcionarse.
- El proceso no realiza `git add`, commits, push, merges ni despliegues. Los cambios quedan en la rama de implementación, disponibles para revisión. Reanudar es posible aunque el árbol tenga cambios generados por agentes; iniciar un checkpoint nuevo exige rama limpia.
- Los logs/estado se conservan localmente bajo `.factory/`, excluidos de Git. Se almacenan stdout/stderr y las respuestas finales de Codex: **no deben contener secretos**; revisar y proteger acceso al workspace.
- No ejecutar dos orquestadores simultáneamente en el mismo directorio. El checkpoint es de un único proceso, no un candado distribuido.
- Si cambia un contrato o el conjunto de contratos durante la ejecución, se detiene antes de continuar para evitar aplicar un checkpoint obsoleto; requiere revisión.
- Los agentes pueden devolver éxito aunque la calidad del código sea insuficiente. El estado `review` significa **trabajo generado para revisión**, no PoC aceptado.
- Para disponer de los PDFs originales en ejecución, ofrecerlos al entorno Codex de manera autorizada. El repositorio no incluye las especificaciones completas.

## Estados

`pending` → `working` → `review` → (aceptación humana) `accepted`.

`blocked` se usa por borrador, dependencias no aceptadas, errores/timeout de agentes. `run-all --resume` reintenta cuando se resuelva la condición. Una vez aceptado un PoC, desbloquea los sucesores en el siguiente `--resume`.
