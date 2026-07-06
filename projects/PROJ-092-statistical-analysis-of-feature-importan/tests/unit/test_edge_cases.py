"""
Unit tests for edge cases: missing data and model failure scenarios.
"""
import pytest
import numpy as np
import pandas as pd
from pathlib import Path
import tempfile
import json
import os
import sys

# Add code directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from preprocess import handle_missing_values, check_variance, split_into_windows
from train_and_importance import validate_model_performance, train_model, calculate_importance
from utils.config import get_config


class TestMissingDataEdgeCases:
    """Tests for handling missing data scenarios."""

    def test_handle_missing_values_median_imputation(self):
        """Test that missing values are correctly imputed with median."""
        df = pd.DataFrame({
            'feature1': [1.0, 2.0, np.nan, 4.0],
            'feature2': [10.0, np.nan, 30.0, 40.0],
            'target': [100, 200, 300, 400]
        })

        result = handle_missing_values(df, strategy='median')

        # Check that no NaN values remain
        assert not result.isnull().any().any()
        
        # Check that imputed values are medians
        # feature1 median of [1, 2, 4] is 2
        assert result.loc[2, 'feature1'] == 2.0
        # feature2 median of [10, 30, 40] is 30
        assert result.loc[1, 'feature2'] == 30.0

    def test_handle_missing_values_all_nan_column(self):
        """Test handling of a column where all values are missing."""
        df = pd.DataFrame({
            'feature1': [1.0, 2.0, 3.0],
            'feature2': [np.nan, np.nan, np.nan],
            'target': [100, 200, 300]
        })

        # This should raise a warning or handle gracefully
        # For now, we expect it to fill with 0.0 or similar
        result = handle_missing_values(df, strategy='median')
        
        # The column should be filled with 0.0 (pandas default for empty median)
        assert not result['feature2'].isnull().any()

    def test_handle_missing_values_no_missing(self):
        """Test that data without missing values is returned unchanged."""
        df = pd.DataFrame({
            'feature1': [1.0, 2.0, 3.0],
            'feature2': [10.0, 20.0, 30.0],
            'target': [100, 200, 300]
        })

        result = handle_missing_values(df, strategy='median')
        
        pd.testing.assert_frame_equal(result, df)

class TestVarianceEdgeCases:
    """Tests for variance checking and zero-variance feature dropping."""

    def test_check_variance_zero_var_feature(self):
        """Test that zero-variance features are detected and dropped."""
        df = pd.DataFrame({
            'feature1': [1.0, 2.0, 3.0, 4.0],
            'feature_zero_var': [5.0, 5.0, 5.0, 5.0],  # Constant
            'feature2': [10.0, 20.0, 30.0, 40.0],
            'target': [100, 200, 300, 400]
        })

        dropped, remaining = check_variance(df, threshold=1e-5)

        assert 'feature_zero_var' in dropped
        assert 'feature1' not in dropped
        assert 'feature2' not in dropped
        assert len(remaining.columns) == len(df.columns) - 1

    def test_check_variance_all_features_zero_var(self):
        """Test behavior when all features have zero variance."""
        df = pd.DataFrame({
            'feature1': [1.0, 1.0, 1.0],
            'feature2': [2.0, 2.0, 2.0],
            'target': [100, 200, 300]
        })

        dropped, remaining = check_variance(df, threshold=1e-5)

        assert 'feature1' in dropped
        assert 'feature2' in dropped
        # Target should not be in remaining features if it was included in check
        # but usually target is excluded from feature check

    def test_check_variance_no_zero_var(self):
        """Test that no features are dropped when all have variance."""
        df = pd.DataFrame({
            'feature1': [1.0, 2.0, 3.0],
            'feature2': [10.0, 20.0, 30.0],
            'target': [100, 200, 300]
        })

        dropped, remaining = check_variance(df, threshold=1e-5)

        assert len(dropped) == 0
        assert len(remaining.columns) == len(df.columns) - 1  # -1 for target

class TestModelFailureEdgeCases:
    """Tests for model failure scenarios (R² < threshold)."""

    def test_validate_model_performance_failure(self):
        """Test that model failure is correctly identified when R² < 0.8."""
        r_squared = 0.5
        threshold = 0.8

        is_valid, message = validate_model_performance(r_squared, threshold)

        assert is_valid is False
        assert "Model Failure" in message or "R²" in message

    def test_validate_model_performance_success(self):
        """Test that model success is correctly identified when R² >= 0.8."""
        r_squared = 0.9
        threshold = 0.8

        is_valid, message = validate_model_performance(r_squared, threshold)

        assert is_valid is True

    def test_validate_model_performance_boundary(self):
        """Test boundary condition where R² exactly equals threshold."""
        r_squared = 0.8
        threshold = 0.8

        is_valid, message = validate_model_performance(r_squared, threshold)

        assert is_valid is True

    def test_train_model_with_poor_data(self):
        """Test model training on data that yields poor R²."""
        # Create data with no relationship between features and target
        X = np.random.rand(100, 5)
        y = np.random.rand(100)  # Random target, no correlation

        model = train_model(X, y, n_estimators=10, max_depth=2, seed=42)
        
        # We expect low R² here
        from sklearn.metrics import r2_score
        y_pred = model.predict(X)
        r2 = r2_score(y, y_pred)
        
        # Just verify it runs without crashing; R² might be low
        assert model is not None

class TestSplitIntoWindowsEdgeCases:
    """Tests for window splitting edge cases."""

    def test_split_into_windows_uneven_remainder(self):
        """Test splitting when total rows don't divide evenly by window size."""
        df = pd.DataFrame({
            'timestamp': pd.date_range('2020-01-01', periods=35),
            'feature1': range(35),
            'target': range(35)
        })

        windows = split_into_windows(df, window_size=10, timestamp_col='timestamp')

        # Should have 3 windows: 10, 10, 15
        assert len(windows) == 3
        assert len(windows[0]) == 10
        assert len(windows[1]) == 10
        assert len(windows[2]) == 15

    def test_split_into_windows_single_window(self):
        """Test splitting when data fits exactly one window."""
        df = pd.DataFrame({
            'timestamp': pd.date_range('2020-01-01', periods=10),
            'feature1': range(10),
            'target': range(10)
        })

        windows = split_into_windows(df, window_size=10, timestamp_col='timestamp')

        assert len(windows) == 1
        assert len(windows[0]) == 10

    def test_split_into_windows_insufficient_data(self):
        """Test splitting when data is less than one window."""
        df = pd.DataFrame({
            'timestamp': pd.date_range('2020-01-01', periods=5),
            'feature1': range(5),
            'target': range(5)
        })

        windows = split_into_windows(df, window_size=10, timestamp_col='timestamp')

        assert len(windows) == 1
        assert len(windows[0]) == 5
