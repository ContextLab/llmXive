"""Autonomous exhaustion handling for the execution fix-loop.

A project's analysis-execution fix-loop must NEVER park at
``human_input_needed`` (the sole sanctioned human gate is the publication DOI
sign-off). At the per-tier fix-round cap the loop:

  1. MODEL ESCALATION — bumps to the next usable model tier and resets
     ``fix_rounds`` (retrying the full cap with a different model), staying
     IN_PROGRESS; and
  2. once EVERY tier is exhausted, RE-PLANS with a DETERMINISTIC report (no LLM
     call) routed to ``planned``.

These tests drive the REAL ``execution_status`` store and the REAL
``graph._decide_next_stage`` routing over a synthetic on-disk repo — no mocks.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

import pytest

from llmxive.pipeline import graph
from llmxive.state import execution_status as es
from llmxive.state import project as project_store
from llmxive.types import Project, Stage


@pytest.fixture(autouse=True)
def _free_first_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """Default FREE-FIRST: no paid opt-in, no configured paid tiers."""
    monkeypatch.delenv("LLMXIVE_PAID_OPT_IN", raising=False)
    monkeypatch.delenv("LLMXIVE_EXECUTION_PAID_TIERS", raising=False)


def _force_fix_rounds_at_cap(repo: Path, pid: str) -> None:
    """Pin fix_rounds to the cap on the recorded status (the loop reached it)."""
    p = repo / "state" / "execution_status" / f"{pid}.json"
    rec = json.loads(p.read_text())
    rec["fix_rounds"] = es.MAX_EXECUTION_FIX_ROUNDS
    p.write_text(json.dumps(rec))


def _project_in_progress(repo: Path, pid: str) -> tuple[Project, Path]:
    pdir = repo / "projects" / pid
    feat = pdir / "specs" / "001-research"
    feat.mkdir(parents=True)
    (feat / "tasks.md").write_text("- [X] T001 done\n", encoding="utf-8")
    now = datetime.now(UTC)
    proj = Project(
        id=pid,
        title="exhaustion",
        field="test",
        current_stage=Stage.IN_PROGRESS,
        created_at=now,
        updated_at=now,
        speckit_research_dir=f"projects/{pid}/specs/001-research",
    )
    project_store.save(proj, repo_root=repo)
    return proj, pdir


# --- execution_status tier helpers -----------------------------------------


def test_model_tier_defaults_to_zero_and_record_preserves_it(tmp_path: Path) -> None:
    (tmp_path / "state" / "execution_status").mkdir(parents=True)
    pid = "PROJ-010-tier"
    es.record(pid, ok=False, reason="boom", artifacts=[], failures=["x"],
              repo_root=tmp_path)
    assert es.model_tier(pid, repo_root=tmp_path) == 0
    # Bump the tier, then a subsequent record() must NOT clobber it.
    new_tier = es.bump_model_tier(pid, repo_root=tmp_path)
    assert new_tier == 1
    assert es.fix_rounds(pid, repo_root=tmp_path) == 0  # reset on bump
    es.record(pid, ok=False, reason="boom2", artifacts=[], failures=["y"],
              repo_root=tmp_path)
    assert es.model_tier(pid, repo_root=tmp_path) == 1  # preserved
    assert es.fix_rounds(pid, repo_root=tmp_path) == 1  # bumped from 0


def test_ladder_skips_paid_tiers_when_opt_in_off(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    (tmp_path / "state" / "execution_status").mkdir(parents=True)
    monkeypatch.setenv(
        "LLMXIVE_EXECUTION_PAID_TIERS", "anthropic.claude-haiku,anthropic.claude-sonnet"
    )
    # Ladder LISTS paid tiers (stable indices) but they're unusable opt-in off.
    assert es.model_tier_ladder() == (
        "", "openai.gpt-oss-120b", "anthropic.claude-haiku", "anthropic.claude-sonnet"
    )
    assert es.next_usable_tier(0) == 1  # free second opinion
    assert es.next_usable_tier(1) is None  # paid tiers skipped (opt-in off)
    pid = "PROJ-011-paid"
    es.record(pid, ok=False, reason="boom", artifacts=[], failures=["x"],
              repo_root=tmp_path)
    es.bump_model_tier(pid, repo_root=tmp_path)  # 0 -> 1 (free)
    with pytest.raises(ValueError):
        es.bump_model_tier(pid, repo_root=tmp_path)  # 1 -> none (paid skipped)


def test_fabrication_escalation_never_climbs_to_a_paid_tier(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A stronger PAID model cannot make an unavailable dataset available: the
    deterministic fabrication guard fires on the code's OUTPUT regardless of which
    model wrote it. PROJ-284 climbed to a paid Claude tier (11 rounds deep) still
    fabricating synthetic brain-imaging data — pure waste. Fabrication escalation
    must cap at the last FREE tier; then re-plan (bounded), never pay to re-fabricate.
    """
    (tmp_path / "state" / "execution_status").mkdir(parents=True)
    monkeypatch.setenv("LLMXIVE_EXECUTION_PAID_TIERS", "anthropic.claude-haiku")
    monkeypatch.setattr(es, "paid_tier_usable", lambda m: True)  # opt-in ON, has budget
    # A CODE BUG can use the paid tier; fabrication cannot.
    assert es.next_usable_tier(1) == 2                       # paid reachable in general
    assert es.next_usable_tier(1, free_only=True) is None    # ...but not free_only
    assert es.next_usable_tier(0, free_only=True) == 1       # free second opinion is fine

    pid = "PROJ-284-fab"
    es.record(pid, ok=False, reason="fabricated results", artifacts=[], failures=["x"],
              repo_root=tmp_path)
    es.bump_model_tier(pid, repo_root=tmp_path, free_only=True)   # 0 -> 1 (free)
    with pytest.raises(ValueError):
        es.bump_model_tier(pid, repo_root=tmp_path, free_only=True)  # 1 -> none (no paid)


