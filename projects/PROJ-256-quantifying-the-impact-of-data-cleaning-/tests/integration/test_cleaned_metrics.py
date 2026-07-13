import os
import json
import pytest
import pandas as pd
import numpy as np
from pathlib import Path

# Import the main function to test
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))
from t023_reanalyze_cleaned_variants import main, find_cleaned_datasets, analyze_cleaned_variant

@pytest.fixture
def temp_processed_dir(tmp_path):
    """Create a temporary processed directory with dummy cleaned CSVs."""
    processed_dir = tmp_path / "data" / "processed"
    processed_dir.mkdir(parents=True)
    
    # Create a dummy dataset with numeric columns and a binary column for t-test
    data = {
        "feature1": [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0],
        "feature2": [10.0, 20.0, 30.0, 40.0, 50.0, 60.0, 70.0, 80.0, 90.0, 100.0],
        "outcome": [2.0, 4.0, 6.0, 8.0, 10.0, 12.0, 14.0, 16.0, 18.0, 20.0],
        "group": [0, 0, 0, 0, 0, 1, 1, 1, 1, 1]
    }
    df = pd.DataFrame(data)
    filepath = processed_dir / "test_dataset_iqr.csv"
    df.to_csv(filepath, index=False)
    
    return processed_dir

def test_find_cleaned_datasets(temp_processed_dir):
    files = find_cleaned_datasets(str(temp_processed_dir))
    assert len(files) == 1
    assert "test_dataset_iqr.csv" in files[0]

def test_analyze_cleaned_variant(temp_processed_dir):
    filepath = temp_processed_dir / "test_dataset_iqr.csv"
    result = analyze_cleaned_variant(str(filepath), "iqr", seed=42)
    
    assert result is not None
    assert result["cleaning_strategy"] == "iqr"
    assert result["n_rows"] == 10
    assert "analysis" in result
    
    # Check t-test results if binary column exists
    if "t_test" in result["analysis"]:
        t_test_res = result["analysis"]["t_test"]
        assert "p_value" in t_test_res
        assert 0 < t_test_res["p_value"] < 1
        assert "ci_lower" in t_test_res
        assert "ci_upper" in t_test_res
        assert t_test_res["ci_lower"] < t_test_res["ci_upper"]
    
    # Check regression results
    if "regression" in result["analysis"]:
        reg_res = result["analysis"]["regression"]
        assert "r_squared" in reg_res
        assert 0 <= reg_res["r_squared"] <= 1
        assert "coefficients" in reg_res
        assert len(reg_res["coefficients"]) > 0

def test_main_writes_output(temp_processed_dir, tmp_path):
    # Override output path via environment or mock config if necessary
    # For this test, we assume the config defaults to the processed_dir
    # We need to ensure the output file is created
    
    # Run the main function
    # Note: This might need config mocking if it reads from env vars
    # Assuming default config behavior
    exit_code = main()
    
    # Check if the output file was created
    output_path = temp_processed_dir / "cleaned_metrics.json"
    assert output_path.exists(), "cleaned_metrics.json was not created"
    
    with open(output_path, 'r') as f:
        data = json.load(f)
    
    assert "datasets_analyzed" in data
    assert data["datasets_analyzed"] > 0
    assert "datasets" in data
    assert len(data["datasets"]) > 0
    
    # Validate structure of a dataset entry
    entry = data["datasets"][0]
    assert "analysis" in entry
    assert "t_test" in entry["analysis"] or "regression" in entry["analysis"]