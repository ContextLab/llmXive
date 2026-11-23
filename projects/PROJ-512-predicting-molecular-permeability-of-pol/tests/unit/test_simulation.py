"""
Unit tests for the PolyPerme Simulation Generator (T009a).
"""
import os
import sys
import tempfile
import csv
import unittest

# Add project root to path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from data.simulation import generate_polymer_graphs, save_simulation_data, _calculate_log_permeability
from data.utils import set_seed

class TestSimulationGenerator(unittest.TestCase):
    def setUp(self):
        set_seed(42)
        self.test_dir = tempfile.mkdtemp()

    def test_generate_polymer_graphs_count(self):
        """Test that the correct number of records is generated."""
        count = 50
        records = generate_polymer_graphs(count=count)
        self.assertEqual(len(records), count)

    def test_generate_polymer_graphs_structure(self):
        """Test that generated records have the required fields."""
        records = generate_polymer_graphs(count=10)
        required_fields = ['id', 'smiles', 'molecular_weight', 'num_atoms', 'log_permeability', 'source']
        
        for record in records:
            for field in required_fields:
                self.assertIn(field, record, f"Missing field: {field}")
            
            # Validate types
            self.assertIsInstance(record['id'], str)
            self.assertIsInstance(record['smiles'], str)
            self.assertIsInstance(record['molecular_weight'], float)
            self.assertIsInstance(record['num_atoms'], int)
            self.assertIsInstance(record['log_permeability'], float)
            self.assertEqual(record['source'], 'simulation')
            
            # Validate constraints
            self.assertGreater(record['molecular_weight'], 0)
            self.assertGreater(record['num_atoms'], 0)
            self.assertGreaterEqual(len(record['smiles']), 1)

    def test_save_simulation_data(self):
        """Test that data is saved correctly to CSV."""
        output_path = os.path.join(self.test_dir, 'test_simulation.csv')
        records = generate_polymer_graphs(count=20)
        
        save_simulation_data(records, output_path)
        
        # Verify file exists
        self.assertTrue(os.path.exists(output_path))
        
        # Verify content
        with open(output_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            
        self.assertEqual(len(rows), 20)
        
        # Check header
        expected_fields = ['id', 'smiles', 'molecular_weight', 'num_atoms', 'log_permeability', 'source']
        self.assertEqual(reader.fieldnames, expected_fields)

    def test_log_permeability_calculation(self):
        """Test the log permeability calculation logic."""
        # Simple test case
        mw = 100.0
        num_atoms = 10
        node_features = [{'hybridization': 'SP3'} for _ in range(10)]
        
        log_p = _calculate_log_permeability(mw, num_atoms, node_features)
        
        self.assertIsInstance(log_p, float)
        # Should be a reasonable value (not NaN or Inf)
        self.assertTrue(-100 < log_p < 100)

if __name__ == '__main__':
    unittest.main()