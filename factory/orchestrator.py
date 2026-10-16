"""Orquestador reanudable: catálogo DAG -> roles Codex -> revisión de evidencias.

No declara completados ensayos físicos ni aprueba contratos de forma automática.
"""
from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

from factory.contracts import ROOT, ContractError, load_catalog, evidence_report, roles_for
from factory.prompts import compose_prompt

RoleExecutor = Callable[[dict[str, Any], str, Path], None]
STATES = {"pending", "working", "review", "accepted", "blocked"}


def ordered(catalog: dict[str, dict[str, Any]]) -> list[str]:
    """Orden topológico estable sin tratar el ID numérico como secuencia de ejecución."""
    done: set[str] = set()
    result: list[str] = []
    def visit(cid: str) -> None:
        if cid in done:
            return
        for dep in sorted(catalog[cid]["depends_on"]):
            if dep not in catalog:
                raise ContractError(f"Dependencia inexistente: {dep}")
            visit(dep)
        done.add(cid)
        result.append(cid)
    for cid in sorted(catalog):
        visit(cid)
    return result


def fingerprint(data: dict[str, Any]) -> str:
    return hashlib.sha256(json.dumps(data, sort_keys=True, ensure_ascii=False).encode()).hexdigest()


def _write_atomic(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=path.parent, delete=False) as stream:
        json.dump(data, stream, indent=2, ensure_ascii=False)
        stream.write("\n")
        temp = Path(stream.name)
    os.replace(temp, path)


def _git(root: Path, *args: str) -> str:
    p = subprocess.run(["git", *args], cwd=root, capture_output=True, text=True, check=False)
    if p.returncode:
        raise ContractError(f"Git {' '.join(args)}: {p.stderr.strip()}")
    return p.stdout.strip()


def guard(root: Path, *, clean: bool = False) -> str:
    if not shutil.which("git"):
        raise ContractError("Se requiere Git")
    branch = _git(root, "branch", "--show-current")
    if not branch or branch in {"main", "master"}:
        raise ContractError("Orquestador prohibido en main/master o detached HEAD")
    if clean and _git(root, "status", "--porcelain", "--untracked-files=normal"):
        raise ContractError("Iniciar una ejecución nueva requiere árbol Git limpio")
    return branch


def _initial(catalog: dict[str, dict[str, Any]], branch: str) -> dict[str, Any]:
    return {
        "version": 1, "branch": branch, "created_at": datetime.now(timezone.utc).isoformat(),
        "contracts": {
            cid: {"fingerprint": fingerprint(data), "state": "pending", "roles_done": [],
                  "last_error": None, "reviewed_by": None}
            for cid, data in catalog.items()
        },
    }


def load_state(root: Path, catalog: dict[str, dict[str, Any]], *, initialize: bool = False) -> dict[str, Any]:
    path = root / ".factory" / "orchestrator-state.json"
    branch = guard(root, clean=initialize)
    if not path.exists():
        if not initialize:
            raise ContractError("No hay estado; iniciar con run-all --execute")
        state = _initial(catalog, branch)
        _write_atomic(path, state)
        return state
    if initialize:
        raise ContractError("Existe un estado previo; use run-all --resume")
    try:
        state = json.loads(path.read_text(encoding="utf-8"))
    except (ValueError, OSError) as exc:
        raise ContractError(f"Estado dañado: {exc}") from exc
    if state.get("version") != 1 or state.get("branch") != branch:
        raise ContractError("Versión/rama del checkpoint distinta; no se permite reanudar")
    entries = state.get("contracts")
    if not isinstance(entries, dict) or set(entries) != set(catalog):
        raise ContractError("El catálogo cambió respecto al checkpoint")
    for cid, data in catalog.items():
        entry = entries[cid]
        if entry.get("fingerprint") != fingerprint(data):
            raise ContractError(f"{cid} cambió desde la ejecución; revisión manual del checkpoint requerida")
        roles_done = entry.get("roles_done")
        roles = roles_for(data)
        if (entry.get("state") not in STATES or not isinstance(roles_done, list)
                or roles_done != roles[:len(roles_done)]):
            raise ContractError(f"Checkpoint inválido de {cid}")
    return state


def _save(root: Path, state: dict[str, Any]) -> None:
    _write_atomic(root / ".factory" / "orchestrator-state.json", state)


