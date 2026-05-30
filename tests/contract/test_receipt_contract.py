"""T025 — Contract tests for state/results.py + results/harness.py (spec 016, US2).

All tests use real tmp files and a real env key via monkeypatch.
No mocks, no stubs.
"""

from __future__ import annotations

import hashlib

import pytest

from llmxive.results.harness import mint_receipt, result_backed
from llmxive.results.receipt import (
    RECEIPT_KEY_ENV,
    Receipt,
    load_signing_key,
    sign_receipt,
    verify_receipt,
)
from llmxive.state import results as _result_store


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def repo_root(tmp_path):
    return tmp_path


@pytest.fixture(autouse=True)
def _set_signing_key(monkeypatch):
    monkeypatch.setenv(RECEIPT_KEY_ENV, "contract-test-receipt-key")


# ---------------------------------------------------------------------------
# T025-a: save → load round-trip
# ---------------------------------------------------------------------------

class TestResultStore:
    def test_save_load_roundtrip(self, repo_root):
        key = load_signing_key()
        payload = {
            "result_id": "r_aabb1234",
            "value": "7.5",
            "kind": "scalar",
            "producer": {"script_path": "run.py", "code_sha": "abc",
                         "entrypoint": "main", "seed": 0},
            "inputs": {"dataset_id": "ds1", "data_sha256": "ff00",
                       "params": {}},
            "env_sha": "envhash",
            "captured": {"stdout_path": "out.txt", "return_repr": "7.5"},
            "output_sha256": hashlib.sha256(b"7.5").hexdigest(),
            "created_at": "2026-05-30T00:00:00Z",
            "hmac": "",
        }
        sig = sign_receipt(payload, key=key)
        payload["hmac"] = sig
        r = Receipt(**payload)

        path = _result_store.save("PROJ-TEST", r, repo_root=repo_root)
        assert path.exists()
        assert path.name == "r_aabb1234.yaml"
        assert path.parent.name == "PROJ-TEST"

        loaded = _result_store.load("PROJ-TEST", "r_aabb1234", repo_root=repo_root)
        assert loaded is not None
        assert loaded.result_id == r.result_id
        assert loaded.value == r.value
        assert loaded.hmac == r.hmac

    def test_load_nonexistent_returns_none(self, repo_root):
        result = _result_store.load("NO-PROJ", "r_missing0", repo_root=repo_root)
        assert result is None

    def test_get_alias(self, repo_root):
        key = load_signing_key()
        payload = {
            "result_id": "r_gettest1",
            "value": "3.14",
            "kind": "scalar",
            "producer": {"script_path": "a.py", "code_sha": "cc",
                         "entrypoint": "run", "seed": 1},
            "inputs": {"dataset_id": "d2", "data_sha256": "ee",
                       "params": {}},
            "env_sha": "eenv",
            "captured": {"stdout_path": "o.txt", "return_repr": "3.14"},
            "output_sha256": hashlib.sha256(b"3.14").hexdigest(),
            "created_at": "2026-05-30T00:00:00Z",
            "hmac": "",
        }
        sig = sign_receipt(payload, key=key)
        payload["hmac"] = sig
        r = Receipt(**payload)
        _result_store.save("PROJ-GET", r, repo_root=repo_root)

        via_get = _result_store.get("PROJ-GET", "r_gettest1", repo_root=repo_root)
        assert via_get is not None
        assert via_get.result_id == "r_gettest1"

    def test_path_structure(self, repo_root):
        """Receipt lives at state/results/<PROJ>/<result_id>.yaml."""
        key = load_signing_key()
        payload = {
            "result_id": "r_pathtest",
            "value": "0",
            "kind": "scalar",
            "producer": {"script_path": "x.py", "code_sha": "dd",
                         "entrypoint": "f", "seed": 0},
            "inputs": {"dataset_id": "d", "data_sha256": "00",
                       "params": {}},
            "env_sha": "e",
            "captured": {"stdout_path": "s.txt", "return_repr": "0"},
            "output_sha256": hashlib.sha256(b"0").hexdigest(),
            "created_at": "2026-05-30T00:00:00Z",
            "hmac": "",
        }
        sig = sign_receipt(payload, key=key)
        payload["hmac"] = sig
        r = Receipt(**payload)
        path = _result_store.save("PROJ-PATH", r, repo_root=repo_root)
        expected = repo_root / "state" / "results" / "PROJ-PATH" / "r_pathtest.yaml"
        assert path == expected


# ---------------------------------------------------------------------------
# T025-b / T026-a: mint_receipt → persist → load round-trip
# ---------------------------------------------------------------------------

