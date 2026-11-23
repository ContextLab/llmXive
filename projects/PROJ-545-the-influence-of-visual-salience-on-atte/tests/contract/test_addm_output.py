"""
Contract tests for aDDM Model Output Schema.
Verifies that the fitted model parameters adhere to the expected schema.
"""
import json
import pytest
from pathlib import Path
from typing import Dict, Any
import sys
import os

# Ensure project root is in path for imports if running from root
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

REQUIRED_KEYS = [
    "log_likelihood", "drift_rate", "threshold", "salience_weight",
    "aic", "bic", "converged"
]

@pytest.fixture
def sample_model_params() -> Dict[str, Any]:
    """
    Fixture to load the actual fitted parameters from the pipeline output.
    This ensures the contract test validates the real artifact produced by T025.
    """
    output_path = PROJECT_ROOT / "data" / "processed" / "addm_fitted_params.json"
    
    if not output_path.exists():
        pytest.fail(f"Model output file not found at {output_path}. "
                    "Run the fitting pipeline (T020-T025) before running this test.")
    
    with open(output_path, 'r') as f:
        data = json.load(f)
    
    # Handle case where the file might contain a list of results or a single dict
    # Based on T025 spec, it saves "best parameters and log-likelihood"
    # We assume the top-level is the params dict or a dict containing a 'best' key.
    # If it's a list, we take the first one (or the best one if marked).
    if isinstance(data, list):
        if len(data) == 0:
            pytest.fail("Model output list is empty.")
        # If list, assume the first is the best or we need to find the one with max log_likelihood
        # For simplicity in contract test, we take the first if it looks like params
        data = data[0]
    
    return data

def test_schema_structure(sample_model_params: Dict[str, Any]):
    """
    Contract Test: Verify output JSON contains required keys.
    """
    missing = set(REQUIRED_KEYS) - set(sample_model_params.keys())
    assert len(missing) == 0, f"Missing required keys in model params: {missing}"

def test_schema_numeric_types(sample_model_params: Dict[str, Any]):
    """
    Contract Test: Verify numeric fields are actually numeric.
    """
    numeric_fields = ["log_likelihood", "drift_rate", "threshold", "salience_weight", "aic", "bic"]
    for field in numeric_fields:
        assert isinstance(sample_model_params[field], (int, float)), f"Field '{field}' is not numeric"

def test_schema_threshold_range(sample_model_params: Dict[str, Any]):
    """
    Contract Test: Verify threshold is within expected bounds (0, 1).
    """
    threshold = sample_model_params["threshold"]
    assert 0.0 < threshold < 1.0, f"Threshold {threshold} is out of expected range (0, 1)"

def test_schema_salience_weight_range(sample_model_params: Dict[str, Any]):
    """
    Contract Test: Verify salience_weight is within [0.0, 1.0].
    """
    weight = sample_model_params["salience_weight"]
    assert 0.0 <= weight <= 1.0, f"Salience weight {weight} is out of range [0.0, 1.0]"

def test_schema_converged_flag(sample_model_params: Dict[str, Any]):
    """
    Contract Test: Verify converged is a boolean.
    """
    assert isinstance(sample_model_params["converged"], bool), "Converged flag must be boolean"
    
    # Additional logical check: if not converged, log_likelihood might be invalid or -inf
    if not sample_model_params["converged"]:
        # We allow non-converged runs in the file, but the contract ensures the flag is present
        pass