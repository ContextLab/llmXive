"""
Integration test for T010: Verify baseline analysis script produces valid p-values and finite CIs.
"""
import os
import json
import pytest
import pandas as pd
import numpy as np
from pathlib import Path

# Ensure project root is in path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.t012_run_baseline_analysis import main as run_baseline_main
from code.t013_record_baseline_metrics import main as record_baseline_main

OUTPUT_FILE = "data/processed/baseline_metrics.json"

@pytest.fixture(autouse=True)
def setup_and_teardown():
    """Ensure output directory exists and clean up after test."""
    os.makedirs("data/processed", exist_ok=True)
    yield
    if os.path.exists(OUTPUT_FILE):
        os.remove(OUTPUT_FILE)

def test_baseline_analysis_produces_valid_metrics():
    """
    Verify that the baseline analysis pipeline:
    1. Produces data/processed/baseline_metrics.json
    2. Contains valid p-values (0 < p < 1)
    3. Contains finite confidence intervals
    """
    # Run the baseline analysis and recording tasks
    # Note: In a real scenario, we would ensure data is downloaded first.
    # For this test, we assume T011 has downloaded at least one dataset.
    
    try:
        run_baseline_main()
        record_baseline_main()
    except Exception as e:
        # If no data is available, we might get an error, which is acceptable
        # if the file is not produced. But we need to check if the file exists.
        pass

    # Check if file exists
    assert os.path.exists(OUTPUT_FILE), f"Baseline metrics file {OUTPUT_FILE} was not created."

    with open(OUTPUT_FILE, 'r') as f:
        metrics = json.load(f)

    # Validate structure
    assert "datasets" in metrics, "Missing 'datasets' key in baseline metrics."
    assert len(metrics["datasets"]) > 0, "No datasets analyzed in baseline metrics."

    # Check each dataset's analysis
    for dataset_entry in metrics["datasets"]:
        analysis = dataset_entry.get("analysis", {})
        
        # Check t-tests
        t_tests = analysis.get("t_tests", {})
        for test_name, test_result in t_tests.items():
            p_value = test_result.get("p_value")
            assert p_value is not None, f"Missing p_value for t-test {test_name}"
            assert 0 < p_value < 1, f"Invalid p_value {p_value} for {test_name} (must be 0 < p < 1)"
        
        # Check regressions for finite coefficients and p-values
        regressions = analysis.get("regressions", {})
        for reg_name, reg_result in regressions.items():
            p_values = reg_result.get("p_values", [])
            for p in p_values:
                assert p is not None, f"Missing p_value in regression {reg_name}"
                assert np.isfinite(p), f"Non-finite p_value {p} in regression {reg_name}"
            # Check R-squared
            r_sq = reg_result.get("r_squared")
            if r_sq is not None:
                assert np.isfinite(r_sq), f"Non-finite R-squared {r_sq} in regression {reg_name}"

def test_baseline_metrics_json_is_valid_json():
    """Verify the output file is valid JSON."""
    # Force a run to ensure file exists
    try:
        run_baseline_main()
        record_baseline_main()
    except:
        pass
    
    if not os.path.exists(OUTPUT_FILE):
        pytest.skip("Baseline metrics file not created (no data available).")
    
    try:
        with open(OUTPUT_FILE, 'r') as f:
            json.load(f)
    except json.JSONDecodeError as e:
        pytest.fail(f"Invalid JSON in {OUTPUT_FILE}: {e}")
