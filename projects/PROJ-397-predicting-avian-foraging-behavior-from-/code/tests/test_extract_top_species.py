"""
Unit tests for the extract_top_species functionality.
"""
import os
import sys
import unittest
import tempfile
import json
from pathlib import Path
import pandas as pd

# Add project root to path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from data.extract_top_species import load_species_profiles, extract_top_species, save_top_species

class TestExtractTopSpecies(unittest.TestCase):
    """Test cases for extract_top_species module."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.test_profiles_path = Path(self.temp_dir) / 'test_profiles.csv'
        self.test_output_path = Path(self.temp_dir) / 'test_top_species.json'

        # Create sample data
        self.sample_data = [
            {'species_id': 'A', 'observation_count': 1000, 'foraging_guild': 'Ground'},
            {'species_id': 'B', 'observation_count': 800, 'foraging_guild': 'Canopy'},
            {'species_id': 'C', 'observation_count': 500, 'foraging_guild': 'Ground'},
            {'species_id': 'D', 'observation_count': 200, 'foraging_guild': 'Midstory'},
            {'species_id': 'E', 'observation_count': 50, 'foraging_guild': 'Canopy'},
        ]
        df = pd.DataFrame(self.sample_data)
        df.to_csv(self.test_profiles_path, index=False)

    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_load_species_profiles(self):
        """Test loading species profiles from CSV."""
        profiles = load_species_profiles(self.test_profiles_path)
        self.assertEqual(len(profiles), 5)
        self.assertIn('species_id', profiles[0])
        self.assertIn('observation_count', profiles[0])

    def test_extract_top_species_count(self):
        """Test extracting top N species."""
        profiles = load_species_profiles(self.test_profiles_path)
        top_3 = extract_top_species(profiles, top_n=3)
        self.assertEqual(len(top_3), 3)

    def test_extract_top_species_order(self):
        """Test that top species are sorted by observation count descending."""
        profiles = load_species_profiles(self.test_profiles_path)
        top_3 = extract_top_species(profiles, top_n=3)
        counts = [p['observation_count'] for p in top_3]
        self.assertEqual(counts, sorted(counts, reverse=True))

    def test_extract_top_species_values(self):
        """Test that the correct species are selected."""
        profiles = load_species_profiles(self.test_profiles_path)
        top_3 = extract_top_species(profiles, top_n=3)
        species_ids = [p['species_id'] for p in top_3]
        self.assertIn('A', species_ids)
        self.assertIn('B', species_ids)
        self.assertIn('C', species_ids)
        self.assertNotIn('D', species_ids)
        self.assertNotIn('E', species_ids)

    def test_save_top_species(self):
        """Test saving top species to JSON."""
        profiles = load_species_profiles(self.test_profiles_path)
        top_species = extract_top_species(profiles, top_n=3)
        save_top_species(top_species, self.test_output_path)

        self.assertTrue(self.test_output_path.exists())

        with open(self.test_output_path, 'r') as f:
            data = json.load(f)

        self.assertIn('species', data)
        self.assertEqual(len(data['species']), 3)
        self.assertIn('metadata', data)

    def test_extract_all_species(self):
        """Test extracting all species when top_n >= total."""
        profiles = load_species_profiles(self.test_profiles_path)
        top_all = extract_top_species(profiles, top_n=10)
        self.assertEqual(len(top_all), 5)

    def test_extract_empty_list(self):
        """Test handling of empty profile list."""
        profiles = []
        top = extract_top_species(profiles, top_n=5)
        self.assertEqual(len(top), 0)

if __name__ == '__main__':
    unittest.main()