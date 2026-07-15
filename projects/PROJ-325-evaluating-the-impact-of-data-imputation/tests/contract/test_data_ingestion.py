"""
Contract test for data ingestion schema (T010).

Verifies that the output of `code/data_ingestion.py` conforms to the
schema defined in `specs/contracts/dataset.schema.yaml`.

This test ensures:
1. The required columns (weight, psu, strata, and target variable) exist.
2. The data types match the schema (numeric for design vars, numeric for target).
3. No critical columns contain NaN values where the schema forbids it.
"""
import os
import sys
import pytest
import yaml
import pandas as pd
from pathlib import Path

# Add project root to path to import config if needed, though this is a contract test
project_root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(project_root))

from data_ingestion import load_gss_data_subset, ensure_design_columns

# Path constants
SCHEMA_PATH = project_root / "specs" / "contracts" / "dataset.schema.yaml"
RAW_DATA_PATH = project_root / "data" / "raw" / "gss_2018_subset.csv"

@pytest.fixture(scope="module")
def schema():
    """Load the dataset schema contract."""
    if not SCHEMA_PATH.exists():
        pytest.fail(f"Schema file not found at {SCHEMA_PATH}. "
                    "Task T006 (contracts) must be completed first.")
    with open(SCHEMA_PATH, "r") as f:
        return yaml.safe_load(f)

@pytest.fixture(scope="module")
def data():
    """Load the ingested data artifact."""
    if not RAW_DATA_PATH.exists():
        pytest.fail(f"Data artifact not found at {RAW_DATA_PATH}. "
                    "Task T004 (data ingestion) must be completed first.")
    return pd.read_csv(RAW_DATA_PATH)

def test_required_columns_present(schema, data):
    """
    Contract Test: Verify all required columns defined in the schema exist.
    """
    required_columns = schema.get("required_columns", [])
    missing = [col for col in required_columns if col not in data.columns]
    
    assert not missing, (
        f"Data ingestion contract violation: Missing required columns: {missing}. "
        f"Expected columns per schema: {required_columns}"
    )

def test_design_columns_numeric(schema, data):
    """
    Contract Test: Verify design columns (weight, psu, strata) are numeric.
    """
    design_cols = schema.get("design_columns", [])
    
    for col in design_cols:
        if col not in data.columns:
            continue # Checked in test_required_columns_present
        
        if not pd.api.types.is_numeric_dtype(data[col]):
            pytest.fail(
                f"Data ingestion contract violation: Column '{col}' "
                f"must be numeric (design variable) but is {data[col].dtype}."
            )

def test_no_null_design_variables(schema, data):
    """
    Contract Test: Design variables (weight, psu, strata) must not be null.
    """
    design_cols = schema.get("design_columns", [])
    
    for col in design_cols:
        if col in data.columns:
            null_count = data[col].isna().sum()
            assert null_count == 0, (
                f"Data ingestion contract violation: Column '{col}' "
                f"contains {null_count} null values. Design variables must be complete."
            )

def test_target_variable_exists_and_numeric(schema, data):
    """
    Contract Test: Verify the primary analysis target variable exists and is numeric.
    """
    target_var = schema.get("target_variable")
    
    if target_var:
        assert target_var in data.columns, (
            f"Data ingestion contract violation: Target variable '{target_var}' not found."
        )
        assert pd.api.types.is_numeric_dtype(data[target_var]), (
            f"Data ingestion contract violation: Target variable '{target_var}' "
            f"must be numeric but is {data[target_var].dtype}."
        )

def test_data_not_empty(schema, data):
    """
    Contract Test: Verify the dataset is not empty.
    """
    assert len(data) > 0, "Data ingestion contract violation: Dataset is empty."

def test_column_types_match_schema(schema, data):
    """
    Contract Test: Verify column types match the schema definition exactly.
    """
    columns_spec = schema.get("columns", {})
    
    for col_name, col_spec in columns_spec.items():
        if col_name not in data.columns:
            continue
        
        expected_type = col_spec.get("type")
        actual_dtype = data[col_name].dtype
          
        # Map schema types to pandas dtypes
        type_map = {
            "integer": ["int8", "int16", "int32", "int64", "uint8", "uint16", "uint32", "uint64"],
            "number": ["float16", "float32", "float64"],
            "string": ["object", "string"],
            "boolean": ["bool"]
        }
        
        allowed_dtypes = type_map.get(expected_type, [])
        
        if expected_type and actual_dtype not in allowed_dtypes:
            pytest.fail(
                f"Data ingestion contract violation: Column '{col_name}' "
                f"expected type '{expected_type}' (dtypes: {allowed_dtypes}) "
                f"but found '{actual_dtype}'."
            )