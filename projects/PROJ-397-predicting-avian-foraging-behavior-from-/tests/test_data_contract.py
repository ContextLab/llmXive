import os
import sys
import unittest
import yaml
import pandas as pd
from pathlib import Path

# Add project root to path to allow imports from utils, data, etc.
PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from utils.config import get_data_dir, get_metadata_file

def load_schema(schema_path=None):
    """
    Load the dataset schema from the contracts directory.
    Defaults to contracts/dataset.schema.yaml relative to project root.
    """
    if schema_path is None:
        schema_path = PROJECT_ROOT / "contracts" / "dataset.schema.yaml"
    
    if not schema_path.exists():
        raise FileNotFoundError(f"Schema file not found at {schema_path}")
    
    with open(schema_path, 'r') as f:
        schema = yaml.safe_load(f)
    return schema

def validate_schema_compliance(df, schema):
    """
    Validates that a DataFrame conforms to the provided schema.
    
    Args:
        df (pd.DataFrame): The data to validate.
        schema (dict): The schema definition.
        
    Returns:
        tuple: (is_valid, list of errors)
    """
    errors = []
    
    # Check required columns
    required_columns = schema.get('required_columns', [])
    actual_columns = set(df.columns)
    
    for col in required_columns:
        if col not in actual_columns:
            errors.append(f"Missing required column: {col}")
    
    # Check specific column types if defined
    column_types = schema.get('column_types', {})
    for col, expected_type in column_types.items():
        if col in actual_columns:
            if expected_type == 'string' and not pd.api.types.is_string_dtype(df[col]):
                # Allow object dtype for strings
                if not pd.api.types.is_object_dtype(df[col]) and not pd.api.types.is_string_dtype(df[col]):
                    errors.append(f"Column {col} should be string type, got {df[col].dtype}")
            elif expected_type == 'float' and not pd.api.types.is_float_dtype(df[col]):
                errors.append(f"Column {col} should be float type, got {df[col].dtype}")
            elif expected_type == 'int' and not pd.api.types.is_integer_dtype(df[col]):
                errors.append(f"Column {col} should be int type, got {df[col].dtype}")
    
    # Check land cover proportions sum to 1.0 (within tolerance)
    # Identify land cover proportion columns (ending with '_prop_100m')
    lc_cols = [c for c in actual_columns if c.endswith('_prop_100m')]
    if lc_cols:
        sum_cols = df[lc_cols].sum(axis=1)
        # Allow small floating point errors
        if not ((sum_cols - 1.0).abs() < 0.01).all():
            errors.append(f"Land cover proportions do not sum to 1.0 for some rows")
    
    return len(errors) == 0, errors

