"""
Unit tests for T016: finalize_dataset.py
"""
import os
import sys
import json
import csv
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add code directory to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "code"))

from data.finalize_dataset import (
    load_processed_data,
    calculate_success_rate,
    save_post_filter_distribution,
    main
)

class TestFinalizeDataset(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.temp_path = Path(self.temp_dir.name)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_load_processed_data(self):
        """Test loading processed data from CSV."""
        csv_file = self.temp_path / "test.csv"
        with open(csv_file, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['smiles', 'rate_constant', 'substrate_class'])
            writer.writerow(['CCO', '1.0', 'secondary'])
            writer.writerow(['CC(C)O', '2.0', 'tertiary'])
        
        data = load_processed_data(csv_file)
        self.assertEqual(len(data), 2)
        self.assertEqual(data[0]['smiles'], 'CCO')
        self.assertEqual(data[1]['substrate_class'], 'tertiary')

    def test_load_processed_data_empty(self):
        """Test loading empty CSV."""
        csv_file = self.temp_path / "empty.csv"
        with open(csv_file, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['smiles', 'rate_constant', 'substrate_class'])
        
        data = load_processed_data(csv_file)
        self.assertEqual(len(data), 0)

    def test_load_processed_data_not_found(self):
        """Test loading non-existent file."""
        with self.assertRaises(FileNotFoundError):
            load_processed_data(self.temp_path / "nonexistent.csv")

    def test_calculate_success_rate(self):
        """Test success rate calculation."""
        self.assertAlmostEqual(calculate_success_rate(100, 95), 95.0)
        self.assertAlmostEqual(calculate_success_rate(100, 50), 50.0)
        self.assertAlmostEqual(calculate_success_rate(100, 100), 100.0)
        self.assertEqual(calculate_success_rate(100, 0), 0.0)
        self.assertEqual(calculate_success_rate(0, 0), 0.0) # Should handle division by zero

    def test_save_post_filter_distribution(self):
        """Test saving post-filter distribution."""
        data = [
            {'substrate_class': 'secondary'},
            {'substrate_class': 'tertiary'},
            {'substrate_class': 'secondary'},
            {'substrate_class': 'unknown'}
        ]
        output_file = self.temp_path / "distribution.json"
        save_post_filter_distribution(data, output_file)
        
        self.assertTrue(output_file.exists())
        with open(output_file, 'r') as f:
            dist = json.load(f)
        
        self.assertEqual(dist['secondary'], 2)
        self.assertEqual(dist['tertiary'], 1)
        self.assertEqual(dist['unknown'], 1)

    def test_main_success_rate_above_threshold(self):
        """Test main function with success rate above threshold."""
        # Create mock input data
        input_file = self.temp_path / "input.csv"
        with open(input_file, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['smiles', 'rate_constant', 'substrate_class'])
            for i in range(100):
                writer.writerow([f'CCO{i}', '1.0', 'secondary'])
        
        # Create mock exclusion report (0 exclusions)
        exclusion_file = self.temp_path / "exclusion_report.csv"
        with open(exclusion_file, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['row_index', 'reason', 'original_smiles'])
        
        # Patch paths
        with patch('data.finalize_dataset.PROCESSED_DIR', self.temp_path):
            with patch('data.finalize_dataset.INPUT_PATH', input_file):
                with patch('data.finalize_dataset.EXCLUSION_REPORT_PATH', exclusion_file):
                    with patch('data.finalize_dataset.OUTPUT_PATH', self.temp_path / "output.csv"):
                        with patch('data.finalize_dataset.CHECKSUM_PATH', self.temp_path / "output.csv.sha256"):
                            with patch('data.finalize_dataset.POST_FILTER_DIST_PATH', self.temp_path / "dist.json"):
                                # Run main with args to avoid sys.argv issues
                                with patch('sys.argv', ['finalize_dataset.py', '--input', str(input_file)]):
                                    try:
                                        main()
                                    except SystemExit as e:
                                        if e.code != 0:
                                            self.fail("main() exited with non-zero code unexpectedly")
        
        # Verify output files
        self.assertTrue((self.temp_path / "output.csv").exists())
        self.assertTrue((self.temp_path / "output.csv.sha256").exists())
        self.assertTrue((self.temp_path / "dist.json").exists())

    def test_main_success_rate_below_threshold(self):
        """Test main function with success rate below threshold."""
        # Create mock input data (small)
        input_file = self.temp_path / "input.csv"
        with open(input_file, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['smiles', 'rate_constant', 'substrate_class'])
            for i in range(10):
                writer.writerow([f'CCO{i}', '1.0', 'secondary'])
        
        # Create mock exclusion report (many exclusions -> low success rate)
        # Original count = 10 (input) + 90 (excluded) = 100
        # Final count = 10
        # Success rate = 10%
        exclusion_file = self.temp_path / "exclusion_report.csv"
        with open(exclusion_file, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['row_index', 'reason', 'original_smiles'])
            for i in range(90):
                writer.writerow([i, 'test_reason', 'test_smiles'])
        
        # Patch paths
        with patch('data.finalize_dataset.PROCESSED_DIR', self.temp_path):
            with patch('data.finalize_dataset.INPUT_PATH', input_file):
                with patch('data.finalize_dataset.EXCLUSION_REPORT_PATH', exclusion_file):
                    with patch('data.finalize_dataset.OUTPUT_PATH', self.temp_path / "output.csv"):
                        with patch('data.finalize_dataset.CHECKSUM_PATH', self.temp_path / "output.csv.sha256"):
                            with patch('data.finalize_dataset.POST_FILTER_DIST_PATH', self.temp_path / "dist.json"):
                                with patch('sys.argv', ['finalize_dataset.py', '--input', str(input_file)]):
                                    with self.assertRaises(SystemExit) as context:
                                        main()
                                    self.assertEqual(context.exception.code, 1)

if __name__ == '__main__':
    unittest.main()