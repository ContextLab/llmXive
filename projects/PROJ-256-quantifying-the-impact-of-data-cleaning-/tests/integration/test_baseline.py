import os
import json
import pytest
import pandas as pd
import numpy as np
from pathlib import Path

# Ensure we can import from code/
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from analysis import run_t_test, run_linear_regression, compute_effect_size_cohen_d

@pytest.mark.integration
def test_baseline_analysis_integration(tmp_path):
    """
    Verify baseline analysis script produces valid metrics.
    Simulates the output of T012/T013.
    """
    # Create a dummy dataset
    np.random.seed(42)
    n = 100
    data = {
        "predictor": np.random.normal(0, 1, n),
        "outcome": np.random.normal(0, 1, n) + 0.5 * np.random.normal(0, 1, n)
    }
    df = pd.DataFrame(data)
    
    # Run analysis
    from analysis import run_baseline_analysis
    results = run_baseline_analysis(df, "outcome", ["predictor"])
    
    assert "tests" in results
    assert len(results["tests"]) > 0
    
    for test in results["tests"]:
        assert "regression" in test
        assert "t_test" in test
        
        # Validate p-values are in (0, 1)
        p_reg = test["regression"]["p_value"]
        p_t = test["t_test"]["p_value"]
        
        assert 0 <= p_reg <= 1, f"Regression p-value {p_reg} out of bounds"
        assert 0 <= p_t <= 1, f"T-test p-value {p_t} out of bounds"
        
        # Validate finite values
        assert np.isfinite(test["regression"]["slope"])
        assert np.isfinite(test["regression"]["r_squared"])
        assert np.isfinite(test["t_test"]["t_statistic"])
        assert np.isfinite(test["t_test"]["cohen_d"])

@pytest.mark.integration
def test_metrics_json_generation(tmp_path):
    """
    Verify that metrics can be serialized to JSON as required by T013/T023.
    """
    metrics = {
        "dataset": "test",
        "tests": [
            {
                "predictor": "x",
                "p_value": 0.0345,
                "effect_size": 0.5
            }
        ]
    }
    
    output_file = tmp_path / "baseline_metrics.json"
    with open(output_file, 'w') as f:
        json.dump(metrics, f)
    
    assert output_file.exists()
    with open(output_file, 'r') as f:
        loaded = json.load(f)
    
    assert loaded["dataset"] == "test"
    assert loaded["tests"][0]["p_value"] == 0.0345