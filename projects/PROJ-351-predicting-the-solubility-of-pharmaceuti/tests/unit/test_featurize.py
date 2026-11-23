"""
Unit tests for T012a: code/data/featurize.py
"""
import os
import sys
import unittest
import tempfile
import pickle
from pathlib import Path
from unittest.mock import patch, MagicMock

import numpy as np

# Add project root to path
project_root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(project_root))

from data.featurize import (
    generate_morgan_fingerprint,
    featurize_dataset,
    load_cleaned_data,
    save_featurized_data
)

class TestFeaturize(unittest.TestCase):

    def test_generate_morgan_fingerprint_valid(self):
        """Test fingerprint generation for a valid SMILES string."""
        smiles = "CCO"  # Ethanol
        fp = generate_morgan_fingerprint(smiles, radius=2, n_bits=2048)
        self.assertEqual(fp.shape, (2048,))
        self.assertTrue(np.all((fp == 0) | (fp == 1)))

    def test_generate_morgan_fingerprint_invalid(self):
        """Test fingerprint generation raises error for invalid SMILES."""
        with self.assertRaises(ValueError):
            generate_morgan_fingerprint("INVALID_SMILES", radius=2, n_bits=2048)

    def test_featurize_dataset(self):
        """Test the full featurization pipeline on a small dataset."""
        mock_data = [
            {"smiles": "CCO", "logS": -0.5},
            {"smiles": "CCCCO", "logS": -1.2},
            {"smiles": "c1ccccc1", "logS": -2.1}
        ]
        
        X, y = featurize_dataset(mock_data)
        
        self.assertEqual(X.shape, (3, 2048))
        self.assertEqual(y.shape, (3,))
        self.assertTrue(np.all((X == 0) | (X == 1)))

    def test_featurize_dataset_skips_invalid(self):
        """Test that featurize_dataset skips invalid entries without crashing."""
        mock_data = [
            {"smiles": "CCO", "logS": -0.5},
            {"smiles": None, "logS": -1.0},  # Missing SMILES
            {"smiles": "CCO", "logS": None},  # Missing logS
            {"smiles": "INVALID", "logS": -1.0},  # Invalid SMILES
            {"smiles": "CCCC", "logS": -0.8}
        ]
        
        X, y = featurize_dataset(mock_data)
        
        # Should have 2 valid entries
        self.assertEqual(X.shape[0], 2)
        self.assertEqual(y.shape[0], 2)

    def test_save_featurized_data(self):
        """Test saving and loading the NPZ file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test_fingerprints.npz"
            X = np.random.randint(0, 2, (10, 128))
            y = np.array([1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0])
            
            save_featurized_data(X, y, output_path)
            
            self.assertTrue(output_path.exists())
            self.assertGreater(output_path.stat().st_size, 0)
            
            # Load and verify
            loaded = np.load(output_path)
            self.assertTrue(np.array_equal(loaded['features'], X))
            self.assertTrue(np.array_equal(loaded['targets'], y))

    @patch('data.featurize.setup_logging')
    def test_load_cleaned_data(self, mock_logger):
        """Test loading cleaned data from pickle."""
        with tempfile.TemporaryDirectory() as tmpdir:
            input_path = Path(tmpdir) / "cleaned_graphs.pkl"
            mock_data = [{"smiles": "CCO", "logS": -0.5}]
            
            with open(input_path, 'wb') as f:
                pickle.dump(mock_data, f)
            
            loaded = load_cleaned_data(input_path)
            self.assertEqual(loaded, mock_data)

    def test_load_cleaned_data_missing_file(self):
        """Test that loading missing file raises FileNotFoundError."""
        with self.assertRaises(FileNotFoundError):
            load_cleaned_data(Path("non_existent_file.pkl"))

if __name__ == "__main__":
    unittest.main()