"""
Unit tests for preprocessing logic in src/ingestion/preprocess.py.
"""

import pytest
import pandas as pd
import numpy as np
from code.src.ingestion.preprocess import (
    weight_pct_to_atomic_pct,
    handle_synthesis_range,
    clean_column_name
)
from code.src.utils import constants


class TestWeightToAtomicConversion:
    """Tests for weight_pct_to_atomic_pct function."""

    def test_zero_weight_pct(self):
        """Test that 0% weight results in 0% atomic."""
        result = weight_pct_to_atomic_pct(0.0, "C")
        assert result == 0.0

    def test_known_conversion(self):
        """Test a known conversion manually calculated."""
        # Example: 10% weight of Carbon (12.01) in MgB2 (avg 15.308)
        # Moles C = 10 / 12.01 = 0.8326
        # Moles Host = 90 / 15.308 = 5.879
        # Total Moles = 6.7116
        # At% = (0.8326 / 6.7116) * 100 = 12.40%
        result = weight_pct_to_atomic_pct(10.0, "C")
        expected = 12.40
        assert abs(result - expected) < 0.05

    def test_high_weight_pct(self):
        """Test high weight percentage conversion."""
        result = weight_pct_to_atomic_pct(50.0, "Al") # Al = 26.98
        # Moles Al = 50/26.98 = 1.853
        # Moles Host = 50/15.308 = 3.266
        # Total = 5.119
        # At% = 1.853/5.119 = 36.2%
        assert 36.0 < result < 37.0

    def test_unknown_element(self):
        """Test behavior with unknown element."""
        result = weight_pct_to_atomic_pct(10.0, "X")
        # Should return NaN
        assert pd.isna(result)

    def test_negative_weight_pct(self):
        """Test negative weight percentage."""
        result = weight_pct_to_atomic_pct(-5.0, "C")
        assert result == 0.0


class TestSynthesisRange:
    """Tests for handle_synthesis_range function."""

    def test_single_value(self):
        """Test with a single numeric value."""
        assert handle_synthesis_range(10) == 10.0
        assert handle_synthesis_range(10.5) == 10.5

    def test_range_string(self):
        """Test with a range string."""
        assert handle_synthesis_range("10-20") == 15.0
        assert handle_synthesis_range("10 - 20") == 15.0
        assert handle_synthesis_range("5-15") == 10.0

    def test_invalid_string(self):
        """Test with invalid string."""
        assert np.isnan(handle_synthesis_range("abc"))
        assert np.isnan(handle_synthesis_range("10-"))
        assert np.isnan(handle_synthesis_range("-20"))

    def test_nan_input(self):
        """Test with NaN input."""
        assert np.isnan(handle_synthesis_range(np.nan))


class TestCleanColumnName:
    """Tests for clean_column_name function."""

    def test_lowercase(self):
        assert clean_column_name("Tc") == "tc"

    def test_strip_whitespace(self):
        assert clean_column_name("  tc  ") == "tc"

    def test_replace_spaces(self):
        assert clean_column_name("critical temperature") == "critical_temperature"

    def test_replace_special_chars(self):
        assert clean_column_name("impurity-weight") == "impurity_weight"
        assert clean_column_name("impurity/weight") == "impurity_weight"

    def test_non_string(self):
        assert clean_column_name(123) == "123"
