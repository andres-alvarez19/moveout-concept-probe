"""Tests del orquestador sin lanzar Codex ni utilizar red/dispositivo."""
import copy
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from factory.contracts import ContractError
from factory.orchestrator import ordered, run_all, accept, load_state, fingerprint


def catalog_factory():
    template = json.loads((Path(__file__).resolve().parents[1] / "templates" / "contract.template.json").read_text())
    result = {}
    for n, deps in [(1, []), (2, ["POC-001"]), (3, ["POC-001"]), (4, ["POC-002", "POC-003"])]:
        data = copy.deepcopy(template)
        data["id"] = f"POC-{n:03d}"
        data["status"] = "approved"
        data["depends_on"] = deps
        data["acceptance"][0]["evidence_path"] = f"evidence/{data['id']}/bridge.md"
        result[data["id"]] = data
    return result


class OrchestratorTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.catalog = catalog_factory()
        self.git = patch("factory.orchestrator.guard", return_value="feat/test")
        self.git.start()
        self.addCleanup(self.git.stop)
        self.calls = []

    def executor(self, data, role, root):
        self.calls.append((data["id"], role))

    def test_topological_order(self):
        self.assertEqual(ordered(self.catalog), ["POC-001", "POC-002", "POC-003", "POC-004"])

    def test_draft_blocks_execution(self):
        self.catalog["POC-001"]["status"] = "draft"
        report = run_all(self.root, catalog=self.catalog, executor=self.executor)
        self.assertFalse(self.calls)
        self.assertEqual(report["contracts"]["POC-001"]["state"], "blocked")

    def test_checkpoint_after_roles_and_dependency_block(self):
        report = run_all(self.root, catalog=self.catalog, executor=self.executor)
        self.assertEqual(report["contracts"]["POC-001"]["state"], "review")
        self.assertEqual(report["contracts"]["POC-002"]["state"], "blocked")
        self.assertEqual(len(self.calls), 4)
        self.assertFalse(report["all_accepted"])

    def test_resume_after_failure_skips_finished_roles(self):
        attempts = []
        def executor(data, role, root):
            attempts.append(role)
            if role == "android" and attempts.count("android") == 1:
                raise ContractError("temporary")
        a = run_all(self.root, catalog=self.catalog, executor=executor)
        self.assertEqual(a["contracts"]["POC-001"]["roles_done"], ["architect"])
        b = run_all(self.root, resume=True, catalog=self.catalog, executor=executor)
        self.assertEqual(b["contracts"]["POC-001"]["state"], "review")
        self.assertEqual(attempts.count("architect"), 1)
        self.assertEqual(attempts.count("android"), 2)

    def test_acceptance_gate_requires_evidence(self):
        run_all(self.root, catalog=self.catalog, executor=self.executor)
        with self.assertRaises(ContractError):
            accept("POC-001", "reviewer", self.root, self.catalog)
        file = self.root / "evidence/POC-001/bridge.md"
        file.parent.mkdir(parents=True)
        file.write_text("observed", encoding="utf-8")
        report = accept("POC-001", "reviewer", self.root, self.catalog)
        self.assertEqual(report["contracts"]["POC-001"]["state"], "accepted")
        report = run_all(self.root, resume=True, catalog=self.catalog, executor=self.executor)
        self.assertEqual(report["contracts"]["POC-002"]["state"], "review")
        self.assertEqual(report["contracts"]["POC-003"]["state"], "review")

    def test_changed_contract_invalidates_checkpoint(self):
        run_all(self.root, catalog=self.catalog, executor=self.executor)
        self.catalog["POC-001"]["objective"] = "different"
        with self.assertRaises(ContractError):
            run_all(self.root, resume=True, catalog=self.catalog, executor=self.executor)

    def test_wrong_branch_invalidates_checkpoint(self):
        run_all(self.root, catalog=self.catalog, executor=self.executor)
        with patch("factory.orchestrator.guard", return_value="feat/other"):
            with self.assertRaises(ContractError):
                load_state(self.root, self.catalog)

    def test_no_unreviewed_acceptance(self):
        with self.assertRaises(ContractError):
            accept("POC-001", "reviewer", self.root, self.catalog)


if __name__ == "__main__":
    unittest.main()
