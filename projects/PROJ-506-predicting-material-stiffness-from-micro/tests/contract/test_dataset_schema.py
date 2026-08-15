"""
Contract test for dataset schema (T016).

Validates that the generated dataset conforms to the schema defined in
specs/001-predict-stiffness-cnn/contracts/dataset.schema.yaml.

This test:
1. Loads the schema definition.
2. Loads a sample metadata file from data/processed/ (or generates one if
   the pipeline has been run).
3. Validates each record against the schema requirements:
   - image_path: string (exists and is .png)
   - stiffness_tensor: float[] (length 6 for Voigt notation)
   - inclusion_density: float (0.0 <= value <= 1.0)
   - seed: integer (non-negative)
"""

import os
import json
import yaml
from pathlib import Path
import pytest

# Project root relative to this test file
PROJECT_ROOT = Path(__file__).parent.parent.parent
SCHEMA_PATH = PROJECT_ROOT / "specs" / "001-predict-stiffness-cnn" / "contracts" / "dataset.schema.yaml"
METADATA_PATH = PROJECT_ROOT / "data" / "processed" / "dataset_metadata.json"

def load_schema():
    """Load the YAML schema definition."""
    if not SCHEMA_PATH.exists():
        raise FileNotFoundError(f"Schema file not found at {SCHEMA_PATH}")
    with open(SCHEMA_PATH, "r") as f:
        return yaml.safe_load(f)

def load_metadata():
    """Load the generated dataset metadata."""
    if not METADATA_PATH.exists():
        pytest.skip(
            f"Metadata file not found at {METADATA_PATH}. "
            "Run the data generation pipeline (T017-T020) first."
        )
    with open(METADATA_PATH, "r") as f:
        return json.load(f)

def validate_record(record, schema_fields):
    """Validate a single record against the schema requirements."""
    errors = []

    # Check image_path
    if "image_path" not in record:
        errors.append("Missing 'image_path' field")
    elif not isinstance(record["image_path"], str):
        errors.append("'image_path' must be a string")
    elif not Path(record["image_path"]).suffix.lower() == ".png":
        errors.append("'image_path' must point to a .png file")
    elif not Path(record["image_path"]).exists():
        # Only check existence if the path is absolute or relative to root
        # If it's just a filename, we assume it's in data/raw/
        expected_path = PROJECT_ROOT / "data" / "raw" / Path(record["image_path"]).name
        if not expected_path.exists():
            errors.append(f"Image file not found: {record['image_path']}")

    # Check stiffness_tensor
    if "stiffness_tensor" not in record:
        errors.append("Missing 'stiffness_tensor' field")
    elif not isinstance(record["stiffness_tensor"], list):
        errors.append("'stiffness_tensor' must be a list of floats")
    elif len(record["stiffness_tensor"]) != 6:
        errors.append(f"'stiffness_tensor' must have length 6 (Voigt notation), got {len(record['stiffness_tensor'])}")
    else:
        try:
            vals = [float(x) for x in record["stiffness_tensor"]]
            # Basic physical plausibility check: stiffness should be positive
            if any(v <= 0 for v in vals):
                errors.append("'stiffness_tensor' contains non-positive values")
        except (ValueError, TypeError):
            errors.append("'stiffness_tensor' contains non-numeric values")

    # Check inclusion_density
    if "inclusion_density" not in record:
        errors.append("Missing 'inclusion_density' field")
    elif not isinstance(record["inclusion_density"], (int, float)):
        errors.append("'inclusion_density' must be a number")
    else:
        if not (0.0 <= record["inclusion_density"] <= 1.0):
            errors.append(f"'inclusion_density' must be between 0.0 and 1.0, got {record['inclusion_density']}")

    # Check seed
    if "seed" not in record:
        errors.append("Missing 'seed' field")
    elif not isinstance(record["seed"], int):
        errors.append("'seed' must be an integer")
    elif record["seed"] < 0:
        errors.append("'seed' must be non-negative")

    return errors

def test_schema_exists():
    """Verify the schema file exists."""
    assert SCHEMA_PATH.exists(), f"Schema file missing: {SCHEMA_PATH}"

def test_schema_structure():
    """Verify the schema file has the expected structure."""
    schema = load_schema()
    assert "fields" in schema, "Schema must define 'fields'"
    expected_fields = ["image_path", "stiffness_tensor", "inclusion_density", "seed"]
    schema_field_names = [f["name"] for f in schema["fields"]]
    for field in expected_fields:
        assert field in schema_field_names, f"Schema missing required field: {field}"

def test_dataset_conforms_to_schema():
    """
    Main contract test: Verify all records in the dataset metadata
    conform to the schema defined in dataset.schema.yaml.
    """
    schema = load_schema()
    metadata = load_metadata()

    # The metadata file should be a list of records
    if not isinstance(metadata, list):
        pytest.fail("Dataset metadata must be a list of records")

    if len(metadata) == 0:
        pytest.skip("Dataset metadata is empty")

    all_errors = []
    for i, record in enumerate(metadata):
        errors = validate_record(record, schema["fields"])
        if errors:
            all_errors.append(f"Record {i}: {errors}")

    if all_errors:
        pytest.fail(f"Schema validation failed for {len(all_errors)} records:\n" + "\n".join(all_errors))