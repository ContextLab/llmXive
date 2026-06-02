"""Reviewer frontmatter recovery — robust to a missing closing ``---``.

Part-7 finding (PROJ-552 spec stage, 2026-05-30): a single reviewer
(``scope_fidelity``) emitted a response that began with two blank lines and an
opening ``---`` but NO closing ``---`` delimiter (the reasoning model ended
right after ``concerns:``). The strict both-delimiters regex matched nothing and
raised ``RuntimeError: response has no YAML frontmatter`` — crashing the ENTIRE
spec panel/run rather than degrading gracefully.

``_extract_frontmatter`` recovers the structured verdict/concerns from the three
real-world shapes; only a response with no opening ``---`` at all is rejected.
"""

from __future__ import annotations

import pytest

from llmxive.convergence.llm_reviewer import _extract_frontmatter, _parse_response


class TestExtractFrontmatter:
    def test_proper_both_delimiters_fast_path(self):
        text = "---\nverdict: accept\nconcerns: []\n---\nprose"
        assert _extract_frontmatter(text) == "verdict: accept\nconcerns: []"

    def test_missing_closing_delimiter_recovered(self):
        text = "---\nverdict: accept\nconcerns: []"
        fm = _extract_frontmatter(text)
        assert fm is not None
        assert "verdict: accept" in fm

    def test_doc_end_boundary_recovered(self):
        text = "---\nverdict: accept\nconcerns: []\n...\nprose"
        fm = _extract_frontmatter(text)
        assert fm is not None
        assert "verdict: accept" in fm
        assert "prose" not in fm

    def test_trailing_prose_without_closing_delim_dropped(self):
        text = (
            "---\nverdict: accept\nconcerns: []\n\n"
            "This is unfenced prose with no closing delimiter."
        )
        fm = _extract_frontmatter(text)
        assert fm is not None
        assert "verdict: accept" in fm

    def test_no_opening_delimiter_returns_none(self):
        assert _extract_frontmatter("just some prose, no frontmatter") is None
        assert _extract_frontmatter("verdict: accept\nconcerns: []") is None


class TestParseResponseRecovery:
    def test_exact_proj552_failure_shape(self):
        """Leading blank lines + opening ``---`` + metadata + concerns, with NO
        closing ``---`` — the precise shape that crashed the PROJ-552 run."""
        resp = (
            "\n\n---\n"
            "reviewer_name: scope_fidelity\n"
            "reviewer_kind: llm\n"
            "stage: clarified\n"
            "artifact_path: projects/PROJ-552/specs/001/spec.md\n"
            "artifact_hash: abc123\n"
            "verdict: minor_revision\n"
            "concerns:\n"
            "  - severity: writing\n"
            "    location: Section 2\n"
            "    text: The scope statement omits the braid-index bound.\n"
        )
        verdict, concerns = _parse_response(
            resp, lens="scope", stage="clarified",
            default_artifact="projects/PROJ-552/specs/001/spec.md",
        )
        assert verdict == "minor_revision"
        assert len(concerns) == 1
        assert "braid-index bound" in concerns[0].text
        assert concerns[0].severity.value == "writing"

    def test_accept_with_no_closing_delim_no_concerns(self):
        resp = "---\nverdict: accept\nconcerns: []"
        verdict, concerns = _parse_response(
            resp, lens="x", stage="clarified", default_artifact="x.md",
        )
        assert verdict == "accept"
        assert concerns == []

    def test_genuinely_missing_frontmatter_still_raises(self):
        resp = "I think the spec looks fine overall, no YAML here."
        with pytest.raises(RuntimeError, match="no YAML frontmatter"):
            _parse_response(
                resp, lens="x", stage="clarified", default_artifact="x.md",
            )

    def test_fenced_yaml_in_prose_does_not_hijack(self):
        """The actual PROJ-552 crash: opening `---`, NO closing `---`, and a
        ```yaml fenced example in the prose body. Stripping the fence first
        would hijack the parse to the example; frontmatter must win."""
        resp = (
            "\n\n---\n"
            "reviewer_name: scope_fidelity\n"
            "reviewer_kind: llm\n"
            "stage: clarified\n"
            "artifact_path: x.md\n"
            "verdict: minor_revision\n"
            "concerns:\n"
            "  - severity: writing\n"
            "    location: s2\n"
            "    text: scope omits the braid-index bound\n"
            "\n"
            "Here is the offending block:\n"
            "```yaml\n"
            "foo: bar\n"
            "```\n"
            "more prose\n"
        )
        verdict, concerns = _parse_response(
            resp, lens="scope", stage="clarified", default_artifact="x.md",
        )
        assert verdict == "minor_revision"
        assert len(concerns) == 1
        assert "braid-index bound" in concerns[0].text

    def test_whole_response_wrapped_in_yaml_fence(self):
        """Some models wrap the entire YAML doc in a ```yaml fence — unwrap and
        parse the frontmatter inside."""
        resp = "```yaml\n---\nverdict: accept\nconcerns: []\n---\n```"
        verdict, concerns = _parse_response(
            resp, lens="x", stage="clarified", default_artifact="x.md",
        )
        assert verdict == "accept"
        assert concerns == []

    def test_proper_delims_with_fenced_prose_example_no_hijack(self):
        resp = (
            "---\n"
            "verdict: reject\n"
            "concerns:\n"
            "  - severity: science\n"
            "    location: s1\n"
            "    text: the 27635 count is wrong\n"
            "---\n"
            "Example of the right shape:\n"
            "```yaml\n"
            "example: 1\n"
            "```\n"
        )
        verdict, concerns = _parse_response(
            resp, lens="x", stage="clarified", default_artifact="x.md",
        )
        assert verdict == "reject"
        assert len(concerns) == 1
        assert "27635" in concerns[0].text


