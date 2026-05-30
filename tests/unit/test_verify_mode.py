"""T003 — unit tests for verify/mode.py (spec 018, T003/T004)."""

from __future__ import annotations

from llmxive.claims.models import Claim, ClaimKind, ClaimStatus
from llmxive.verify.mode import looks_approximate, looks_self_contained, select_mode


def _make_claim(
    raw: str,
    kind: ClaimKind = ClaimKind.NUMERIC,
    canonical: str = "",
) -> Claim:
    return Claim(
        claim_id="c_test",
        kind=kind,
        raw_text=raw,
        canonical=canonical or raw,
        context="test",
        artifact_path="test.md",
        source_type="external",
        status=ClaimStatus.PENDING,
        resolved_value=None,
        evidence=None,
        resolver=None,
        attempts=0,
        updated_at="2026-05-30T00:00:00Z",
    )


# ---------------------------------------------------------------------------
# looks_self_contained
# ---------------------------------------------------------------------------

class TestLooksSelfContained:
    def test_arithmetic_relation_true(self):
        assert looks_self_contained("1 plus 2 is 1") is True

    def test_comparison_true(self):
        assert looks_self_contained("1 is larger than 2") is True

    def test_percentage_true(self):
        assert looks_self_contained("30% of 200 is 60") is True

    def test_unit_conversion_true(self):
        assert looks_self_contained("5 km is 5200 m") is True

    def test_external_entity_false(self):
        # references an external entity/subject — not self-contained
        assert looks_self_contained("9,988 prime knots at 13 crossings") is False

    def test_capital_fact_false(self):
        assert looks_self_contained("the capital of Australia is Sydney") is False

    def test_mixed_arithmetic_fact_false(self):
        # mixed: arithmetic operator present but also references external named subject
        # FR-017: must NOT be self-contained
        assert looks_self_contained("there are 9988 plus 1 prime knots") is False

    def test_simple_equality_true(self):
        assert looks_self_contained("1 plus 1 is 2") is True

    def test_inequality_true(self):
        assert looks_self_contained("3 times 4 equals 12") is True

    def test_named_constant_relation_true(self):
        # "pi is approximately 3.14" is self-contained (pi is a defined constant, not external subject)
        assert looks_self_contained("pi is approximately 3.14") is True


# ---------------------------------------------------------------------------
# looks_approximate
# ---------------------------------------------------------------------------

class TestLooksApproximate:
    def test_about_hedge_true(self):
        assert looks_approximate("pi is about 3") is True

    def test_approximately_hedge_true(self):
        assert looks_approximate("the value is approximately 3.14") is True

    def test_tilde_hedge_true(self):
        assert looks_approximate("the value is ~3.14") is True

    def test_approx_symbol_true(self):
        assert looks_approximate("the value is ≈ 3.14") is True

    def test_roughly_hedge_true(self):
        assert looks_approximate("roughly 2.718") is True

    def test_around_hedge_true(self):
        assert looks_approximate("around 6.28") is True

    def test_decimal_value_true(self):
        assert looks_approximate("the value is 3.14") is True

    def test_recognized_constant_true(self):
        assert looks_approximate("pi is 3.14159") is True

    def test_bare_integer_false(self):
        assert looks_approximate("9988 prime knots") is False

    def test_bare_integer_count_false(self):
        assert looks_approximate("there are 42 items") is False

    def test_scientific_notation_true(self):
        assert looks_approximate("the value is 3.0e8") is True


# ---------------------------------------------------------------------------
# select_mode (heuristic path, backend=None)
# ---------------------------------------------------------------------------

class TestSelectModeHeuristic:
    def test_self_contained_computational(self):
        claim = _make_claim("1 plus 2 is 1", kind=ClaimKind.NUMERIC)
        assert select_mode(claim, backend=None) == "computational"

    def test_comparison_computational(self):
        claim = _make_claim("1 is larger than 2", kind=ClaimKind.NUMERIC)
        assert select_mode(claim, backend=None) == "computational"

    def test_percentage_computational(self):
        claim = _make_claim("30% of 200 is 60", kind=ClaimKind.NUMERIC)
        assert select_mode(claim, backend=None) == "computational"

    def test_unit_conversion_computational(self):
        claim = _make_claim("5 km is 5200 m", kind=ClaimKind.NUMERIC)
        assert select_mode(claim, backend=None) == "computational"

    def test_pi_approximate(self):
        claim = _make_claim("pi is about 3", kind=ClaimKind.NUMERIC)
        assert select_mode(claim, backend=None) == "approximate"

    def test_decimal_approximate(self):
        claim = _make_claim("the value is 3.14", kind=ClaimKind.NUMERIC)
        assert select_mode(claim, backend=None) == "approximate"

    def test_recognized_constant_approximate(self):
        claim = _make_claim("pi is 3.14159", kind=ClaimKind.NUMERIC)
        assert select_mode(claim, backend=None) == "approximate"

    def test_integer_discrete_count_exact(self):
        # bare integer count → exact (NEVER approximate — default-safe FR-003)
        claim = _make_claim("9,988 prime knots at 13 crossings", kind=ClaimKind.NUMERIC)
        mode = select_mode(claim, backend=None)
        assert mode == "exact"

    def test_integer_count_never_approximate(self):
        # Default-safe: integer-valued discrete claim NEVER returns "approximate"
        claim = _make_claim("there are 42 species", kind=ClaimKind.NUMERIC)
        mode = select_mode(claim, backend=None)
        assert mode != "approximate"

    def test_entity_fact_source(self):
        claim = _make_claim("the capital of Australia is Sydney", kind=ClaimKind.ENTITY_FACT)
        assert select_mode(claim, backend=None) == "source"

    def test_relational_source(self):
        claim = _make_claim("the capital of France is Paris", kind=ClaimKind.RELATIONAL)
        assert select_mode(claim, backend=None) == "source"

    def test_result_kind_source(self):
        # RESULT claims should never go to computational
        claim = _make_claim("the study found 42 cases", kind=ClaimKind.RESULT)
        mode = select_mode(claim, backend=None)
        assert mode != "computational"
