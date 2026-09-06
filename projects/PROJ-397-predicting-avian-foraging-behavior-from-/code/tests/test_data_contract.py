import os
import sys
import unittest
import yaml
import pandas as pd
from pathlib import Path

# Add project root to path
project_root = Path(__file__).resolve().parents[2]
code_root = project_root / "code"
sys.path.insert(0, str(code_root))

from utils.config import get_processed_dir, get_project_root

def load_schema(schema_path=None):
    """Load the dataset schema from YAML file."""
    if schema_path is None:
        schema_path = get_project_root() / "code" / "contracts" / "dataset.schema.yaml"
    
    if not os.path.exists(schema_path):
        raise FileNotFoundError(f"Schema file not found: {schema_path}")
    
    with open(schema_path, 'r') as f:
        return yaml.safe_load(f)

def validate_schema_compliance(df, schema):
    """
    Validate that a DataFrame matches the schema requirements.
    
    Args:
        df: pandas DataFrame to validate
        schema: dict loaded from dataset.schema.yaml
    
    Returns:
        bool: True if compliant, raises ValueError otherwise
    
    Raises:
        ValueError: If schema compliance fails
    """
    required_columns = schema.get('required_columns', [])
    column_definitions = schema.get('column_definitions', {})
    constraints = schema.get('constraints', [])
    
    # Check required columns
    missing_cols = set(required_columns) - set(df.columns)
    if missing_cols:
        raise ValueError(f"Missing required columns: {missing_cols}")
    
    # Check column types and constraints
    for col_name, col_def in column_definitions.items():
        if col_name not in df.columns:
            continue  # Already checked above
        
        dtype = col_def.get('type')
        nullable = col_def.get('nullable', True)
        min_val = col_def.get('min')
        max_val = col_def.get('max')
        allowed_values = col_def.get('allowed_values')
        
        # Check nullability
        if not nullable and df[col_name].isnull().any():
            raise ValueError(f"Column '{col_name}' contains null values but is marked as non-nullable")
        
        # Check value ranges for numeric columns
        if dtype == 'float':
            if min_val is not None:
                if (df[col_name] < min_val).any():
                    raise ValueError(f"Column '{col_name}' has values below minimum {min_val}")
            if max_val is not None:
                if (df[col_name] > max_val).any():
                    raise ValueError(f"Column '{col_name}' has values above maximum {max_val}")
        
        # Check allowed values for categorical columns
        if allowed_values:
            invalid_vals = set(df[col_name].dropna().unique()) - set(allowed_values)
            if invalid_vals:
                raise ValueError(f"Column '{col_name}' contains invalid values: {invalid_vals}")
    
    # Check constraints
    for constraint in constraints:
        check_expr = constraint.get('check')
        if check_expr:
            try:
                # Evaluate the constraint expression
                # This is a simple approach; in production, use a safer evaluation method
                result = df.eval(check_expr)
                if not result.all():
                    failing_rows = df[~result]
                    raise ValueError(f"Constraint failed: {constraint['description']}. "
                                   f"Failing rows: {len(failing_rows)}")
            except Exception as e:
                raise ValueError(f"Constraint check failed: {constraint['description']}. Error: {str(e)}")
    
    return True

class TestDataContract(unittest.TestCase):
    """Test suite for dataset schema compliance validation."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.processed_dir = get_processed_dir()
        self.schema_path = get_project_root() / "code" / "contracts" / "dataset.schema.yaml"
        self.merged_file = self.processed_dir / "merged_observations.csv"
        self.schema = load_schema(self.schema_path)
    
    def test_schema_exists(self):
        """Test that the schema file exists."""
        self.assertTrue(os.path.exists(self.schema_path), 
                      f"Schema file not found at {self.schema_path}")
    
    def test_schema_structure(self):
        """Test that the schema has the required structure."""
        self.assertIn('required_columns', self.schema)
        self.assertIn('column_definitions', self.schema)
        self.assertIn('merged_observations', self.schema.get('name', ''))
    
    def test_validate_schema(self):
        """
        Test that merged_observations.csv matches the schema defined in 
        contracts/dataset.schema.yaml.
        
        Specifically validates columns: species_id, foraging_guild, and 
        land cover proportion columns.
        """
        # Check if the merged file exists
        if not os.path.exists(self.merged_file):
            self.fail(f"Merged observations file not found at {self.merged_file}. "
                    "Ensure T039 (merge_and_buffer.py) has been executed successfully.")
        
        # Load the merged data
        try:
            df = pd.read_csv(self.merged_file)
        except Exception as e:
            self.fail(f"Failed to load merged_observations.csv: {str(e)}")
        
        # Validate schema compliance
        try:
            validate_schema_compliance(df, self.schema)
        except ValueError as e:
            self.fail(f"Schema validation failed: {str(e)}")
    
    def test_required_columns_present(self):
        """Test that all required columns are present in the merged data."""
        if not os.path.exists(self.merged_file):
            self.skipTest("Merged observations file not found")
        
        df = pd.read_csv(self.merged_file)
        required_cols = self.schema.get('required_columns', [])
        
        for col in required_cols:
            self.assertIn(col, df.columns, 
                        f"Required column '{col}' missing from merged_observations.csv")
    
    def test_land_cover_proportions_range(self):
        """Test that land cover proportions are in valid range [0.0, 1.0]."""
        if not os.path.exists(self.merged_file):
            self.skipTest("Merged observations file not found")
        
        df = pd.read_csv(self.merged_file)
        land_cover_cols = [col for col in df.columns if 'prop_100m' in col]
        
        for col in land_cover_cols:
            self.assertTrue((df[col] >= 0.0).all(), 
                          f"Column '{col}' has values below 0.0")
            self.assertTrue((df[col] <= 1.0).all(), 
                          f"Column '{col}' has values above 1.0")
    
    def test_foraging_guild_values(self):
        """Test that foraging_guild column contains only valid values."""
        if not os.path.exists(self.merged_file):
            self.skipTest("Merged observations file not found")
        
        df = pd.read_csv(self.merged_file)
        allowed_guilds = self.schema['column_definitions']['foraging_guild']['allowed_values']
        
        invalid_guilds = set(df['foraging_guild'].dropna().unique()) - set(allowed_guilds)
        self.assertEqual(len(invalid_guilds), 0, 
                       f"Invalid foraging guilds found: {invalid_guilds}")
    
    def test_proportion_sum_constraint(self):
        """Test that land cover proportions sum to approximately 1.0."""
        if not os.path.exists(self.merged_file):
            self.skipTest("Merged observations file not found")
        
        df = pd.read_csv(self.merged_file)
        land_cover_cols = [col for col in df.columns if 'prop_100m' in col]
        
        # Calculate sum of proportions
        prop_sum = df[land_cover_cols].sum(axis=1)
        
        # Check if all sums are approximately 1.0 (within 0.01 tolerance)
        invalid_sums = prop_sum[(prop_sum < 0.99) | (prop_sum > 1.01)]
        self.assertEqual(len(invalid_sums), 0, 
                       f"Land cover proportions do not sum to ~1.0 in {len(invalid_sums)} rows")
    
    def test_species_id_not_empty(self):
        """Test that species_id column is not empty."""
        if not os.path.exists(self.merged_file):
            self.skipTest("Merged observations file not found")
        
        df = pd.read_csv(self.merged_file)
        empty_species = df[df['species_id'].str.len() == 0]
        
        self.assertEqual(len(empty_species), 0, 
                       f"Found {len(empty_species)} rows with empty species_id")

if __name__ == '__main__':
    unittest.main()