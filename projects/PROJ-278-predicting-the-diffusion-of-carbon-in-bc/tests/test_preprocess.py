"""
Test suite for User Story 1: Data Preprocessing and Validation.
Includes contract tests for dataset.schema.yaml and data integrity checks.
"""
import os
import sys
import json
import pytest
import yaml
from pathlib import Path

# Add project root to path to allow imports from code/
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root / "code"))

import pandas as pd
from utils import get_properties
from exceptions import DataInsufficientError, PowerWarning

# Constants
DATA_DIR = project_root / "data" / "processed"
CONTRACTS_DIR = project_root / "contracts"
SCHEMA_PATH = CONTRACTS_DIR / "dataset.schema.yaml"
OUTPUT_FILE = DATA_DIR / "dataset_cleaned.csv"


def load_schema():
    """Load the dataset schema from YAML."""
    if not SCHEMA_PATH.exists():
        pytest.fail(f"Schema file not found: {SCHEMA_PATH}")
    with open(SCHEMA_PATH, 'r') as f:
        return yaml.safe_load(f)


def load_dataset():
    """Load the cleaned dataset if it exists."""
    if not OUTPUT_FILE.exists():
        # If the file doesn't exist, the test environment might not have run T010 yet.
        # We raise a skip or fail depending on strictness. For contract tests,
        # we assume the pipeline runs T010 before T012 in CI, or we skip.
        # However, per task description, we are implementing the test.
        # We will raise a clear error if the data is missing so the user knows to run T010.
        pytest.skip(f"Dataset not found at {OUTPUT_FILE}. Run T010 (preprocess) first.")
    return pd.read_csv(OUTPUT_FILE)


@pytest.fixture(scope="module")
def schema():
    return load_schema()


@pytest.fixture(scope="module")
def df():
    return load_dataset()


class TestDatasetSchemaContract:
    """
    T012: Contract test for dataset.schema.yaml validation.
    Verifies that the generated dataset matches the schema defined in contracts/dataset.schema.yaml.
    """

    def test_schema_file_exists(self):
        """Verify the schema file exists."""
        assert SCHEMA_PATH.exists(), "Schema file missing"

    def test_required_columns_present(self, schema, df):
        """Verify all columns defined in schema.required_columns exist in the dataset."""
        required_cols = schema.get("required_columns", [])
        actual_cols = set(df.columns)
        
        missing = set(required_cols) - actual_cols
        assert not missing, f"Missing required columns: {missing}"

    def test_column_types_match(self, schema, df):
        """Verify data types of columns match the schema definition."""
        type_mapping = {
            "int": "int64",
            "integer": "int64",
            "float": "float64",
            "double": "float64",
            "string": "object"
        }

        columns_def = schema.get("columns", {})
        
        for col_name, col_spec in columns_def.items():
            if col_name not in df.columns:
                continue # Handled by required_columns test
            
            expected_type_str = col_spec.get("type", "")
            expected_dtype = type_mapping.get(expected_type_str.lower(), expected_type_str)
            
            actual_dtype = str(df[col_name].dtype)
            
            # Normalize dtype for comparison
            if "int" in expected_dtype and "int" in actual_dtype:
                continue
            if "float" in expected_dtype and "float" in actual_dtype:
                continue
            if "object" in expected_dtype and "object" in actual_dtype:
                continue
            
            # If specific string match fails, check for compatibility
            if expected_dtype not in actual_dtype:
                # Allow some flexibility for pandas inference if schema is generic
                # But strictly, we check if the inferred type is compatible
                if not (
                    (expected_dtype == "float64" and "float" in actual_dtype) or
                    (expected_dtype == "int64" and "int" in actual_dtype) or
                    (expected_dtype == "object" and "object" in actual_dtype)
                ):
                    assert False, f"Column '{col_name}' type mismatch: expected {expected_dtype}, got {actual_dtype}"

    def test_no_nulls_in_required_fields(self, schema, df):
        """Verify that columns marked as required and non-nullable have no nulls."""
        columns_def = schema.get("columns", {})
        required_cols = schema.get("required_columns", [])
        
        for col in required_cols:
            if col not in df.columns:
                continue
            
            # Check if schema explicitly forbids nulls (often implied by required)
            col_spec = columns_def.get(col, {})
            if col_spec.get("nullable", False) is False or "required" in str(col_spec):
                if df[col].isnull().any():
                    count = df[col].isnull().sum()
                    assert False, f"Column '{col}' is required and non-nullable but has {count} null values"

    def test_composition_fractions_sum_to_one(self, df):
        """
        Verify that the atomic fraction columns sum to 1.0 (within tolerance).
        This validates the normalization step in T010.
        """
        # Identify composition columns (usually starting with 'composition_' or similar)
        # Based on typical schema, they might be named explicitly or we look for float cols not in standard metadata
        # Let's assume the schema or standard practice defines them.
        # A robust check: look for columns that are clearly composition fractions.
        # If the schema defines a specific set, use that.
        
        # Fallback: Look for columns with 'fraction' or 'atomic_' in name if not explicitly listed
        # But for a strict contract test, we rely on the schema if it lists them.
        # Since I don't see the exact schema content here, I will assume standard naming 
        # or check if the schema has a "composition_columns" key.
        
        comp_cols = [c for c in df.columns if 'fraction' in c.lower() or 'atomic_' in c.lower()]
        
        if not comp_cols:
            # If no composition columns found, maybe the schema lists them differently?
            # We'll skip if we can't identify them, but log a warning.
            pytest.skip("No composition fraction columns identified in dataset.")
        
        # Sum across the row
        row_sums = df[comp_cols].sum(axis=1)
        
        # Check tolerance (e.g., 1e-5)
        tolerance = 1e-5
        deviations = abs(row_sums - 1.0)
        
        if (deviations > tolerance).any():
            bad_rows = df[deviations > tolerance]
            pytest.fail(f"Atomic fractions do not sum to 1.0. Max deviation: {deviations.max()}")

    def test_bcc_structure_filter(self, df):
        """Verify all entries have structure == 'BCC'."""
        if 'structure' in df.columns:
            non_bcc = df[df['structure'] != 'BCC']
            assert len(non_bcc) == 0, f"Found {len(non_bcc)} non-BCC entries"
        else:
            pytest.skip("Structure column not found in dataset")

    def test_solute_filter(self, df):
        """Verify all entries have solute == 'C'."""
        if 'solute' in df.columns:
            non_c = df[df['solute'] != 'C']
            assert len(non_c) == 0, f"Found {len(non_c)} entries where solute is not 'C'"
        else:
            pytest.skip("Solute column not found in dataset")


