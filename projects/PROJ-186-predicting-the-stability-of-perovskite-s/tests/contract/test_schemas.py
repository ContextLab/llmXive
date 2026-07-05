"""
Contract tests for data schemas.

This module validates that the generated data artifacts conform to the
definitions in contracts/data-schema.yaml.
"""
import os
import csv
import yaml
from pathlib import Path
import pytest

# Ensure the test can find the project root for imports if run via pytest
# though this script primarily uses standard library + yaml
PROJECT_ROOT = Path(__file__).parent.parent.parent
CONTRACTS_DIR = PROJECT_ROOT / "contracts"
DATA_DIR = PROJECT_ROOT / "data"
PROCESSED_DIR = DATA_DIR / "processed"
SCHEMA_PATH = CONTRACTS_DIR / "data-schema.yaml"
FEATURES_PATH = PROCESSED_DIR / "features.csv"


def load_schema():
    """Load the data schema definition from YAML."""
    if not SCHEMA_PATH.exists():
        raise FileNotFoundError(f"Schema file not found: {SCHEMA_PATH}")
    with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def load_csv_headers(filepath):
    """Load headers from a CSV file."""
    if not filepath.exists():
        raise FileNotFoundError(f"Data file not found: {filepath}")
    with open(filepath, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        return list(reader.fieldnames)


def test_features_csv_schema_validation():
    """
    Contract test: Validate that data/processed/features.csv matches
    the schema defined in contracts/data-schema.yaml.
    
    Checks:
    1. File existence
    2. Schema file existence
    3. Required columns presence
    4. No unexpected columns (strict mode)
    5. Type validation for numeric columns (if defined)
    """
    # 1. Check file existence
    assert FEATURES_PATH.exists(), f"Expected features file not found at {FEATURES_PATH}. Run data pipeline first."
    
    schema = load_schema()
    
    # Ensure the schema defines the features CSV
    assert "features" in schema, "Schema must define a 'features' section"
    
    features_schema = schema["features"]
    required_columns = features_schema.get("required_columns", [])
    column_types = features_schema.get("column_types", {})
    
    # 2. Load actual headers
    actual_headers = load_csv_headers(FEATURES_PATH)
    
    # 3. Check required columns
    missing_columns = set(required_columns) - set(actual_headers)
    assert not missing_columns, f"Missing required columns in features.csv: {missing_columns}"
    
    # 4. Check for unexpected columns (strict contract)
    # If the schema defines 'allowed_columns', enforce it. Otherwise, just ensure required are present.
    if "allowed_columns" in features_schema:
        allowed = set(features_schema["allowed_columns"])
        actual_set = set(actual_headers)
        unexpected = actual_set - allowed
        assert not unexpected, f"Unexpected columns found in features.csv: {unexpected}"
    
    # 5. Validate types for a sample of rows
    # We check the first 10 rows to ensure numeric columns are parseable as float
    numeric_cols = [k for k, v in column_types.items() if v in ["float", "int", "number"]]
    
    with open(FEATURES_PATH, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        row_count = 0
        for row in reader:
            row_count += 1
            for col in numeric_cols:
                if col in row and row[col] != "":
                    try:
                        float(row[col])
                    except ValueError:
                        raise AssertionError(
                            f"Type validation failed: Column '{col}' contains non-numeric value "
                            f"'{row[col]}' in row {row_count}"
                        )
            
            # Stop after checking a few rows to keep test fast, 
            # unless we want to check all (might be slow for large datasets)
            if row_count >= 10:
                break
    
    # If we get here, the schema is valid
    assert True, "Schema validation passed"
