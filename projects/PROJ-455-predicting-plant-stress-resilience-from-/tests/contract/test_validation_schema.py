"""
Contract test for validation results schema (T028).

This test verifies that the output of the validation pipeline (cross-stress eval,
LODO CV, permutation tests) conforms to the expected schema defined in
`contracts/validation_result.schema.yaml`.

It ensures that:
1. The output is a valid JSON/YAML document.
2. Required top-level fields exist (e.g., `validation_type`, `metrics`, `summary`).
3. Nested structures match the schema (e.g., `metrics` contains `r_squared`, `p_value`).
4. Data types are correct (e.g., scores are floats, lists are lists).
"""

import json
import os
import pytest
import yaml
from pathlib import Path
from typing import Any, Dict

# Import schema validation helper if available, otherwise use jsonschema or manual check
# Since the project uses Pydantic, we can also try to validate against a model if defined,
# but for contract tests, usually we validate against the JSON Schema file.
# Assuming jsonschema is installed or we do manual structural checks.
# Given the dependencies list, we might not have jsonschema explicitly, so we do manual checks
# or assume the schema file is the source of truth for structure.

try:
    import jsonschema
    HAS_JSONSCHEMA = True
except ImportError:
    HAS_JSONSCHEMA = False


# Path to the schema file
SCHEMA_PATH = Path("contracts/validation_result.schema.yaml")

@pytest.fixture
def validation_schema() -> Dict[str, Any]:
    """Load the validation result schema from the contracts directory."""
    if not SCHEMA_PATH.exists():
        pytest.fail(f"Schema file not found: {SCHEMA_PATH}. Ensure T004 or similar created it.")
    with open(SCHEMA_PATH, "r") as f:
        return yaml.safe_load(f)

@pytest.fixture
def sample_validation_result() -> Dict[str, Any]:
    """
    Generate a sample validation result that mimics the output of
    code/models/validate.py (e.g., lodo_cv, cross_stress_eval, permutation_test).
    This is used to test against the schema.
    """
    return {
        "validation_type": "cross_stress",
        "model_id": "rf_model_001",
        "train_stress": "drought",
        "test_stress": "heat",
        "metrics": {
            "r_squared": 0.45,
            "pearson_r": 0.62,
            "rmse": 12.3,
            "n_samples": 150
        },
        "permutation_test": {
            "p_value": 0.003,
            "n_permutations": 1000,
            "observed_score": 0.45,
            "mean_null_score": -0.02
        },
        "pathway_alignment": {
            "jaccard_similarity": 0.35,
            "enrichment_p_value": 0.04,
            "is_aligned": True
        },
        "summary": {
            "generalizability_score": "moderate",
            "biological_plausibility": True,
            "recommendation": "Proceed with caution"
        }
    }

def test_schema_file_structure(validation_schema: Dict[str, Any]):
    """Verify the schema file itself has the expected structure."""
    assert "type" in validation_schema
    assert validation_schema["type"] == "object"
    assert "properties" in validation_schema
    required_fields = ["validation_type", "metrics"]
    for field in required_fields:
        assert field in validation_schema["properties"], f"Required field '{field}' missing in schema."

def test_validation_result_conforms_to_schema(
    validation_schema: Dict[str, Any],
    sample_validation_result: Dict[str, Any]
):
    """
    Validate that a sample validation result conforms to the defined schema.
    """
    if HAS_JSONSCHEMA:
        jsonschema.validate(instance=sample_validation_result, schema=validation_schema)
    else:
        # Fallback: Manual structural validation if jsonschema is not available
        # This mimics the logic of the schema defined in contracts/
        props = validation_schema.get("properties", {})
        
        # Check top-level required fields
        for field in ["validation_type", "metrics", "summary"]:
            assert field in sample_validation_result, f"Missing required field: {field}"
        
        # Check types
        assert isinstance(sample_validation_result["validation_type"], str)
        assert isinstance(sample_validation_result["metrics"], dict)
        assert isinstance(sample_validation_result["summary"], dict)
        
        # Check metrics structure
        metrics = sample_validation_result["metrics"]
        assert "r_squared" in metrics or "pearson_r" in metrics
        assert isinstance(metrics.get("n_samples", 0), int)
        
        # Check permutation test if present
        if "permutation_test" in sample_validation_result:
            perm = sample_validation_result["permutation_test"]
            assert "p_value" in perm
            assert 0.0 <= perm["p_value"] <= 1.0
        
        # Check pathway alignment if present
        if "pathway_alignment" in sample_validation_result:
            align = sample_validation_result["pathway_alignment"]
            assert "jaccard_similarity" in align
            assert "is_aligned" in align
            assert isinstance(align["is_aligned"], bool)

def test_validation_result_types(sample_validation_result: Dict[str, Any]):
    """Ensure all numeric fields are numbers and boolean fields are booleans."""
    metrics = sample_validation_result["metrics"]
    assert isinstance(metrics["r_squared"], (int, float))
    assert isinstance(metrics["n_samples"], int)
    
    if "permutation_test" in sample_validation_result:
        assert isinstance(sample_validation_result["permutation_test"]["p_value"], (int, float))
    
    if "pathway_alignment" in sample_validation_result:
        assert isinstance(sample_validation_result["pathway_alignment"]["jaccard_similarity"], (int, float))
        assert isinstance(sample_validation_result["pathway_alignment"]["is_aligned"], bool)

def test_validation_result_serialization(sample_validation_result: Dict[str, Any]):
    """Ensure the result can be serialized to JSON and back."""
    try:
        json_str = json.dumps(sample_validation_result)
        restored = json.loads(json_str)
        assert restored == sample_validation_result
    except (TypeError, ValueError) as e:
        pytest.fail(f"Validation result failed JSON serialization: {e}")

def test_validation_result_file_output(tmp_path: Path, sample_validation_result: Dict[str, Any]):
    """
    Test that a validation result can be written to a file in the expected format
    (JSON or YAML) as per project conventions.
    """
    output_file = tmp_path / "validation_result.json"
    with open(output_file, "w") as f:
        json.dump(sample_validation_result, f, indent=2)
    
    assert output_file.exists()
    with open(output_file, "r") as f:
        loaded = json.load(f)
    
    assert loaded == sample_validation_result

def test_schema_completeness(validation_schema: Dict[str, Any]):
    """
    Verify that the schema includes definitions for all expected validation types
    (LODO, Cross-Stress, Permutation).
    """
    # Check if the schema allows for different validation types via enum or description
    validation_type_prop = validation_schema["properties"].get("validation_type", {})
    if "enum" in validation_type_prop:
        allowed_types = validation_type_prop["enum"]
        expected_types = ["lodo_cv", "cross_stress", "permutation_test"]
        for t in expected_types:
            assert t in allowed_types, f"Validation type '{t}' not in schema enum: {allowed_types}"
    else:
        # If no enum, check description mentions them
        desc = validation_type_prop.get("description", "").lower()
        assert "lodo" in desc or "cross" in desc or "permutation" in desc, \
            "Schema description for validation_type is missing expected types."