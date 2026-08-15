import os
import sys
import unittest
import yaml
import pandas as pd
from pathlib import Path

# Import from existing utils
from utils.config import get_project_root, get_data_dir
from data.merge_and_buffer import validate_schema

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
        if self.schema_path.exists():
            self.schema = load_schema(str(self.schema_path))
        else:
            self.schema = None
    
    def test_validate_schema(self):
        """
        Unit test for the validate_schema() function in merge_and_buffer.py.
        
        Verifies that the function raised ValueError if required columns
        are missing.
        """
        # Test 1: DataFrame with missing 'species_id'
        df_missing_species = pd.DataFrame({'foraging_guild': ['A'], 'lc_1': [0.5]})
        with self.assertRaises(ValueError) as context:
            validate_schema(df_missing_species)
        self.assertIn('species_id', str(context.exception))
        
        # Test 2: DataFrame with missing 'foraging_guild'
        df_missing_guild = pd.DataFrame({'species_id': ['S1'], 'lc_1': [0.5]})
        with self.assertRaises(ValueError) as context:
            validate_schema(df_missing_guild)
        self.assertIn('foraging_guild', str(context.exception))
        
        # Test 3: DataFrame with missing land cover columns
        df_missing_lc = pd.DataFrame({'species_id': ['S1'], 'foraging_guild': ['A']})
        with self.assertRaises(ValueError) as context:
            validate_schema(df_missing_lc)
        self.assertIn('land cover', str(context.exception).lower())
        
        # Test 4: Valid DataFrame should pass
        df_valid = pd.DataFrame({
            'species_id': ['S1'], 
            'foraging_guild': ['A'], 
            'lc_1': [0.5], 
            'lc_2': [0.5]
        })
        try:
            validate_schema(df_valid)
        except ValueError:
            self.fail("validate_schema() raised ValueError unexpectedly for valid DataFrame")

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
        
        # Validate schema compliance using the function from merge_and_buffer
        try:
            validate_schema(df)
        except ValueError as e:
            self.fail(f"Schema validation failed: {e}")
        
        # Additional specific checks for required columns mentioned in task
        required_cols = ['species_id', 'foraging_guild']
        for col in required_cols:
            self.assertIn(col, df.columns, 
                        f"Required column '{col}' is missing from the dataset")
        
        # Verify land cover columns exist
        lc_cols = [col for col in df.columns if col.startswith('lc_') or 'prop' in col.lower()]
        self.assertTrue(len(lc_cols) > 0, "No land cover proportion columns found")
        
        # Verify data types (basic checks)
        self.assertTrue(df['species_id'].dtype == 'object' or 
                      pd.api.types.is_numeric_dtype(df['species_id']),
                      "species_id should be string or numeric")
        
        self.assertTrue(df['foraging_guild'].dtype == 'object',
                      "foraging_guild should be string")

if __name__ == '__main__':
    unittest.main()