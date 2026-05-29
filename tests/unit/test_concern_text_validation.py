"""Regression tests for Concern.text + ConcernResponse non-empty
invariants (spec 015, calibration-bug fix).

Calibration run ``paper_implement__20260529T102205Z`` emitted concerns
like::

    figure_critic [writing] (unstated) — <EMPTY>

The reviewer-parser was silently coercing missing/empty ``text`` to
``""`` and ``Concern.text: str`` had no length constraint, so the bug
got persisted into the convergence record. These tests pin the fix:

1. ``Concern.text`` is now ``Field(min_length=1)`` with a whitespace-
   stripping validator. Empty + whitespace-only + non-string ``text``
   raises ``ValidationError`` at model construction.

2. ``ConcernResponse.response`` and ``ConcernResponse.what_changed``
   carry the same invariant (an empty reviser response is the same
   class of bug — a claim of action with no description).

3. ``LLMReviewer._parse_response`` rejects empty/missing ``text:``
   BEFORE constructing the ``Concern``, raising ``RuntimeError`` (the
   engine-recognised non-convergence signal) rather than a pydantic
   ``ValidationError``.

NO mocks — every test exercises the real pydantic models and the real
YAML-frontmatter parser.
"""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from llmxive.convergence.llm_reviewer import _parse_response
from llmxive.convergence.types import Concern, ConcernResponse, Severity

# --- Concern.text validator -----------------------------------------------


def test_concern_text_rejects_empty_string():
    """Empty string at construction → ValidationError (min_length=1)."""
    with pytest.raises(ValidationError):
        Concern(
            id="C001",
            reviewer="figure_critic",
            severity=Severity.WRITING,
            artifact="paper.tex",
            text="",
        )


def test_concern_text_rejects_whitespace_only():
    """Whitespace-only text → ValidationError. ``min_length=1`` alone
    accepts ``" "`` (length 1), so the whitespace-stripping validator
    is needed to make this fail too."""
    for blank in (" ", "\t", "\n", "   \n  \t  \n"):
        with pytest.raises(ValidationError):
            Concern(
                id="C001",
                reviewer="figure_critic",
                severity=Severity.WRITING,
                artifact="paper.tex",
                text=blank,
            )


def test_concern_text_rejects_non_string_types():
    """``text=None`` / ``text=int`` / ``text=list`` → ValidationError."""
    for bogus in (None, 0, 42, [], ["a list"], {"a": "dict"}):
        with pytest.raises(ValidationError):
            Concern(
                id="C001",
                reviewer="figure_critic",
                severity=Severity.WRITING,
                artifact="paper.tex",
                text=bogus,  # type: ignore[arg-type]
            )


def test_concern_text_strips_surrounding_whitespace():
    """A real concern with extra whitespace is accepted but the value
    is stored stripped — keeps the persisted records clean."""
    c = Concern(
        id="C001",
        reviewer="figure_critic",
        severity=Severity.WRITING,
        artifact="paper.tex",
        text="  needs more detail in §3  \n",
    )
    assert c.text == "needs more detail in §3"


def test_concern_text_single_char_is_allowed():
    """``min_length=1`` accepts a single non-whitespace char; existing
    fixtures use ``text='x'`` as a short placeholder + must keep working."""
    c = Concern(
        id="C001",
        reviewer="r",
        severity=Severity.WRITING,
        artifact="a.md",
        text="x",
    )
    assert c.text == "x"


# --- ConcernResponse validators -------------------------------------------


def test_concern_response_rejects_empty_response():
    with pytest.raises(ValidationError):
        ConcernResponse(concern_id="C001", response="", what_changed="ok")


def test_concern_response_rejects_empty_what_changed():
    with pytest.raises(ValidationError):
        ConcernResponse(concern_id="C001", response="ok", what_changed="")


def test_concern_response_rejects_whitespace_only_response():
    with pytest.raises(ValidationError):
        ConcernResponse(
            concern_id="C001", response="   \n  ", what_changed="ok"
        )


