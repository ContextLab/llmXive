"""
Contract and Integration tests for RSA output schema and permutation test convergence (User Story 3).

These tests verify that:
1. RSA outputs conform to the schema defined in:
   specs/001-neural-narrative-networks/contracts/rsa-output.schema.yaml
2. The permutation test convergence logic works correctly (integration test).

Tests run without executing the full RSA pipeline; they validate the structure
of example data against the contract and simulate the convergence logic.
"""
import json
import os
import sys
from pathlib import Path
from typing import Any, Dict
import time

import pytest
import yaml
import numpy as np

# Add project root to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "code"))

from utils.schema_validation import validate_rsa_output
from utils.logging_config import get_logger, info, error, warning


def load_test_rsa_data() -> Dict[str, Any]:
    """
    Load a minimal but complete RSA output example for testing.
    
    This mimics the structure expected by the RSA output schema without
    requiring the full pipeline to have run.
    """
    return {
        "metadata": {
            "dataset": "ds001495",
            "subjects": ["sub-01", "sub-02"],
            "rois": ["left_hippocampus", "right_hippocampus", "dlpfc"],
            "model_comparison": "brain_inspired_vs_baseline",
            "timestamp": "2026-05-31T12:00:00Z"
        },
        "rsa_matrix": [
            {
                "subject_id": "sub-01",
                "roi": "left_hippocampus",
                "story_pair": ["story_001", "story_002"],
                "neural_distance": 0.42,
                "model_distance_brain": 0.38,
                "model_distance_baseline": 0.65,
                "correlation": 0.87
            },
            {
                "subject_id": "sub-01",
                "roi": "left_hippocampus",
                "story_pair": ["story_001", "story_003"],
                "neural_distance": 0.51,
                "model_distance_brain": 0.49,
                "model_distance_baseline": 0.72,
                "correlation": 0.91
            },
            {
                "subject_id": "sub-02",
                "roi": "dlpfc",
                "story_pair": ["story_002", "story_003"],
                "neural_distance": 0.33,
                "model_distance_brain": 0.31,
                "model_distance_baseline": 0.58,
                "correlation": 0.85
            }
        ],
        "permutation_test": {
            "n_permutations": 10000,
            "p_value": 0.003,
            "converged": True,
            "threshold": 0.05
        }
    }


def test_rsa_schema_exists():
    """Verify that the RSA output schema file exists."""
    schema_path = (
        project_root / "specs" / "001-neural-narrative-networks" / "contracts" / "rsa-output.schema.yaml"
    )
    assert schema_path.exists(), f"RSA output schema not found at {schema_path}"


def test_rsa_output_validates_correctly():
    """
    Contract test: Verify that valid RSA output passes schema validation.
    
    This test ensures that the schema validation function correctly accepts
    properly structured RSA output data.
    """
    test_data = load_test_rsa_data()
    assert validate_rsa_output(test_data) is True, "Valid RSA data should pass validation"


def test_rsa_output_missing_metadata_fails():
    """
    Contract test: Verify that RSA output without metadata fails validation.
    """
    invalid_data = load_test_rsa_data()
    del invalid_data["metadata"]
    assert validate_rsa_output(invalid_data) is False, "RSA data missing metadata should fail validation"


def test_rsa_output_missing_matrix_fails():
    """
    Contract test: Verify that RSA output without rsa_matrix fails validation.
    """
    invalid_data = load_test_rsa_data()
    del invalid_data["rsa_matrix"]
    assert validate_rsa_output(invalid_data) is False, "RSA data missing rsa_matrix should fail validation"


def test_rsa_output_missing_permutation_test_fails():
    """
    Contract test: Verify that RSA output without permutation_test fails validation.
    """
    invalid_data = load_test_rsa_data()
    del invalid_data["permutation_test"]
    assert validate_rsa_output(invalid_data) is False, "RSA data missing permutation_test should fail validation"


def test_rsa_matrix_entry_required_fields():
    """
    Contract test: Verify that rsa_matrix entries with missing required fields fail.
    """
    valid_data = load_test_rsa_data()
    # Remove required field from first entry
    del valid_data["rsa_matrix"][0]["neural_distance"]
    assert validate_rsa_output(valid_data) is False, "RSA matrix entry missing neural_distance should fail"


def test_rsa_matrix_entry_type_validation():
    """
    Contract test: Verify that rsa_matrix entries with wrong types fail.
    """
    valid_data = load_test_rsa_data()
    # Set neural_distance to a string instead of float
    valid_data["rsa_matrix"][0]["neural_distance"] = "not_a_number"
    assert validate_rsa_output(valid_data) is False, "RSA matrix entry with wrong type should fail"


def test_rsa_permutation_test_required_fields():
    """
    Contract test: Verify that permutation_test with missing required fields fails.
    """
    valid_data = load_test_rsa_data()
    del valid_data["permutation_test"]["p_value"]
    assert validate_rsa_output(valid_data) is False, "Permutation test missing p_value should fail"


# --- Integration Tests for Permutation Test Convergence ---

def simulate_permutation_p_values(n_permutations: int, true_p: float = 0.03, noise_level: float = 0.005) -> list:
    """
    Simulate a sequence of p-values as if they were coming from a running permutation test.
    The values converge towards 'true_p' with some noise that decreases over time.
    """
    p_values = []
    current_p = true_p
    for i in range(n_permutations):
        # Simulate convergence: noise decreases as 1/sqrt(i)
        noise = np.random.normal(0, noise_level / np.sqrt(i + 1))
        current_p = true_p + noise
        p_values.append(max(0.0, min(1.0, current_p)))
    return p_values


def check_convergence(p_values: list, window_size: int = 1000, threshold: float = 0.001) -> bool:
    """
    Check if the p-value sequence has converged.
    Convergence is defined as the variance of the last 'window_size' values being < 'threshold'.
    """
    if len(p_values) < window_size:
        return False
    
    window = p_values[-window_size:]
    variance = np.var(window)
    return variance < threshold


def test_permutation_test_convergence_logic():
    """
    Integration test: Verify that the convergence check logic works correctly.
    
    This test simulates a permutation test running and verifies that:
    1. Convergence is NOT detected early in the process.
    2. Convergence IS detected after sufficient iterations with stable values.
    """
    # Simulate 2000 permutations where p-values stabilize after ~1500
    n_total = 2000
    p_values = simulate_permutation_p_values(n_total)
    
    # Check early (should be False)
    assert not check_convergence(p_values[:500], window_size=100), "Should not converge early"
    
    # Check late (should be True)
    assert check_convergence(p_values, window_size=1000), "Should converge after sufficient iterations"


def test_permutation_test_convergence_with_noise():
    """
    Integration test: Verify convergence logic handles high noise correctly (does not converge).
    """
    # Simulate with high noise that never stabilizes
    n_total = 2000
    p_values_high_noise = simulate_permutation_p_values(n_total, noise_level=0.1)
    
    # Even at the end, variance should be high
    window = p_values_high_noise[-1000:]
    variance = np.var(window)
    
    # Assert that with high noise, it does NOT converge
    assert variance > 0.001, "High noise should prevent convergence"
    assert not check_convergence(p_values_high_noise, window_size=1000), "High noise should prevent convergence"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])