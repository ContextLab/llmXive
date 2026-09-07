"""
Contract tests for dataset and output schemas.
Validates that generated data files conform to the defined YAML schemas.
"""
import json
import os
import pandas as pd
import pytest
import yaml
from pathlib import Path

# Base path relative to project root
BASE_DIR = Path(__file__).parent.parent.parent
CONTRACTS_DIR = BASE_DIR / "contracts"
DATA_DIR = BASE_DIR / "data"
RESULTS_DIR = BASE_DIR / "results"

def load_schema(schema_name: str) -> dict:
    """Load a YAML schema from the contracts directory."""
    schema_path = CONTRACTS_DIR / f"{schema_name}.yaml"
    if not schema_path.exists():
        raise FileNotFoundError(f"Schema file not found: {schema_path}")
    with open(schema_path, "r") as f:
        return yaml.safe_load(f)

def validate_json_against_schema(data: dict, schema: dict, path: str) -> bool:
    """
    Basic validation of a dictionary against a JSON Schema (draft-07).
    Note: For full validation, a library like 'jsonschema' is recommended,
    but this provides a lightweight check for the contract test.
    """
    # Check required top-level keys
    if "required" in schema:
        for key in schema["required"]:
            if key not in data:
                raise AssertionError(f"Missing required key '{key}' in {path}")

    # Check properties
    if "properties" in schema:
        for key, prop_schema in schema["properties"].items():
            if key in data:
                value = data[key]
                # Type check
                if "type" in prop_schema:
                    expected_type = prop_schema["type"]
                    if expected_type == "object" and not isinstance(value, dict):
                        raise AssertionError(f"Key '{key}' in {path} must be an object, got {type(value)}")
                    elif expected_type == "array" and not isinstance(value, list):
                        raise AssertionError(f"Key '{key}' in {path} must be an array, got {type(value)}")
                    elif expected_type == "string" and not isinstance(value, str):
                        raise AssertionError(f"Key '{key}' in {path} must be a string, got {type(value)}")
                    elif expected_type == "integer" and not isinstance(value, int):
                        raise AssertionError(f"Key '{key}' in {path} must be an integer, got {type(value)}")
                    elif expected_type == "number" and not isinstance(value, (int, float)):
                        raise AssertionError(f"Key '{key}' in {path} must be a number, got {type(value)}")
    return True

@pytest.mark.contract
def test_dataset_schema_exists():
    """Verify that the dataset schema file exists and is valid YAML."""
    schema = load_schema("dataset.schema")
    assert "properties" in schema
    assert "metadata" in schema["properties"]
    assert "series" in schema["properties"]

@pytest.mark.contract
def test_output_schema_exists():
    """Verify that the output schema file exists and is valid YAML."""
    schema = load_schema("output.schema")
    assert "properties" in schema
    assert "coverage_results" in schema["properties"]

@pytest.mark.contract
def test_coverage_csv_schema_conformity():
    """
    Contract test for results/coverage.csv.
    Validates structure and data types against output.schema.yaml.
    """
    coverage_file = RESULTS_DIR / "coverage.csv"
    
    # Skip if file doesn't exist yet (pipeline not run)
    if not coverage_file.exists():
        pytest.skip("results/coverage.csv not found. Run pipeline first.")

    df = pd.read_csv(coverage_file)
    schema = load_schema("output.schema")
    
    # Validate columns
    expected_cols = [
        "series_id", "model", "horizon", "nominal_coverage", 
        "empirical_coverage", "deviation", "p_raw", "p_value"
    ]
    assert list(df.columns) == expected_cols, f"Columns mismatch. Expected {expected_cols}, got {list(df.columns)}"

    # Validate a sample row against the schema structure
    sample_row = df.iloc[0].to_dict()
    sample_schema = schema["properties"]["coverage_results"]["properties"]["sample_records"]["items"]
    
    # Check required fields in sample
    for field in sample_schema["required"]:
        assert field in sample_row, f"Missing field '{field}' in coverage data"

    # Check types
    assert isinstance(sample_row["series_id"], str)
    assert sample_row["model"] in ["ARIMA", "ETS", "Prophet", "LightGBM"]
    assert isinstance(sample_row["horizon"], int)
    assert 0 <= sample_row["nominal_coverage"] <= 1
    assert 0 <= sample_row["empirical_coverage"] <= 1
    assert 0 <= sample_row["p_raw"] <= 1
    assert 0 <= sample_row["p_value"] <= 1

@pytest.mark.contract
def test_stratified_csv_schema_conformity():
    """
    Contract test for results/stratified_coverage.csv.
    """
    stratified_file = RESULTS_DIR / "stratified_coverage.csv"
    
    if not stratified_file.exists():
        pytest.skip("results/stratified_coverage.csv not found.")

    df = pd.read_csv(stratified_file)
    
    expected_cols = [
        "subgroup_type", "subgroup_value", "model", "horizon", "avg_coverage_deviation"
    ]
    assert list(df.columns) == expected_cols, f"Columns mismatch. Expected {expected_cols}, got {list(df.columns)}"

    sample_row = df.iloc[0].to_dict()
    assert sample_row["subgroup_type"] in ["seasonality", "trend_strength"]
    assert sample_row["model"] in ["ARIMA", "ETS", "Prophet", "LightGBM"]
    assert isinstance(sample_row["horizon"], int)
    assert isinstance(sample_row["avg_coverage_deviation"], (int, float))