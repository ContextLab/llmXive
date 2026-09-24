import os
import sys
import unittest
import tempfile
import json
import pandas as pd
import numpy as np
from pathlib import Path
from shapely.geometry import Point
import geopandas as gpd
from unittest.mock import patch, MagicMock

# Add code to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'code'))

from data.calculate_100m_buffers import (
    calculate_land_cover_proportions, 
    validate_proportions, 
    CLASS_TO_CATEGORY
)

class TestCalculate100mBuffers(unittest.TestCase):
    
    def setUp(self):
        """Set up test fixtures."""
        self.test_df = pd.DataFrame({
            'species_id': ['sp1', 'sp2'],
            'latitude': [40.7128, 34.0522],
            'longitude': [-74.0060, -118.2437]
        })
        
        # Mock raster dataset
        self.mock_raster = MagicMock()
        self.mock_raster.transform = (1.0, 0.0, 0.0, 0.0, -1.0, 0.0) # Dummy transform
        self.mock_raster.crs = MagicMock()
        self.mock_raster.crs.to_epsg.return_value = 4326
        self.mock_raster.width = 100
        self.mock_raster.height = 100
        
        # Mock the mask function to return a known array
        # We want to test that proportions sum to 1.0
        # Create a mock array where we know the counts
        mock_data = np.ones((10, 10)) * 21 # All forest
        self.mock_raster.read.return_value = [mock_data]
        self.mock_raster.read(1).shape = (10, 10)
        
    @patch('data.calculate_100m_buffers.mask')
    def test_proportions_sum_to_one(self, mock_mask_func):
        """Test that land cover proportions sum to 1.0 for a known coordinate."""
        
        # Mock the mask function to return a specific array
        # Let's say we have a 10x10 grid, all forest (class 21)
        mock_out_image = np.ones((10, 10)) * 21
        mock_transform = (1.0, 0.0, 0.0, 0.0, -1.0, 0.0)
        
        mock_mask_func.return_value = (mock_out_image, mock_transform)
        
        # Run calculation
        result_df = calculate_land_cover_proportions(self.test_df, self.mock_raster)
        
        # Check proportions
        forest_prop = result_df['forest_prop_100m'].iloc[0]
        other_props = result_df[['grassland_prop_100m', 'wetland_prop_100m', 
                                 'urban_prop_100m', 'other_prop_100m']].sum(axis=1).iloc[0]
        
        total = forest_prop + other_props
        
        # Assert sum is 1.0 within tolerance
        self.assertAlmostEqual(total, 1.0, places=6, 
                             msg=f"Proportions do not sum to 1.0: {total}")
        
    def test_validate_proportions(self):
        """Test the validation function."""
        df = pd.DataFrame({
            'forest_prop_100m': [0.5, 0.0],
            'grassland_prop_100m': [0.5, 0.0],
            'wetland_prop_100m': [0.0, 0.0],
            'urban_prop_100m': [0.0, 0.0],
            'other_prop_100m': [0.0, 1.0]
        })
        
        # First row sums to 1.0, second row sums to 1.0
        self.assertTrue(validate_proportions(df))
        
        # Modify one row to not sum to 1.0
        df.loc[0, 'forest_prop_100m'] = 0.4
        self.assertFalse(validate_proportions(df))

if __name__ == '__main__':
    unittest.main()