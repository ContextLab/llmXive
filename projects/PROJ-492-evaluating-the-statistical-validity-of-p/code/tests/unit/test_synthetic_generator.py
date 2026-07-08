"""
Unit tests for the synthetic dataset generator (T026).
Verifies that the generator produces valid data with both outcome types.
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
    set_all_seeds
)
from code.src.config import SEED


class TestSyntheticGenerator(TestCase):
    """Tests for the synthetic dataset generation module."""

    def setUp(self):
        """Set up a temporary directory for test outputs."""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.output_path = Path(self.temp_dir.name)

    def tearDown(self):
        """Clean up temporary directory."""
        self.temp_dir.cleanup()

    def test_generates_minimum_records(self):
        """Verify that at least 10,000 records are generated."""
        summaries_file, metadata_file = generate_synthetic_dataset(
            total_records=10000,
            output_dir=str(self.output_path),
            seed=SEED
        )

        # Count records in CSV
        with open(summaries_file, "r", newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            rows = list(reader)
        
        self.assertGreaterEqual(len(rows), 10000, 
            "Generated dataset must contain at least 10,000 records")

    def test_binary_outcomes_present(self):
        """Verify that binary outcomes are present in the dataset."""
        summaries_file, metadata_file = generate_synthetic_dataset(
            total_records=10000,
            output_dir=str(self.output_path),
            seed=SEED
        )

        with open(metadata_file, "r") as f:
            metadata = json.load(f)

        self.assertGreater(metadata.get("binary_count", 0), 0,
            "Dataset must contain binary outcomes")

    def test_continuous_outcomes_present(self):
        """Verify that continuous outcomes are present in the dataset."""
        summaries_file, metadata_file = generate_synthetic_dataset(
            total_records=10000,
            output_dir=str(self.output_path),
            seed=SEED
        )

        with open(metadata_file, "r") as f:
            metadata = json.load(f)

        self.assertGreater(metadata.get("continuous_count", 0), 0,
            "Dataset must contain continuous outcomes")

    def test_verify_outcome_types_function(self):
        """Test the verify_outcome_types helper function."""
        # Valid metadata
        valid_meta = {
            "binary_count": 5000,
            "continuous_count": 5000,
            "total_records": 10000
        }
        self.assertTrue(verify_outcome_types(valid_meta))

        # Missing binary
        invalid_binary = {
            "binary_count": 0,
            "continuous_count": 10000,
            "total_records": 10000
        }
        self.assertFalse(verify_outcome_types(invalid_binary))

        # Missing continuous
        invalid_continuous = {
            "binary_count": 10000,
            "continuous_count": 0,
            "total_records": 10000
        }
        self.assertFalse(verify_outcome_types(invalid_continuous))

    def test_csv_structure(self):
        """Verify that the generated CSV has the expected columns."""
        summaries_file, _ = generate_synthetic_dataset(
            total_records=100, # Small sample for speed
            output_dir=str(self.output_path),
            seed=SEED
        )

        expected_columns = [
            "id", "domain", "year", "outcome_type", "n_control", "n_treatment",
            "metric_name", "baseline_value", "treatment_value", "reported_p_value",
            "effect_size", "successes_control", "successes_treatment",
            "std_control", "std_treatment", "inconsistency_injected"
        ]

        with open(summaries_file, "r", newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            self.assertEqual(set(reader.fieldnames), set(expected_columns),
                f"CSV columns mismatch. Expected: {expected_columns}")

    def test_reproducibility(self):
        """Verify that the same seed produces the same output."""
        summaries_file_1, metadata_file_1 = generate_synthetic_dataset(
            total_records=100,
            output_dir=str(self.output_path / "run1"),
            seed=42
        )

        summaries_file_2, metadata_file_2 = generate_synthetic_dataset(
            total_records=100,
            output_dir=str(self.output_path / "run2"),
            seed=42
        )

        # Compare file contents
        with open(summaries_file_1, "r") as f1, open(summaries_file_2, "r") as f2:
            self.assertEqual(f1.read(), f2.read(),
                "Same seed should produce identical output")

    def test_metadata_structure(self):
        """Verify that the metadata JSON has required fields."""
        _, metadata_file = generate_synthetic_dataset(
            total_records=100,
            output_dir=str(self.output_path),
            seed=SEED
        )

        with open(metadata_file, "r") as f:
            metadata = json.load(f)

        required_fields = [
            "generated_at", "total_records", "binary_count", 
            "continuous_count", "seed", "file_path"
        ]

        for field in required_fields:
            self.assertIn(field, metadata, f"Metadata missing required field: {field}")

        self.assertEqual(metadata["total_records"], 100)
        self.assertEqual(metadata["seed"], SEED)
        self.assertGreater(metadata["binary_count"], 0)
        self.assertGreater(metadata["continuous_count"], 0)
