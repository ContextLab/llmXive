"""
Contract Test for T030: Linearity Check Output Schema.
Validates that the output JSON matches the expected schema defined in FR-007.
"""
import json
import os
from pathlib import Path

import pytest

# Path to the output file (relative to project root)
PROJECT_ROOT = Path(__file__).resolve().parents[2]
OUTPUT_PATH = PROJECT_ROOT / "data" / "results" / "linearity_check.json"

@pytest.mark.contract
def test_linearity_check_output_schema():
    """Verifies the output file exists and contains valid schema keys."""
    assert OUTPUT_PATH.exists(), f"Output file {OUTPUT_PATH} does not exist. Run src/validation/linearity_check.py first."

    with open(OUTPUT_PATH, 'r') as f:
        data = json.load(f)

    required_keys = {
        "correlation": (float, int),
        "validity": bool,
        "threshold": (float, int),
        "sample_size": int
    }

    for key, expected_types in required_keys.items():
        assert key in data, f"Missing required key: {key}"
        assert isinstance(data[key], expected_types), f"Key '{key}' has invalid type: {type(data[key])}"

    # Validate logic constraints
    assert -1.0 <= data["correlation"] <= 1.0, "Correlation must be between -1 and 1."
    assert data["validity"] is True or data["validity"] is False, "Validity must be a boolean."
    
    # If validity is True, correlation must be >= threshold
    if data["validity"]:
        assert data["correlation"] >= data["threshold"], "Validity is True but correlation < threshold."
    
    # If validity is False, correlation must be < threshold
    if not data["validity"]:
        assert data["correlation"] < data["threshold"], "Validity is False but correlation >= threshold."

@pytest.mark.contract
def test_linearity_check_p_value_exists():
    """Verifies that a p-value is reported (optional but expected)."""
    if not OUTPUT_PATH.exists():
        pytest.skip("Output file not found, skipping p-value check.")
    
    with open(OUTPUT_PATH, 'r') as f:
        data = json.load(f)
    
    assert "p_value" in data, "p_value key is missing from output."
    assert isinstance(data["p_value"], (float, int)), "p_value must be numeric."
    assert 0.0 <= data["p_value"] <= 1.0, "p_value must be between 0 and 1."
