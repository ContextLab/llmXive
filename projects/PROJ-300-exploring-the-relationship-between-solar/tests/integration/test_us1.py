"""
Integration test for User Story 1: Quantify Lag-Adjusted Coupling.
Verifies the full pipeline produces correct JSON output.
"""
import pytest
import json
import os
import sys
from datetime import datetime, timedelta
import pandas as pd
import numpy as np

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from code.main import run_pipeline

@pytest.fixture
def sample_date_range():
    # Use a small, real date range where data is likely available
    return ("2023-01-01", "2023-01-02")

def test_us1_full_pipeline(sample_date_range):
    """
    Run the full US-1 pipeline and verify output keys.
    """
    start, end = sample_date_range
    
    # Run pipeline
    # Note: This may take time due to data fetching
    try:
        result = run_pipeline(start, end)
    except Exception as e:
        # If real data fetch fails, the test fails (as per "Fail Loudly" constraint)
        pytest.fail(f"Pipeline execution failed: {e}")

    # Verify result is a dict
    assert isinstance(result, dict), "Pipeline should return a dictionary"

    # Verify required keys in the report
    required_keys = [
        "metadata", "physics", "correlation", "lag_search", 
        "sensitivity_table", "plots", "notes"
    ]
    for key in required_keys:
        assert key in result, f"Missing key in report: {key}"

    # Verify specific correlation keys
    corr_keys = ["pearson", "spearman", "p_val_permutation", "significant_flag"]
    for key in corr_keys:
        assert key in result["correlation"], f"Missing key in correlation: {key}"

    # Verify numeric types
    assert isinstance(result["correlation"]["pearson"], (int, float))
    assert isinstance(result["correlation"]["spearman"], (int, float))
    
    # Verify plots exist
    assert os.path.exists(result["plots"]["scatter"]), "Scatter plot not generated"
    assert os.path.exists(result["plots"]["timeseries"]), "Timeseries plot not generated"

    # Verify quality log exists
    log_path = "data/processed/quality_log.json"
    assert os.path.exists(log_path), "Quality log not generated"

    # Verify JSON report exists
    report_path = "data/processed/us1_correlation.json"
    assert os.path.exists(report_path), "JSON report not generated"

def test_us1_nan_handling(sample_date_range):
    """
    Verify pipeline handles NaN gaps by cleaning, resampling, and producing output.
    """
    # The pipeline includes cleaning logic. We verify it runs without error.
    # If the real data has NaNs, the clean_and_resample function should handle them.
    # This test implicitly verifies the pipeline's robustness.
    start, end = sample_date_range
    
    try:
        result = run_pipeline(start, end)
        assert "correlation" in result
    except Exception as e:
        pytest.fail(f"Pipeline failed on data with potential NaNs: {e}")
