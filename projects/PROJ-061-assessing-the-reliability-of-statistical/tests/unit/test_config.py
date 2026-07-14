"""
Unit tests for code/config.py to verify dataset configuration.
"""

import os
import sys
import json
import unittest

# Add parent directory to path to import code.config
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from code import config


class TestConfig(unittest.TestCase):

    def test_dataset_count(self):
        """Verify we have exactly 10 datasets."""
        datasets = config.get_dataset_list()
        self.assertEqual(len(datasets), 10)

    def test_outcome_distribution(self):
        """Verify 3 continuous, 3 count, 4 binary."""
        datasets = config.get_dataset_list()
        continuous = sum(1 for d in datasets if d['outcome_type'] == 'continuous')
        count = sum(1 for d in datasets if d['outcome_type'] == 'count')
        binary = sum(1 for d in datasets if d['outcome_type'] == 'binary')

        self.assertEqual(continuous, 3, "Expected 3 continuous datasets")
        self.assertEqual(count, 3, "Expected 3 count datasets")
        self.assertEqual(binary, 4, "Expected 4 binary datasets")

    def test_required_fields(self):
        """Verify each dataset has required fields."""
        required_fields = ['id', 'name', 'url', 'outcome_type', 'source']
        datasets = config.get_dataset_list()
        for d in datasets:
            for field in required_fields:
                self.assertIn(field, d, f"Missing field '{field}' in dataset {d.get('name', 'unknown')}")

    def test_urls_are_strings(self):
        """Verify all URLs are non-empty strings."""
        datasets = config.get_dataset_list()
        for d in datasets:
            self.assertIsInstance(d['url'], str)
            self.assertTrue(len(d['url']) > 0)

    def test_save_dataset_list(self):
        """Verify save_dataset_list creates a valid JSON file."""
        # Use a temporary path for testing
        temp_path = os.path.join(config.DATA_RAW_DIR, "test_dataset_list.json")
        try:
            saved_path = config.save_dataset_list(temp_path)
            self.assertTrue(os.path.exists(saved_path))

            with open(saved_path, 'r') as f:
                loaded_data = json.load(f)

            self.assertEqual(len(loaded_data), 10)
            self.assertEqual(loaded_data[0]['name'], config.DATASETS[0]['name'])
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)


if __name__ == '__main__':
    unittest.main()