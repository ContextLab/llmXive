"""T028 — Real-call test: harness-signed execution receipts (spec 016, US2).

Gated: most tests run offline with a real env key (no network/LLM needed
because receipt logic is deterministic).  Parts requiring LLM/network calls
are gated behind LLMXIVE_REAL_TESTS.

SC-004: forge/alter a receipt (wrong key, mutate value) → verify_receipt
False and resolution blocked.
"""

from __future__ import annotations

import hashlib
import os
import subprocess
import sys
import textwrap
from pathlib import Path

import pytest

from llmxive.claims.models import Claim, ClaimKind, ClaimStatus
from llmxive.claims.resolve import resolve_result
from llmxive.results.harness import mint_receipt, result_backed
from llmxive.results.receipt import (
    RECEIPT_KEY_ENV,
    Receipt,
    load_signing_key,
    sign_receipt,
    verify_receipt,
)
from llmxive.state import results as _result_store

# All receipt tests are offline-deterministic; set the key for the session.
pytestmark = pytest.mark.usefixtures("_signing_key")


@pytest.fixture(autouse=True)
def _signing_key(monkeypatch):
    monkeypatch.setenv(RECEIPT_KEY_ENV, "real-call-test-receipt-key-t028")


@pytest.fixture
def repo_root(tmp_path):
    return tmp_path


# ---------------------------------------------------------------------------
# T028-a: run a real Python script via subprocess, mint receipt, verify
# ---------------------------------------------------------------------------

class TestRealScriptMintAndVerify:
    def test_real_script_execution(self, tmp_path, repo_root):
        """Run a real Python script, capture stdout/return, mint receipt → VERIFIED."""
        # Write a trivial script that computes a sum and prints it.
        script = tmp_path / "sum_script.py"
        script.write_text(textwrap.dedent("""\
            # Real script: sums 1..10
            result = sum(range(1, 11))
            print(result)
        """))

        # Execute the script as a real subprocess.
        proc = subprocess.run(
            [sys.executable, str(script)],
            capture_output=True, text=True, check=True,
        )
        stdout = proc.stdout.strip()
        return_repr = stdout  # script prints the result
        assert stdout == "55", f"Expected 55 from sum(range(1,11)), got: {stdout}"

        # Mint a receipt from the real captured output.
        receipt = mint_receipt(
            value=return_repr,
            kind="scalar",
            producer={
                "script_path": str(script.relative_to(tmp_path)),
                "code_sha": hashlib.sha256(script.read_bytes()).hexdigest()[:16],
                "entrypoint": "__main__",
                "seed": 0,
            },
            inputs={"dataset_id": "none", "data_sha256": "n/a", "params": {}},
            env_sha=hashlib.sha256(sys.version.encode()).hexdigest()[:16],
            captured={"stdout_path": "stdout.txt", "return_repr": return_repr},
            repo_root=repo_root,
            project_id="PROJ-T028",
        )

        key = load_signing_key()
        assert verify_receipt(receipt, key=key) is True
        assert receipt.value == "55"
        assert receipt.output_sha256 == hashlib.sha256(b"55").hexdigest()

    def test_result_backed_verified_after_mint(self, tmp_path, repo_root):
        """mint → result_backed returns the receipt for the exact value."""
        mint_receipt(
            value="55",
            kind="scalar",
            producer={"script_path": "s.py", "code_sha": "abc",
                      "entrypoint": "__main__", "seed": 0},
            inputs={"dataset_id": "none", "data_sha256": "n/a", "params": {}},
            env_sha="test_env",
            captured={"stdout_path": "out.txt", "return_repr": "55"},
            repo_root=repo_root,
            project_id="PROJ-T028B",
        )
        r = result_backed("55", "PROJ-T028B", repo_root=repo_root)
        assert r is not None
        assert r.value == "55"


# ---------------------------------------------------------------------------
# T028-b: result numeral with NO receipt → blocked (NOT_ENOUGH_INFO)
# ---------------------------------------------------------------------------

class TestUnbackedResultBlocked:
    def _make_result_claim(self, value: str, artifact_path: str) -> Claim:
        from llmxive.claims.models import compute_claim_id
        cid = compute_claim_id(ClaimKind.RESULT, value, "test context")
        return Claim(
            claim_id=cid,
            kind=ClaimKind.RESULT,
            raw_text=value,
            canonical=value,
            context="test context",
            artifact_path=artifact_path,
            source_type="result",
            status=ClaimStatus.PENDING,
            resolved_value=None,
            evidence=None,
            resolver=None,
            attempts=0,
            updated_at="2026-05-30T00:00:00Z",
        )

    def test_no_receipt_returns_not_enough_info(self, repo_root):
        """A RESULT claim with no backing receipt → NOT_ENOUGH_INFO."""
        claim = self._make_result_claim(
            "42.7",
            "projects/PROJ-T028C/implementation_plan.md",
        )
        verdict = resolve_result(claim, backend=None, model=None,
                                 repo_root=repo_root)
        assert verdict.status == ClaimStatus.NOT_ENOUGH_INFO
        assert verdict.resolver == "resolve_result"
        assert "no signed receipt" in (verdict.evidence or {}).get("note", "")

    def test_backed_result_returns_verified(self, repo_root):
        """A RESULT claim backed by a valid receipt → VERIFIED + result_id in evidence."""
        mint_receipt(
            value="42.7",
            kind="scalar",
            producer={"script_path": "p.py", "code_sha": "cc",
                      "entrypoint": "run", "seed": 0},
            inputs={"dataset_id": "ds", "data_sha256": "xx", "params": {}},
            env_sha="ev",
            captured={"stdout_path": "o.txt", "return_repr": "42.7"},
            repo_root=repo_root,
            project_id="PROJ-T028D",
        )
        claim = self._make_result_claim(
            "42.7",
            "projects/PROJ-T028D/implementation_plan.md",
        )
        verdict = resolve_result(claim, backend=None, model=None,
                                 repo_root=repo_root)
        assert verdict.status == ClaimStatus.VERIFIED
        assert verdict.value == "42.7"
        # FR-010: result_id must be in evidence for downstream citation
        assert "result_id" in (verdict.evidence or {})
        assert (verdict.evidence or {}).get("source", "").startswith("result:")


