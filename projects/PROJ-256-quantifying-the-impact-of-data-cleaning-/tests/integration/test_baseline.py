"""
Integration test for baseline analysis pipeline (Task T010).

Verifies that the baseline analysis script produces `baseline_metrics.json`
with valid p-values (0 < p < 1) and finite confidence intervals.
"""
import os
import sys
import json
import tempfile
import shutil
import pandas as pd
import numpy as np
from pathlib import Path

# Add project root to path
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from analysis import run_baseline_analysis
from config import get_config

def test_baseline_analysis_output():
    """
    Test that run_baseline_analysis produces a valid JSON file with
    p-values in (0, 1) and finite CIs.
    """
    # Create a temporary directory for test data
    with tempfile.TemporaryDirectory() as tmpdir:
        raw_dir = os.path.join(tmpdir, "raw")
        output_dir = os.path.join(tmpdir, "output")
        os.makedirs(raw_dir)
        os.makedirs(output_dir)
        
        # Create a synthetic dataset with known properties
        # Ensure we have a binary group and a numeric outcome
        np.random.seed(42)
        n = 100
        df = pd.DataFrame({
            "group": np.random.choice([0, 1], n),
            "outcome": np.random.normal(loc=10, scale=2, size=n) + np.random.choice([0, 5], n)
        })
        
        # Save to raw directory
        csv_path = os.path.join(raw_dir, "test_dataset.csv")
        df.to_csv(csv_path, index=False)
        
        output_path = os.path.join(output_dir, "baseline_metrics.json")
        
        # Run the analysis
        config = get_config()
        result = run_baseline_analysis(raw_dir, output_path, config=config)
        
        assert result is True, "Analysis should return True on success."
        assert os.path.exists(output_path), "Output file should be created."
        
        # Load and validate the JSON
        with open(output_path, 'r') as f:
            data = json.load(f)
        
        assert isinstance(data, list), "Output should be a list of results."
        assert len(data) > 0, "Output should contain at least one result."
        
        for entry in data:
            # Check for t-test results
            if "t_test" in entry:
                t_test = entry["t_test"]
                if "p_value" in t_test:
                    p_val = t_test["p_value"]
                    assert isinstance(p_val, (int, float)), "P-value must be numeric."
                    assert 0 < p_val < 1, f"P-value {p_val} must be in (0, 1)."
                
                if "ci" in t_test:
                    ci = t_test["ci"]
                    assert isinstance(ci, list) and len(ci) == 2, "CI must be a list of 2 values."
                    assert all(isinstance(x, (int, float)) and not np.isnan(x) and not np.isinf(x) for x in ci), \
                        "CI bounds must be finite numbers."
            
            # Check for regression results
            if "regression" in entry:
                reg = entry["regression"]
                if "r_squared" in reg:
                    r2 = reg["r_squared"]
                    assert isinstance(r2, (int, float)) and not np.isnan(r2), "R-squared must be finite."

if __name__ == "__main__":
    test_baseline_analysis_output()
    print("Integration test passed.")