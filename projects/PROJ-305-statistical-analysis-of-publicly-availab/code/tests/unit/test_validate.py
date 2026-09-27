"""
Unit tests for src/data/validate.py
"""
import os
import sys
import tempfile
import pytest
import pandas as pd
import yaml
from pathlib import Path

# Add project root to path for imports if running standalone
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from src.data.validate import load_schema, validate_columns, validate_data, E_SCHEMA_MISSING


@pytest.fixture
def temp_schema_file():
    """Creates a temporary schema file for testing."""
    schema = {
        "version": "1.0",
        "required_columns": ["VAX_TYPE", "SOC_CODE", "REPT_DATE", "AGE", "LLT"]
    }
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        yaml.dump(schema, f)
        temp_path = f.name
    yield temp_path
    os.unlink(temp_path)


@pytest.fixture
def valid_csv_file():
    """Creates a temporary CSV file with valid columns."""
    data = {
        "VAX_TYPE": ["COVID-19", "Influenza"],
        "SOC_CODE": ["SOC001", "SOC002"],
        "LLT": ["LLT001", "LLT002"],
        "REPT_DATE": ["2021-01-01", "2021-01-02"],
        "AGE": ["30", "45"]
    }
    df = pd.DataFrame(data)
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        df.to_csv(f, index=False)
        temp_path = f.name
    yield temp_path
    os.unlink(temp_path)


@pytest.fixture
def invalid_csv_file():
    """Creates a temporary CSV file with missing columns."""
    data = {
        "VAX_TYPE": ["COVID-19"],
        "LLT": ["LLT001"],
        "AGE": ["30"]
        # Missing SOC_CODE and REPT_DATE
    }
    df = pd.DataFrame(data)
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        df.to_csv(f, index=False)
        temp_path = f.name
    yield temp_path
    os.unlink(temp_path)


class TestLoadSchema:
    def test_load_schema_success(self, temp_schema_file):
        schema = load_schema(temp_schema_file)
        assert "version" in schema
        assert "required_columns" in schema
        assert schema["version"] == "1.0"

    def test_load_schema_not_found(self):
        with pytest.raises(FileNotFoundError):
            load_schema("non_existent_file.yaml")


class TestValidateColumns:
    def test_validate_columns_success(self):
        df = pd.DataFrame({"A": [1], "B": [2], "C": [3]})
        assert validate_columns(df, ["A", "B", "C"]) is True

    def test_validate_columns_missing(self):
        df = pd.DataFrame({"A": [1], "B": [2]})
        assert validate_columns(df, ["A", "B", "C"]) is False


class TestValidateData:
    def test_validate_data_valid(self, valid_csv_file, temp_schema_file):
        result = validate_data(valid_csv_file, temp_schema_file)
        assert result is True

    def test_validate_data_missing_columns_raises(self, invalid_csv_file, temp_schema_file):
        with pytest.raises(SystemExit) as exc_info:
            validate_data(invalid_csv_file, temp_schema_file)
        assert exc_info.value.code == E_SCHEMA_MISSING

    def test_validate_data_file_not_found(self, temp_schema_file):
        with pytest.raises(SystemExit) as exc_info:
            validate_data("non_existent.csv", temp_schema_file)
        assert exc_info.value.code == E_SCHEMA_MISSING


class TestMainCommandLine:
    def test_main_success(self, valid_csv_file, temp_schema_file, capsys):
        # Simulate command line arguments
        original_argv = sys.argv
        try:
            sys.argv = ['validate.py', valid_csv_file, temp_schema_file]
            from src.data.validate import main
            # We expect main to exit with 0 on success
            # However, pytest captures sys.exit. We need to handle this carefully.
            # Ideally, we test the logic, but for CLI tools, checking exit code is standard.
            with pytest.raises(SystemExit) as exc_info:
                main()
            assert exc_info.value.code == 0
        finally:
            sys.argv = original_argv

    def test_main_failure(self, invalid_csv_file, temp_schema_file, capsys):
        original_argv = sys.argv
        try:
            sys.argv = ['validate.py', invalid_csv_file, temp_schema_file]
            from src.data.validate import main
            with pytest.raises(SystemExit) as exc_info:
                main()
            assert exc_info.value.code == E_SCHEMA_MISSING
        finally:
            sys.argv = original_argv
