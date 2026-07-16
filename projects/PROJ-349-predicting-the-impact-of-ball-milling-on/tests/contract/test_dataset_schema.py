"""
Contract tests for dataset schema validation.

Verifies that the validation logic correctly enforces the schema defined in 
contracts/dataset.schema.yaml.
"""
import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import pandas as pd
import pytest
import yaml

from src.utils.validate_schema import (
    load_schema, 
    validate_dataframe_schema, 
    validate_and_clean,
    DEFAULT_SCHEMA_PATH
)
from src.exceptions import SchemaValidationError, InsufficientDataError


@pytest.fixture
def valid_schema_dict():
    return {
        "type": "object",
        "required": ["id", "value"],
        "properties": {
            "id": {"type": "string"},
            "value": {"type": "number"}
        },
        "additionalProperties": False
    }

@pytest.fixture
def valid_dataframe():
    data = {
        "id": ["exp_001", "exp_002"] * 100, # Ensure > 150 rows
        "value": [1.0, 2.0] * 100
    }
    return pd.DataFrame(data)

@pytest.fixture
def small_dataframe():
    # Less than 150 rows
    data = {
        "id": ["exp_001", "exp_002"],
        "value": [1.0, 2.0]
    }
    return pd.DataFrame(data)

@pytest.fixture
def missing_col_dataframe():
    data = {
        "id": ["exp_001"],
        # "value" is missing
    }
    return pd.DataFrame(data)

@pytest.fixture
def null_value_dataframe():
    data = {
        "id": ["exp_001"] * 151,
        "value": [1.0] * 150 + [None] # One null in required field
    }
    return pd.DataFrame(data)

@pytest.fixture
def extra_col_dataframe():
    data = {
        "id": ["exp_001"] * 151,
        "value": [1.0] * 151,
        "extra_col": ["x"] * 151
    }
    return pd.DataFrame(data)

class TestLoadSchema:
    def test_load_schema_success(self, tmp_path):
        schema_content = {
            "type": "object",
            "properties": {"test": {"type": "string"}}
        }
        schema_file = tmp_path / "test_schema.yaml"
        with open(schema_file, "w") as f:
            yaml.dump(schema_content, f)
        
        result = load_schema(schema_file)
        assert result == schema_content

    def test_load_schema_file_not_found(self):
        with pytest.raises(FileNotFoundError):
            load_schema("non_existent_path.yaml")

    def test_load_schema_invalid_yaml(self, tmp_path):
        schema_file = tmp_path / "bad.yaml"
        with open(schema_file, "w") as f:
            f.write("invalid: yaml: content: [")
        
        with pytest.raises(Exception): # yaml.YAMLError or similar
            load_schema(schema_file)

class TestValidateDataFrameSchema:
    def test_valid_dataframe(self, valid_dataframe, valid_schema_dict):
        # Temporarily patch the schema to use our fixture
        with patch('src.utils.validate_schema.DEFAULT_SCHEMA_PATH', None):
            # We pass the schema directly to avoid file loading
            result = validate_dataframe_schema(valid_dataframe, schema=valid_schema_dict)
            assert result is True

    def test_insufficient_rows(self, small_dataframe, valid_schema_dict):
        with pytest.raises(InsufficientDataError):
            validate_dataframe_schema(small_dataframe, schema=valid_schema_dict)

    def test_missing_required_columns(self, missing_col_dataframe, valid_schema_dict):
        with pytest.raises(SchemaValidationError):
            validate_dataframe_schema(missing_col_dataframe, schema=valid_schema_dict)

    def test_extra_columns_strict(self, extra_col_dataframe, valid_schema_dict):
        # valid_schema_dict has additionalProperties: False
        with pytest.raises(SchemaValidationError):
            validate_dataframe_schema(extra_col_dataframe, schema=valid_schema_dict)

    def test_null_in_required_field(self, null_value_dataframe, valid_schema_dict):
        with pytest.raises(SchemaValidationError):
            validate_dataframe_schema(null_value_dataframe, schema=valid_schema_dict)

    def test_non_dataframe_input(self, valid_schema_dict):
        with pytest.raises(TypeError):
            validate_dataframe_schema("not a dataframe", schema=valid_schema_dict)

    def test_validation_false_on_error_non_strict(self, missing_col_dataframe, valid_schema_dict):
        result = validate_dataframe_schema(missing_col_dataframe, schema=valid_schema_dict, strict=False)
        assert result is False

class TestValidateAndClean:
    def test_success(self, valid_dataframe, valid_schema_dict):
        with patch('src.utils.validate_schema.DEFAULT_SCHEMA_PATH', None):
            result = validate_and_clean(valid_dataframe, schema_path=valid_schema_dict)
            # Should return the same dataframe
            assert result.equals(valid_dataframe)

    def test_raises_on_error(self, small_dataframe, valid_schema_dict):
        with pytest.raises(InsufficientDataError):
            validate_and_clean(small_dataframe, schema_path=valid_schema_dict)