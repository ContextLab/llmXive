import os
import json
import pytest
from pathlib import Path

def test_model_metrics_schema():
    """
    Contract test for model_metrics.json schema (T018).
    Verifies R², RMSE, and disclaimer exist.
    """
    metrics_path = Path("data/results/model_metrics.json")
    assert metrics_path.exists(), "model_metrics.json not found. Run code/03_train.py first."
    
    with open(metrics_path, 'r') as f:
        data = json.load(f)
    
    assert 'r2' in data, "Missing 'r2' key in metrics."
    assert 'rmse' in data, "Missing 'rmse' key in metrics."
    assert isinstance(data['r2'], (int, float)), "'r2' must be numeric."
    assert isinstance(data['rmse'], (int, float)), "'rmse' must be numeric."
    
    # T025 Requirement: Disclaimer must be present
    assert 'disclaimer' in data, "Missing 'disclaimer' key in metrics."
    assert "associational" in data['disclaimer'].lower(), "Disclaimer must mention 'associational'."

def test_nested_cv_integration():
    """
    Integration test for cross-validation loop (T019).
    Checks that the training script produces a model file and valid metrics.
    """
    # This test assumes the script has been run. 
    # In a real CI, we might trigger the script, but here we verify outputs.
    model_path = Path("data/models/random_forest.pkl")
    metrics_path = Path("data/results/model_metrics.json")
    
    assert model_path.exists(), "Model artifact not found. Run code/03_train.py."
    assert metrics_path.exists(), "Metrics artifact not found. Run code/03_train.py."
    
    with open(metrics_path, 'r') as f:
        metrics = json.load(f)
    
    # Basic sanity check: R2 should be < 1.0 (perfect) and typically > -1.0 (random/bad)
    # In real data, it might be low, but it should be a valid float.
    r2 = metrics.get('r2')
    assert -2.0 <= r2 <= 1.0, f"R² value {r2} is outside expected bounds for a valid regression model."

def test_disclaimer_in_interpretation_report():
    """
    Test for T025: Verify interpretation_report.json contains the associational disclaimer.
    """
    report_path = Path("data/results/interpretation_report.json")
    assert report_path.exists(), "interpretation_report.json not found. Run code/06_generate_report.py first."
    
    with open(report_path, 'r') as f:
        data = json.load(f)
    
    assert 'disclaimer' in data, "Missing 'disclaimer' key in interpretation report."
    assert "associational" in data['disclaimer'].lower(), "Disclaimer in interpretation report must mention 'associational'."
    assert "observational" in data['disclaimer'].lower(), "Disclaimer in interpretation report must mention 'observational'."