def codex_role(data: dict[str, Any], role: str, root: Path, timeout_seconds: int = 1800) -> None:
    if shutil.which("codex") is None:
        raise ContractError("Codex CLI ausente; instale y autentique Codex externamente")
    logs = root / ".factory" / "runs" / data["id"]
    logs.mkdir(parents=True, exist_ok=True)
    name = role + "-final.md"
    # Los prompts usan AGENTS.md, el perfil de agente y el JSON contractual.
    command = ["codex", "exec", "-C", str(root), "--sandbox", "workspace-write",
               "--output-last-message", str(logs / name), "-"]
    try:
        proc = subprocess.run(command, cwd=root, input=compose_prompt(data, role, root=root),
                              capture_output=True, text=True, timeout=timeout_seconds, check=False)
    except subprocess.TimeoutExpired as exc:
        raise ContractError(f"{data['id']} / {role}: timeout ({timeout_seconds}s)") from exc
    (logs / f"{role}-stdout.txt").write_text(proc.stdout, encoding="utf-8")
    (logs / f"{role}-stderr.txt").write_text(proc.stderr, encoding="utf-8")
    if proc.returncode:
        raise ContractError(f"{data['id']} / {role}: salida {proc.returncode}; ver .factory/runs")


def run_all(root: Path = ROOT, *, resume: bool = False,
            executor: RoleExecutor | None = None,
            catalog: dict[str, dict[str, Any]] | None = None) -> dict[str, Any]:
    """Ejecuta roles elegibles; las dependencias exigen aceptación humana.

    El estado local es checkpoint. La ejecución no hace commits, push, merge,
    aprobación de contratos, ni afirma que pruebas de Android hayan ocurrido.
    """
    catalog = catalog if catalog is not None else load_catalog(root / "contracts")
    state = load_state(root, catalog, initialize=not resume)
    run_role = executor or codex_role
    order = ordered(catalog)
    for cid in order:
        data = catalog[cid]
        entry = state["contracts"][cid]
        if entry["state"] in {"accepted", "review"}:
            continue
        if data["status"] != "approved":
            entry["state"] = "blocked"
            entry["last_error"] = "Contrato en draft: se requiere aprobación explícita"
            _save(root, state)
            continue
        if any(state["contracts"][dep]["state"] != "accepted" for dep in data["depends_on"]):
            entry["state"] = "blocked" if not entry["roles_done"] else "working"
            entry["last_error"] = "Dependencias pendientes de aceptación"
            _save(root, state)
            continue
        entry["state"] = "working"
        entry["last_error"] = None
        _save(root, state)
        for role in roles_for(data)[len(entry["roles_done"]):]:
            try:
                run_role(data, role, root)
            except (ContractError, OSError) as exc:
                entry["state"] = "blocked"
                entry["last_error"] = str(exc)
                _save(root, state)
                return summary(state, order)
            entry["roles_done"].append(role)
            _save(root, state)
        entry["state"] = "review"
        entry["last_error"] = "Requiere revisión de evidencias y aceptación humana"
        _save(root, state)
    return summary(state, order)


def accept(cid: str, reviewer: str, root: Path = ROOT,
           catalog: dict[str, dict[str, Any]] | None = None) -> dict[str, Any]:
    """Aceptar solo evidencias presentes; requiere decisión humana explícita.

    Los AC requieren verificar su contenido fuera del orquestador. 'accept'
    registra esa decisión, no la simula ni automatiza.
    """
    catalog = catalog if catalog is not None else load_catalog(root / "contracts")
    if cid not in catalog or not reviewer.strip():
        raise ContractError("Contrato o identificador de revisor inválido")
    state = load_state(root, catalog)
    entry = state["contracts"][cid]
    if entry["state"] != "review":
        raise ContractError(f"{cid} no ha completado todos los roles")
    report = evidence_report(catalog[cid], root)
    if not report["evidence_complete"]:
        missing = [x["id"] for x in report["criteria"] if not x["evidence_present"]]
        raise ContractError(f"Evidencias ausentes: {', '.join(missing)}")
    if any(state["contracts"][dep]["state"] != "accepted" for dep in catalog[cid]["depends_on"]):
        raise ContractError("Dependencias sin aceptación")
    entry["state"] = "accepted"
    entry["reviewed_by"] = reviewer.strip()
    entry["reviewed_at"] = datetime.now(timezone.utc).isoformat()
    entry["last_error"] = None
    _save(root, state)
    return summary(state, ordered(catalog))


def summary(state: dict[str, Any], order: list[str]) -> dict[str, Any]:
    return {
        "order": order,
        "counts": {s: sum(state["contracts"][x]["state"] == s for x in order) for s in sorted(STATES)},
        "contracts": {cid: {key: value for key, value in state["contracts"][cid].items()
                            if key not in {"fingerprint"}} for cid in order},
        "all_accepted": all(state["contracts"][x]["state"] == "accepted" for x in order),
        "human_approval_required": True,
    }


def status(root: Path = ROOT) -> dict[str, Any]:
    catalog = load_catalog(root / "contracts")
    return summary(load_state(root, catalog), ordered(catalog))
