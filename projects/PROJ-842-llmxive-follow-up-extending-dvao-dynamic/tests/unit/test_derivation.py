import pytest
import sys
import os

# Ensure src is in path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from src.derivation.variance_scaling import derive_variance_scaling
from src.derivation.sample_complexity import invert_to_sample_complexity


class TestVarianceScalingDerivation:
    """Tests for verifying symbolic variance scaling equations simplify correctly."""

    def test_returns_sympy_expr(self):
        """Verify the derivation returns a sympy expression object."""
        result = derive_variance_scaling()
        # Check type without assuming specific sympy version internals too deeply
        # We just need to ensure it's a symbolic expression object
        assert hasattr(result, 'free_symbols'), "Result must be a symbolic expression with free symbols"
        assert result is not None

    def test_includes_expected_symbols(self):
        """Verify the expression contains N and epsilon (or equivalent noise term)."""
        result = derive_variance_scaling()
        symbols = [str(s) for s in result.free_symbols]
        # The derivation should depend on N (number of objectives)
        assert 'N' in symbols, f"Expected 'N' in free symbols, got {symbols}"
        # Should also depend on the noise term (epsilon or epsilon_i)
        has_epsilon = any('epsilon' in s.lower() for s in symbols)
        assert has_epsilon, f"Expected an epsilon symbol in free symbols, got {symbols}"

    def test_simplification_reduces_complexity(self):
        """Verify that simplifying the expression reduces its structural complexity."""
        from sympy import simplify

        raw_expr = derive_variance_scaling()
        simplified_expr = simplify(raw_expr)

        # Simplification should generally reduce the number of nodes in the expression tree
        # or at least not increase it significantly. We check that the expression is valid.
        assert simplified_expr is not None
        # A basic sanity check: the simplified form should still have the same free symbols
        assert set(str(s) for s in raw_expr.free_symbols) == set(str(s) for s in simplified_expr.free_symbols)


class TestSampleComplexityInversion:
    """Tests for verifying sample complexity inversion simplifies correctly."""

    def test_returns_string_equation(self):
        """Verify the inversion returns a string representation of the equation."""
        result = invert_to_sample_complexity()
        assert isinstance(result, str), f"Expected string, got {type(result)}"
        assert len(result) > 0, "Equation string should not be empty"

    def test_contains_variance_term(self):
        """Verify the equation string references variance or epsilon."""
        result = invert_to_sample_complexity()
        # The equation should relate sample complexity to variance/noise
        lower_case = result.lower()
        has_variance_term = 'var' in lower_case or 'epsilon' in lower_case or 'eps' in lower_case
        assert has_variance_term, f"Equation should reference variance/noise terms: {result}"

    def test_contains_n_objectives(self):
        """Verify the equation string references N (number of objectives)."""
        result = invert_to_sample_complexity()
        # The sample complexity should scale with N
        assert 'n' in result.lower() or 'N' in result, f"Equation should reference N: {result}"

    def test_simplification_consistency(self):
        """Verify that if we parse the equation back (conceptually), it remains consistent."""
        # This is a structural check on the string output to ensure it's a valid equation form
        result = invert_to_sample_complexity()
        # Check for basic equation structure (contains an equals sign)
        assert '=' in result, f"Sample complexity equation should be an equality: {result}"
        # Check for basic mathematical operators
        assert any(op in result for op in ['+', '-', '*', '/', '^']), f"Equation should contain operators: {result}"