def test_execution_model_override_resolves_tier(tmp_path: Path) -> None:
    (tmp_path / "state" / "execution_status").mkdir(parents=True)
    pid = "PROJ-012-override"
    es.record(pid, ok=False, reason="boom", artifacts=[], failures=["x"],
              repo_root=tmp_path)
    # Tier 0 -> the registered default (no override).
    assert es.execution_model_override(
        pid, default_model="REGISTERED-DEFAULT", repo_root=tmp_path
    ) == "REGISTERED-DEFAULT"
    es.bump_model_tier(pid, repo_root=tmp_path)
    # Tier 1 -> the free second-opinion model id.
    assert es.execution_model_override(
        pid, default_model="REGISTERED-DEFAULT", repo_root=tmp_path
    ) == "openai.gpt-oss-120b"


# --- graph routing ----------------------------------------------------------


def test_at_cap_tier0_escalates_to_tier1_stays_in_progress(tmp_path: Path) -> None:
    repo = tmp_path
    pid = "PROJ-020-escalate"
    proj, pdir = _project_in_progress(repo, pid)
    es.record(pid, ok=False, reason="failed", artifacts=["data/r.csv"],
              failures=["code/a.py -> rc=1\n  ValueError"], repo_root=repo)
    _force_fix_rounds_at_cap(repo, pid)

    nxt = graph._decide_next_stage(proj, pdir, repo_root=repo)

    assert nxt == Stage.IN_PROGRESS
    assert nxt != Stage.HUMAN_INPUT_NEEDED
    assert es.model_tier(pid, repo_root=repo) == 1
    assert es.fix_rounds(pid, repo_root=repo) == 0  # reset for a fresh cap


def test_at_cap_last_tier_replans_with_deterministic_report(tmp_path: Path) -> None:
    repo = tmp_path
    pid = "PROJ-021-replan"
    proj, pdir = _project_in_progress(repo, pid)
    es.record(pid, ok=False, reason="still failing",
              artifacts=["data/results.csv", "figures/plot.png"],
              failures=["code/train.py -> rc=1\n  KeyError: 'col'"], repo_root=repo)
    # Put the project at the LAST available tier (tier 1) at the cap.
    es.bump_model_tier(pid, repo_root=repo)
    assert es.model_tier(pid, repo_root=repo) == 1
    es.record(pid, ok=False, reason="still failing",
              artifacts=["data/results.csv", "figures/plot.png"],
              failures=["code/train.py -> rc=1\n  KeyError: 'col'"], repo_root=repo)
    _force_fix_rounds_at_cap(repo, pid)

    nxt = graph._decide_next_stage(proj, pdir, repo_root=repo)

    assert nxt == Stage.PLANNED
    assert nxt != Stage.HUMAN_INPUT_NEEDED
    assert graph.is_valid_transition(Stage.IN_PROGRESS, Stage.PLANNED)
    # fix_rounds AND model_tier both reset for a clean re-planned project.
    assert es.fix_rounds(pid, repo_root=repo) == 0
    assert es.model_tier(pid, repo_root=repo) == 0
    # Deterministic re-plan report written to the Planner's kickback-ingestion
    # file with: a produced artifact, a failing command, and the adjust note.
    report = (pdir / ".specify" / "memory" / "kickback_feedback.md").read_text()
    assert "data/results.csv" in report  # what worked
    assert "code/train.py" in report  # what failed
    assert "needs adjustment given the errors above" in report  # adjust note
    assert "re-plan with a design that avoids them" in report


