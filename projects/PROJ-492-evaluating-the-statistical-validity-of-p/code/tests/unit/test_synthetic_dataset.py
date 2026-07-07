"""
Unit tests for synthetic dataset generator (Task T026).
Verifies that the generator produces at least 10,000 records
and includes both binary and continuous outcomes.
"""
import csv
import json
import os
import unittest
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.src.audit.synthetic import (
    generate_synthetic_dataset,
    verify_outcome_types,
    generate_binary_outcome,
    generate_continuous_outcome,
    set_all_seeds
)
from code.src.config import SEED


class TestSyntheticDataset(unittest.TestCase):
    """Tests for the synthetic dataset generator."""

    def setUp(self):
        """Set up test fixtures."""
        self.test_dir = Path("data/synthetic")
        self.test_dir.mkdir(parents=True, exist_ok=True)
        set_all_seeds(SEED)

    def test_generate_binary_outcome_structure(self):
        """Test that binary outcome generation produces correct structure."""
        result = generate_binary_outcome(
            n_control=100,
            n_treatment=100,
            baseline_rate=0.2,
            effect_size=0.1,
            seed=42
        )

        self.assertIn("n_control", result)
        self.assertIn("n_treatment", result)
        self.assertIn("x_control", result)
        self.assertIn("x_treatment", result)
        self.assertIn("baseline_rate", result)
        self.assertIn("treatment_rate", result)
        self.assertIn("p_value", result)
        self.assertIn("effect_size", result)
        self.assertIn("outcome_type", result)
        self.assertEqual(result["outcome_type"], "binary")
        self.assertIsInstance(result["p_value"], float)
        self.assertGreaterEqual(result["p_value"], 0.0)
        self.assertLessEqual(result["p_value"], 1.0)

    def test_generate_continuous_outcome_structure(self):
        """Test that continuous outcome generation produces correct structure."""
        result = generate_continuous_outcome(
            n_control=100,
            n_treatment=100,
            baseline_mean=50.0,
            effect_size=5.0,
            std_dev=10.0,
            seed=42
        )

        self.assertIn("n_control", result)
        self.assertIn("n_treatment", result)
        self.assertIn("mean_control", result)
        self.assertIn("mean_treatment", result)
        self.assertIn("std_control", result)
        self.assertIn("std_treatment", result)
        self.assertIn("p_value", result)
        self.assertIn("effect_size", result)
        self.assertIn("outcome_type", result)
        self.assertEqual(result["outcome_type"], "continuous")
        self.assertIsInstance(result["p_value"], float)
        self.assertGreaterEqual(result["p_value"], 0.0)
        self.assertLessEqual(result["p_value"], 1.0)

    def test_generate_synthetic_dataset_minimum_count(self):
        """Test that the dataset generator produces at least 10,000 records."""
        records = generate_synthetic_dataset(
            total_records=10000,
            binary_ratio=0.5,
            seed=SEED
        )

        self.assertGreaterEqual(len(records), 10000)

    def test_generate_synthetic_dataset_both_outcome_types(self):
        """Test that the dataset includes both binary and continuous outcomes."""
        records = generate_synthetic_dataset(
            total_records=10000,
            binary_ratio=0.5,
            seed=SEED
        )

        binary_count = sum(1 for r in records if r["outcome_type"] == "binary")
        continuous_count = sum(1 for r in records if r["outcome_type"] == "continuous")

        self.assertGreater(binary_count, 0, "Dataset must contain binary outcomes")
        self.assertGreater(continuous_count, 0, "Dataset must contain continuous outcomes")

    def test_verify_outcome_types(self):
        """Test the verification function."""
        records = generate_synthetic_dataset(
            total_records=10000,
            binary_ratio=0.5,
            seed=SEEND
        )

        verification = verify_outcome_types(records)

        self.assertTrue(verification["meets_minimum"])
        self.assertTrue(verification["has_both_types"])
        self.assertGreaterEqual(verification["total_records"], 10000)
        self.assertGreater(verification["binary_count"], 0)
        self.assertGreater(verification["continuous_count"], 0)

    def test_csv_output_contains_required_fields(self):
        """Test that the generated CSV contains all required fields."""
        records = generate_synthetic_dataset(
            total_records=100,
            binary_ratio=0.5,
            seed=SEED
        )

        csv_path = self.test_dir / "test_summaries.csv"

        # Write a small test file
        fieldnames = [
            "id", "outcome_type", "n_control", "n_treatment",
            "baseline_rate", "treatment_rate", "mean_control", "mean_treatment",
            "std_control", "std_treatment", "x_control", "x_treatment",
            "p_value", "effect_size", "domain", "year"
        ]

        with open(csv_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction='ignore')
            writer.writeheader()
            writer.writerows(records)

        # Read and verify
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        self.assertEqual(len(rows), 100)

        # Check a sample row for required fields
        sample = rows[0]
        self.assertIn("outcome_type", sample)
        self.assertIn("n_control", sample)
        self.assertIn("n_treatment", sample)
        self.assertIn("p_value", sample)
        self.assertIn("effect_size", sample)

        # Cleanup
        os.remove(csv_path)

    def test_deterministic_generation(self):
        """Test that generation is deterministic with the same seed."""
        set_all_seeds(SEED)
        records1 = generate_synthetic_dataset(
            total_records=100,
            binary_ratio=0.5,
            seed=SEED
        )

        set_all_seeds(SEED)
        records2 = generate_synthetic_dataset(
            total_records=100,
            binary_ratio=0.5,
            seed=SEED
        )

        # Compare first few records
        for i in range(10):
            self.assertEqual(records1[i]["p_value"], records2[i]["p_value"])
            self.assertEqual(records1[i]["outcome_type"], records2[i]["outcome_type"])


if __name__ == "__main__":
    unittest.main()