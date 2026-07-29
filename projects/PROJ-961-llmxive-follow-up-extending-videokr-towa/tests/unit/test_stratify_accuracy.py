"""
Unit tests for accuracy calculation logic in code/analysis/stratify_accuracy.py.
"""
import unittest
import csv
import tempfile
import os
import json
from pathlib import Path
import sys

sys.path.insert(0, 'code')

from analysis.stratify_accuracy import (
    load_annotated_data,
    bin_hop_length,
    calculate_accuracy_by_bin,
    write_results
)


class TestStratifyAccuracy(unittest.TestCase):
    """Tests for the stratify_accuracy module."""

    def setUp(self):
        """Create a temporary CSV file with mock annotated data."""
        self.temp_dir = tempfile.mkdtemp()
        self.data_path = os.path.join(self.temp_dir, 'test_annotated.csv')
        
        with open(self.data_path, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['id', 'question', 'answer', 'chain_length', 'chain_bin', 'correctness'])
            
            # 1-hop: 10 correct, 0 wrong -> 100%
            for i in range(10):
                writer.writerow([f'id_1_{i}', 'q', 'a', 1, '1', 1])
            
            # 2-hop: 5 correct, 5 wrong -> 50%
            for i in range(5):
                writer.writerow([f'id_2_{i}', 'q', 'a', 2, '2', 1])
            for i in range(5):
                writer.writerow([f'id_2_{i+5}', 'q', 'a', 2, '2', 0])
            
            # 3-hop: 2 correct, 8 wrong -> 20%
            for i in range(2):
                writer.writerow([f'id_3_{i}', 'q', 'a', 3, '3+', 1])
            for i in range(8):
                writer.writerow([f'id_3_{i+2}', 'q', 'a', 3, '3+', 0])

    def tearDown(self):
        """Clean up temporary files."""
        if os.path.exists(self.data_path):
            os.remove(self.data_path)
        os.rmdir(self.temp_dir)

    def test_load_annotated_data(self):
        """Test that data is loaded correctly."""
        data = load_annotated_data(self.data_path)
        self.assertEqual(len(data), 25) # 10 + 10 + 5
        # Check a sample record
        self.assertIn('chain_length', data[0])
        self.assertIn('correctness', data[0])

    def test_bin_hop_length(self):
        """Test the binning logic."""
        # Test exact bins
        self.assertEqual(bin_hop_length(1), '1')
        self.assertEqual(bin_hop_length(2), '2')
        self.assertEqual(bin_hop_length(3), '3+')
        self.assertEqual(bin_hop_length(5), '3+')
        self.assertEqual(bin_hop_length(10), '3+')

    def test_calculate_accuracy_by_bin(self):
        """Test accuracy calculation per bin."""
        data = load_annotated_data(self.data_path)
        accuracy_dict = calculate_accuracy_by_bin(data)
        
        # Check 1-hop
        self.assertIn('1', accuracy_dict)
        self.assertAlmostEqual(accuracy_dict['1']['accuracy'], 1.0, places=2)
        self.assertEqual(accuracy_dict['1']['count'], 10)

        # Check 2-hop
        self.assertIn('2', accuracy_dict)
        self.assertAlmostEqual(accuracy_dict['2']['accuracy'], 0.5, places=2)
        self.assertEqual(accuracy_dict['2']['count'], 10)

        # Check 3+
        self.assertIn('3+', accuracy_dict)
        self.assertAlmostEqual(accuracy_dict['3+']['accuracy'], 0.2, places=2)
        self.assertEqual(accuracy_dict['3+']['count'], 10)

    def test_write_results(self):
        """Test that results are written to a file."""
        data = load_annotated_data(self.data_path)
        accuracy_dict = calculate_accuracy_by_bin(data)
        
        output_path = os.path.join(self.temp_dir, 'results.json')
        write_results(accuracy_dict, output_path)
        
        self.assertTrue(os.path.exists(output_path))
        
        # Verify content
        with open(output_path, 'r') as f:
            results = json.load(f)
        
        self.assertIn('1', results)
        self.assertIn('accuracy', results['1'])


if __name__ == '__main__':
    unittest.main()