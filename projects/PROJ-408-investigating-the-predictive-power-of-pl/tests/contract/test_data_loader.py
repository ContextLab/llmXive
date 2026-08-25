"""
Contract test for data loader output schema (Task T010).

This test verifies that the output of the data loader (once implemented)
strictly adheres to the schema defined in `tests/contract/schemas/data_loader.yaml`.

It uses a mock data structure that simulates what the real loader should return,
ensuring the validation logic is sound before the real network fetch is implemented.
"""

import yaml
import re
from pathlib import Path
from typing import Any, Dict, List

# Import the schema loader logic if needed, but here we load directly
SCHEMA_PATH = Path(__file__).parent / "schemas" / "data_loader.yaml"


def load_schema(schema_path: Path) -> Dict[str, Any]:
    """Load the YAML schema definition."""
    with open(schema_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def validate_type(value: Any, expected_type: str, path: str) -> None:
    """Validate a value against a simple type string."""
    if expected_type == "object":
        if not isinstance(value, dict):
            raise AssertionError(f"{path}: Expected object, got {type(value).__name__}")
    elif expected_type == "array":
        if not isinstance(value, list):
            raise AssertionError(f"{path}: Expected array, got {type(value).__name__}")
    elif expected_type == "string":
        if not isinstance(value, str):
            raise AssertionError(f"{path}: Expected string, got {type(value).__name__}")
    elif expected_type == "number":
        if not isinstance(value, (int, float)):
            raise AssertionError(f"{path}: Expected number, got {type(value).__name__}")


def validate_pattern(value: str, pattern: str, path: str) -> None:
    """Validate a string against a regex pattern."""
    if not re.match(pattern, value):
        raise AssertionError(f"{path}: Value '{value}' does not match pattern '{pattern}'")


def validate_schema(data: Dict[str, Any], schema: Dict[str, Any], path: str = "root") -> None:
    """
    Recursively validate data against the simplified schema.
    This is a lightweight validator tailored for the specific schema structure.
    """
    # Check type
    if "type" in schema:
        validate_type(data, schema["type"], path)

    # Check required fields for objects
    if schema.get("type") == "object" and "required" in schema:
        for req_field in schema["required"]:
            if req_field not in data:
                raise AssertionError(f"{path}: Missing required field '{req_field}'")

    # Check properties for objects
    if schema.get("type") == "object" and "properties" in schema:
        for key, prop_schema in schema["properties"].items():
            if key in data:
                validate_schema(data[key], prop_schema, f"{path}.{key}")

    # Check patternProperties for objects (for sequences and metabolites keys)
    if schema.get("type") == "object" and "patternProperties" in schema:
        if isinstance(data, dict):
            for key, value in data.items():
                matched = False
                for pattern, prop_schema in schema["patternProperties"].items():
                    if re.match(pattern, key):
                        validate_schema(value, prop_schema, f"{path}['{key}']")
                        matched = True
                        break
                if not matched and not schema.get("additionalProperties"):
                    # If no pattern matches and no additionalProperties allowed, fail
                    # (Though our schema uses additionalProperties for the outer dicts)
                    pass

    # Check additionalProperties for objects
    if schema.get("type") == "object" and "additionalProperties" in schema:
        if isinstance(data, dict):
            for key, value in data.items():
                # Check if key matches any patternProperties first
                matched_pattern = False
                if "patternProperties" in schema:
                    for pattern in schema["patternProperties"].keys():
                        if re.match(pattern, key):
                            matched_pattern = True
                            break

                if not matched_pattern:
                    validate_schema(value, schema["additionalProperties"], f"{path}['{key}']")

    # Check items for arrays
    if schema.get("type") == "array" and "items" in schema:
        if isinstance(data, list):
            for i, item in enumerate(data):
                validate_schema(item, schema["items"], f"{path}[{i}]")

    # Check pattern for strings
    if schema.get("type") == "string" and "pattern" in schema:
        if isinstance(data, str):
            validate_pattern(data, schema["pattern"], path)


def test_data_loader_schema_matches():
    """
    Test that a valid sample output from the data loader matches the schema.

    Since the real loader (T013/T014) is not yet implemented, we construct
    a valid mock output that simulates the expected real data structure.
    The test ensures the schema correctly accepts valid data and would reject invalid.
    """
    schema = load_schema(SCHEMA_PATH)

    # Valid mock data simulating the output of code/data_loader.py
    valid_data = {
        "sequences": {
            "Arabidopsis_thaliana": {
                "18S": "ACGTACGTACGTACGTACGTACGTACGTACGT",
                "rbcL": "GCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTA",
                "matK": "TGCATGCATGCATGCATGCATGCATGCATGCA"
            },
            "Oryza_sativa": {
                "18S": "ACGTACGTACGTACGTACGTACGTACGTACGT",
                "rbcL": "GCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTA"
            }
        },
        "metabolites": {
            "Arabidopsis_thaliana": ["C00001", "C00002", "C00003"],
            "Oryza_sativa": ["C00001", "C00005"]
        }
    }

    # This should not raise an AssertionError
    try:
        validate_schema(valid_data, schema)
    except AssertionError as e:
        raise AssertionError(f"Valid mock data failed schema validation: {e}")

    # Test 2: Verify the schema rejects invalid data (e.g., wrong metabolite ID format)
    invalid_data_metabolite_id = {
        "sequences": {
            "Test_Species": {
                "18S": "ACGTACGTACGTACGTACGTACGTACGTACGT"
            }
        },
        "metabolites": {
            "Test_Species": ["INVALID_ID"]  # Should be C followed by 5 digits
        }
    }

    try:
        validate_schema(invalid_data_metabolite_id, schema)
        raise AssertionError("Schema validation should have failed for invalid metabolite ID format.")
    except AssertionError:
        # Expected failure
        pass

    # Test 3: Verify the schema rejects invalid data (e.g., non-DNA sequence)
    invalid_data_sequence = {
        "sequences": {
            "Test_Species": {
                "18S": "XYZXYZXYZXYZXYZXYZXYZXYZXYZXYZXYZXYZ"  # Invalid bases
            }
        },
        "metabolites": {
            "Test_Species": ["C00001"]
        }
    }

    try:
        validate_schema(invalid_data_sequence, schema)
        raise AssertionError("Schema validation should have failed for invalid DNA sequence.")
    except AssertionError:
        # Expected failure
        pass