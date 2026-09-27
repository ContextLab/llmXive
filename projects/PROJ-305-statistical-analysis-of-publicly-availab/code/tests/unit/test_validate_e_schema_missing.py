"""
Specific test for T012 requirement: verifying E_SCHEMA_MISSING is raised on missing columns.
"""
import os
import tempfile
import pytest
import pandas as pd
import yaml
import sys
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from src.data.validate import validate_data, E_SCHEMA_MISSING


def test_validate_data_missing_columns_raises_schema_missing():
    """
    Verify that validate_data exits with E_SCHEMA_MISSING when required columns are missing.
    """
    # Create a temporary schema
    schema = {
        "version": "1.0",
        "required_columns": ["VAX_TYPE", "SOC_CODE", "REPT_DATE", "AGE", "LLT"]
    }
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as sf:
        yaml.dump(schema, sf)
        schema_path = sf.name

    # Create a CSV with missing columns (missing SOC_CODE and REPT_DATE)
    data = {
        "VAX_TYPE": ["COVID-19"],
        "LLT": ["LLT001"],
        "AGE": ["30"]
    }
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as df:
        pd.DataFrame(data).to_csv(df, index=False)
        data_path = df.name

    try:
        with pytest.raises(SystemExit) as exc_info:
            validate_data(data_path, schema_path)
        
        assert exc_info.value.code == E_SCHEMA_MISSING, f"Expected exit code {E_SCHEMA_MISSING}, got {exc_info.value.code}"
    finally:
        os.unlink(schema_path)
        os.unlink(data_path)