def test_concern_response_rejects_whitespace_only_what_changed():
    with pytest.raises(ValidationError):
        ConcernResponse(
            concern_id="C001", response="ok", what_changed="\t\t"
        )


def test_concern_response_accepts_marker_placeholders():
    """The existing revisers substitute ``<missing>`` / ``<empty>`` when
    the LLM omits a field. These markers MUST still be accepted — they
    are non-empty + meaningful signals to the engine."""
    cr1 = ConcernResponse(
        concern_id="C001", response="<missing>", what_changed="<empty>"
    )
    assert cr1.response == "<missing>"
    assert cr1.what_changed == "<empty>"


# --- Parser-level rejection (LLMReviewer._parse_response) -----------------


def _frontmatter(yaml_body: str) -> str:
    """Wrap a YAML body in the ``--- ... ---`` frontmatter the parser
    expects, with a one-line prose body."""
    return f"---\n{yaml_body}\n---\nprose body\n"


def test_parser_rejects_empty_text_concern():
    """Empty ``text:`` in YAML frontmatter → RuntimeError BEFORE Concern
    construction, with a helpful message naming the lens + concern index
    + severity."""
    body = _frontmatter(
        "verdict: minor_revision\n"
        "concerns:\n"
        "  - severity: writing\n"
        "    location: §3\n"
        '    text: ""\n'
    )
    with pytest.raises(RuntimeError, match="empty/missing text"):
        _parse_response(
            body, lens="figure_critic", stage="paper_review",
            default_artifact="paper.tex",
        )


def test_parser_rejects_whitespace_only_text_concern():
    body = _frontmatter(
        "verdict: minor_revision\n"
        "concerns:\n"
        "  - severity: science\n"
        '    text: "   \\n   "\n'
    )
    with pytest.raises(RuntimeError, match="empty/missing text"):
        _parse_response(
            body, lens="statistical_analysis", stage="paper_review",
            default_artifact="paper.tex",
        )


def test_parser_rejects_missing_text_key():
    """Concern dict with NO ``text:`` key at all → RuntimeError."""
    body = _frontmatter(
        "verdict: minor_revision\n"
        "concerns:\n"
        "  - severity: writing\n"
        "    location: §3\n"
    )
    with pytest.raises(RuntimeError, match="empty/missing text"):
        _parse_response(
            body, lens="figure_critic", stage="paper_review",
            default_artifact="paper.tex",
        )


def test_parser_accepts_valid_text_concern():
    """Sanity: a well-formed concern still parses cleanly."""
    body = _frontmatter(
        "verdict: minor_revision\n"
        "concerns:\n"
        "  - severity: writing\n"
        "    location: §3\n"
        '    text: "Methods section needs more detail."\n'
    )
    verdict, concerns = _parse_response(
        body, lens="figure_critic", stage="paper_review",
        default_artifact="paper.tex",
    )
    assert verdict == "minor_revision"
    assert len(concerns) == 1
    assert concerns[0].text == "Methods section needs more detail."
    assert concerns[0].severity is Severity.WRITING
    assert concerns[0].location == "§3"


def test_parser_strips_text_whitespace_before_storing():
    """Parser passes the stripped value to Concern (post-validator)."""
    body = _frontmatter(
        "verdict: minor_revision\n"
        "concerns:\n"
        "  - severity: writing\n"
        '    text: "   needs more detail  "\n'
    )
    _, concerns = _parse_response(
        body, lens="figure_critic", stage="paper_review",
        default_artifact="paper.tex",
    )
    assert concerns[0].text == "needs more detail"


def test_parser_rejects_legacy_action_items_with_empty_text():
    """The parser accepts both ``concerns:`` (spec-015 SSoT) and
    ``action_items:`` (legacy 12-panel / 8-panel prompts). The empty-
    text rejection MUST apply to BOTH key paths."""
    body = _frontmatter(
        "verdict: minor_revision\n"
        "action_items:\n"
        "  - severity: writing\n"
        '    text: ""\n'
    )
    with pytest.raises(RuntimeError, match="empty/missing text"):
        _parse_response(
            body, lens="claim_accuracy", stage="paper_review",
            default_artifact="paper.tex",
        )
