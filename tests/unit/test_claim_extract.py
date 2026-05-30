"""T015 — Unit tests for claims/extract.py (T015).

Offline: exercises the REAL post-parse filter directly (no mock backend).
Real-LLM: gated behind LLMXIVE_REAL_TESTS.
"""

from __future__ import annotations

import os
import pytest

from llmxive.claims.extract import _filter_check_worthy
from llmxive.claims.models import ClaimStatus


class TestFilterCheckWorthy:
    """Offline tests for the post-parse deterministic filter (no backend)."""

    def test_numeric_claim_kept(self):
        candidates = ["There are 9,988 prime knots at 10 crossings."]
        result = _filter_check_worthy(candidates)
        assert len(result) == 1
        assert result[0] == "There are 9,988 prime knots at 10 crossings."

    def test_design_choice_dropped(self):
        candidates = [
            "We use a threshold of p < 0.05.",
        ]
        result = _filter_check_worthy(candidates)
        assert len(result) == 0

    def test_parameter_setting_dropped(self):
        candidates = [
            "The learning rate is set to 0.001.",
        ]
        result = _filter_check_worthy(candidates)
        assert len(result) == 0

    def test_resolution_setting_dropped(self):
        candidates = ["Image resolution is 1200x900 pixels."]
        result = _filter_check_worthy(candidates)
        assert len(result) == 0

    def test_requirement_id_dropped(self):
        candidates = ["FR-001 requires the system to log all events."]
        result = _filter_check_worthy(candidates)
        assert len(result) == 0

    def test_subjective_statement_dropped(self):
        candidates = ["This approach is elegant and well-suited to the problem."]
        result = _filter_check_worthy(candidates)
        assert len(result) == 0

    def test_mixed_keeps_only_checkworthy(self):
        candidates = [
            "There are 9,988 prime knots at 10 crossings.",  # keep: numeric empirical
            "We use a threshold of p < 0.05.",               # drop: design choice
            "The approach is well-suited for the task.",     # drop: subjective
            "Knot theory was founded by Carl Friedrich Gauss.",  # keep: entity fact
        ]
        result = _filter_check_worthy(candidates)
        assert "There are 9,988 prime knots at 10 crossings." in result
        assert "Knot theory was founded by Carl Friedrich Gauss." in result
        for dropped in ["We use a threshold of p < 0.05.", "The approach is well-suited for the task."]:
            assert dropped not in result

    def test_empty_input(self):
        assert _filter_check_worthy([]) == []

    def test_empty_string_dropped(self):
        result = _filter_check_worthy([""])
        assert result == []

    def test_short_fragment_dropped(self):
        """Very short strings (< 10 chars) are not check-worthy claims."""
        result = _filter_check_worthy(["yes", "no"])
        assert result == []


@pytest.mark.skipif(
    not os.environ.get("LLMXIVE_REAL_TESTS"),
    reason="Real LLM call — set LLMXIVE_REAL_TESTS=1 to run",
)
class TestExtractClaimsRealLLM:
    """Real-LLM extraction (requires LLMXIVE_REAL_TESTS=1 and Dartmouth key)."""

    def test_extract_returns_pending_claims(self, tmp_path):
        from llmxive.claims.extract import extract_claims
        from llmxive.credentials import load_dartmouth_key
        from llmxive.backends.dartmouth import DartmouthBackend

        key = load_dartmouth_key()
        if not key:
            pytest.skip("No Dartmouth key available")

        backend = DartmouthBackend()
        text = (
            "Knot theory studies closed loops in 3D space. "
            "There are 9,988 prime knots with at most 10 crossings "
            "(OEIS A002863, https://oeis.org/A002863). "
            "We use a convergence threshold of 0.95. "
            "The largest known prime knot has millions of crossings."
        )
        claims = extract_claims(
            text,
            artifact_path="test/doc.md",
            backend=backend,
            model="qwen.qwen3.5-122b",
            repo_root=tmp_path,
        )
        # Must return a list (possibly empty on extraction error)
        assert isinstance(claims, list)
        for c in claims:
            assert c.status == ClaimStatus.PENDING
            assert c.raw_text
            assert c.claim_id.startswith("c_")
        # Should NOT include the design threshold
        threshold_texts = [c.raw_text for c in claims if "0.95" in c.raw_text and "threshold" in c.raw_text.lower()]
        assert len(threshold_texts) == 0, f"Design threshold leaked into claims: {threshold_texts}"
