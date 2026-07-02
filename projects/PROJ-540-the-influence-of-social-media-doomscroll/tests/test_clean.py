"""
Unit tests for the data cleaning module (clean.py).

This module tests listwise deletion logic and power check enforcement.
"""
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import tempfile
import os
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))

from clean import (
    apply_listwise_deletion,
    check_power,
    clean_and_validate,
    REQUIRED_PREDICTORS,
    REQUIRED_OUTCOME,
    MIN_POWER_HARD_STOP,
    MIN_POWER_LOW_WARNING
)
from exceptions import PowerLimitationError

class TestCleaning:
    """Tests for the cleaning module."""

    def test_listwise_deletion_removes_rows_with_missing_values(self):
        """Verify that rows with missing critical values are removed."""
        # Create test data with some missing values
        data = {
            'news_exposure_freq': [1, 2, np.nan, 4, 5],
            'age': [25, 30, 35, np.nan, 45],
            'gender': ['M', 'F', 'M', 'F', np.nan],
            'anxiety_score': [10, 15, 20, 25, 30],
            'other_col': [1, 2, 3, 4, 5]  # Should be kept even if present
        }
        df = pd.DataFrame(data)
        
        # Apply listwise deletion
        cleaned_df = apply_listwise_deletion(df)
        
        # Should have 2 rows removed (rows 2, 3, 4 have missing values)
        # Actually: row 2 (news_exposure_freq), row 3 (age), row 4 (gender)
        # So 3 rows removed, 2 remaining
        assert len(cleaned_df) == 2
        assert 'other_col' in cleaned_df.columns

    def test_listwise_deletion_preserves_complete_rows(self):
        """Verify that complete rows are preserved."""
        data = {
            'news_exposure_freq': [1, 2, 3],
            'age': [25, 30, 35],
            'gender': ['M', 'F', 'M'],
            'anxiety_score': [10, 15, 20]
        }
        df = pd.DataFrame(data)
        
        cleaned_df = apply_listwise_deletion(df)
        
        assert len(cleaned_df) == 3
        pd.testing.assert_frame_equal(cleaned_df, df)

    def test_listwise_deletion_raises_error_on_missing_columns(self):
        """Verify that missing required columns raise an error."""
        data = {
            'news_exposure_freq': [1, 2, 3],
            'age': [25, 30, 35],
            # Missing 'gender' and 'anxiety_score'
        }
        df = pd.DataFrame(data)
        
        with pytest.raises(ValueError, match="Missing required columns"):
            apply_listwise_deletion(df)

    def test_check_power_raises_error_on_low_sample(self):
        """Verify that sample size < 30 raises PowerLimitationError."""
        # Create a small dataframe
        data = {
            'news_exposure_freq': list(range(20)),
            'age': list(range(20, 40)),
            'gender': ['M'] * 20,
            'anxiety_score': list(range(40, 60))
        }
        df = pd.DataFrame(data)
        
        with pytest.raises(PowerLimitationError, match="Power limitation"):
            check_power(df)

    def test_check_power_warns_on_marginal_sample(self, caplog):
        """Verify that sample size 30-99 logs a warning."""
        # Create a dataframe with 50 rows
        data = {
            'news_exposure_freq': list(range(50)),
            'age': list(range(50, 100)),
            'gender': ['M'] * 50,
            'anxiety_score': list(range(100, 150))
        }
        df = pd.DataFrame(data)
        
        with caplog.at_level("WARNING"):
            check_power(df)
        
        assert "Low Power Warning" in caplog.text

    def test_check_power_passes_on_sufficient_sample(self, caplog):
        """Verify that sample size >= 100 passes without warning."""
        # Create a dataframe with 100 rows
        data = {
            'news_exposure_freq': list(range(100)),
            'age': list(range(100, 200)),
            'gender': ['M'] * 100,
            'anxiety_score': list(range(200, 300))
        }
        df = pd.DataFrame(data)
        
        with caplog.at_level("WARNING"):
            check_power(df)
        
        assert "Low Power Warning" not in caplog.text
        assert "Power check passed" in caplog.text

    def test_clean_and_validate_integration(self):
        """Integration test for the full cleaning pipeline."""
        # Create temporary files
        with tempfile.TemporaryDirectory() as tmpdir:
            raw_path = Path(tmpdir) / "raw.csv"
            output_path = Path(tmpdir) / "cleaned.csv"
            
            # Create raw data with some missing values
            data = {
                'news_exposure_freq': [1, 2, np.nan, 4, 5, 6, 7, 8, 9, 10] * 4,  # 40 rows
                'age': list(range(40)),
                'gender': ['M'] * 40,
                'anxiety_score': list(range(40, 80)),
                'extra': ['x'] * 40
            }
            # Introduce missing values in some rows
            for i in [5, 15, 25, 35]:
                data['news_exposure_freq'][i] = np.nan
            
            df = pd.DataFrame(data)
            df.to_csv(raw_path, index=False)
            
            # Run cleaning
            cleaned_df, n = clean_and_validate(raw_path, output_path)
            
            # Verify output file exists
            assert output_path.exists()
            
            # Verify row count (4 missing rows removed)
            assert n == 36
            assert len(cleaned_df) == 36
            
            # Verify no missing values in critical columns
            assert cleaned_df[REQUIRED_PREDICTORS + [REQUIRED_OUTCOME]].isna().sum().sum() == 0

    def test_clean_and_validate_halts_on_insufficient_power(self):
        """Verify that cleaning halts if final sample is too small."""
        with tempfile.TemporaryDirectory() as tmpdir:
            raw_path = Path(tmpdir) / "raw.csv"
            output_path = Path(tmpdir) / "cleaned.csv"
            
            # Create raw data with many missing values to result in N < 30
            data = {
                'news_exposure_freq': [1, 2, np.nan, 4, np.nan] * 5,  # 25 rows, many missing
                'age': list(range(25)),
                'gender': ['M'] * 25,
                'anxiety_score': list(range(25, 50))
            }
            df = pd.DataFrame(data)
            df.to_csv(raw_path, index=False)
            
            # Should raise PowerLimitationError
            with pytest.raises(PowerLimitationError):
                clean_and_validate(raw_path, output_path)
            
            # Output file should not exist
            assert not output_path.exists()
