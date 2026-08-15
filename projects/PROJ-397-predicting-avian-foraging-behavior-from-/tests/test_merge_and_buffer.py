"""
Unit tests for T013: merge_and_buffer.py
"""
import os
import sys
import unittest
import tempfile
import json
import pandas as pd
import numpy as np
from pathlib import Path
import rasterio
from rasterio.crs import CRS
from shapely.geometry import Point

# Add code directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from data.merge_and_buffer import (
    load_filtered_ebd,
    load_guild_mapping,
    calculate_land_cover_proportions,
    assign_guilds,
    validate_schema,
    LAND_COVER_GROUPS
)

class TestMergeAndBuffer(unittest.TestCase):
    
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.temp_path = Path(self.temp_dir.name)
        
        # Create mock eBird data
        self.ebd_file = self.temp_path / "ebd_train.csv"
        mock_ebd = pd.DataFrame({
            'species_id': ['A001', 'A001', 'B002', 'C003'],
            'latitude': [40.0, 41.0, 42.0, 43.0],
            'longitude': [-74.0, -75.0, -76.0, -77.0]
        })
        mock_ebd.to_csv(self.ebd_file, index=False)
        
        # Create mock top species list
        self.top_species_file = self.temp_path / "top_25_species_ids.json"
        with open(self.top_species_file, 'w') as f:
            json.dump(['A001', 'B002'], f)
        
        # Create mock guild mapping
        self.guild_file = self.temp_path / "guild_mapping.csv"
        mock_guild = pd.DataFrame({
            'species_id': ['A001', 'B002', 'C003'],
            'foraging_guild': ['Forest', 'Grassland', 'Wetland']
        })
        mock_guild.to_csv(self.guild_file, index=False)
        
        # Create mock NLCD raster
        self.nlcd_file = self.temp_path / "nlcd_2019.zip"
        # We can't easily create a zip with rasterio in a unit test without files,
        # so we will test the calculation function directly with a numpy array.
        
    def tearDown(self):
        self.temp_dir.cleanup()

    def test_load_filtered_ebd(self):
        df = load_filtered_ebd(self.top_species_file, self.ebd_file)
        self.assertEqual(len(df), 3) # A001 (2 rows) + B002 (1 row)
        self.assertTrue(all(df['species_id'].isin(['A001', 'B002'])))

    def test_load_guild_mapping(self):
        df = load_guild_mapping(self.guild_file)
        self.assertEqual(len(df), 3)
        self.assertIn('foraging_guild', df.columns)

    def test_calculate_land_cover_proportions(self):
        # Create a simple 10x10 raster
        raster_data = np.ones((10, 10), dtype=np.int16) * 41 # All forest
        meta = {
            'crs': CRS.from_epsg(32618), # UTM 18N
            'transform': rasterio.transform.from_bounds(-75, 40, -74, 41, 10, 10),
            'width': 10,
            'height': 10,
            'nodata': -1
        }
        
        # Point in the center
        props = calculate_land_cover_proportions(40.5, -74.5, raster_data, meta)
        
        # Should be 100% forest
        self.assertAlmostEqual(props['forest_prop_100m'], 1.0, places=1)
        self.assertAlmostEqual(props['grassland_prop_100m'], 0.0, places=1)

    def test_assign_guilds(self):
        ebd_df = pd.DataFrame({
            'species_id': ['A001', 'B002'],
            'lat': [40, 41],
            'lon': [-74, -75]
        })
        guild_df = pd.DataFrame({
            'species_id': ['A001', 'B002'],
            'foraging_guild': ['Forest', 'Grassland']
        })
        
        result = assign_guilds(ebd_df, guild_df)
        self.assertEqual(result['foraging_guild'].tolist(), ['Forest', 'Grassland'])

    def test_validate_schema(self):
        # Valid schema
        valid_df = pd.DataFrame({
            'species_id': ['A'],
            'foraging_guild': ['Forest'],
            'forest_prop_100m': [0.5],
            'grassland_prop_100m': [0.2],
            'wetland_prop_100m': [0.1],
            'urban_prop_100m': [0.1],
            'water_prop_100m': [0.1],
            'barren_prop_100m': [0.0],
            'other_prop_100m': [0.0]
        })
        self.assertTrue(validate_schema(valid_df))
        
        # Invalid schema (missing column)
        invalid_df = pd.DataFrame({
            'species_id': ['A'],
            'foraging_guild': ['Forest']
        })
        self.assertFalse(validate_schema(invalid_df))

if __name__ == '__main__':
    unittest.main()