class TestMintReceipt:
    def test_mint_persists_and_is_loadable(self, repo_root):
        receipt = mint_receipt(
            value="100",
            kind="scalar",
            producer={"script_path": "s.py", "code_sha": "aaa",
                      "entrypoint": "run", "seed": 42},
            inputs={"dataset_id": "ds42", "data_sha256": "abc",
                    "params": {"x": 1}},
            env_sha="e_sha",
            captured={"stdout_path": "out.txt", "return_repr": "100"},
            repo_root=repo_root,
            project_id="PROJ-MINT",
        )
        assert receipt.result_id.startswith("r_")
        assert receipt.value == "100"
        assert len(receipt.hmac) == 64  # sha256 hex

        # Load from disk and verify HMAC still valid.
        loaded = _result_store.load("PROJ-MINT", receipt.result_id,
                                    repo_root=repo_root)
        assert loaded is not None
        key = load_signing_key()
        assert verify_receipt(loaded, key=key) is True

    def test_output_sha256_computed_from_value(self, repo_root):
        receipt = mint_receipt(
            value="hello",
            kind="scalar",
            producer={"script_path": "p.py", "code_sha": "b",
                      "entrypoint": "e", "seed": 0},
            inputs={"dataset_id": "d", "data_sha256": "x", "params": {}},
            env_sha="env",
            captured={"stdout_path": "o", "return_repr": "hello"},
            repo_root=repo_root,
            project_id="PROJ-SHA",
        )
        expected = hashlib.sha256(b"hello").hexdigest()
        assert receipt.output_sha256 == expected

    def test_result_id_derived_from_sha(self, repo_root):
        receipt = mint_receipt(
            value="xyz",
            kind="scalar",
            producer={"script_path": "p.py", "code_sha": "b",
                      "entrypoint": "e", "seed": 0},
            inputs={"dataset_id": "d", "data_sha256": "x", "params": {}},
            env_sha="env",
            captured={"stdout_path": "o", "return_repr": "xyz"},
            repo_root=repo_root,
            project_id="PROJ-IDTEST",
        )
        sha = hashlib.sha256(b"xyz").hexdigest()
        assert receipt.result_id == "r_" + sha[:8]


# ---------------------------------------------------------------------------
# T025-c / T026-b: result_backed
# ---------------------------------------------------------------------------

class TestResultBacked:
    def test_returns_receipt_for_matching_value(self, repo_root):
        mint_receipt(
            value="42",
            kind="scalar",
            producer={"script_path": "r.py", "code_sha": "c",
                      "entrypoint": "go", "seed": 0},
            inputs={"dataset_id": "ds", "data_sha256": "h", "params": {}},
            env_sha="ev",
            captured={"stdout_path": "o.txt", "return_repr": "42"},
            repo_root=repo_root,
            project_id="PROJ-BACKED",
        )
        result = result_backed("42", "PROJ-BACKED", repo_root=repo_root)
        assert result is not None
        assert result.value == "42"

    def test_returns_none_for_non_matching_value(self, repo_root):
        mint_receipt(
            value="42",
            kind="scalar",
            producer={"script_path": "r.py", "code_sha": "c",
                      "entrypoint": "go", "seed": 0},
            inputs={"dataset_id": "ds", "data_sha256": "h", "params": {}},
            env_sha="ev",
            captured={"stdout_path": "o.txt", "return_repr": "42"},
            repo_root=repo_root,
            project_id="PROJ-NOMATCH",
        )
        result = result_backed("999", "PROJ-NOMATCH", repo_root=repo_root)
        assert result is None

    def test_corrupted_hmac_returns_none(self, repo_root):
        """A receipt whose HMAC is corrupted on disk → result_backed returns None."""
        receipt = mint_receipt(
            value="55",
            kind="scalar",
            producer={"script_path": "r.py", "code_sha": "c",
                      "entrypoint": "go", "seed": 0},
            inputs={"dataset_id": "ds", "data_sha256": "h", "params": {}},
            env_sha="ev",
            captured={"stdout_path": "o.txt", "return_repr": "55"},
            repo_root=repo_root,
            project_id="PROJ-CORRUPT",
        )
        # Corrupt the HMAC on disk.
        receipt_path = (repo_root / "state" / "results" / "PROJ-CORRUPT"
                        / f"{receipt.result_id}.yaml")
        import yaml
        raw = yaml.safe_load(receipt_path.read_text())
        raw["hmac"] = "a" * 64  # wrong HMAC
        receipt_path.write_text(yaml.safe_dump(raw, sort_keys=True))

        result = result_backed("55", "PROJ-CORRUPT", repo_root=repo_root)
        assert result is None

    def test_no_receipts_returns_none(self, repo_root):
        result = result_backed("any_value", "PROJ-EMPTY", repo_root=repo_root)
        assert result is None
