import os
import sys
import unittest
import tempfile
import json
import pandas as pd
from pathlib import Path

# Add code directory to path for imports
code_dir = Path(__file__).parent.parent
sys.path.insert(0, str(code_dir))

from data.aggregate import (
    load_merged_observations,
    parse_land_cover_proportions,
    aggregate_species_profiles,
    save_species_profiles
)
from utils.config import get_processed_dir, get_raw_data_dir


class TestAggregate(unittest.TestCase):
    """Unit tests for T016 aggregate.py"""

    def setUp(self):
        """Set up temporary directories and mock data for testing."""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.processed_dir = Path(self.temp_dir.name)
        
        # Mock the config functions to use our temp dir
        # We will directly pass paths to functions in tests rather than relying on global config
        
        # Create mock merged_observations.csv
        self.mock_merged_path = self.processed_dir / 'merged_observations.csv'
        mock_data = {
            'species_id': ['sp1', 'sp1', 'sp2', 'sp3', 'sp3'],
            'foraging_guild': ['G1', 'G1', 'G2', 'G1', 'G1'],
            'land_cover_proportions': [
                '{"forest": 0.5, "grass": 0.5}',
                '{"forest": 0.6, "grass": 0.4}',
                '{"forest": 0.1, "grass": 0.9}',
                '{"forest": 0.8, "grass": 0.2}',
                '{"forest": 0.7, "grass": 0.3}'
            ]
        }
        self.mock_df = pd.DataFrame(mock_data)
        self.mock_df.to_csv(self.mock_merged_path, index=False)

    def tearDown(self):
        """Clean up temporary directory."""
        self.temp_dir.cleanup()

    def test_parse_land_cover_proportions(self):
        """Test that stringified JSON land cover proportions are parsed correctly."""
        df = self.mock_df.copy()
        parsed_df, lc_cols = parse_land_cover_proportions(df)
        
        self.assertIn('lc_forest', lc_cols)
        self.assertIn('lc_grass', lc_cols)
        self.assertEqual(len(parsed_df), 5)
        self.assertTrue('lc_forest' in parsed_df.columns)
        self.assertAlmostEqual(parsed_df.iloc[0]['lc_forest'], 0.5)

    def test_aggregate_species_profiles(self):
        """Test aggregation logic: mean calculation and dropping invalid rows."""
        df = self.mock_df.copy()
        parsed_df, lc_cols = parse_land_cover_proportions(df)
        
        aggregated_df, log_entry = aggregate_species_profiles(parsed_df, lc_cols)
        
        # Check aggregation
        # sp1 should have 3 rows: (0.5+0.6+0.8)/3 = 0.6333
        sp1_row = aggregated_df[aggregated_df['species_id'] == 'sp1'].iloc[0]
        self.assertAlmostEqual(sp1_row['lc_forest'], 0.6333, places=3)
        self.assertEqual(sp1_row['observation_count'], 3)
        
        # Check log entry
        self.assertEqual(log_entry['initial_observations'], 5)
        self.assertEqual(log_entry['final_species_profiles'], 3) # sp1, sp2, sp3
        self.assertEqual(log_entry['observations_dropped'], 0)

    def test_aggregate_drops_missing_values(self):
        """Test that rows with NaN in land cover columns are dropped."""
        df = self.mock_df.copy()
        # Insert a NaN row
        df.loc[len(df)] = ['sp4', 'G2', '{"forest": 0.5, "grass": null}']
        
        parsed_df, lc_cols = parse_land_cover_proportions(df)
        aggregated_df, log_entry = aggregate_species_profiles(parsed_df, lc_cols)
        
        self.assertEqual(log_entry['observations_dropped'], 1)
        self.assertTrue('missing land cover data' in log_entry['reasons'][0])
        self.assertNotIn('sp4', aggregated_df['species_id'].values)

    def test_save_species_profiles(self):
        """Test that output files are created correctly."""
        df = self.mock_df.copy()
        parsed_df, lc_cols = parse_land_cover_proportions(df)
        aggregated_df, log_entry = aggregate_species_profiles(parsed_df, lc_cols)
        
        output_path = save_species_profiles(aggregated_df, log_entry)
        
        self.assertTrue(os.path.exists(output_path))
        self.assertTrue(os.path.exists(self.processed_dir / 'aggregate_dropped_log.json'))
        
        # Verify content
        result_df = pd.read_csv(output_path)
        self.assertEqual(len(result_df), 3)

    def test_load_merged_observations_missing_file(self):
        """Test that FileNotFoundError is raised if input file is missing."""
        # Temporarily rename the file to simulate missing state
        self.mock_merged_path.rename(self.processed_dir / 'merged_observations.csv.bak')
        try:
            with self.assertRaises(FileNotFoundError):
                load_merged_observations()
        finally:
            # Restore
            (self.processed_dir / 'merged_observations.csv.bak').rename(self.mock_merged_path)


if __name__ == '__main__':
    unittest.main()