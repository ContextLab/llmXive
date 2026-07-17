"""
Contract tests for the VIF report schema (results/statistics/vif_report.json).
"""
import os
import json
import pytest
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.parent
DATA_PATH = PROJECT_ROOT / "results" / "statistics" / "vif_report.json"

def test_vif_report_exists():
    """Test that the VIF report file exists."""
    assert DATA_PATH.exists(), f"VIF report file not found: {DATA_PATH}"

def test_vif_report_structure():
    """Test that the VIF report has the expected structure."""
    if not DATA_PATH.exists():
        pytest.skip("VIF report file not found.")
    
    with open(DATA_PATH, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Expected structure: dict with predictor names as keys and VIF scores as values
    # or a list of objects with 'predictor' and 'vif' keys.
    # Based on typical implementation, we expect a dict or list.
    
    if isinstance(data, dict):
        for key, value in data.items():
            assert isinstance(key, str), f"Key '{key}' must be a string"
            assert isinstance(value, (int, float)), f"Value for '{key}' must be a number"
    elif isinstance(data, list):
        for item in data:
            assert isinstance(item, dict), "Each item in VIF list must be a dictionary"
            assert "predictor" in item, "Missing 'predictor' key in VIF item"
            assert "vif" in item, "Missing 'vif' key in VIF item"
            assert isinstance(item["predictor"], str)
            assert isinstance(item["vif"], (int, float))
    else:
        pytest.fail(f"VIF report has unexpected type: {type(data)}")
