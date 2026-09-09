import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import sys
import os

# Add code directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from data.validation import validate_feature_matrix, clean_or_drop_missing

class TestValidateFeatureMatrix:
    
    def test_no_missing_values(self):
        """Test validation passes when no missing values exist."""
        df = pd.DataFrame({
            'feature_a': [1.0, 2.0, 3.0],
            'feature_b': [4.0, 5.0, 6.0],
            'feature_c': [7.0, 8.0, 9.0]
        })
        features = ['feature_a', 'feature_b', 'feature_c']
        
        is_valid, missing_cols, summary = validate_feature_matrix(df, features)
        
        assert is_valid is True
        assert len(missing_cols) == 0
        assert all(v == 0 for v in summary.values())

    def test_missing_values_detected(self):
        """Test validation detects missing values."""
        df = pd.DataFrame({
            'feature_a': [1.0, np.nan, 3.0],
            'feature_b': [4.0, 5.0, 6.0],
            'feature_c': [7.0, 8.0, np.nan]
        })
        features = ['feature_a', 'feature_b', 'feature_c']
        
        is_valid, missing_cols, summary = validate_feature_matrix(df, features)
        
        assert is_valid is False
        assert 'feature_a' in missing_cols
        assert 'feature_c' in missing_cols
        assert 'feature_b' not in missing_cols
        assert summary['feature_a'] == 1
        assert summary['feature_c'] == 1

    def test_missing_column_in_features(self):
        """Test validation fails if a required feature column is missing from DataFrame."""
        df = pd.DataFrame({
            'feature_a': [1.0, 2.0],
            'feature_b': [3.0, 4.0]
        })
        features = ['feature_a', 'feature_b', 'feature_missing']
        
        is_valid, missing_cols, _ = validate_feature_matrix(df, features)
        
        assert is_valid is False
        assert 'feature_missing' in missing_cols

    def test_empty_dataframe(self):
        """Test validation handles empty DataFrame."""
        df = pd.DataFrame()
        features = ['feature_a']
        
        is_valid, missing_cols, _ = validate_feature_matrix(df, features)
        
        assert is_valid is False
        assert len(missing_cols) > 0

class TestCleanOrDropMissing:
    
    def test_drop_mode_no_missing(self):
        """Test drop mode returns original df when no missing values."""
        df = pd.DataFrame({
            'feature_a': [1.0, 2.0, 3.0],
            'feature_b': [4.0, 5.0, 6.0]
        })
        features = ['feature_a', 'feature_b']
        
        cleaned_df, dropped_count = clean_or_drop_missing(df, features, mode="drop")
        
        assert len(cleaned_df) == 3
        assert dropped_count == 0
        assert cleaned_df.equals(df)

    def test_drop_mode_with_missing(self):
        """Test drop mode removes rows with missing values."""
        df = pd.DataFrame({
            'feature_a': [1.0, np.nan, 3.0, 4.0],
            'feature_b': [4.0, 5.0, np.nan, 7.0],
            'feature_c': [8.0, 9.0, 10.0, 11.0]
        })
        features = ['feature_a', 'feature_b', 'feature_c']
        
        cleaned_df, dropped_count = clean_or_drop_missing(df, features, mode="drop")
        
        # Row 1 (index 1) has NaN in feature_a, Row 2 (index 2) has NaN in feature_b
        # Both should be dropped
        assert len(cleaned_df) == 2
        assert dropped_count == 2
        
        # Check remaining rows have no NaN in features
        assert cleaned_df['feature_a'].notna().all()
        assert cleaned_df['feature_b'].notna().all()

    def test_error_mode_with_missing(self):
        """Test error mode raises ValueError when missing values exist."""
        df = pd.DataFrame({
            'feature_a': [1.0, np.nan, 3.0],
            'feature_b': [4.0, 5.0, 6.0]
        })
        features = ['feature_a', 'feature_b']
        
        with pytest.raises(ValueError, match="Missing values found"):
            clean_or_drop_missing(df, features, mode="error")

    def test_error_mode_no_missing(self):
        """Test error mode passes when no missing values."""
        df = pd.DataFrame({
            'feature_a': [1.0, 2.0],
            'feature_b': [3.0, 4.0]
        })
        features = ['feature_a', 'feature_b']
        
        cleaned_df, dropped_count = clean_or_drop_missing(df, features, mode="error")
        
        assert len(cleaned_df) == 2
        assert dropped_count == 0
