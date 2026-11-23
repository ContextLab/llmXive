import json
import os
import tempfile
import unittest
from pathlib import Path

import pandas as pd

# Import the function to test
from download import log_sample_metadata, stratified_sample_metadata

class TestT053_SampleMetadataLogging(unittest.TestCase):
    
    def setUp(self):
        """Set up temporary directory for test outputs."""
        self.temp_dir = tempfile.mkdtemp()
        self.output_path = os.path.join(self.temp_dir, "test_sample_metadata.json")

    def tearDown(self):
        """Clean up temporary files."""
        if os.path.exists(self.output_path):
            os.remove(self.output_path)
        if os.path.exists(self.temp_dir):
            os.rmdir(self.temp_dir)

    def test_log_sample_metadata_creates_file(self):
        """Test that log_sample_metadata creates the JSON file."""
        selected_ids = ["series_001", "series_002", "series_003"]
        method = "stratified by frequency"
        seed = 42
        nominal_levels = [0.80, 0.95]

        log_sample_metadata(selected_ids, method, seed, nominal_levels, self.output_path)

        self.assertTrue(os.path.exists(self.output_path))

    def test_log_sample_metadata_content(self):
        """Test that the JSON file contains required fields."""
        selected_ids = ["series_001", "series_002"]
        method = "stratified by frequency"
        seed = 123
        nominal_levels = [0.90]

        log_sample_metadata(selected_ids, method, seed, nominal_levels, self.output_path)

        with open(self.output_path, 'r') as f:
            data = json.load(f)

        # Verify required keys
        self.assertIn("sample_size", data)
        self.assertIn("sampling_method", data)
        self.assertIn("seed", data)
        self.assertIn("nominal_levels", data)
        self.assertIn("series_ids", data)

        # Verify values
        self.assertEqual(data["sample_size"], 2)
        self.assertEqual(data["sampling_method"], method)
        self.assertEqual(data["seed"], seed)
        self.assertEqual(data["nominal_levels"], nominal_levels)
        self.assertEqual(data["series_ids"], selected_ids)

    def test_log_sample_metadata_sample_size(self):
        """Test that sample_size matches the length of selected_ids."""
        selected_ids = [f"series_{i}" for i in range(50)]
        method = "random"
        seed = 999
        nominal_levels = [0.95]

        log_sample_metadata(selected_ids, method, seed, nominal_levels, self.output_path)

        with open(self.output_path, 'r') as f:
            data = json.load(f)

        self.assertEqual(data["sample_size"], len(selected_ids))

class TestT013a_2_StratifiedSample(unittest.TestCase):
    """Test the sampling logic used in T013a-2."""

    def test_stratified_sample_filters_short_series(self):
        """Test that series with length <= 50 are excluded."""
        # Create mock metadata
        data = {
            'id': ['A', 'B', 'C', 'D'],
            'frequency': ['Y', 'Y', 'M', 'M'],
            'seasonality': [4, 4, 12, 12],
            'length': [100, 50, 60, 40] # B is exactly 50 (excluded), D is < 50 (excluded)
        }
        metadata = pd.DataFrame(data)

        selected = stratified_sample_metadata(
            metadata=metadata,
            target_distribution={},
            seed=42,
            max_samples=10,
            min_length=50
        )

        # A (100) and C (60) should be candidates. B (50) and D (40) excluded.
        # Since max_samples is 10, we expect A and C.
        self.assertIn('A', selected)
        self.assertIn('C', selected)
        self.assertNotIn('B', selected)
        self.assertNotIn('D', selected)

    def test_stratified_sample_respects_max_samples(self):
        """Test that the sample size does not exceed max_samples."""
        data = {
            'id': [f's_{i}' for i in range(100)],
            'frequency': ['Y'] * 100,
            'seasonality': [4] * 100,
            'length': [100] * 100
        }
        metadata = pd.DataFrame(data)

        selected = stratified_sample_metadata(
            metadata=metadata,
            target_distribution={},
            seed=42,
            max_samples=10,
            min_length=50
        )

        self.assertEqual(len(selected), 10)

if __name__ == '__main__':
    unittest.main()