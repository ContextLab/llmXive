import os
import tempfile
import pytest
import pandas as pd
import yaml
from pathlib import Path

import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from src.data.validate import load_schema, validate_columns, validate_data, main

# Fixtures
@pytest.fixture
def temp_schema_file():
    schema = {
        "required_columns": ["VAX_TYPE", "SOC_CODE", "REPT_DATE", "AGE"]
    }
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        yaml.dump(schema, f)
        return f.name

@pytest.fixture
def valid_csv_file():
    df = pd.DataFrame({
        "VAX_TYPE": ["COVID-19", "Non-COVID"],
        "SOC_CODE": ["100001", "100002"],
        "REPT_DATE": ["2021-01-01", "2021-01-02"],
        "AGE": [30, 45]
    })
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        df.to_csv(f, index=False)
        return f.name

@pytest.fixture
def invalid_csv_file():
    # Missing REPT_DATE column
    df = pd.DataFrame({
        "VAX_TYPE": ["COVID-19"],
        "SOC_CODE": ["100001"],
        "AGE": [30]
    })
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        df.to_csv(f, index=False)
        return f.name

# Tests for load_schema
def test_load_schema_valid(temp_schema_file):
    schema = load_schema(temp_schema_file)
    assert "required_columns" in schema
    assert len(schema["required_columns"]) == 4

def test_load_schema_file_not_found():
    with pytest.raises(FileNotFoundError):
        load_schema("/non/existent/path.yaml")

def test_load_schema_invalid_yaml(temp_schema_file):
    # Overwrite with invalid yaml
    with open(temp_schema_file, 'w') as f:
        f.write("invalid: yaml: content: [")
    with pytest.raises((yaml.YAMLError, ValueError)):
        load_schema(temp_schema_file)

# Tests for validate_columns
def test_validate_columns_all_present(valid_csv_file, temp_schema_file):
    schema = load_schema(temp_schema_file)
    df = pd.read_csv(valid_csv_file)
    missing = validate_columns(df, schema)
    assert len(missing) == 0

def test_validate_columns_missing(invalid_csv_file, temp_schema_file):
    schema = load_schema(temp_schema_file)
    df = pd.read_csv(invalid_csv_file)
    missing = validate_columns(df, schema)
    assert "REPT_DATE" in missing
    assert len(missing) == 1

# Tests for validate_data
def test_validate_data_valid(valid_csv_file, temp_schema_file):
    result = validate_data(valid_csv_file, temp_schema_file)
    assert result["valid"] is True
    assert result["missing_columns"] == []

def test_validate_data_missing_columns(invalid_csv_file, temp_schema_file):
    with pytest.raises(SystemExit) as exc_info:
        validate_data(invalid_csv_file, temp_schema_file)
    assert exc_info.value.code != 0

def test_validate_data_file_not_found(temp_schema_file):
    with pytest.raises(FileNotFoundError):
        validate_data("/non/existent/data.csv", temp_schema_file)

def test_validate_data_no_schema_key(invalid_csv_file):
    # Create schema without required_columns
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        yaml.dump({"other_key": []}, f)
        schema_path = f.name
    
    with pytest.raises(ValueError):
        validate_data(invalid_csv_file, schema_path)

# Tests for main
def test_main_command_line_valid(valid_csv_file, temp_schema_file):
    import sys
    original_argv = sys.argv
    try:
        sys.argv = ['validate', valid_csv_file, temp_schema_file]
        # Should not raise
        main()
    finally:
        sys.argv = original_argv

def test_main_command_line_missing_args():
    import sys
    original_argv = sys.argv
    try:
        sys.argv = ['validate']
        with pytest.raises(SystemExit):
            main()
    finally:
        sys.argv = original_argv
def test_validate_data_missing_columns_raises_system_exit(invalid_csv_file, temp_schema_file):
    """
    Unit test for src/data/validate.py ensuring E_SCHEMA_MISSING is raised on missing columns.
    This verifies that validate_data exits with a non-zero code when required columns are missing.
    """
    with pytest.raises(SystemExit) as excinfo:
        validate_data(invalid_csv_file, temp_schema_file)
    
    # Verify it's a non-zero exit code (indicating failure)
    assert excinfo.value.code != 0