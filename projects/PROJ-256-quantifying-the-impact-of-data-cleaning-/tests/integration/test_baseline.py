import os
import json
import pytest
import pandas as pd
import numpy as np

# Add parent directory to path
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from analysis import run_baseline_analysis, write_output
from config import get_config

@pytest.fixture
def sample_data_dir(tmp_path):
    """Create a temporary directory with sample CSV data."""
    raw_dir = tmp_path / "data" / "raw"
    raw_dir.mkdir(parents=True)
    
    # Create a simple dataset with a categorical and numerical column
    df = pd.DataFrame({
        'group': ['A', 'A', 'B', 'B', 'A', 'B', 'A', 'B'] * 10,
        'value': np.random.normal(loc=10, scale=2, size=80),
        'other': np.random.normal(loc=5, scale=1, size=80)
    })
    
    filepath = raw_dir / "test_dataset.csv"
    df.to_csv(filepath, index=False)
    return str(raw_dir)

@pytest.fixture
def output_dir(tmp_path):
    """Create a temporary output directory."""
    out_dir = tmp_path / "data" / "processed"
    out_dir.mkdir(parents=True)
    return str(out_dir)

def test_baseline_analysis_produces_valid_metrics(sample_data_dir, output_dir):
    """
    Integration test: Verify baseline analysis script produces baseline_metrics.json 
    with valid p-values (0 < p < 1) and finite CIs.
    """
    output_file = os.path.join(output_dir, "baseline_metrics.json")
    
    # Run analysis
    success = run_baseline_analysis(sample_data_dir, output_file)
    
    assert success, "Analysis should run successfully"
    assert os.path.exists(output_file), "Output file should be created"
    
    with open(output_file, 'r') as f:
        data = json.load(f)
    
    assert "results" in data, "Results key must exist"
    assert len(data["results"]) > 0, "At least one dataset result expected"
    
    for res in data["results"]:
        if res.get("status") == "success":
            if "t_tests" in res:
                for t_test in res["t_tests"]:
                    if t_test.get("status") == "success":
                        p_val = t_test.get("p_value")
                        assert p_val is not None, "P-value must exist"
                        assert 0 < p_val < 1, f"P-value {p_val} must be between 0 and 1"
                        
                        ci = t_test.get("ci_95")
                        if ci:
                            assert len(ci) == 2, "CI must have 2 bounds"
                            assert all(np.isfinite(x) for x in ci), "CI bounds must be finite"
            
            if "regressions" in res:
                for reg in res["regressions"]:
                    if reg.get("status") == "success":
                        p_val = reg.get("p_value")
                        if p_val is not None:
                            assert 0 <= p_val <= 1, f"Regression P-value {p_val} must be in [0, 1]"
                            
                        r_sq = reg.get("r_squared")
                        if r_sq is not None:
                            assert np.isfinite(r_sq), "R-squared must be finite"

def test_baseline_analysis_on_dataframe():
    """Test running baseline analysis directly on a DataFrame."""
    df = pd.DataFrame({
        'cat': ['X', 'Y', 'X', 'Y', 'X', 'Y'],
        'num': [1.0, 2.0, 1.5, 2.5, 1.2, 2.8]
    })
    
    result = run_baseline_analysis(df, dataset_name="inline_test")
    
    assert isinstance(result, dict), "Result should be a dict"
    assert "results" in result, "Result should contain 'results' key"
    assert len(result["results"]) == 1, "Should analyze one dataset"
    
    dataset_res = result["results"][0]
    assert dataset_res["dataset_name"] == "inline_test"
    # Verify structure
    assert "t_tests" in dataset_res or "regressions" in dataset_res