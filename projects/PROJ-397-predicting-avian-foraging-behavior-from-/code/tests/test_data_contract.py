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
    
    # Validate types for numeric columns with constraints
    for col_def in expected_columns:
        col_name = col_def['name']
        if col_name in df.columns:
            col_type = col_def['type']
            if col_type == 'float':
                if not pd.api.types.is_numeric_dtype(df[col_name]):
                    raise ValueError(f"Column '{col_name}' should be numeric but is {df[col_name].dtype}")
                
                # Check constraints if defined
                constraints = col_def.get('constraints', {})
                if 'min' in constraints:
                    if df[col_name].min() < constraints['min']:
                        raise ValueError(f"Column '{col_name}' has values below minimum {constraints['min']}")
                if 'max' in constraints:
                    if df[col_name].max() > constraints['max']:
                        raise ValueError(f"Column '{col_name}' has values above maximum {constraints['max']}")
            
            elif col_type == 'string':
                if df[col_name].isna().any():
                    # Check if nullable is false
                    if not col_def.get('nullable', True):
                        raise ValueError(f"Column '{col_name}' contains null values but is marked as non-nullable")
    
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
        required_cols = ['species_id', 'foraging_guild', 'forest_prop', 'grassland_prop', 
                       'wetland_prop', 'urban_prop', 'water_prop', 'barren_prop', 'other_prop']
        
        for col in required_cols:
            self.assertIn(col, df.columns, 
                        f"Required column '{col}' is missing from the dataset")
        
        # Verify data types (basic checks)
        self.assertTrue(df['species_id'].dtype == 'object' or 
                      pd.api.types.is_numeric_dtype(df['species_id']),
                      "species_id should be string or numeric")
        
        self.assertTrue(df['foraging_guild'].dtype == 'object',
                      "foraging_guild should be string")
        
        # Verify land cover proportions are numeric
        land_cover_cols = ['forest_prop', 'grassland_prop', 'wetland_prop', 
                         'urban_prop', 'water_prop', 'barren_prop', 'other_prop']
        for col in land_cover_cols:
            self.assertTrue(pd.api.types.is_numeric_dtype(df[col]),
                          f"Column '{col}' should be numeric")
    
    def test_validate_schema(self):
        """
        Unit test for the validate_schema function in merge_and_buffer.py.
        
        This test specifically verifies that the validate_schema function
        raises a ValueError when required columns are missing.
        """
        from data.merge_and_buffer import validate_schema
        
        # Test 1: Valid DataFrame (should pass)
        valid_df = pd.DataFrame({
            'species_id': ['A', 'B'],
            'foraging_guild': ['G1', 'G2'],
            'forest_prop': [0.5, 0.6],
            'grassland_prop': [0.3, 0.2],
            'wetland_prop': [0.1, 0.1],
            'urban_prop': [0.0, 0.1],
            'water_prop': [0.0, 0.0],
            'barren_prop': [0.0, 0.0],
            'other_prop': [0.1, 0.0]
        })
        
        # Should not raise
        try:
            validate_schema(valid_df)
        except ValueError:
            self.fail("validate_schema raised ValueError on valid data")
        
        # Test 2: Missing 'species_id' (should raise)
        invalid_df_1 = valid_df.drop(columns=['species_id'])
        with self.assertRaises(ValueError) as context:
            validate_schema(invalid_df_1)
        self.assertIn('species_id', str(context.exception))
        
        # Test 3: Missing 'foraging_guild' (should raise)
        invalid_df_2 = valid_df.drop(columns=['foraging_guild'])
        with self.assertRaises(ValueError) as context:
            validate_schema(invalid_df_2)
        self.assertIn('foraging_guild', str(context.exception))
        
        # Test 4: Missing a land cover column (should raise)
        invalid_df_3 = valid_df.drop(columns=['forest_prop'])
        with self.assertRaises(ValueError) as context:
            validate_schema(invalid_df_3)
        self.assertIn('forest_prop', str(context.exception))

if __name__ == '__main__':
    unittest.main()