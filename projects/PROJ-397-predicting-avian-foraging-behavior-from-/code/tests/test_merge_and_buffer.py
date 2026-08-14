import os
import sys
import unittest
import tempfile
import json
import pandas as pd
from pathlib import Path
from unittest.mock import patch, MagicMock
import yaml

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from data.merge_and_buffer import validate_schema, REQUIRED_COLUMNS

class TestMergeAndBuffer(unittest.TestCase):
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.test_df = pd.DataFrame({
            'species_id': ['A001', 'A002', 'A003'],
            'foraging_guild': ['insectivore', 'granivore', 'omnivore'],
            'land_cover_proportions': [
                {'urban': 0.1, 'agriculture': 0.2, 'forest': 0.3, 'water': 0.0, 'wetland': 0.0, 'grassland': 0.3, 'barren': 0.1},
                {'urban': 0.0, 'agriculture': 0.8, 'forest': 0.1, 'water': 0.0, 'wetland': 0.0, 'grassland': 0.1, 'barren': 0.0},
                {'urban': 0.5, 'agriculture': 0.2, 'forest': 0.1, 'water': 0.0, 'wetland': 0.0, 'grassland': 0.2, 'barren': 0.0}
            ],
            'latitude': [40.0, 41.0, 42.0],
            'longitude': [-105.0, -106.0, -107.0]
        })
        
    def test_validate_schema_passes_with_valid_data(self):
        """Test that validate_schema returns True for valid data."""
        result = validate_schema(self.test_df)
        self.assertTrue(result)
        
    def test_validate_schema_fails_missing_species_id(self):
        """Test that validate_schema raises ValueError when species_id is missing."""
        df_missing = self.test_df.drop(columns=['species_id'])
        with self.assertRaises(ValueError) as context:
            validate_schema(df_missing)
        self.assertIn('species_id', str(context.exception))
        
    def test_validate_schema_fails_missing_foraging_guild(self):
        """Test that validate_schema raises ValueError when foraging_guild is missing."""
        df_missing = self.test_df.drop(columns=['foraging_guild'])
        with self.assertRaises(ValueError) as context:
            validate_schema(df_missing)
        self.assertIn('foraging_guild', str(context.exception))
        
    def test_validate_schema_fails_missing_land_cover_proportions(self):
        """Test that validate_schema raises ValueError when land_cover_proportions is missing."""
        df_missing = self.test_df.drop(columns=['land_cover_proportions'])
        with self.assertRaises(ValueError) as context:
            validate_schema(df_missing)
        self.assertIn('land_cover_proportions', str(context.exception))
        
    def test_validate_schema_fails_null_species_id(self):
        """Test that validate_schema raises ValueError when species_id contains null."""
        df_null = self.test_df.copy()
        df_null.loc[0, 'species_id'] = None
        with self.assertRaises(ValueError) as context:
            validate_schema(df_null)
        self.assertIn('species_id', str(context.exception))
        
    def test_validate_schema_fails_null_foraging_guild(self):
        """Test that validate_schema raises ValueError when foraging_guild contains null."""
        df_null = self.test_df.copy()
        df_null.loc[0, 'foraging_guild'] = None
        with self.assertRaises(ValueError) as context:
            validate_schema(df_null)
        self.assertIn('foraging_guild', str(context.exception))
        
    def test_validate_schema_fails_null_land_cover_proportions(self):
        """Test that validate_schema raises ValueError when land_cover_proportions contains null."""
        df_null = self.test_df.copy()
        df_null.loc[0, 'land_cover_proportions'] = None
        with self.assertRaises(ValueError) as context:
            validate_schema(df_null)
        self.assertIn('land_cover_proportions', str(context.exception))
        
    def test_validate_schema_fails_invalid_land_cover_structure(self):
        """Test that validate_schema raises ValueError for invalid land_cover_proportions structure."""
        df_invalid = self.test_df.copy()
        df_invalid.loc[0, 'land_cover_proportions'] = "not a dict"
        with self.assertRaises(ValueError) as context:
            validate_schema(df_invalid)
        self.assertIn('land_cover_proportions', str(context.exception))
        
    def test_validate_schema_fails_missing_land_cover_keys(self):
        """Test that validate_schema raises ValueError for missing land cover keys."""
        df_invalid = self.test_df.copy()
        df_invalid.loc[0, 'land_cover_proportions'] = {'urban': 1.0}  # Missing other keys
        with self.assertRaises(ValueError) as context:
            validate_schema(df_invalid)
        self.assertIn('land_cover_proportions', str(context.exception))
        
    def test_validate_schema_handles_string_json_proportions(self):
        """Test that validate_schema handles string-encoded JSON proportions."""
        df_valid = self.test_df.copy()
        df_valid.loc[0, 'land_cover_proportions'] = json.dumps({
            'urban': 0.1, 'agriculture': 0.2, 'forest': 0.3, 
            'water': 0.0, 'wetland': 0.0, 'grassland': 0.3, 'barren': 0.1
        })
        result = validate_schema(df_valid)
        self.assertTrue(result)
        
    def test_validate_schema_raises_on_invalid_json_string(self):
        """Test that validate_schema raises ValueError for invalid JSON string."""
        df_invalid = self.test_df.copy()
        df_invalid.loc[0, 'land_cover_proportions'] = "not valid json"
        with self.assertRaises(ValueError) as context:
            validate_schema(df_invalid)
        self.assertIn('land_cover_proportions', str(context.exception))
        
    def test_required_columns_constant(self):
        """Test that REQUIRED_COLUMNS contains expected values."""
        expected_cols = ['species_id', 'foraging_guild', 'land_cover_proportions']
        self.assertEqual(REQUIRED_COLUMNS, expected_cols)

if __name__ == '__main__':
    unittest.main()