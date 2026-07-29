"""
Tests for T026 and related analysis functions.
"""
import json
import os
import sys
import tempfile
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
from scipy import stats

# Add code to path
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))

from analysis import (
    compute_correlation_matrix,
    compute_p_values,
    identify_significant_correlations,
    run_mlr,
    perform_residual_diagnostics,
    verify_residual_diagnostics,
    save_analysis_results
)
from error_handlers import StatisticalInsufficiencyError

@pytest.fixture
def mock_data():
    """Generate a mock dataset for testing."""
    np.random.seed(42)
    n = 100
    data = {
        "tpsa": np.random.normal(50, 20, n),
        "rotatable_bonds": np.random.normal(5, 2, n),
        "mw": np.random.normal(300, 50, n),
        "aromatic_rings": np.random.normal(2, 1, n),
        "wiener_index": np.random.normal(10, 3, n),
        "zagreb_index": np.random.normal(20, 5, n),
        "half_life": np.random.normal(100, 20, n)
    }
    # Add some correlation
    data["half_life"] = data["half_life"] + 0.5 * data["tpsa"]
    return pd.DataFrame(data)

@pytest.fixture
def mock_gate_status_pass(tmp_path):
    """Mock gate_status.json indicating PASS."""
    gate_file = tmp_path / "gate_status.json"
    gate_file.write_text(json.dumps({"status": "PASS", "n": 100}))
    return gate_file

def test_compute_correlation_matrix(mock_data):
    features = ["tpsa", "mw"]
    target = "half_life"
    corr = compute_correlation_matrix(mock_data, features, target)

    assert "tpsa" in corr.columns
    assert "half_life" in corr.columns
    assert not corr.isnull().any().any()

def test_compute_p_values(mock_data):
    features = ["tpsa"]
    target = "half_life"
    p_vals = compute_p_values(mock_data, features, target)

    assert "tpsa" in p_vals
    assert p_vals["tpsa"] < 0.05  # Since we added correlation

def test_identify_significant_correlations(mock_data):
    features = ["tpsa", "mw"]
    target = "half_life"
    p_vals = compute_p_values(mock_data, features, target)
    sig = identify_significant_correlations(p_vals)

    # tpsa should be significant
    assert "tpsa" in sig

def test_run_mlr(mock_data):
    features = ["tpsa", "mw"]
    target = "half_life"
    res = run_mlr(mock_data, features, target)

    assert "r_squared" in res
    assert "coefficients" in res
    assert res["r_squared"] > 0

def test_perform_residual_diagnostics(mock_data):
    features = ["tpsa", "mw"]
    target = "half_life"
    # Run MLR first to get residuals context
    mlr_res = run_mlr(mock_data, features, target)
    diag = perform_residual_diagnostics(mlr_res, mock_data, features, target, model_type="MLR")

    assert "shapiro_wilk" in diag
    assert "breusch_pagan" in diag
    assert "statistic" in diag["shapiro_wilk"]
    assert "p_value" in diag["shapiro_wilk"]

def test_verify_residual_diagnostics():
    # Mock diagnostics
    diag = {
        "shapiro_wilk": {"p_value": 0.1}, # Pass
        "breusch_pagan": {"p_value": 0.01} # Fail
    }
    summary = verify_residual_diagnostics(diag)

    assert summary["normality_assumption"] == "PASS"
    assert summary["homoscedasticity_assumption"] == "FAIL"

def test_save_analysis_results(mock_data, tmp_path):
    """Test T026: Save analysis results to JSON."""
    # Mock some results
    mlr_res = {"r_squared": 0.5, "coefficients": {"tpsa": 1.0}}
    lasso_res = {"r_squared": 0.45, "coefficients": {"tpsa": 0.9}}
    corr = {"tpsa": {"half_life": 0.7}}
    p_vals = {"tpsa": 0.01}
    diag = {"normality_assumption": "PASS", "homoscedasticity_assumption": "PASS"}
    conclusion = "Test conclusion"

    output_path = tmp_path / "analysis_results.json"

    # We need to patch get_data_path to use tmp_path
    import analysis
    original_get_data_path = analysis.get_data_path
    analysis.get_data_path = lambda: tmp_path

    try:
        save_analysis_results(mlr_res, lasso_res, corr, p_vals, diag, conclusion)

        assert output_path.exists()
        with open(output_path) as f:
            data = json.load(f)

        assert "mlr_model" in data
        assert "lasso_model" in data
        assert "conclusion" in data
        assert data["mlr_model"]["r_squared"] == 0.5
    finally:
        analysis.get_data_path = original_get_data_path
