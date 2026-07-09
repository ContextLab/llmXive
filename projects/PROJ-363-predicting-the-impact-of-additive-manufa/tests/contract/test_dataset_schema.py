"""
Contract test: Validate data/processed/cleaned_316L.csv against contracts/dataset.schema.yaml.

This test ensures the preprocessed dataset adheres to the strict schema defined for
the 316L Stainless Steel porosity prediction project.
"""
import json
import os
import sys
import unittest
from pathlib import Path

import pandas as pd
import yaml
from jsonschema import validate, ValidationError

# Add project root to path for imports if running as script
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

DATA_PATH = PROJECT_ROOT / "data" / "processed" / "cleaned_316L.csv"
SCHEMA_PATH = PROJECT_ROOT / "contracts" / "dataset.schema.yaml"


class TestDatasetSchema(unittest.TestCase):
    """Contract tests for the cleaned 316L dataset."""

    @classmethod
    def setUpClass(cls):
        """Load the dataset and schema once before all tests."""
        if not DATA_PATH.exists():
            raise FileNotFoundError(
                f"Dataset not found at {DATA_PATH}. "
                "Please ensure T018 (save processed data) has been completed."
            )

        if not SCHEMA_PATH.exists():
            raise FileNotFoundError(
                f"Schema not found at {SCHEMA_PATH}. "
                "Please ensure T004 (create schema) has been completed."
            )

        # Load data
        cls.df = pd.read_csv(DATA_PATH)

        # Load schema
        with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
            cls.schema = yaml.safe_load(f)

    def test_schema_exists(self):
        """Verify the schema file is valid YAML and not empty."""
        self.assertIsNotNone(self.schema)
        self.assertIn("type", self.schema)
        self.assertEqual(self.schema["type"], "object")

    def test_required_columns_present(self):
        """Verify all required columns defined in the schema exist in the dataframe."""
        required_properties = self.schema.get("properties", {})
        required_fields = self.schema.get("required", [])

        missing_columns = []
        for field in required_fields:
            if field not in required_properties:
                # If it's required in the schema but not defined in properties, that's a schema issue
                # but we check against properties to be safe
                continue
            
            if field not in self.df.columns:
                missing_columns.append(field)

        self.assertEqual(
            len(missing_columns), 0,
            f"Missing required columns: {missing_columns}. "
            f"Expected: {required_fields}, Found: {list(self.df.columns)}"
        )

    def test_column_types(self):
        """Verify that columns match the expected types (numeric)."""
        properties = self.schema.get("properties", {})
        
        numeric_columns = []
        for col, definition in properties.items():
            if definition.get("type") == "number":
                numeric_columns.append(col)

        for col in numeric_columns:
            if col in self.df.columns:
                # Check if the column is numeric (int or float)
                if not pd.api.types.is_numeric_dtype(self.df[col]):
                    self.fail(
                        f"Column '{col}' is expected to be numeric (number) "
                        f"but is of type {self.df[col].dtype}"
                    )

    def test_no_null_values(self):
        """Verify there are no null values in the dataframe."""
        null_counts = self.df.isnull().sum()
        null_columns = null_counts[null_counts > 0]

        self.assertEqual(
            len(null_columns), 0,
            f"Dataset contains null values in columns: {null_columns.to_dict()}"
        )

    def test_schema_validation(self):
        """Run full JSON schema validation against the dataframe records."""
        # Convert dataframe to list of dicts for validation
        # Note: jsonschema validates a single instance. We validate a sample or the whole list
        # depending on schema definition. Usually schemas for datasets define the structure of a row.
        # If the schema defines an 'items' array, we validate the list.
        # Based on typical T004 generation, it likely defines a row object.
        
        # If the schema expects an array of objects:
        if self.schema.get("type") == "array" and "items" in self.schema:
            item_schema = self.schema["items"]
            for idx, row in self.df.iterrows():
                row_dict = row.to_dict()
                try:
                    validate(instance=row_dict, schema=item_schema)
                except ValidationError as e:
                    self.fail(
                        f"Row {idx} failed schema validation: {e.message}. "
                        f"Data: {row_dict}"
                    )
        # If the schema expects a single object (row structure):
        elif self.schema.get("type") == "object":
            for idx, row in self.df.iterrows():
                row_dict = row.to_dict()
                try:
                    validate(instance=row_dict, schema=self.schema)
                except ValidationError as e:
                    self.fail(
                        f"Row {idx} failed schema validation: {e.message}. "
                        f"Data: {row_dict}"
                    )
        else:
            # Fallback: assume it's a row schema
            for idx, row in self.df.iterrows():
                row_dict = row.to_dict()
                try:
                    validate(instance=row_dict, schema=self.schema)
                except ValidationError as e:
                    self.fail(
                        f"Row {idx} failed schema validation: {e.message}. "
                        f"Data: {row_dict}"
                    )


if __name__ == "__main__":
    unittest.main()