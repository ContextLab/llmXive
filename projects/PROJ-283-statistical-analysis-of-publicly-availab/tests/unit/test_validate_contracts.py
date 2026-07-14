"""
Unit tests for contract validation module.
"""
import pytest
import pandas as pd
import numpy as np
import tempfile
import os
from pathlib import Path
import yaml

from src.validation.validate_contracts import (
    SchemaValidationError,
    load_schema,
    get_available_schemas,
    validate_column_exists,
    validate_column_type,
    validate_no_nulls,
    validate_column_range,
    validate_schema,
    validate_dataframe_against_contract,
    validate_all_contracts,
)

# Sample schema for testing
sample_schema = {
    "required_columns": ["id", "name", "value"],
    "column_types": {
        "id": "int",
        "name": "string",
        "value": "float"
    },
    "column_ranges": {
        "value": {"min": 0, "max": 100}
    }
}

# Valid DataFrame
valid_df = pd.DataFrame({
    "id": [1, 2, 3],
    "name": ["Alice", "Bob", "Charlie"],
    "value": [10.5, 20.3, 30.1]
})

# Invalid DataFrame - nulls
invalid_df_nulls = pd.DataFrame({
    "id": [1, None, 3],
    "name": ["Alice", "Bob", "Charlie"],
    "value": [10.5, 20.3, 30.1]
})

# Invalid DataFrame - missing column
invalid_df_missing_col = pd.DataFrame({
    "id": [1, 2, 3],
    "name": ["Alice", "Bob", "Charlie"]
})

# Invalid DataFrame - wrong type
invalid_df_wrong_type = pd.DataFrame({
    "id": ["1", "2", "3"],  # Should be int
    "name": ["Alice", "Bob", "Charlie"],
    "value": [10.5, 20.3, 30.1]
})

# Invalid DataFrame - range violation
invalid_df_range = pd.DataFrame({
    "id": [1, 2, 3],
    "name": ["Alice", "Bob", "Charlie"],
    "value": [10.5, 150.0, 30.1]  # 150 exceeds max
})

def test_validate_column_exists_valid():
    is_valid, missing = validate_column_exists(valid_df, sample_schema)
    assert is_valid
    assert len(missing) == 0

def test_validate_column_exists_missing():
    is_valid, missing = validate_column_exists(invalid_df_missing_col, sample_schema)
    assert not is_valid
    assert "value" in missing

def test_validate_column_type_valid():
    is_valid, errors = validate_column_type(valid_df, sample_schema)
    assert is_valid
    assert len(errors) == 0

def test_validate_column_type_invalid():
    is_valid, errors = validate_column_type(invalid_df_wrong_type, sample_schema)
    assert not is_valid
    assert any("id" in e for e in errors)

def test_validate_no_nulls_valid():
    is_valid, errors = validate_no_nulls(valid_df, sample_schema)
    assert is_valid
    assert len(errors) == 0

def test_validate_no_nulls_invalid():
    is_valid, errors = validate_no_nulls(invalid_df_nulls, sample_schema)
    assert not is_valid
    assert any("id" in e for e in errors)

def test_validate_column_range_valid():
    is_valid, errors = validate_column_range(valid_df, sample_schema)
    assert is_valid
    assert len(errors) == 0

def test_validate_column_range_invalid():
    is_valid, errors = validate_column_range(invalid_df_range, sample_schema)
    assert not is_valid
    assert any("150" in e or "max" in e for e in errors)

def test_validate_schema_valid():
    is_valid, errors = validate_schema(valid_df, sample_schema, "test_schema")
    assert is_valid
    assert len(errors) == 0

def test_validate_schema_invalid_nulls():
    is_valid, errors = validate_schema(invalid_df_nulls, sample_schema, "test_schema")
    assert not is_valid
    assert any("null" in e for e in errors)

def test_validate_schema_invalid_missing_col():
    is_valid, errors = validate_schema(invalid_df_missing_col, sample_schema, "test_schema")
    assert not is_valid
    assert any("Missing" in e for e in errors)

def test_validate_dataframe_against_contract_valid():
    with tempfile.TemporaryDirectory() as tmpdir:
        schema_path = Path(tmpdir) / "test.schema.yaml"
        with open(schema_path, 'w') as f:
            yaml.dump(sample_schema, f)
        
        result = validate_dataframe_against_contract(valid_df, schema_path)
        assert result is True

def test_validate_all_contracts_valid():
    with tempfile.TemporaryDirectory() as tmpdir:
        schema_path = Path(tmpdir) / "test.schema.yaml"
        with open(schema_path, 'w') as f:
            yaml.dump(sample_schema, f)
        
        results = validate_all_contracts(valid_df, Path(tmpdir))
        assert len(results) == 1
        assert results["test"] is True

def test_load_schema_missing_file():
    with pytest.raises(FileNotFoundError):
        load_schema(Path("/nonexistent/schema.yaml"))

def test_get_available_schemas():
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        # Create some schema files
        (tmp_path / "a.schema.yaml").touch()
        (tmp_path / "b.schema.yaml").touch()
        (tmp_path / "c.txt").touch()  # Should be ignored
        
        schemas = get_available_schemas(tmp_path)
        assert len(schemas) == 2
        assert all(s.suffix == ".yaml" for s in schemas)

def test_schema_validation_error_message():
    with tempfile.TemporaryDirectory() as tmpdir:
        schema_path = Path(tmpdir) / "test.schema.yaml"
        with open(schema_path, 'w') as f:
            yaml.dump(sample_schema, f)
        
        with pytest.raises(SchemaValidationError) as exc_info:
            validate_dataframe_against_contract(invalid_df_nulls, schema_path)
        
        assert "Validation failed" in str(exc_info.value)
