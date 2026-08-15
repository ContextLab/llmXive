"""
Contract test for dataset schema validation.
Validates that the dataset conforms to the schema defined in contracts/dataset.schema.yaml.
"""
import os
import sys
import json
import pytest
from pathlib import Path

import pandas as pd
from jsonschema import validate, ValidationError

# Add project root to path for imports if running directly
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.preprocess.validate_schema import load_schema
from src.utils.exceptions import InsufficientDataError


def test_schema_validation_passes(df):
    """
    Test that a valid dataframe passes schema validation.

    Args:
        df (pd.DataFrame): A dataframe that should conform to the schema.
    """
    schema_path = project_root / "contracts" / "dataset.schema.yaml"
    if not schema_path.exists():
        pytest.fail(f"Schema file not found at {schema_path}")

    schema = load_schema(schema_path)

    # Convert dataframe to dict for jsonschema validation
    # jsonschema expects a dict of lists or a single object dict.
    # Since our schema defines an 'object' with properties, we validate a single row.
    # To test the structure, we validate the first row.
    if len(df) == 0:
        pytest.skip("DataFrame is empty, cannot validate structure.")

    # Convert to dict of lists format if needed, but jsonschema.validate
    # expects the instance to match the schema type.
    # The schema is type: object. So we validate a single row dict.
    row_dict = df.iloc[0].to_dict()

    try:
        validate(instance=row_dict, schema=schema)
    except ValidationError as e:
        pytest.fail(f"Schema validation failed for row: {e.message}")


def test_schema_validation_fails_missing_field():
    """
    Test that a dataframe with a missing required field fails validation.
    """
    schema_path = project_root / "contracts" / "dataset.schema.yaml"
    schema = load_schema(schema_path)

    # Create a dataframe missing 'experiment_id'
    data = {
        "source_name": ["Materials Project"],
        "source_id": ["12345"],
        # missing experiment_id
        "material_type": ["Copper"],
        "milling_speed": [500.0],
        "milling_time": [1.0],
        "ball_to_powder_ratio": [10.0],
        "youngs_modulus": [110.0],
        "density": [8.96],
        "d10": [10.0],
        "d50": [50.0],
        "d90": [100.0],
        "process_duration": [3600.0]
    }
    df = pd.DataFrame(data)
    row_dict = df.iloc[0].to_dict()

    with pytest.raises(ValidationError):
        validate(instance=row_dict, schema=schema)


def test_schema_validation_fails_wrong_type():
    """
    Test that a dataframe with a wrong type for a field fails validation.
    """
    schema_path = project_root / "contracts" / "dataset.schema.yaml"
    schema = load_schema(schema_path)

    # Create a dataframe with wrong type for milling_speed (string instead of number)
    data = {
        "experiment_id": ["exp_001"],
        "source_name": ["Materials Project"],
        "source_id": ["12345"],
        "material_type": ["Copper"],
        "milling_speed": "fast",  # Should be number
        "milling_time": [1.0],
        "ball_to_powder_ratio": [10.0],
        "youngs_modulus": [110.0],
        "density": [8.96],
        "d10": [10.0],
        "d50": [50.0],
        "d90": [100.0],
        "process_duration": [3600.0]
    }
    df = pd.DataFrame(data)
    row_dict = df.iloc[0].to_dict()

    with pytest.raises(ValidationError):
        validate(instance=row_dict, schema=schema)


def test_schema_validation_fails_enum():
    """
    Test that a dataframe with an invalid source_name fails validation.
    """
    schema_path = project_root / "contracts" / "dataset.schema.yaml"
    schema = load_schema(schema_path)

    # Create a dataframe with invalid source_name
    data = {
        "experiment_id": ["exp_001"],
        "source_name": ["Invalid Source"],  # Not in enum
        "source_id": ["12345"],
        "material_type": ["Copper"],
        "milling_speed": [500.0],
        "milling_time": [1.0],
        "ball_to_powder_ratio": [10.0],
        "youngs_modulus": [110.0],
        "density": [8.96],
        "d10": [10.0],
        "d50": [50.0],
        "d90": [100.0],
        "process_duration": [3600.0]
    }
    df = pd.DataFrame(data)
    row_dict = df.iloc[0].to_dict()

    with pytest.raises(ValidationError):
        validate(instance=row_dict, schema=schema)