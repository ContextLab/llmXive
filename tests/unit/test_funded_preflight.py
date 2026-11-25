"""The reliability run's preflight reports an unusable funded path, without detail."""

from __future__ import annotations

import importlib.util
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def _module():
    spec = importlib.util.spec_from_file_location("funded_preflight", ROOT / "scripts/ci/funded_preflight.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _repo(tmp_path: Path) -> Path:
    subprocess.run(["git", "init", "-q", str(tmp_path)], check=True)
    return tmp_path


def test_a_missing_bill_to_id_is_reported_by_type_only(tmp_path, monkeypatch):
    monkeypatch.delenv("LLMXIVE_HF_BILL_TO", raising=False)
    assert _module().check(_repo(tmp_path)) == "funded guard unavailable (FundedUnavailable)"


def test_a_repository_without_the_ledger_remote_is_reported_and_names_nothing(tmp_path, monkeypatch):
    """The run-4 failure: settings present, but the fresh repository has no ``origin``."""
    monkeypatch.setenv("LLMXIVE_HF_BILL_TO", "placeholder-group")
    monkeypatch.setenv("HF_TOKEN", "placeholder-token")
    monkeypatch.setenv("LLMXIVE_FUNDED_LEDGER_ANCHOR", "0" * 40)
    monkeypatch.delenv("LLMXIVE_FUNDED_LEDGER_REMOTE", raising=False)
    reason = _module().check(_repo(tmp_path))
    assert reason == "funded guard unavailable (FundedUnavailable)"
    assert "placeholder" not in reason
