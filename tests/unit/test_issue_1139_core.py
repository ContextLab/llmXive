"""Regression tests locking the CORE fixes for GitHub issue #1139.

Each test pins ONE already-implemented fix against the exact anti-pattern the
recon reproduced, using REAL temp dirs + REAL functions. The only monkeypatched
seams are the named external boundaries (the LaTeX builder, the Kaggle offload
backend, and the paper-gate's sibling verifiers) — never the code under test.

Mapping (defect → test):
  D1  paper-complete gate consumes the producer's own pdf_path (not a hard-coded
      source/main.pdf the producer never writes) + requires PDF freshness
      → test_paper_complete_gate_consumes_producer_pdf_path
  D4  durable execution FailureClass taxonomy + class-specific re-plan guidance
      → test_failure_class_from_signals
        test_execution_status_round_trips_failure_class
        test_replan_feedback_is_class_specific
  D12 one backend-independent semantic gate; the GPU-offload path rejoins it
      → test_verify_artifact_bundle_rejects_fabrication
        test_offload_complete_rejects_fabricated_bundle
  D2  execution repair reopens tasks via the SSoT feature-dir pointer, not the
      first lexicographic specs/*/tasks.md
      → test_reopen_uses_pointer_feature_dir
  D3  routing ignores a stale/cross-stage convergence kickback instead of
      returning an illegal lifecycle edge
      → test_decide_next_stage_ignores_stale_cross_stage_kickback
"""

from __future__ import annotations

import json
import os
from datetime import UTC, datetime
from pathlib import Path

import pytest
import yaml

from llmxive.agents.lifecycle import is_valid_transition
from llmxive.execution import offload as offload_mod
from llmxive.execution.analysis_runner import (
    AnalysisRunResult,
    RunCommandResult,
    verify_artifact_bundle,
)
from llmxive.execution.failure_class import REPLAN_GUIDANCE, FailureClass
from llmxive.execution.stage import (
    _compute_infra_failures,
    _data_unavailable_failures,
    _poll_offload,
    _reopen_failing_tasks,
)
from llmxive.pipeline import graph
from llmxive.state import execution_status
from llmxive.state import project as project_store
from llmxive.types import Project, Stage


