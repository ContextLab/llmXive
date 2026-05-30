"""T007 — unit tests for verify/approximate.py (spec 018, T007/T008)."""

from __future__ import annotations

import math

import pytest

from llmxive.verify.approximate import (
    PrecisionSpec,
    correction,
    has_hedge,
    is_valid_rounding,
    parse_precision,
)


class TestParsePrecision:
    def test_two_decimals(self):
        p = parse_precision("3.14")
        assert p.decimals == 2
        assert p.claimed == pytest.approx(3.14)

    def test_zero_decimals(self):
        p = parse_precision("3")
        assert p.decimals == 0
        assert p.claimed == pytest.approx(3.0)

    def test_five_decimals(self):
        p = parse_precision("3.14159")
        assert p.decimals == 5
        assert p.claimed == pytest.approx(3.14159)

    def test_one_decimal(self):
        p = parse_precision("2.7")
        assert p.decimals == 1
        assert p.claimed == pytest.approx(2.7)

    def test_scientific_notation(self):
        p = parse_precision("3.0e8")
        assert p.claimed == pytest.approx(3.0e8)
        # sig_figs should be populated for scientific notation
        assert p.sig_figs >= 1

    def test_large_integer(self):
        p = parse_precision("299792458")
        assert p.decimals == 0
        assert p.claimed == pytest.approx(299792458.0)


class TestHasHedge:
    def test_about(self):
        assert has_hedge("pi is about 3") is True

    def test_approximately(self):
        assert has_hedge("approximately 3.14") is True

    def test_roughly(self):
        assert has_hedge("roughly 2.718") is True

    def test_tilde(self):
        assert has_hedge("the value is ~3.14") is True

    def test_approx_symbol(self):
        assert has_hedge("π ≈ 3.14") is True

    def test_around(self):
        assert has_hedge("around 6.28") is True

    def test_no_hedge(self):
        assert has_hedge("pi is 3.14") is False

    def test_no_hedge_plain(self):
        assert has_hedge("the count is 9988") is False


class TestIsValidRounding:
    def test_pi_two_decimals_exact(self):
        assert is_valid_rounding(3.14, math.pi, decimals=2, hedge=False) is True

    def test_pi_zero_decimals_hedge(self):
        # "pi is about 3" — hedge allows decimals±1
        assert is_valid_rounding(3, math.pi, decimals=0, hedge=True) is True

    def test_pi_two_decimals_wrong_exact(self):
        assert is_valid_rounding(3.15, math.pi, decimals=2, hedge=False) is False

    def test_e_one_decimal_wrong(self):
        # round(e, 1) = 2.7 ≠ 2.5
        assert is_valid_rounding(2.5, math.e, decimals=1, hedge=False) is False

    def test_e_one_decimal_correct(self):
        assert is_valid_rounding(2.7, math.e, decimals=1, hedge=False) is True

    def test_pi_five_decimals(self):
        # 3.14159 rounds to 3.14159 at 5 dp
        assert is_valid_rounding(3.14159, math.pi, decimals=5, hedge=False) is True

    def test_pi_wrong_hedge_still_fails_far_off(self):
        # 3.2 is not within even decimals±1=1dp of pi (round(pi,1)=3.1)
        assert is_valid_rounding(3.2, math.pi, decimals=2, hedge=True) is False

    def test_hedge_allows_one_less_decimal(self):
        # round(pi, 1) = 3.1 → claimed=3.1 with decimals=2 and hedge should pass
        assert is_valid_rounding(3.1, math.pi, decimals=2, hedge=True) is True

    def test_no_substring_comparison(self):
        # Confirm numeric compare: 3.141 claimed, round(pi,3)=3.142 → False
        assert is_valid_rounding(3.141, math.pi, decimals=3, hedge=False) is False

    def test_speed_of_light_zero_decimals(self):
        import scipy.constants
        # round(c, 0) = 299792458.0
        assert is_valid_rounding(299792458.0, scipy.constants.c, decimals=0, hedge=False) is True


class TestCorrection:
    def test_e_one_decimal(self):
        assert correction(math.e, decimals=1) == "2.7"

    def test_pi_zero_decimals(self):
        # round(pi, 0) = 3.0 → formatted as "3" (no trailing .0)
        assert correction(math.pi, decimals=0) == "3"

    def test_pi_two_decimals(self):
        assert correction(math.pi, decimals=2) == "3.14"

    def test_e_zero_decimals(self):
        # round(e, 0) = 3.0 → "3"
        assert correction(math.e, decimals=0) == "3"

    def test_two_point_seven(self):
        # Already a clean value
        assert correction(2.7, decimals=1) == "2.7"

    def test_no_trailing_dot_zero(self):
        result = correction(math.pi, decimals=0)
        assert "." not in result or not result.endswith(".0")
