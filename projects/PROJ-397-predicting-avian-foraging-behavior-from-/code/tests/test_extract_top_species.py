import os
import sys
import unittest
import tempfile
import json
from pathlib import Path
import pandas as pd

# Ensure project root is in path
project_root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(project_root))

from data.extract_top_species import extract_top_species, save_top_species, load_species_profiles

class TestExtractTopSpecies(unittest.TestCase):
    
    def setUp(self):
        """Set up test fixtures."""
        self.test_data = pd.DataFrame({
            'species_id': ['sp1', 'sp2', 'sp3', 'sp4', 'sp5'],
            'observation_count': [100, 90, 80, 70, 60],
            'other_col': ['a', 'b', 'c', 'd', 'e']
        })
    
    def test_extract_top_n_basic(self):
        """Test extracting top N species without ties."""
        result = extract_top_species(self.test_data, n=3)
        
        self.assertEqual(len(result), 3)
        self.assertEqual(result[0]['species_id'], 'sp1')
        self.assertEqual(result[0]['observation_count'], 100)
        self.assertEqual(result[2]['species_id'], 'sp3')
        self.assertEqual(result[2]['observation_count'], 80)
    
    def test_extract_top_n_with_ties(self):
        """Test extracting top N species with ties at the cutoff."""
        tied_data = pd.DataFrame({
            'species_id': ['sp1', 'sp2', 'sp3', 'sp4', 'sp5'],
            'observation_count': [100, 90, 80, 80, 60],
        })
        
        result = extract_top_species(tied_data, n=3)
        
        # Should include both sp3 and sp4 because they are tied at rank 3
        self.assertEqual(len(result), 4)
        species_ids = [r['species_id'] for r in result]
        self.assertIn('sp3', species_ids)
        self.assertIn('sp4', species_ids)
    
    def test_extract_fewer_than_n(self):
        """Test when there are fewer species than requested N."""
        small_data = pd.DataFrame({
            'species_id': ['sp1', 'sp2'],
            'observation_count': [100, 90],
        })
        
        result = extract_top_species(small_data, n=5)
        
        self.assertEqual(len(result), 2)
    
    def test_extract_empty_dataframe(self):
        """Test with an empty dataframe."""
        empty_data = pd.DataFrame(columns=['species_id', 'observation_count'])
        
        result = extract_top_species(empty_data, n=5)
        
        self.assertEqual(len(result), 0)
    
    def test_extract_single_species(self):
        """Test with a single species."""
        single_data = pd.DataFrame({
            'species_id': ['sp1'],
            'observation_count': [100],
        })
        
        result = extract_top_species(single_data, n=5)
        
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['species_id'], 'sp1')

if __name__ == '__main__':
    unittest.main()