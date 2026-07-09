"""
Unit tests for the synthetic dataset generator (T026).
Verifies that the generator produces at least 10,000 records
with both binary and continuous outcomes.
"""
import csv
import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest
import numpy as np

from code.src.audit.synthetic import (
    set_all_seeds,
    generate_sample_sizes,
    generate_binary_outcome,
    generate_continuous_outcome,
    generate_synthetic_dataset,
    verify_outcome_types,
    write_metadata,
    main
)
from code.src.config import SEED


class TestSyntheticGenerator:
    """Test cases for synthetic dataset generation."""

    def test_set_all_seeds_deterministic(self):
        """Verify that seeding produces deterministic results."""
        set_all_seeds(SEED)
        result1 = np.random.random()

        set_all_seeds(SEED)
        result2 = np.random.random()

        assert result1 == result2, "Seeding should produce deterministic results"

    def test_generate_sample_sizes_range(self):
        """Verify sample sizes are within expected range."""
        n_control, n_treatment = generate_sample_sizes()

        assert 100 <= n_control <= 10000, "Control sample size out of range"
        assert 100 <= n_treatment <= 10000, "Treatment sample size out of range"
        assert isinstance(n_control, int), "Sample sizes should be integers"
        assert isinstance(n_treatment, int), "Sample sizes should be integers"

    def test_generate_binary_outcome_validity(self):
        """Verify binary outcome generation produces valid statistics."""
        n_control, n_treatment = 1000, 1000
        result = generate_binary_outcome(n_control, n_treatment)

        assert result["outcome_type"] == "binary"
        assert result["n_control"] == n_control
        assert result["n_treatment"] == n_treatment
        assert 0 <= result["rate_control"] <= 1
        assert 0 <= result["rate_treatment"] <= 1
        assert 0 <= result["p_value"] <= 1
        assert result["successes_control"] <= n_control
        assert result["successes_treatment"] <= n_treatment

    def test_generate_continuous_outcome_validity(self):
        """Verify continuous outcome generation produces valid statistics."""
        n_control, n_treatment = 1000, 1000
        result = generate_continuous_outcome(n_control, n_treatment)

        assert result["outcome_type"] == "continuous"
        assert result["n_control"] == n_control
        assert result["n_treatment"] == n_treatment
        assert result["mean_control"] > 0
        assert result["mean_treatment"] > 0
        assert result["std_control"] > 0
        assert result["std_treatment"] > 0
        assert 0 <= result["p_value"] <= 1

    def test_verify_outcome_types_success(self):
        """Verify that outcome type verification passes for valid data."""
        records = [
            {"outcome_type": "binary", "id": "1"},
            {"outcome_type": "continuous", "id": "2"},
            {"outcome_type": "binary", "id": "3"}
        ]

        binary_count, continuous_count = verify_outcome_types(records)

        assert binary_count == 2
        assert continuous_count == 1

    def test_verify_outcome_types_missing_binary(self):
        """Verify that missing binary outcomes raises error."""
        records = [
            {"outcome_type": "continuous", "id": "1"},
            {"outcome_type": "continuous", "id": "2"}
        ]

        with pytest.raises(ValueError, match="No binary outcomes"):
            verify_outcome_types(records)

    def test_verify_outcome_types_missing_continuous(self):
        """Verify that missing continuous outcomes raises error."""
        records = [
            {"outcome_type": "binary", "id": "1"},
            {"outcome_type": "binary", "id": "2"}
        ]

        with pytest.raises(ValueError, match="No continuous outcomes"):
            verify_outcome_types(records)

    def test_verify_outcome_types_insufficient_records(self):
        """Verify that insufficient records raises error."""
        records = [
            {"outcome_type": "binary", "id": "1"},
            {"outcome_type": "continuous", "id": "2"}
        ]

        with pytest.raises(ValueError, match="expected at least"):
            verify_outcome_types(records)

    def test_generate_synthetic_dataset_minimum_count(self):
        """Verify that generated dataset meets minimum record count."""
        records = generate_synthetic_dataset(10000)

        assert len(records) >= 10000, f"Expected at least 10000 records, got {len(records)}"

    def test_generate_synthetic_dataset_both_outcomes_present(self):
        """Verify that both outcome types are present in generated dataset."""
        records = generate_synthetic_dataset(10000)

        outcome_types = {r["outcome_type"] for r in records}

        assert "binary" in outcome_types, "Binary outcomes missing"
        assert "continuous" in outcome_types, "Continuous outcomes missing"

    def test_generate_synthetic_dataset_required_fields(self):
        """Verify that all required fields are present in generated records."""
        records = generate_synthetic_dataset(100)

        required_fields = [
            "id", "outcome_type", "n_control", "n_treatment",
            "p_value", "effect_size", "domain", "year"
        ]

        for record in records:
            for field in required_fields:
                assert field in record, f"Missing required field: {field}"

    def test_generate_synthetic_dataset_domain_distribution(self):
        """Verify that domains are distributed across records."""
        records = generate_synthetic_dataset(100)

        domains = {r["domain"] for r in records}
        expected_domains = {"tech", "finance", "health", "retail", "education"}

        assert domains == expected_domains, f"Expected domains {expected_domains}, got {domains}"

    def test_main_creates_output_files(self):
        """Verify that main() creates the expected output files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir) / "data" / "synthetic"
            output_dir.mkdir(parents=True, exist_ok=True)

            # Mock the OUTPUT_DIR and METADATA_FILE
            with patch("code.src.audit.synthetic.OUTPUT_DIR", output_dir):
                with patch("code.src.audit.synthetic.OUTPUT_FILE", output_dir / "synthetic_summaries.csv"):
                    with patch("code.src.audit.synthetic.METADATA_FILE", output_dir / "synthetic_metadata.json"):
                        result = main()

            assert result == 0, "main() should return 0 on success"
            assert (output_dir / "synthetic_summaries.csv").exists(), "CSV file not created"
            assert (output_dir / "synthetic_metadata.json").exists(), "Metadata file not created"

    def test_main_output_file_content(self):
        """Verify that the output CSV contains valid data."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir) / "data" / "synthetic"
            output_dir.mkdir(parents=True, exist_ok=True)

            with patch("code.src.audit.synthetic.OUTPUT_DIR", output_dir):
                with patch("code.src.audit.synthetic.OUTPUT_FILE", output_dir / "synthetic_summaries.csv"):
                    with patch("code.src.audit.synthetic.METADATA_FILE", output_dir / "synthetic_metadata.json"):
                        main()

            # Read and validate CSV
            with open(output_dir / "synthetic_summaries.csv", "r") as f:
                reader = csv.DictReader(f)
                rows = list(reader)

            assert len(rows) >= 10000, f"Expected at least 10000 rows, got {len(rows)}"

            # Check outcome types
            outcome_types = {row["outcome_type"] for row in rows}
            assert "binary" in outcome_types
            assert "continuous" in outcome_types

    def test_main_metadata_content(self):
        """Verify that the metadata file contains expected information."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir) / "data" / "synthetic"
            output_dir.mkdir(parents=True, exist_ok=True)

            with patch("code.src.audit.synthetic.OUTPUT_DIR", output_dir):
                with patch("code.src.audit.synthetic.OUTPUT_FILE", output_dir / "synthetic_summaries.csv"):
                    with patch("code.src.audit.synthetic.METADATA_FILE", output_dir / "synthetic_metadata.json"):
                        main()

            with open(output_dir / "synthetic_metadata.json", "r") as f:
                metadata = json.load(f)

            assert "total_records" in metadata
            assert "binary_count" in metadata
            assert "continuous_count" in metadata
            assert "seed" in metadata
            assert metadata["total_records"] >= 10000
            assert metadata["binary_count"] > 0
            assert metadata["continuous_count"] > 0
            assert metadata["seed"] == SEED
