import os
import sys
import json
import pytest
import pandas as pd
import numpy as np
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'code'))

from analysis import run_baseline_analysis, load_datasets_from_raw
from utils import setup_logging

@pytest.fixture(scope="module")
def sample_data_dir(tmp_path):
    """Create a temporary directory with sample data for testing."""
    raw_dir = tmp_path / "raw"
    raw_dir.mkdir()
    
    # Create a sample CSV with a binary group and a numeric outcome
    data = {
        "group": ["A"] * 50 + ["B"] * 50,
        "value": np.random.normal(loc=0, scale=1, size=50).tolist() + 
                 np.random.normal(loc=0.5, scale=1, size=50).tolist()
    }
    df = pd.DataFrame(data)
    df.to_csv(raw_dir / "sample_data.csv", index=False)
    
    return raw_dir

def test_baseline_analysis_script(sample_data_dir, tmp_path):
    """
    Integration test: Verify baseline analysis script produces baseline_metrics.json 
    with valid p-values (0 < p < 1) and finite CIs.
    """
    setup_logging("DEBUG")
    output_path = tmp_path / "baseline_metrics.json"
    
    # Run the analysis
    success = run_baseline_analysis(str(sample_data_dir), str(output_path))
    
    assert success, "Baseline analysis script should return True on success"
    assert output_path.exists(), "Output file should exist"
    
    # Load and validate the JSON
    with open(output_path, 'r') as f:
        metrics = json.load(f)
        
    assert "datasets" in metrics, "Metrics should contain 'datasets' key"
    assert len(metrics["datasets"]) > 0, "Metrics should contain at least one dataset"
    
    for ds in metrics["datasets"]:
        # Check for t-test results if they exist
        if "t_test" in ds:
            p_val = ds["t_test"].get("p_value")
            ci = ds["t_test"].get("ci")
            
            assert p_val is not None, "T-test should have a p-value"
            assert 0 < p_val < 1, f"P-value {p_val} should be between 0 and 1"
            
            if ci:
                assert len(ci) == 2, "CI should have 2 bounds"
                assert all(isinstance(x, (int, float)) and np.isfinite(x) for x in ci), "CI bounds should be finite"
                
        # Check for regression results if they exist
        if "regression" in ds:
            r_sq = ds["regression"].get("r_squared")
            if r_sq is not None:
                assert 0 <= r_sq <= 1, f"R-squared {r_sq} should be between 0 and 1"
                
def test_load_datasets_from_raw(sample_data_dir):
    """Test loading datasets from raw directory."""
    datasets = load_datasets_from_raw(str(sample_data_dir))
    assert len(datasets) == 1, "Should load exactly one dataset"
    df, name = datasets[0]
    assert df.shape[0] == 100, "Dataset should have 100 rows"
    assert name == "sample_data", "Dataset name should match file name"