import pytest
import pandas as pd
import yaml
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from config import load_paths

def load_schema(schema_path: str) -> dict:
    """Load schema from YAML file."""
    with open(schema_path, 'r') as f:
        return yaml.safe_load(f)

def validate_dataset_schema(df: pd.DataFrame, schema: dict):
    """Validate DataFrame against schema."""
    required_columns = schema.get('required_columns', [])
    column_types = schema.get('column_types', {})
    
    # Check required columns
    missing_columns = set(required_columns) - set(df.columns)
    assert not missing_columns, f"Missing required columns: {missing_columns}"
    
    # Check column types
    for col, expected_type in column_types.items():
        if col in df.columns:
            if expected_type == 'numeric':
                assert pd.api.types.is_numeric_dtype(df[col]), f"Column {col} is not numeric"
            elif expected_type == 'string':
                assert pd.api.types.is_string_dtype(df[col]) or df[col].dtype == object, f"Column {col} is not string"
            elif expected_type == 'non_null':
                assert df[col].notna().all(), f"Column {col} contains null values"

def test_dataset_schema_compliance():
    """Test that the processed dataset complies with the schema."""
    paths = load_paths()
    schema_path = paths['dataset_schema']
    data_path = paths['processed_descriptors']
    
    # Load schema
    schema = load_schema(schema_path)
    
    # Load data
    df = pd.read_csv(data_path)
    
    # Validate
    validate_dataset_schema(df, schema)

def test_descriptor_columns_non_null():
    """Test that all descriptor columns are non-null."""
    paths = load_paths()
    data_path = paths['processed_descriptors']
    
    df = pd.read_csv(data_path)
    
    # Check for nulls in descriptor columns
    descriptor_cols = [col for col in df.columns if 'mean' in col or 'variance' in col]
    
    for col in descriptor_cols:
        assert df[col].notna().all(), f"Descriptor column {col} contains null values"
