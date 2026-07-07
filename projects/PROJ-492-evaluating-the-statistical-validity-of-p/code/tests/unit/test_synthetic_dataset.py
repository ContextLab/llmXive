"""
Unit tests for synthetic dataset generator (T026).
"""
import csv
import json
from pathlib import Path
import tempfile
import pytest

import numpy as np

from code.src.audit.synthetic import (
    set_all_seeds,
    generate_sample_sizes,
    generate_binary_outcome,
    generate_continuous_outcome,
    generate_synthetic_dataset,
    verify_outcome_types,
    write_csv_output,
    write_metadata,
)
from code.src.config import SEED


class TestSyntheticDatasetGenerator:
    """Tests for the synthetic dataset generator."""

    def test_set_all_seeds_determinism(self):
        """Test that setting seeds produces deterministic results."""
        set_all_seeds(SEED)
        result1 = generate_binary_outcome(100, 0.5, 0.1, seed=SEED)

        set_all_seeds(SEED)
        result2 = generate_binary_outcome(100, 0.5, 0.1, seed=SEED)

        assert result1 == result2, "Results should be identical with same seed"

    def test_generate_binary_outcome(self):
        """Test binary outcome generation."""
        n_control, n_treatment, succ_c, succ_t, p_val = generate_binary_outcome(
            1000, 0.5, 0.05, seed=42
        )

        assert n_control == 1000
        assert n_treatment == 1000
        assert 0 <= succ_c <= n_control
        assert 0 <= succ_t <= n_treatment
        assert 0 <= p_val <= 1

    def test_generate_continuous_outcome(self):
        """Test continuous outcome generation."""
        (n_control, n_treatment, mean_c, mean_t, std_c, std_t, p_val) = (
            generate_continuous_outcome(1000, 2.0, seed=42)
        )

        assert n_control == 1000
        assert n_treatment == 1000
        assert isinstance(mean_c, float)
        assert isinstance(mean_t, float)
        assert std_c > 0
        assert std_t > 0
        assert 0 <= p_val <= 1

    def test_generate_synthetic_dataset_minimum_count(self):
        """Test that dataset generation produces at least 10,000 records."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            metadata = generate_synthetic_dataset(
                total_records=10000,
                binary_ratio=0.5,
                output_dir=output_dir,
                seed=SEED
            )

            assert metadata["total_records"] >= 10000
            assert metadata["binary_count"] + metadata["continuous_count"] == metadata["total_records"]

    def test_generate_synthetic_dataset_both_outcome_types(self):
        """Test that both binary and continuous outcomes are present."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            metadata = generate_synthetic_dataset(
                total_records=10000,
                binary_ratio=0.5,
                output_dir=output_dir,
                seed=SEED
            )

            assert metadata["binary_count"] > 0, "Binary outcomes must be present"
            assert metadata["continuous_count"] > 0, "Continuous outcomes must be present"

    def test_csv_output_exists_and_readable(self):
        """Test that CSV output file is created and readable."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            generate_synthetic_dataset(
                total_records=1000,
                binary_ratio=0.5,
                output_dir=output_dir,
                seed=SEED
            )

            csv_path = output_dir / "synthetic_summaries.csv"
            assert csv_path.exists(), "CSV file should exist"

            with open(csv_path, "r") as f:
                reader = csv.DictReader(f)
                rows = list(reader)

            assert len(rows) == 1000, f"Expected 1000 rows, got {len(rows)}"

    def test_metadata_json_exists_and_valid(self):
        """Test that metadata JSON file is created and valid."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            generate_synthetic_dataset(
                total_records=1000,
                binary_ratio=0.5,
                output_dir=output_dir,
                seed=SEED
            )

            metadata_path = output_dir / "synthetic_metadata.json"
            assert metadata_path.exists(), "Metadata file should exist"

            with open(metadata_path, "r") as f:
                metadata = json.load(f)

            assert "total_records" in metadata
            assert "binary_count" in metadata
            assert "continuous_count" in metadata
            assert metadata["total_records"] == 1000

    def test_verify_outcome_types_passes(self):
        """Test that verify_outcome_types passes for valid data."""
        records = [
            {"outcome_type": "binary"},
            {"outcome_type": "binary"},
            {"outcome_type": "continuous"},
        ]
        # Should not raise
        verify_outcome_types(records, 2, 1)

    def test_verify_outcome_types_fails_missing_type(self):
        """Test that verify_outcome_types fails when a type is missing."""
        records = [
            {"outcome_type": "binary"},
            {"outcome_type": "binary"},
        ]
        with pytest.raises(ValueError, match="Continuous outcomes must be present"):
            verify_outcome_types(records, 2, 0)

    def test_sample_size_generation(self):
        """Test sample size generation within bounds."""
        sizes = generate_sample_sizes(100)
        assert len(sizes) == 100
        for size in sizes:
            assert 50 <= size <= 5000, f"Size {size} out of bounds"

    def test_deterministic_generation(self):
        """Test that generation is deterministic with same seed."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir1 = Path(tmpdir) / "run1"
            output_dir2 = Path(tmpdir) / "run2"
            output_dir1.mkdir()
            output_dir2.mkdir()

            generate_synthetic_dataset(
                total_records=100,
                binary_ratio=0.5,
                output_dir=output_dir1,
                seed=42
            )
            generate_synthetic_dataset(
                total_records=100,
                binary_ratio=0.5,
                output_dir=output_dir2,
                seed=42
            )

            csv1 = output_dir1 / "synthetic_summaries.csv"
            csv2 = output_dir2 / "synthetic_summaries.csv"

            with open(csv1, "r") as f1, open(csv2, "r") as f2:
                assert f1.read() == f2.read(), "CSV outputs should be identical"