class TestDataContract(unittest.TestCase):
    """
    Test suite for validating data contracts against schema.
    Specifically tests merged_observations.csv against dataset.schema.yaml
    """

    def setUp(self):
        """Set up test fixtures."""
        self.schema_path = PROJECT_ROOT / "contracts" / "dataset.schema.yaml"
        self.data_path = get_data_dir() / "processed" / "merged_observations.csv"
        
        # Ensure directories exist
        (get_data_dir() / "processed").mkdir(parents=True, exist_ok=True)
        (PROJECT_ROOT / "contracts").mkdir(parents=True, exist_ok=True)
        
        # Create default schema if it doesn't exist
        if not self.schema_path.exists():
            default_schema = {
                'name': 'merged_observations',
                'description': 'Merged eBird observations with land cover data',
                'required_columns': [
                    'species_id', 
                    'foraging_guild',
                    'forest_prop_100m',
                    'grassland_prop_100m',
                    'wetland_prop_100m',
                    'urban_prop_100m',
                    'other_prop_100m'
                ],
                'column_types': {
                    'species_id': 'string',
                    'foraging_guild': 'string',
                    'forest_prop_100m': 'float',
                    'grassland_prop_100m': 'float',
                    'wetland_prop_100m': 'float',
                    'urban_prop_100m': 'float',
                    'other_prop_100m': 'float'
                }
            }
            with open(self.schema_path, 'w') as f:
                yaml.dump(default_schema, f)

    def test_schema_compliance(self):
        """
        Test that merged_observations.csv conforms to dataset.schema.yaml.
        
        This test verifies:
        1. All required columns are present
        2. Column types match the schema
        3. Land cover proportions sum to 1.0
        """
        # Check if the merged observations file exists
        if not self.data_path.exists():
            self.skipTest(f"Data file not found: {self.data_path}. "
                        "Run data/write_merged_observations.py first.")
        
        # Load the schema
        schema = load_schema(self.schema_path)
        
        # Load the data
        df = pd.read_csv(self.data_path)
        
        # Validate against schema
        is_valid, errors = validate_schema_compliance(df, schema)
        
        # Assert compliance
        self.assertTrue(is_valid, f"Schema validation failed with errors: {errors}")
        
        # Additional specific checks for T010 requirements
        # Must have species_id and foraging_guild
        self.assertIn('species_id', df.columns, "Missing 'species_id' column")
        self.assertIn('foraging_guild', df.columns, "Missing 'foraging_guild' column")
        
        # Must have all 100m buffer land cover proportion columns
        required_lc_cols = [
            'forest_prop_100m',
            'grassland_prop_100m',
            'wetland_prop_100m',
            'urban_prop_100m',
            'other_prop_100m'
        ]
        for col in required_lc_cols:
            self.assertIn(col, df.columns, f"Missing land cover column: {col}")

    def test_empty_dataframe(self):
        """Test that an empty DataFrame fails validation appropriately."""
        schema = load_schema(self.schema_path)
        empty_df = pd.DataFrame()
        
        is_valid, errors = validate_schema_compliance(empty_df, schema)
        
        self.assertFalse(is_valid, "Empty DataFrame should fail schema validation")
        self.assertGreater(len(errors), 0, "Should have validation errors for empty DataFrame")

    def test_partial_columns(self):
        """Test that a DataFrame with missing required columns fails validation."""
        schema = load_schema(self.schema_path)
        
        # Create a DataFrame with only some required columns
        partial_df = pd.DataFrame({
            'species_id': ['species1', 'species2'],
            'forest_prop_100m': [0.5, 0.6]
            # Missing foraging_guild and other land cover columns
        })
        
        is_valid, errors = validate_schema_compliance(partial_df, schema)
        
        self.assertFalse(is_valid, "Partial DataFrame should fail schema validation")
        self.assertTrue(any("Missing required column" in err for err in errors),
                      "Should report missing required columns")

    def test_proportion_sum(self):
        """Test that land cover proportions must sum to 1.0."""
        schema = load_schema(self.schema_path)
        
        # Create a DataFrame with proportions that don't sum to 1.0
        bad_df = pd.DataFrame({
            'species_id': ['species1', 'species2'],
            'foraging_guild': ['guild1', 'guild2'],
            'forest_prop_100m': [0.5, 0.6],
            'grassland_prop_100m': [0.2, 0.2],
            'wetland_prop_100m': [0.1, 0.1],
            'urban_prop_100m': [0.1, 0.1],
            'other_prop_100m': [0.1, 0.1]  # Sum is 1.0 for first, 1.1 for second
        })
        
        is_valid, errors = validate_schema_compliance(bad_df, schema)
        
        self.assertFalse(is_valid, "DataFrame with bad proportions should fail validation")
        self.assertTrue(any("sum to 1.0" in err for err in errors),
                      "Should report proportion sum error")

    def test_correct_proportions(self):
        """Test that land cover proportions that sum to 1.0 pass validation."""
        schema = load_schema(self.schema_path)
        
        # Create a DataFrame with valid proportions
        good_df = pd.DataFrame({
            'species_id': ['species1', 'species2'],
            'foraging_guild': ['guild1', 'guild2'],
            'forest_prop_100m': [0.5, 0.4],
            'grassland_prop_100m': [0.2, 0.3],
            'wetland_prop_100m': [0.1, 0.1],
            'urban_prop_100m': [0.1, 0.1],
            'other_prop_100m': [0.1, 0.1]  # All sum to 1.0
        })
        
        is_valid, errors = validate_schema_compliance(good_df, schema)
        
        self.assertTrue(is_valid, f"Valid DataFrame should pass validation. Errors: {errors}")

if __name__ == '__main__':
    unittest.main()