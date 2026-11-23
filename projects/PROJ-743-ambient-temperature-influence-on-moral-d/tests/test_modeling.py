"""
Unit and Integration tests for code/modeling.py (T025).

Tests:
1. Log-transformation logic (handling <=0 values).
2. Outlier handling (winsorize vs exclude).
3. Model convergence fallback logic (mocked).
"""
import pytest
import pandas as pd
import numpy as np
from unittest.mock import patch, MagicMock
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from modeling import log_transform_response_times, handle_outliers, fit_lmm, fit_glmm_fallback

class TestLogTransform:
    def test_log_transform_valid_data(self):
        """Test log transformation on valid positive data."""
        df = pd.DataFrame({"response_time_ms": [100, 200, 300, 400, 500]})
        df_clean, log_series = log_transform_response_times(df)
        
        assert len(df_clean) == 5
        assert "log_response_time" in df_clean.columns
        # Check a specific value: log(100)
        expected = np.log(100)
        assert np.isclose(df_clean.loc[0, "log_response_time"], expected)

    def test_log_transform_invalid_data(self):
        """Test that <=0 values are filtered out."""
        df = pd.DataFrame({"response_time_ms": [100, -50, 0, 200, 300]})
        df_clean, log_series = log_transform_response_times(df)
        
        assert len(df_clean) == 3
        assert all(df_clean["response_time_ms"] > 0)

class TestOutlierHandling:
    def test_winsorize_low(self):
        """Test winsorizing low outliers."""
        df = pd.DataFrame({"log_response_time": [1.0, 1.1, 1.2, 10.0]}) # 1.0 is low outlier
        # 1.0 is below 25th percentile (approx 1.075)
        df_out = handle_outliers(df, method="winsorize", lower_percentile=25, upper_percentile=75)
        
        # The lowest value should be raised to the 25th percentile
        assert df_out["log_response_time"].min() >= df["log_response_time"].quantile(0.25)

    def test_exclude_high(self):
        """Test excluding high outliers."""
        df = pd.DataFrame({"log_response_time": [1.0, 1.1, 1.2, 1.3, 1.4, 100.0]})
        df_out = handle_outliers(df, method="exclude", upper_percentile=90)
        
        # 100.0 should be removed
        assert 100.0 not in df_out["log_response_time"].values
        assert len(df_out) < len(df)

class TestModelConvergenceFallback:
    @patch('modeling.smf.mixedlm')
    def test_lmm_converges(self, mock_mixedlm):
        """Test successful LMM fit."""
        mock_result = MagicMock()
        mock_result.converged = True
        mock_model = MagicMock()
        mock_model.fit.return_value = mock_result
        mock_mixedlm.return_value = mock_model
        
        df = pd.DataFrame({"y": [1, 2, 3], "x": [1, 2, 3], "group": [1, 1, 2]})
        result = fit_lmm(df, "y ~ x")
        
        assert result is not None
        assert result.converged is True

    @patch('modeling.smf.mixedlm')
    def test_lmm_fails_convergence_triggers_fallback_logic(self, mock_mixedlm):
        """Test that non-converging LMM returns None, allowing fallback in main logic."""
        mock_result = MagicMock()
        mock_result.converged = False # Simulate failure
        mock_model = MagicMock()
        mock_model.fit.return_value = mock_result
        mock_mixedlm.return_value = mock_model
        
        df = pd.DataFrame({"y": [1, 2, 3], "x": [1, 2, 3], "group": [1, 1, 2]})
        result = fit_lmm(df, "y ~ x")
        
        assert result is None

    @patch('modeling.smf.ols')
    def test_fallback_robust_ols(self, mock_ols):
        """Test that fallback robust OLS works."""
        mock_ols_result = MagicMock()
        mock_ols_result.params = pd.Series({"x": 0.5})
        mock_ols_result.bse = pd.Series({"x": 0.1})
        mock_ols_result.pvalues = pd.Series({"x": 0.01})
        
        mock_robust = MagicMock()
        mock_robust.params = mock_ols_result.params
        mock_robust.bse = mock_ols_result.bse
        mock_robust.pvalues = mock_ols_result.pvalues
        
        mock_ols.return_value.fit.return_value.get_robustcov_results.return_value = mock_robust
        
        df = pd.DataFrame({"y": [1, 2, 3], "x": [1, 2, 3], "country_code": [1, 1, 2]})
        result = fit_glmm_fallback(df, "y ~ x")
        
        assert result is not None
        assert result.params["x"] == 0.5

if __name__ == "__main__":
    pytest.main([__file__, "-v"])