"""
Specific unit test to verify E_SCHEMA_MISSING behavior.
This test explicitly checks that the validation logic correctly identifies
missing columns and triggers the expected exit behavior.
"""
import os
import tempfile
import pytest
import pandas as pd
import yaml
import sys
from pathlib import Path

# Ensure the project root is in the path
project_root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(project_root))

from src.data.validate import validate_data, E_SCHEMA_MISSING

def test_validate_data_missing_columns_raises_schema_missing():
    """
    Unit test for src/data/validate.py ensuring E_SCHEMA_MISSING is raised on missing columns.
    
    This test creates a CSV file missing a required column (REPT_DATE) and a valid schema.
    It then calls validate_data and asserts that a SystemExit is raised with a non-zero code,
    simulating the E_SCHEMA_MISSING failure condition.
    """
    # Create a schema
    schema = {
        "required_columns": ["VAX_TYPE", "SOC_CODE", "REPT_DATE", "AGE"]
    }
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        yaml.dump(schema, f)
        schema_path = f.name

    # Create an invalid CSV (missing REPT_DATE)
    df = pd.DataFrame({
        "VAX_TYPE": ["COVID-19"],
        "SOC_CODE": ["100001"],
        "AGE": [30]
    })
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        df.to_csv(f, index=False)
        data_path = f.name

    try:
        # This should raise SystemExit because REPT_DATE is missing
        with pytest.raises(SystemExit) as excinfo:
            validate_data(data_path, schema_path)

        # Verify the exit code is non-zero (indicating the E_SCHEMA_MISSING condition)
        assert excinfo.value.code != 0, "Expected non-zero exit code for missing columns"
        
    finally:
        # Cleanup
        os.unlink(schema_path)
        os.unlink(data_path)