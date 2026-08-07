"""
Unit tests for data preprocessing logic (T010).
"""
import csv
import os
import tempfile
from pathlib import Path
import unittest
from unittest.mock import patch, MagicMock

# Import the module under test
# We need to adjust the import path to match the project structure
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / 'code'))

from data.preprocessing import load_raw_data, preprocess_data, write_clean_data

class TestPreprocessing(unittest.TestCase):

    def setUp(self):
        """Set up temporary files and directories for testing."""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.raw_data_path = Path(self.temp_dir.name) / "raw.csv"
        self.filtered_data_path = Path(self.temp_dir.name) / "filtered.csv"

    def tearDown(self):
        """Clean up temporary files."""
        self.temp_dir.cleanup()

    def _create_raw_csv(self, rows):
        """Helper to create a raw CSV file with given rows."""
        with open(self.raw_data_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=['smiles', 'logPapp', 'assay_id'])
            writer.writeheader()
            writer.writerows(rows)

    def test_load_raw_data(self):
        """Test loading raw data from CSV."""
        rows = [
            {'smiles': 'CCO', 'logPapp': '-4.5', 'assay_id': '1'},
            {'smiles': 'CCC', 'logPapp': '-5.0', 'assay_id': '2'}
        ]
        self._create_raw_csv(rows)

        # Mock get_project_root to return temp dir
        with patch('data.preprocessing.get_project_root', return_value=Path(self.temp_dir.name)):
            with patch('data.preprocessing.RAW_DATA_PATH', 'raw.csv'):
                data = load_raw_data()
                self.assertEqual(len(data), 2)
                self.assertEqual(data[0]['smiles'], 'CCO')
                self.assertEqual(data[1]['logPapp'], '-5.0')

    def test_preprocess_data_filters_missing_smiles(self):
        """Test that records with missing SMILES are excluded."""
        rows = [
            {'smiles': 'CCO', 'logPapp': '-4.5', 'assay_id': '1'},
            {'smiles': '', 'logPapp': '-5.0', 'assay_id': '2'},
            {'smiles': '   ', 'logPapp': '-5.0', 'assay_id': '3'}
        ]
        self._create_raw_csv(rows)

        with patch('data.preprocessing.get_project_root', return_value=Path(self.temp_dir.name)):
            with patch('data.preprocessing.RAW_DATA_PATH', 'raw.csv'):
                raw_data = load_raw_data()
                filtered = preprocess_data(raw_data)

                self.assertEqual(len(filtered), 1)
                self.assertEqual(filtered[0]['smiles'], 'CCO')

    def test_preprocess_data_filters_missing_logpapp(self):
        """Test that records with missing logPapp are excluded."""
        rows = [
            {'smiles': 'CCO', 'logPapp': '-4.5', 'assay_id': '1'},
            {'smiles': 'CCC', 'logPapp': '', 'assay_id': '2'},
            {'smiles': 'CCN', 'logPapp': '   ', 'assay_id': '3'}
        ]
        self._create_raw_csv(rows)

        with patch('data.preprocessing.get_project_root', return_value=Path(self.temp_dir.name)):
            with patch('data.preprocessing.RAW_DATA_PATH', 'raw.csv'):
                raw_data = load_raw_data()
                filtered = preprocess_data(raw_data)

                self.assertEqual(len(filtered), 1)
                self.assertEqual(filtered[0]['smiles'], 'CCO')

    def test_preprocess_data_filters_invalid_logpapp(self):
        """Test that records with invalid logPapp values are excluded."""
        rows = [
            {'smiles': 'CCO', 'logPapp': '-4.5', 'assay_id': '1'},
            {'smiles': 'CCC', 'logPapp': 'not_a_number', 'assay_id': '2'},
            {'smiles': 'CCN', 'logPapp': 'NaN', 'assay_id': '3'}
        ]
        self._create_raw_csv(rows)

        with patch('data.preprocessing.get_project_root', return_value=Path(self.temp_dir.name)):
            with patch('data.preprocessing.RAW_DATA_PATH', 'raw.csv'):
                raw_data = load_raw_data()
                filtered = preprocess_data(raw_data)

                self.assertEqual(len(filtered), 1)
                self.assertEqual(filtered[0]['smiles'], 'CCO')

    def test_preprocess_data_pass_rate(self):
        """Test that pass rate is calculated correctly."""
        rows = [
            {'smiles': 'CCO', 'logPapp': '-4.5', 'assay_id': '1'},
            {'smiles': 'CCC', 'logPapp': '-5.0', 'assay_id': '2'},
            {'smiles': '', 'logPapp': '-5.0', 'assay_id': '3'},
            {'smiles': 'CCN', 'logPapp': '', 'assay_id': '4'}
        ]
        self._create_raw_csv(rows)

        with patch('data.preprocessing.get_project_root', return_value=Path(self.temp_dir.name)):
            with patch('data.preprocessing.RAW_DATA_PATH', 'raw.csv'):
                raw_data = load_raw_data()
                filtered = preprocess_data(raw_data)

                # 4 total, 2 excluded, 2 passed -> 50% pass rate
                self.assertEqual(len(filtered), 2)

    def test_write_clean_data(self):
        """Test writing filtered data to CSV."""
        data = [
            {'smiles': 'CCO', 'logPapp': '-4.5', 'assay_id': '1'},
            {'smiles': 'CCC', 'logPapp': '-5.0', 'assay_id': '2'}
        ]

        write_clean_data(data, self.filtered_data_path)

        self.assertTrue(self.filtered_data_path.exists())

        with open(self.filtered_data_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0]['smiles'], 'CCO')
        self.assertEqual(rows[1]['logPapp'], '-5.0')

    def test_write_clean_data_empty(self):
        """Test writing empty data creates an empty file."""
        write_clean_data([], self.filtered_data_path)

        self.assertTrue(self.filtered_data_path.exists())
        self.assertEqual(self.filtered_data_path.stat().st_size, 0)

if __name__ == '__main__':
    unittest.main()