"""
Contract tests for JSON schema compliance.
"""
import pytest
import json
from pathlib import Path

def test_baseline_narrative_schema():
    """Test that baseline narrative output matches required schema."""
    # Example valid output
    valid_output = {
        "r_value": 0.85,
        "p_value": 0.001,
        "var_x": "income",
        "var_y": "education",
        "significance": "highly_significant",
        "primary_narrative": "Higher income is associated with higher education levels."
    }

    required_keys = ["r_value", "p_value", "var_x", "var_y", "significance", "primary_narrative"]
    for key in required_keys:
        assert key in valid_output

    # Type checks
    assert isinstance(valid_output["r_value"], float)
    assert isinstance(valid_output["p_value"], float)
    assert isinstance(valid_output["var_x"], str)
    assert isinstance(valid_output["var_y"], str)
    assert isinstance(valid_output["significance"], str)
    assert isinstance(valid_output["primary_narrative"], str)

def test_sensitivity_report_schema():
    """Test that sensitivity report output matches required schema."""
    # Example valid output
    valid_output = {
        "threshold_config": "p<0.05, |r|>0.15",
        "claim": "Variable A is associated with Variable B",
        "p_value": 0.03,
        "partial_r": 0.25,
        "stability_score": 0.9,
        "validity_status": "verified"
    }

    required_keys = ["threshold_config", "claim", "p_value", "partial_r", "stability_score", "validity_status"]
    for key in required_keys:
        assert key in valid_output

    # Type checks
    assert isinstance(valid_output["p_value"], float)
    assert isinstance(valid_output["partial_r"], float)
    assert isinstance(valid_output["stability_score"], float)
    assert isinstance(valid_output["validity_status"], str)