class TestContentlessReviewGuard:
    """False-convergence guard: a review whose frontmatter has NEITHER a
    `verdict:` NOR a `concerns:`/`action_items:` key carries no evidence a review
    happened, so it MUST NOT be silently defaulted to a clean `accept` with zero
    concerns (the same "absence of evidence MUST NOT pass" principle as the
    reviser `<missing>` guard and the spec-019 fill gate). Before this guard a
    truncated/empty reviewer response masked as convergence."""

    def test_empty_frontmatter_raises(self):
        with pytest.raises(RuntimeError, match="false-convergence guard"):
            _parse_response(
                "---\n---\n", lens="scope", stage="clarified",
                default_artifact="x.md",
            )

    def test_contentless_frontmatter_raises(self):
        """Model hung after emitting only an unrelated key — no verdict, no
        concerns. Previously returned ('accept', []) → silent convergence."""
        with pytest.raises(RuntimeError, match="false-convergence guard"):
            _parse_response(
                "---\nnotes: the model stopped here\n---\n",
                lens="scope", stage="clarified", default_artifact="x.md",
            )

    def test_explicit_verdict_only_is_legit_accept(self):
        """A genuine clean accept states `verdict:` explicitly — NOT rejected."""
        verdict, concerns = _parse_response(
            "---\nverdict: accept\n---\n", lens="x", stage="clarified",
            default_artifact="x.md",
        )
        assert verdict == "accept"
        assert concerns == []

    def test_explicit_empty_concerns_is_legit_accept(self):
        verdict, concerns = _parse_response(
            "---\nverdict: accept\nconcerns: []\n---\n", lens="x",
            stage="clarified", default_artifact="x.md",
        )
        assert verdict == "accept"
        assert concerns == []

    def test_legacy_explicit_empty_action_items_is_legit_accept(self):
        """Legacy paper/research panels signal 'clean' via an explicit
        `action_items: []` (no `verdict:` key) — that is affirmative, NOT
        contentless, so it MUST still parse as a clean accept."""
        verdict, concerns = _parse_response(
            "---\naction_items: []\n---\n", lens="x", stage="clarified",
            default_artifact="x.md",
        )
        assert verdict == "accept"
        assert concerns == []

    def test_concerns_without_verdict_still_parses(self):
        """A review that raises concerns but omits `verdict:` is not contentless
        (it has evidence) — the concerns must be processed."""
        resp = (
            "---\nconcerns:\n  - severity: science\n"
            "    text: the data source is unverified\n---\n"
        )
        _verdict, concerns = _parse_response(
            resp, lens="x", stage="clarified", default_artifact="x.md",
        )
        assert len(concerns) == 1
        assert "unverified" in concerns[0].text
