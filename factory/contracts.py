"""Validación determinista de contratos y dependencias (sin terceros)."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
CONTRACT_DIR = ROOT / "contracts"

COMPONENTS = {
    "C1-P": "android",
    "C1-B": "android",
    "C1-A": "android",
    "C1-D": "android",
    "C1-OS": "android",
    "C1-V": "android",
    "C1-R": "android",
    "C1-S": "android",
    "C2": "backend",
    "C3": "backend",
}
METHODS = {"automated", "integration", "device", "manual"}
ID_PATTERN = re.compile(r"^POC-[0-9]{3}$")
REF_PATTERN = re.compile(r"^(?:RF|RNF|OTR)-[0-9]{2}$")
AC_PATTERN = re.compile(r"^AC-[0-9]{2}$")


class ContractError(ValueError):
    """Contrato inválido, inseguro o inconsistente."""


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise ContractError(message)


def _string(value: Any, field: str) -> str:
    _require(isinstance(value, str) and bool(value.strip()), f"{field}: texto obligatorio")
    return value


def _string_list(value: Any, field: str, nonempty: bool = False) -> list[str]:
    _require(isinstance(value, list), f"{field}: se requiere lista")
    _require(not nonempty or bool(value), f"{field}: lista vacía")
    for item in value:
        _string(item, field)
    _require(len(value) == len(set(value)), f"{field}: elementos duplicados")
    return value


def _relative_evidence(path: str, contract_id: str) -> None:
    expected_prefix = f"evidence/{contract_id}/"
    p = Path(path)
    _require(
        path.startswith(expected_prefix)
        and not p.is_absolute()
        and ".." not in p.parts
        and len(p.parts) >= 3
        and not path.endswith("/"),
        f"evidence_path debe estar bajo {expected_prefix} y no escapar del repositorio",
    )


def validate_contract(data: Any) -> dict[str, Any]:
    _require(isinstance(data, dict), "El contrato debe ser un objeto JSON")
    required = {
        "version", "id", "title", "objective", "status", "components",
        "traceability", "acceptance", "depends_on", "privacy", "environment",
    }
    _require(set(data) == required, f"Campos obligatorios/exclusivos: {sorted(required)}")
    _require(type(data["version"]) is int and data["version"] == 1, "version debe ser 1")
    cid = _string(data["id"], "id")
    _require(bool(ID_PATTERN.fullmatch(cid)), "id debe ser POC-XXX")
    _string(data["title"], "title")
    _string(data["objective"], "objective")
    _require(data["status"] in {"draft", "approved"}, "status debe ser draft|approved")

    components = _string_list(data["components"], "components", nonempty=True)
    _require(set(components) <= set(COMPONENTS), "Componente inexistente en SDD")

    refs = data["traceability"]
    _require(isinstance(refs, dict) and set(refs) == {"sdd", "srs", "api"}, "traceability requiere sdd,srs,api")
    _string_list(refs["sdd"], "traceability.sdd", nonempty=True)
    for ref in _string_list(refs["srs"], "traceability.srs", nonempty=True):
        _require(bool(REF_PATTERN.fullmatch(ref)), f"Referencia SRS inválida: {ref}")
    for ref in _string_list(refs["api"], "traceability.api"):
        _require(bool(re.fullmatch(r"#[0-9]{2}", ref)), f"Contrato API inválido: {ref}")

    dependencies = _string_list(data["depends_on"], "depends_on")
    for dep in dependencies:
        _require(bool(ID_PATTERN.fullmatch(dep)) and dep != cid, f"Dependencia inválida: {dep}")

    privacy = data["privacy"]
    _require(
        isinstance(privacy, dict)
        and set(privacy) == {"no_video_storage", "no_video_transfer"}
        and privacy["no_video_storage"] is True
        and privacy["no_video_transfer"] is True,
        "Privacidad: está prohibido almacenar o transmitir video/fotogramas corporales",
    )

    env = data["environment"]
    _require(isinstance(env, dict) and set(env) == {"requires_real_android", "requires_postgres"},
             "environment requiere requires_real_android,requires_postgres")
    _require(all(type(x) is bool for x in env.values()), "environment: valores booleanos")
    if set(components) & {"C1-OS", "C1-V", "C1-B"}:
        _require(env["requires_real_android"], "Puente/Android OS/MediaPipe requieren evidencia en Android real")
    if set(components) & {"C2", "C3"}:
        _require(env["requires_postgres"], "Backend requiere PostgreSQL real en integración")

    acceptance = data["acceptance"]
    _require(isinstance(acceptance, list) and acceptance, "acceptance: se requiere al menos un criterio")
    seen: set[str] = set()
    for ac in acceptance:
        _require(isinstance(ac, dict) and set(ac) == {"id", "description", "method", "expected", "evidence_path"},
                 "Criterio requiere id,description,method,expected,evidence_path")
        aid = _string(ac["id"], "acceptance.id")
        _require(bool(AC_PATTERN.fullmatch(aid)) and aid not in seen, "acceptance.id: inválido/duplicado")
        seen.add(aid)
        _string(ac["description"], f"{aid}.description")
        _string(ac["expected"], f"{aid}.expected")
        _require(ac["method"] in METHODS, f"{aid}.method: método inválido")
        _relative_evidence(_string(ac["evidence_path"], f"{aid}.evidence_path"), cid)

    if env["requires_real_android"]:
        _require(any(a["method"] == "device" for a in acceptance),
                 "La prueba requiere criterio con método device")
    if env["requires_postgres"]:
        _require(any(a["method"] == "integration" for a in acceptance),
                 "La prueba requiere criterio de integración con PostgreSQL")
    return data


def load_contract(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ContractError(f"No se pudo leer {path}: {exc}") from exc
    return validate_contract(data)


def load_catalog(directory: Path = CONTRACT_DIR) -> dict[str, dict[str, Any]]:
    catalog: dict[str, dict[str, Any]] = {}
    for path in sorted(directory.glob("POC-*.json")):
        data = load_contract(path)
        _require(path.name == data["id"] + ".json", f"ID diferente del nombre: {path.name}")
        _require(data["id"] not in catalog, f"ID duplicado: {data['id']}")
        catalog[data["id"]] = data

    visiting: set[str] = set()
    visited: set[str] = set()

    def visit(cid: str) -> None:
        if cid in visited:
            return
        _require(cid not in visiting, f"Dependencia cíclica detectada en {cid}")
        visiting.add(cid)
        for dep in catalog[cid]["depends_on"]:
            _require(dep in catalog, f"{cid}: dependencia inexistente: {dep}")
            visit(dep)
        visiting.remove(cid)
        visited.add(cid)

    for cid in catalog:
        visit(cid)
    return catalog


def roles_for(data: dict[str, Any]) -> list[str]:
    components = data["components"]
    roles = ["architect"]
    if any(COMPONENTS[part] == "android" for part in components):
        roles.append("android")
    if any(COMPONENTS[part] == "backend" for part in components):
        roles.append("backend")
    roles.extend(["integrator", "qa"])
    return roles


def plan_for(data: dict[str, Any]) -> dict[str, Any]:
    return {
        "contract": data["id"],
        "status": data["status"],
        "depends_on": data["depends_on"],
        "components": data["components"],
        "roles_in_order": roles_for(data),
        "acceptance_ids": [a["id"] for a in data["acceptance"]],
        "human_approval_required": True,
        "device_verification_required": data["environment"]["requires_real_android"],
        "postgres_integration_required": data["environment"]["requires_postgres"],
    }


def evidence_report(data: dict[str, Any], root: Path = ROOT) -> dict[str, Any]:
    criteria = []
    for ac in data["acceptance"]:
        path = root / ac["evidence_path"]
        exists = path.is_file() and path.stat().st_size > 0
        criteria.append({
            "id": ac["id"],
            "method": ac["method"],
            "evidence_path": ac["evidence_path"],
            "evidence_present": exists,
            "manual_review_required": ac["method"] in {"manual", "device", "integration"},
        })
    return {
        "contract": data["id"],
        "evidence_complete": all(a["evidence_present"] for a in criteria),
        "human_approval_required": True,
        "criteria": criteria,
    }
