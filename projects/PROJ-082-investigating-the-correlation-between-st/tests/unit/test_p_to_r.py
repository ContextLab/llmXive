"""
Unit tests for p-value to r conversion (Task T040).
"""
import math
import pytest
from pathlib import Path
import sys

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from code.analysis.p_to_r import (
    p_to_t,
    t_to_r,
    convert_p_to_r,
    convert_t_to_r,
    process_row,
    DataConversionError
)

class TestPtoT:
    """Tests for p-value to t-statistic conversion."""

    def test_valid_two_tailed(self):
        """Test valid two-tailed p-value conversion."""
        # For df=20, p=0.05 two-tailed -> t ≈ 2.086
        t_val = p_to_t(0.05, 20, two_tailed=True)
        assert abs(t_val - 2.086) < 0.01

    def test_valid_one_tailed(self):
        """Test valid one-tailed p-value conversion."""
        # For df=20, p=0.025 one-tailed -> t ≈ 2.086 (same as 0.05 two-tailed)
        t_val = p_to_t(0.025, 20, two_tailed=False)
        assert abs(t_val - 2.086) < 0.01

    def test_invalid_p_value_zero(self):
        """Test that p=0 raises an error."""
        with pytest.raises(DataConversionError):
            p_to_t(0.0, 20)

    def test_invalid_p_value_one(self):
        """Test that p=1 raises an error."""
        with pytest.raises(DataConversionError):
            p_to_t(1.0, 20)

    def test_invalid_p_value_negative(self):
        """Test that p<0 raises an error."""
        with pytest.raises(DataConversionError):
            p_to_t(-0.1, 20)

    def test_invalid_df(self):
        """Test that invalid df raises an error."""
        with pytest.raises(DataConversionError):
            p_to_t(0.05, 0)

    def test_invalid_df_negative(self):
        """Test that negative df raises an error."""
        with pytest.raises(DataConversionError):
            p_to_t(0.05, -5)

class TestTtoR:
    """Tests for t-statistic to r conversion."""

    def test_positive_t(self):
        """Test positive t-statistic conversion."""
        # t=2, df=20 -> r = sqrt(4 / (4+20)) = sqrt(4/24) ≈ 0.408
        r_val = t_to_r(2.0, 20)
        expected = math.sqrt(4 / 24)
        assert abs(r_val - expected) < 1e-6

    def test_negative_t(self):
        """Test negative t-statistic conversion (sign preservation)."""
        r_val = t_to_r(-2.0, 20)
        expected = -math.sqrt(4 / 24)
        assert abs(r_val - expected) < 1e-6

    def test_zero_t(self):
        """Test t=0 conversion."""
        r_val = t_to_r(0.0, 20)
        assert r_val == 0.0

    def test_invalid_df(self):
        """Test that invalid df raises an error."""
        with pytest.raises(DataConversionError):
            t_to_r(2.0, 0)

class TestConvertPtoR:
    """Tests for direct p-value to r conversion."""

    def test_valid_conversion(self):
        """Test valid p-value to r conversion."""
        # p=0.05 two-tailed, df=20 -> t≈2.086 -> r≈0.41
        r_val = convert_p_to_r(0.05, 20, two_tailed=True)
        assert 0.40 < r_val < 0.42

    def test_invalid_p(self):
        """Test that invalid p raises error."""
        with pytest.raises(DataConversionError):
            convert_p_to_r(1.5, 20)

class TestProcessRow:
    """Tests for row processing logic."""

    def test_existing_r(self):
        """Test row with existing valid r."""
        row = {'r': '0.5', 'author': 'Test', 'year': '2020'}
        r_val, method = process_row(row)
        assert r_val == 0.5
        assert method == 'existing'

    def test_existing_r_invalid(self):
        """Test row with invalid r (>1)."""
        row = {'r': '1.5', 'author': 'Test', 'year': '2020'}
        r_val, method = process_row(row)
        assert r_val is None
        assert 'invalid' in method

    def test_from_t(self):
        """Test conversion from t-statistic."""
        row = {'t': '2.0', 'n': '22', 'author': 'Test', 'year': '2020'}
        # df = n - 2 = 20
        r_val, method = process_row(row)
        assert r_val is not None
        assert method == 'from_t'

    def test_from_p(self):
        """Test conversion from p-value."""
        row = {'p': '0.05', 'n': '22', 'author': 'Test', 'year': '2020'}
        r_val, method = process_row(row)
        assert r_val is not None
        assert method == 'from_p'

    def test_missing_df_and_n(self):
        """Test row missing both df and n."""
        row = {'p': '0.05', 'author': 'Test', 'year': '2020'}
        r_val, method = process_row(row)
        assert r_val is None
        assert method == 'missing_df'

    def test_missing_stats(self):
        """Test row with no stats."""
        row = {'author': 'Test', 'year': '2020'}
        r_val, method = process_row(row)
        assert r_val is None
        assert method == 'missing_stats'

    def test_from_p_one_tailed(self):
        """Test conversion from one-tailed p-value."""
        row = {'p': '0.025', 'n': '22', 'two_tailed': 'false', 'author': 'Test', 'year': '2020'}
        r_val, method = process_row(row)
        assert r_val is not None
        assert method == 'from_p'

class TestEdgeCases:
    """Edge case tests."""

    def test_large_t(self):
        """Test very large t-statistic (r approaches 1)."""
        r_val = t_to_r(100.0, 20)
        assert r_val > 0.99

    def test_small_p(self):
        """Test very small p-value."""
        r_val = convert_p_to_r(0.0001, 20)
        assert r_val > 0.6

    def test_parse_error_t(self):
        """Test parse error for t-statistic."""
        row = {'t': 'abc', 'n': '22', 'author': 'Test', 'year': '2020'}
        r_val, method = process_row(row)
        assert r_val is None
        assert method == 'parse_error'

    def test_parse_error_p(self):
        """Test parse error for p-value."""
        row = {'p': 'abc', 'n': '22', 'author': 'Test', 'year': '2020'}
        r_val, method = process_row(row)
        assert r_val is None
        assert method == 'parse_error'