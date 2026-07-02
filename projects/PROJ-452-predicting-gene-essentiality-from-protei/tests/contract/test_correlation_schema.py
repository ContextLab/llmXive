"""
Contract test for correlation result schema (US1).

This test validates that the output produced by the correlation analysis pipeline
conforms to the schema defined in contracts/correlation_result.schema.yaml.

It verifies:
1. The JSON file exists at the expected path.
2. The JSON is valid and parseable.
3. The structure matches the schema (required fields, types, nested objects).
4. Specific scientific fields (rho, p_value) are numeric.
"""

import json
import os
import pytest
import yaml
from pathlib import Path
from typing import Any, Dict

# Import schema validation helper from existing test infrastructure
# T008 created tests/contract/test_schemas.py which likely contains a validator
# We assume a helper function exists or we implement a simple one here if not provided
# Since T008 is completed, we rely on the schema file existing.

PROJECT_ROOT = Path(__file__).parent.parent.parent
SCHEMA_PATH = PROJECT_ROOT / "contracts" / "correlation_result.schema.yaml"
OUTPUT_PATH = PROJECT_ROOT / "results" / "correlations.json"

def load_schema() -> Dict[str, Any]:
    """Load the JSON Schema from the contracts directory."""
    if not SCHEMA_PATH.exists():
        pytest.fail(f"Schema file not found at {SCHEMA_PATH}. Ensure T007 is complete.")
    with open(SCHEMA_PATH, "r") as f:
        return yaml.safe_load(f)

def validate_json_against_schema(data: Dict[str, Any], schema: Dict[str, Any]) -> None:
    """
    Simple validation logic to check required fields and types.
    Since 'jsonschema' might not be in the minimal env, we do a structural check
    that aligns with the schema definition for this specific contract test.
    
    If 'jsonschema' is available, it should be used. We attempt import first.
    """
    try:
        import jsonschema
        jsonschema.validate(instance=data, schema=schema)
        return
    except ImportError:
        # Fallback manual validation if jsonschema is not installed
        # This ensures the test runs even in minimal environments, though jsonschema is standard for this task.
        pass

    # Manual structural checks based on expected schema structure for US1
    # Expected keys: organisms (dict), metadata (dict)
    if "organisms" not in data:
        raise AssertionError("Missing required field: 'organisms'")
    
    if not isinstance(data["organisms"], dict):
        raise AssertionError("'organisms' must be a dictionary")
    
    # Check at least one organism exists
    if len(data["organisms"]) == 0:
        raise AssertionError("No organisms found in results")

    # Check structure of a single organism entry
    # Expected: { organism_id: { "degree": { "rho": float, "p_value": float }, ... }, ... }
    for org_id, org_data in data["organisms"].items():
        if not isinstance(org_data, dict):
            raise AssertionError(f"Data for organism '{org_id}' must be a dictionary")
        
        # We expect at least one centrality metric (e.g., 'degree') to be present
        # as per the task description: "verify ... contains a valid Spearman ρ and p-value for degree centrality"
        found_metric = False
        for metric_name, metrics in org_data.items():
            if isinstance(metrics, dict):
                if "rho" in metrics and "p_value" in metrics:
                    if not isinstance(metrics["rho"], (int, float)):
                        raise AssertionError(f"'rho' for {org_id}/{metric_name} must be numeric")
                    if not isinstance(metrics["p_value"], (int, float)):
                        raise AssertionError(f"'p_value' for {org_id}/{metric_name} must be numeric")
                    found_metric = True
        
        if not found_metric:
            raise AssertionError(f"No valid centrality metrics (with rho/p_value) found for organism '{org_id}'")

@pytest.mark.contract
def test_correlation_schema_conformance():
    """
    Test that the correlation results file conforms to the defined schema.
    
    This test will FAIL if:
    - The results file does not exist (pipeline not run).
    - The file is not valid JSON.
    - The structure does not match the schema (missing fields, wrong types).
    """
    # 1. Check if output file exists
    if not OUTPUT_PATH.exists():
        pytest.fail(f"Output file not found at {OUTPUT_PATH}. "
                    "Run the pipeline (T017) to generate results before running this test.")

    # 2. Load and parse JSON
    try:
        with open(OUTPUT_PATH, "r") as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        pytest.fail(f"Invalid JSON in {OUTPUT_PATH}: {e}")

    # 3. Load schema
    schema = load_schema()

    # 4. Validate
    try:
        validate_json_against_schema(data, schema)
    except AssertionError as e:
        pytest.fail(f"Schema validation failed: {e}")
    except Exception as e:
        # Catch any unexpected errors during validation (e.g. jsonschema errors)
        pytest.fail(f"Validation error: {e}")

@pytest.mark.contract
def test_correlation_result_numeric_fields():
    """
    Specific check that rho and p_value are numeric and within expected ranges.
    Spearman's rho is in [-1, 1], p_value in [0, 1].
    """
    if not OUTPUT_PATH.exists():
        pytest.skip("Output file not found, skipping numeric check.")

    with open(OUTPUT_PATH, "r") as f:
        data = json.load(f)

    for org_id, org_data in data.get("organisms", {}).items():
        for metric_name, metrics in org_data.items():
            if isinstance(metrics, dict):
                rho = metrics.get("rho")
                p_val = metrics.get("p_value")
                
                if rho is not None:
                    assert isinstance(rho, (int, float)), f"rho must be numeric for {org_id}/{metric_name}"
                    assert -1.0 <= rho <= 1.0, f"rho must be between -1 and 1 for {org_id}/{metric_name}"
                
                if p_val is not None:
                    assert isinstance(p_val, (int, float)), f"p_value must be numeric for {org_id}/{metric_name}"
                    assert 0.0 <= p_val <= 1.0, f"p_value must be between 0 and 1 for {org_id}/{metric_name}"