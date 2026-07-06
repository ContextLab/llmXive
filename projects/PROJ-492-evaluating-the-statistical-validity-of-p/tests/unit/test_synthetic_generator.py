"""
Unit tests for the synthetic dataset generator (T026).

Verifies that the generator produces at least 10,000 records
and includes both binary and continuous outcomes.
"""
import json
import csv
import tempfile
from pathlib import Path
import pytest

from code.src.audit.synthetic import (
    generate_synthetic_dataset,
    verify_outcome_types,
    set_all_seeds
)
from code.src.config import SEED


class TestSyntheticGenerator:
    """Tests for synthetic dataset generation."""

    def test_minimum_record_count(self, tmp_path):
        """Verify that at least 10,000 records are generated."""
        output_dir = tmp_path / "synthetic"
        summaries, counts = generate_synthetic_dataset(
            n_total=10000,
            binary_ratio=0.5,
            output_dir=output_dir,
            seed=SEED
        )

        assert len(summaries) >= 10000, f"Expected >= 10000 records, got {len(summaries)}"

    def test_both_outcome_types_present(self, tmp_path):
        """Verify that both binary and continuous outcomes are generated."""
        output_dir = tmp_path / "synthetic"
        summaries, counts = generate_synthetic_dataset(
            n_total=10000,
            binary_ratio=0.5,
            output_dir=output_dir,
            seed=SEED
        )

        success, verified_counts = verify_outcome_types(summaries)

        assert success, "Dataset must contain both binary and continuous outcomes"
        assert verified_counts["binary"] > 0, "No binary outcomes found"
        assert verified_counts["continuous"] > 0, "No continuous outcomes found"

    def test_csv_output_file_created(self, tmp_path):
        """Verify that CSV output file is created."""
        output_dir = tmp_path / "synthetic"
        generate_synthetic_dataset(
            n_total=100,
            binary_ratio=0.5,
            output_dir=output_dir,
            seed=SEED
        )

        csv_file = output_dir / "synthetic_summaries.csv"
        assert csv_file.exists(), "CSV output file not created"

        # Verify file is readable and has content
        with open(csv_file, 'r') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            assert len(rows) == 100, f"Expected 100 rows in CSV, got {len(rows)}"

    def test_json_output_file_created(self, tmp_path):
        """Verify that JSON output file is created."""
        output_dir = tmp_path / "synthetic"
        generate_synthetic_dataset(
            n_total=100,
            binary_ratio=0.5,
            output_dir=output_dir,
            seed=SEED
        )

        json_file = output_dir / "synthetic_summaries.json"
        assert json_file.exists(), "JSON output file not created"

        # Verify file is readable and has content
        with open(json_file, 'r') as f:
            data = json.load(f)
            assert len(data) == 100, f"Expected 100 records in JSON, got {len(data)}"

    def test_metadata_file_created(self, tmp_path):
        """Verify that metadata file is created."""
        output_dir = tmp_path / "synthetic"
        generate_synthetic_dataset(
            n_total=100,
            binary_ratio=0.5,
            output_dir=output_dir,
            seed=SEED
        )

        metadata_file = output_dir / "synthetic_metadata.json"
        assert metadata_file.exists(), "Metadata file not created"

        with open(metadata_file, 'r') as f:
            metadata = json.load(f)
            assert "total_records" in metadata
            assert "outcome_counts" in metadata
            assert metadata["total_records"] == 100

    def test_reproducibility_with_seed(self, tmp_path):
        """Verify that same seed produces same results."""
        output_dir1 = tmp_path / "synthetic1"
        output_dir2 = tmp_path / "synthetic2"

        summaries1, _ = generate_synthetic_dataset(
            n_total=100,
            binary_ratio=0.5,
            output_dir=output_dir1,
            seed=42
        )

        summaries2, _ = generate_synthetic_dataset(
            n_total=100,
            binary_ratio=0.5,
            output_dir=output_dir2,
            seed=42
        )

        # Compare first few records
        for i in range(5):
            assert summaries1[i]["p_value"] == summaries2[i]["p_value"]
            assert summaries1[i]["n_a"] == summaries2[i]["n_a"]
            assert summaries1[i]["outcome_type"] == summaries2[i]["outcome_type"]

    def test_record_structure(self, tmp_path):
        """Verify that each record has required fields."""
        output_dir = tmp_path / "synthetic"
        summaries, _ = generate_synthetic_dataset(
            n_total=100,
            binary_ratio=0.5,
            output_dir=output_dir,
            seed=SEED
        )

        required_fields = ["id", "n_a", "n_b", "p_value", "outcome_type", "domain", "year"]
        binary_fields = ["x_a", "x_b"]
        continuous_fields = ["mean_a", "mean_b", "std_a", "std_b"]

        for summary in summaries:
            # Check required fields
            for field in required_fields:
                assert field in summary, f"Missing required field: {field}"

            # Check outcome-type-specific fields
            if summary["outcome_type"] == "binary":
                for field in binary_fields:
                    assert field in summary, f"Missing binary field: {field}"
            elif summary["outcome_type"] == "continuous":
                for field in continuous_fields:
                    assert field in summary, f"Missing continuous field: {field}"

    def test_outcome_type_distribution(self, tmp_path):
        """Verify that outcome types are distributed according to binary_ratio."""
        output_dir = tmp_path / "synthetic"
        summaries, counts = generate_synthetic_dataset(
            n_total=1000,
            binary_ratio=0.7,
            output_dir=output_dir,
            seed=SEED
        )

        # Allow some variance due to randomization
        binary_ratio_actual = counts["binary"] / len(summaries)
        assert 0.65 <= binary_ratio_actual <= 0.75, \
            f"Expected ~0.7 binary ratio, got {binary_ratio_actual}"
