"""Compone instrucciones y contratos para agentes de codificación."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from factory.contracts import ROOT, roles_for


def compose_prompt(data: dict[str, Any], role: str, root: Path = ROOT) -> str:
    if role not in roles_for(data):
        raise ValueError(f"Agente {role} no corresponde al contrato {data['id']}")
    role_file = root / ".github" / "agents" / f"{role}.agent.md"
    profile = role_file.read_text(encoding="utf-8")
    if profile.startswith("---\n"):
        profile = profile.split("---", 2)[-1].strip()

    guardrails = (root / "AGENTS.md").read_text(encoding="utf-8")
    contract = json.dumps(data, ensure_ascii=False, indent=2)
    return (
        f"# Trabajo de agente: {role} / {data['id']}\n\n"
        "Solo ejecutar los criterios del contrato. La SRS v2.3 y los Contratos API v1.6 "
        "son normativos; el SDD v0.5 define la arquitectura. Si faltan fuentes, "
        "identificar los vacíos sin inventar implementaciones.\n\n"
        f"## Contrato de entrada\n\n```json\n{contract}\n```\n\n"
        f"## Perfil de agente\n\n{profile}\n\n"
        f"## Normas globales\n\n{guardrails}\n\n"
        "## Entregables\n"
        "- Resumen de los archivos cambiados y decisiones tomadas.\n"
        "- Comandos realmente ejecutados, resultados, errores y restricciones del entorno.\n"
        "- Evidencias para cada AC en la ruta exacta prevista (no fabricar evidencias).\n"
        "- Lista de criterios pendientes, especialmente pruebas físicas y aprobación humana.\n"
    )
