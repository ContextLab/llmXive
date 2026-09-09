"""
Unit tests for refactor_utils module.
"""
import pytest
import numpy as np
from code.utils.refactor_utils import (
    safe_divide,
    clamp,
    format_float,
    validate_positive,
    validate_non_negative,
    normalize_array,
    batch_process,
    merge_dicts,
    get_safe_value,
    validate_input_type,
    summarize_array,
    ValidationResult
)


class TestSafeDivide:
    """Tests for safe_divide function."""

    def test_normal_division(self):
        """Test normal division works correctly."""
        result = safe_divide(10.0, 2.0)
        assert result == 5.0

    def test_division_by_zero(self):
        """Test division by zero returns default."""
        result = safe_divide(10.0, 0.0)
        assert result == 0.0

    def test_division_by_near_zero(self):
        """Test division by near-zero returns default."""
        result = safe_divide(10.0, 1e-15)
        assert result == 0.0

    def test_array_division(self):
        """Test array division with zeros."""
        numerator = np.array([10.0, 20.0, 30.0])
        denominator = np.array([2.0, 0.0, 5.0])
        result = safe_divide(numerator, denominator)
        expected = np.array([5.0, 0.0, 6.0])
        np.testing.assert_array_almost_equal(result, expected)

    def test_custom_default(self):
        """Test custom default value for division by zero."""
        result = safe_divide(10.0, 0.0, default=99.0)
        assert result == 99.0


class TestClamp:
    """Tests for clamp function."""

    def test_clamp_min(self):
        """Test clamping to minimum."""
        result = clamp(5.0, min_val=10.0)
        assert result == 10.0

    def test_clamp_max(self):
        """Test clamping to maximum."""
        result = clamp(15.0, max_val=10.0)
        assert result == 10.0

    def test_clamp_range(self):
        """Test clamping within range."""
        result = clamp(5.0, min_val=0.0, max_val=10.0)
        assert result == 5.0

    def test_array_clamp(self):
        """Test array clamping."""
        arr = np.array([-5.0, 5.0, 15.0])
        result = clamp(arr, min_val=0.0, max_val=10.0)
        expected = np.array([0.0, 5.0, 10.0])
        np.testing.assert_array_almost_equal(result, expected)


class TestFormatFloat:
    """Tests for format_float function."""

    def test_standard_format(self):
        """Test standard float formatting."""
        result = format_float(3.14159265, precision=2)
        assert result == "3.14"

    def test_scientific_format(self):
        """Test scientific notation."""
        result = format_float(123456.0, precision=2, scientific=True)
        assert "e" in result.lower()

    def test_strip_zeros(self):
        """Test stripping trailing zeros."""
        result = format_float(3.140000, precision=6, strip_zeros=True)
        assert result == "3.14"


class TestValidatePositive:
    """Tests for validate_positive function."""

    def test_positive_value(self):
        """Test positive value passes."""
        result = validate_positive(5.0, name="test")
        assert result.is_valid

    def test_zero_strict(self):
        """Test zero fails strict validation."""
        result = validate_positive(0.0, name="test", strict=True)
        assert not result.is_valid

    def test_zero_non_strict(self):
        """Test zero passes non-strict validation."""
        result = validate_positive(0.0, name="test", strict=False)
        assert result.is_valid

    def test_negative_value(self):
        """Test negative value fails."""
        result = validate_positive(-1.0, name="test")
        assert not result.is_valid

    def test_array_positive(self):
        """Test array of positive values."""
        result = validate_positive(np.array([1.0, 2.0, 3.0]), name="test")
        assert result.is_valid

    def test_array_with_zero(self):
        """Test array with zero fails strict."""
        result = validate_positive(np.array([1.0, 0.0, 3.0]), name="test", strict=True)
        assert not result.is_valid


class TestNormalizeArray:
    """Tests for normalize_array function."""

    def test_minmax_normalization(self):
        """Test min-max normalization."""
        arr = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
        result = normalize_array(arr, method="minmax")
        expected = np.array([0.0, 0.25, 0.5, 0.75, 1.0])
        np.testing.assert_array_almost_equal(result, expected)

    def test_zscore_normalization(self):
        """Test z-score normalization."""
        arr = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
        result = normalize_array(arr, method="zscore")
        # Mean should be 0, std should be 1
        assert np.abs(np.mean(result)) < 1e-10
        assert np.abs(np.std(result) - 1.0) < 1e-10

    def test_unit_normalization(self):
        """Test unit norm normalization."""
        arr = np.array([3.0, 4.0])
        result = normalize_array(arr, method="unit")
        expected_norm = 1.0
        actual_norm = np.linalg.norm(result)
        assert np.abs(actual_norm - expected_norm) < 1e-10

    def test_invalid_method(self):
        """Test invalid method raises error."""
        with pytest.raises(ValueError):
            normalize_array(np.array([1.0, 2.0]), method="invalid")


class TestMergeDicts:
    """Tests for merge_dicts function."""

    def test_simple_merge(self):
        """Test simple dictionary merge."""
        d1 = {"a": 1, "b": 2}
        d2 = {"c": 3, "d": 4}
        result = merge_dicts(d1, d2)
        expected = {"a": 1, "b": 2, "c": 3, "d": 4}
        assert result == expected

    def test_overwrite_merge(self):
        """Test merge with overwrite."""
        d1 = {"a": 1, "b": 2}
        d2 = {"b": 20, "c": 3}
        result = merge_dicts(d1, d2, overwrite=True)
        expected = {"a": 1, "b": 20, "c": 3}
        assert result == expected

    def test_no_overwrite_merge(self):
        """Test merge without overwrite."""
        d1 = {"a": 1, "b": 2}
        d2 = {"b": 20, "c": 3}
        result = merge_dicts(d1, d2, overwrite=False)
        expected = {"a": 1, "b": 2, "c": 3}
        assert result == expected


class TestGetSafeValue:
    """Tests for get_safe_value function."""

    def test_existing_key(self):
        """Test getting existing key."""
        d = {"a": 1, "b": 2}
        result = get_safe_value(d, "a")
        assert result == 1

    def test_missing_key_default(self):
        """Test missing key returns default."""
        d = {"a": 1}
        result = get_safe_value(d, "b", default=99)
        assert result == 99

    def test_missing_key_required(self):
        """Test missing required key raises error."""
        d = {"a": 1}
        with pytest.raises(KeyError):
            get_safe_value(d, "b", required=True)


class TestValidateInputType:
    """Tests for validate_input_type function."""

    def test_correct_type(self):
        """Test correct type passes."""
        result = validate_input_type(5, int, name="test")
        assert result.is_valid

    def test_wrong_type(self):
        """Test wrong type fails."""
        result = validate_input_type("5", int, name="test")
        assert not result.is_valid
        assert "must be int" in result.message


class TestSummarizeArray:
    """Tests for summarize_array function."""

    def test_basic_summary(self):
        """Test basic array summary."""
        arr = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
        summary = summarize_array(arr, name="test")

        assert summary["name"] == "test"
        assert summary["shape"] == (5,)
        assert summary["min"] == 1.0
        assert summary["max"] == 5.0
        assert summary["mean"] == 3.0
        assert summary["nan_count"] == 0
        assert summary["inf_count"] == 0
