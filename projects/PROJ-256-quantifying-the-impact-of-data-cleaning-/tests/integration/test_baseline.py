import os
import json
import pytest
import pandas as pd
from pathlib import Path
from analysis import run_baseline_analysis, save_json_file

TEST_OUTPUT_FILE = "data/processed/test_baseline_metrics.json"

@pytest.fixture(autouse=True)
def setup_teardown():
    # Setup
    os.makedirs("data/processed", exist_ok=True)
    yield
    # Teardown
    if os.path.exists(TEST_OUTPUT_FILE):
        os.remove(TEST_OUTPUT_FILE)

def test_baseline_analysis_creates_valid_json():
    """
    Integration test: Verify baseline analysis script produces 
    baseline_metrics.json with valid p-values (0 < p < 1) and finite CIs.
    """
    # Create a dummy dataset for testing
    data = {
        "outcome": [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0],
        "group": ["A", "A", "A", "A", "B", "B", "B", "B"],
        "predictor": [10, 20, 30, 40, 15, 25, 35, 45]
    }
    df = pd.DataFrame(data)
    
    # Save to raw directory
    os.makedirs("data/raw", exist_ok=True)
    temp_csv = "data/raw/test_dataset.csv"
    df.to_csv(temp_csv, index=False)
    
    try:
        # Run analysis
        success = run_baseline_analysis("data/raw", TEST_OUTPUT_FILE, config={})
        
        assert success is True, "Baseline analysis should return True"
        assert os.path.exists(TEST_OUTPUT_FILE), "Output file should be created"
        
        # Load and validate
        with open(TEST_OUTPUT_FILE, 'r') as f:
            metrics = json.load(f)
        
        assert "datasets" in metrics, "Metrics should contain 'datasets' key"
        assert len(metrics["datasets"]) > 0, "Metrics should contain at least one dataset"
        
        ds = metrics["datasets"][0]
        t_test = ds.get("t_test", {})
        
        p_val = t_test.get("p_value")
        ci_low = t_test.get("ci_low")
        ci_high = t_test.get("ci_high")
        
        # Validate p-value
        assert p_val is not None, "p-value should not be None"
        assert 0 < p_val < 1, f"p-value {p_val} should be in (0, 1)"
        
        # Validate CI bounds are finite
        import math
        assert ci_low is not None and math.isfinite(ci_low), "CI low should be finite"
        assert ci_high is not None and math.isfinite(ci_high), "CI high should be finite"
        
    finally:
        # Cleanup
        if os.path.exists(temp_csv):
            os.remove(temp_csv)
