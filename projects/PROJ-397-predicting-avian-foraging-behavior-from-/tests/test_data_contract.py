import os
import sys
import unittest
import yaml
import pandas as pd
from pathlib import Path

# Import from existing utils
from utils.config import get_project_root, get_data_dir

def load_schema(schema_path: str = None):
    """Load the dataset schema from YAML."""
    if schema_path is None:
        project_root = get_project_root()
        schema_path = project_root / "contracts" / "dataset.schema.yaml"
    
    if not Path(schema_path).exists():
        raise FileNotFoundError(f"Schema file not found at {schema_path}")
    
    with open(schema_path, 'r') as f:
        return yaml.safe_load(f)

def validate_schema_compliance(df, schema):
    """
    Validate that a DataFrame matches the expected schema.
    
    Args:
        df: pandas DataFrame to validate
        schema: Dict containing schema definition (expected columns, types)
    
    Returns:
        bool: True if compliant, False otherwise
    
    Raises:
        ValueError: If schema validation fails
    """
    expected_columns = schema.get('columns', [])
    
    if not expected_columns:
        raise ValueError("Schema definition contains no expected columns")
    
    missing_columns = [col for col in expected_columns if col not in df.columns]
    
    if missing_columns:
        raise ValueError(f"DataFrame missing required columns: {missing_columns}")
    
    return True

class TestDataContract(unittest.TestCase):
    """
    Test suite for data contract compliance.
    
    This test validates that merged_observations.csv matches the schema
    defined in contracts/dataset.schema.yaml, specifically checking for
    species_id, foraging_guild, and land_cover_proportions columns.
    """
    
    def setUp(self):
        """Set up test fixtures."""
        self.project_root = get_project_root()
        self.schema_path = self.project_root / "contracts" / "dataset.schema.yaml"
        self.data_path = self.project_root / "data" / "processed" / "merged_observations.csv"
        
        # Load schema
        self.schema = load_schema(str(self.schema_path))
    
    def test_schema_compliance(self):
        """
        Test that the merged observations CSV matches the expected schema.
        
        Validates that the output of T013 (merge_and_buffer.py) contains
        the required columns: species_id, foraging_guild, and 
        land_cover_proportions as defined in the contract.
        """
        # Verify the data file exists
        if not self.data_path.exists():
            self.fail(f"Data file not found at {self.data_path}. "
                     "Ensure T013 (merge_and_buffer.py) has been executed.")
        
        # Load the CSV
        try:
            df = pd.read_csv(self.data_path)
        except Exception as e:
            self.fail(f"Failed to load {self.data_path}: {e}")
        
        # Validate schema compliance
        try:
            validate_schema_compliance(df, self.schema)
        except ValueError as e:
            self.fail(f"Schema validation failed: {e}")
        
        # Additional specific checks for required columns mentioned in task
        required_cols = ['species_id', 'foraging_guild', 'land_cover_proportions']
        for col in required_cols:
            self.assertIn(col, df.columns, 
                        f"Required column '{col}' is missing from the dataset")
        
        # Verify data types (basic checks)
        self.assertTrue(df['species_id'].dtype == 'object' or 
                      pd.api.types.is_numeric_dtype(df['species_id']),
                      "species_id should be string or numeric")
        
        self.assertTrue(df['foraging_guild'].dtype == 'object',
                      "foraging_guild should be string")
        
        # land_cover_proportions might be stored as stringified JSON or dict
        # depending on how it was saved, but it must exist
        self.assertIn('land_cover_proportions', df.columns,
                    "land_cover_proportions column is missing")

if __name__ == '__main__':
    unittest.main()