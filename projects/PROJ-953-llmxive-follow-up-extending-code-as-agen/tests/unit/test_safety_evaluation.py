"""
Unit tests for the safety evaluation logic (T032).
"""
import pytest
import json
import tempfile
from pathlib import Path
from code.scripts.evaluate_safety import (
    evaluate_safety_constraint,
    update_model_report,
    load_threshold_sweep
)

def test_evaluate_safety_constraint_safe():
    """Test that a model with low FNR is marked safe."""
    sweep_data = {
        "thresholds": [0.01, 0.05, 0.1],
        "fnr_values": [0.0005, 0.0001, 0.0002],
        "min_achievable_fnr": 0.0001
    }
    assert evaluate_safety_constraint(sweep_data) is True

def test_evaluate_safety_constraint_unsafe():
    """Test that a model with high FNR is marked unsafe."""
    sweep_data = {
        "thresholds": [0.01, 0.05, 0.1],
        "fnr_values": [0.005, 0.002, 0.0015],
        "min_achievable_fnr": 0.0015  # > 0.001 (0.1%)
    }
    assert evaluate_safety_constraint(sweep_data) is False

def test_evaluate_safety_constraint_missing_fnr():
    """Test that missing min_achievable_fnr results in unsafe (conservative)."""
    sweep_data = {
        "thresholds": [0.01],
        "fnr_values": [0.0005]
        # Missing min_achievable_fnr
    }
    assert evaluate_safety_constraint(sweep_data) is False

def test_update_model_report_creates_file():
    """Test that update_model_report creates the file if it doesn't exist."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        report_path = Path(tmp_dir) / "model_report.json"
        sweep_data = {"min_achievable_fnr": 0.0001}
        
        update_model_report(True, sweep_data, report_path)
        
        assert report_path.exists()
        with open(report_path, 'r') as f:
            data = json.load(f)
        assert "safety_evaluation" in data
        assert data["safety_evaluation"]["constraint_met"] is True

def test_update_model_report_merges_existing():
    """Test that update_model_report merges into an existing report."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        report_path = Path(tmp_dir) / "model_report.json"
        
        # Create an existing report
        existing_data = {"existing_field": "value"}
        with open(report_path, 'w') as f:
            json.dump(existing_data, f)
        
        sweep_data = {"min_achievable_fnr": 0.0001}
        update_model_report(False, sweep_data, report_path)
        
        with open(report_path, 'r') as f:
            data = json.load(f)
        
        assert data["existing_field"] == "value"
        assert "safety_evaluation" in data
        assert data["safety_evaluation"]["constraint_met"] is False
