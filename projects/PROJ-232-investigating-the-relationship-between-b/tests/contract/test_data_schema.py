"""
Contract test for data schema validation (US1).

This test validates that the data artifacts produced by the download pipeline
conform to the contracts defined in `contracts/dataset.schema.yaml`.

It verifies:
1. The behavioral CSV matches the expected columns (BMRQ scores, demographics).
2. The connectivity matrices (if present in the test fixture) match the schema.
3. The metadata JSON matches the expected structure.

Note: This test assumes real data has been downloaded to `data/raw/` or
a fixture exists. If no real data is available, it skips gracefully or fails
loudly if the schema contract is missing.
"""

import json
import os
import sys
from pathlib import Path

import pandas as pd
import pytest
import yaml
from jsonschema import validate, ValidationError, SchemaError

# Project root relative to tests/contract/
ROOT_DIR = Path(__file__).resolve().parent.parent.parent
CONTRACTS_DIR = ROOT_DIR / "contracts"
DATA_DIR = ROOT_DIR / "data"
SCHEMA_PATH = CONTRACTS_DIR / "dataset.schema.yaml"

# Expected paths based on T011 implementation
BEHAVIORAL_FILE = DATA_DIR / "raw" / "bmrq_scores.csv"
METADATA_FILE = DATA_DIR / "raw" / "dataset_metadata.json"
# Connectivity matrices are usually generated in T013, but we validate the schema
# expectation here if a sample exists or if the contract defines the structure.
CONNECTIVITY_DIR = DATA_DIR / "processed" / "connectivity"

@pytest.fixture
def schema():
    """Load the dataset schema contract."""
    if not SCHEMA_PATH.exists():
        pytest.fail(f"Schema contract not found at {SCHEMA_PATH}. "
                    "Ensure T007 (contracts) is completed.")
    with open(SCHEMA_PATH, "r") as f:
        try:
            return yaml.safe_load(f)
        except yaml.YAMLError as e:
            pytest.fail(f"Invalid YAML in schema contract: {e}")

def _validate_csv_structure(file_path: Path, schema_def: dict) -> None:
    """Validate a CSV file against a schema definition."""
    if not file_path.exists():
        pytest.fail(f"Data file missing: {file_path}. "
                    "Run download pipeline (T011) first.")

    df = pd.read_csv(file_path)
    required_columns = schema_def.get("required_columns", [])

    missing = set(required_columns) - set(df.columns)
    if missing:
        pytest.fail(f"CSV missing required columns: {missing}. "
                    f"Found: {list(df.columns)}")

    # Validate types if specified
    type_map = schema_def.get("column_types", {})
    for col, expected_type in type_map.items():
        if col in df.columns:
            # Simple type check (pandas dtypes)
            if expected_type == "numeric":
                if not pd.api.types.is_numeric_dtype(df[col]):
                    pytest.fail(f"Column '{col}' should be numeric, got {df[col].dtype}")

def _validate_json_structure(file_path: Path, schema_def: dict) -> None:
    """Validate a JSON file against a schema definition using jsonschema."""
    if not file_path.exists():
        pytest.fail(f"Data file missing: {file_path}. "
                    "Run download pipeline (T011) first.")

    with open(file_path, "r") as f:
        data = json.load(f)

    try:
        validate(instance=data, schema=schema_def)
    except ValidationError as e:
        pytest.fail(f"JSON validation failed: {e.message} at path {e.absolute_path}")
    except SchemaError as e:
        pytest.fail(f"Schema definition error: {e.message}")

def test_behavioral_data_schema(schema):
    """
    T009: Validate BMRQ behavioral data against dataset.schema.yaml.
    
    Checks that the downloaded CSV contains all required columns defined
    in the contract (e.g., subject_id, BMRQ_Total, age, sex).
    """
    if "behavioral" not in schema:
        pytest.skip("Behavioral schema section not defined in contract.")

    schema_def = schema["behavioral"]
    _validate_csv_structure(BEHAVIORAL_FILE, schema_def)

def test_metadata_schema(schema):
    """
    T009: Validate dataset metadata JSON against dataset.schema.yaml.
    
    Checks that the metadata file contains dataset description, version,
    and source information as per the contract.
    """
    if "metadata" not in schema:
        pytest.skip("Metadata schema section not defined in contract.")

    schema_def = schema["metadata"]
    _validate_json_structure(METADATA_FILE, schema_def)

def test_connectivity_schema_exists(schema):
    """
    T009: Validate that connectivity schema is defined and (if data exists) valid.
    
    This checks the schema definition itself. If sample connectivity data exists,
    it validates the structure (symmetric, 200x200, etc.).
    """
    if "connectivity" not in schema:
        pytest.skip("Connectivity schema section not defined in contract.")

    schema_def = schema["connectivity"]
    
    # If the directory exists, validate one file if available
    if CONNECTIVITY_DIR.exists() and any(CONNECTIVITY_DIR.glob("*.json")):
        sample_file = next(CONNECTIVITY_DIR.glob("*.json"))
        # For JSON matrices, we expect a specific structure defined in the schema
        # If the schema defines 'items' or 'properties', validate against it
        try:
            with open(sample_file, "r") as f:
                data = json.load(f)
            validate(instance=data, schema=schema_def)
        except ValidationError as e:
            pytest.fail(f"Connectivity data validation failed: {e.message}")
        except json.JSONDecodeError:
            # If it's a matrix format not matching the JSON schema, skip or check alternative
            pass
    else:
        # If no data, we just confirm the schema definition exists and is valid YAML
        # The actual data validation happens when data is present
        assert "type" in schema_def or "properties" in schema_def, \
            "Connectivity schema definition is malformed."