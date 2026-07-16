"""Issue #1139 round-2 downstream fixes (audit A4/A5/A6, P1-2 residual).

Four independent fixes, each with a real (no-mock) test:

* Fix 1 — ``scripts/maintenance/backfill_failure_class.py`` reconstructs the
  durable ``failure_class`` on legacy execution-status records.
* Fix 2 — the paper-compile workflow now invokes the deterministic PDF audit
  (non-failing, bounded) so restyled papers reach ``audited``.
* Fix 3 — the ``reproduction.md`` state-reader allowlist justification names the
  ACCURATE consumer (git-committed human artifact, not a dashboard link).
* Fix 4 — a failed GPU-offload record carries the semantic-gate diagnosis.
"""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import yaml

_REPO = Path(__file__).resolve().parents[2]


# --------------------------------------------------------------------------- #
# Fix 1: backfill_failure_class migration
# --------------------------------------------------------------------------- #
def _load_backfill():
    script = _REPO / "scripts" / "maintenance" / "backfill_failure_class.py"
    spec = importlib.util.spec_from_file_location("backfill_failure_class", script)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


def _seed_exec_status(repo: Path, pid: str, rec: dict) -> Path:
    d = repo / "state" / "execution_status"
    d.mkdir(parents=True, exist_ok=True)
    p = d / f"{pid}.json"
    p.write_text(json.dumps(rec, indent=2) + "\n", encoding="utf-8")
    return p


def test_backfill_failure_class_reconstructs_classes(tmp_path: Path) -> None:
    mod = _load_backfill()

    # compute_env failure (CUDA), no failure_class key.
    _seed_exec_status(tmp_path, "PROJ-001", {
        "project_id": "PROJ-001", "ok": False,
        "reason": "analysis failed", "artifacts": [],
        "failures": ["python code/train.py -> rc=1: RuntimeError: CUDA out of memory"],
    })
    # data_unreachable failure (HfUriError), failure_class present but null.
    _seed_exec_status(tmp_path, "PROJ-002", {
        "project_id": "PROJ-002", "ok": False, "failure_class": None,
        "reason": "dataset load failed", "artifacts": [],
        "failures": ["python code/load.py -> rc=1: HfUriError: Repository id must be 'namespace/name'"],
    })
    # fabrication failure — signal only in the reason string (SemanticGate prose).
    _seed_exec_status(tmp_path, "PROJ-003", {
        "project_id": "PROJ-003", "ok": False,
        "reason": "2 fabricated/simulated-result signal(s) — results are not real measurements",
        "artifacts": [], "failures": ["python code/run.py -> rc=0"],
    })
    # ok=true — MUST be left untouched.
    _seed_exec_status(tmp_path, "PROJ-004", {
        "project_id": "PROJ-004", "ok": True,
        "reason": "3 artifacts produced", "artifacts": ["results/x.json"], "failures": [],
    })
    # already-classified failure — MUST be left untouched (idempotent).
    _seed_exec_status(tmp_path, "PROJ-005", {
        "project_id": "PROJ-005", "ok": False, "failure_class": "execution_bug",
        "reason": "ImportError", "artifacts": [],
        "failures": ["python code/a.py -> rc=1: ImportError"],
    })

    rc = mod.main(["--apply", "--repo-root", str(tmp_path)])
    assert rc == 0

    def _load(pid: str) -> dict:
        return json.loads((tmp_path / "state" / "execution_status" / f"{pid}.json").read_text())

    assert _load("PROJ-001")["failure_class"] == "compute_env"
    assert _load("PROJ-001")["evidence"]  # matched infra signal recorded
    assert _load("PROJ-002")["failure_class"] == "data_unreachable"
    assert _load("PROJ-003")["failure_class"] == "fabrication"

    # ok=true untouched: no failure_class key added.
    p004 = _load("PROJ-004")
    assert p004["ok"] is True
    assert "failure_class" not in p004 or p004["failure_class"] is None

    # already-classified untouched: value preserved.
    assert _load("PROJ-005")["failure_class"] == "execution_bug"


def test_backfill_failure_class_dry_run_writes_nothing(tmp_path: Path) -> None:
    mod = _load_backfill()
    rec = {
        "project_id": "PROJ-010", "ok": False,
        "reason": "boom", "artifacts": [],
        "failures": ["python code/x.py -> rc=1: RuntimeError: CUDA error"],
    }
    p = _seed_exec_status(tmp_path, "PROJ-010", rec)
    before = p.read_text()
    rc = mod.main(["--repo-root", str(tmp_path)])  # no --apply
    assert rc == 0
    assert p.read_text() == before  # dry-run mutated nothing


# --------------------------------------------------------------------------- #
# Fix 2: paper-compile workflow wires the PDF audit (safe + bounded + non-failing)
# --------------------------------------------------------------------------- #
def test_paper_compile_workflow_wires_pdf_audit() -> None:
    wf_path = _REPO / ".github" / "workflows" / "paper-compile.yml"
    doc = yaml.safe_load(wf_path.read_text())  # parses cleanly
    steps = doc["jobs"]["compile"]["steps"]
    audit_steps = [s for s in steps if "pdf-pipeline audit" in (s.get("run") or "")]
    assert len(audit_steps) == 1, "expected exactly one PDF-audit step"
    run = audit_steps[0]["run"]
    # Non-failing: swallows per-paper exit codes and never fails the job.
    assert "set +e" in run and "exit 0" in run
    # Bounded: caps the sweep so one tick cannot audit unboundedly.
    assert "200" in run
    # Runs AFTER compile and BEFORE the commit step so state changes get pushed.
    names = [s.get("name", "") for s in steps]
    assert names.index(audit_steps[0]["name"]) < names.index("Commit + push")


# --------------------------------------------------------------------------- #
# Fix 3: reproduction.md allowlist justification names the real consumer
# --------------------------------------------------------------------------- #
def test_reproduction_allowlist_justification_is_accurate() -> None:
    from llmxive.checks.state_readers import ALLOWLIST

    just = ALLOWLIST["reproduction.md"]
    # Accurate consumer: a git-committed human artifact.
    assert "git-committed" in just
    assert "human" in just
    # No longer claims the non-existent dashboard link (audit A4).
    assert "dashboard artifact" not in just


# --------------------------------------------------------------------------- #
# Fix 4: a failed offload record carries the gate's diagnosis
# --------------------------------------------------------------------------- #
def test_failed_offload_record_carries_reason(tmp_path: Path) -> None:
    from llmxive.state import execution_status

    pid = "PROJ-900"
    # A prior in-flight offload sub-record (submitted) — no reason yet.
    submitted = execution_status.record_offload(
        pid, status="submitted", kernel_ref="user/kern-1", repo_root=tmp_path,
    )
    assert submitted["offload"]["reason"] == ""  # pending carries no failure reason

    # Now the bundle fails the semantic gate: reason + evidence must persist.
    rec = execution_status.record_offload(
        pid, status="failed", kernel_ref="user/kern-1",
        reason="2 fabricated/simulated-result signal(s) — results are not real",
        evidence=["results/metrics.json: constant 0.0"],
        repo_root=tmp_path,
    )
    off = rec["offload"]
    assert off["status"] == "failed"
    assert "fabricated" in off["reason"]
    assert off["evidence"] == ["results/metrics.json: constant 0.0"]

    # Durable: re-loading from disk shows the same diagnosis.
    reloaded = execution_status.offload_state(pid, repo_root=tmp_path)
    assert reloaded["reason"] == off["reason"]
    assert reloaded["evidence"] == off["evidence"]
    # And the offload transition never bumped fix_rounds.
    assert rec["fix_rounds"] == 0
