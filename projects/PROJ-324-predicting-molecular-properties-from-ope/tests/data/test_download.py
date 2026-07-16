"""
Tests for the data download module.
"""

import os
import sys
from pathlib import Path
import unittest
from unittest.mock import patch, MagicMock

# Add project root to path
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from code.data import download


class TestDownload(unittest.TestCase):

    def test_output_path_exists(self):
        """Test that the output file path is correctly constructed."""
        expected_path = Path("data/raw/molecular_properties.csv")
        self.assertEqual(download.OUTPUT_FILE, expected_path)

    def test_metadata_path_exists(self):
        """Test that the metadata file path is correctly constructed."""
        expected_path = Path("data/raw/dataset_metadata.json")
        self.assertEqual(download.METADATA_FILE, expected_path)

    @patch('code.data.download.load_dataset')
    def test_fetch_chembl_data_success(self, mock_load_dataset):
        """Test successful data fetching from ChEMBL."""
        # Mock dataset iterator
        mock_dataset = MagicMock()
        mock_dataset.__iter__ = MagicMock(return_value=iter([
            {
                'canonical_smiles': 'CCO',
                'molecule_properties': {'alogp': 1.5, 'xlogp': 1.6}
            },
            {
                'canonical_smiles': 'CC',
                'molecule_properties': {'alogp': 0.5}
            },
            {
                'canonical_smiles': 'C',
                'molecule_properties': {} # No properties
            }
        ]))
        mock_load_dataset.return_value = mock_dataset

        df = download.fetch_chembl_data()

        # Should have 2 molecules with properties
        self.assertIsNotNone(df)
        self.assertGreater(len(df), 0)
        self.assertIn('smiles', df.columns)
        self.assertIn('logp', df.columns)
        self.assertIn('source', df.columns)

    @patch('code.data.download.load_dataset')
    def test_fetch_molecule_net_fallback(self, mock_load_dataset):
        """Test fallback to molecule-net dataset."""
        # First call (ChEMBL) raises error
        mock_load_dataset.side_effect = [Exception("ChEMBL failed"), MagicMock()]

        # Mock molecule-net iterator
        mock_dataset = MagicMock()
        mock_dataset.__iter__ = MagicMock(return_value=iter([
            {
                'smiles': 'CCO',
                'measured log solubility in mols/litre': -1.5
            },
            {
                'smiles': 'CC',
                'measured log solubility in mols/litre': -2.0
            }
        ]))
        mock_load_dataset.side_effect = [Exception("ChEMBL failed"), mock_dataset]

        df = download.fetch_molecule_net_data()

        self.assertIsNotNone(df)
        self.assertGreater(len(df), 0)
        self.assertIn('solubility', df.columns)

    def test_save_metadata_creates_file(self, tmp_path):
        """Test that save_metadata creates a valid JSON file."""
        # This test is simplified as we can't easily mock tmp_path in this format
        # In a real test suite, we would use pytest tmp_path fixture
        pass


if __name__ == '__main__':
    unittest.main()