"""Guard test: no advancement-decision path reads accumulated review points (spec
015 T038 / FR-019/FR-020). The point system was removed in T041; the gate is now
unanimous LLM-panel acceptance everywhere. This is a grep-guard plus a behavioral
check that empty-records / non-accept records do NOT advance to a `*_ACCEPTED`
stage on the strength of any threshold."""

from __future__ import annotations

import re
from pathlib import Path

_REPO = Path(__file__).resolve().parents[2]


def test_advancement_does_not_read_a_threshold():
    """The research/paper review handlers in advancement.py must not compare
    any sum-of-scores against a threshold any more (RESEARCH_ACCEPT_THRESHOLD /
    PAPER_ACCEPT_THRESHOLD / accept_total>=N pattern)."""
    src = (_REPO / "src" / "llmxive" / "agents" / "advancement.py").read_text()
    # The legacy point summation must be gone.
    assert "accept_total" not in src or "accept_total" in (
        "comment-only references"
    ), "advancement.py still computes accept_total (point sum)"
    # The function bodies must not import/use the threshold constants for a
    # comparison (mention in a comment explaining the removal is fine).
    body_lines = [ln for ln in src.splitlines() if not ln.lstrip().startswith("#")]
    body = "\n".join(body_lines)
    assert ">= RESEARCH_ACCEPT_THRESHOLD" not in body
    assert ">= PAPER_ACCEPT_THRESHOLD" not in body
    # _award_review_points was deleted (only comments may mention it).
    assert "def _award_review_points" not in body


def test_no_points_in_advancement_imports():
    """advancement.py no longer imports the threshold constants from config."""
    src = (_REPO / "src" / "llmxive" / "agents" / "advancement.py").read_text()
    # Strip comment lines, then look for a bare `RESEARCH_ACCEPT_THRESHOLD` /
    # `PAPER_ACCEPT_THRESHOLD` in an `import` statement.
    code = "\n".join(ln for ln in src.splitlines() if not ln.lstrip().startswith("#"))
    assert not re.search(
        r"^from llmxive\.config import .*RESEARCH_ACCEPT_THRESHOLD", code, re.MULTILINE,
    )
    assert not re.search(
        r"^from llmxive\.config import .*PAPER_ACCEPT_THRESHOLD", code, re.MULTILINE,
    )


def test_evaluate_does_not_advance_on_no_accept_records(tmp_path):
    """Behavioral guard: a project with zero accept records must NOT advance to
    RESEARCH_ACCEPTED (under the old threshold-only gate, vacuous accept_total
    + missing required-specialists could falsely trip the gate)."""
    from datetime import UTC, datetime

    from llmxive.agents.advancement import evaluate
    from llmxive.types import Project, Stage

    proj = Project(
        id="PROJ-041-no-accepts",
        title="t",
        field="biology",
        current_stage=Stage.RESEARCH_REVIEW,
        points_research={},
        points_paper={},
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
        artifact_hashes={},
    )
    out = evaluate(proj, repo_root=tmp_path)
    assert out.current_stage != Stage.RESEARCH_ACCEPTED
