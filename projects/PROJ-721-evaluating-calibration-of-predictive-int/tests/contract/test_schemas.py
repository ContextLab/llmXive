"""
Contract tests for dataset and output schemas.
Validates that data files adhere to the defined YAML schemas.
"""
import os
import json
import yaml
from pathlib import Path
import pytest
from typing import Dict, Any, List

# Project root relative to this file
ROOT_DIR = Path(__file__).parent.parent.parent
CONTRACTS_DIR = ROOT_DIR / "contracts"

def load_schema(schema_name: str) -> Dict[str, Any]:
    """Load a schema file from the contracts directory."""
    schema_path = CONTRACTS_DIR / f"{schema_name}"
    if not schema_path.exists():
        raise FileNotFoundError(f"Schema file not found: {schema_path}")
    
    with open(schema_path, "r") as f:
        return yaml.safe_load(f)

def validate_csv_structure(df: Any, schema_key: str, schema: Dict[str, Any]) -> None:
    """
    Validate a pandas DataFrame against a specific schema key.
    Note: This is a structural check. For full type checking, pydantic or jsonschema is recommended.
    """
    required_columns = schema[schema_key]["properties"]["columns"]["enum"]
    actual_columns = list(df.columns)
    
    # Check column presence
    missing_cols = set(required_columns) - set(actual_columns)
    if missing_cols:
        raise AssertionError(f"Missing required columns: {missing_cols}")
    
    # Check column order (optional but strict for contracts)
    if actual_columns != required_columns:
        # Depending on strictness, we might just warn or fail. 
        # For contract testing, let's fail if order is wrong.
        raise AssertionError(f"Column order mismatch. Expected: {required_columns}, Got: {actual_columns}")

def test_dataset_schema_exists():
    """Ensure the dataset schema file exists."""
    assert (CONTRACTS_DIR / "dataset.schema.yaml").exists()

def test_output_schema_exists():
    """Ensure the output schema file exists."""
    assert (CONTRACTS_DIR / "output.schema.yaml").exists()

def test_dataset_schema_valid_yaml():
    """Ensure dataset schema is valid YAML."""
    schema = load_schema("dataset.schema.yaml")
    assert "type" in schema
    assert "properties" in schema
    assert "series" in schema["properties"]

def test_output_schema_valid_yaml():
    """Ensure output schema is valid YAML."""
    schema = load_schema("output.schema.yaml")
    assert "coverage_csv" in schema
    assert "stratified_coverage_csv" in schema
    assert "recalibration_csv" in schema
    assert "sensitivity_analysis_csv" in schema

@pytest.fixture
def mock_coverage_df():
    """Create a mock DataFrame matching coverage.csv schema."""
    import pandas as pd
    data = {
        "series_id": ["M1", "M2"],
        "model": ["ARIMA", "Prophet"],
        "horizon": [1, 12],
        "nominal_coverage": [0.80, 0.95],
        "empirical_coverage": [0.78, 0.94],
        "deviation": [0.02, 0.01],
        "p_raw": [0.05, 0.10],
        "p_value": [0.10, 0.15]
    }
    return pd.DataFrame(data)

@pytest.fixture
def mock_stratified_df():
    """Create a mock DataFrame matching stratified_coverage.csv schema."""
    import pandas as pd
    data = {
        "subgroup_type": ["seasonality", "trend_strength"],
        "subgroup_value": ["Yes", "High"],
        "model": ["ARIMA", "ETS"],
        "horizon": [1, 6],
        "avg_coverage_deviation": [0.01, 0.02]
    }
    return pd.DataFrame(data)

def test_coverage_schema_structure(mock_coverage_df):
    """Validate the structure of coverage.csv against schema."""
    schema = load_schema("output.schema.yaml")
    validate_csv_structure(mock_coverage_df, "coverage_csv", schema)

def test_stratified_schema_structure(mock_stratified_df):
    """Validate the structure of stratified_coverage.csv against schema."""
    schema = load_schema("output.schema.yaml")
    validate_csv_structure(mock_stratified_df, "stratified_coverage_csv", schema)

def test_recalibration_schema_structure():
    """Validate the structure of recalibration.csv against schema."""
    import pandas as pd
    schema = load_schema("output.schema.yaml")
    
    data = {
        "series_id": ["M1"],
        "model": ["LightGBM"],
        "horizon": [1],
        "baseline_coverage": [0.75],
        "recalibrated_coverage": [0.80],
        "improvement": [0.05],
        "p_value_improvement": [0.03]
    }
    df = pd.DataFrame(data)
    validate_csv_structure(df, "recalibration_csv", schema)

def test_sensitivity_schema_structure():
    """Validate the structure of sensitivity_analysis.csv against schema."""
    import pandas as pd
    schema = load_schema("output.schema.yaml")
    
    data = {
        "threshold": [0.01],
        "model": ["ARIMA"],
        "horizon": [1],
        "avg_deviation": [0.005],
        "series_count": [100]
    }
    df = pd.DataFrame(data)
    validate_csv_structure(df, "sensitivity_analysis_csv", schema)
