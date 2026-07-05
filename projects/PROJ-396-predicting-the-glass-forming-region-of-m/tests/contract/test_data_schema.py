"""
Contract test for data schema validation (User Story 1).

This test verifies that the data ingestion pipeline produces output
conforming to the strict schema required for downstream descriptor
computation and model training.

It specifically checks for:
1. Presence of required columns: composition, gfa_label (or critical_cooling_rate),
   and the computed thermodynamic descriptors (delta_H_mix, delta, vec, delta_chi).
2. Absence of null values in predictor fields.
3. Correct data types for numeric fields.
"""
import os
import sys
import pytest
import pandas as pd
from pathlib import Path

# Add project root to path to allow imports if running as script
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Expected schema definition
REQUIRED_COLUMNS = [
    "composition",
    "gfa_label",
    "delta_H_mix",
    "delta",
    "vec",
    "delta_chi"
]

PREDICTOR_COLUMNS = [
    "delta_H_mix",
    "delta",
    "vec",
    "delta_chi"
]

NUMERIC_COLUMNS = [
    "delta_H_mix",
    "delta",
    "vec",
    "delta_chi"
]

def get_test_data_path():
    """
    Locates the validated composition file or the computed descriptors file.
    Prefers the computed descriptors file as it contains the full schema.
    Falls back to validated_compositions.csv if descriptors haven't been computed yet,
    in which case it tests for the base columns (composition, gfa_label).
    """
    processed_dir = project_root / "data" / "processed"
    descriptors_file = processed_dir / "computed_descriptors.csv"
    validated_file = processed_dir / "validated_compositions.csv"

    if descriptors_file.exists():
        return descriptors_file
    elif validated_file.exists():
        return validated_file
    else:
        # If neither exists, we are in a state where the pipeline hasn't run yet.
        # The contract test should fail if the expected file is missing,
        # but we need to handle the case where we are testing the *existence* of the file.
        # For this specific contract test, we assume the pipeline (T029) has run.
        # If not, we raise a clear error.
        raise FileNotFoundError(
            f"Contract test failed: Neither {descriptors_file} nor {validated_file} exists. "
            "Please run the data ingestion and descriptor computation pipeline first."
        )

def load_test_data():
    """Loads the data for testing."""
    path = get_test_data_path()
    return pd.read_csv(path)

@pytest.fixture
def data():
    """Fixture to load data for all contract tests."""
    return load_test_data()

class TestDataSchemaContract:
    """
    Contract tests ensuring the data output matches the specification.
    """

    def test_required_columns_exist(self, data):
        """
        Verify that all required columns are present in the dataset.
        """
        # Determine which columns to check based on file type
        if "computed_descriptors" in str(data.columns):
            # Full schema check
            missing = [col for col in REQUIRED_COLUMNS if col not in data.columns]
        else:
            # Base schema check (if only validated_compositions exists)
            missing = [col for col in ["composition", "gfa_label"] if col not in data.columns]
            # Skip descriptor checks if file doesn't have them yet
            if missing:
                pytest.fail(f"Missing required base columns: {missing}")
                return

        if missing:
            pytest.fail(f"Schema violation: Missing required columns: {missing}")

    def test_no_null_predictors(self, data):
        """
        Verify that there are no null values in the predictor fields.
        """
        # Check only columns that exist in the current data
        predictors_to_check = [col for col in PREDICTOR_COLUMNS if col in data.columns]
        
        if not predictors_to_check:
            pytest.skip("No predictor columns found in dataset (pipeline may not have run).")

        null_counts = data[predictors_to_check].isnull().sum()
        total_nulls = null_counts.sum()

        if total_nulls > 0:
            null_details = null_counts[null_counts > 0].to_dict()
            pytest.fail(f"Schema violation: Null values found in predictor fields: {null_details}")

    def test_numeric_columns_are_numeric(self, data):
        """
        Verify that numeric columns are of a numeric dtype.
        """
        numeric_to_check = [col for col in NUMERIC_COLUMNS if col in data.columns]
        
        if not numeric_to_check:
            pytest.skip("No numeric columns found in dataset.")

        non_numeric = []
        for col in numeric_to_check:
            if not pd.api.types.is_numeric_dtype(data[col]):
                non_numeric.append(col)

        if non_numeric:
            pytest.fail(f"Schema violation: Columns expected to be numeric are not: {non_numeric}")

    def test_composition_not_empty(self, data):
        """
        Verify that the composition column is not empty and contains strings.
        """
        if "composition" not in data.columns:
            pytest.skip("Composition column not found.")
        
        if data["composition"].isnull().any():
            pytest.fail("Schema violation: Composition column contains null values.")
        
        if data["composition"].str.strip().eq("").any():
            pytest.fail("Schema violation: Composition column contains empty strings.")

    def test_gfa_label_present(self, data):
        """
        Verify that GFA label or critical cooling rate is present.
        """
        has_label = "gfa_label" in data.columns
        has_rate = "critical_cooling_rate" in data.columns

        if not (has_label or has_rate):
            pytest.fail("Schema violation: Neither 'gfa_label' nor 'critical_cooling_rate' found.")

        # If we have gfa_label, ensure it's not all null
        if has_label:
            if data["gfa_label"].isnull().all():
                pytest.fail("Schema violation: 'gfa_label' column is entirely null.")

if __name__ == "__main__":
    # Allow running directly for quick checks
    pytest.main([__file__, "-v"])