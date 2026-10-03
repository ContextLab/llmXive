import os
import sys
import tempfile
import pytest
import pandas as pd
import yaml
from pathlib import Path

# Add parent directory to path for imports if needed, though usually handled by test runner
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'code'))

from src.data.validate import load_schema, validate_columns, validate_data, E_SCHEMA_MISSING, E_VALIDATION_FAILED

@pytest.fixture
def temp_schema_file():
    schema = {
        "name": "test_schema",
        "required_columns": ["VAX_TYPE", "SOC_CODE", "REPT_DATE", "AGE", "SOC"],
        "column_definitions": {
            "VAX_TYPE": {"type": "string", "nullable": False},
            "SOC_CODE": {"type": "string", "nullable": False},
            "REPT_DATE": {"type": "date", "nullable": False},
            "AGE": {"type": "numeric", "nullable": True},
            "SOC": {"type": "string", "nullable": False}
        }
    }
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        yaml.dump(schema, f)
        yield f.name
    os.unlink(f.name)

@pytest.fixture
def valid_csv_file():
    data = {
        "VAX_TYPE": ["COVID-19", "Influenza"],
        "SOC_CODE": ["10000001", "10000002"],
        "REPT_DATE": ["01/01/2021", "02/02/2021"],
        "AGE": [30, 45],
        "SOC": ["Cardiac", "Respiratory"]
    }
    df = pd.DataFrame(data)
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        df.to_csv(f, index=False)
        yield f.name
    os.unlink(f.name)

@pytest.fixture
def invalid_csv_file():
    data = {
        "VAX_TYPE": ["COVID-19"],
        "REPT_DATE": ["01/01/2021"],
        "AGE": [30]
        # Missing SOC_CODE and SOC
    }
    df = pd.DataFrame(data)
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        df.to_csv(f, index=False)
        yield f.name
    os.unlink(f.name)

class TestLoadSchema:
    def test_load_schema_valid(self, temp_schema_file):
        schema = load_schema(temp_schema_file)
        assert schema["name"] == "test_schema"
        assert "required_columns" in schema

    def test_load_schema_missing_file(self):
        with pytest.raises(FileNotFoundError):
            load_schema("non_existent_path.yaml")

class TestValidateColumns:
    def test_validate_columns_pass(self):
        df = pd.DataFrame({"A": [1], "B": [2]})
        cols = ["A", "B"]
        missing = validate_columns(df, cols)
        assert missing == []

    def test_validate_columns_fail(self):
        df = pd.DataFrame({"A": [1]})
        cols = ["A", "B"]
        missing = validate_columns(df, cols)
        assert missing == ["B"]

class TestValidateData:
    def test_validate_data_success(self, temp_schema_file):
        schema = load_schema(temp_schema_file)
        df = pd.DataFrame({
            "VAX_TYPE": ["COVID-19"],
            "SOC_CODE": ["10000001"],
            "REPT_DATE": ["01/01/2021"],
            "AGE": [30],
            "SOC": ["Cardiac"]
        })
        assert validate_data(df, schema) is True

    def test_validate_data_missing_columns_raises_schema_missing(self, temp_schema_file, invalid_csv_file):
        schema = load_schema(temp_schema_file)
        df = pd.read_csv(invalid_csv_file)
        with pytest.raises(SystemExit) as excinfo:
            validate_data(df, schema)
        assert excinfo.value.code == E_SCHEMA_MISSING

    def test_validate_data_empty_dataframe_raises(self, temp_schema_file):
        schema = load_schema(temp_schema_file)
        df = pd.DataFrame(columns=["VAX_TYPE", "SOC_CODE", "REPT_DATE", "AGE", "SOC"])
        with pytest.raises(SystemExit) as excinfo:
            validate_data(df, schema)
        assert excinfo.value.code == E_VALIDATION_FAILED

class TestMainCommandLine:
    def test_main_valid(self, temp_schema_file, valid_csv_file, caplog):
        # Simulate sys.argv for main
        original_argv = sys.argv
        try:
            sys.argv = ['validate.py', '--data', valid_csv_file, '--schema', temp_schema_file]
            from src.data.validate import main
            # main should exit with 0 on success
            # We need to catch the SystemExit
            with pytest.raises(SystemExit) as excinfo:
                main()
            assert excinfo.value.code == 0
        finally:
            sys.argv = original_argv

    def test_main_missing_data(self, temp_schema_file, caplog):
        original_argv = sys.argv
        try:
            sys.argv = ['validate.py', '--data', 'non_existent.csv', '--schema', temp_schema_file]
            from src.data.validate import main
            with pytest.raises(SystemExit) as excinfo:
                main()
            assert excinfo.value.code == 2 # E_DATA_MISSING
        finally:
            sys.argv = original_argv

    def test_main_missing_schema(self, valid_csv_file, caplog):
        original_argv = sys.argv
        try:
            sys.argv = ['validate.py', '--data', valid_csv_file, '--schema', 'non_existent.yaml']
            from src.data.validate import main
            with pytest.raises(SystemExit) as excinfo:
                main()
            assert excinfo.value.code == 1 # E_SCHEMA_MISSING
        finally:
            sys.argv = original_argv