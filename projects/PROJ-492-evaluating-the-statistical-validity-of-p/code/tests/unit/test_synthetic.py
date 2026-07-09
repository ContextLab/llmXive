"""
Unit tests for the synthetic dataset generator (T026).

Verifies:
1. Dataset generation produces correct file structure
2. Both binary and continuous outcomes are present
3. Record count meets minimum threshold (≥ 10,000)
4. Data types and field presence are correct
"""

import csv
import json
import os
import tempfile
from pathlib import Path
from unittest import TestCase

from code.src.audit.synthetic import (
    generate_synthetic_dataset,
    verify_outcome_types,
    set_all_seeds,
    generate_binary_outcome,
    generate_continuous_outcome
)
from code.src.config import SEED


class TestSyntheticGenerator(TestCase):
    """Test cases for the synthetic dataset generator."""

    def setUp(self):
        """Set up temporary directory for test outputs."""
        self.temp_dir = tempfile.mkdtemp()
        self.output_dir = Path(self.temp_dir)

    def tearDown(self):
        """Clean up temporary directory."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_generate_binary_outcome_structure(self):
        """Test that binary outcome generation produces correct fields."""
        set_all_seeds(SEED)
        record = generate_binary_outcome(1000, 1000, baseline_rate=0.10)

        required_fields = [
            "n_control", "n_treatment", "successes_control", "successes_treatment",
            "baseline_rate", "observed_lift", "p_value", "outcome_type"
        ]

        for field in required_fields:
            self.assertIn(field, record, f"Missing required field: {field}")

        self.assertEqual(record["outcome_type"], "binary")
        self.assertIsInstance(record["n_control"], int)
        self.assertIsInstance(record["p_value"], float)
        self.assertGreaterEqual(record["n_control"], 100)
        self.assertGreaterEqual(record["n_treatment"], 100)

    def test_generate_continuous_outcome_structure(self):
        """Test that continuous outcome generation produces correct fields."""
        set_all_seeds(SEED)
        record = generate_continuous_outcome(1000, 1000, baseline_mean=100.0)

        required_fields = [
            "n_control", "n_treatment", "mean_control", "mean_treatment",
            "std_control", "std_treatment", "baseline_mean", "observed_lift",
            "p_value", "outcome_type"
        ]

        for field in required_fields:
            self.assertIn(field, record, f"Missing required field: {field}")

        self.assertEqual(record["outcome_type"], "continuous")
        self.assertIsInstance(record["n_control"], int)
        self.assertIsInstance(record["p_value"], float)

    def test_generate_synthetic_dataset_creates_files(self):
        """Test that dataset generation creates expected output files."""
        n_records = 100
        csv_path, metadata_path = generate_synthetic_dataset(
            n_records=n_records,
            output_dir=self.output_dir,
            seed=SEED
        )

        self.assertTrue(csv_path.exists(), "CSV file was not created")
        self.assertTrue(metadata_path.exists(), "Metadata file was not created")

        # Verify file sizes are non-zero
        self.assertGreater(csv_path.stat().st_size, 0, "CSV file is empty")
        self.assertGreater(metadata_path.stat().st_size, 0, "Metadata file is empty")

    def test_synthetic_dataset_record_count(self):
        """Test that generated dataset has correct number of records."""
        n_records = 100
        csv_path, _ = generate_synthetic_dataset(
            n_records=n_records,
            output_dir=self.output_dir,
            seed=SEED
        )

        with open(csv_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            actual_count = sum(1 for _ in reader)

        self.assertEqual(actual_count, n_records, f"Expected {n_records} records, got {actual_count}")

    def test_synthetic_dataset_both_outcome_types(self):
        """Test that generated dataset contains both binary and continuous outcomes."""
        n_records = 1000  # Use larger sample to ensure both types appear
        csv_path, _ = generate_synthetic_dataset(
            n_records=n_records,
            output_dir=self.output_dir,
            seed=SEED
        )

        verification = verify_outcome_types(csv_path)

        self.assertTrue(verification["has_binary"], "Dataset missing binary outcomes")
        self.assertTrue(verification["has_continuous"], "Dataset missing continuous outcomes")
        self.assertTrue(verification["valid"], "Dataset verification failed")

    def test_synthetic_dataset_minimum_threshold(self):
        """Test that dataset generation meets the 10,000 record minimum (FR-030)."""
        n_records = 10000
        csv_path, _ = generate_synthetic_dataset(
            n_records=n_records,
            output_dir=self.output_dir,
            seed=SEED
        )

        verification = verify_outcome_types(csv_path)

        self.assertTrue(verification["meets_minimum_threshold"], "Dataset does not meet 10,000 record minimum")
        self.assertEqual(verification["total_records"], n_records)

    def test_metadata_contains_required_fields(self):
        """Test that metadata file contains required information."""
        n_records = 100
        _, metadata_path = generate_synthetic_dataset(
            n_records=n_records,
            output_dir=self.output_dir,
            seed=SEED
        )

        with open(metadata_path, "r", encoding="utf-8") as f:
            metadata = json.load(f)

        required_fields = ["total_records", "binary_count", "continuous_count", "verification_passed"]
        for field in required_fields:
            self.assertIn(field, metadata, f"Missing metadata field: {field}")

        self.assertEqual(metadata["total_records"], n_records)
        self.assertTrue(metadata["verification_passed"])

    def test_reproducibility_with_seed(self):
        """Test that generation is reproducible with the same seed."""
        n_records = 100

        # Generate first dataset
        csv_path1, _ = generate_synthetic_dataset(
            n_records=n_records,
            output_dir=self.output_dir,
            seed=SEED
        )

        # Generate second dataset with same seed
        csv_path2, _ = generate_synthetic_dataset(
            n_records=n_records,
            output_dir=self.output_dir,
            seed=SEED
        )

        # Compare file contents
        with open(csv_path1, "r", encoding="utf-8") as f1, open(csv_path2, "r", encoding="utf-8") as f2:
            content1 = f1.read()
            content2 = f2.read()

        self.assertEqual(content1, content2, "Generation is not reproducible with same seed")

    def test_sample_size_minimum_constraint(self):
        """Test that sample sizes respect the minimum of 100 per group."""
        set_all_seeds(SEED)
        for _ in range(100):
            record = generate_binary_outcome(10000, 10000)
            self.assertGreaterEqual(record["n_control"], 100)
            self.assertGreaterEqual(record["n_treatment"], 100)

    def test_p_value_range(self):
        """Test that p-values are within valid range [0, 1]."""
        set_all_seeds(SEED)
        for _ in range(100):
            record = generate_binary_outcome(1000, 1000)
            self.assertGreaterEqual(record["p_value"], 0.0)
            self.assertLessEqual(record["p_value"], 1.0)
            
            record = generate_continuous_outcome(1000, 1000)
            self.assertGreaterEqual(record["p_value"], 0.0)
            self.assertLessEqual(record["p_value"], 1.0)