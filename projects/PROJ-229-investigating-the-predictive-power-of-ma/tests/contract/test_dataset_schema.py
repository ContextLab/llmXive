"""
Contract test for dataset schema (US1).

This test verifies that the processed dataset produced by the data pipeline
adheres to the schema defined in specs/001-phase-change-predictive-power/contracts/dataset.schema.yaml.

It checks:
1. Presence of required columns.
2. Correct data types for each column.
3. Absence of null values in critical columns (melting_point, latent_heat, etc.).
4. Valid value ranges where applicable.
"""

import os
import sys
import unittest
import yaml
from pathlib import Path
import pandas as pd
import numpy as np

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Import schema loader utility if it exists, otherwise load directly
# We assume the schema file exists as per T007
SCHEMA_PATH = project_root / "specs" / "001-phase-change-predictive-power" / "contracts" / "dataset.schema.yaml"
DATA_PATH = project_root / "data" / "processed" / "materials_project_processed.csv"

def load_schema(schema_path: Path) -> dict:
    """Load the dataset schema definition from YAML."""
    if not schema_path.exists():
        raise FileNotFoundError(f"Schema file not found at {schema_path}")
    with open(schema_path, 'r') as f:
        return yaml.safe_load(f)

def load_processed_data(data_path: Path) -> pd.DataFrame:
    """Load the processed dataset for validation."""
    if not data_path.exists():
        raise FileNotFoundError(f"Processed data file not found at {data_path}")
    return pd.read_csv(data_path)

class TestDatasetSchema(unittest.TestCase):
    """Contract tests for the Materials Project dataset schema."""

    @classmethod
    def setUpClass(cls):
        """Load schema and data once for all tests."""
        try:
            cls.schema = load_schema(SCHEMA_PATH)
            cls.data = load_processed_data(DATA_PATH)
        except FileNotFoundError as e:
            # If data or schema is missing, we can't run the test.
            # This is expected if the pipeline hasn't run yet (T015).
            # However, for the contract test to be valid, the schema must exist.
            # We will assert existence in the test itself to provide a clear error.
            cls.schema = None
            cls.data = None
            cls.error_msg = str(e)

    def test_schema_file_exists(self):
        """Verify that the schema definition file exists."""
        self.assertTrue(SCHEMA_PATH.exists(), f"Schema file missing: {SCHEMA_PATH}")

    def test_data_file_exists(self):
        """Verify that the processed data file exists."""
        self.assertTrue(DATA_PATH.exists(), f"Processed data file missing: {DATA_PATH}")

    def test_required_columns_present(self):
        """Verify all columns defined in the schema are present in the data."""
        if self.schema is None:
            self.fail(self.error_msg)

        schema_columns = set(self.schema.get("required_columns", []))
        data_columns = set(self.data.columns)

        missing_columns = schema_columns - data_columns
        self.assertEqual(
            len(missing_columns), 0,
            f"Missing required columns: {missing_columns}. "
            f"Available: {list(self.data.columns)}"
        )

    def test_column_data_types(self):
        """Verify data types match the schema definition."""
        if self.schema is None:
            self.fail(self.error_msg)

        type_mapping = {
            "int": (int, np.integer),
            "float": (float, np.floating),
            "string": (str,),
            "boolean": (bool, np.bool_)
        }

        for col_def in self.schema.get("columns", []):
            col_name = col_def.get("name")
            expected_type = col_def.get("type")

            if col_name not in self.data.columns:
                continue  # Already checked in required_columns

            if expected_type not in type_mapping:
                continue  # Skip unknown types

            expected_python_type = type_mapping[expected_type]
            actual_dtype = self.data[col_name].dtype

            # Check if the actual dtype is compatible with the expected python type
            # Note: pandas might use float64 for ints, so we check the underlying numpy type
            if not isinstance(actual_dtype.type(0), expected_python_type):
                # Special case: pandas nullable integers or object columns that contain mixed types
                # We allow object columns if the schema expects string, but verify content
                if expected_type == "string" and actual_dtype == object:
                    continue
                
                # Check if it's a numeric type that can be cast
                if expected_type in ("int", "float"):
                    try:
                        self.data[col_name].astype(float)
                        continue
                    except (ValueError, TypeError):
                        pass

                self.fail(
                    f"Column '{col_name}' has dtype {actual_dtype}, "
                    f"expected {expected_type} ({expected_python_type})."
                )

    def test_no_nulls_in_required_columns(self):
        """Verify critical columns have no null values."""
        if self.schema is None:
            self.fail(self.error_msg)

        required_cols = self.schema.get("required_columns", [])
        # Identify which required columns should not be null based on schema constraints
        # Usually, the schema defines 'nullable: false' for critical fields
        non_nullable_cols = [
            col["name"] for col in self.schema.get("columns", [])
            if not col.get("nullable", True)
        ]

        # If no explicit non-nullable list, assume all required columns are non-nullable
        if not non_nullable_cols:
            non_nullable_cols = required_cols

        for col_name in non_nullable_cols:
            if col_name not in self.data.columns:
                continue

            null_count = self.data[col_name].isnull().sum()
            self.assertEqual(
                null_count, 0,
                f"Column '{col_name}' contains {null_count} null values."
            )

    def test_value_ranges(self):
        """Verify numeric columns are within expected ranges defined in schema."""
        if self.schema is None:
            self.fail(self.error_msg)

        for col_def in self.schema.get("columns", []):
            col_name = col_def.get("name")
            if col_name not in self.data.columns:
                continue

            min_val = col_def.get("min")
            max_val = col_def.get("max")

            if min_val is not None:
                min_actual = self.data[col_name].min()
                self.assertGreaterEqual(
                    min_actual, min_val,
                    f"Column '{col_name}' has minimum {min_actual}, expected >= {min_val}"
                )

            if max_val is not None:
                max_actual = self.data[col_name].max()
                self.assertLessEqual(
                    max_actual, max_val,
                    f"Column '{col_name}' has maximum {max_actual}, expected <= {max_val}"
                )

    def test_record_count_minimum(self):
        """Verify the dataset meets the minimum record count requirement."""
        if self.schema is None:
            self.fail(self.error_msg)

        min_records = self.schema.get("min_records", 0)
        actual_records = len(self.data)

        self.assertGreaterEqual(
            actual_records, min_records,
            f"Dataset has {actual_records} records, minimum required is {min_records}"
        )

if __name__ == "__main__":
    unittest.main()