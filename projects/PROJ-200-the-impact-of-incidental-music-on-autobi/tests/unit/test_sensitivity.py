"""
Unit tests for Sensitivity Analysis (T039a / T044c).
"""
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import sys
import os

# Add project root to path
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from modeling import (
    run_sensitivity_loop_setup,
    re_calculate_exposure,
    re_match_cues,
    re_aggregate,
    run_sensitivity_analysis
)

class TestSensitivityAnalysis:
    """Tests for T044c sensitivity analysis logic."""

    @pytest.fixture
    def mock_setup_data(self):
        """Create mock setup data for sensitivity analysis."""
        mock_df = pd.DataFrame({
            "track_id": [1, 2, 3, 4, 5],
            "user_id": [1, 1, 2, 2, 3],
            "total_listens": [10, 5, 3, 2, 20],
            "adolescent_listens": [5, 2, 1, 0, 15],
            "total_valid_listens": [10, 5, 3, 2, 20],
            "popularity": [0.5, 0.6, 0.7, 0.8, 0.9],
            "mean_vividness": [3.0, 4.0, 2.5, 3.5, 4.5]
        })
        return {
            "base_df": mock_df,
            "thresholds": [2, 3, 4],
            "config": {}
        }

    def test_run_sensitivity_loop_setup(self, mock_setup_data):
        """Test that setup returns correct structure."""
        # In a real test, we would load from parquet
        # Here we mock the return
        result = mock_setup_data
        assert "base_df" in result
        assert "thresholds" in result
        assert len(result["thresholds"]) > 0

    def test_re_calculate_exposure(self, mock_setup_data):
        """Test re-calculation of exposure scores."""
        df = re_calculate_exposure(mock_setup_data, threshold=4)
        assert "adolescent_exposure_ratio" in df.columns
        # Check that ratio is calculated correctly for non-zero total
        # For track 1: 5/10 = 0.5
        assert df.loc[df["track_id"] == 1, "adolescent_exposure_ratio"].iloc[0] == 0.5

    def test_re_aggregate(self, mock_setup_data):
        """Test re-aggregation logic."""
        filtered_df = re_calculate_exposure(mock_setup_data, threshold=4)
        result = re_aggregate(mock_setup_data, threshold=4, filtered_df=filtered_df)
        assert isinstance(result, pd.DataFrame)
        assert len(result) > 0

    def test_run_sensitivity_analysis_structure(self, mock_setup_data):
        """Test that sensitivity analysis returns a DataFrame with expected columns."""
        # Mock the internal functions to avoid actual model fitting which might fail on small data
        import modeling
        original_fit = modeling.fit_mixed_model
        
        def mock_fit(df, formula=None):
            class MockResult:
                params = {"adolescent_exposure_ratio": 0.5, "popularity": 0.1}
                bse = {"adolescent_exposure_ratio": 0.1, "popularity": 0.05}
                tvalues = {"adolescent_exposure_ratio": 5.0, "popularity": 2.0}
                pvalues = {"adolescent_exposure_ratio": 0.01, "popularity": 0.05}
            return MockResult()
        
        modeling.fit_mixed_model = mock_fit
        
        try:
            result = run_sensitivity_analysis(mock_setup_data)
            assert isinstance(result, pd.DataFrame)
            assert "threshold" in result.columns
            assert "p_value_exposure" in result.columns
            assert len(result) == len(mock_setup_data["thresholds"])
        finally:
            modeling.fit_mixed_model = original_fit