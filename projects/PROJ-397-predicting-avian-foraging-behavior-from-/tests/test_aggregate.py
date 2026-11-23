"""
Unit tests for the data/aggregate.py module.
"""
import os
import sys
import unittest
import tempfile
import json
import pandas as pd
from pathlib import Path
from unittest.mock import patch, MagicMock
import shutil

# Add code directory to path
code_root = Path(__file__).parent.parent
sys.path.insert(0, str(code_root))

from data.aggregate import (
    load_merged_observations,
    parse_land_cover_proportions,
    aggregate_species_profiles,
    save_species_profiles,
    main
)
from utils.config import get_processed_dir, get_data_dir, get_file_path

class TestAggregate(unittest.TestCase):
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.processed_dir = Path(self.temp_dir) / "processed"
        self.processed_dir.mkdir()
        
        # Mock config functions to use temp dir
        self.patcher_get_processed = patch(
            'utils.config.get_processed_dir',
            return_value=self.processed_dir
        )
        self.patcher_get_processed.start()
        
        self.patcher_get_data = patch(
            'utils.config.get_data_dir',
            return_value=Path(self.temp_dir)
        )
        self.patcher_get_data.start()

    def tearDown(self):
        """Clean up test fixtures."""
        self.patcher_get_processed.stop()
        self.patcher_get_data.stop()
        shutil.rmtree(self.temp_dir)

    def test_load_merged_observations_file_not_found(self):
        """Test that FileNotFoundError is raised if input file is missing."""
        with self.assertRaises(FileNotFoundError):
            load_merged_observations()

    def test_load_merged_observations_empty_file(self):
        """Test that ValueError is raised if input file is empty."""
        empty_csv = self.processed_dir / "merged_observations.csv"
        empty_csv.touch()
        
        with self.assertRaises(ValueError):
            load_merged_observations()

    def test_load_merged_observations_missing_columns(self):
        """Test that ValueError is raised if required columns are missing."""
        df = pd.DataFrame({'species_id': ['A', 'B']}) # Missing land cover cols
        csv_path = self.processed_dir / "merged_observations.csv"
        df.to_csv(csv_path, index=False)
        
        with self.assertRaises(ValueError):
            load_merged_observations()

    def test_load_merged_observations_success(self):
        """Test successful loading of merged observations."""
        # Create a valid mock dataframe
        data = {
            'species_id': ['Sp1', 'Sp2', 'Sp1'],
            'foraging_guild': ['Ground', 'Canopy', 'Ground'],
            'forest_prop_100m': [0.8, 0.2, 0.7],
            'grassland_prop_100m': [0.1, 0.3, 0.2],
            'wetland_prop_100m': [0.0, 0.4, 0.0],
            'urban_prop_100m': [0.1, 0.1, 0.1],
            'other_prop_100m': [0.0, 0.0, 0.0]
        }
        df = pd.DataFrame(data)
        csv_path = self.processed_dir / "merged_observations.csv"
        df.to_csv(csv_path, index=False)
        
        loaded_df = load_merged_observations()
        self.assertEqual(len(loaded_df), 3)
        self.assertIn('forest_prop_100m', loaded_df.columns)

    def test_parse_land_cover_proportions(self):
        """Test identification of land cover proportion columns."""
        data = {
            'species_id': ['A'],
            'foraging_guild': ['G'],
            'forest_prop_100m': [0.5],
            'grassland_prop_100m': [0.5],
            'wetland_prop_100m': [0.0],
            'urban_prop_100m': [0.0],
            'other_prop_100m': [0.0],
            'extra_col': [1]
        }
        df = pd.DataFrame(data)
        
        lc_cols = parse_land_cover_proportions(df)
        expected = ['forest_prop_100m', 'grassland_prop_100m', 'wetland_prop_100m', 
                  'urban_prop_100m', 'other_prop_100m']
        self.assertEqual(sorted(lc_cols), sorted(expected))

    def test_aggregate_species_profiles_basic(self):
        """Test basic aggregation of species profiles."""
        data = {
            'species_id': ['Sp1', 'Sp2', 'Sp1'],
            'foraging_guild': ['Ground', 'Canopy', 'Ground'],
            'forest_prop_100m': [0.8, 0.2, 0.6],
            'grassland_prop_100m': [0.1, 0.3, 0.2],
            'wetland_prop_100m': [0.0, 0.4, 0.0],
            'urban_prop_100m': [0.1, 0.1, 0.2],
            'other_prop_100m': [0.0, 0.0, 0.0]
        }
        df = pd.DataFrame(data)
        
        profiles, log_entries = aggregate_species_profiles(df)
        
        # Check Sp1: mean forest = (0.8+0.6)/2 = 0.7
        sp1_row = profiles[profiles['species_id'] == 'Sp1']
        self.assertEqual(len(sp1_row), 1)
        self.assertAlmostEqual(sp1_row['forest_prop_100m'].values[0], 0.7, places=5)
        self.assertEqual(sp1_row['foraging_guild'].values[0], 'Ground')
        
        # Check log entries (should be empty for valid data)
        self.assertEqual(len(log_entries), 0)

    def test_aggregate_species_profiles_missing_data(self):
        """Test handling of missing land cover data."""
        data = {
            'species_id': ['Sp1', 'Sp2', 'Sp1'],
            'foraging_guild': ['Ground', 'Canopy', 'Ground'],
            'forest_prop_100m': [0.8, 0.2, None],
            'grassland_prop_100m': [0.1, 0.3, 0.2],
            'wetland_prop_100m': [0.0, 0.4, 0.0],
            'urban_prop_100m': [0.1, 0.1, 0.2],
            'other_prop_100m': [0.0, 0.0, 0.0]
        }
        df = pd.DataFrame(data)
        
        profiles, log_entries = aggregate_species_profiles(df)
        
        # Sp1 should be dropped because of missing value in the second row
        # Wait, the aggregation drops rows with ANY missing value BEFORE grouping
        # So Sp1 only has 1 row left (0.8), Sp2 has 1 row
        # Actually, the code drops rows with missing values first.
        # Row 2 (Sp1) has None in forest_prop_100m -> dropped.
        # Remaining: Row 0 (Sp1, 0.8), Row 1 (Sp2, 0.2)
        # Aggregation: Sp1 -> 0.8, Sp2 -> 0.2
        
        self.assertEqual(len(profiles), 2)
        self.assertEqual(len(log_entries), 1)
        self.assertEqual(log_entries[0]['reason_code'], 'MISSING_LANDCOVER')

    def test_save_species_profiles(self):
        """Test saving species profiles to CSV and log."""
        data = {
            'species_id': ['Sp1', 'Sp2'],
            'foraging_guild': ['Ground', 'Canopy'],
            'forest_prop_100m': [0.7, 0.2],
            'grassland_prop_100m': [0.1, 0.3],
            'wetland_prop_100m': [0.0, 0.4],
            'urban_prop_100m': [0.2, 0.1],
            'other_prop_100m': [0.0, 0.0],
            'observation_count': [2, 1]
        }
        df = pd.DataFrame(data)
        
        save_species_profiles(df, [])
        
        # Check files exist
        csv_path = self.processed_dir / "species_profiles.csv"
        log_path = self.processed_dir / "aggregate_log.json"
        
        self.assertTrue(csv_path.exists())
        self.assertTrue(log_path.exists())
        
        # Verify content
        saved_df = pd.read_csv(csv_path)
        self.assertEqual(len(saved_df), 2)
        self.assertIn('Sp1', saved_df['species_id'].values)

if __name__ == '__main__':
    unittest.main()