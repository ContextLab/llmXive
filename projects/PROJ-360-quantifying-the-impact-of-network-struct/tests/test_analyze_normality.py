import pytest
import pandas as pd
import numpy as np
import os
import sys
from pathlib import Path

# Add code directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))

from analyze import perform_normality_test

class TestNormalityTransformation:
    
    def test_shapiro_normal_data(self, tmp_path):
        """Test that normally distributed data is not transformed."""
        # Generate normal data
        np.random.seed(42)
        data = {
            'metric_a': np.random.normal(10, 2, 100),
            'thermal': np.random.normal(50, 10, 100)
        }
        df = pd.DataFrame(data)
        
        # Run test
        result_df, log = perform_normality_test(df, ['metric_a'], 'thermal')
        
        # Check that no transformation occurred (data should be identical)
        assert result_df.equals(df), "Normally distributed data should not be transformed."
        assert log['metric_a']['action'] == 'none', "Action should be 'none' for normal data."
        assert log['thermal']['action'] == 'none', "Action should be 'none' for normal target."

    def test_shapiro_non_normal_data(self, tmp_path):
        """Test that exponentially distributed data is log-transformed."""
        # Generate skewed data (exponential)
        np.random.seed(42)
        data = {
            'metric_b': np.random.exponential(2, 100) + 1, # +1 to ensure positive
            'thermal_skew': np.random.exponential(10, 100) + 1
        }
        df = pd.DataFrame(data)
        
        # Run test
        result_df, log = perform_normality_test(df, ['metric_b'], 'thermal_skew')
        
        # Check that transformation occurred
        assert not result_df.equals(df), "Non-normal data should be transformed."
        assert log['metric_b']['action'] == 'log_transform', "Action should be 'log_transform'."
        assert log['thermal_skew']['action'] == 'log_transform', "Action should be 'log_transform'."
        
        # Verify log transformation was applied (values should be different)
        assert not result_df['metric_b'].equals(df['metric_b'])

    def test_handles_zero_values(self, tmp_path):
        """Test that log transformation handles zeros correctly using log1p."""
        data = {
            'metric_c': [0, 1, 2, 3, 4, 5, 6, 7, 8, 9],
            'thermal_c': [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]
        }
        df = pd.DataFrame(data)
        
        # This should not crash and should use log1p
        result_df, log = perform_normality_test(df, ['metric_c'], 'thermal_c')
        
        # Check that 0 became log(1) = 0
        assert result_df.loc[0, 'metric_c'] == 0.0, "log1p(0) should be 0."
        assert result_df.loc[1, 'metric_c'] == np.log(2), "log1p(1) should be log(2)."

    def test_handles_negative_values(self, tmp_path):
        """Test that log transformation handles negative values by shifting."""
        data = {
            'metric_d': [-5, -2, 0, 2, 5],
            'thermal_d': [-10, -5, 0, 5, 10]
        }
        df = pd.DataFrame(data)
        
        # This should not crash
        result_df, log = perform_normality_test(df, ['metric_d'], 'thermal_d')
        
        # Check that transformation happened without error
        assert len(result_df) == 5
        # Values should be shifted and logged
        assert result_df['metric_d'].min() > -np.inf
        assert result_df['thermal_d'].min() > -np.inf