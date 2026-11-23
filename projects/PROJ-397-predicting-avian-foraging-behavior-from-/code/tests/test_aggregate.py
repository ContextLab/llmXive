import os
import sys
import unittest
import tempfile
import json
import pandas as pd
from pathlib import Path
import numpy as np

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))
from data.aggregate import (
    load_merged_observations,
    parse_land_cover_proportions,
    aggregate_species_profiles,
    save_species_profiles
)

class TestAggregate(unittest.TestCase):
    """Unit tests for data/aggregate.py functionality."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.test_data = {
            'species_id': ['A', 'A', 'A', 'B', 'B', 'C'],
            'foraging_guild': ['Forest', 'Forest', 'Grassland', 'Forest', 'Forest', 'Urban'],
            'forest_prop_100m': [0.8, 0.9, 0.1, 0.7, 0.8, 0.2],
            'grassland_prop_100m': [0.1, 0.05, 0.8, 0.1, 0.05, 0.1],
            'wetland_prop_100m': [0.05, 0.05, 0.05, 0.05, 0.05, 0.05],
            'urban_prop_100m': [0.05, 0.0, 0.05, 0.15, 0.15, 0.6],
            'other_prop_100m': [0.0, 0.0, 0.0, 0.0, 0.0, 0.05]
        }
        
        # Create test input file
        self.input_path = os.path.join(self.temp_dir, 'merged_observations.csv')
        df = pd.DataFrame(self.test_data)
        df.to_csv(self.input_path, index=False)

    def tearDown(self):
        """Clean up temporary files."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_load_merged_observations(self):
        """Test loading the merged observations file."""
        df = load_merged_observations(self.input_path)
        self.assertEqual(len(df), 6)
        self.assertIn('species_id', df.columns)
        self.assertIn('foraging_guild', df.columns)

    def test_parse_land_cover_proportions(self):
        """Test parsing of land cover columns."""
        df = load_merged_observations(self.input_path)
        parsed_df = parse_land_cover_proportions(df)
        
        expected_cols = [
            'forest_prop_100m', 'grassland_prop_100m', 
            'wetland_prop_100m', 'urban_prop_100m', 'other_prop_100m'
        ]
        for col in expected_cols:
            self.assertIn(col, parsed_df.columns)
            self.assertTrue(pd.api.types.is_float_dtype(parsed_df[col]))

    def test_aggregate_species_profiles(self):
        """Test aggregation into species-level profiles."""
        df = load_merged_observations(self.input_path)
        df = parse_land_cover_proportions(df)
        
        profiles, drop_logs = aggregate_species_profiles(df, min_obs=2)
        
        # Should have 2 species (A and B with >= 2 obs, C has only 1)
        self.assertEqual(len(profiles), 2)
        self.assertIn('species_id', profiles.columns)
        self.assertIn('observation_count', profiles.columns)
        
        # Check that species C was dropped
        dropped_species = [log['species_id'] for log in drop_logs if log.get('reason_code') == 'insufficient_observations']
        self.assertIn('C', dropped_species)

    def test_aggregate_with_missing_data(self):
        """Test handling of missing land cover data."""
        # Create data with NaN values
        test_data = self.test_data.copy()
        test_data['forest_prop_100m'][0] = np.nan
        
        df = pd.DataFrame(test_data)
        test_input = os.path.join(self.temp_dir, 'merged_with_nan.csv')
        df.to_csv(test_input, index=False)
        
        loaded_df = load_merged_observations(test_input)
        parsed_df = parse_land_cover_proportions(loaded_df)
        
        profiles, drop_logs = aggregate_species_profiles(parsed_df, min_obs=2)
        
        # Should have dropped the row with NaN
        self.assertEqual(len(profiles), 2)  # Still 2 species, but one less observation for A
        
        # Check drop log for invalid_value
        invalid_drops = [log for log in drop_logs if log.get('reason_code') == 'invalid_value']
        self.assertGreater(len(invalid_drops), 0)

    def test_save_species_profiles(self):
        """Test saving species profiles and drop logs."""
        df = load_merged_observations(self.input_path)
        df = parse_land_cover_proportions(df)
        profiles, drop_logs = aggregate_species_profiles(df, min_obs=2)
        
        output_path = os.path.join(self.temp_dir, 'species_profiles.csv')
        save_species_profiles(profiles, output_path, drop_logs)
        
        # Check files exist
        self.assertTrue(os.path.exists(output_path))
        log_path = output_path.replace('.csv', '_drop_log.json')
        self.assertTrue(os.path.exists(log_path))
        
        # Verify content
        saved_profiles = pd.read_csv(output_path)
        self.assertEqual(len(saved_profiles), len(profiles))
        
        with open(log_path, 'r') as f:
            saved_logs = json.load(f)
        self.assertEqual(len(saved_logs), len(drop_logs))

    def test_out_of_bounds_proportions(self):
        """Test handling of out-of-bounds proportion values."""
        # Create data with invalid proportions
        test_data = self.test_data.copy()
        test_data['forest_prop_100m'][0] = 1.5  # > 1
        
        df = pd.DataFrame(test_data)
        test_input = os.path.join(self.temp_dir, 'merged_oob.csv')
        df.to_csv(test_input, index=False)
        
        loaded_df = load_merged_observations(test_input)
        parsed_df = parse_land_cover_proportions(loaded_df)
        
        profiles, drop_logs = aggregate_species_profiles(parsed_df, min_obs=2)
        
        # Check for out_of_bounds in drop logs
        oob_drops = [log for log in drop_logs if log.get('reason_code') == 'out_of_bounds']
        self.assertGreater(len(oob_drops), 0)

if __name__ == '__main__':
    unittest.main()