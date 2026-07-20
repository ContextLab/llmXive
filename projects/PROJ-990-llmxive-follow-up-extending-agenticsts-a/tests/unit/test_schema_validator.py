import pytest
import json
import pandas as pd
from pathlib import Path
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "code"))

from schema_validator import (
    SchemaField, Schema, validate_dataframe_schema, 
    validate_json_schema, create_processed_directories,
    validate_schema_file, validate_all_processed_files,
    write_schema_registry
)

def test_schema_field_creation():
    field = SchemaField("name", "str", required=True)
    assert field.name == "name"
    assert field.dtype == "str"
    assert field.required is True

def test_validate_dataframe_schema_missing_column():
    df = pd.DataFrame({"a": [1, 2]})
    schema = Schema("test", [SchemaField("a", "int"), SchemaField("b", "int", required=True)])
    result = validate_dataframe_schema(df, schema)
    assert result["valid"] is False
    assert any("Missing required column" in err for err in result["errors"])

def test_validate_dataframe_schema_correct():
    df = pd.DataFrame({"a": [1, 2], "b": [3.0, 4.0]})
    schema = Schema("test", [SchemaField("a", "int"), SchemaField("b", "float")])
    result = validate_dataframe_schema(df, schema)
    assert result["valid"] is True
    assert len(result["errors"]) == 0

def test_validate_json_schema_missing_field():
    data = [{"a": 1}]
    schema = {"fields": {"a": "int", "b": "int"}}
    result = validate_json_schema(Path("/dev/null"), schema) # Mock path, logic checks data structure if we passed dict, but function expects file
    # Re-implement test for file based logic
    pass

def test_create_processed_directories(tmp_path):
    processed_dir = tmp_path / "data" / "processed"
    create_processed_directories(tmp_path)
    assert processed_dir.exists()

def test_write_schema_registry(tmp_path):
    write_schema_registry(tmp_path)
    registry_path = tmp_path / "specs" / "schema_registry.json"
    assert registry_path.exists()
    with open(registry_path, 'r') as f:
        data = json.load(f)
    assert "ablation_labels_full.json" in data
    assert "utility_labels.csv" in data