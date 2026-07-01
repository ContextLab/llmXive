"""Audit regression guard (user-requested deep audit): an anti-fabrication
guardrail must be present at EVERY step of the pipeline that can produce or must
detect fabricated results. Fabrication (synthetic/fake INPUT data, hard-coded
metrics, random.*/simulated values standing in for a real measurement) is the
DOMINANT paper-init blocker — the deterministic fabrication guard backstops the
execution gate + every convergence stage, and these prompt guardrails prevent it
at the SOURCE and flag it in review. If a future prompt edit drops one, this fails.
"""

from __future__ import annotations

from pathlib import Path

_PROMPTS = Path(__file__).resolve().parents[2] / "agents" / "prompts"


def _text(name: str) -> str:
    return (_PROMPTS / name).read_text(encoding="utf-8").lower()


# --- generator stages: must forbid producing fabricated data/results ---------


def test_tasker_forbids_fabrication_tasks() -> None:
    t = _text("tasker.md")
    assert "never task fabrication" in t
    assert "fabrication guard" in t
    assert "real dataset" in t or "real data" in t


def test_paper_statistics_forbids_fabrication() -> None:
    t = _text("paper_statistics.md")
    assert "never fabricate a statistic" in t
    assert "data_source_path" in t


def test_research_implementer_prompt_forbids_fabrication() -> None:
    t = _text("implementer_research.md")
    assert "real data only" in t or "real source" in t
    assert "fabricat" in t or "fake" in t


def test_planner_forbids_fabricated_dataset_sources() -> None:
    t = _text("planner.md")
    assert "fabricat" in t  # "do NOT fabricate a URL" / "rather than fabricating one"
    assert "verified" in t and "dataset" in t


# --- detector stages: must flag fabrication as a blocking defect --------------


def test_research_data_quality_reviewer_flags_fabrication() -> None:
    t = _text("research_reviewer_data_quality_research.md")
    assert "fabrication is a blocking scientific defect" in t
    assert "synthetic or fake input data" in t


def test_paper_data_quality_reviewer_flags_fabrication() -> None:
    t = _text("paper_reviewer_data_quality_paper.md")
    assert "fabrication is in your lens and is blocking" in t
