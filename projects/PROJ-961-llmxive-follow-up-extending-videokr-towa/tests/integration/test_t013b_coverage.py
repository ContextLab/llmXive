"""
Integration test for T013b: calculate_annotation_coverage.py

This test verifies that the coverage calculation logic works correctly
on a mock dataset that simulates the output of T013.
"""
import csv
import json
import os
import tempfile
from pathlib import Path
import unittest
from unittest.mock import patch, MagicMock

# Add parent directory to path to import utils
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from ingest.calculate_annotation_coverage import load_annotated_data, calculate_coverage, save_coverage_results

class TestT013bCoverage(unittest.TestCase):
    
    def setUp(self):
        """Set up temporary directory and mock data."""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.data_dir = Path(self.temp_dir.name)
        
        # Create a mock annotated CSV
        self.mock_csv_path = self.data_dir / "annotated_videokr.csv"
        self.mock_json_path = self.data_dir / "annotation_coverage.json"
        
        # Mock data: mix of valid hops and unresolvable
        mock_data = [
            {"id": "1", "question": "Q1", "answer": "A1", "chain_length": "1", "chain_bin": "1", "correctness": "1"},
            {"id": "2", "question": "Q2", "answer": "A2", "chain_length": "2", "chain_bin": "2", "correctness": "1"},
            {"id": "3", "question": "Q3", "answer": "A3", "chain_length": "3", "chain_bin": "3+", "correctness": "0"},
            {"id": "4", "question": "Q4", "answer": "A4", "chain_length": "unresolvable", "chain_bin": "unresolvable", "correctness": "0"},
            {"id": "5", "question": "Q5", "answer": "A5", "chain_length": "unmapped", "chain_bin": "unmapped", "correctness": "0"},
            {"id": "6", "question": "Q6", "answer": "A6", "chain_length": "4", "chain_bin": "3+", "correctness": "1"},
        ]
        
        with open(self.mock_csv_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=mock_data[0].keys())
            writer.writeheader()
            writer.writerows(mock_data)

    def tearDown(self):
        """Clean up temporary directory."""
        self.temp_dir.cleanup()

    def test_load_annotated_data(self):
        """Test loading the mock CSV file."""
        records = load_annotated_data(self.mock_csv_path)
        self.assertEqual(len(records), 6)
        self.assertEqual(records[0]['id'], '1')
        self.assertEqual(records[3]['chain_length'], 'unresolvable')

    def test_calculate_coverage(self):
        """Test coverage calculation logic."""
        records = load_annotated_data(self.mock_csv_path)
        stats = calculate_coverage(records)
        
        # Expected: 6 total, 2 unresolvable (unresolvable, unmapped), 4 annotated
        self.assertEqual(stats['total_input_records'], 6)
        self.assertEqual(stats['unresolvable_count'], 2)
        self.assertEqual(stats['annotated_count'], 4)
        self.assertAlmostEqual(stats['proportion'], 4/6, places=4)
        
        # Check distribution
        self.assertIn(1, stats['chain_length_distribution'])
        self.assertIn(2, stats['chain_length_distribution'])
        self.assertIn(3, stats['chain_length_distribution'])
        self.assertIn(4, stats['chain_length_distribution'])

    def test_save_coverage_results(self):
        """Test saving results to JSON."""
        records = load_annotated_data(self.mock_csv_path)
        stats = calculate_coverage(records)
        
        save_coverage_results(stats, self.mock_json_path)
        
        self.assertTrue(self.mock_json_path.exists())
        
        with open(self.mock_json_path, 'r') as f:
            loaded_stats = json.load(f)
        
        self.assertEqual(loaded_stats['total_input_records'], 6)
        self.assertEqual(loaded_stats['annotated_count'], 4)

    def test_missing_file(self):
        """Test handling of missing input file."""
        with self.assertRaises(FileNotFoundError):
            load_annotated_data(self.data_dir / "nonexistent.csv")

    def test_empty_file(self):
        """Test handling of empty CSV file."""
        empty_csv = self.data_dir / "empty.csv"
        with open(empty_csv, 'w') as f:
            f.write("")
        
        with self.assertRaises(ValueError):
            load_annotated_data(empty_csv)

    def test_missing_columns(self):
        """Test handling of CSV with missing required columns."""
        bad_csv = self.data_dir / "bad.csv"
        with open(bad_csv, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=['id', 'question'])
            writer.writeheader()
            writer.writerow({'id': '1', 'question': 'Q1'})
        
        with self.assertRaises(ValueError):
            load_annotated_data(bad_csv)

if __name__ == '__main__':
    unittest.main()