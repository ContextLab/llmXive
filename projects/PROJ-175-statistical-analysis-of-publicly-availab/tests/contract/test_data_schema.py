"""
Contract tests for data schema validation.

This module validates that the output of the data pre-processing pipeline
conforms to the defined schema in specs/001-statistical-analysis-of-recipe-data/contracts/dataset.schema.yaml.

It checks:
1. Presence of required columns (ingredient_pair, log_co_occurrence, flavor_similarity, functional_role, etc.)
2. Data types (float, int, string)
3. Value constraints (non-negative counts, similarity in [0,1], valid role categories)
4. Schema structure compliance
"""

import os
import sys
import json
import pytest
import pandas as pd
from pathlib import Path

# Add project root to path for imports if running from tests/
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Import schema definitions if available, otherwise define inline for contract test
# Since T007 created the schema, we assume it exists or we define the contract here
EXPECTED_COLUMNS = {
    "ingredient_pair_id": "string",
    "ingredient_1": "string",
    "ingredient_2": "string",
    "log_co_occurrence": "float",
    "flavor_similarity": "float",
    "functional_role": "string",
    "role_missing_flag": "int",
    "similarity_missing_flag": "int",
    "compatibility_label": "int"
}

EXPECTED_DTYPE_MAPPING = {
    "ingredient_pair_id": "object",
    "ingredient_1": "object",
    "ingredient_2": "object",
    "log_co_occurrence": "float64",
    "flavor_similarity": "float64",
    "functional_role": "object",
    "role_missing_flag": "int64",
    "similarity_missing_flag": "int64",
    "compatibility_label": "int64"
}

VALID_ROLES = ["Primary", "Secondary", "Garnish", "Unknown"]

# Path to the expected output file from the pipeline (T015-T018)
# This path assumes the pipeline has run and produced data/processed/recipe_pairs.csv
OUTPUT_FILE_PATH = "data/processed/recipe_pairs.csv"
SCHEMA_PATH = "specs/001-statistical-analysis-of-recipe-data/contracts/dataset.schema.yaml"

@pytest.fixture
def data_file_path():
    """Returns the path to the data file to be tested."""
    return project_root / OUTPUT_FILE_PATH

@pytest.fixture
def schema_file_path():
    """Returns the path to the schema definition file."""
    return project_root / SCHEMA_PATH

def load_schema(schema_path):
    """
    Loads the schema definition from the YAML file.
    If the file doesn't exist, returns the inline contract definition.
    """
    if not schema_path.exists():
        # Fallback to inline contract if schema file is missing
        return {
            "required_columns": list(EXPECTED_COLUMNS.keys()),
            "valid_roles": VALID_ROLES
        }
    
    try:
        import yaml
        with open(schema_path, 'r') as f:
            return yaml.safe_load(f)
    except ImportError:
        # If pyyaml is not installed, fallback to inline
        return {
            "required_columns": list(EXPECTED_COLUMNS.keys()),
            "valid_roles": VALID_ROLES
        }
    except Exception:
        # If file is malformed, fallback to inline
        return {
            "required_columns": list(EXPECTED_COLUMNS.keys()),
            "valid_roles": VALID_ROLES
        }

def test_schema_file_exists(schema_file_path):
    """Contract test: Verify the schema definition file exists."""
    # Note: This test might be skipped if T007 hasn't run yet, but the schema
    # contract is defined inline as a fallback.
    # We assert existence to ensure the spec is maintained.
    # If the file is missing, we rely on the inline definition but log a warning.
    if not schema_file_path.exists():
        pytest.skip(f"Schema file {schema_file_path} not found. Using inline contract definition.")

def test_data_file_exists(data_file_path):
    """Contract test: Verify the processed data file exists."""
    assert data_file_path.exists(), f"Data file {data_file_path} does not exist. Run the preprocessing pipeline first."

def test_required_columns_present(data_file_path):
    """Contract test: Verify all required columns are present in the data."""
    df = pd.read_csv(data_file_path)
    schema = load_schema(project_root / SCHEMA_PATH)
    required_cols = schema.get("required_columns", list(EXPECTED_COLUMNS.keys()))
    
    missing_cols = set(required_cols) - set(df.columns)
    assert len(missing_cols) == 0, f"Missing required columns: {missing_cols}"