# ---------------------------------------------------------------------------
# T028-c / SC-004: forge / alter a receipt → verify_receipt False → blocked
# ---------------------------------------------------------------------------

class TestForgeryBlocked:
    def test_wrong_key_fails_verify(self, repo_root):
        """Signing with one key and verifying with another → False (SC-004)."""
        key = load_signing_key()
        receipt = mint_receipt(
            value="100",
            kind="scalar",
            producer={"script_path": "p.py", "code_sha": "aa",
                      "entrypoint": "e", "seed": 0},
            inputs={"dataset_id": "d", "data_sha256": "h", "params": {}},
            env_sha="ev",
            captured={"stdout_path": "o.txt", "return_repr": "100"},
            repo_root=repo_root,
            project_id="PROJ-FORGE1",
        )
        wrong_key = b"attacker-supplied-wrong-key"
        assert verify_receipt(receipt, key=wrong_key) is False

    def test_mutated_value_on_disk_blocked(self, repo_root):
        """Mutating the value field on disk → result_backed returns None (SC-004)."""
        import yaml
        mint_receipt(
            value="200",
            kind="scalar",
            producer={"script_path": "p.py", "code_sha": "aa",
                      "entrypoint": "e", "seed": 0},
            inputs={"dataset_id": "d", "data_sha256": "h", "params": {}},
            env_sha="ev",
            captured={"stdout_path": "o.txt", "return_repr": "200"},
            repo_root=repo_root,
            project_id="PROJ-FORGE2",
        )
        # Mutate the value on disk without re-signing.
        results_dir = repo_root / "state" / "results" / "PROJ-FORGE2"
        yaml_files = list(results_dir.glob("*.yaml"))
        assert yaml_files, "No receipt file found"
        raw = yaml.safe_load(yaml_files[0].read_text())
        raw["value"] = "999"  # forge the value
        yaml_files[0].write_text(yaml.safe_dump(raw, sort_keys=True))

        # result_backed for the ORIGINAL value → no matching sha
        r = result_backed("200", "PROJ-FORGE2", repo_root=repo_root)
        assert r is None

        # result_backed for the forged value → sha matches but HMAC fails
        r2 = result_backed("999", "PROJ-FORGE2", repo_root=repo_root)
        assert r2 is None

    def test_corrupted_hmac_on_disk_blocked(self, repo_root):
        """Receipt with a corrupted HMAC on disk → result_backed None (SC-004)."""
        import yaml
        mint_receipt(
            value="300",
            kind="scalar",
            producer={"script_path": "p.py", "code_sha": "bb",
                      "entrypoint": "e", "seed": 0},
            inputs={"dataset_id": "d", "data_sha256": "h", "params": {}},
            env_sha="ev",
            captured={"stdout_path": "o.txt", "return_repr": "300"},
            repo_root=repo_root,
            project_id="PROJ-FORGE3",
        )
        results_dir = repo_root / "state" / "results" / "PROJ-FORGE3"
        yaml_files = list(results_dir.glob("*.yaml"))
        assert yaml_files
        raw = yaml.safe_load(yaml_files[0].read_text())
        raw["hmac"] = "0" * 64  # corrupt HMAC
        yaml_files[0].write_text(yaml.safe_dump(raw, sort_keys=True))

        r = result_backed("300", "PROJ-FORGE3", repo_root=repo_root)
        assert r is None

    def test_key_never_appears_in_receipt_fields(self, repo_root):
        """The signing key must not appear in any field of the minted Receipt."""
        import json as _json
        key_str = "real-call-test-receipt-key-t028"
        receipt = mint_receipt(
            value="77",
            kind="scalar",
            producer={"script_path": "p.py", "code_sha": "cc",
                      "entrypoint": "e", "seed": 0},
            inputs={"dataset_id": "d", "data_sha256": "h", "params": {}},
            env_sha="ev",
            captured={"stdout_path": "o.txt", "return_repr": "77"},
            repo_root=repo_root,
            project_id="PROJ-KEYCHECK",
        )
        receipt_json = _json.dumps({
            "result_id": receipt.result_id,
            "value": receipt.value,
            "kind": receipt.kind,
            "producer": receipt.producer,
            "inputs": receipt.inputs,
            "env_sha": receipt.env_sha,
            "captured": receipt.captured,
            "output_sha256": receipt.output_sha256,
            "created_at": receipt.created_at,
            "hmac": receipt.hmac,
        })
        assert key_str not in receipt_json
