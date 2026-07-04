import pytest
import pandas as pd
import numpy as np
from scipy import stats
import sys
import os
import tempfile
from pathlib import Path

# Add code to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.data.preprocessing import _check_and_transform_ace_skewness

class TestACELogTransformation:
    """
    Unit tests for T017: ACE score skewness check and log-transformation.
    """

    def test_skewness_below_threshold_no_transform(self):
        """Test that data with skewness <= 1.0 is not transformed."""
        # Create a dataset with low skewness (approx normal)
        data = {
            "ACE": np.random.normal(loc=5, scale=2, size=100)
        }
        df = pd.DataFrame(data)
        
        original_skew = float(stats.skew(df["ACE"].dropna()))
        # Ensure we have low skewness for this test (might need retry logic in real scenario, 
        # but for unit test we assume the generated normal distribution is close enough or filter)
        if abs(original_skew) > 1.0:
            # Fallback: create perfectly symmetric data
            df = pd.DataFrame({"ACE": [1, 2, 3, 4, 5, 5, 4, 3, 2, 1] * 10})
            original_skew = float(stats.skew(df["ACE"].dropna()))
        
        df_result, skew_out = _check_and_transform_ace_skewness(df, "ACE")
        
        assert abs(skew_out) <= 1.0, "Test setup failed: skewness should be <= 1.0"
        assert "ACE_log" not in df_result.columns, "Log column should not be created if not transformed"
        # Values should be unchanged
        pd.testing.assert_series_equal(df_result["ACE"], df["ACE"])

    def test_skewness_above_threshold_log_transform(self):
        """Test that data with skewness > 1.0 is log-transformed."""
        # Create a highly right-skewed dataset (e.g., exponential)
        data = {
            "ACE": np.random.exponential(scale=2, size=1000) + 1 # +1 to avoid 0 if using log, though log1p handles 0
        }
        df = pd.DataFrame(data)
        
        original_skew = float(stats.skew(df["ACE"].dropna()))
        assert original_skew > 1.0, "Test setup failed: skewness should be > 1.0"
        
        df_result, skew_out = _check_and_transform_ace_skewness(df, "ACE")
        
        assert "ACE_log" in df_result.columns, "Log column should be created"
        assert df_result["ACE"].equals(df_result["ACE_log"]), "Main ACE column should be updated to log values"
        
        # Verify new skewness is reduced
        new_skew = float(stats.skew(df_result["ACE"].dropna()))
        assert new_skew < original_skew, "New skewness should be lower than original"
        # Note: We don't strictly assert new_skew <= 1.0 as log might not be enough for extreme cases,
        # but the task is to apply it if > 1.0.

    def test_skewness_negative_high(self):
        """Test that data with skewness < -1.0 is log-transformed."""
        # Create a highly left-skewed dataset
        # Invert exponential data
        data = {
            "ACE": 10 - np.random.exponential(scale=1, size=1000)
        }
        # Ensure non-negative for log1p if we assume ACE >= 0, but log1p handles -1 < x
        # If data goes below -1, log1p fails. Let's shift to be positive but left skewed.
        # Actually, standard ACE scores are non-negative. A left skew implies many high scores.
        # Let's create a distribution from 10 down to 1.
        data = {
            "ACE": 10 - np.random.exponential(scale=0.5, size=1000)
        }
        # Filter to keep positive
        df = pd.DataFrame(data)
        df = df[df["ACE"] > 0]
        
        if len(df) < 10:
            pytest.skip("Not enough data to generate left skew with positive values")
            
        original_skew = float(stats.skew(df["ACE"].dropna()))
        
        # If skew is not low enough, skip or adjust
        if original_skew >= -1.0:
            # Force a left skew manually
            df = pd.DataFrame({"ACE": [1, 1, 1, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10] * 10})
            # This is likely right skewed. Left skew needs high values frequent.
            df = pd.DataFrame({"ACE": [10, 10, 10, 10, 9, 8, 7, 6, 5, 4, 3, 2, 1] * 10})
            original_skew = float(stats.skew(df["ACE"].dropna()))
            
        if original_skew < -1.0:
            df_result, skew_out = _check_and_transform_ace_skewness(df, "ACE")
            assert "ACE_log" in df_result.columns
            # Log1p of positive numbers is valid
            assert not df_result["ACE"].equals(df["ACE"])

    def test_missing_column(self):
        """Test that missing column raises ValueError."""
        df = pd.DataFrame({"Other": [1, 2, 3]})
        with pytest.raises(ValueError):
            _check_and_transform_ace_skewness(df, "ACE")

    def test_empty_series(self):
        """Test handling of empty or all-NaN series."""
        df = pd.DataFrame({"ACE": [np.nan, np.nan]})
        df_result, skew_out = _check_and_transform_ace_skewness(df, "ACE")
        assert skew_out == 0.0
        # No transformation should happen
        assert "ACE_log" not in df_result.columns