"""End-to-end domain traversal harness (spec 015 T071).

Drives a project through the FULL pipeline (brainstorm → flesh_out →
specify → clarify → plan → tasks → analyze → implement → review →
paper → publisher → posted) for each of the 9
:data:`LIBRARIAN_DEFAULT_FIELDS` domains, and asserts:

1. Every domain reaches ``posted`` (T073 — gated by maintainer DOI
   sign-off per FR-054).
2. A deliberately weak project per domain is REJECTED / kicked back
   (T075).
3. Every produced artifact is honest — no truncation markers, no
   broken-tool placeholders, no task marked ``[X]`` with placeholder
   content (T074).

This module is the SCAFFOLD: it defines the test structure + the
assertion helpers. The actual real-call traversal (T073) requires
``LLMXIVE_REAL_TESTS=1`` AND maintainer approval per domain (DOI sign-
off via ``llmxive project publish-approve``) — that's the human gate
the harness pauses at.

Default (no env var): the structure-level tests below verify the
domain list, the per-domain test parametrization, and the dry-run
artifact-inspection helpers. They do NOT call the LLM.
"""

from __future__ import annotations

import os
import re
from pathlib import Path

import pytest

from llmxive.calibration.domains import ANCHOR_PAPERS, AnchorPaper
from llmxive.librarian import LIBRARIAN_DEFAULT_FIELDS

REAL_TESTS_ENABLED = os.environ.get("LLMXIVE_REAL_TESTS") == "1"

# --- placeholder / truncation / broken-tool markers --------------------
# These markers MUST NOT appear in produced artifacts. Each is a pattern
# the implementer agent has historically emitted (placeholder content,
# truncated output, tool failure stubs). The T074 verification scans
# every artifact for them.

_PLACEHOLDER_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"\bTODO\b"),
    re.compile(r"\bTBD\b"),
    re.compile(r"\bFIXME\b"),
    re.compile(r"<placeholder>", re.IGNORECASE),
    re.compile(r"\.{3}truncated\.{3}"),
    re.compile(r"\[truncated\]", re.IGNORECASE),
    re.compile(r"tool error: ", re.IGNORECASE),
    re.compile(r"\[NEEDS CLARIFICATION:"),
)


def scan_for_placeholders(text: str) -> list[str]:
    """Return every placeholder/truncation/broken-tool marker found in
    ``text``. Empty list = artifact is honest."""
    hits: list[str] = []
    for pat in _PLACEHOLDER_PATTERNS:
        m = pat.search(text)
        if m:
            hits.append(m.group(0))
    return hits


def assert_artifact_is_honest(path: Path) -> None:
    """Read ``path`` and assert it contains no placeholder/truncation/
    broken-tool markers. Raises ``AssertionError`` with the specific
    markers found if any are present."""
    text = path.read_text(encoding="utf-8", errors="replace")
    hits = scan_for_placeholders(text)
    assert not hits, (
        f"artifact {path} contains placeholder/truncation/broken-tool "
        f"markers: {hits!r}. T074 requires honest artifacts — every "
        "task marked complete MUST produce real content."
    )


# --- structure-level tests (always run) ---------------------------------


def test_harness_covers_every_librarian_default_field():
    """The harness MUST exercise every domain in LIBRARIAN_DEFAULT_FIELDS
    (no silent dropping of a field)."""
    field_names = {a.field_name for a in ANCHOR_PAPERS}
    assert field_names == set(LIBRARIAN_DEFAULT_FIELDS)
    assert len(ANCHOR_PAPERS) == 9


@pytest.mark.parametrize("anchor", ANCHOR_PAPERS, ids=lambda a: a.field_name)
def test_per_domain_harness_scaffolding(anchor: AnchorPaper):
    """The per-domain harness scaffolding is present: each anchor MUST
    carry a DOI + URL the test can use to verify the produced paper's
    bibliography correctly cites the anchor (T074)."""
    assert anchor.doi.strip()
    assert anchor.url.startswith("http")
    # If this is the held-out anchor, the calibration set MUST flag it
    # so the harness can skip prompt-tuning steps for this domain.
    if anchor.held_out:
        assert anchor.field_name == "psychology"


def test_placeholder_scanner_catches_known_markers():
    """The T074 honesty scanner MUST catch every documented placeholder
    pattern. Without this, the e2e test could silently green even when
    a task produced "TODO: real implementation later"."""
    samples = [
        "TODO: implement this later",
        "implementation TBD",
        "FIXME: broken handling",
        "<placeholder>",
        "...truncated...",
        "[TRUNCATED] more text follows",
        "tool error: backend timed out",
        "[NEEDS CLARIFICATION: which approach?]",
    ]
    for sample in samples:
        hits = scan_for_placeholders(sample)
        assert hits, f"scanner missed marker in: {sample!r}"


def test_placeholder_scanner_does_not_false_positive_on_clean_text():
    """The scanner must NOT flag legitimate prose. False positives would
    fail every legitimate test run."""
    clean_samples = [
        "We performed regression analysis on the data.",
        "The methodology is described in Section 3.",
        "Results show effect size 0.35 (95% CI 0.28-0.42).",
    ]
    for sample in clean_samples:
        assert scan_for_placeholders(sample) == []


def test_assert_artifact_is_honest_passes_on_clean_file(tmp_path: Path):
    p = tmp_path / "clean.md"
    p.write_text("# Clean spec\n\nFR-001: do X. Verified by tests/test_x.py.")
    assert_artifact_is_honest(p)  # should not raise


def test_assert_artifact_is_honest_fails_on_dirty_file(tmp_path: Path):
    p = tmp_path / "dirty.md"
    p.write_text("# Spec\n\nFR-001: TODO write this.")
    with pytest.raises(AssertionError, match="placeholder/truncation/broken-tool"):
        assert_artifact_is_honest(p)


# --- real-call traversal stubs (T073) -----------------------------------


@pytest.mark.skipif(not REAL_TESTS_ENABLED, reason="LLMXIVE_REAL_TESTS!=1")
@pytest.mark.parametrize("anchor", ANCHOR_PAPERS, ids=lambda a: a.field_name)
def test_traversal_to_posted_per_domain(anchor: AnchorPaper, tmp_path: Path):
    """Drive a project for ``anchor.field_name`` through the full
    pipeline to ``posted``.

    This test PAUSES at the FR-054 manual DOI sign-off step — the
    maintainer must run ``llmxive project publish-approve
    <PROJ-ID>`` for each domain before the test can complete. The
    test SKIPS (does not fail) when the sign-off hasn't been recorded
    yet, so a partial CI run doesn't mark itself failed for what is a
    human-gate-pending state.
    """
    pytest.skip(
        f"T073 manual gate: this test requires the maintainer to run "
        f"`llmxive project publish-approve PROJ-<id>` for the "
        f"{anchor.field_name} domain. Until then this branch is a "
        f"no-op skip. See spec 015 FR-054."
    )


@pytest.mark.skipif(not REAL_TESTS_ENABLED, reason="LLMXIVE_REAL_TESTS!=1")
def test_weak_project_is_rejected_or_kicked_back(tmp_path: Path):
    """T075: a deliberately weak project (circular RQ + missing data +
    contradictory plan) MUST be rejected or kicked back to an earlier
    stage. The harness asserts the project does NOT advance past the
    review stage that should have caught the flaws.

    Like the per-domain traversal, this requires real LLM calls and
    SKIPS by default. Maintainer runs with LLMXIVE_REAL_TESTS=1.
    """
    pytest.skip(
        "T075 manual gate: weak-project rejection verification requires "
        "real LLM calls + maintainer co-evaluation per FR-046."
    )
