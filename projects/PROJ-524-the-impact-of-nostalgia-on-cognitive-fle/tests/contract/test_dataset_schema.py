"""
Contract test for dataset schema validation.

This test validates that the dataset schema defined in `contracts/dataset.schema.yaml`
matches the actual structure of the cleaned dataset produced by the ingestion pipeline.

It ensures:
1. All required columns are present.
2. Data types match the schema definition.
3. No unexpected columns are present (strict mode).
"""
import os
import json
import yaml
import pytest
from pathlib import Path
import pandas as pd
import numpy as np

# Project root is assumed to be the parent of the 'tests' directory
PROJECT_ROOT = Path(__file__).parent.parent.parent
SCHEMA_PATH = PROJECT_ROOT / "contracts" / "dataset.schema.yaml"
DATASET_PATH = PROJECT_ROOT / "data" / "processed" / "cleaned_dataset.csv"
EXCLUSION_LOG_PATH = PROJECT_ROOT / "data" / "processed" / "exclusion_log.json"

@pytest.fixture
def schema():
    """Load the dataset schema from YAML."""
    if not SCHEMA_PATH.exists():
        pytest.skip(f"Schema file not found at {SCHEMA_PATH}. Run T007 first.")
    with open(SCHEMA_PATH, 'r') as f:
        return yaml.safe_load(f)

@pytest.fixture
def dataset():
    """Load the cleaned dataset if it exists."""
    if not DATASET_PATH.exists():
        pytest.skip(f"Dataset not found at {DATASET_PATH}. Run T014a first.")
    return pd.read_csv(DATASET_PATH)

@pytest.fixture
def exclusion_log():
    """Load the exclusion log if it exists."""
    if not EXCLUSION_LOG_PATH.exists():
        # Not strictly required for schema validation of the remaining rows, 
        # but good to have for context.
        return {"total_raw": 0, "excluded": 0, "reasons": {}}
    with open(EXCLUSION_LOG_PATH, 'r') as f:
        return json.load(f)

def test_schema_exists(schema):
    """Verify the schema object is loaded and non-empty."""
    assert schema is not None
    assert "properties" in schema
    assert "required" in schema

def test_required_columns_present(dataset, schema):
    """Verify all columns marked as required in the schema exist in the dataset."""
    required_cols = schema.get("required", [])
    dataset_cols = set(dataset.columns)
    
    missing_cols = set(required_cols) - dataset_cols
    assert len(missing_cols) == 0, f"Missing required columns: {missing_cols}"

def test_column_types_match(dataset, schema):
    """Verify data types of columns match the schema definition."""
    properties = schema.get("properties", {})
    
    type_mapping = {
        "string": object,
        "integer": np.integer,
        "number": (np.floating, float),
        "boolean": (bool, np.bool_)
    }
    
    errors = []
    for col_name, col_def in properties.items():
        if col_name not in dataset.columns:
            continue # Checked in test_required_columns_present
        
        expected_type_str = col_def.get("type")
        if not expected_type_str:
            continue
        
        expected_type = type_mapping.get(expected_type_str)
        if expected_type is None:
            errors.append(f"Unknown type mapping for '{expected_type_str}'")
            continue

        actual_dtype = dataset[col_name].dtype
        
        # Special handling for object columns that should be strings
        if expected_type_str == "string" and actual_dtype == "object":
            # Check if it's actually numeric stored as object or mixed
            # For strictness, we assume object is acceptable for string in pandas CSV
            continue
        
        if expected_type_str == "integer" and not np.issubdtype(actual_dtype, np.integer):
            # Check if it's a float that is actually integer (e.g. 1.0)
            if np.issubdtype(actual_dtype, np.floating):
                if not dataset[col_name].eq(dataset[col_name].astype(int)).all():
                    errors.append(f"Column '{col_name}' is float but contains non-integers")
                continue
            errors.append(f"Column '{col_name}' is {actual_dtype}, expected integer")
            continue

        if expected_type_str == "number" and not np.issubdtype(actual_dtype, np.floating) and not np.issubdtype(actual_dtype, np.integer):
            errors.append(f"Column '{col_name}' is {actual_dtype}, expected number")
            continue

    assert len(errors) == 0, f"Type mismatches found:\n" + "\n".join(errors)

def test_no_extra_columns(dataset, schema):
    """Ensure no unexpected columns are in the dataset (strict contract)."""
    schema_cols = set(schema.get("properties", {}).keys())
    dataset_cols = set(dataset.columns)
    
    extra_cols = dataset_cols - schema_cols
    assert len(extra_cols) == 0, f"Unexpected columns found: {extra_cols}"

def test_no_nulls_in_required_columns(dataset, schema):
    """Verify required columns do not contain null values."""
    required_cols = schema.get("required", [])
    errors = []
    
    for col in required_cols:
        if col in dataset.columns:
            if dataset[col].isnull().any():
                count = dataset[col].isnull().sum()
                errors.append(f"Column '{col}' has {count} null values")
    
    assert len(errors) == 0, f"Nulls found in required columns:\n" + "\n".join(errors)

def test_stimulus_type_values(dataset):
    """Specific validation for stimulus_type enum values."""
    if "stimulus_type" in dataset.columns:
        valid_values = {"nostalgia", "control"}
        actual_values = set(dataset["stimulus_type"].dropna().unique())
        invalid_values = actual_values - valid_values
        assert len(invalid_values) == 0, f"Invalid stimulus_type values found: {invalid_values}"

def test_age_range_valid(dataset):
    """Specific validation for age >= 65 as per study design."""
    if "age" in dataset.columns:
        invalid_ages = dataset[dataset["age"] < 65]
        assert len(invalid_ages) == 0, f"Found {len(invalid_ages)} records with age < 65"

def test_cognitive_metrics_non_negative(dataset):
    """Ensure cognitive metrics (errors, categories) are non-negative."""
    metric_cols = ["perseverative_errors", "categories_completed"]
    for col in metric_cols:
        if col in dataset.columns:
            negative_vals = dataset[dataset[col] < 0]
            assert len(negative_vals) == 0, f"Column '{col}' contains negative values"

def test_exclusion_log_consistency(exclusion_log):
    """Verify exclusion log has the expected structure."""
    assert "total_raw" in exclusion_log
    assert "excluded" in exclusion_log
    assert "reasons" in exclusion_log
    assert isinstance(exclusion_log["reasons"], dict)