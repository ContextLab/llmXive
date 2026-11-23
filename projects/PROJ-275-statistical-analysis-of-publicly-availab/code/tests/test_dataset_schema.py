"""
Unit tests for the Dataset Schema validation.
Validates that the processed dataset conforms to specs/001-sentiment-revenue-lag-analysis/contracts/dataset.schema.yaml
"""
import os
import sys
import yaml
import pytest
import pandas as pd
from pathlib import Path
from typing import Any, Dict, List

# Add parent directory to path to allow imports from code/
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

SCHEMA_PATH = Path(__file__).parent.parent.parent / "specs" / "001-sentiment-revenue-lag-analysis" / "contracts" / "dataset.schema.yaml"

def load_schema() -> Dict[str, Any]:
    """Load the dataset schema from the contract file."""
    if not SCHEMA_PATH.exists():
        pytest.fail(f"Dataset Schema file not found: {SCHEMA_PATH}. Ensure T005 is complete.")
    with open(SCHEMA_PATH, "r") as f:
        return yaml.safe_load(f)

def validate_data_frame(df: pd.DataFrame, schema: Dict[str, Any]) -> List[str]:
    """
    Validate a pandas DataFrame (dataset) against the loaded schema.
    Returns a list of error messages. Empty list means valid.
    """
    errors = []

    if df is None:
        return ["Dataset DataFrame is None"]

    columns = set(df.columns)
    
    # 1. Check required columns from schema
    required_columns = schema.get("required_columns", [])
    missing_cols = set(required_columns) - columns
    if missing_cols:
        errors.append(f"Missing required columns in dataset: {missing_cols}")

    # 2. Validate column types and nullability
    columns_def = schema.get("columns", {})
    for col_name, col_spec in columns_def.items():
        if col_name in columns:
            col_type = col_spec.get("type")
            if col_type == "numeric":
                if not pd.api.types.is_numeric_dtype(df[col_name]):
                    errors.append(f"Column '{col_name}' must be numeric but is {df[col_name].dtype}")
            elif col_type == "string":
                # Allow object or string dtype
                if not (pd.api.types.is_string_dtype(df[col_name]) or df[col_name].dtype == 'object'):
                    errors.append(f"Column '{col_name}' must be string but is {df[col_name].dtype}")
            elif col_type == "integer":
                if not pd.api.types.is_integer_dtype(df[col_name]):
                    errors.append(f"Column '{col_name}' must be integer but is {df[col_name].dtype}")
            elif col_type == "datetime":
                if not pd.api.types.is_datetime64_any_dtype(df[col_name]):
                    errors.append(f"Column '{col_name}' must be datetime but is {df[col_name].dtype}")
            
            # Check for nulls if specified
            if col_spec.get("nullable") is False:
                if df[col_name].isnull().any():
                    errors.append(f"Column '{col_name}' must not contain null values")

    # 3. Specific business logic checks for dataset
    # e.g., row_count >= 500 check
    if len(df) < 500:
        errors.append(f"Dataset must contain at least 500 rows, found {len(df)}")

    # Check specific columns if present
    if "opening_weekend_revenue" in columns:
        if (df["opening_weekend_revenue"] < 0).any():
            errors.append("opening_weekend_revenue cannot be negative")
    
    if "sentiment_score" in columns:
        if (df["sentiment_score"] < -1).any() or (df["sentiment_score"] > 1).any():
            errors.append("sentiment_score must be between -1 and 1")

    return errors

@pytest.fixture
def sample_schema():
    return load_schema()

@pytest.fixture
def valid_dataframe(sample_schema):
    """Create a minimal valid Dataset DataFrame."""
    # Create a sample DataFrame that meets the schema requirements
    # Assuming schema requires: title, release_date, opening_weekend_revenue, sentiment_score, genre
    data = {
        "title": ["Movie A", "Movie B"] * 250, # Ensure >= 500 rows
        "release_date": pd.date_range(start="2023-01-01", periods=500, freq="D"),
        "opening_weekend_revenue": [1000000.0 + i * 1000 for i in range(500)],
        "sentiment_score": [0.5 + (i % 10) * 0.01 for i in range(500)],
        "genre": ["Action"] * 250 + ["Drama"] * 250
    }
    return pd.DataFrame(data)

def test_schema_exists(sample_schema):
    """Test that the dataset schema file is valid YAML."""
    assert isinstance(sample_schema, dict)
    assert "required_columns" in sample_schema or "columns" in sample_schema

def test_valid_dataframe_passes(valid_dataframe, sample_schema):
    """Test that a correctly formatted DataFrame passes validation."""
    errors = validate_data_frame(valid_dataframe, sample_schema)
    assert len(errors) == 0, f"Validation failed for valid data: {errors}"

def test_missing_column_fails(sample_schema):
    """Test that a DataFrame missing a required column fails."""
    bad_df = pd.DataFrame({
        "title": ["Movie A"],
        "release_date": ["2023-01-01"],
        # Missing opening_weekend_revenue, etc.
    })
    errors = validate_data_frame(bad_df, sample_schema)
    assert len(errors) > 0
    assert any("Missing required columns" in e for e in errors)

def test_null_required_field_fails(sample_schema):
    """Test that a DataFrame with null in a non-nullable field fails."""
    data = {
        "title": ["Movie A"] * 500,
        "release_date": pd.date_range(start="2023-01-01", periods=500, freq="D"),
        "opening_weekend_revenue": [1000000.0] * 499 + [None], # One null
        "sentiment_score": [0.5] * 500,
        "genre": ["Action"] * 500
    }
    bad_df = pd.DataFrame(data)
    errors = validate_data_frame(bad_df, sample_schema)
    assert any("must not contain null values" in e for e in errors)

def test_contract_validation_with_real_output(sample_schema):
    """
    Integration test: Validate the actual output file if it exists.
    This ensures the pipeline output conforms to the schema.
    """
    output_path = Path(__file__).parent.parent.parent / "data" / "processed" / "merged_clean.parquet"
    if not output_path.exists():
        pytest.skip(f"Real output file not found: {output_path}. Skipping integration test.")
    
    try:
        df = pd.read_parquet(output_path)
    except Exception as e:
        pytest.fail(f"Failed to load real output file: {e}")
    
    errors = validate_data_frame(df, sample_schema)
    # If errors exist, the pipeline output does not match the contract
    if errors:
        pytest.fail(f"Real output file failed schema validation: {errors}")

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
