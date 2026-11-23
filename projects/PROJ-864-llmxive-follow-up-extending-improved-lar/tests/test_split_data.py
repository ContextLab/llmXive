"""
Tests for the split_data module (T016).
"""
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

# Add project root to path
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from code.data.split_data import load_jsonl, save_jsonl, split_data

class TestSplitData(unittest.TestCase):
    
    def setUp(self):
        """Set up temporary directory and sample data for tests."""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.temp_path = Path(self.temp_dir.name)
        
        # Create sample data
        self.sample_data = [
            {"id": 1, "text": "Sample text 1", "tokens": 10},
            {"id": 2, "text": "Sample text 2", "tokens": 15},
            {"id": 3, "text": "Sample text 3", "tokens": 20},
            {"id": 4, "text": "Sample text 4", "tokens": 25},
            {"id": 5, "text": "Sample text 5", "tokens": 30},
            {"id": 6, "text": "Sample text 6", "tokens": 12},
            {"id": 7, "text": "Sample text 7", "tokens": 18},
            {"id": 8, "text": "Sample text 8", "tokens": 22},
            {"id": 9, "text": "Sample text 9", "tokens": 28},
            {"id": 10, "text": "Sample text 10", "tokens": 32},
        ]

    def tearDown(self):
        """Clean up temporary directory."""
        self.temp_dir.cleanup()

    def test_load_jsonl(self):
        """Test loading a valid JSONL file."""
        file_path = self.temp_path / "test.jsonl"
        with open(file_path, 'w') as f:
            for item in self.sample_data:
                f.write(json.dumps(item) + '\n')
        
        loaded_data = load_jsonl(file_path)
        self.assertEqual(len(loaded_data), 10)
        self.assertEqual(loaded_data[0]["id"], 1)

    def test_save_jsonl(self):
        """Test saving data to a JSONL file."""
        file_path = self.temp_path / "output.jsonl"
        save_jsonl(self.sample_data, file_path)
        
        self.assertTrue(file_path.exists())
        loaded_data = load_jsonl(file_path)
        self.assertEqual(len(loaded_data), 10)

    def test_split_data_ratio(self):
        """Test that split_data respects the ratio."""
        # 90% train, 10% test -> 9 train, 1 test
        train, test = split_data(self.sample_data, train_ratio=0.9)
        self.assertEqual(len(train), 9)
        self.assertEqual(len(test), 1)

    def test_split_data_no_overlap(self):
        """Test that train and test sets have no overlapping items."""
        train, test = split_data(self.sample_data, train_ratio=0.8)
        
        train_ids = set(item["id"] for item in train)
        test_ids = set(item["id"] for item in test)
        
        self.assertEqual(len(train_ids.intersection(test_ids)), 0)

    def test_split_data_total_count(self):
        """Test that the total count is preserved."""
        train, test = split_data(self.sample_data, train_ratio=0.7)
        self.assertEqual(len(train) + len(test), len(self.sample_data))

    def test_split_data_invalid_ratio(self):
        """Test that invalid ratio raises ValueError."""
        with self.assertRaises(ValueError):
            split_data(self.sample_data, train_ratio=1.5)
        with self.assertRaises(ValueError):
            split_data(self.sample_data, train_ratio=-0.1)

    def test_split_data_empty_test_set(self):
        """Test that a ratio resulting in empty test set raises error."""
        # With 10 items, ratio 1.0 would mean 10 train, 0 test -> error in implementation
        # Our implementation raises error if split_idx == len(data)
        with self.assertRaises(ValueError):
            split_data(self.sample_data, train_ratio=1.0)

    def test_split_data_empty_train_set(self):
        """Test that a ratio resulting in empty train set raises error."""
        with self.assertRaises(ValueError):
            split_data(self.sample_data, train_ratio=0.0)

def run_tests():
    """Helper to run tests if called directly."""
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromTestCase(TestSplitData)
    runner = unittest.TextTestRunner(verbosity=2)
    runner.run(suite)

if __name__ == "__main__":
    run_tests()