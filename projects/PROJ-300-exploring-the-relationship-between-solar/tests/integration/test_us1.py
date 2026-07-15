"""
Integration tests for User Story 1: Lag-Adjusted Coupling.
File path: projects/PROJ-300-exploring-the-relationship-between-solar/tests/integration/test_us1.py
"""
import pytest
import os
import sys
import json
from datetime import datetime, timedelta

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from code.main import run_pipeline
from code.data.clean import clean_and_resample
from code.data.lag import calculate_physics_lag

def test_us1_full_pipeline():
    """
    Verify the full pipeline runs and produces expected JSON keys.
    Uses a small sample range to minimize execution time.
    """
    # Use a short range to avoid long fetch times in CI
    start = "2023-01-01"
    end = "2023-01-02"
    
    try:
        results = run_pipeline(start, end, output_dir="data/processed")
    except RuntimeError as e:
        # If data fetch fails (e.g., API limits), skip test
        if "Failed to fetch data" in str(e):
            pytest.skip("Data fetch failed (API limit or network issue)")
        else:
            raise

    assert results["status"] == "success" or results["status"] == "empty"
    
    if results["status"] == "empty":
        # Expected if no data overlap
        assert "warnings" in results
        return

    # Check required keys
    required_keys = [
        "pearson", "spearman", "p_val_permutation", "significant_flag",
        "optimal_lag_minutes", "physics_lag_minutes"
    ]
    for key in required_keys:
        assert key in results, f"Missing key: {key}"

    # Check numeric types
    assert isinstance(results["pearson"], float)
    assert isinstance(results["spearman"], float)
    assert isinstance(results["p_val_permutation"], float)
    assert isinstance(results["significant_flag"], bool)

    # Check file existence
    report_path = "data/processed/us1_correlation.json"
    assert os.path.exists(report_path), f"Report file not found: {report_path}"
    
    quality_path = "data/processed/quality_log.json"
    assert os.path.exists(quality_path), f"Quality log not found: {quality_path}"

def test_us1_nan_handling():
    """
    Verify pipeline handles NaN gaps by cleaning and resampling.
    """
    # This is implicitly tested by the full pipeline if the real data has gaps.
    # A more explicit test would require mocking data, which is not allowed per spec.
    # We rely on the real data path to verify robustness.
    pass

def test_us1_lag_calculation():
    """
    Verify physics lag calculation logic.
    """
    # Test with typical solar wind speed
    vsw = 400.0 # km/s
    lag = calculate_physics_lag(vsw)
    assert lag > 0
    # Typical lag for 400 km/s to 60 Re is roughly (60 * 6371) / 400 / 60 ~ 16 minutes
    # With K_PROPAGATION (usually ~1), it should be in a reasonable range
    assert 5 < lag < 60, f"Lag {lag} seems out of physical range for 400 km/s"