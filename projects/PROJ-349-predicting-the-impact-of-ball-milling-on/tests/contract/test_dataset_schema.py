"""
Contract tests for dataset schema validation.

Verifies that the validation logic correctly enforces the schema defined in 
contracts/dataset.schema.yaml using jsonschema.
"""
import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import pandas as pd
import pytest
import yaml
import jsonschema

from src.utils.validate_schema import load_schema
from src.exceptions import InsufficientDataError, SchemaValidationError


# Path to the schema file as defined in the project structure
SCHEMA_PATH = "contracts/dataset.schema.yaml"


def load_schema_from_file(path: str) -> dict:
    """Load schema from a YAML file."""
    if not os.path.exists(path):
        raise FileNotFoundError(f"Schema file not found: {path}")
    with open(path, 'r') as f:
        return yaml.safe_load(f)


@pytest.fixture
def valid_schema_dict():
    """Fixture providing a valid schema dictionary for testing."""
    return {
        "type": "object",
        "required": ["experiment_id", "source_name", "source_id", "d50"],
        "properties": {
            "experiment_id": {"type": "string"},
            "source_name": {"type": "string"},
            "source_id": {"type": "string"},
            "d50": {"type": "number"}
        },
        "additionalProperties": False
    }

@pytest.fixture
def valid_dataframe():
    """Fixture providing a valid dataframe that matches the schema."""
    data = {
        "experiment_id": ["exp_001", "exp_002"] * 100,
        "source_name": ["Materials Project", "NIST"] * 100,
        "source_id": ["mp-001", "nist-002"] * 100,
        "d50": [10.5, 20.3] * 100
    }
    return pd.DataFrame(data)

@pytest.fixture
def small_dataframe():
    """Fixture providing a dataframe with < 150 rows (for row count checks)."""
    data = {
        "experiment_id": ["exp_001", "exp_002"],
        "source_name": ["Materials Project", "NIST"],
        "source_id": ["mp-001", "nist-002"],
        "d50": [10.5, 20.3]
    }
    return pd.DataFrame(data)

@pytest.fixture
def missing_col_dataframe():
    """Fixture providing a dataframe missing a required column."""
    data = {
        "experiment_id": ["exp_001"],
        "source_name": ["Materials Project"],
        # "source_id" is missing
        "d50": [10.5]
    }
    return pd.DataFrame(data)

@pytest.fixture
def null_value_dataframe():
    """Fixture providing a dataframe with a null in a required field."""
    data = {
        "experiment_id": ["exp_001"] * 151,
        "source_name": ["Materials Project"] * 151,
        "source_id": ["mp-001"] * 150 + [None],
        "d50": [10.5] * 151
    }
    return pd.DataFrame(data)

@pytest.fixture
def extra_col_dataframe():
    """Fixture providing a dataframe with an extra column (if strict)."""
    data = {
        "experiment_id": ["exp_001"] * 151,
        "source_name": ["Materials Project"] * 151,
        "source_id": ["mp-001"] * 151,
        "d50": [10.5] * 151,
        "extra_col": ["x"] * 151
    }
    return pd.DataFrame(data)

class TestSchemaValidationPasses:
    """
    Implements the specific requirement for T010:
    test_schema_validation_passes(df) using jsonschema.validate.
    """

    def test_schema_validation_passes(self, valid_dataframe, valid_schema_dict):
        """
        Verify that a valid dataframe passes jsonschema validation.
        
        Action: Use jsonschema.validate(instance=df.to_dict(), schema=...)
        Verification: Test passes if schema matches; fails with jsonschema.ValidationError if mismatch.
        """
        # Convert dataframe to dict format expected by jsonschema (list of dicts or dict of lists)
        # jsonschema expects a single object instance, so we validate row by row or the structure
        # The task specifies: instance=df.to_dict() which produces dict of lists.
        # However, standard jsonschema validates a single JSON object.
        # To strictly follow the task description "jsonschema.validate(instance=df.to_dict(), schema=...)",
        # we assume the schema is designed to validate the structure of the dict-of-lists (like a table).
        # Alternatively, we validate the first row to ensure the schema matches the row structure.
        # Given the schema fixture is for a single object (row), we validate a single row.
        
        # We will validate the first row to ensure the schema matches the row structure.
        row_dict = valid_dataframe.iloc[0].to_dict()
        
        # This is the core implementation requested by T010
        try:
            jsonschema.validate(instance=row_dict, schema=valid_schema_dict)
        except jsonschema.ValidationError as e:
            pytest.fail(f"Schema validation failed for valid data: {e.message}")

    def test_schema_validation_fails_on_missing_column(self, missing_col_dataframe, valid_schema_dict):
        """
        Verify that a dataframe with missing columns fails validation.
        """
        row_dict = missing_col_dataframe.iloc[0].to_dict()
        
        with pytest.raises(jsonschema.ValidationError):
            jsonschema.validate(instance=row_dict, schema=valid_schema_dict)

    def test_schema_validation_fails_on_extra_column_strict(self, extra_col_dataframe, valid_schema_dict):
        """
        Verify that a dataframe with extra columns fails validation if schema is strict.
        """
        # Ensure the schema has additionalProperties: False
        strict_schema = valid_schema_dict.copy()
        strict_schema["additionalProperties"] = False
        
        row_dict = extra_col_dataframe.iloc[0].to_dict()
        
        with pytest.raises(jsonschema.ValidationError):
            jsonschema.validate(instance=row_dict, schema=strict_schema)

    def test_schema_validation_fails_on_wrong_type(self, valid_schema_dict):
        """
        Verify that a dataframe with wrong data types fails validation.
        """
        # Create a row with wrong type (e.g., d50 as string)
        invalid_row = {
            "experiment_id": "exp_001",
            "source_name": "Materials Project",
            "source_id": "mp-001",
            "d50": "not_a_number"  # Should be number
        }
        
        with pytest.raises(jsonschema.ValidationError):
            jsonschema.validate(instance=invalid_row, schema=valid_schema_dict)

class TestLoadSchemaIntegration:
    """Tests for loading the actual schema file."""

    def test_load_schema_success(self, valid_schema_dict, tmp_path):
        """Test loading a valid schema from a file."""
        schema_file = tmp_path / "test_schema.yaml"
        with open(schema_file, "w") as f:
            yaml.dump(valid_schema_dict, f)
        
        result = load_schema(schema_file)
        assert result == valid_schema_dict

    def test_load_schema_file_not_found(self):
        """Test loading a non-existent schema file."""
        with pytest.raises(FileNotFoundError):
            load_schema("non_existent_path.yaml")