"""
Unit tests for the Hardy-Littlewood expected count function (task T013b-a).
"""

import math
import pytest

from generate_primes import (
    calculate_hardy_littlewood_expected_count,
    compute_hardy_littlewood_expected_count,
    HARDY_LITTLEWOOD_CONSTANT,
)


class TestCalculateHardyLittlewoodExpectedCount:
    def test_formula_matches_definition(self):
        x = 10**9
        expected = HARDY_LITTLEWOOD_CONSTANT * x / (math.log(x) ** 2)
        assert calculate_hardy_littlewood_expected_count(x) == pytest.approx(expected, rel=1e-12)

    def test_value_at_1e9(self):
        # C_2 * x / (ln x)^2 for x = 10^9
        x = 10**9
        ln_x = math.log(x)
        expected = 0.660161815846869573927812110014 * x / (ln_x * ln_x)
        val = calculate_hardy_littlewood_expected_count(x)
        assert abs(val - expected) < 1e-6

    def test_small_x_returns_zero(self):
        assert calculate_hardy_littlewood_expected_count(0) == 0.0
        assert calculate_hardy_littlewood_expected_count(1) == 0.0
        assert calculate_hardy_littlewood_expected_count(2) == 0.0

    def test_monotone_growth(self):
        assert (calculate_hardy_littlewood_expected_count(10**6)
                < calculate_hardy_littlewood_expected_count(10**9))

    def test_float_input_accepted(self):
        val = calculate_hardy_littlewood_expected_count(1e9)
        assert val > 0 and math.isfinite(val)

    def test_invalid_type_raises(self):
        with pytest.raises(TypeError):
            calculate_hardy_littlewood_expected_count("1000")

    def test_nan_raises(self):
        with pytest.raises(ValueError):
            calculate_hardy_littlewood_expected_count(float("nan"))

    def test_consistency_with_legacy_alias(self):
        for x in (10**3, 10**6, 10**9):
            assert (calculate_hardy_littlewood_expected_count(x)
                    == pytest.approx(compute_hardy_littlewood_expected_count(x), rel=1e-12))