"""
Contract test for the metallic glass dataset schema.
Verifies that data/clean_data.csv matches contracts/dataset.schema.yaml.
"""
import json
import os
import unittest
from pathlib import Path

import pandas as pd
import yaml
from jsonschema import validate, ValidationError, Draft7Validator
from jsonschema.exceptions import best_match

# Add project root to path for imports if running as script
project_root = Path(__file__).resolve().parents[2]
data_path = project_root / "data" / "clean_data.csv"
schema_path = project_root / "contracts" / "dataset.schema.yaml"

class TestDatasetSchema(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        """Load the schema and data once for all tests."""
        if not schema_path.exists():
            raise FileNotFoundError(
                f"Schema file not found at {schema_path}. "
                "Ensure T006 and schema creation tasks are complete."
            )
        
        with open(schema_path, "r", encoding="utf-8") as f:
            cls.schema = yaml.safe_load(f)
        
        if not data_path.exists():
            raise FileNotFoundError(
                f"Data file not found at {data_path}. "
                "Ensure data pipeline (T012-T015) has been executed."
            )
        
        cls.df = pd.read_csv(data_path)

    def test_schema_structure(self):
        """Verify the schema itself is a valid JSON Schema Draft 7."""
        Draft7Validator.check_schema(self.schema)

    def test_required_columns(self):
        """Verify all required columns defined in schema are present in data."""
        required_cols = self.schema.get("required", [])
        actual_cols = set(self.df.columns)
        missing = set(required_cols) - actual_cols
        
        self.assertEqual(
            len(missing), 0,
            f"Missing required columns: {missing}. "
            f"Expected: {required_cols}, Found: {list(actual_cols)}"
        )

    def test_column_types(self):
        """Verify data types match the schema definitions."""
        properties = self.schema.get("properties", {})
        
        for col_name, col_schema in properties.items():
            if col_name not in self.df.columns:
                continue  # Handled by required check
            
            expected_type = col_schema.get("type")
            actual_dtype = self.df[col_name].dtype
            
            # Map JSON Schema types to pandas dtypes
            type_map = {
                "string": "object",
                "number": "float64",
                "integer": "int64",
                "boolean": "bool",
            }
            
            expected_pandas_type = type_map.get(expected_type)
            
            if expected_pandas_type:
                # Allow numeric columns to be int or float
                if expected_type == "number":
                    self.assertTrue(
                        pd.api.types.is_numeric_dtype(actual_dtype),
                        f"Column '{col_name}' should be numeric (float), got {actual_dtype}"
                    )
                elif expected_type == "integer":
                    self.assertTrue(
                        pd.api.types.is_integer_dtype(actual_dtype),
                        f"Column '{col_name}' should be integer, got {actual_dtype}"
                    )
                elif expected_type == "string":
                    # Pandas object can contain strings
                    self.assertTrue(
                        actual_dtype == "object" or pd.api.types.is_string_dtype(actual_dtype),
                        f"Column '{col_name}' should be string, got {actual_dtype}"
                    )

    def test_no_null_values(self):
        """Verify no null values exist in the dataset (based on schema 'nullable: false')."""
        properties = self.schema.get("properties", {})
        
        for col_name, col_schema in properties.items():
            if col_schema.get("nullable", True) is False:
                null_count = self.df[col_name].isnull().sum()
                self.assertEqual(
                    null_count, 0,
                    f"Column '{col_name}' must not contain null values. Found {null_count}."
                )

    def test_json_schema_validation(self):
        """Validate the entire dataset against the JSON schema record-by-record."""
        # Convert dataframe to list of dicts
        records = self.df.to_dict(orient="records")
        
        # Validate each record
        for i, record in enumerate(records):
            try:
                validate(instance=record, schema=self.schema)
            except ValidationError as e:
                self.fail(
                    f"Validation failed at row {i}: {e.message}. "
                    f"Instance: {record}"
                )

if __name__ == "__main__":
    unittest.main()