def test_replan_report_is_deterministic_from_a_status_dict(tmp_path: Path) -> None:
    """Build the report from a realistic execution_status dict and assert its
    contents deterministically (no LLM call involved)."""
    pdir = tmp_path / "projects" / "PROJ-022-report"
    pdir.mkdir(parents=True)
    rec = {
        "project_id": "PROJ-022-report",
        "ok": False,
        "reason": "analysis run failed: 2 of 3 commands errored",
        "artifacts": ["data/clean.csv", "figures/hist.png"],
        "failures": [
            "code/model.py -> rc=1\n  RuntimeError: no GPU",
            "code/eval.py -> rc=2\n  FileNotFoundError: data/preds.csv",
        ],
        "fix_rounds": es.MAX_EXECUTION_FIX_ROUNDS,
        "model_tier": 1,
    }
    text = graph._write_execution_replan_feedback(pdir, rec)
    # (a) what worked — every produced artifact with its path
    assert "## What worked" in text
    assert "`data/clean.csv`" in text
    assert "`figures/hist.png`" in text
    # (b) what failed — each failing command + error tail
    assert "## What failed" in text
    assert "code/model.py -> rc=1" in text
    assert "RuntimeError: no GPU" in text
    assert "code/eval.py -> rc=2" in text
    # (c) the explicit adjust-the-approach note
    assert "needs adjustment given the errors above" in text
    # Persisted to the SAME doc-stage kickback-ingestion file (SSoT).
    on_disk = (pdir / ".specify" / "memory" / "kickback_feedback.md").read_text()
    assert on_disk == text
    # Determinism: same input -> identical output.
    assert graph._write_execution_replan_feedback(pdir, rec) == text


def test_below_cap_stays_in_progress_no_tier_change(tmp_path: Path) -> None:
    repo = tmp_path
    pid = "PROJ-023-belowcap"
    proj, pdir = _project_in_progress(repo, pid)
    es.record(pid, ok=False, reason="failed once", artifacts=[],
              failures=["code/a.py -> rc=1"], repo_root=repo)
    assert es.fix_rounds(pid, repo_root=repo) == 1  # well below the cap
    nxt = graph._decide_next_stage(proj, pdir, repo_root=repo)
    assert nxt == Stage.IN_PROGRESS
    assert es.model_tier(pid, repo_root=repo) == 0  # unchanged below the cap


def test_human_input_needed_is_auto_recovered_to_planned(tmp_path: Path) -> None:
    """A project stranded at human_input_needed (a pre-fix straggler) is
    recovered into the pipeline by run_one_step: routed to PLANNED, fix-round +
    model-tier counters reset, escalation reason cleared, and a deterministic
    re-plan report dropped for the planner — NO human action required."""
    repo = tmp_path
    pid = "PROJ-999-stranded"
    pdir = repo / "projects" / pid
    (pdir / "specs" / "001-research").mkdir(parents=True)
    (repo / "state" / "execution_status").mkdir(parents=True)
    es.record(pid, ok=False, reason="analysis failed",
              artifacts=["data/x.parquet"],
              failures=["python code/a.py -> rc=1"], repo_root=repo)
    _force_fix_rounds_at_cap(repo, pid)
    now = datetime.now(UTC)
    proj = Project(
        id=pid, title="stranded", field="test",
        current_stage=Stage.HUMAN_INPUT_NEEDED,
        human_escalation_reason="analysis execution failed after the fix-round cap",
        created_at=now, updated_at=now,
        speckit_research_dir=f"projects/{pid}/specs/001-research",
    )
    project_store.save(proj, repo_root=repo)

    out = graph.run_one_step(proj, repo_root=repo)

    assert out.current_stage == Stage.PLANNED  # recovered, not parked
    assert out.human_escalation_reason is None
    assert es.fix_rounds(pid, repo_root=repo) == 0  # fresh attempt
    assert es.model_tier(pid, repo_root=repo) == 0
    # deterministic re-plan report written for the planner to ingest
    mem = pdir / ".specify" / "memory"
    assert any(mem.glob("*feedback*")), "no re-plan report written"
