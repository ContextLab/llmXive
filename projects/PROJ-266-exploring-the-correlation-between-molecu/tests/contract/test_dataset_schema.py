"""
Contract tests for dataset.schema.yaml and analysis_output.schema.yaml.
Validates that generated data files conform to the defined JSON schemas.
"""
import json
import os
from pathlib import Path

import pytest
import yaml
from jsonschema import validate, ValidationError, Draft7Validator

# Import config to find project root if needed, though we assume relative paths from test run
from utils.config import get_project_root

PROJECT_ROOT = get_project_root()
CONTRACTS_DIR = PROJECT_ROOT / "specs" / "001-molecular-flexibility-permeability" / "contracts"
DATA_DIR = PROJECT_ROOT / "data" / "processed"

# Load schemas
def load_schema(schema_name: str) -> dict:
    schema_path = CONTRACTS_DIR / schema_name
    if not schema_path.exists():
        raise FileNotFoundError(f"Schema not found: {schema_path}")
    with open(schema_path, "r") as f:
        return yaml.safe_load(f)

DATASET_SCHEMA = load_schema("dataset.schema.yaml")
ANALYSIS_SCHEMA = load_schema("analysis_output.schema.yaml")

def validate_json_against_schema(data: dict, schema: dict, file_path: str) -> None:
    """Validates data against schema and raises a descriptive error if invalid."""
    validator = Draft7Validator(schema)
    errors = list(validator.iter_errors(data))
    if errors:
        error_messages = [
            f"Path: {' -> '.join(map(str, e.path))}: {e.message}"
            for e in errors
        ]
        raise AssertionError(
            f"Validation failed for {file_path}:\n" + "\n".join(error_messages)
        )

@pytest.mark.contract
def test_dataset_schema_structure():
    """
    Test that if a dataset CSV/JSON exists, it validates against dataset.schema.yaml.
    Skips if no data file is present (e.g., if T009/T010 haven't run yet).
    """
    # Expected output file from T010 (preprocessing)
    dataset_file = DATA_DIR / "caco2_preprocessed.json"
    
    if not dataset_file.exists():
        # If the file doesn't exist yet, this test is skipped rather than failed
        # This allows the test suite to run even if data retrieval hasn't completed.
        pytest.skip(f"Dataset file not found at {dataset_file}. Skipping contract test.")

    with open(dataset_file, "r") as f:
        data = json.load(f)

    validate_json_against_schema(data, DATASET_SCHEMA, str(dataset_file))

@pytest.mark.contract
def test_analysis_output_schema_structure():
    """
    Test that if an analysis output JSON exists, it validates against analysis_output.schema.yaml.
    Skips if no analysis file is present.
    """
    # Expected output file from T014c/T015 (descriptors/analysis)
    analysis_file = DATA_DIR / "analysis_results.json"

    if not analysis_file.exists():
        pytest.skip(f"Analysis output file not found at {analysis_file}. Skipping contract test.")

    with open(analysis_file, "r") as f:
        data = json.load(f)

    validate_json_against_schema(data, ANALYSIS_SCHEMA, str(analysis_file))

@pytest.mark.contract
def test_schema_files_are_valid_yaml():
    """
    Ensures the schema files themselves are valid YAML and parseable.
    """
    # If we got here, load_schema didn't fail, so they are valid.
    # This is a sanity check for the schema definitions themselves.
    assert isinstance(DATASET_SCHEMA, dict)
    assert isinstance(ANALYSIS_SCHEMA, dict)
    assert "$schema" in DATASET_SCHEMA
    assert "$schema" in ANALYSIS_SCHEMA
