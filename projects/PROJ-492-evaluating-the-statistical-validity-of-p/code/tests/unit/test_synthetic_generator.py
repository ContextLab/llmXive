"""
Unit tests for the synthetic dataset generator.

Verifies:
1. The generator creates the required number of records (>= 10,000).
2. Both binary and continuous outcomes are present.
3. The output files are created in the expected locations.
4. The ground truth data is consistent with the summaries.
"""
import json
import csv
import os
import tempfile
from pathlib import Path
import pytest

from code.src.audit.synthetic import (
    generate_synthetic_dataset,
    verify_outcome_types,
    set_all_seeds,
    generate_binary_outcome,
    generate_continuous_outcome,
)
from code.src.config import SEED


class TestSyntheticGenerator:
    """Tests for the synthetic dataset generation module."""

    @pytest.fixture
    def temp_output_dir(self):
        """Create a temporary directory for test outputs."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    def test_generate_binary_outcome_structure(self):
        """Test that binary outcome generation returns expected fields."""
        result = generate_binary_outcome(100, 100)
        required_fields = [
            "outcome_type", "n_control", "n_treatment", "successes_control",
            "successes_treatment", "baseline_proportion", "treatment_proportion",
            "effect_size", "true_p_value", "reported_p_value", "is_inconsistent"
        ]
        for field in required_fields:
            assert field in result, f"Missing field: {field}"
        assert result["outcome_type"] == "binary"
        assert 0.0 <= result["reported_p_value"] <= 1.0

    def test_generate_continuous_outcome_structure(self):
        """Test that continuous outcome generation returns expected fields."""
        result = generate_continuous_outcome(100, 100)
        required_fields = [
            "outcome_type", "n_control", "n_treatment", "mean_control",
            "mean_treatment", "std_control", "std_treatment", "baseline_mean",
            "effect_size", "std_dev", "true_p_value", "reported_p_value",
            "is_inconsistent"
        ]
        for field in required_fields:
            assert field in result, f"Missing field: {field}"
        assert result["outcome_type"] == "continuous"
        assert 0.0 <= result["reported_p_value"] <= 1.0

    def test_synthetic_dataset_minimum_records(self, temp_output_dir):
        """Test that the generator produces at least 10,000 records."""
        n_records = 10000
        summaries_path, _ = generate_synthetic_dataset(
            n_records=n_records,
            output_dir=str(temp_output_dir),
            seed=SEED
        )

        assert summaries_path.exists(), "Summaries file was not created"

        with open(summaries_path, "r", encoding="utf-8") as f:
            reader = csv.reader(f)
            row_count = sum(1 for _ in reader) - 1  # Exclude header

        assert row_count >= 10000, f"Expected at least 10000 records, got {row_count}"

    def test_synthetic_dataset_both_outcome_types(self, temp_output_dir):
        """Test that both binary and continuous outcomes are present."""
        n_records = 10000
        summaries_path, ground_truth_path = generate_synthetic_dataset(
            n_records=n_records,
            output_dir=str(temp_output_dir),
            seed=SEED
        )

        assert ground_truth_path.exists(), "Ground truth file was not created"

        counts = verify_outcome_types(ground_truth_path)
        assert counts["binary"] > 0, "No binary outcomes generated"
        assert counts["continuous"] > 0, "No continuous outcomes generated"

        # Verify roughly 50/50 split
        total = counts["binary"] + counts["continuous"]
        assert 0.4 <= counts["binary"] / total <= 0.6, "Binary proportion out of expected range"

    def test_synthetic_dataset_files_exist(self, temp_output_dir):
        """Test that all expected output files are created."""
        n_records = 10000
        summaries_path, ground_truth_path = generate_synthetic_dataset(
            n_records=n_records,
            output_dir=str(temp_output_dir),
            seed=SEED
        )

        assert summaries_path.exists(), "Summaries CSV not found"
        assert ground_truth_path.exists(), "Ground truth JSON not found"

        # Check metadata file
        metadata_path = temp_output_dir / "synthetic_metadata.json"
        assert metadata_path.exists(), "Metadata file not found"

    def test_synthetic_dataset_csv_columns(self, temp_output_dir):
        """Test that the CSV has the required columns."""
        n_records = 10000
        summaries_path, _ = generate_synthetic_dataset(
            n_records=n_records,
            output_dir=str(temp_output_dir),
            seed=SEED
        )

        with open(summaries_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            fieldnames = reader.fieldnames

        required_columns = [
            "id", "domain", "year", "outcome_type", "n_control", "n_treatment",
            "reported_p_value", "effect_size", "baseline_rate", "treatment_rate"
        ]

        for col in required_columns:
            assert col in fieldnames, f"Missing column: {col}"

    def test_synthetic_dataset_ground_truth_consistency(self, temp_output_dir):
        """Test that ground truth matches the generated summaries."""
        n_records = 10000
        summaries_path, ground_truth_path = generate_synthetic_dataset(
            n_records=n_records,
            output_dir=str(temp_output_dir),
            seed=SEED
        )

        with open(ground_truth_path, "r", encoding="utf-8") as f:
            ground_truth = json.load(f)

        # Check that ground truth has same number of records
        assert len(ground_truth) == n_records, "Ground truth record count mismatch"

        # Check that IDs match
        summary_ids = set()
        with open(summaries_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                summary_ids.add(row["id"])

        truth_ids = {record["id"] for record in ground_truth}
        assert summary_ids == truth_ids, "ID mismatch between summaries and ground truth"

    def test_inconsistent_records_flagged(self, temp_output_dir):
        """Test that inconsistent records are properly flagged in ground truth."""
        n_records = 10000
        _, ground_truth_path = generate_synthetic_dataset(
            n_records=n_records,
            output_dir=str(temp_output_dir),
            seed=SEED,
            inconsistency_rate=0.20
        )

        with open(ground_truth_path, "r", encoding="utf-8") as f:
            ground_truth = json.load(f)

        inconsistent_count = sum(1 for r in ground_truth if r.get("is_inconsistent", False))
        # Should be approximately 20%
        assert 0.15 * n_records <= inconsistent_count <= 0.25 * n_records, \
            f"Inconsistent count {inconsistent_count} not within expected range for 20% rate"
