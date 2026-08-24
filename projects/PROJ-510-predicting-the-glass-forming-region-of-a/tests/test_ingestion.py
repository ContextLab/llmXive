import pytest
import pandas as pd
import numpy as np
import os
import sys

# Ensure code directory is in path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'code'))

from ingestion import validate_critical_cooling_rate, MIN_ROWS

class TestValidation:
    """Tests for T017: Validation of critical_cooling_rate variance and count."""

    def test_validation_passes_with_sufficient_data_and_variance(self):
        """Test that validation passes when conditions are met."""
        data = {
            'critical_cooling_rate': [10.0, 20.0, 30.0, 40.0, 50.0] * 200  # 1000 rows, high variance
        }
        df = pd.DataFrame(data)
        # Should not raise
        validate_critical_cooling_rate(df)

    def test_validation_fails_low_count(self):
        """Test that validation fails if count < 500."""
        # Create exactly 499 rows
        data = {
            'critical_cooling_rate': [10.0] * 499
        }
        df = pd.DataFrame(data)
        with pytest.raises(ValueError) as exc_info:
            validate_critical_cooling_rate(df)
        assert "entries" in str(exc_info.value).lower()
        assert str(MIN_ROWS) in str(exc_info.value)

    def test_validation_fails_zero_variance(self):
        """Test that validation fails if variance is zero or near-zero."""
        # Create 1000 rows with same value (zero variance)
        data = {
            'critical_cooling_rate': [10.0] * 1000
        }
        df = pd.DataFrame(data)
        with pytest.raises(ValueError) as exc_info:
            validate_critical_cooling_rate(df)
        assert "variance" in str(exc_info.value).lower()

    def test_validation_fails_nan_variance(self):
        """Test that validation fails if variance is NaN (e.g., single row or all NaN)."""
        # Single row -> variance is NaN
        data = {
            'critical_cooling_rate': [10.0]
        }
        df = pd.DataFrame(data)
        with pytest.raises(ValueError) as exc_info:
            validate_critical_cooling_rate(df)
        # Should fail on count first, but if count was enough and variance NaN, it should fail on variance
        # Let's test a case with >500 rows but all NaN
        data_nan = {
            'critical_cooling_rate': [np.nan] * 1000
        }
        df_nan = pd.DataFrame(data_nan)
        # Note: dropna usually happens before this, but if passed here:
        # variance of all NaN is NaN
        with pytest.raises(ValueError):
            validate_critical_cooling_rate(df_nan)

    def test_validation_fails_missing_column(self):
        """Test that validation fails if the column is missing."""
        df = pd.DataFrame({'other_col': [1, 2, 3]})
        with pytest.raises(ValueError) as exc_info:
            validate_critical_cooling_rate(df)
        assert "not found" in str(exc_info.value).lower()
