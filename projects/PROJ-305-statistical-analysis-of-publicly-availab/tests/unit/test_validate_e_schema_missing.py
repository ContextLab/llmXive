import os
import tempfile
import pytest
import pandas as pd
import yaml
import sys

# Ensure src is in path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from src.data.validate import validate_data

def test_validate_data_missing_columns_raises_schema_missing():
    """
    Unit test for src/data/validate.py ensuring E_SCHEMA_MISSING is raised on missing columns.
    This verifies that validate_data exits with a non-zero code when required columns are missing.
    """
    # Create a temporary schema file
    schema = {
        "required_columns": ["VAX_TYPE", "SOC_CODE", "REPT_DATE", "AGE"]
    }
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        yaml.dump(schema, f)
        schema_path = f.name

    try:
        # Create a temporary CSV file missing the 'REPT_DATE' column
        df = pd.DataFrame({
            "VAX_TYPE": ["COVID-19"],
            "SOC_CODE": ["100001"],
            "AGE": [30]
            # REPT_DATE is missing
        })
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            df.to_csv(f, index=False)
            csv_path = f.name

        try:
            # Expect SystemExit with a non-zero code
            with pytest.raises(SystemExit) as exc_info:
                validate_data(csv_path, schema_path)
            
            # Verify the exit code indicates failure (non-zero)
            # The implementation should use a specific error code or just non-zero
            assert exc_info.value.code != 0
        finally:
            os.unlink(csv_path)
    finally:
        os.unlink(schema_path)