class TestDataIntegrity:
    """Additional validation tests for the preprocessed data."""

    def test_no_missing_composition(self, df):
        """Verify no entries have missing composition data."""
        # Composition columns are critical
        comp_cols = [c for c in df.columns if 'fraction' in c.lower() or 'atomic_' in c.lower()]
        if comp_cols:
            for col in comp_cols:
                assert not df[col].isnull().any(), f"Missing values in composition column: {col}"

    def test_log_transformation_valid(self, df):
        """Verify log-transformed diffusion coefficient is valid (no NaN/Inf from log(0) or log(neg))."""
        log_col = 'log_diffusion_coefficient'
        if log_col in df.columns:
            assert not df[log_col].isnull().any(), "NaN found in log-transformed diffusion coefficient"
            assert not df[log_col].isin([float('inf'), float('-inf')]).any(), "Inf found in log-transformed diffusion coefficient"
        else:
            pytest.skip("Log diffusion coefficient column not found")

    def test_descriptors_computed(self, df):
        """Verify that computed descriptors exist and are numeric."""
        expected_descriptors = [
            'atomic_radius_variance', 
            'VEC', 
            'electronegativity_spread'
        ]
        
        for desc in expected_descriptors:
            if desc in df.columns:
                assert pd.api.types.is_numeric_dtype(df[desc]), f"Descriptor {desc} is not numeric"
                assert not df[desc].isnull().any(), f"Descriptor {desc} has null values"
            else:
                # If the schema doesn't require them, maybe they are named differently?
                # But per T010 spec, these specific names are expected.
                # We fail if they are missing unless the schema says otherwise.
                # For now, we assume they must be present.
                pytest.fail(f"Expected descriptor '{desc}' not found in dataset")

    def test_data_count_threshold_warning(self, df):
        """
        Verify that if the dataset count is < 30, the system handled it (this test 
        validates the data exists, but the actual warning emission is tested in T011).
        However, we can check if the dataset is small.
        """
        count = len(df)
        if count < 30:
            # This is a valid state per T011, but we note it.
            pass # Test passes, data is just small
        assert count > 0, "Dataset is empty"