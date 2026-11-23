"""
Contract test for data schema validation.

Validates that the processed dataset conforms to the schema defined in
contracts/dataset.schema.yaml. This ensures data integrity before model training.

Run with: pytest tests/contract/test_data_schema.py -v
"""

import os
import sys
import yaml
import pytest
import pandas as pd
import numpy as np
from pathlib import Path

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.utils.config import DATA_PROCESSED_DIR


def load_schema():
    """Load the dataset schema from YAML file."""
    schema_path = PROJECT_ROOT / "contracts" / "dataset.schema.yaml"
    if not schema_path.exists():
        raise FileNotFoundError(f"Schema file not found: {schema_path}")
    
    with open(schema_path, 'r') as f:
        return yaml.safe_load(f)


def get_processed_data_path():
    """Get the path to the processed dataset."""
    # Look for the most recent processed CSV file
    data_dir = Path(DATA_PROCESSED_DIR)
    if not data_dir.exists():
        raise FileNotFoundError(f"Processed data directory not found: {data_dir}")
    
    csv_files = list(data_dir.glob("*.csv"))
    if not csv_files:
        raise FileNotFoundError(f"No CSV files found in {data_dir}")
    
    # Return the most recent file
    return max(csv_files, key=os.path.getctime)


def test_schema_file_exists():
    """Contract test: Verify schema file exists."""
    schema_path = PROJECT_ROOT / "contracts" / "dataset.schema.yaml"
    assert schema_path.exists(), "Schema file must exist for contract testing"


def test_schema_structure():
    """Contract test: Verify schema has required structure."""
    schema = load_schema()
    
    assert "type" in schema, "Schema must have 'type' field"
    assert schema["type"] == "object", "Schema type must be 'object'"
    assert "required" in schema, "Schema must have 'required' field"
    assert "properties" in schema, "Schema must have 'properties' field"
    
    required_fields = ["columns", "dtypes", "sample_count"]
    for field in required_fields:
        assert field in schema["required"], f"Schema must require '{field}'"
        assert field in schema["properties"], f"Schema must define '{field}'"


def test_data_loads():
    """Contract test: Verify processed data can be loaded."""
    data_path = get_processed_data_path()
    assert data_path.exists(), f"Processed data file must exist: {data_path}"
    
    df = pd.read_csv(data_path)
    assert not df.empty, "Processed dataset must not be empty"

def test_column_presence():
    """Contract test: Verify all required columns are present."""
    schema = load_schema()
    data_path = get_processed_data_path()
    df = pd.read_csv(data_path)
    
    expected_columns = schema["properties"]["columns"]["items"]
    
    missing_columns = []
    for col in expected_columns:
        if col not in df.columns:
            missing_columns.append(col)
    
    assert not missing_columns, f"Missing required columns: {missing_columns}"

def test_data_types():
    """Contract test: Verify data types match schema."""
    schema = load_schema()
    data_path = get_processed_data_path()
    df = pd.read_csv(data_path)
    
    expected_dtypes = schema["properties"]["dtypes"]["properties"]
    
    type_errors = []
    for col, expected_type in expected_dtypes.items():
        if col not in df.columns:
            continue
        
        actual_dtype = df[col].dtype
        
        # Map schema types to pandas dtypes
        if expected_type["type"] == "number":
            if not np.issubdtype(actual_dtype, np.number):
                type_errors.append(f"Column '{col}' should be numeric, got {actual_dtype}")
        elif expected_type["type"] == "integer":
            if not np.issubdtype(actual_dtype, np.integer):
                type_errors.append(f"Column '{col}' should be integer, got {actual_dtype}")
    
    assert not type_errors, "Data type errors:\n" + "\n".join(type_errors)

def test_no_null_target():
    """Contract test: Verify target variable has no null values."""
    data_path = get_processed_data_path()
    df = pd.read_csv(data_path)
    
    target_col = "yield_strength"
    if target_col in df.columns:
        null_count = df[target_col].isnull().sum()
        assert null_count == 0, f"Target variable '{target_col}' must not have null values. Found {null_count} nulls."

def test_sample_count_valid():
    """Contract test: Verify sample count meets minimum requirement."""
    schema = load_schema()
    data_path = get_processed_data_path()
    df = pd.read_csv(data_path)
    
    min_samples = schema["properties"]["sample_count"]["minimum"]
    actual_count = len(df)
    
    assert actual_count >= min_samples, (
        f"Dataset must have at least {min_samples} samples. "
        f"Found {actual_count} samples."
    )

def test_full_schema_validation():
    """Contract test: Run full validation against schema."""
    schema = load_schema()
    data_path = get_processed_data_path()
    df = pd.read_csv(data_path)
    
    # Check all required properties
    errors = []
    
    # 1. Check columns
    expected_columns = schema["properties"]["columns"]["items"]
    for col in expected_columns:
        if col not in df.columns:
            errors.append(f"Missing column: {col}")
    
    # 2. Check data types
    expected_dtypes = schema["properties"]["dtypes"]["properties"]
    for col, type_def in expected_dtypes.items():
        if col in df.columns:
            if type_def["type"] == "number" and not np.issubdtype(df[col].dtype, np.number):
                errors.append(f"Column '{col}' is not numeric")
    
    # 3. Check sample count
    if len(df) < schema["properties"]["sample_count"]["minimum"]:
        errors.append(f"Insufficient samples: {len(df)} < {schema['properties']['sample_count']['minimum']}")
    
    # 4. Check for null target
    if "yield_strength" in df.columns:
        nulls = df["yield_strength"].isnull().sum()
        if nulls > 0:
            errors.append(f"Target has {nulls} null values")
    
    assert not errors, f"Schema validation failed:\n" + "\n".join(errors)

if __name__ == "__main__":
    pytest.main([__file__, "-v"])