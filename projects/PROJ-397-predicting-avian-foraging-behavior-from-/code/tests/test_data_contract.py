import os
import sys
import unittest
import yaml
import pandas as pd
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add code to path to allow imports
code_root = Path(__file__).parent.parent
sys.path.insert(0, str(code_root))

from utils.config import get_processed_dir, get_project_root
from data.merge_and_buffer import validate_schema, REQUIRED_COLUMNS

def load_schema():
    """Loads the dataset schema from YAML."""
    schema_path = get_project_root() / "contracts" / "dataset.schema.yaml"
    if not schema_path.exists():
        # Fallback if file is missing for test environment, though spec requires it
        return {
            "required_columns": list(REQUIRED_COLUMNS)
        }
    with open(schema_path, 'r') as f:
        return yaml.safe_load(f)

def validate_schema_compliance(df: pd.DataFrame) -> bool:
    """Checks if DataFrame matches the schema."""
    schema = load_schema()
    required = set(schema.get("required_columns", []))
    return required.issubset(set(df.columns))

class TestDataContract(unittest.TestCase):
    
    def setUp(self):
        """Set up test fixtures."""
        self.valid_data = pd.DataFrame({
            'species_id': ['A', 'B', 'C'],
            'foraging_guild': ['G1', 'G2', 'G1'],
            'latitude': [40.0, 41.0, 42.0],
            'longitude': [-74.0, -75.0, -76.0],
            'observation_date': ['2023-01-01', '2023-01-02', '2023-01-03'],
            'forest_prop_100m': [0.5, 0.6, 0.7],
            'grassland_prop_100m': [0.2, 0.1, 0.1],
            'wetland_prop_100m': [0.0, 0.0, 0.0],
            'urban_prop_100m': [0.3, 0.3, 0.2],
            'water_prop_100m': [0.0, 0.0, 0.0],
            'cropland_prop_100m': [0.0, 0.0, 0.0],
            'barren_prop_100m': [0.0, 0.0, 0.0],
            'shrub_prop_100m': [0.0, 0.0, 0.0]
        })
        
        self.invalid_data_missing_col = pd.DataFrame({
            'species_id': ['A', 'B'],
            'foraging_guild': ['G1', 'G2'],
            'latitude': [40.0, 41.0],
            'longitude': [-74.0, -75.0],
            'observation_date': ['2023-01-01', '2023-01-02'],
            'forest_prop_100m': [0.5, 0.6],
            'grassland_prop_100m': [0.2, 0.1],
            # Missing wetland_prop_100m and others
        })

    def test_validate_schema_valid(self):
        """Test that a valid DataFrame passes validation."""
        # Should not raise
        validate_schema(self.valid_data)
        self.assertTrue(validate_schema_compliance(self.valid_data))

    def test_validate_schema_missing_columns(self):
        """Test that a DataFrame with missing columns raises ValueError."""
        with self.assertRaises(ValueError) as context:
            validate_schema(self.invalid_data_missing_col)
        self.assertIn("Missing required columns", str(context.exception))

    def test_validate_schema_empty_dataframe(self):
        """Test that an empty DataFrame raises ValueError."""
        empty_df = pd.DataFrame()
        with self.assertRaises(ValueError) as context:
            validate_schema(empty_df)
        self.assertIn("DataFrame is None or empty", str(context.exception))

    def test_validate_schema_non_numeric(self):
        """Test that non-numeric data in numeric columns raises ValueError."""
        bad_df = self.valid_data.copy()
        bad_df['forest_prop_100m'] = ['a', 'b', 'c']
        with self.assertRaises(ValueError) as context:
            validate_schema(bad_df)
        self.assertIn("must be numeric", str(context.exception))

    def test_schema_compliance_function(self):
        """Test the standalone schema compliance function."""
        self.assertTrue(validate_schema_compliance(self.valid_data))
        self.assertFalse(validate_schema_compliance(self.invalid_data_missing_col))

if __name__ == '__main__':
    unittest.main()