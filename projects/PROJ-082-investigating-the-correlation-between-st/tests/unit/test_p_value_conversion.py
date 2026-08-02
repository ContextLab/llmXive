"""
Unit tests for p-value conversion edge cases.
Covers: zero p-values, p=1.0, invalid inputs, two-tailed conversion,
and boundary conditions for Fisher's Z transformation.
"""

import math
import pytest
import sys
from pathlib import Path

# Add project root to path if running from tests/
project_root = Path(__file__).parent.parent.parent
if str(project_root / "code") not in sys.path:
    sys.path.insert(0, str(project_root / "code"))

from extraction.p_value_converter import p_to_z_two_tailed, convert_p_value_to_effect_size


class TestPValueToZTwoTailed:
    """Tests for the p_to_z_two_tailed function."""

    def test_p_value_one(self):
        """When p=1.0, z should be 0.0."""
        assert math.isclose(p_to_z_two_tailed(1.0), 0.0, rel_tol=1e-9)

    def test_p_value_half(self):
        """When p=0.5, z should be approximately 0.6745."""
        z = p_to_z_two_tailed(0.5)
        assert math.isclose(z, 0.67448975, rel_tol=1e-4)

    def test_p_value_small(self):
        """When p is very small, z should be large positive."""
        z = p_to_z_two_tailed(0.001)
        assert z > 3.0  # z ~ 3.29

    def test_p_value_boundary_zero(self):
        """p=0.0 should raise ValueError (infinite z)."""
        with pytest.raises(ValueError):
            p_to_z_two_tailed(0.0)

    def test_p_value_boundary_very_small(self):
        """Very small p should produce large but finite z."""
        z = p_to_z_two_tailed(1e-10)
        assert z > 6.0

    def test_p_value_invalid_negative(self):
        """Negative p-value should raise ValueError."""
        with pytest.raises(ValueError):
            p_to_z_two_tailed(-0.1)

    def test_p_value_invalid_greater_than_one(self):
        """p > 1.0 should raise ValueError."""
        with pytest.raises(ValueError):
            p_to_p_value_to_effect_size(1.5)

    def test_p_value_invalid_type(self):
        """Non-numeric input should raise TypeError."""
        with pytest.raises(TypeError):
            p_to_z_two_tailed("0.05")

    def test_p_value_null(self):
        """None input should raise TypeError."""
        with pytest.raises(TypeError):
            p_to_z_two_tailed(None)


class TestConvertPValueToEffectSize:
    """Tests for the convert_p_value_to_effect_size function."""

    def test_basic_conversion(self):
        """Basic p=0.05 should yield r ~ 0.34."""
        r, z = convert_p_value_to_effect_size(0.05, n=30)
        assert math.isclose(r, 0.34, abs_tol=0.01)
        assert z > 0

    def test_p_value_one(self):
        """p=1.0 should yield r=0."""
        r, z = convert_p_value_to_effect_size(1.0, n=30)
        assert math.isclose(r, 0.0, rel_tol=1e-9)
        assert math.isclose(z, 0.0, rel_tol=1e-9)

    def test_p_value_small(self):
        """Small p should yield high positive r."""
        r, z = convert_p_value_to_effect_size(0.001, n=50)
        assert r > 0.5

    def test_p_value_boundary_zero(self):
        """p=0.0 should raise ValueError."""
        with pytest.raises(ValueError):
            convert_p_value_to_effect_size(0.0, n=30)

    def test_p_value_invalid_negative(self):
        """Negative p should raise ValueError."""
        with pytest.raises(ValueError):
            convert_p_value_to_effect_size(-0.1, n=30)

    def test_p_value_invalid_greater_than_one(self):
        """p > 1.0 should raise ValueError."""
        with pytest.raises(ValueError):
            convert_p_value_to_effect_size(1.5, n=30)

    def test_invalid_n(self):
        """n <= 0 should raise ValueError."""
        with pytest.raises(ValueError):
            convert_p_value_to_effect_size(0.05, n=0)

        with pytest.raises(ValueError):
            convert_p_value_to_effect_size(0.05, n=-5)

    def test_invalid_n_type(self):
        """Non-integer n should raise TypeError."""
        with pytest.raises(TypeError):
            convert_p_value_to_effect_size(0.05, n="30")

    def test_n_very_small(self):
        """Very small n should still work but yield large SE."""
        r, z = convert_p_value_to_effect_size(0.05, n=3)
        assert r > 0

    def test_large_n(self):
        """Large n should yield stable estimates."""
        r, z = convert_p_value_to_effect_size(0.05, n=10000)
        assert 0.01 < r < 0.1  # r should be small but significant

    def test_null_p(self):
        """None p should raise TypeError."""
        with pytest.raises(TypeError):
            convert_p_value_to_effect_size(None, n=30)

    def test_null_n(self):
        """None n should raise TypeError."""
        with pytest.raises(TypeError):
            convert_p_value_to_effect_size(0.05, None)

    def test_p_value_as_string(self):
        """String p-value should raise TypeError (no implicit conversion)."""
        with pytest.raises(TypeError):
            convert_p_value_to_effect_size("0.05", n=30)

    def test_p_value_very_close_to_zero(self):
        """p=1e-15 should work but yield very large r."""
        r, z = convert_p_value_to_effect_size(1e-15, n=100)
        assert r > 0.9  # Very strong correlation

    def test_p_value_very_close_to_one(self):
        """p=0.9999 should yield very small r."""
        r, z = convert_p_value_to_effect_size(0.9999, n=100)
        assert math.isclose(r, 0.0, abs_tol=0.01)

    def test_consistency_with_manual_calculation(self):
        """Verify conversion matches manual Fisher's Z calculation."""
        p = 0.05
        n = 50
        r, z = convert_p_value_to_effect_size(p, n)

        # Manual calculation:
        # z = inverse_normal_cdf(1 - p/2)
        # r = tanh(z / sqrt(n - 3))
        from scipy.stats import norm
        z_manual = norm.ppf(1 - p / 2)
        r_manual = math.tanh(z_manual / math.sqrt(n - 3))

        assert math.isclose(r, r_manual, rel_tol=1e-6)
        assert math.isclose(z, z_manual, rel_tol=1e-6)

    def test_two_tailed_assumption(self):
        """Verify the function assumes two-tailed test (standard)."""
        # For a two-tailed test at p=0.05, z should be ~1.96
        # Our function uses norm.ppf(1 - p/2) which is correct for two-tailed
        r, z = convert_p_value_to_effect_size(0.05, n=100)
        from scipy.stats import norm
        z_expected = norm.ppf(1 - 0.05 / 2)
        assert math.isclose(z, z_expected, rel_tol=1e-5)

    def test_edge_case_n_equals_three(self):
        """n=3 is the minimum for Fisher's Z (df=0)."""
        # This should technically work but SE is undefined (division by zero in SE calc)
        # However, our function only uses n for tanh scaling, not SE
        r, z = convert_p_value_to_effect_size(0.05, n=3)
        assert r > 0

    def test_extreme_p_values(self):
        """Test behavior at extreme p values."""
        # p=0.0000001
        r1, _ = convert_p_value_to_effect_size(1e-7, n=100)
        assert r1 > 0.8

        # p=0.9999999
        r2, _ = convert_p_value_to_effect_size(0.9999999, n=100)
        assert r2 < 0.1