"""
Contract test for aDDM model output schema.
Verifies that the JSON output from the model fitting stage contains
the required fields and types.
"""
import os
import sys
import json
import pytest
from pathlib import Path
from typing import Any, Dict, List, Optional

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# Constants for schema validation
REQUIRED_KEYS = [
    'log_likelihood',
    'drift_rate',
    'threshold',
    'salience_weight'
]

REQUIRED_NUMERIC_KEYS = [
    'log_likelihood',
    'drift_rate',
    'threshold',
    'salience_weight'
]


def load_test_artifact(path: str) -> Dict[str, Any]:
    """
    Helper to load a JSON artifact for testing.
    Raises FileNotFoundError if the file does not exist.
    """
    full_path = project_root / path
    if not full_path.exists():
        raise FileNotFoundError(f"Contract test artifact not found: {full_path}")
    
    with open(full_path, 'r') as f:
        return json.load(f)


class TestAddmOutputSchema:
    """
    Contract test suite for User Story 2: aDDM Simulation and Parameter Fitting.
    
    These tests ensure that the model fitting process produces a valid JSON
    structure with the necessary parameters for downstream analysis.
    """

    def test_addm_output_contains_required_keys(self):
        """
        Contract test: Verify output JSON contains `log_likelihood`, `drift_rate`, 
        `threshold`, `salience_weight`.
        """
        artifact_path = "data/processed/addm_fitted_params.json"
        
        try:
            data = load_test_artifact(artifact_path)
        except FileNotFoundError:
            pytest.skip(
                f"Artifact {artifact_path} not found. "
                "This is expected if T025 (fit) has not been run yet."
            )

        # Check if data is a dict (top level)
        assert isinstance(data, dict), (
            f"Contract violation: Expected root object to be a dict, got {type(data)}"
        )

        # Check for required keys
        missing_keys = [key for key in REQUIRED_KEYS if key not in data]
        assert not missing_keys, (
            f"Contract violation: Missing required keys: {missing_keys}. "
            f"Found keys: {list(data.keys())}"
        )

    def test_addm_output_values_are_numeric(self):
        """
        Contract test: Verify that required parameter values are numeric.
        """
        artifact_path = "data/processed/addm_fitted_params.json"
        
        try:
            data = load_test_artifact(artifact_path)
        except FileNotFoundError:
            pytest.skip(
                f"Artifact {artifact_path} not found. "
                "This is expected if T025 (fit) has not been run yet."
            )

        for key in REQUIRED_NUMERIC_KEYS:
            value = data.get(key)
            assert value is not None, f"Contract violation: Key '{key}' is missing."
            assert isinstance(value, (int, float)), (
                f"Contract violation: Key '{key}' must be numeric. "
                f"Got type: {type(value)}, value: {value}"
            )

    def test_addm_output_salience_weight_range(self):
        """
        Contract test: Verify `salience_weight` is within expected bounds [0.0, 1.0].
        (Based on T021 grid search step 0.1 to 1.0)
        """
        artifact_path = "data/processed/addm_fitted_params.json"
        
        try:
            data = load_test_artifact(artifact_path)
        except FileNotFoundError:
            pytest.skip(
                f"Artifact {artifact_path} not found. "
                "This is expected if T025 (fit) has not been run yet."
            )

        weight = data.get('salience_weight')
        if weight is not None:
            assert 0.0 <= weight <= 1.0, (
                f"Contract violation: 'salience_weight' ({weight}) is outside [0.0, 1.0]."
            )
    
    def test_addm_output_log_likelihood_negative(self):
        """
        Contract test: Verify `log_likelihood` is negative (standard for log-likelihoods).
        """
        artifact_path = "data/processed/addm_fitted_params.json"
        
        try:
            data = load_test_artifact(artifact_path)
        except FileNotFoundError:
            pytest.skip(
                f"Artifact {artifact_path} not found. "
                "This is expected if T025 (fit) has not been run yet."
            )

        ll = data.get('log_likelihood')
        if ll is not None:
            # Log likelihoods are typically negative numbers (sum of logs of probabilities <= 1)
            # Allow a small tolerance for 0 if perfect fit (unlikely)
            assert ll <= 0.0, (
                f"Contract violation: 'log_likelihood' ({ll}) is positive. "
                "Log-likelihoods should be <= 0."
            )
