"""
Unit tests for code/data/loader.py
"""
import pytest
from data.loader import (
    RAMExceededError,
    LowNumericColumnsError,
    LowPowerError,
    estimate_memory_usage,
    validate_numeric_columns,
    check_sample_size
)

def test_low_power_error():
    """Test that LowPowerError is raised for small datasets."""
    with pytest.raises(LowPowerError):
        check_sample_size(n=10)

def test_low_numeric_columns_error():
    """Test that LowNumericColumnsError is raised for few numeric columns."""
    with pytest.raises(LowNumericColumnsError):
        validate_numeric_columns(numeric_count=2)

def test_estimate_memory_usage():
    """Test memory estimation function."""
    # Test with a simple case
    estimated = estimate_memory_usage(n_rows=1000, n_cols=10)
    assert estimated > 0
    assert isinstance(estimated, float)
