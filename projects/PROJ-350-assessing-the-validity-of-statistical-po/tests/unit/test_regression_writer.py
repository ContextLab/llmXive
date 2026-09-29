"""
Unit tests for the regression results writer module.
"""
import json
import tempfile
from pathlib import Path

import pytest

from regression_results_writer import write_regression_results

@pytest.fixture
def mock_results():
    return {
        "model_summary": {
            "r_squared": 0.25,
            "adj_r_squared": 0.22,
            "f_statistic": 10.5,
            "f_statistic_pvalue": 0.0001,
            "n_obs": 100,
            "n_params": 3,
            "formula": "power_gap ~ C(field) + effect_size_domain",
            "model_type": "OLS"
        },
        "coefficients": [
            {
                "term": "Intercept",
                "estimate": 0.1,
                "std_err": 0.02,
                "p_value": 0.001,
                "conf_int": [0.06, 0.14]
            }
        ],
        "vif_diagnostics": [
            {"term": "Intercept", "vif_factor": 1.0}
        ],
        "warnings": []
    }

def test_write_regression_results_creates_file(mock_results, tmp_path):
    """Test that the writer creates the file and writes valid JSON."""
    output_file = tmp_path / "results.json"
    
    write_regression_results(
        mock_results,
        output_file,
        input_file="data/derived/power_analysis.csv",
        excluded_predictors=["sample_size_category"]
    )
    
    assert output_file.exists()
    
    with open(output_file, 'r') as f:
        data = json.load(f)
    
    assert "model_summary" in data
    assert "coefficients" in data
    assert "vif_diagnostics" in data
    assert "metadata" in data
    assert data["metadata"]["excluded_predictors"] == ["sample_size_category"]

def test_write_regression_results_handles_empty_warnings(mock_results, tmp_path):
    """Test that empty warnings list is handled correctly."""
    mock_results["warnings"] = []
    output_file = tmp_path / "results.json"
    
    write_regression_results(
        mock_results,
        output_file,
        input_file="data/derived/power_analysis.csv"
    )
    
    with open(output_file, 'r') as f:
        data = json.load(f)
    
    assert data["warnings"] == []