"""
Contract test for TestResult schema.
Validates JSON data against contracts/TestResult.schema.yaml.
"""
import json
import os
import sys
from pathlib import Path
from datetime import datetime
import jsonschema
from jsonschema import validate, ValidationError

# Add project root to path to resolve relative imports if running as script
project_root = Path(__file__).parent.parent.parent
schema_path = project_root / "contracts" / "TestResult.schema.yaml"

import yaml

def load_schema(schema_file_path: Path) -> dict:
    """Load and parse the YAML schema file."""
    with open(schema_file_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def test_test_result_schema():
    """
    Validates a representative TestResult JSON object against the schema.
    This ensures the data structure produced by US2 (T025) matches the contract.
    """
    if not schema_path.exists():
        raise FileNotFoundError(f"Schema file not found at {schema_path}")

    schema = load_schema(schema_path)

    # Construct a valid example TestResult object
    valid_test_result = {
        "ks_statistic": 0.012345,
        "p_value": 0.85,
        "n_samples": 10000,
        "n_cutoff": 1000000,
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "control_comparison": {
            "control_ks_statistic": 0.011000,
            "ks_difference": 0.001345,
            "threshold_passed": True
        },
        "notes": "Test passed SC-006 verification."
    }

    try:
        validate(instance=valid_test_result, schema=schema)
    except ValidationError as e:
        raise AssertionError(f"Valid test result failed schema validation: {e.message}")

    # Test with invalid data to ensure the schema actually rejects bad input
    invalid_test_result = valid_test_result.copy()
    invalid_test_result["ks_statistic"] = "not a number"  # Type error

    try:
        validate(instance=invalid_test_result, schema=schema)
        raise AssertionError("Invalid test result should have failed schema validation")
    except ValidationError:
        # Expected behavior
        pass

    # Test missing required field
    missing_field_result = {k: v for k, v in valid_test_result.items() if k != "p_value"}
    try:
        validate(instance=missing_field_result, schema=schema)
        raise AssertionError("Missing required field should have failed schema validation")
    except ValidationError:
        # Expected behavior
        pass

    print("Contract test passed: TestResult schema is valid and enforces structure.")

if __name__ == "__main__":
    test_test_result_schema()
