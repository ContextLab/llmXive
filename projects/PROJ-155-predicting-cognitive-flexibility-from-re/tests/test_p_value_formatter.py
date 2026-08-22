"""
Tests for p-value formatting logic (Task T032).
"""
import pytest
import numpy as np
from code.analysis.p_value_formatter import format_p_value, format_p_value_float, is_significant

class TestPValueFormatting:
    def test_p_value_zero(self):
        """Test that p=0.0 is formatted as '< 0.0001'."""
        result = format_p_value(0.0)
        assert result == "< 0.0001"

    def test_p_value_below_threshold(self):
        """Test that p < 0.0001 is formatted as '< 0.0001'."""
        result = format_p_value(0.00005)
        assert result == "< 0.0001"

    def test_p_value_normal(self):
        """Test normal p-value formatting."""
        result = format_p_value(0.04567)
        assert result == "0.0457"
        
        result = format_p_value(0.99)
        assert result == "0.9900"

    def test_p_value_numpy_float(self):
        """Test handling of numpy float types."""
        result = format_p_value(np.float64(0.0))
        assert result == "< 0.0001"
        
        result = format_p_value(np.float32(0.0234))
        assert result == "0.0234"

    def test_p_value_float_cap(self):
        """Test that format_p_value_float returns a non-zero floor."""
        result = format_p_value_float(0.0)
        assert result == 0.0001
        
        result = format_p_value_float(0.0005)
        assert result == 0.0005

    def test_is_significant(self):
        """Test significance checking."""
        assert is_significant(0.04) is True
        assert is_significant(0.05) is False
        assert is_significant(0.0) is True
        assert is_significant(0.06) is False

    def test_is_significant_custom_alpha(self):
        """Test significance with custom alpha."""
        assert is_significant(0.04, alpha=0.01) is False
        assert is_significant(0.005, alpha=0.01) is True
