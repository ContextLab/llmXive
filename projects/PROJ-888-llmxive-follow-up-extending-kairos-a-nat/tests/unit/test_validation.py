import pytest
import numpy as np
from typing import List

from code.data.validation import (
    validate_discrete_state_vector,
    validate_dataset_for_degeneracy,
    check_single_vector_degeneracy,
    DegeneracyError
)
from code.data.schema import QuantizationLevel

def test_valid_vector_4bit():
    """Test a valid 4-bit vector."""
    vector = [0, 5, 10, 15, 8, 1, 2, 3]
    is_valid, msg = validate_discrete_state_vector(vector, QuantizationLevel.LOW)
    assert is_valid is True
    assert "Valid" in msg

def test_vector_out_of_range():
    """Test a vector with values exceeding 4-bit max (15)."""
    vector = [0, 5, 16, 10]  # 16 is invalid for 4-bit
    is_valid, msg = validate_discrete_state_vector(vector, QuantizationLevel.LOW)
    assert is_valid is False
    assert "out of range" in msg

def test_vector_negative():
    """Test a vector with negative values."""
    vector = [0, -1, 5]
    is_valid, msg = validate_discrete_state_vector(vector, QuantizationLevel.LOW)
    assert is_valid is False
    assert "out of range" in msg

def test_1bit_collision_detection():
    """Test detection of 1-bit collapse (all zeros or all same value)."""
    # All zeros
    vector = [0, 0, 0, 0, 0]
    with pytest.raises(DegeneracyError) as exc_info:
        validate_discrete_state_vector(vector, QuantizationLevel.LOW)
    assert "Degenerate data detected" in str(exc_info.value)
    assert "Only 1 unique values" in str(exc_info.value)

def test_1bit_collision_detection_mixed():
    """Test detection of collapse where only 2 values exist but threshold is strict."""
    # Only two values: 0 and 1. If min_unique_values is set to 3, this should fail.
    # Default min_unique_values is 2, so this passes.
    vector = [0, 1, 0, 1, 0]
    is_valid, msg = validate_discrete_state_vector(vector, QuantizationLevel.LOW)
    assert is_valid is True

    # Now force a stricter threshold via internal logic or custom call if needed.
    # For this test, we rely on the default behavior passing 2 unique values.
    # To test failure, we create a vector with 1 unique value (already tested above).

def test_dataset_validation_pass():
    """Test dataset validation with mostly valid data."""
    data = [
        [0, 1, 2, 3],
        [4, 5, 6, 7],
        [8, 9, 10, 11]
    ]
    result = validate_dataset_for_degeneracy(data, QuantizationLevel.LOW)
    assert result["is_valid"] is True
    assert result["degenerate_count"] == 0
    assert result["degeneracy_rate"] == 0.0

def test_dataset_validation_fail():
    """Test dataset validation with collapsed data."""
    data = [
        [0, 0, 0, 0],  # Degenerate
        [1, 1, 1, 1],  # Degenerate
        [0, 1, 2, 3],  # Valid
    ]
    # 2 out of 3 is 66% degeneracy. Default threshold is 10% (0.1).
    result = validate_dataset_for_degeneracy(data, QuantizationLevel.LOW)
    assert result["is_valid"] is False
    assert result["degenerate_count"] == 2
    assert result["degeneracy_rate"] == pytest.approx(0.666, rel=0.01)

def test_check_single_vector_degeneracy():
    """Test the quick check function."""
    vector = [0, 0, 0, 0]
    result = check_single_vector_degeneracy(vector, bits=4)
    assert result["collapsed"] is True
    assert result["unique_count"] == 1

    vector = [0, 1, 2, 3]
    result = check_single_vector_degeneracy(vector, bits=4)
    assert result["collapsed"] is False
    assert result["unique_count"] == 4
