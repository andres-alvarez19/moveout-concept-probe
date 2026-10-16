"""Orquestación secuencial, explícita y opt-in mediante Codex CLI."""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path
from typing import Any

from factory.contracts import ROOT, ContractError, roles_for
from factory.prompts import compose_prompt


def _git(root: Path, *args: str) -> str:
    proc = subprocess.run(["git", *args], cwd=root, capture_output=True, text=True, check=False)
    if proc.returncode:
        raise ContractError(f"Error Git: {proc.stderr.strip()}")
    return proc.stdout.strip()


def guard_execution(data: dict[str, Any], root: Path = ROOT) -> None:
    if data["status"] != "approved":
        raise ContractError("El contrato debe tener status=approved antes de ejecutar agentes")
    if shutil.which("git") is None:
        raise ContractError("Git no está instalado")
    if shutil.which("codex") is None:
        raise ContractError("Codex CLI no disponible: instálelo y autentíquelo externamente")
    branch = _git(root, "branch", "--show-current")
    if not branch or branch in {"main", "master"}:
        raise ContractError("Trabaje sobre una rama de PoC, nunca main/master")
    if _git(root, "status", "--porcelain"):
        raise ContractError("Árbol Git con cambios: revise/guarde antes de ejecutar la fábrica")


def run_agents(data: dict[str, Any], root: Path = ROOT, timeout_seconds: int = 900) -> list[dict[str, Any]]:
    guard_execution(data, root)
    run_dir = root / ".factory" / "runs" / data["id"]
    run_dir.mkdir(parents=True, exist_ok=True)
    results = []
    for role in roles_for(data):
        prompt = compose_prompt(data, role, root=root)
        output_path = run_dir / f"{role}-final.md"
        # Sin shell: evita interpolar instrucciones o ejecutar comandos del contrato.
        command = [
            "codex", "exec", "-C", str(root),
            "--sandbox", "workspace-write",
            "--output-last-message", str(output_path),
            "-",
        ]
        try:
            proc = subprocess.run(
                command, cwd=root, input=prompt, capture_output=True,
                text=True, check=False, timeout=timeout_seconds,
            )
        except subprocess.TimeoutExpired as exc:
            raise ContractError(f"Agente {role} excedió {timeout_seconds}s") from exc
        (run_dir / f"{role}-stdout.txt").write_text(proc.stdout, encoding="utf-8")
        (run_dir / f"{role}-stderr.txt").write_text(proc.stderr, encoding="utf-8")
        results.append({"role": role, "exit_code": proc.returncode, "output": str(output_path)})
        if proc.returncode:
            raise ContractError(
                f"Agente {role} falló ({proc.returncode}); revisar {run_dir / (role + '-stderr.txt')}"
            )
    return results
