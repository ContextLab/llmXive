import os
import sys
import unittest
import tempfile
import json
import pandas as pd
from pathlib import Path

# Add project root to path if needed
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from data.aggregate import (
    load_merged_observations,
    parse_land_cover_proportions,
    aggregate_species_profiles,
    save_species_profiles
)

class TestAggregate(unittest.TestCase):
    
    def setUp(self):
        """Set up temporary directory for test files."""
        self.temp_dir = tempfile.mkdtemp()
        self.input_file = os.path.join(self.temp_dir, "merged_observations.csv")
        self.output_file = os.path.join(self.temp_dir, "species_profiles.csv")
        self.drop_log_file = os.path.join(self.temp_dir, "drop_log.json")
        
        # Create a sample merged observations DataFrame
        self.sample_data = pd.DataFrame({
            'species_id': ['A', 'A', 'B', 'B', 'C'],
            'foraging_guild': ['G1', 'G1', 'G2', 'G2', 'G1'],
            'observation_id': [1, 2, 3, 4, 5],
            'forest_prop': [0.5, 0.6, 0.2, 0.3, 0.4],
            'grassland_prop': [0.3, 0.2, 0.7, 0.6, 0.5],
            'urban_prop': [0.2, 0.2, 0.1, 0.1, 0.1]
        })
        
        # Save sample data
        self.sample_data.to_csv(self.input_file, index=False)
    
    def tearDown(self):
        """Clean up temporary directory."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_load_merged_observations(self):
        """Test loading merged observations from CSV."""
        df = load_merged_observations(self.input_file)
        self.assertEqual(len(df), 5)
        self.assertIn('species_id', df.columns)
        self.assertIn('forest_prop', df.columns)
    
    def test_parse_land_cover_proportions(self):
        """Test parsing land cover proportions."""
        df = load_merged_observations(self.input_file)
        # Add a row with NaN to test parsing
        df.loc[5] = ['D', 'G3', 6, None, 0.5, 0.5]
        
        parsed_df = parse_land_cover_proportions(df)
        self.assertTrue(pd.api.types.is_float_dtype(parsed_df['forest_prop']))
        self.assertTrue(parsed_df['forest_prop'].isna().iloc[5])
    
    def test_aggregate_species_profiles(self):
        """Test aggregation of species profiles."""
        df = load_merged_observations(self.input_file)
        profiles, stats = aggregate_species_profiles(df, self.drop_log_file)
        
        # Check that we have 3 unique species
        self.assertEqual(len(profiles), 3)
        
        # Check that species A has 2 observations
        species_a = profiles[profiles['species_id'] == 'A']
        self.assertEqual(species_a['observation_count'].values[0], 2)
        
        # Check that mean forest_prop for A is correct
        expected_forest = (0.5 + 0.6) / 2
        self.assertAlmostEqual(species_a['forest_prop'].values[0], expected_forest, places=5)
        
        # Check stats
        self.assertEqual(stats['dropped_count'], 0)
        self.assertEqual(stats['valid_count'], 5)
        self.assertEqual(stats['profile_count'], 3)
    
    def test_aggregate_with_missing_data(self):
        """Test aggregation with missing land cover data."""
        # Create data with missing values
        data_with_missing = pd.DataFrame({
            'species_id': ['A', 'A', 'B'],
            'foraging_guild': ['G1', 'G1', 'G2'],
            'observation_id': [1, 2, 3],
            'forest_prop': [0.5, None, 0.2],
            'grassland_prop': [0.3, 0.2, 0.7],
            'urban_prop': [0.2, 0.2, 0.1]
        })
        
        test_input = os.path.join(self.temp_dir, "test_missing.csv")
        data_with_missing.to_csv(test_input, index=False)
        
        df = load_merged_observations(test_input)
        profiles, stats = aggregate_species_profiles(df, self.drop_log_file)
        
        # Species A should be dropped because one row has NaN
        # So only species B remains
        self.assertEqual(len(profiles), 1)
        self.assertEqual(profiles['species_id'].values[0], 'B')
        
        # Check drop log
        self.assertTrue(os.path.exists(self.drop_log_file))
        with open(self.drop_log_file, 'r') as f:
            drop_log = json.load(f)
        self.assertEqual(len(drop_log), 1)
        self.assertEqual(drop_log[0]['species_id'], 'A')
    
    def test_save_species_profiles(self):
        """Test saving species profiles."""
        df = load_merged_observations(self.input_file)
        profiles, stats = aggregate_species_profiles(df, self.drop_log_file)
        
        save_species_profiles(profiles, self.output_file, stats)
        
        self.assertTrue(os.path.exists(self.output_file))
        saved_df = pd.read_csv(self.output_file)
        self.assertEqual(len(saved_df), 3)
        
        # Check stats file
        stats_file = self.output_file.replace('.csv', '_stats.json')
        self.assertTrue(os.path.exists(stats_file))
        with open(stats_file, 'r') as f:
            saved_stats = json.load(f)
        self.assertEqual(saved_stats['profile_count'], 3)

if __name__ == '__main__':
    unittest.main()