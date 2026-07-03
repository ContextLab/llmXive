"""
Unit tests for data/aggregate.py
"""
import os
import sys
import unittest
import tempfile
import json
from pathlib import Path
import pandas as pd
import numpy as np

# Add project root to path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from data.aggregate import load_merged_observations, parse_land_cover_proportions, aggregate_species_profiles

class TestAggregate(unittest.TestCase):
    """Test cases for the aggregation module."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.test_data_path = Path(self.temp_dir.name) / 'test_merged.csv'
        
        # Create sample data
        sample_data = [
            {
                'species_id': 'sp001',
                'foraging_guild': 'ground_forager',
                'land_cover_proportions': {
                    'urban': 0.1,
                    'forest': 0.6,
                    'water': 0.0,
                    'agriculture': 0.3
                }
            },
            {
                'species_id': 'sp001',
                'foraging_guild': 'ground_forager',
                'land_cover_proportions': {
                    'urban': 0.2,
                    'forest': 0.5,
                    'water': 0.1,
                    'agriculture': 0.2
                }
            },
            {
                'species_id': 'sp002',
                'foraging_guild': 'aerial_forager',
                'land_cover_proportions': {
                    'urban': 0.5,
                    'forest': 0.2,
                    'water': 0.1,
                    'agriculture': 0.2
                }
            },
            {
                'species_id': 'sp002',
                'foraging_guild': 'aerial_forager',
                'land_cover_proportions': {
                    'urban': 0.6,
                    'forest': 0.1,
                    'water': 0.2,
                    'agriculture': 0.1
                }
            },
            {
                'species_id': 'sp002',
                'foraging_guild': 'aerial_forager',
                'land_cover_proportions': {
                    'urban': 0.4,
                    'forest': 0.3,
                    'water': 0.1,
                    'agriculture': 0.2
                }
            }
        ]
        
        df = pd.DataFrame(sample_data)
        df.to_csv(self.test_data_path, index=False)

    def tearDown(self):
        """Clean up test fixtures."""
        self.temp_dir.cleanup()

    def test_load_merged_observations(self):
        """Test loading merged observations."""
        df = load_merged_observations(self.test_data_path)
        self.assertEqual(len(df), 5)
        self.assertIn('species_id', df.columns)
        self.assertIn('foraging_guild', df.columns)
        self.assertIn('land_cover_proportions', df.columns)

    def test_parse_land_cover_proportions(self):
        """Test parsing land cover proportions."""
        df = load_merged_observations(self.test_data_path)
        lc_df = parse_land_cover_proportions(df['land_cover_proportions'])
        
        self.assertEqual(len(lc_df), 5)
        self.assertIn('urban', lc_df.columns)
        self.assertIn('forest', lc_df.columns)
        self.assertIn('water', lc_df.columns)
        self.assertIn('agriculture', lc_df.columns)
        
        # Check that values are numeric
        self.assertTrue(np.issubdtype(lc_df['urban'].dtype, np.number))

    def test_aggregate_species_profiles(self):
        """Test species profile aggregation."""
        df = load_merged_observations(self.test_data_path)
        profiles = aggregate_species_profiles(df)
        
        # Should have 2 species
        self.assertEqual(len(profiles), 2)
        
        # Check that species_id is present
        self.assertIn('species_id', profiles.columns)
        self.assertIn('foraging_guild', profiles.columns)
        self.assertIn('observation_count', profiles.columns)
        
        # Check observation counts
        sp001_count = profiles[profiles['species_id'] == 'sp001']['observation_count'].iloc[0]
        sp002_count = profiles[profiles['species_id'] == 'sp002']['observation_count'].iloc[0]
        
        self.assertEqual(sp001_count, 2)
        self.assertEqual(sp002_count, 3)
        
        # Check that mean land cover proportions are calculated
        sp001_urban_mean = profiles[profiles['species_id'] == 'sp001']['urban_mean'].iloc[0]
        expected_urban_mean = (0.1 + 0.2) / 2
        self.assertAlmostEqual(sp001_urban_mean, expected_urban_mean, places=5)

    def test_aggregation_sorting(self):
        """Test that profiles are sorted by observation count descending."""
        df = load_merged_observations(self.test_data_path)
        profiles = aggregate_species_profiles(df)
        
        counts = profiles['observation_count'].values
        self.assertTrue(all(counts[i] >= counts[i+1] for i in range(len(counts)-1)))

if __name__ == '__main__':
    unittest.main()