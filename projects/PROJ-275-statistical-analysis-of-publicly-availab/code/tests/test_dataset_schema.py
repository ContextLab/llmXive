import os
import sys
import yaml
import pytest
from pathlib import Path
from typing import Any, Dict, List

# Add project root to path if running from script
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from config import get_dataset_urls, ensure_directories
from entities import TimeSeriesMovie

SCHEMA_PATH = Path("specs/001-sentiment-revenue-lag-analysis/contracts/dataset.schema.yaml")
OUTPUT_DIR = Path("data/processed")
LOG_PATH = Path("data/logs/ingestion_log.txt")

def load_schema() -> Dict[str, Any]:
    """Load the dataset schema contract from the specs directory."""
    if not SCHEMA_PATH.exists():
        raise FileNotFoundError(f"Schema file not found at {SCHEMA_PATH}")
    with open(SCHEMA_PATH, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)

def validate_data_frame(df: Any, schema: Dict[str, Any]) -> List[str]:
    """
    Validate a pandas DataFrame against the provided schema.
    Returns a list of validation error messages. Empty list means valid.
    """
    import pandas as pd
    if not isinstance(df, pd.DataFrame):
        return ["Input is not a pandas DataFrame"]

    errors = []
    required_fields = schema.get('required_fields', [])
    column_types = schema.get('column_types', {})
    nullable_fields = schema.get('nullable_fields', [])

    # Check required columns
    missing_cols = [col for col in required_fields if col not in df.columns]
    if missing_cols:
        errors.append(f"Missing required columns: {missing_cols}")

    # Check column types
    for col, expected_type in column_types.items():
        if col in df.columns:
            # Simple type checking (pandas specific)
            if expected_type == "datetime":
                if not pd.api.types.is_datetime64_any_dtype(df[col]):
                    errors.append(f"Column '{col}' should be datetime, got {df[col].dtype}")
            elif expected_type == "numeric":
                if not pd.api.types.is_numeric_dtype(df[col]):
                    errors.append(f"Column '{col}' should be numeric, got {df[col].dtype}")
            elif expected_type == "string":
                if not pd.api.types.is_string_dtype(df[col]):
                    errors.append(f"Column '{col}' should be string, got {df[col].dtype}")

    # Check nullability for required fields
    for col in required_fields:
        if col not in nullable_fields and col in df.columns:
            if df[col].isnull().any():
                errors.append(f"Required column '{col}' contains null values")

    # Check row count constraint if present
    min_rows = schema.get('min_rows')
    if min_rows is not None:
        if len(df) < min_rows:
            errors.append(f"DataFrame has {len(df)} rows, minimum required is {min_rows}")

    return errors

# Sample schema for testing logic (not used in production validation)
sample_schema = {
    "required_fields": ["title", "release_date", "opening_weekend_revenue", "sentiment_score"],
    "column_types": {
        "title": "string",
        "release_date": "datetime",
        "opening_weekend_revenue": "numeric",
        "sentiment_score": "numeric"
    },
    "nullable_fields": ["genre", "sentiment_score"],
    "min_rows": 500
}

# Valid DataFrame for testing (dummy data for schema logic check)
import pandas as pd
import numpy as np
from datetime import datetime

valid_df = pd.DataFrame({
    "title": ["Movie A", "Movie B"],
    "release_date": pd.to_datetime(["2023-01-01", "2023-02-01"]),
    "opening_weekend_revenue": [1000000.0, 2000000.0],
    "sentiment_score": [0.8, 0.9],
    "genre": ["Action", "Drama"]
})

def test_schema_exists():
    """Verify the schema file exists in the expected location."""
    assert SCHEMA_PATH.exists(), f"Schema file missing: {SCHEMA_PATH}"

def test_valid_dataframe_passes():
    """Test that a valid dataframe passes validation against the sample schema."""
    errors = validate_data_frame(valid_df, sample_schema)
    assert len(errors) == 0, f"Valid dataframe failed validation: {errors}"

def test_missing_column_fails():
    """Test that a dataframe missing a required column fails validation."""
    bad_df = pd.DataFrame({
        "title": ["Movie A"],
        "release_date": pd.to_datetime(["2023-01-01"])
        # Missing opening_weekend_revenue and sentiment_score
    })
    errors = validate_data_frame(bad_df, sample_schema)
    assert len(errors) > 0
    assert any("Missing required columns" in e for e in errors)

def test_null_required_field_fails():
    """Test that a required column with null values fails validation."""
    bad_df = pd.DataFrame({
        "title": ["Movie A", "Movie B"],
        "release_date": pd.to_datetime(["2023-01-01", "2023-02-01"]),
        "opening_weekend_revenue": [1000000.0, None], # Null in required field
        "sentiment_score": [0.8, 0.9],
        "genre": ["Action", "Drama"]
    })
    errors = validate_data_frame(bad_df, sample_schema)
    assert len(errors) > 0
    assert any("contains null values" in e for e in errors)

def test_contract_validation_with_real_output():
    """
    Contract test: If the ingestion pipeline has run, validate the output.
    This test checks the actual data artifact against the schema contract.
    It is skipped if the data file does not exist yet (pipeline not run).
    """
    output_file = OUTPUT_DIR / "merged_clean.parquet"
    
    if not output_file.exists():
        pytest.skip(f"Output file {output_file} does not exist. Run data ingestion first.")
    
    import pandas as pd
    schema = load_schema()
    df = pd.read_parquet(output_file)
    
    errors = validate_data_frame(df, schema)
    
    # Log results
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(LOG_PATH, 'a', encoding='utf-8') as f:
        f.write(f"Contract Test T008: {output_file.name}\n")
        f.write(f"Rows: {len(df)}, Columns: {list(df.columns)}\n")
        if errors:
            f.write(f"VALIDATION FAILED: {errors}\n")
        else:
            f.write("VALIDATION PASSED\n")
        f.write("-" * 40 + "\n")
    
    assert len(errors) == 0, f"Contract validation failed: {errors}"