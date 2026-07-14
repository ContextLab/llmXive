import pytest
import pandas as pd
import numpy as np
from datetime import datetime
import os
import json
import tempfile

from analysis import run_baseline_analysis, run_t_test, run_linear_regression, analyze_dataset

def test_run_t_test():
    """Test t-test calculation."""
    data = pd.DataFrame({"col1": [1.0, 2.0, 3.0, 4.0, 5.0]})
    result = run_t_test(data, "col1")
    
    assert "p_value" in result
    assert 0 < result["p_value"] < 1
    assert "ci_95" in result
    assert len(result["ci_95"]) == 2
    assert "cohen_d" in result

def test_run_linear_regression():
    """Test linear regression calculation."""
    data = pd.DataFrame({
        "x": [1.0, 2.0, 3.0, 4.0, 5.0],
        "y": [2.0, 4.0, 5.0, 4.0, 5.0]
    })
    result = run_linear_regression(data, "x", "y")
    
    assert "r_squared" in result
    assert "coefficient" in result
    assert "p_value" in result
    assert 0 <= result["r_squared"] <= 1

def test_run_baseline_analysis_dataframe():
    """Test run_baseline_analysis with DataFrame input."""
    data = pd.DataFrame({
        "x": [1.0, 2.0, 3.0, 4.0, 5.0],
        "y": [2.0, 4.0, 5.0, 4.0, 5.0]
    })
    
    result = run_baseline_analysis(data, dataset_name="test_dataset")
    
    assert isinstance(result, dict)
    assert result["dataset_name"] == "test_dataset"
    assert "t_tests" in result
    assert "regressions" in result

def test_run_baseline_analysis_directory():
    """Test run_baseline_analysis with directory input."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create a test CSV
        df = pd.DataFrame({
            "x": [1.0, 2.0, 3.0, 4.0, 5.0],
            "y": [2.0, 4.0, 5.0, 4.0, 5.0]
        })
        csv_path = os.path.join(tmpdir, "test.csv")
        df.to_csv(csv_path, index=False)
        
        output_file = os.path.join(tmpdir, "output.json")
        
        result = run_baseline_analysis(tmpdir, output_file)
        
        assert result is True
        assert os.path.exists(output_file)
        
        with open(output_file, 'r') as f:
            data = json.load(f)
        
        assert "generated_at" in data
        assert "datasets" in data
        assert len(data["datasets"]) == 1

def test_run_baseline_analysis_missing_column():
    """Test handling of missing columns."""
    data = pd.DataFrame({"col1": [1.0, 2.0, 3.0]})
    result = run_t_test(data, "nonexistent")
    
    assert "error" in result

def test_run_baseline_analysis_insufficient_data():
    """Test handling of insufficient data."""
    data = pd.DataFrame({"col1": [1.0]})
    result = run_t_test(data, "col1")
    
    assert "error" in result