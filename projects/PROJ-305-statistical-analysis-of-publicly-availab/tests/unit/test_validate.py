import os
import sys
import tempfile
from pathlib import Path
import pandas as pd
import pytest
import yaml

# Ensure src is in path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.data.validate import load_schema, validate_data, _get_required_columns

@pytest.fixture
def temp_schema_file():
    schema = {
        "required": ["VAX_TYPE", "SOC_CODE", "REPT_DATE"],
    }
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        yaml.dump(schema, f)
        path = f.name
    yield path
    os.unlink(path)

def test_load_schema_valid(temp_schema_file):
    schema = load_schema(temp_schema_file)
    assert "required" in schema

def test_load_schema_missing():
    with pytest.raises(FileNotFoundError):
        load_schema("non_existent_schema.yaml")

def test_validate_data_success(temp_schema_file):
    schema = load_schema(temp_schema_file)
    df = pd.DataFrame({
        "VAX_TYPE": ["COVID-19"],
        "SOC_CODE": ["100"],
        "REPT_DATE": ["2021-01-01"]
    })
    assert validate_data(df, schema) is True

def test_validate_data_missing_col(temp_schema_file):
    schema = load_schema(temp_schema_file)
    df = pd.DataFrame({
        "SOC_CODE": ["100"],
        "REPT_DATE": ["2021-01-01"]
    })
    assert validate_data(df, schema) is False

def test_validate_data_null_val(temp_schema_file):
    schema = load_schema(temp_schema_file)
    df = pd.DataFrame({
        "VAX_TYPE": [None],
        "SOC_CODE": ["100"],
        "REPT_DATE": ["2021-01-01"]
    })
    assert validate_data(df, schema) is False

def test_validate_data_empty(temp_schema_file):
    schema = load_schema(temp_schema_file)
    df = pd.DataFrame(columns=["VAX_TYPE", "SOC_CODE", "REPT_DATE"])
    assert validate_data(df, schema) is False

def test_main_cli_success(temp_schema_file):
    with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
        pd.DataFrame({"VAX_TYPE": ["A"], "SOC_CODE": ["B"], "REPT_DATE": ["C"]}).to_csv(f, index=False)
        data_path = f.name
    
    try:
        original_argv = sys.argv
        sys.argv = ["validate.py", "--input", data_path, "--schema", temp_schema_file]
        from src.data.validate import main
        with pytest.raises(SystemExit) as excinfo:
            main()
        assert excinfo.value.code == 0
    finally:
        sys.argv = original_argv
        os.unlink(data_path)

def test_main_cli_failure(temp_schema_file):
    with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
        # Missing VAX_TYPE
        pd.DataFrame({"SOC_CODE": ["B"], "REPT_DATE": ["C"]}).to_csv(f, index=False)
        data_path = f.name
    
    try:
        original_argv = sys.argv
        sys.argv = ["validate.py", "--input", data_path, "--schema", temp_schema_file]
        from src.data.validate import main
        with pytest.raises(SystemExit) as excinfo:
            main()
        assert excinfo.value.code == 1
    finally:
        sys.argv = original_argv
        os.unlink(data_path)
