"""T016 — Unit tests for verify/compute.py (spec 018, US5).

Pure / offline. Real sympy (no mocks). backend=None throughout.
"""

from __future__ import annotations

import pytest

from llmxive.claims.models import Claim, ClaimKind, ClaimStatus, compute_claim_id
from llmxive.verify.compute import (
    ComputeStatus,
    ComputeVerdict,
    evaluate,
    extract_expression,
    verify_computational,
)


def _make_claim(
    raw_text: str,
    kind: ClaimKind = ClaimKind.NUMERIC,
    canonical: str = "",
) -> Claim:
    return Claim(
        claim_id=compute_claim_id(kind, canonical or raw_text, "test"),
        kind=kind,
        raw_text=raw_text,
        canonical=canonical or raw_text,
        context="test",
        artifact_path="test.md",
        source_type="external",
        status=ClaimStatus.PENDING,
        resolved_value=None,
        evidence=None,
        resolver=None,
        attempts=0,
        updated_at="2026-01-01T00:00:00Z",
    )


# ---------------------------------------------------------------------------
# evaluate() tests
# ---------------------------------------------------------------------------

class TestEvaluate:
    def test_simple_addition(self):
        result = evaluate("1+2")
        assert result == "3"

    def test_subtraction(self):
        assert evaluate("5-3") == "2"

    def test_multiplication(self):
        assert evaluate("3*4") == "12"

    def test_division(self):
        result = evaluate("10/2")
        assert result == "5"

    def test_power(self):
        assert evaluate("2**10") == "1024"

    def test_parentheses(self):
        assert evaluate("(2+3)*4") == "20"

    def test_comparison_false(self):
        result = evaluate("1>2")
        assert result is not None
        assert result.lower() in ("false", "0")

    def test_comparison_true(self):
        result = evaluate("3>1")
        assert result is not None
        assert result.lower() in ("true", "1")

    def test_less_than_true(self):
        result = evaluate("1<2")
        assert result is not None
        assert result.lower() in ("true", "1")

    def test_less_than_false(self):
        result = evaluate("5<2")
        assert result is not None
        assert result.lower() in ("false", "0")

    def test_algebraic_identity_zero(self):
        """(x+1)^2 - (x^2+2x+1) = 0 symbolically."""
        result = evaluate("(x+1)**2-(x**2+2*x+1)")
        assert result == "0"

    def test_percentage_30_of_200(self):
        result = evaluate("30% of 200")
        assert result is not None
        assert float(result) == pytest.approx(60.0)

    def test_percentage_50_of_100(self):
        result = evaluate("50% of 100")
        assert result is not None
        assert float(result) == pytest.approx(50.0)

    def test_unit_conversion_km_to_m(self):
        result = evaluate("5 km → m")
        assert result is not None
        assert float(result) == pytest.approx(5000.0)

    def test_unit_conversion_km_to_m_to_arrow(self):
        result = evaluate("5 km to m")
        assert result is not None
        assert float(result) == pytest.approx(5000.0)

    def test_unit_conversion_cm_to_m(self):
        result = evaluate("100 cm → m")
        assert result is not None
        assert float(result) == pytest.approx(1.0)

    def test_unparseable_returns_none(self):
        result = evaluate("this is not math $$@!!")
        assert result is None

    def test_empty_string_returns_none(self):
        result = evaluate("")
        assert result is None

    def test_never_raises(self):
        """evaluate must never raise, even on pathological input."""
        for bad in ["__import__('os')", "os.system('ls')", "1/0", "", "???", "∞∞∞"]:
            result = evaluate(bad)
            assert result is None or isinstance(result, str)

    def test_no_eval_no_exec(self):
        """Confirm compute.py has no Python built-in eval or exec calls.

        Uses tokenize to scan only real NAME tokens (not comments or strings).
        'evaluate' as an identifier and 'evaluate=True' keyword args are fine.
        """
        import io
        import tokenize
        import inspect
        from llmxive.verify import compute
        src = inspect.getsource(compute)

        forbidden: list[str] = []
        tokens = list(tokenize.generate_tokens(io.StringIO(src).readline))
        for i, tok in enumerate(tokens):
            if tok.type != tokenize.NAME:
                continue
            if tok.string not in ("eval", "exec"):
                continue
            # Must be followed (skipping whitespace tokens) by OP '('
            for j in range(i + 1, min(i + 4, len(tokens))):
                nxt = tokens[j]
                if nxt.type in (tokenize.NL, tokenize.NEWLINE,
                                tokenize.INDENT, tokenize.DEDENT,
                                tokenize.COMMENT):
                    continue
                if nxt.type == tokenize.OP and nxt.string == "(":
                    forbidden.append(f"{tok.string}( at line {tok.start[0]}")
                break

        assert forbidden == [], (
            f"Found Python built-in eval/exec calls in compute.py: {forbidden}"
        )


# ---------------------------------------------------------------------------
# extract_expression() tests (backend=None, deterministic)
# ---------------------------------------------------------------------------

