"""
Unit tests for features.py module.
Tests verify lagged feature calculations and VIF filtering logic.
"""
import os
import sys
import pytest
from pathlib import Path
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from features import compute_lagged_features, compute_interaction_features
from features import check_definitional_circularity, calculate_vif, filter_high_vif
from features import main

class TestLaggedFeatures:
    """Test lagged feature computation."""

    def test_compute_lagged_features_returns_dataframe(self):
        """Verify compute_lagged_features returns a DataFrame."""
        # Create sample time-series data
        dates = pd.date_range(start='2020-01-01', periods=10, freq='D')
        data = {'SST': [25.0 + i * 0.1 for i in range(10)]}
        df = pd.DataFrame(data, index=dates)
        
        result = compute_lagged_features(df, target_col='SST', lags=[1, 3])
        assert isinstance(result, pd.DataFrame)
        assert 'SST_lag_1' in result.columns
        assert 'SST_lag_3' in result.columns

    def test_compute_lagged_features_values(self):
        """Verify lagged values are calculated correctly."""
        dates = pd.date_range(start='2020-01-01', periods=5, freq='D')
        data = {'SST': [1.0, 2.0, 3.0, 4.0, 5.0]}
        df = pd.DataFrame(data, index=dates)
        
        result = compute_lagged_features(df, target_col='SST', lags=[1])
        # SST_lag_1 for index 1 should be 1.0 (value at index 0)
        assert result['SST_lag_1'].iloc[1] == 1.0
        # SST_lag_1 for index 0 should be NaN
        assert pd.isna(result['SST_lag_1'].iloc[0])

    def test_compute_lagged_features_rolling_mean(self):
        """Verify rolling mean calculation for lagged features."""
        dates = pd.date_range(start='2020-01-01', periods=5, freq='D')
        data = {'SST': [1.0, 2.0, 3.0, 4.0, 5.0]}
        df = pd.DataFrame(data, index=dates)
        
        result = compute_lagged_features(df, target_col='SST', window=3)
        # Rolling mean of first 3 values (1, 2, 3) is 2.0
        # The result should have a column like 'SST_rolling_3'
        # Note: The actual implementation might name it differently, but we check existence
        rolling_cols = [c for c in result.columns if 'rolling' in c.lower() or 'mean' in c.lower()]
        assert len(rolling_cols) > 0

class TestInteractionFeatures:
    """Test interaction feature computation."""

    def test_compute_interaction_features_returns_dataframe(self):
        """Verify compute_interaction_features returns a DataFrame."""
        data = {
            'DHW': [1.0, 2.0, 3.0, 4.0],
            'thermal_tolerance': [10.0, 11.0, 12.0, 13.0]
        }
        df = pd.DataFrame(data)
        
        result = compute_interaction_features(df, col1='DHW', col2='thermal_tolerance')
        assert isinstance(result, pd.DataFrame)
        # Check for the interaction column name
        assert 'DHW_thermal_tolerance' in result.columns or 'DHW_x_thermal_tolerance' in result.columns

    def test_compute_interaction_features_values(self):
        """Verify interaction values are calculated correctly."""
        data = {
            'DHW': [2.0, 3.0],
            'thermal_tolerance': [5.0, 4.0]
        }
        df = pd.DataFrame(data)
        
        result = compute_interaction_features(df, col1='DHW', col2='thermal_tolerance')
        # 2.0 * 5.0 = 10.0
        assert result.iloc[0]['DHW_thermal_tolerance'] == 10.0
        # 3.0 * 4.0 = 12.0
        assert result.iloc[1]['DHW_thermal_tolerance'] == 12.0

class TestDefinitionalCircularity:
    """Test definitional circularity check."""

    def test_check_definitional_circularity_returns_bool(self):
        """Verify check_definitional_circularity returns a boolean."""
        # DHW is derived from SST, so this should return True
        is_circular, message = check_definitional_circularity(['SST', 'DHW'])
        assert isinstance(is_circular, bool)
        assert isinstance(message, str)

    def test_check_definitional_circularity_dhw_sst(self):
        """Verify DHW vs SST is detected as circular."""
        is_circular, message = check_definitional_circularity(['SST', 'DHW'])
        assert is_circular is True
        assert 'DHW' in message and 'SST' in message

    def test_check_definitional_circularity_independent(self):
        """Verify independent variables are not flagged."""
        is_circular, message = check_definitional_circularity(['latitude', 'longitude'])
        assert is_circular is False

class TestVIF:
    """Test Variance Inflation Factor calculations."""

    def test_calculate_vif_returns_dict(self):
        """Verify calculate_vif returns a dictionary of VIF scores."""
        data = {
            'x1': [1, 2, 3, 4, 5],
            'x2': [2, 4, 6, 8, 10], # Perfectly correlated with x1
            'x3': [1, 3, 5, 7, 9]
        }
        df = pd.DataFrame(data)
        
        result = calculate_vif(df)
        assert isinstance(result, dict)
        assert 'x1' in result
        assert 'x2' in result
        assert 'x3' in result

    def test_calculate_vif_high_correlation(self):
        """Verify VIF is high for correlated features."""
        data = {
            'x1': [1, 2, 3, 4, 5],
            'x2': [1.01, 2.01, 3.01, 4.01, 5.01] # Highly correlated
        }
        df = pd.DataFrame(data)
        
        result = calculate_vif(df)
        # VIF should be significantly greater than 1 for correlated features
        assert result['x1'] > 1
        assert result['x2'] > 1

    def test_filter_high_vif_removes_features(self):
        """Verify filter_high_vif removes features with VIF > threshold."""
        data = {
            'x1': [1, 2, 3, 4, 5],
            'x2': [1, 2, 3, 4, 5], # Perfectly correlated
            'x3': [1, 2, 3, 4, 5],
            'y': [1, 2, 3, 4, 5]
        }
        df = pd.DataFrame(data)
        
        # Calculate VIFs
        vif_scores = calculate_vif(df)
        
        # Filter with threshold 5
        filtered_df, dropped_cols = filter_high_vif(df, threshold=5)
        
        # x1 and x2 are perfectly correlated, so one should be dropped
        # The exact behavior depends on implementation, but at least one correlated feature should be gone
        assert len(filtered_df.columns) < len(df.columns)
        # Check that 'y' is still there (target)
        assert 'y' in filtered_df.columns

    def test_filter_high_vif_returns_tuple(self):
        """Verify filter_high_vif returns (DataFrame, list)."""
        data = {'x': [1, 2, 3], 'y': [1, 2, 3]}
        df = pd.DataFrame(data)
        
        result_df, dropped = filter_high_vif(df, threshold=10)
        assert isinstance(result_df, pd.DataFrame)
        assert isinstance(dropped, list)

class TestMainFunction:
    """Test the main entry point logic."""

    def test_main_exists(self):
        """Verify main function exists and is callable."""
        assert callable(main)
