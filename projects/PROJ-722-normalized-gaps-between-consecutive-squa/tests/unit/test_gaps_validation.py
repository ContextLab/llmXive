"""
Unit tests for gaps validation logic (Task T016).

Verifies that the mean of normalized gaps is exactly 1.0 within tolerance (SC-001).
"""
import numpy as np
import pytest
from code.gaps import validate_normalized_gaps_mean, normalize_gaps


def test_normalize_gaps_mean_is_one():
    """
    Unit test: Verify normalization logic produces a mean of 1.0.
    
    This is a direct implementation of the independent test requirement for US1:
    "confirm mean of normalized gaps is 1.0".
    """
    # Create a simple list of gaps
    raw_gaps = [1, 2, 3, 4, 5]
    
    # Normalize them
    normalized = normalize_gaps(raw_gaps)
    
    # Verify the mean is 1.0
    mean_val = np.mean(normalized)
    assert abs(mean_val - 1.0) < 1e-9, f"Expected mean 1.0, got {mean_val}"


def test_validate_normalized_gaps_mean_passes():
    """
    Test that validate_normalized_gaps_mean returns True for valid data.
    """
    # Create normalized data that should have mean 1.0
    data = np.array([1.0, 1.0, 1.0, 1.0])
    
    result = validate_normalized_gaps_mean(data)
    assert result is True


def test_validate_normalized_gaps_mean_fails_outside_tolerance():
    """
    Test that validate_normalized_gaps_mean raises AssertionError when mean is outside tolerance.
    """
    # Create data with mean significantly different from 1.0
    data = np.array([1.0, 1.0, 2.0, 2.0])  # Mean is 1.5
    
    with pytest.raises(AssertionError) as exc_info:
        validate_normalized_gaps_mean(data, tolerance=1e-9)
    
    assert "Validation failed" in str(exc_info.value)
    assert "SC-001" in str(exc_info.value)


def test_validate_normalized_gaps_mean_edge_case_precision():
    """
    Test validation with floating point precision edge cases.
    """
    # Create data that is 1.0 but with floating point noise
    data = np.array([1.0 + 1e-12, 1.0 - 1e-12, 1.0])
    
    # Should pass with default tolerance (1e-9)
    result = validate_normalized_gaps_mean(data)
    assert result is True
    
    # Should fail with very tight tolerance
    with pytest.raises(AssertionError):
        validate_normalized_gaps_mean(data, tolerance=1e-13)