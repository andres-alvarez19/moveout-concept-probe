"""Pruebas unitarias de contratos y orquestación sin ejecutar agentes."""

import copy
import json
import tempfile
import unittest
from pathlib import Path

from factory.contracts import (
    ContractError, evidence_report, load_catalog, roles_for, validate_contract,
)
from factory.prompts import compose_prompt


TEMPLATE = Path(__file__).resolve().parents[1] / "templates" / "contract.template.json"


class ContractTests(unittest.TestCase):
    def setUp(self):
        self.data = json.loads(TEMPLATE.read_text(encoding="utf-8"))

    def test_template_is_valid_but_not_approved(self):
        self.assertEqual(validate_contract(self.data)["status"], "draft")

    def test_role_plan_for_android(self):
        self.assertEqual(roles_for(self.data), ["architect", "android", "integrator", "qa"])

    def test_fullstack_plan(self):
        self.data["components"] = ["C1-B", "C2"]
        self.data["environment"]["requires_postgres"] = True
        self.data["acceptance"].append({
            "id": "AC-02", "description": "Transacción en PostgreSQL real",
            "method": "integration", "expected": "Sin datos duplicados",
            "evidence_path": "evidence/POC-001/postgres-test.md",
        })
        self.assertIn("backend", roles_for(validate_contract(self.data)))

    def test_reject_privacy_violation(self):
        self.data["privacy"]["no_video_transfer"] = False
        with self.assertRaises(ContractError):
            validate_contract(self.data)

    def test_reject_missing_android_device(self):
        self.data["environment"]["requires_real_android"] = False
        with self.assertRaises(ContractError):
            validate_contract(self.data)

    def test_reject_missing_postgres_integration(self):
        self.data["components"] = ["C2"]
        self.data["environment"]["requires_postgres"] = True
        self.data["environment"]["requires_real_android"] = False
        with self.assertRaises(ContractError):
            validate_contract(self.data)

    def test_reject_path_traversal(self):
        self.data["acceptance"][0]["evidence_path"] = "evidence/POC-001/../../bad.md"
        with self.assertRaises(ContractError):
            validate_contract(self.data)

    def test_reject_duplicate_acceptance_id(self):
        self.data["acceptance"].append(copy.deepcopy(self.data["acceptance"][0]))
        with self.assertRaises(ContractError):
            validate_contract(self.data)

    def test_reject_dependency_cycle(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp)
            first = copy.deepcopy(self.data)
            first["depends_on"] = ["POC-002"]
            second = copy.deepcopy(self.data)
            second["id"] = "POC-002"
            second["acceptance"][0]["evidence_path"] = "evidence/POC-002/bridge.md"
            second["depends_on"] = ["POC-001"]
            (folder / "POC-001.json").write_text(json.dumps(first), encoding="utf-8")
            (folder / "POC-002.json").write_text(json.dumps(second), encoding="utf-8")
            with self.assertRaises(ContractError):
                load_catalog(folder)

    def test_missing_evidence_is_not_accepted(self):
        with tempfile.TemporaryDirectory() as tmp:
            report = evidence_report(self.data, Path(tmp))
            self.assertFalse(report["evidence_complete"])
            self.assertTrue(report["human_approval_required"])

    def test_prompt_includes_contract_and_architecture(self):
        prompt = compose_prompt(self.data, "android")
        self.assertIn("POC-001", prompt)
        self.assertIn("MediaPipe", prompt)
        with self.assertRaises(ValueError):
            compose_prompt(self.data, "backend")


if __name__ == "__main__":
    unittest.main()