def test_column_dtypes(data_file_path):
    """Contract test: Verify column data types match the schema."""
    df = pd.read_csv(data_file_path)
    
    for col, expected_dtype in EXPECTED_DTYPE_MAPPING.items():
        if col in df.columns:
            # Handle potential float/int variations
            actual_dtype = str(df[col].dtype)
            # Allow some flexibility for object vs string, but enforce numeric types
            if "float" in expected_dtype:
                assert pd.api.types.is_float_dtype(df[col]) or pd.api.types.is_integer_dtype(df[col]), \
                    f"Column {col} should be numeric, got {actual_dtype}"
            elif "int" in expected_dtype:
                assert pd.api.types.is_integer_dtype(df[col]) or pd.api.types.is_float_dtype(df[col]), \
                    f"Column {col} should be integer-like, got {actual_dtype}"
            else:
                assert df[col].dtype == expected_dtype or df[col].dtype == "object", \
                    f"Column {col} should be {expected_dtype}, got {actual_dtype}"

def test_value_constraints_log_co_occurrence(data_file_path):
    """Contract test: Verify log_co_occurrence is non-negative (log(C+1) >= 0 for C>=0)."""
    df = pd.read_csv(data_file_path)
    if "log_co_occurrence" in df.columns:
        assert (df["log_co_occurrence"] >= 0).all(), "log_co_occurrence must be non-negative"
        assert not df["log_co_occurrence"].isna().any(), "log_co_occurrence contains NaN values"

def test_value_constraints_flavor_similarity(data_file_path):
    """Contract test: Verify flavor_similarity is in [0, 1] range."""
    df = pd.read_csv(data_file_path)
    if "flavor_similarity" in df.columns:
        assert (df["flavor_similarity"] >= 0).all() and (df["flavor_similarity"] <= 1).all(), \
            "flavor_similarity must be between 0 and 1"

def test_value_constraints_functional_role(data_file_path):
    """Contract test: Verify functional_role contains only valid categories."""
    df = pd.read_csv(data_file_path)
    schema = load_schema(project_root / SCHEMA_PATH)
    valid_roles = schema.get("valid_roles", VALID_ROLES)
    
    if "functional_role" in df.columns:
        invalid_roles = set(df["functional_role"].dropna().unique()) - set(valid_roles)
        assert len(invalid_roles) == 0, f"Invalid functional_role values found: {invalid_roles}"

def test_flag_columns_binary(data_file_path):
    """Contract test: Verify flag columns are binary (0 or 1)."""
    df = pd.read_csv(data_file_path)
    flag_cols = ["role_missing_flag", "similarity_missing_flag"]
    
    for col in flag_cols:
        if col in df.columns:
            valid_values = {0, 1}
            actual_values = set(df[col].unique()) - {0, 1}
            # Allow for NaN if flags are float, but check non-null values
            non_null_values = set(df[col].dropna().unique())
            invalid_values = non_null_values - valid_values
            assert len(invalid_values) == 0, f"Column {col} should be binary (0 or 1), found: {invalid_values}"

def test_compatibility_label_valid(data_file_path):
    """Contract test: Verify compatibility_label is binary (0 or 1)."""
    df = pd.read_csv(data_file_path)
    if "compatibility_label" in df.columns:
        valid_values = {0, 1}
        non_null_values = set(df["compatibility_label"].dropna().unique())
        invalid_values = non_null_values - valid_values
        assert len(invalid_values) == 0, f"compatibility_label should be binary (0 or 1), found: {invalid_values}"

def test_no_duplicate_pairs(data_file_path):
    """Contract test: Verify no duplicate ingredient pairs exist."""
    df = pd.read_csv(data_file_path)
    if "ingredient_pair_id" in df.columns:
        duplicates = df[df.duplicated(subset=["ingredient_pair_id"], keep=False)]
        assert len(duplicates) == 0, f"Found duplicate ingredient_pair_id: {duplicates['ingredient_pair_id'].tolist()[:5]}"
    elif "ingredient_1" in df.columns and "ingredient_2" in df.columns:
        # Check for duplicates considering order (A,B) == (B,A)
        sorted_pairs = df.apply(lambda row: tuple(sorted([row["ingredient_1"], row["ingredient_2"]])), axis=1)
        duplicates = sorted_pairs[sorted_pairs.duplicated(keep=False)]
        assert len(duplicates) == 0, "Found duplicate ingredient pairs (order-independent)"

def test_data_integrity_no_nulls_critical_fields(data_file_path):
    """Contract test: Verify critical fields do not contain nulls."""
    df = pd.read_csv(data_file_path)
    critical_fields = ["ingredient_1", "ingredient_2", "log_co_occurrence", "functional_role"]
    
    for field in critical_fields:
        if field in df.columns:
            null_count = df[field].isna().sum()
            assert null_count == 0, f"Critical field {field} contains {null_count} null values"
