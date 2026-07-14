"""
Contract tests to ensure that required schema files exist and are valid JSON.
These tests verify the foundation (T007) before running deeper validation tests.
"""
import json
from pathlib import Path
import pytest

from tests.contract import SCHEMAS_DIR

# List of expected schema files as defined in T007
EXPECTED_SCHEMAS = [
    "simulation_run.json",
    "scaling_result.json",
    "regression_result.json"
]

@pytest.mark.parametrize("schema_file", EXPECTED_SCHEMAS)
def test_schema_file_exists(schema_file: str):
    """Verify that each expected schema file exists on disk."""
    schema_path = SCHEMAS_DIR / schema_file
    assert schema_path.exists(), f"Schema file missing: {schema_path}"

@pytest.mark.parametrize("schema_file", EXPECTED_SCHEMAS)
def test_schema_file_is_valid_json(schema_file: str):
    """Verify that each schema file contains valid JSON."""
    schema_path = SCHEMAS_DIR / schema_file
    try:
        with open(schema_path, 'r', encoding='utf-8') as f:
            json.load(f)
    except json.JSONDecodeError as e:
        pytest.fail(f"Schema file {schema_file} is not valid JSON: {e}")

def test_schemas_directory_is_not_empty():
    """Basic sanity check that the contracts directory has content."""
    assert SCHEMAS_DIR.exists(), "Contracts directory missing."
    files = list(SCHEMAS_DIR.glob("*.json"))
    assert len(files) > 0, "No JSON files found in contracts directory."
