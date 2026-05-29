"""Tests for action_items↔concerns schema back-compat in LLMReviewer.

The spec-015 SSoT schema uses ``concerns:`` for structured panel
findings. The legacy 12-panel + 8-panel prompts
(``paper_reviewer_*.md`` / ``research_reviewer_*.md``) were authored
pre-spec-015 against the v1.1.0 reviewer contract that uses
``action_items:`` instead.

The 12-panel is reused as the paper_review R1 panelists (FR-028 +
T042); its prompts emit ``action_items``. Without back-compat
acceptance, every paper_review panelist's output would be parsed as
"no concerns" and the engine would falsely report convergence.

This regression test locks in the parser's behavior: both shapes are
accepted; when both are present, ``concerns`` wins (the LLM
explicitly produced the SSoT shape).
"""

from __future__ import annotations

import pytest

from llmxive.convergence.llm_reviewer import _parse_response


def test_action_items_key_is_parsed_as_concerns():
    """Calibration runs 26613660779 + 26601505137 (paper_implement)
    surfaced 0 concerns despite the panel evaluating the fabricated
    citation — root cause: the panel emitted ``action_items:``
    (v1.1.0 contract) but the parser only read ``concerns:``."""
    resp = (
        "---\n"
        "verdict: minor_revision\n"
        "score: 0.0\n"
        "action_items:\n"
        "  - text: The citation [FabricatedAuthor2024] does not exist in any database.\n"
        "    severity: science\n"
        "  - text: Section 3.2 references an undefined symbol epsilon-prime.\n"
        "    severity: writing\n"
        "---\n"
        "Prose body of the review.\n"
    )
    verdict, concerns = _parse_response(
        resp, lens="claim_accuracy", stage="paper_review",
        default_artifact="paper/source/main.tex",
    )
    assert verdict == "minor_revision"
    assert len(concerns) == 2
    assert "FabricatedAuthor2024" in concerns[0].text
    assert concerns[0].severity.value == "science"
    assert concerns[1].severity.value == "writing"


def test_concerns_key_still_works_unchanged():
    """Regression: the new SSoT schema continues to parse correctly."""
    resp = (
        "---\n"
        "verdict: minor_revision\n"
        "concerns:\n"
        "  - text: An issue\n"
        "    severity: requirement\n"
        "---\n"
        "Body\n"
    )
    verdict, concerns = _parse_response(
        resp, lens="x", stage="clarified", default_artifact="x.md",
    )
    assert verdict == "minor_revision"
    assert len(concerns) == 1
    assert concerns[0].severity.value == "requirement"


def test_concerns_wins_when_both_keys_present():
    """When the LLM emits both shapes (e.g. confused by prompt that
    says one thing but the system prompt says another), ``concerns``
    wins because that's the LLM explicitly producing the SSoT shape."""
    resp = (
        "---\n"
        "verdict: minor_revision\n"
        "concerns:\n"
        "  - text: SSoT concern\n"
        "    severity: writing\n"
        "action_items:\n"
        "  - text: Legacy item that should be ignored\n"
        "    severity: science\n"
        "---\n"
        "Body\n"
    )
    _, concerns = _parse_response(
        resp, lens="x", stage="paper_review", default_artifact="x",
    )
    assert len(concerns) == 1
    assert "SSoT concern" in concerns[0].text


def test_empty_concerns_falls_through_to_action_items():
    """If ``concerns:`` is explicitly empty (not just missing), fall
    through to ``action_items``. This handles the common case where the
    LLM produces both but leaves the SSoT key blank."""
    resp = (
        "---\n"
        "verdict: minor_revision\n"
        "concerns: []\n"
        "action_items:\n"
        "  - text: This should still be picked up\n"
        "    severity: writing\n"
        "---\n"
        "Body\n"
    )
    _, concerns = _parse_response(
        resp, lens="x", stage="paper_review", default_artifact="x",
    )
    assert len(concerns) == 1
    assert "should still be picked up" in concerns[0].text


def test_both_missing_yields_zero_concerns_no_crash():
    """Neither key present = clean review (legit when the LLM
    accepts). Parser MUST return zero concerns + the verdict, NOT
    crash on missing both keys."""
    resp = (
        "---\n"
        "verdict: accept\n"
        "---\n"
        "Body\n"
    )
    verdict, concerns = _parse_response(
        resp, lens="x", stage="paper_review", default_artifact="x",
    )
    assert verdict == "accept"
    assert concerns == []


def test_action_items_must_be_a_list():
    """A misshapen ``action_items`` value (string instead of list) is
    surfaced clearly so the engine treats it as a non-convergence."""
    resp = (
        "---\n"
        "verdict: minor_revision\n"
        "action_items: this should be a list, not a string\n"
        "---\n"
    )
    with pytest.raises(RuntimeError, match="must be a list"):
        _parse_response(
            resp, lens="x", stage="paper_review", default_artifact="x",
        )
