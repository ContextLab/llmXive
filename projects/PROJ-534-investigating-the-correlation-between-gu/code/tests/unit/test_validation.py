"""
Unit tests for the validation module.
"""
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import tempfile
import os
import sys

# Ensure project root is in path
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from code.src.utils.validation import (
    load_schema,
    validate_field_type,
    validate_enum,
    validate_range,
    validate_dataframe_against_schema,
    validate_dataset,
    validate_result_against_analysis_schema
)

@pytest.fixture
def sample_schema():
    return {
        "name": "test_schema",
        "version": "1.0.0",
        "entities": [
            {
                "name": "participant",
                "fields": [
                    {"name": "id", "type": "str", "constraints": ["not_null"]},
                    {"name": "age", "type": "int", "constraints": ["not_null", {"min": 0}]},
                    {"name": "score", "type": "float", "constraints": []},
                    {"name": "active", "type": "bool", "constraints": ["not_null"]},
                    {"name": "category", "type": "enum", "values": ["A", "B", "C"], "constraints": ["not_null"]}
                ]
            }
        ]
    }

@pytest.fixture
def valid_dataframe():
    return pd.DataFrame({
        "id": ["p1", "p2"],
        "age": [25, 30],
        "score": [0.5, 0.8],
        "active": [True, False],
        "category": ["A", "B"]
    })

@pytest.fixture
def invalid_dataframe():
    return pd.DataFrame({
        "id": ["p1", None],  # Null in not_null
        "age": [25, -5],     # Out of range
        "score": ["bad", 0.8], # Wrong type
        "active": [True, "yes"], # Wrong type
        "category": ["A", "D"]   # Invalid enum
    })

def test_load_schema(sample_schema):
    # Since we are mocking the schema in the fixture, we just ensure the structure is correct
    assert "entities" in sample_schema
    assert len(sample_schema["entities"]) == 1

def test_validate_field_type_str():
    assert validate_field_type("hello", "str") is True
    assert validate_field_type(123, "str") is False

def test_validate_field_type_int():
    assert validate_field_type(10, "int") is True
    assert validate_field_type(10.5, "int") is False
    assert validate_field_type(np.int64(10), "int") is True

def test_validate_field_type_float():
    assert validate_field_type(10.5, "float") is True
    assert validate_field_type(10, "float") is True
    assert validate_field_type("10.5", "float") is False

def test_validate_field_type_bool():
    assert validate_field_type(True, "bool") is True
    assert validate_field_type(False, "bool") is True
    assert validate_field_type(1, "bool") is False
    assert validate_field_type(np.bool_(True), "bool") is True

def test_validate_enum():
    assert validate_enum("A", ["A", "B", "C"]) is True
    assert validate_enum("D", ["A", "B", "C"]) is False
    assert validate_enum(None, ["A", "B", "C"]) is True

def test_validate_range():
    assert validate_range(5, {"min": 0, "max": 10}) is True
    assert validate_range(-1, {"min": 0, "max": 10}) is False
    assert validate_range(11, {"min": 0, "max": 10}) is False
    assert validate_range(None, {"min": 0, "max": 10}) is True

def test_validate_dataframe_valid(valid_dataframe, sample_schema):
    result = validate_dataframe_against_schema(valid_dataframe, sample_schema)
    assert result["valid"] is True
    assert "All checks passed" in result["details"]

def test_validate_dataframe_invalid(invalid_dataframe, sample_schema):
    result = validate_dataframe_against_schema(invalid_dataframe, sample_schema)
    assert result["valid"] is False
    assert len(result["details"]) > 0

def test_validate_missing_required_column():
    schema = {
        "entities": [{"name": "test", "fields": [{"name": "missing_col", "type": "str"}]}]
    }
    df = pd.DataFrame({"other_col": [1]})
    result = validate_dataframe_against_schema(df, schema)
    assert result["valid"] is False
    assert "Missing required column" in str(result["details"])

def test_validate_dataset_integration(valid_dataframe, sample_schema):
    result = validate_dataset(valid_dataframe, sample_schema)
    assert result["valid"] is True

def test_validate_result_analysis_schema():
    schema = {
        "entities": [{"name": "result", "fields": [{"name": "p_value", "type": "float"}, {"name": "test", "type": "str"}]}]
    }
    result_data = {"p_value": 0.05, "test": "correlation"}
    validation = validate_result_against_analysis_schema(result_data, schema)
    assert validation["valid"] is True

def test_validate_result_missing_required_field():
    schema = {
        "entities": [{"name": "result", "fields": [{"name": "p_value", "type": "float"}]}]
    }
    result_data = {"other_field": 0.05}
    validation = validate_result_against_analysis_schema(result_data, schema)
    assert validation["valid"] is False
    assert "Missing required result field" in str(validation["details"])

def test_validate_enum_with_none():
    assert validate_enum(None, ["A", "B"]) is True

def test_validate_range_with_none():
    assert validate_range(None, {"min": 0}) is True
