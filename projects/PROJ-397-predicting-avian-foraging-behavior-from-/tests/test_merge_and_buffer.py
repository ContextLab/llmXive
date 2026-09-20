import os
import sys
import unittest
import tempfile
import json
import pandas as pd
import numpy as np
from pathlib import Path

# Add project root to path
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from data.merge_and_buffer import (
    validate_schema,
    load_filtered_ebd,
    load_guild_mapping,
    assign_guilds,
    filter_by_observation_count,
    calculate_land_cover_proportions
)
from utils.config import get_project_root, get_data_dir, get_processed_dir

class TestMergeAndBuffer(unittest.TestCase):
    
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.project_root = get_project_root()
        
        # Create mock data
        self.ebd_data = pd.DataFrame({
            'species_id': ['sp1', 'sp1', 'sp2', 'sp2', 'sp2', 'sp3'],
            'latitude': [40.0, 40.1, 41.0, 41.1, 41.2, 42.0],
            'longitude': [-75.0, -75.1, -76.0, -76.1, -76.2, -77.0],
            'observation_date': ['2020-01-01'] * 6
        })
        
        self.guild_data = pd.DataFrame({
            'species_id': ['sp1', 'sp2', 'sp3'],
            'foraging_guild': ['ground', 'canopy', 'unknown']
        })
        
        self.ebd_path = os.path.join(self.temp_dir, 'filtered_ebd.csv')
        self.guild_path = os.path.join(self.temp_dir, 'guild_mapping.csv')
        
        self.ebd_data.to_csv(self.ebd_path, index=False)
        self.guild_data.to_csv(self.guild_path, index=False)

    def tearDown(self):
        import shutil
        shutil.rmtree(self.temp_dir)

    def test_validate_schema(self):
        # Test with valid data
        df = self.ebd_data.copy()
        validate_schema(df) # Should not raise
        
        # Test with missing column
        df_missing = df.drop(columns=['latitude'])
        with self.assertRaises(ValueError):
            validate_schema(df_missing)

    def test_load_filtered_ebd(self):
        df = load_filtered_ebd(self.ebd_path)
        self.assertEqual(len(df), 6)
        self.assertIn('species_id', df.columns)
        self.assertIn('latitude', df.columns)
        self.assertIn('longitude', df.columns)

    def test_load_guild_mapping(self):
        df = load_guild_mapping(self.guild_path)
        self.assertEqual(len(df), 3)
        self.assertIn('species_id', df.columns)
        self.assertIn('foraging_guild', df.columns)

    def test_assign_guilds(self):
        ebd_df = load_filtered_ebd(self.ebd_path)
        guild_df = load_guild_mapping(self.guild_path)
        merged = assign_guilds(ebd_df, guild_df)
        
        self.assertEqual(len(merged), len(ebd_df))
        self.assertIn('foraging_guild', merged.columns)
        
        # Check specific assignments
        self.assertEqual(merged.loc[merged['species_id'] == 'sp1', 'foraging_guild'].iloc[0], 'ground')
        self.assertEqual(merged.loc[merged['species_id'] == 'sp2', 'foraging_guild'].iloc[0], 'canopy')
        self.assertEqual(merged.loc[merged['species_id'] == 'sp3', 'foraging_guild'].iloc[0], 'unknown')

    def test_filter_by_observation_count(self):
        ebd_df = load_filtered_ebd(self.ebd_path)
        
        # Filter for >= 3 observations
        filtered = filter_by_observation_count(ebd_df, min_count=3)
        self.assertEqual(len(filtered), 3) # Only sp2 has 3 obs
        
        # Filter for >= 2 observations
        filtered2 = filter_by_observation_count(ebd_df, min_count=2)
        self.assertEqual(len(filtered2), 5) # sp1 (2) + sp2 (3)

    # Note: Testing calculate_land_cover_proportions requires a real raster file.
    # We skip this in unit tests or use a very small synthetic raster if possible.
    # For now, we test that the function exists and has the right signature.
    def test_calculate_land_cover_proportions_signature(self):
        # We cannot easily test the full logic without a raster, but we can check imports
        # and that the function is callable
        self.assertTrue(callable(calculate_land_cover_proportions))

if __name__ == '__main__':
    unittest.main()
