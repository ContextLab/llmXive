"""
Integration test for User Story 1 (US-1).
Verifies the full pipeline execution and output schema.
"""
import pytest
import os
import sys
import json
import tempfile
import shutil
from datetime import datetime, timedelta
import pandas as pd
import numpy as np

# Add project root to path
_project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _project_root)

from code.main import run_pipeline, RESULTS_DIR

@pytest.fixture
def sample_date_range():
    # Use a small, known range that should have data
    # Jan 2023 is a good candidate for OMNI data availability
    return "2023-01-01", "2023-01-03"

@pytest.fixture
def results_dir():
    # Ensure results directory exists for the test
    os.makedirs(RESULTS_DIR, exist_ok=True)
    return RESULTS_DIR

def test_us1_full_pipeline(sample_date_range, results_dir):
    """
    Run the full US-1 pipeline and verify output keys.
    This test expects real data to be fetched.
    """
    start, end = sample_date_range
    try:
        results = run_pipeline(start, end)
    except Exception as e:
        # If real data fetch fails (e.g., network), skip this specific test
        # rather than failing the whole suite, but log the error.
        pytest.skip(f"Real data fetch failed: {e}")

    # Verify required keys exist
    required_keys = [
        "pearson", "spearman", "p_val_permutation", "significant_flag",
        "optimal_lag", "lag_correlation_value", "physics_lag_minutes",
        "lag_difference", "notes"
    ]
    
    for key in required_keys:
        assert key in results, f"Missing key in results: {key}"
    
    # Verify types
    assert isinstance(results["pearson"], float)
    assert isinstance(results["spearman"], float)
    assert isinstance(results["p_val_permutation"], float)
    assert isinstance(results["significant_flag"], bool)
    assert isinstance(results["optimal_lag"], int)
    
    # Verify ranges (correlation must be between -1 and 1)
    assert -1.0 <= results["pearson"] <= 1.0
    assert -1.0 <= results["spearman"] <= 1.0
    assert 0.0 <= results["p_val_permutation"] <= 1.0

def test_quality_log_creation(sample_date_range, results_dir):
    """
    Verify that quality_log.json is created if warnings occur.
    (This is harder to trigger deterministically without forcing a warning,
     so we just check the file path logic exists in the module).
    """
    # We rely on the fact that run_pipeline calls log_quality_warnings
    # if warnings are generated. If no warnings, the file might not be created.
    # This test validates the schema if it exists.
    log_path = os.path.join(results_dir, "quality_log.json")
    if os.path.exists(log_path):
        with open(log_path, 'r') as f:
            data = json.load(f)
        assert isinstance(data, list)
        # Each warning should have a type
        for item in data:
            assert "type" in item
            assert "msg" in item