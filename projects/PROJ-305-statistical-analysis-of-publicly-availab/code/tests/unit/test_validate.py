"""
Unit tests for src.data.validate module.
"""
import os
import tempfile
import pytest
import pandas as pd
import yaml
from pathlib import Path

# Import the module to test
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "code"))

from src.data import validate


@pytest.fixture
def temp_schema_file():
    """Create a temporary schema file for testing."""
    schema = {
        "required_columns": ["VAX_TYPE", "SOC_CODE", "REPT_DATE", "AGE"],
        "column_constraints": {
            "VAX_TYPE": {"non_empty": True},
            "AGE": {"non_empty": False}
        }
    }
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        yaml.dump(schema, f)
        f.flush()
        yield f.name
    
    os.unlink(f.name)


@pytest.fixture
def valid_csv_file():
    """Create a temporary valid CSV file for testing."""
    data = {
        "VAX_TYPE": ["COVID-19", "Non-COVID", "Flu"],
        "SOC_CODE": ["SOC001", "SOC002", "SOC003"],
        "REPT_DATE": ["2021-01-01", "2021-01-02", "2021-01-03"],
        "AGE": [25, 30, 45]
    }
    df = pd.DataFrame(data)
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        df.to_csv(f, index=False)
        f.flush()
        yield f.name
    
    os.unlink(f.name)


@pytest.fixture
def invalid_csv_file():
    """Create a temporary CSV file missing required columns."""
    data = {
        "VAX_TYPE": ["COVID-19", "Non-COVID"],
        "AGE": [25, 30]
        # Missing SOC_CODE and REPT_DATE
    }
    df = pd.DataFrame(data)
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        df.to_csv(f, index=False)
        f.flush()
        yield f.name
    
    os.unlink(f.name)


def test_load_schema_valid(temp_schema_file):
    """Test loading a valid schema file."""
    schema = validate.load_schema(Path(temp_schema_file))
    assert "required_columns" in schema
    assert schema["required_columns"] == ["VAX_TYPE", "SOC_CODE", "REPT_DATE", "AGE"]


def test_load_schema_file_not_found():
    """Test loading a non-existent schema file exits with E_FILE_NOT_FOUND."""
    with pytest.raises(SystemExit) as exc_info:
        validate.load_schema(Path("/nonexistent/schema.yaml"))
    assert exc_info.value.code == validate.E_FILE_NOT_FOUND


def test_load_schema_invalid_yaml():
    """Test loading an invalid YAML schema file exits with E_INVALID_SCHEMA."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        f.write("invalid: yaml: content: [")
        f.flush()
        temp_path = f.name
    
    with pytest.raises(SystemExit) as exc_info:
        validate.load_schema(Path(temp_path))
    assert exc_info.value.code == validate.E_INVALID_SCHEMA
    
    os.unlink(temp_path)


def test_validate_columns_all_present():
    """Test column validation when all required columns are present."""
    df = pd.DataFrame({
        "VAX_TYPE": ["A"],
        "SOC_CODE": ["B"],
        "REPT_DATE": ["C"],
        "AGE": [1]
    })
    missing = validate.validate_columns(df, ["VAX_TYPE", "SOC_CODE", "REPT_DATE", "AGE"])
    assert missing == []


def test_validate_columns_missing():
    """Test column validation when some required columns are missing."""
    df = pd.DataFrame({
        "VAX_TYPE": ["A"],
        "AGE": [1]
    })
    missing = validate.validate_columns(df, ["VAX_TYPE", "SOC_CODE", "REPT_DATE", "AGE"])
    assert set(missing) == {"SOC_CODE", "REPT_DATE"}


def test_validate_data_valid(valid_csv_file, temp_schema_file):
    """Test validation of a valid CSV file."""
    result = validate.validate_data(valid_csv_file, temp_schema_file)
    assert result is True


def test_validate_data_missing_columns(invalid_csv_file, temp_schema_file):
    """Test validation exits with E_SCHEMA_MISSING when columns are missing."""
    with pytest.raises(SystemExit) as exc_info:
        validate.validate_data(invalid_csv_file, temp_schema_file)
    assert exc_info.value.code == validate.E_SCHEMA_MISSING


def test_validate_data_file_not_found(temp_schema_file):
    """Test validation exits with E_FILE_NOT_FOUND when input file is missing."""
    with pytest.raises(SystemExit) as exc_info:
        validate.validate_data("/nonexistent/file.csv", temp_schema_file)
    assert exc_info.value.code == validate.E_FILE_NOT_FOUND


def test_validate_data_no_schema_key(temp_schema_file, valid_csv_file):
    """Test validation exits with E_INVALID_SCHEMA if schema lacks required_columns."""
    # Create a schema without required_columns
    bad_schema = {"other_key": "value"}
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        yaml.dump(bad_schema, f)
        f.flush()
        bad_schema_path = f.name
    
    with pytest.raises(SystemExit) as exc_info:
        validate.validate_data(valid_csv_file, bad_schema_path)
    assert exc_info.value.code == validate.E_INVALID_SCHEMA
    
    os.unlink(bad_schema_path)


def test_main_command_line_valid(valid_csv_file, temp_schema_file):
    """Test main function with valid command line arguments."""
    import sys
    original_argv = sys.argv
    try:
        sys.argv = ["validate", valid_csv_file, temp_schema_file]
        # Capture exit code
        with pytest.raises(SystemExit) as exc_info:
            validate.main()
        assert exc_info.value.code == validate.E_SUCCESS
    finally:
        sys.argv = original_argv


def test_main_command_line_missing_args():
    """Test main function with missing command line arguments."""
    import sys
    original_argv = sys.argv
    try:
        sys.argv = ["validate"]
        with pytest.raises(SystemExit) as exc_info:
            validate.main()
        assert exc_info.value.code == validate.E_VALIDATION_ERROR
    finally:
        sys.argv = original_argv