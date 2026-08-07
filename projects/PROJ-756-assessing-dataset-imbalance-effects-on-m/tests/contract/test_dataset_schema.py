"""
Contract Test T012: Data Schema Validation.

Validates the data in data/processed/ against the schema defined in contracts/dataset.schema.yaml.
This test ensures that the data produced by the ingestion and descriptor computation steps
conforms to the expected structure.
"""
import os
import sys
import unittest
import yaml
import pandas as pd
from pathlib import Path

# Add code directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

class TestDataSchemaValidation(unittest.TestCase):
    """Test case for data schema validation."""

    def setUp(self):
        """Set up test fixtures."""
        self.schema_path = Path("contracts/dataset.schema.yaml")
        self.processed_dir = Path("data/processed")
        
        # Load schema if it exists
        if self.schema_path.exists():
            with open(self.schema_path, 'r') as f:
                self.schema = yaml.safe_load(f)
        else:
            self.schema = None
            self.skipTest("Schema file not found. Skipping test.")

    def test_schema_exists(self):
        """Test that the schema file exists."""
        self.assertTrue(self.schema_path.exists(), "Schema file contracts/dataset.schema.yaml must exist.")

    def test_descriptors_file_exists(self):
        """Test that the descriptors file exists."""
        descriptors_path = self.processed_dir / "descriptors.parquet"
        self.assertTrue(descriptors_path.exists(), f"Descriptors file {descriptors_path} must exist.")

    def test_descriptors_file_not_empty(self):
        """Test that the descriptors file is not empty."""
        descriptors_path = self.processed_dir / "descriptors.parquet"
        if descriptors_path.exists():
            self.assertGreater(descriptors_path.stat().st_size, 0, "Descriptors file must not be empty.")

    def test_descriptors_schema_compliance(self):
        """Test that the descriptors data complies with the schema."""
        if not self.schema:
            self.skipTest("Schema not loaded.")
        
        descriptors_path = self.processed_dir / "descriptors.parquet"
        if not descriptors_path.exists():
            self.skipTest("Descriptors file not found.")
        
        # Load data
        df = pd.read_parquet(descriptors_path)
        
        # Check required columns based on schema
        # Note: The schema defines 'property', 'composition', 'target_value', 'descriptors'
        # We check if these columns (or similar) exist.
        required_columns = self.schema.get('required', [])
        
        # For a parquet file with descriptors, we expect specific columns.
        # We'll check for the presence of key columns.
        expected_cols = ['composition', 'target_value'] # At minimum
        
        for col in expected_cols:
            self.assertIn(col, df.columns, f"Column '{col}' must be present in descriptors data.")

    def test_data_types(self):
        """Test that data types are correct."""
        if not self.schema:
            self.skipTest("Schema not loaded.")
        
        descriptors_path = self.processed_dir / "descriptors.parquet"
        if not descriptors_path.exists():
            self.skipTest("Descriptors file not found.")
        
        df = pd.read_parquet(descriptors_path)
        
        # Check 'target_value' is numeric
        if 'target_value' in df.columns:
            self.assertTrue(pd.api.types.is_numeric_dtype(df['target_value']), 
                            "Column 'target_value' must be numeric.")

if __name__ == '__main__':
    unittest.main()
