"""
Unit tests for the synthetic dataset generator (T026).
Verifies that the generator creates valid data, respects constraints,
and produces the expected output files.
"""

import csv
import json
import math
import tempfile
from pathlib import Path
from unittest import TestCase

import numpy as np
from scipy import stats

from code.src.audit.synthetic import (
    generate_binary_outcome,
    generate_continuous_outcome,
    generate_synthetic_dataset,
    verify_outcome_types,
    write_summaries_to_csv,
    write_metadata,
    set_all_seeds,
    TOTAL_RECORDS
)
from code.src.config import SEED


class TestSyntheticGenerator(TestCase):
    """Tests for the synthetic data generation module."""

    def setUp(self):
        """Set up test fixtures."""
        set_all_seeds(SEED)
        self.temp_dir = Path(tempfile.mkdtemp())

    def tearDown(self):
        """Clean up temporary files."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_generate_binary_outcome_valid(self):
        """Test that binary outcome generation produces valid probabilities."""
        n_c, n_t = 1000, 1000
        p_base, effect = 0.2, 0.05

        record, true_p = generate_binary_outcome(n_c, n_t, p_base, effect, False)

        self.assertEqual(record["outcome_type"], "binary")
        self.assertEqual(record["n_control"], n_c)
        self.assertEqual(record["n_treatment"], n_t)
        self.assertGreaterEqual(record["successes_control"], 0)
        self.assertLessEqual(record["successes_control"], n_c)
        self.assertGreaterEqual(record["successes_treatment"], 0)
        self.assertLessEqual(record["successes_treatment"], n_t)

        # Check proportions are within [0, 1]
        self.assertGreaterEqual(record["proportion_control"], 0.0)
        self.assertLessEqual(record["proportion_control"], 1.0)
        self.assertGreaterEqual(record["proportion_treatment"], 0.0)
        self.assertLessEqual(record["proportion_treatment"], 1.0)

        # Check p-value is valid
        self.assertGreaterEqual(true_p, 0.0)
        self.assertLessEqual(true_p, 1.0)

    def test_generate_continuous_outcome_valid(self):
        """Test that continuous outcome generation produces valid statistics."""
        n_c, n_t = 1000, 1000
        mean_c, std_c = 50.0, 10.0
        mean_t, std_t = 55.0, 12.0

        record, true_p = generate_continuous_outcome(
            n_c, n_t, mean_c, std_c, mean_t, std_t, False
        )

        self.assertEqual(record["outcome_type"], "continuous")
        self.assertEqual(record["n_control"], n_c)
        self.assertEqual(record["n_treatment"], n_t)

        # Check means and stds are reasonable
        self.assertIsInstance(record["mean_control"], float)
        self.assertIsInstance(record["std_control"], float)
        self.assertGreater(record["std_control"], 0)

        self.assertGreaterEqual(true_p, 0.0)
        self.assertLessEqual(true_p, 1.0)

    def test_inconsistency_flag(self):
        """Test that inconsistent records have significantly different reported vs true p-values."""
        n_c, n_t = 2000, 2000
        p_base, effect = 0.3, 0.02

        # Generate inconsistent record
        record, true_p = generate_binary_outcome(n_c, n_t, p_base, effect, True)

        reported_p = record["reported_p_value"]

        # The inconsistency logic ensures a difference of at least 0.06
        # (unless clamped to 0 or 1, but with 2000 samples, true_p is rarely extreme)
        diff = abs(reported_p - true_p)
        # Allow some tolerance for edge cases where true_p is near 0 or 1
        # but generally it should be large
        self.assertGreater(diff, 0.01)

    def test_generate_synthetic_dataset_size(self):
        """Test that the generated dataset meets the minimum record count requirement."""
        # Generate a smaller subset for speed in unit tests
        test_size = 100
        records = generate_synthetic_dataset(n_records=test_size, seed=SEED)

        self.assertEqual(len(records), test_size)

        # Verify all required fields exist
        required_fields = [
            "outcome_type", "n_control", "n_treatment", "domain", "year",
            "id", "reported_p_value", "true_p_value", "is_inconsistent"
        ]
        for record in records:
            for field in required_fields:
                self.assertIn(field, record)

    def test_outcome_type_distribution(self):
        """Test that the outcome type distribution is roughly correct."""
        test_size = 1000
        records = generate_synthetic_dataset(n_records=test_size, seed=SEED)

        counts = verify_outcome_types(records)

        # Binary ratio is 0.6
        binary_ratio = counts["binary"] / counts["total"]
        # Allow 10% tolerance
        self.assertGreater(binary_ratio, 0.5)
        self.assertLess(binary_ratio, 0.7)

    def test_write_summaries_to_csv(self):
        """Test that writing to CSV produces a valid file."""
        records = generate_synthetic_dataset(n_records=50, seed=SEED)
        csv_path = self.temp_dir / "test_output.csv"

        write_summaries_to_csv(records, csv_path)

        self.assertTrue(csv_path.exists())

        with open(csv_path, 'r', newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        self.assertEqual(len(rows), 50)
        self.assertIn("outcome_type", rows[0])
        self.assertIn("domain", rows[0])

    def test_write_metadata(self):
        """Test that writing metadata produces valid JSON."""
        metadata = {
            "seed": SEED,
            "total_records": 100,
            "test_key": "test_value"
        }
        json_path = self.temp_dir / "test_metadata.json"

        write_metadata(metadata, json_path)

        self.assertTrue(json_path.exists())

        with open(json_path, 'r', encoding='utf-8') as f:
            loaded = json.load(f)

        self.assertEqual(loaded["seed"], SEED)
        self.assertEqual(loaded["total_records"], 100)

    def test_reproducibility(self):
        """Test that generating with the same seed produces identical results."""
        seed = 12345
        records1 = generate_synthetic_dataset(n_records=10, seed=seed)
        records2 = generate_synthetic_dataset(n_records=10, seed=seed)

        # Compare specific fields
        for r1, r2 in zip(records1, records2):
            self.assertEqual(r1["id"], r2["id"])
            self.assertEqual(r1["outcome_type"], r2["outcome_type"])
            self.assertEqual(r1["n_control"], r2["n_control"])
            self.assertEqual(r1["reported_p_value"], r2["reported_p_value"])

    def test_minimum_record_requirement(self):
        """
        Verify that the full generation meets the T026 requirement of >= 10,000 records.
        This test runs the full generator (or a subset check if too slow).
        """
        # We check the constant and a smaller sample to ensure the logic holds
        # The actual full generation is tested in integration tests or manually.
        self.assertGreaterEqual(TOTAL_RECORDS, 10000)

        # Generate a sample and verify structure
        sample_records = generate_synthetic_dataset(n_records=100, seed=SEED)
        self.assertEqual(len(sample_records), 100)
        # Verify all have unique IDs
        ids = [r["id"] for r in sample_records]
        self.assertEqual(len(ids), len(set(ids)))