@pytest.fixture(autouse=True)
def _allow_localhost(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("LLMXIVE_ALLOW_LOCALHOST", "1")


def _mk_project_dir(tmp_path: Path, project_id: str) -> Path:
    proj = tmp_path / "projects" / project_id
    proj.mkdir(parents=True, exist_ok=True)
    (tmp_path / "state" / "execution_status").mkdir(parents=True, exist_ok=True)
    return proj


# ---------------------------------------------------------------------------
# D1 — paper-complete gate consumes the producer's returned pdf_path
# ---------------------------------------------------------------------------


def test_paper_complete_gate_consumes_producer_pdf_path(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The gate must accept the producer's OWN ``pdf_path`` (paper/pdf/main.pdf),
    not a hard-coded paper/source/main.pdf the builder never writes. Negatives:
    a missing pdf_path file and a PDF older than its source both reject."""
    pid = "PROJ-575-pdf-gate"
    proj = _mk_project_dir(tmp_path, pid)
    source = proj / "paper" / "source" / "main.tex"
    source.parent.mkdir(parents=True, exist_ok=True)
    source.write_text("\\documentclass{article}\\begin{document}x\\end{document}\n",
                      encoding="utf-8")
    pdf = proj / "paper" / "pdf" / "main.pdf"
    pdf.parent.mkdir(parents=True, exist_ok=True)
    pdf.write_bytes(b"%PDF-1.5 real bytes")

    # Fresh PDF: source older than the produced PDF.
    old = datetime(2026, 1, 1).timestamp()
    new = datetime(2026, 1, 2).timestamp()
    os.utime(source, (old, old))
    os.utime(pdf, (new, new))

    # The producer returns ok + its real pdf_path (paper/pdf/main.pdf).
    def _fake_build(project_id, *, main_tex="main.tex", repo_root=None):
        return {"ok": True, "pdf_path": str(pdf)}

    monkeypatch.setattr("llmxive.agents.latex_build.build_paper", _fake_build)
    # Stub the OTHER preconditions so this test isolates the PDF-path logic.
    monkeypatch.setattr(graph, "_all_paper_tasks_done", lambda pd: True)
    monkeypatch.setattr(
        "llmxive.agents.citation_guard.project_unverified_markers",
        lambda *a, **k: [],
    )
    monkeypatch.setattr(
        "llmxive.agents.reference_validator.has_blocking_citations",
        lambda *a, **k: False,
    )
    monkeypatch.setattr(
        "llmxive.agents.proofreader.proofreader_clean", lambda *a, **k: True
    )

    assert graph._paper_complete_preconditions_met(
        pid, proj, repo_root=tmp_path
    ) is True

    # Negative 1: the producer reports a pdf_path that does not exist on disk.
    pdf.unlink()
    assert graph._paper_complete_preconditions_met(
        pid, proj, repo_root=tmp_path
    ) is False

    # Negative 2: a STALE PDF (older than its source) must not satisfy the gate.
    pdf.write_bytes(b"%PDF-1.5 stale")
    os.utime(source, (new, new))   # source now newer than pdf
    os.utime(pdf, (old, old))
    assert graph._paper_complete_preconditions_met(
        pid, proj, repo_root=tmp_path
    ) is False


# ---------------------------------------------------------------------------
# D4 — durable failure classification + class-specific re-plan guidance
# ---------------------------------------------------------------------------


def test_failure_class_from_signals() -> None:
    """The single taxonomy maps already-computed signals to one durable class,
    with the priority the re-plan must address first. Grounded on the REAL
    signature matchers for the compute/data cases."""
    # compute-env dominates.
    assert FailureClass.from_signals(
        compute_infra=True, data_unavailable=False, fabrication=False,
        hollow=False, has_command_failures=True,
    ) is FailureClass.COMPUTE_ENV
    # data-unreachable next.
    assert FailureClass.from_signals(
        compute_infra=False, data_unavailable=True, fabrication=False,
        hollow=False, has_command_failures=True,
    ) is FailureClass.DATA_UNREACHABLE
    # fabrication / hollow → fabrication.
    assert FailureClass.from_signals(
        compute_infra=False, data_unavailable=False, fabrication=True,
        hollow=False, has_command_failures=False,
    ) is FailureClass.FABRICATION
    assert FailureClass.from_signals(
        compute_infra=False, data_unavailable=False, fabrication=False,
        hollow=True, has_command_failures=False,
    ) is FailureClass.FABRICATION
    # a plain command failure → an ordinary code bug.
    assert FailureClass.from_signals(
        compute_infra=False, data_unavailable=False, fabrication=False,
        hollow=False, has_command_failures=True,
    ) is FailureClass.EXECUTION_BUG
    # nothing recognized → unknown.
    assert FailureClass.from_signals(
        compute_infra=False, data_unavailable=False, fabrication=False,
        hollow=False, has_command_failures=False,
    ) is FailureClass.UNKNOWN

    # Grounding: the real signature matchers produce the booleans above.
    cuda = ["python code/train.py -> rc=1\n    RuntimeError: CUDA out of memory"]
    hf = ["python code/load.py -> rc=1\n    HfUriError: Repository id must be 'namespace/name'"]
    assert _compute_infra_failures(cuda)
    assert not _compute_infra_failures(hf)
    assert _data_unavailable_failures(hf)
    assert not _data_unavailable_failures(cuda)


def test_execution_status_round_trips_failure_class(tmp_path: Path) -> None:
    """A failed record persists the durable class + evidence; a success clears
    both back to None/[]."""
    (tmp_path / "state" / "execution_status").mkdir(parents=True)
    pid = "PROJ-843-fc"
    execution_status.record(
        pid, ok=False, reason="HfUriError: dataset not found",
        artifacts=[], failures=["python code/load.py -> rc=1"],
        failure_class="data_unreachable",
        evidence=["python code/load.py"],
        repo_root=tmp_path,
    )
    rec = execution_status.load(pid, repo_root=tmp_path)
    assert rec is not None
    assert rec["failure_class"] == "data_unreachable"
    assert rec["evidence"] == ["python code/load.py"]

    # Success clears the class + evidence.
    execution_status.record(
        pid, ok=True, reason="ok", artifacts=["data/results.json"],
        failures=[], repo_root=tmp_path,
    )
    rec2 = execution_status.load(pid, repo_root=tmp_path)
    assert rec2 is not None
    assert rec2["failure_class"] is None
    assert rec2["evidence"] == []


def test_replan_feedback_is_class_specific(tmp_path: Path) -> None:
    """The re-plan note branches on the durable class: a compute-env failure gets
    GPU/offload guidance, a data-unreachable failure gets verified-source guidance,
    and the two notes are NOT the same generic 'CPU-tractable' text."""
    proj_c = _mk_project_dir(tmp_path, "PROJ-262-compute")
    proj_d = _mk_project_dir(tmp_path, "PROJ-261-data")

    compute_text = graph._write_execution_replan_feedback(
        proj_c,
        {"failure_class": "compute_env", "reason": "CUDA out of memory",
         "failures": ["python code/train.py -> rc=1"], "artifacts": [],
         "model_tier": 1},
    )
    data_text = graph._write_execution_replan_feedback(
        proj_d,
        {"failure_class": "data_unreachable",
         "reason": "HfUriError: dataset unreachable",
         "failures": ["python code/load.py -> rc=1"], "artifacts": []},
    )

    # Each carries its own class-specific guidance verbatim.
    assert REPLAN_GUIDANCE[FailureClass.COMPUTE_ENV] in compute_text
    assert REPLAN_GUIDANCE[FailureClass.DATA_UNREACHABLE] in data_text
    # The diagnosed class is named in each.
    assert "compute_env" in compute_text
    assert "data_unreachable" in data_text
    # Compute guidance is GPU/offload-shaped; the data note must NOT reuse it.
    assert "GPU" in compute_text and "offload" in compute_text
    assert REPLAN_GUIDANCE[FailureClass.COMPUTE_ENV] not in data_text
    # Distinct, class-appropriate strings (not one generic template).
    assert compute_text != data_text


# ---------------------------------------------------------------------------
# D12 — one backend-independent semantic gate
# ---------------------------------------------------------------------------


def _write_fabricated_bundle(proj: Path) -> None:
    """A blatantly fabricated bundle: an RNG metric + a self-declared 'simulated
    metrics' result (mirrors recon-F _probe_offload.py)."""
    code = proj / "code"
    code.mkdir(parents=True, exist_ok=True)
    (code / "run.py").write_text(
        "import random\n"
        "acc = random.random()  # fabricated: not a real measurement\n"
        "print('simulated metrics', acc)\n",
        encoding="utf-8",
    )
    data = proj / "data"
    data.mkdir(parents=True, exist_ok=True)
    (data / "results.json").write_text(
        json.dumps({"accuracy": 0.99, "note": "simulated metrics"}),
        encoding="utf-8",
    )


def _write_clean_bundle(proj: Path) -> None:
    """A real-numbers bundle: measured arithmetic, no fabrication signals."""
    code = proj / "code"
    code.mkdir(parents=True, exist_ok=True)
    (code / "analysis.py").write_text(
        "import json\n"
        "values = [1.0, 2.0, 3.0, 4.0]\n"
        "mean = sum(values) / len(values)\n"
        "json.dump({'mean': mean, 'n': len(values)},\n"
        "          open('data/results.json', 'w'))\n",
        encoding="utf-8",
    )
    data = proj / "data"
    data.mkdir(parents=True, exist_ok=True)
    (data / "results.json").write_text(
        json.dumps({"mean": 2.5, "n": 4}), encoding="utf-8"
    )


def test_verify_artifact_bundle_rejects_fabrication(tmp_path: Path) -> None:
    """The shared semantic gate rejects a fabricated bundle (fabrication reason)
    and accepts a real-numbers bundle."""
    fab = _mk_project_dir(tmp_path, "PROJ-604-fab")
    _write_fabricated_bundle(fab)
    gate = verify_artifact_bundle(fab, ["data/results.json"])
    assert gate.ok is False
    assert "fabricat" in gate.reason().lower()

    clean = _mk_project_dir(tmp_path, "PROJ-604-clean")
    _write_clean_bundle(clean)
    good = verify_artifact_bundle(clean, ["data/results.json"])
    assert good.ok is True, good.reason()


def test_offload_complete_rejects_fabricated_bundle(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A completed Kaggle offload whose retrieved bundle is fabricated must NOT
    advance to research_complete: it rejoins the SAME semantic gate, is rejected,
    and the project is not recorded ok (mirrors recon-F _probe_offload.py).

    Note: the local-fallback ``execution_status.record`` writes a fresh record
    that does not carry the offload sub-record, so 'marked failed' is observed as
    'no longer pending' (+ not-ok) rather than a literal status=='failed' string.
    """
    pid = "PROJ-777-offload"
    proj = _mk_project_dir(tmp_path, pid)
    _write_fabricated_bundle(proj)

    # An offload kernel is in flight.
    execution_status.record_offload(
        pid, status="running", kernel_ref="kref/abc", repo_root=tmp_path
    )

    # Stub the Kaggle boundary only.
    monkeypatch.setattr(offload_mod, "poll", lambda ref: "complete")
    monkeypatch.setattr(
        offload_mod, "retrieve", lambda ref, pd: ["data/results.json"]
    )
    monkeypatch.setattr(offload_mod, "is_available", lambda: False)
    monkeypatch.setattr(offload_mod, "dispatch", lambda pd, repo: None)

    advanced = _poll_offload(proj, tmp_path)

    assert advanced is False
    assert execution_status.is_ok(pid, repo_root=tmp_path) is False
    # Not stuck polling and not advanced: the fabricated bundle was rejected.
    assert execution_status.is_offload_pending(pid, repo_root=tmp_path) is False


# ---------------------------------------------------------------------------
# D2 — execution repair reopens tasks via the SSoT feature-dir pointer
# ---------------------------------------------------------------------------


def test_reopen_uses_pointer_feature_dir(tmp_path: Path) -> None:
    """A multi-cycle project (specs/001-old + specs/010-current) must reopen the
    failing task in the pointer-canonical CURRENT dir, leaving the stale first-
    glob dir untouched (mirror image of the recon-A repro)."""
    pid = "PROJ-002-pointer"
    proj = _mk_project_dir(tmp_path, pid)
    (tmp_path / "state" / "projects").mkdir(parents=True, exist_ok=True)

    task_line = "- [x] T001 run code/analysis.py to produce results\n"
    old_dir = proj / "specs" / "001-old"
    cur_dir = proj / "specs" / "010-current"
    old_dir.mkdir(parents=True)
    cur_dir.mkdir(parents=True)
    (old_dir / "tasks.md").write_text(task_line, encoding="utf-8")
    (cur_dir / "tasks.md").write_text(task_line, encoding="utf-8")

    # Canonical state: the research pointer names 010-current (NOT the first glob).
    now = datetime.now(UTC)
    project = Project(
        id=pid,
        title="pointer regression",
        field="test",
        current_stage=Stage.IN_PROGRESS,
        created_at=now,
        updated_at=now,
        speckit_research_dir=f"projects/{pid}/specs/010-current",
    )
    project_store.save(project, repo_root=tmp_path)

    res = AnalysisRunResult(
        ok=False,
        commands=[
            RunCommandResult(
                "python code/analysis.py", False, 1, 0.5, False,
                "NameError: name 'sys' is not defined",
            ),
        ],
    )

    reopened = _reopen_failing_tasks(proj, res)

    cur_after = (cur_dir / "tasks.md").read_text(encoding="utf-8")
    old_after = (old_dir / "tasks.md").read_text(encoding="utf-8")
    assert reopened >= 1
    assert "- [ ] T001" in cur_after, "the pointer-canonical dir was not reopened"
    assert "- [x] T001" in old_after, "the STALE first-glob dir must stay untouched"


# ---------------------------------------------------------------------------
# D3 — routing ignores a stale/cross-stage kickback, never an illegal edge
# ---------------------------------------------------------------------------


def test_decide_next_stage_ignores_stale_cross_stage_kickback(
    tmp_path: Path
) -> None:
    """A leftover convergence sentinel naming to_stage=paper_planned, consumed at
    PAPER_ANALYZED (whose only legal edge is PAPER_IN_PROGRESS), must be IGNORED —
    _decide_next_stage returns the LEGAL edge, never paper_planned, never raises.
    Also pins the edge-registry invariant for the recorded advance-error pairs."""
    # The invariant that made the recorded advance_errors illegal in the first
    # place: none of these cross-stage sentinel edges are valid transitions.
    illegal_pairs = [
        (Stage.PAPER_ANALYZED, Stage.PAPER_PLANNED),  # PROJ-575, 601
        (Stage.IN_PROGRESS, Stage.CLARIFIED),         # PROJ-577, 606
        (Stage.IN_PROGRESS, Stage.SPECIFIED),         # PROJ-644
    ]
    for src, dst in illegal_pairs:
        assert is_valid_transition(src, dst) is False, f"{src} -> {dst}"

    pid = "PROJ-575-stale-kb"
    proj = _mk_project_dir(tmp_path, pid)
    # A paper project at PAPER_ANALYZED (schema requires the paper pointer set).
    now = datetime.now(UTC)
    project = Project(
        id=pid,
        title="stale kickback regression",
        field="test",
        current_stage=Stage.PAPER_ANALYZED,
        created_at=now,
        updated_at=now,
        speckit_paper_dir=f"projects/{pid}/paper/specs/001-paper",
    )

    # Seed a STALE paper-side kickback sentinel targeting paper_planned.
    mem = proj / "paper" / ".specify" / "memory"
    mem.mkdir(parents=True, exist_ok=True)
    (mem / "convergence_kickback.yaml").write_text(
        yaml.safe_dump({
            "to_stage": "paper_planned",
            "stage": "paper_tasks",
            "reason": "paper tasks panel did not converge",
            "worst_severity": "requirement",
            "unresolved_concerns": [],
        }),
        encoding="utf-8",
    )

    result = graph._decide_next_stage(project, proj, repo_root=tmp_path)

    assert result != Stage.PAPER_PLANNED
    assert result == Stage.PAPER_IN_PROGRESS
    assert is_valid_transition(project.current_stage, result) is True
