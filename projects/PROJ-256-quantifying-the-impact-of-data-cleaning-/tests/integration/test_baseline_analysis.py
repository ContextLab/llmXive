"""
Integration test for baseline analysis pipeline.
Verifies that the script produces a valid JSON with p-values and CIs.
"""
import os
import json
import tempfile
import shutil
import pytest
import pandas as pd
import numpy as np

from code.analysis import run_baseline_analysis, analyze_dataset
from code.config import get_config


@pytest.fixture
def temp_data_dir():
    """Create a temporary directory for test data."""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir)


@pytest.fixture
def sample_csv(temp_data_dir):
    """Create a simple CSV file with numeric and binary categorical columns."""
    data = {
        "group": ["A"] * 50 + ["B"] * 50,
        "value": np.random.normal(loc=10, scale=2, size=50).tolist() + 
                 np.random.normal(loc=12, scale=2, size=50).tolist(),
        "feature1": np.random.randn(100),
        "feature2": np.random.randn(100),
        "feature3": np.random.randn(100)
    }
    df = pd.DataFrame(data)
    csv_path = os.path.join(temp_data_dir, "test_dataset.csv")
    df.to_csv(csv_path, index=False)
    return csv_path


def test_baseline_analysis_produces_json(sample_csv, temp_data_dir):
    """
    Test that run_baseline_analysis produces a valid JSON file with required fields.
    """
    output_path = os.path.join(temp_data_dir, "baseline_metrics.json")
    
    # Run analysis on the single sample dataset
    result = run_baseline_analysis(datasets=[sample_csv], output_path=output_path)
    
    assert result is not None, "Analysis should return a result dictionary"
    assert os.path.exists(output_path), "Output JSON file should be created"
    
    with open(output_path, 'r') as f:
        data = json.load(f)
    
    assert "results" in data, "Result should contain 'results' key"
    assert len(data["results"]) > 0, "At least one dataset should be analyzed"
    
    dataset_res = data["results"][0]
    assert "analyses" in dataset_res, "Dataset result should contain 'analyses'"
    
    found_valid_pvalue = False
    found_valid_ci = False
    
    for analysis in dataset_res["analyses"]:
        metrics = analysis.get("metrics", {})
        if metrics.get("valid"):
            if "p_value" in metrics:
                p_val = metrics["p_value"]
                if isinstance(p_val, float) and 0 < p_val < 1:
                    found_valid_pvalue = True
                ci_lower = metrics.get("ci_lower")
                ci_upper = metrics.get("ci_upper")
                if isinstance(ci_lower, float) and isinstance(ci_upper, float) and np.isfinite(ci_lower) and np.isfinite(ci_upper):
                    found_valid_ci = True
            elif "p_values" in metrics:
                # Regression case
                p_vals = metrics["p_values"]
                if all(isinstance(p, float) and 0 < p < 1 for p in p_vals):
                    found_valid_pvalue = True
                ci_bounds = metrics.get("ci_bounds", [])
                if all(isinstance(b, list) and len(b) == 2 and all(np.isfinite(v) for v in b) for b in ci_bounds):
                    found_valid_ci = True
    
    # We expect at least one valid analysis to have passed validation
    # Note: With random data, sometimes t-tests might not be valid if variances are weird, 
    # but with 100 samples it's highly likely.
    # If the test fails here, it means the logic for validation or calculation is broken.
    assert found_valid_pvalue, "At least one valid p-value (0 < p < 1) should be found"
    assert found_valid_ci, "At least one valid CI (finite bounds) should be found"