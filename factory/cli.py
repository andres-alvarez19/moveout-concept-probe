"""CLI de la fábrica: validación, planificación, prompts, evidencia y ejecución."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from factory.contracts import (
    ROOT, ContractError, evidence_report, load_catalog, load_contract, plan_for,
)
from factory.prompts import compose_prompt
from factory.runner import run_agents
from factory.orchestrator import run_all, accept, status as orchestrator_status, ordered


REQUIRED_FILES = (
    "AGENTS.md",
    "docs/AGENT_FACTORY.md",
    "docs/POC_ROADMAP.md",
    "factory/contract.schema.json",
    ".github/workflows/factory-ci.yml",
    ".github/agents/architect.agent.md",
    ".github/agents/android.agent.md",
    ".github/agents/backend.agent.md",
    ".github/agents/integrator.agent.md",
    ".github/agents/qa.agent.md",
)


def _json(data: object) -> None:
    print(json.dumps(data, ensure_ascii=False, indent=2))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m factory.cli", description="Fábrica agéntica contract-first MoveOut"
    )
    sub = parser.add_subparsers(dest="command", required=True)
    check = sub.add_parser("check", help="Revisar infraestructura y catálogo")
    check.add_argument("--all", action="store_true", required=True)
    validate = sub.add_parser("validate", help="Validar contrato y dependencias")
    validate.add_argument("contract", type=Path)
    plan = sub.add_parser("plan", help="Obtener planificación de roles")
    plan.add_argument("contract", type=Path)
    prompt = sub.add_parser("prompt", help="Emitir instrucciones de un agente")
    prompt.add_argument("contract", type=Path)
    prompt.add_argument("--role", required=True,
                        choices=["architect", "android", "backend", "integrator", "qa"])
    verify = sub.add_parser("verify", help="Verificar existencia de evidencias")
    verify.add_argument("contract", type=Path)
    run = sub.add_parser("run", help="Invocar Codex CLI sobre rama limpia")
    run.add_argument("contract", type=Path)
    run.add_argument("--execute", action="store_true", required=True,
                     help="Confirmar la ejecución de agentes que modificarán archivos")
    all_cmd = sub.add_parser("run-all", help="Orquestar todos los contratos con checkpoints y dependencias")
    mode = all_cmd.add_mutually_exclusive_group(required=True)
    mode.add_argument("--execute", action="store_true", help="Iniciar ejecución en rama limpia")
    mode.add_argument("--resume", action="store_true", help="Reanudar checkpoint en la misma rama")
    sub.add_parser("orchestrator-status", help="Ver estado de los ocho contratos")
    review = sub.add_parser("accept", help="Registrar aceptación humana tras revisar TODAS las evidencias")
    review.add_argument("contract_id", help="ID POC-XXX")
    review.add_argument("--reviewed-by", required=True, help="Identificador no vacío del revisor responsable")
    sub.add_parser("plan-all", help="Orden topológico y dependencias del catálogo")
    return parser


def _contract_and_catalog(path: Path) -> dict:
    data = load_contract(path)
    catalog = load_catalog()
    if path.resolve().parent == (ROOT / "contracts").resolve():
        if path.name != data["id"] + ".json":
            raise ContractError("Nombre de archivo distinto a ID")
        if data["id"] not in catalog:
            raise ContractError("Contrato ausente del catálogo")
    for dep in data["depends_on"]:
        if dep not in catalog:
            raise ContractError(f"Dependencia no disponible: {dep}")
    return data


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        if args.command == "check":
            missing = [name for name in REQUIRED_FILES if not (ROOT / name).is_file()]
            if missing:
                raise ContractError(f"Faltan artefactos de la fábrica: {missing}")
            catalog = load_catalog()
            print(f"Fábrica válida. Contratos activos: {len(catalog)}.")
            if not catalog:
                print("Sin contratos aprobados ni PoC ejecutados; solo infraestructura validada.")
            return 0

        if args.command == "plan-all":
            catalog = load_catalog()
            _json({"order": ordered(catalog), "dependencies": {cid: catalog[cid]["depends_on"] for cid in ordered(catalog)}})
            return 0
        if args.command == "orchestrator-status":
            _json(orchestrator_status())
            return 0
        if args.command == "run-all":
            report = run_all(resume=args.resume)
            _json(report)
            return 0 if report["all_accepted"] else 3
        if args.command == "accept":
            _json(accept(args.contract_id, args.reviewed_by))
            return 0
        data = _contract_and_catalog(args.contract)
        if args.command == "validate":
            _json({"valid": True, "contract": data["id"], "status": data["status"]})
        elif args.command == "plan":
            _json(plan_for(data))
        elif args.command == "prompt":
            print(compose_prompt(data, args.role))
        elif args.command == "verify":
            report = evidence_report(data)
            _json(report)
            return 0 if report["evidence_complete"] else 3
        elif args.command == "run":
            _json({"executed": run_agents(data), "human_approval_required": True})
        return 0
    except (ContractError, ValueError, OSError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
