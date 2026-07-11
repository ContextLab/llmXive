"""
Unit tests for the synthetic dataset generator (T026).
"""

import csv
import json
import os
import tempfile
from pathlib import Path
import unittest

import numpy as np

from code.src.audit.synthetic import (
    set_all_seeds,
    generate_sample_sizes,
    generate_binary_outcome,
    generate_continuous_outcome,
    generate_synthetic_dataset,
    verify_outcome_types
)
from code.src.config import SEED


class TestSyntheticGenerator(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.output_path = Path(self.temp_dir)
        set_all_seeds(SEED)

    def tearDown(self):
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_set_all_seeds(self):
        """Test that seeds are set correctly."""
        set_all_seeds(123)
        # Simple check: random should be deterministic
        val1 = random.random()
        set_all_seeds(123)
        val2 = random.random()
        self.assertEqual(val1, val2)

    def test_generate_sample_sizes(self):
        """Test sample size generation."""
        sizes = generate_sample_sizes(100)
        self.assertEqual(len(sizes), 100)
        for s in sizes:
            self.assertGreaterEqual(s, 50)
            self.assertLessEqual(s, 10000)

    def test_generate_binary_outcome(self):
        """Test binary outcome generation."""
        n, s_c, n_t, s_t, true_p, obs_p = generate_binary_outcome(
            1000, 0.5, 0.1
        )
        self.assertEqual(n, 1000)
        self.assertEqual(n_t, 1000)
        self.assertGreaterEqual(s_c, 0)
        self.assertLessEqual(s_c, n)
        self.assertGreaterEqual(s_t, 0)
        self.assertLessEqual(s_t, n_t)
        self.assertGreaterEqual(obs_p, 0.0)
        self.assertLessEqual(obs_p, 1.0)

    def test_generate_continuous_outcome(self):
        """Test continuous outcome generation."""
        vals_c, vals_t, true_p, obs_p = generate_continuous_outcome(
            1000, 100.0, 15.0, 5.0
        )
        self.assertEqual(len(vals_c), 1000)
        self.assertEqual(len(vals_t), 1000)
        self.assertGreaterEqual(obs_p, 0.0)
        self.assertLessEqual(obs_p, 1.0)

    def test_generate_synthetic_dataset_size(self):
        """Test that the generated dataset meets the >= 10,000 record requirement."""
        csv_path = generate_synthetic_dataset(n_records=10000, output_dir=self.output_path)
        
        # Count lines in CSV (excluding header)
        with open(csv_path, "r", encoding="utf-8") as f:
            reader = csv.reader(f)
            next(reader) # Skip header
            count = sum(1 for _ in reader)
        
        self.assertGreaterEqual(count, 10000)

    def test_generate_synthetic_dataset_outcome_types(self):
        """Test that the dataset contains both binary and continuous outcomes."""
        csv_path = generate_synthetic_dataset(n_records=10000, output_dir=self.output_path)
        counts = verify_outcome_types(csv_path)
        
        self.assertGreater(counts["binary"], 0)
        self.assertGreater(counts["continuous"], 0)

    def test_metadata_generation(self):
        """Test that metadata file is generated correctly."""
        csv_path = generate_synthetic_dataset(n_records=10000, output_dir=self.output_path)
        meta_path = self.output_path / "metadata.json"
        
        self.assertTrue(meta_path.exists())
        
        with open(meta_path, "r", encoding="utf-8") as f:
            meta = json.load(f)
        
        self.assertIn("total_records", meta)
        self.assertEqual(meta["total_records"], 10000)
        self.assertIn("seed", meta)


if __name__ == "__main__":
    import random
    unittest.main()
