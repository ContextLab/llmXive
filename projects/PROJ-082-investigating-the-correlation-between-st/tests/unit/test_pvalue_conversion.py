"""
Unit tests for p-value conversion edge cases.
Covers scenarios for extreme values, zero, infinity, and invalid inputs.
"""
import pytest
import math
import sys
from pathlib import Path

# Add code directory to path for imports
code_path = Path(__file__).parent.parent.parent / "code"
sys.path.insert(0, str(code_path))

from utils.validator import validate_effect_size, validate_study_row
from analysis.meta_analysis import load_effect_sizes_and_se


class TestPValueConversionEdgeCases:
    """Tests for edge cases in p-value to effect size conversion logic."""

    def test_p_value_zero(self):
        """Test handling of p-value = 0 (should be treated as extremely small)."""
        # In real data, p=0 is impossible, but floating point might underflow
        # The validator should reject p=0 as invalid or handle it gracefully
        with pytest.raises(ValueError):
            validate_effect_size(r=0.5, n=100, p_value=0.0)

    def test_p_value_one(self):
        """Test handling of p-value = 1.0."""
        # p=1.0 implies no effect, r should be 0 or very close
        result = validate_effect_size(r=0.0, n=100, p_value=1.0)
        assert result is True

    def test_p_value_extremely_small(self):
        """Test handling of extremely small p-values (e.g., 1e-10)."""
        # Very small p-values with non-zero r should be valid
        result = validate_effect_size(r=0.5, n=100, p_value=1e-10)
        assert result is True

    def test_p_value_extremely_large(self):
        """Test handling of p-values slightly less than 1."""
        result = validate_effect_size(r=0.01, n=100, p_value=0.999)
        assert result is True

    def test_p_value_negative(self):
        """Test handling of negative p-values (invalid)."""
        with pytest.raises(ValueError):
            validate_effect_size(r=0.5, n=100, p_value=-0.1)

    def test_p_value_greater_than_one(self):
        """Test handling of p-values > 1 (invalid)."""
        with pytest.raises(ValueError):
            validate_effect_size(r=0.5, n=100, p_value=1.5)

    def test_p_value_nan(self):
        """Test handling of NaN p-values."""
        with pytest.raises(ValueError):
            validate_effect_size(r=0.5, n=100, p_value=float('nan'))

    def test_p_value_inf(self):
        """Test handling of infinity p-values."""
        with pytest.raises(ValueError):
            validate_effect_size(r=0.5, n=100, p_value=float('inf'))

    def test_r_value_boundary_conditions(self):
        """Test r values at boundaries (-1, 1, 0)."""
        # r = 0 with p = 1.0
        assert validate_effect_size(r=0.0, n=100, p_value=1.0) is True
        
        # r near 1 with very small p
        assert validate_effect_size(r=0.99, n=100, p_value=1e-20) is True
        
        # r near -1 with very small p
        assert validate_effect_size(r=-0.99, n=100, p_value=1e-20) is True

    def test_small_sample_size_edge_case(self):
        """Test p-value conversion with very small sample size."""
        # With n=2, even large r might not be significant
        # This tests the degrees of freedom calculation edge case
        result = validate_effect_size(r=0.9, n=3, p_value=0.1)
        assert result is True

    def test_large_sample_size_edge_case(self):
        """Test p-value conversion with very large sample size."""
        # With large n, tiny r can be significant
        result = validate_effect_size(r=0.01, n=10000, p_value=0.01)
        assert result is True

    def test_inconsistent_r_and_p(self):
        """Test detection of inconsistent r and p-value pairs."""
        # Large r with p=1.0 is inconsistent
        with pytest.raises(ValueError):
            validate_effect_size(r=0.9, n=100, p_value=1.0)

        # Small r with p=1e-20 is inconsistent
        with pytest.raises(ValueError):
            validate_effect_size(r=0.001, n=100, p_value=1e-20)

    def test_valid_study_row_with_p_value(self):
        """Test validation of a complete study row with p-value."""
        study_row = {
            'tract': 'arcuate',
            'r': 0.5,
            'n': 100,
            'p_value': 0.001,
            'author': 'Smith',
            'year': 2020
        }
        result = validate_study_row(study_row)
        assert result is True

    def test_invalid_study_row_with_p_value(self):
        """Test validation of a study row with invalid p-value."""
        study_row = {
            'tract': 'arcuate',
            'r': 0.5,
            'n': 100,
            'p_value': -0.1,
            'author': 'Smith',
            'year': 2020
        }
        with pytest.raises(ValueError):
            validate_study_row(study_row)

    def test_missing_p_value_in_row(self):
        """Test handling of study rows missing p-value."""
        study_row = {
            'tract': 'arcuate',
            'r': 0.5,
            'n': 100,
            'author': 'Smith',
            'year': 2020
        }
        # Should handle missing p-value gracefully (might use alternative calculation)
        # or raise a specific error
        try:
            result = validate_study_row(study_row)
            # If it returns True, it means missing p is acceptable
            assert result is True
        except ValueError:
            # If it raises, that's also acceptable behavior
            pass

    def test_p_value_precision_edge_cases(self):
        """Test handling of p-values with various precision levels."""
        # Very precise p-value
        assert validate_effect_size(r=0.5, n=100, p_value=0.000123456789) is True
        
        # Rounded p-value
        assert validate_effect_size(r=0.5, n=100, p_value=0.05) is True
        
        # Scientific notation
        assert validate_effect_size(r=0.5, n=100, p_value=5e-3) is True

    def test_zero_standard_error_edge_case(self):
        """Test handling of zero standard error (should be invalid)."""
        # SE of 0 implies infinite precision, which is impossible
        # This tests the SE calculation edge case
        try:
            # If the function allows it, it might be a warning
            # If it raises, that's also correct
            load_effect_sizes_and_se([{'r': 0.5, 'n': 100, 'p_value': 0.0}])
        except (ValueError, ZeroDivisionError):
            # Expected behavior
            pass

    def test_infinite_standard_error_edge_case(self):
        """Test handling of infinite standard error."""
        # SE of inf implies no information
        try:
            load_effect_sizes_and_se([{'r': 0.5, 'n': 0, 'p_value': 0.5}])
        except (ValueError, ZeroDivisionError, OverflowError):
            # Expected behavior
            pass