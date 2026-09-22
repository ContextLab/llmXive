import os
import sys
import unittest
import yaml
import pandas as pd
import csv
from pathlib import Path
from typing import List, Dict, Any, Tuple

# Add project root to path
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root / "code"))

from utils.config import get_processed_dir, get_project_root

def load_schema(schema_path: str) -> Dict[str, Any]:
    """Load the YAML schema file."""
    with open(schema_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)

def validate_schema_compliance(
    df: pd.DataFrame, 
    schema: Dict[str, Any]
) -> Tuple[bool, List[str]]:
    """
    Validate that a DataFrame conforms to the given schema.
    
    Returns:
        Tuple of (is_valid, list_of_errors)
    """
    errors = []
    
    # Check required columns
    required_columns = schema.get('required_columns', [])
    actual_columns = list(df.columns)
    
    missing_columns = set(required_columns) - set(actual_columns)
    if missing_columns:
        errors.append(f"Missing required columns: {missing_columns}")
        return False, errors
    
    # Check column types
    column_types = schema.get('column_types', {})
    for col, expected_type in column_types.items():
        if col in df.columns:
            if expected_type == 'string':
                if not pd.api.types.is_string_dtype(df[col]):
                    # Allow object dtype which is common for strings in pandas
                    if df[col].dtype != 'object':
                        errors.append(f"Column '{col}' should be string type, got {df[col].dtype}")
            elif expected_type == 'float':
                if not pd.api.types.is_float_dtype(df[col]):
                    errors.append(f"Column '{col}' should be float type, got {df[col].dtype}")
    
    # Check constraints
    constraints = schema.get('constraints', [])
    for constraint in constraints:
        if 'columns' in constraint:
            # Multi-column constraint
            cols = constraint['columns']
            rule = constraint['rule']
            
            if rule.startswith("float values between"):
                # Check range for all specified columns
                for col in cols:
                    if col in df.columns:
                        if not ((df[col] >= 0.0).all() and (df[col] <= 1.0).all()):
                            errors.append(f"Column '{col}' values must be between 0.0 and 1.0")
            
            elif "Sum of all land-cover proportion" in rule:
                # Check sum constraint
                prop_cols = ['forest_prop_100m', 'grassland_prop_100m', 
                             'wetland_prop_100m', 'urban_prop_100m', 'other_prop_100m']
                if all(col in df.columns for col in prop_cols):
                    sum_cols = df[prop_cols].sum(axis=1)
                    # Allow small floating point error
                    if not (sum_cols <= 1.0001).all():
                        violations = sum_cols[sum_cols > 1.0001]
                        errors.append(f"Some rows have land-cover proportions summing to > 1.0: {len(violations)} violations")
        
        elif 'column' in constraint:
            # Single column constraint
            col = constraint['column']
            rule = constraint['rule']
            
            if col in df.columns:
                if rule == "non-empty string":
                    if df[col].isna().any() or (df[col].astype(str).str.strip() == '').any():
                        errors.append(f"Column '{col}' contains empty or null values")
    
    return len(errors) == 0, errors

class TestDataContract(unittest.TestCase):
    """Test suite for data contract compliance of merged_observations.csv"""
    
    def setUp(self):
        """Set up test fixtures."""
        self.project_root = get_project_root()
        self.processed_dir = get_processed_dir()
        self.schema_path = self.project_root / "contracts" / "dataset.schema.yaml"
        self.data_path = self.processed_dir / "merged_observations.csv"
        
        # Load schema
        if self.schema_path.exists():
            self.schema = load_schema(str(self.schema_path))
        else:
            self.schema = None
    
    def test_schema_file_exists(self):
        """Test that the schema file exists."""
        self.assertTrue(
            self.schema_path.exists(), 
            f"Schema file not found at {self.schema_path}"
        )
    
    def test_data_file_exists(self):
        """Test that the merged_observations.csv file exists."""
        self.assertTrue(
            self.data_path.exists(), 
            f"Merged observations file not found at {self.data_path}"
        )
    
    def test_schema_compliance(self):
        """
        Test that merged_observations.csv conforms to the dataset schema.
        
        This test verifies:
        1. All required columns are present
        2. Column data types match the schema
        3. Data constraints are satisfied (e.g., proportions between 0-1, sum <= 1)
        """
        # Skip if schema or data file doesn't exist
        if not self.schema_path.exists():
            self.fail(f"Schema file not found at {self.schema_path}")
        
        if not self.data_path.exists():
            self.fail(f"Merged observations file not found at {self.data_path}")
        
        # Load the data
        df = pd.read_csv(self.data_path)
        
        # Validate against schema
        is_valid, errors = validate_schema_compliance(df, self.schema)
        
        if not is_valid:
            error_msg = "Schema validation failed with the following errors:\n"
            for err in errors:
                error_msg += f"  - {err}\n"
            self.fail(error_msg)
        
        # Additional specific checks
        required_cols = self.schema['required_columns']
        for col in required_cols:
            self.assertIn(col, df.columns, f"Required column '{col}' is missing")
        
        # Check that land cover proportions sum to <= 1
        prop_cols = ['forest_prop_100m', 'grassland_prop_100m', 
                     'wetland_prop_100m', 'urban_prop_100m', 'other_prop_100m']
        if all(col in df.columns for col in prop_cols):
            sums = df[prop_cols].sum(axis=1)
            self.assertTrue(
                (sums <= 1.0001).all(), 
                "Some rows have land-cover proportions summing to > 1.0"
            )
        
        # Check that proportions are between 0 and 1
        for col in prop_cols:
            if col in df.columns:
                self.assertTrue(
                    ((df[col] >= 0.0) & (df[col] <= 1.0)).all(),
                    f"Column '{col}' contains values outside [0, 1] range"
                )
    
    def test_required_columns_present(self):
        """Test that all required columns from the schema are present."""
        if not self.data_path.exists():
            self.skipTest("Data file does not exist")
        
        df = pd.read_csv(self.data_path)
        required_cols = self.schema['required_columns']
        
        for col in required_cols:
            self.assertIn(
                col, df.columns, 
                f"Required column '{col}' is missing from merged_observations.csv"
            )
    
    def test_land_cover_columns_exist(self):
        """Test that all 100m buffer land cover proportion columns exist."""
        if not self.data_path.exists():
            self.skipTest("Data file does not exist")
        
        df = pd.read_csv(self.data_path)
        expected_cols = [
            'forest_prop_100m',
            'grassland_prop_100m', 
            'wetland_prop_100m',
            'urban_prop_100m',
            'other_prop_100m'
        ]
        
        for col in expected_cols:
            self.assertIn(
                col, df.columns,
                f"Land cover proportion column '{col}' is missing"
            )
    
    def test_species_id_and_guild_columns(self):
        """Test that species_id and foraging_guild columns exist and are non-empty."""
        if not self.data_path.exists():
            self.skipTest("Data file does not exist")
        
        df = pd.read_csv(self.data_path)
        
        # Check species_id
        self.assertIn('species_id', df.columns)
        self.assertFalse(df['species_id'].isna().any(), "species_id contains null values")
        self.assertFalse((df['species_id'].astype(str).str.strip() == '').any(), "species_id contains empty strings")
        
        # Check foraging_guild
        self.assertIn('foraging_guild', df.columns)
        self.assertFalse(df['foraging_guild'].isna().any(), "foraging_guild contains null values")
        self.assertFalse((df['foraging_guild'].astype(str).str.strip() == '').any(), "foraging_guild contains empty strings")

if __name__ == '__main__':
    unittest.main()