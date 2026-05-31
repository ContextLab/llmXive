"""Regression test for the _EXTERNAL_PROMPT_ROOTS map (paper_review +
research_review stages reusing the pre-existing 12-panel + 8-panel
prompts at the agents/prompts root)."""
from pathlib import Path

import pytest

from llmxive.convergence.llm_reviewer import _prompt_path_for

REPO_ROOT = Path(__file__).resolve().parents[2]


def test_paper_review_stage_resolves_to_existing_paper_reviewer_prompts():
    for lens in ("claim_accuracy", "scientific_evidence", "writing_quality",
                 "figure_critic"):
        p = _prompt_path_for(stage="paper_review", lens=lens,
                             repo_root=REPO_ROOT)
        assert p.exists(), f"paper_review/{lens} → {p}"
        assert p.parent.name == "prompts"


def test_research_review_stage_resolves_to_existing_research_reviewer_prompts():
    # Pick one we know exists (others can be authored later).
    p = _prompt_path_for(stage="research_review", lens="idea_quality",
                         repo_root=REPO_ROOT)
    assert p.exists(), f"research_review/idea_quality → {p}"


def test_unknown_stage_raises_with_helpful_error():
    with pytest.raises(ValueError, match="unknown stage 'not_a_stage'"):
        _prompt_path_for(stage="not_a_stage", lens="x", repo_root=REPO_ROOT)


def test_error_message_lists_paper_review_and_research_review_in_known():
    with pytest.raises(ValueError) as ei:
        _prompt_path_for(stage="bogus", lens="x", repo_root=REPO_ROOT)
    msg = str(ei.value)
    assert "paper_review" in msg
    assert "research_review" in msg
