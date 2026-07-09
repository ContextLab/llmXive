"""
Unit tests for the Analysis Results Schema validation.
Validates that the final analysis output conforms to specs/001-sentiment-revenue-lag-analysis/contracts/analysis_results.schema.yaml
"""
import os
import sys
import yaml
import pytest

# Add parent directory to path to allow imports from code/
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pathlib import Path
from typing import Any, Dict, List

# Define the expected schema structure based on T005 (analysis_results.schema.yaml)
SCHEMA_PATH = Path(__file__).parent.parent.parent / "specs" / "001-sentiment-revenue-lag-analysis" / "contracts" / "analysis_results.schema.yaml"

def load_schema() -> Dict[str, Any]:
    """Load the analysis results schema from the contract file."""
    if not SCHEMA_PATH.exists():
        pytest.fail(f"Analysis Results Schema file not found: {SCHEMA_PATH}. Ensure T005 is complete.")
    with open(SCHEMA_PATH, "r") as f:
        return yaml.safe_load(f)

def validate_analysis_results(df: Any, schema: Dict[str, Any]) -> List[str]:
    """
    Validate a pandas DataFrame (analysis results) against the loaded schema.
    Returns a list of error messages. Empty list means valid.
    """
    errors = []

    if df is None:
        return ["Analysis Results DataFrame is None"]

    columns = set(df.columns)
    
    # 1. Check required columns from schema
    required_columns = schema.get("required_columns", [])
    missing_cols = set(required_columns) - columns
    if missing_cols:
        errors.append(f"Missing required columns in analysis results: {missing_cols}")

    # 2. Validate column types
    columns_def = schema.get("columns", {})
    for col_name, col_spec in columns_def.items():
        if col_name in columns:
            col_type = col_spec.get("type")
            if col_type == "numeric":
                if not pd.api.types.is_numeric_dtype(df[col_name]):
                    errors.append(f"Column '{col_name}' must be numeric but is {df[col_name].dtype}")
            elif col_type == "string":
                if not pd.api.types.is_string_dtype(df[col_name]):
                    pass # Allow object
            elif col_type == "integer":
                if not pd.api.types.is_integer_dtype(df[col_name]):
                    errors.append(f"Column '{col_name}' must be integer but is {df[col_name].dtype}")
            
            # Check for nulls if specified
            if col_spec.get("nullable") is False:
                if df[col_name].isnull().any():
                    errors.append(f"Column '{col_name}' must not contain null values")

    # 3. Specific business logic checks for analysis results
    # e.g., lag cannot be negative if defined as positive offset, or p-value must be [0,1]
    if "p_value" in columns:
        if (df["p_value"] < 0).any() or (df["p_value"] > 1).any():
            errors.append("p_value must be between 0 and 1")
    
    if "lag_weeks" in columns:
        # Assuming lag is an integer offset
        if not pd.api.types.is_integer_dtype(df["lag_weeks"]) and not pd.api.types.is_numeric_dtype(df["lag_weeks"]):
             errors.append("lag_weeks should be numeric")

    return errors

@pytest.fixture
def sample_schema():
    return load_schema()

@pytest.fixture
def valid_analysis_df():
    """Create a minimal valid Analysis Results DataFrame."""
    try:
        import pandas as pd
    except ImportError:
        pytest.skip("pandas not installed")
    
    return pd.DataFrame({
        "genre": ["Action", "Drama"],
        "optimal_lag_weeks": [2, 3],
        "correlation_coefficient": [0.65, 0.72],
        "p_value": [0.01, 0.005],
        "sample_size": [150, 200],
        "decay_rate": [-0.05, -0.03]
    })

def test_schema_exists(sample_schema):
    """Test that the analysis results schema file is valid YAML."""
    assert isinstance(sample_schema, dict)
    assert "required_columns" in sample_schema or "columns" in sample_schema

def test_valid_analysis_passes(valid_analysis_df, sample_schema):
    """Test that a correctly formatted analysis DataFrame passes validation."""
    errors = validate_analysis_results(valid_analysis_df, sample_schema)
    assert len(errors) == 0, f"Validation failed for valid data: {errors}"

def test_missing_column_fails(sample_schema):
    """Test that a DataFrame missing a required column fails."""
    try:
        import pandas as pd
    except ImportError:
        pytest.skip("pandas not installed")
    
    bad_df = pd.DataFrame({
        "genre": ["Action"],
        # Missing optimal_lag_weeks, etc.
    })
    errors = validate_analysis_results(bad_df, sample_schema)
    assert len(errors) > 0
    assert any("Missing required columns" in e for e in errors)

def test_invalid_p_value_fails(sample_schema):
    """Test that a p-value outside [0, 1] is caught."""
    try:
        import pandas as pd
    except ImportError:
        pytest.skip("pandas not installed")
    
    bad_df = pd.DataFrame({
        "genre": ["Action"],
        "optimal_lag_weeks": [2],
        "correlation_coefficient": [0.5],
        "p_value": [1.5], # Invalid
        "sample_size": [100],
        "decay_rate": [-0.05]
    })
    errors = validate_analysis_results(bad_df, sample_schema)
    assert any("p_value must be between 0 and 1" in e for e in errors)

if __name__ == "__main__":
    pytest.main([__file__, "-v"])