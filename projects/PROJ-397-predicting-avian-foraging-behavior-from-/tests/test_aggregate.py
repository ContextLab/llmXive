import os
import sys
import unittest
import tempfile
import json
import pandas as pd
from pathlib import Path

# Add code to path for imports
code_root = Path(__file__).parent.parent
sys.path.insert(0, str(code_root))

from data.aggregate import (
    load_merged_observations,
    parse_land_cover_proportions,
    aggregate_species_profiles,
    save_species_profiles
)
from utils.config import get_processed_dir

class TestAggregate(unittest.TestCase):

    def setUp(self):
        """Create a temporary directory and mock data for testing."""
        self.temp_dir = tempfile.mkdtemp()
        self.processed_dir = Path(self.temp_dir)
        
        # Create mock merged_observations.csv
        self.mock_input = self.processed_dir / "merged_observations.csv"
        data = {
            'species_id': ['A', 'A', 'B', 'B', 'C'],
            'foraging_guild': ['Forest', 'Forest', 'Grassland', 'Grassland', 'Wetland'],
            'forest_prop_100m': [0.8, 0.9, 0.1, 0.2, 0.5],
            'grassland_prop_100m': [0.1, 0.05, 0.8, 0.7, 0.2],
            'wetland_prop_100m': [0.05, 0.05, 0.05, 0.05, 0.25],
            'urban_prop_100m': [0.05, 0.0, 0.05, 0.05, 0.05]
        }
        self.df_mock = pd.DataFrame(data)
        self.df_mock.to_csv(self.mock_input, index=False)

    def tearDown(self):
        """Clean up temporary files."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_load_merged_observations(self):
        """Test loading the merged observations file."""
        df = load_merged_observations(str(self.mock_input))
        self.assertEqual(len(df), 5)
        self.assertIn('species_id', df.columns)
        self.assertIn('foraging_guild', df.columns)

    def test_parse_land_cover_proportions(self):
        """Test parsing land cover columns."""
        df = pd.read_csv(self.mock_input)
        lc_cols = parse_land_cover_proportions(df)
        expected = ['forest_prop_100m', 'grassland_prop_100m', 'urban_prop_100m', 'wetland_prop_100m']
        self.assertEqual(sorted(lc_cols), sorted(expected))

    def test_aggregate_species_profiles(self):
        """Test aggregation logic."""
        df = pd.read_csv(self.mock_input)
        lc_cols = parse_land_cover_proportions(df)
        
        agg_df, logs = aggregate_species_profiles(df, lc_cols)
        
        # Should have 3 unique species
        self.assertEqual(len(agg_df), 3)
        
        # Check that species 'A' has averaged forest proportion
        # (0.8 + 0.9) / 2 = 0.85
        row_a = agg_df[agg_df['species_id'] == 'A'].iloc[0]
        self.assertAlmostEqual(row_a['forest_prop_100m'], 0.85, places=2)
        
        # Check logs
        self.assertEqual(len(logs), 0) # No dropped rows in this mock

    def test_aggregate_with_missing_data(self):
        """Test aggregation handles missing data and logs it."""
        # Create a DataFrame with a NaN
        data = {
            'species_id': ['A', 'A', 'B'],
            'foraging_guild': ['Forest', 'Forest', 'Grassland'],
            'forest_prop_100m': [0.8, None, 0.1],
            'grassland_prop_100m': [0.1, 0.05, 0.8],
            'wetland_prop_100m': [0.05, 0.05, 0.05],
            'urban_prop_100m': [0.05, 0.0, 0.05]
        }
        df_nan = pd.DataFrame(data)
        temp_csv = self.processed_dir / "mock_nan.csv"
        df_nan.to_csv(temp_csv, index=False)
        
        df_loaded = pd.read_csv(temp_csv)
        lc_cols = parse_land_cover_proportions(df_loaded)
        
        agg_df, logs = aggregate_species_profiles(df_loaded, lc_cols)
        
        # Should have dropped the row with NaN
        self.assertEqual(len(agg_df), 2) # Species A (1 row), Species B (1 row)
        self.assertEqual(len(logs), 1)
        self.assertEqual(logs[0]['reason_code'], 'MISSING_DATA')

    def test_save_species_profiles(self):
        """Test saving the species profiles."""
        df = pd.read_csv(self.mock_input)
        lc_cols = parse_land_cover_proportions(df)
        agg_df, logs = aggregate_species_profiles(df, lc_cols)
        
        output_path = self.processed_dir / "species_profiles.csv"
        save_species_profiles(agg_df, str(output_path), logs)
        
        self.assertTrue(output_path.exists())
        saved_df = pd.read_csv(output_path)
        self.assertEqual(len(saved_df), 3)

if __name__ == '__main__':
    unittest.main()