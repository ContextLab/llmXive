import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import sys
import os

# Add code directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from data.loader import (
    LowPowerError,
    LowNumericColumnsError,
    RAMExceededError,
    check_sample_size,
    validate_numeric_columns,
    estimate_memory_usage,
    process_and_validate
)

class TestLowPowerValidation:
    """Tests for T005b: Sample size validation logic."""

    def test_check_sample_size_valid(self):
        """Test that a dataset with n >= 30 passes."""
        df = pd.DataFrame({
            'a': range(30),
            'b': range(30),
            'c': range(30),
            'd': range(30),
            'e': range(30)
        })
        # Should not raise
        check_sample_size(df)

    def test_check_sample_size_boundary(self):
        """Test that a dataset with exactly 30 rows passes."""
        df = pd.DataFrame({
            'a': range(30),
            'b': range(30),
            'c': range(30),
            'd': range(30),
            'e': range(30)
        })
        check_sample_size(df)

    def test_check_sample_size_invalid(self):
        """Test that a dataset with n < 30 raises LowPowerError."""
        df = pd.DataFrame({
            'a': range(29),
            'b': range(29),
            'c': range(29),
            'd': range(29),
            'e': range(29)
        })
        with pytest.raises(LowPowerError) as exc_info:
            check_sample_size(df)
        assert "Low Power Error" in str(exc_info.value)
        assert "29" in str(exc_info.value)

    def test_process_and_validate_halts_on_low_power(self):
        """Test that process_and_validate raises LowPowerError for small datasets."""
        df = pd.DataFrame({
            'a': range(10),
            'b': range(10),
            'c': range(10),
            'd': range(10),
            'e': range(10)
        })
        with pytest.raises(LowPowerError):
            process_and_validate(df, "test_dataset")

    def test_process_and_validate_success(self):
        """Test that a valid large dataset passes all checks."""
        df = pd.DataFrame({
            'a': range(100),
            'b': range(100),
            'c': range(100),
            'd': range(100),
            'e': range(100)
        })
        result = process_and_validate(df, "test_dataset")
        assert result is not None
        assert len(result) == 100

class TestNumericColumnValidation:
    """Tests for numeric column validation logic."""

    def test_validate_numeric_columns_valid(self):
        """Test validation with >= 5 numeric columns."""
        df = pd.DataFrame({
            'a': [1.0, 2.0],
            'b': [3.0, 4.0],
            'c': [5.0, 6.0],
            'd': [7.0, 8.0],
            'e': [9.0, 10.0],
            'f': ['string'] * 2  # Non-numeric
        })
        is_valid, cols = validate_numeric_columns(df)
        assert is_valid is True
        assert len(cols) == 5

    def test_validate_numeric_columns_invalid(self):
        """Test validation with < 5 numeric columns."""
        df = pd.DataFrame({
            'a': [1.0, 2.0],
            'b': [3.0, 4.0],
            'c': [5.0, 6.0],
            'd': ['string'] * 2,
            'e': ['string'] * 2
        })
        is_valid, cols = validate_numeric_columns(df)
        assert is_valid is False
        assert len(cols) == 3

class TestMemoryEstimation:
    """Tests for memory estimation logic."""

    def test_estimate_memory_usage(self):
        """Test memory estimation calculation."""
        df = pd.DataFrame({
            'a': np.random.rand(1000),
            'b': np.random.rand(1000)
        })
        mem_gb = estimate_memory_usage(df)
        assert mem_gb > 0
        # Should be small for this size
        assert mem_gb < 1.0