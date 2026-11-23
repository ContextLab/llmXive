"""
Tests for Synthetic Data Generation (T013).
"""
import os
import json
import csv
import tempfile
import shutil
from pathlib import Path
import unittest

# Add project root to path
project_root = Path(__file__).resolve().parent.parent
import sys
sys.path.insert(0, str(project_root / 'code'))

from generators.synthetic_data_generator import generate_synthetic_data, load_pristine_references

class TestSyntheticGeneration(unittest.TestCase):

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.original_cwd = os.getcwd()
        os.chdir(self.temp_dir)
        
        # Create necessary directory structure
        os.makedirs('data/raw', exist_ok=True)
        os.makedirs('data/state', exist_ok=True)

    def tearDown(self):
        """Tear down test fixtures."""
        os.chdir(self.original_cwd)
        shutil.rmtree(self.temp_dir)

    def test_generate_synthetic_data_count(self):
        """Test that the correct number of samples is generated."""
        n_samples = 100
        data = generate_synthetic_data(n_samples, seed=42)
        self.assertEqual(len(data), n_samples)

    def test_generate_synthetic_data_fields(self):
        """Test that all required fields are present in generated data."""
        required_fields = [
            'defect_id', 'defect_type', 'defect_density', 
            'conductivity', 'elastic_tensor', 'fracture_energy',
            'material', 'synthesis_method', 'grain_size'
        ]
        data = generate_synthetic_data(10, seed=42)
        self.assertGreater(len(data), 0)
        for row in data:
            for field in required_fields:
                self.assertIn(field, row, f"Missing field: {field}")

    def test_generate_synthetic_data_physical_bounds(self):
        """Test that generated values are within physical bounds (non-negative)."""
        data = generate_synthetic_data(100, seed=42)
        for row in data:
            self.assertGreaterEqual(float(row['conductivity']), 0.0)
            self.assertGreaterEqual(float(row['elastic_tensor']), 0.0)
            self.assertGreaterEqual(float(row['fracture_energy']), 0.0)
            density = float(row['defect_density'])
            self.assertGreaterEqual(density, 0.0)
            self.assertLessEqual(density, 1.0) # Density should be <= 1

    def test_generate_synthetic_data_reproducibility(self):
        """Test that generation is reproducible with the same seed."""
        data1 = generate_synthetic_data(10, seed=123)
        data2 = generate_synthetic_data(10, seed=123)
        self.assertEqual(data1, data2)

    def test_generate_synthetic_data_different_seeds(self):
        """Test that different seeds produce different data."""
        data1 = generate_synthetic_data(10, seed=123)
        data2 = generate_synthetic_data(10, seed=456)
        self.assertNotEqual(data1, data2)

    def test_load_pristine_references_defaults(self):
        """Test that default references are loaded when file is missing."""
        refs = load_pristine_references()
        self.assertIn('conductivity_0', refs)
        self.assertIn('youngs_modulus_0', refs)
        self.assertIn('fracture_strength_0', refs)
        self.assertGreater(refs['conductivity_0'], 0)
        self.assertGreater(refs['youngs_modulus_0'], 0)
        self.assertGreater(refs['fracture_strength_0'], 0)

if __name__ == '__main__':
    unittest.main()