"""
Contract test for the final results schema (User Story 3).

This test validates that the output from the regression and theory comparison
pipeline adheres to the expected schema defined in contracts/analysis_output.schema.yaml
(specifically the final results section) and the GapResult data model.

It verifies:
1. The existence of the output file.
2. The presence of required top-level keys.
3. The data types and value constraints for critical fields (slope, intercept, p_values, etc.).
4. Compatibility with the GapResult model structure if loaded.
"""

import os
import sys
import json
import pytest
from pathlib import Path

# Add project root to path to allow imports if needed for model validation
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Import the GapResult model to ensure schema alignment
try:
    from models.gap_result import GapResult
except ImportError:
    # Fallback if models are not yet fully importable in test env, 
    # but we rely on the file structure validation below.
    GapResult = None


RESULTS_FILE_PATH = Path(PROJECT_ROOT) / "data" / "processed" / "final_results.json"

# Expected schema structure based on FR-007 and GapResult model
EXPECTED_KEYS = [
    "slope",
    "slope_uncertainty",
    "intercept",
    "intercept_uncertainty",
    "r_squared",
    "n_bins",
    "photoevaporation_p_value",
    "core_powered_p_value",
    "favored_theory",
    "confidence_level",
    "timestamp",
    "methodology"
]

def test_results_file_exists():
    """Verify that the final results file has been generated."""
    assert RESULTS_FILE_PATH.exists(), (
        f"Final results file not found at {RESULTS_FILE_PATH}. "
        "Ensure T032 (regression) and T034 (theory comparison) have been run successfully."
    )

def test_results_is_valid_json():
    """Verify the file is valid JSON."""
    try:
        with open(RESULTS_FILE_PATH, 'r') as f:
            json.load(f)
    except json.JSONDecodeError as e:
        pytest.fail(f"Final results file is not valid JSON: {e}")

def test_results_schema_structure():
    """Verify the top-level keys match the expected schema."""
    with open(RESULTS_FILE_PATH, 'r') as f:
        data = json.load(f)

    missing_keys = [key for key in EXPECTED_KEYS if key not in data]
    assert not missing_keys, (
        f"Missing required keys in final results schema: {missing_keys}. "
        f"Expected keys: {EXPECTED_KEYS}"
    )

def test_numeric_fields_types():
    """Verify numeric fields are floats and within reasonable ranges."""
    with open(RESULTS_FILE_PATH, 'r') as f:
        data = json.load(f)

    numeric_fields = [
        "slope", "slope_uncertainty", 
        "intercept", "intercept_uncertainty", 
        "r_squared"
    ]

    for field in numeric_fields:
        assert isinstance(data[field], (int, float)), (
            f"Field '{field}' must be a number, got {type(data[field])}"
        )
        # Reasonable range check for slope (exoplanet radius gap slope is typically between -0.5 and 0.0)
        if field == "slope":
            assert -1.0 <= data[field] <= 1.0, (
                f"Slope value {data[field]} is outside expected physical range [-1.0, 1.0]"
            )
        # R-squared must be between 0 and 1
        if field == "r_squared":
            assert 0.0 <= data[field] <= 1.0, (
                f"R-squared value {data[field]} is outside valid range [0.0, 1.0]"
            )

def test_p_values_types_and_range():
    """Verify p-values are floats between 0 and 1."""
    with open(RESULTS_FILE_PATH, 'r') as f:
        data = json.load(f)

    p_value_keys = [
        "photoevaporation_p_value",
        "core_powered_p_value"
    ]

    for key in p_value_keys:
        assert isinstance(data[key], (int, float)), (
            f"P-value '{key}' must be a number, got {type(data[key])}"
        )
        assert 0.0 <= data[key] <= 1.0, (
            f"P-value '{key}' ({data[key]}) is outside valid range [0.0, 1.0]"
        )

def test_favored_theory_value():
    """Verify the favored_theory is one of the expected strings."""
    with open(RESULTS_FILE_PATH, 'r') as f:
        data = json.load(f)

    valid_theories = ["photoevaporation", "core-powered mass loss", "inconclusive", "neither"]
    assert data["favored_theory"] in valid_theories, (
        f"favored_theory '{data['favored_theory']}' is not in valid options: {valid_theories}"
    )

def test_gap_result_model_compatibility():
    """
    Verify that the JSON data can be used to construct a GapResult object
    (if the model is available and complete).
    """
    if GapResult is None:
        pytest.skip("GapResult model not importable; skipping model compatibility check.")

    with open(RESULTS_FILE_PATH, 'r') as f:
        data = json.load(f)

    try:
        # Attempt to create an instance. If the schema matches the model, this should pass.
        # We map the JSON keys to the expected dataclass fields.
        # Note: GapResult might have specific field names, we assume a mapping or direct from_dict.
        # Since we don't see the full GapResult implementation here, we check if 'from_dict' exists
        # or if we can instantiate with **data (assuming field names match JSON keys).
        
        # Strategy: Check if the keys in data match the fields in the dataclass
        import inspect
        if hasattr(GapResult, '__dataclass_fields__'):
            model_fields = set(GapResult.__dataclass_fields__.keys())
            json_keys = set(data.keys())
            
            # Check if all json keys are valid model fields (or at least the critical ones)
            # We allow extra keys in JSON that might be metadata, but critical analysis keys must match.
            critical_keys = {"slope", "slope_uncertainty", "favored_theory", "p_value"}
            
            # If the model is strictly typed, this is a strong contract test.
            # For now, we just ensure we can access the values via the model's expected structure
            # if a from_dict method exists.
            if hasattr(GapResult, 'from_dict'):
                instance = GapResult.from_dict(data)
                assert instance is not None
            else:
                # Fallback: just check field names
                missing_in_model = critical_keys - model_fields
                if missing_in_model:
                    pytest.fail(f"Critical keys {missing_in_model} missing from GapResult model fields.")
                    
    except TypeError as e:
        pytest.fail(f"JSON data cannot be mapped to GapResult model: {e}")
    except Exception as e:
        pytest.fail(f"GapResult model validation failed: {e}")