class TestExtractExpression:
    def test_arithmetic_word_form(self):
        claim = _make_claim("1 plus 2 is 3")
        result = extract_expression(claim, backend=None, model=None, repo_root=None)
        assert result is not None
        expr, asserted = result
        assert asserted == "3"
        # expression should be evaluable to 3
        computed = evaluate(expr)
        assert computed == "3"

    def test_comparison_larger_than(self):
        claim = _make_claim("1 is larger than 2")
        result = extract_expression(claim, backend=None, model=None, repo_root=None)
        assert result is not None
        expr, asserted = result
        assert asserted.lower() == "true"
        # expression: 1>2, which is False
        computed = evaluate(expr)
        assert computed is not None
        assert computed.lower() in ("false", "0")

    def test_percentage_claim(self):
        claim = _make_claim("30% of 200 is 60")
        result = extract_expression(claim, backend=None, model=None, repo_root=None)
        assert result is not None
        expr, asserted = result
        assert asserted == "60"
        computed = evaluate(expr)
        assert float(computed) == pytest.approx(60.0)

    def test_unit_claim(self):
        claim = _make_claim("5 km is 5000 m")
        result = extract_expression(claim, backend=None, model=None, repo_root=None)
        assert result is not None
        expr, asserted = result
        assert "5000" in asserted or asserted == "5000"

    def test_unknown_form_returns_none(self):
        claim = _make_claim("The sky is blue on a clear day")
        result = extract_expression(claim, backend=None, model=None, repo_root=None)
        assert result is None


# ---------------------------------------------------------------------------
# verify_computational() tests (backend=None)
# ---------------------------------------------------------------------------

class TestVerifyComputational:
    def test_one_plus_one_is_two_verified(self):
        claim = _make_claim("1 plus 1 is 2")
        verdict = verify_computational(claim, backend=None)
        assert verdict.evaluable is True
        assert verdict.status == ComputeStatus.VERIFIED

    def test_one_plus_two_is_one_refuted(self):
        claim = _make_claim("1 plus 2 is 1")
        verdict = verify_computational(claim, backend=None)
        assert verdict.evaluable is True
        assert verdict.status == ComputeStatus.REFUTED
        # computed should be 3
        assert verdict.computed == "3"

    def test_one_is_larger_than_two_refuted(self):
        claim = _make_claim("1 is larger than 2")
        verdict = verify_computational(claim, backend=None)
        assert verdict.evaluable is True
        assert verdict.status == ComputeStatus.REFUTED

    def test_two_is_larger_than_one_verified(self):
        claim = _make_claim("2 is larger than 1")
        verdict = verify_computational(claim, backend=None)
        assert verdict.evaluable is True
        assert verdict.status == ComputeStatus.VERIFIED

    def test_30_pct_of_200_is_60_verified(self):
        claim = _make_claim("30% of 200 is 60")
        verdict = verify_computational(claim, backend=None)
        assert verdict.evaluable is True
        assert verdict.status == ComputeStatus.VERIFIED

    def test_5_km_is_5200_m_refuted(self):
        """5 km is 5200 m — wrong; should be 5000."""
        claim = _make_claim("5 km is 5200 m")
        verdict = verify_computational(claim, backend=None)
        assert verdict.evaluable is True
        assert verdict.status == ComputeStatus.REFUTED
        # computed should be approximately 5000
        assert verdict.computed is not None
        assert float(verdict.computed) == pytest.approx(5000.0, rel=1e-3)

    def test_5_km_is_5000_m_verified(self):
        claim = _make_claim("5 km is 5000 m")
        verdict = verify_computational(claim, backend=None)
        assert verdict.evaluable is True
        assert verdict.status == ComputeStatus.VERIFIED

    def test_unevaluable_text_not_evaluable(self):
        claim = _make_claim("The capital of France is Paris")
        verdict = verify_computational(claim, backend=None)
        assert verdict.status == ComputeStatus.NOT_EVALUABLE
        assert verdict.evaluable is False

    def test_verdict_is_frozen_dataclass(self):
        claim = _make_claim("1 plus 1 is 2")
        verdict = verify_computational(claim, backend=None)
        assert isinstance(verdict, ComputeVerdict)
        with pytest.raises((AttributeError, TypeError)):
            verdict.status = ComputeStatus.REFUTED  # type: ignore[misc]

    def test_verdict_has_expression(self):
        claim = _make_claim("1 plus 1 is 2")
        verdict = verify_computational(claim, backend=None)
        assert verdict.expression != ""

    def test_verdict_has_asserted(self):
        claim = _make_claim("1 plus 1 is 2")
        verdict = verify_computational(claim, backend=None)
        assert verdict.asserted == "2"

    def test_refuted_verdict_has_computed(self):
        claim = _make_claim("1 plus 2 is 1")
        verdict = verify_computational(claim, backend=None)
        assert verdict.status == ComputeStatus.REFUTED
        assert verdict.computed  # non-empty

    def test_3_times_4_is_12_verified(self):
        claim = _make_claim("3 times 4 is 12")
        verdict = verify_computational(claim, backend=None)
        assert verdict.evaluable is True
        assert verdict.status == ComputeStatus.VERIFIED

    def test_10_divided_by_2_is_5_verified(self):
        claim = _make_claim("10 divided by 2 is 5")
        verdict = verify_computational(claim, backend=None)
        assert verdict.evaluable is True
        assert verdict.status == ComputeStatus.VERIFIED

    def test_less_than_verified(self):
        claim = _make_claim("1 is less than 2")
        verdict = verify_computational(claim, backend=None)
        assert verdict.evaluable is True
        assert verdict.status == ComputeStatus.VERIFIED

    def test_less_than_refuted(self):
        claim = _make_claim("5 is less than 2")
        verdict = verify_computational(claim, backend=None)
        assert verdict.evaluable is True
        assert verdict.status == ComputeStatus.REFUTED
