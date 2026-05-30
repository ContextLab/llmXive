"""Real-call (LLMXIVE_REAL_TESTS=1) test for the F-18 network guard.

Runs ``verify_and_clean`` over a small doc that mixes one REAL, resolvable
arXiv id (``1706.03762`` — "Attention Is All You Need") with the FABRICATED
``arXiv:2402.13`` reference that triggered the PROJ-552 fabrication cascade.

Constitution Principle II: every external reference must be verified against
its primary source; unverifiable ones are flagged ``[UNVERIFIED]`` (never
silently dropped, never silently "fixed" with a different fake number). This
test makes REAL HTTP calls (arXiv API) — gated behind LLMXIVE_REAL_TESTS=1 by
the repo conftest.
"""

from __future__ import annotations

from pathlib import Path

from llmxive.agents.citation_guard import verify_and_clean


def test_verify_and_clean_flags_fake_keeps_real(tmp_path: Path) -> None:
    doc = (
        "# Knot complexity\n\n"
        "The minimal-crossing diagram count is 9,988 "
        "(Lee et al. 2024, arXiv:2402.13).\n\n"
        "Transformers were introduced in arXiv:1706.03762.\n"
    )
    cleaned, report = verify_and_clean(
        doc,
        repo_root=tmp_path,
        project_id="PROJ-TEST-GUARD",
        artifact_path="specs/001-x/spec.md",
    )

    # The fabricated malformed ref is flagged.
    assert "[UNVERIFIED: arXiv:2402.13" in cleaned, cleaned
    assert "2402.13" in report.flagged_values
    # The real arXiv id survives, untouched (it resolves to a real paper).
    assert "arXiv:1706.03762" in cleaned
    assert "1706.03762" not in report.flagged_values
    # The surrounding claim text is preserved (no silent deletion).
    assert "The minimal-crossing diagram count is 9,988" in cleaned
