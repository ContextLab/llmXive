"""
Unit tests for synthetic dataset generator (T026).

Verifies:
- Generation of at least 10,000 records
- Presence of both binary and continuous outcomes
- Statistical validity of generated data
"""

import json
import csv
import pytest
from pathlib import Path
from typing import Dict, Any, List

import numpy as np

from code.src.audit.synthetic import (
    generate_synthetic_dataset,
    verify_outcome_types,
    generate_binary_outcome,
    generate_continuous_outcome,
    set_all_seeds,
    MIN_RECORDS,
)
from code.src.config import SEED


class TestSyntheticGenerator:
    """Tests for the synthetic dataset generator."""

    def test_minimum_record_count(self, tmp_path: Path):
        """Verify that at least 10,000 records are generated."""
        summaries = generate_synthetic_dataset(n_records=MIN_RECORDS, output_dir=tmp_path)
        assert len(summaries) >= MIN_RECORDS, (
            f"Expected at least {MIN_RECORDS} records, got {len(summaries)}"
        )

    def test_both_outcome_types_present(self, tmp_path: Path):
        """Verify that both binary and continuous outcomes are present."""
        summaries = generate_synthetic_dataset(n_records=MIN_RECORDS, output_dir=tmp_path)
        is_valid, counts = verify_outcome_types(summaries)

        assert is_valid, "Both outcome types must be present"
        assert counts["binary"] > 0, "Binary outcomes must be present"
        assert counts["continuous"] > 0, "Continuous outcomes must be present"

    def test_binary_outcome_structure(self):
        """Verify binary outcome data has correct structure."""
        result = generate_binary_outcome(
            n_control=1000, n_treatment=1000, baseline_rate=0.1, effect_size=0.02
        )

        required_fields = [
            "outcome_type",
            "n_control",
            "n_treatment",
            "successes_control",
            "successes_treatment",
            "prop_control",
            "prop_treatment",
            "effect_size",
            "p_value",
            "z_statistic",
            "baseline_rate",
        ]

        for field in required_fields:
            assert field in result, f"Missing required field: {field}"

        assert result["outcome_type"] == "binary"
        assert 0 <= result["prop_control"] <= 1
        assert 0 <= result["prop_treatment"] <= 1
        assert 0 <= result["p_value"] <= 1

    def test_continuous_outcome_structure(self):
        """Verify continuous outcome data has correct structure."""
        result = generate_continuous_outcome(
            n_control=1000, n_treatment=1000, baseline_mean=50.0, effect_size=1.0
        )

        required_fields = [
            "outcome_type",
            "n_control",
            "n_treatment",
            "mean_control",
            "mean_treatment",
            "std_control",
            "std_treatment",
            "effect_size",
            "p_value",
            "t_statistic",
            "cohens_d",
            "baseline_mean",
        ]

        for field in required_fields:
            assert field in result, f"Missing required field: {field}"

        assert result["outcome_type"] == "continuous"
        assert result["std_control"] > 0
        assert result["std_treatment"] > 0
        assert 0 <= result["p_value"] <= 1

    def test_csv_output_exists(self, tmp_path: Path):
        """Verify that CSV output file is created."""
        generate_synthetic_dataset(n_records=100, output_dir=tmp_path)
        csv_path = tmp_path / "synthetic_summaries.csv"
        assert csv_path.exists(), f"CSV file not created: {csv_path}"

    def test_json_output_exists(self, tmp_path: Path):
        """Verify that JSON output file is created."""
        generate_synthetic_dataset(n_records=100, output_dir=tmp_path)
        json_path = tmp_path / "synthetic_summaries.json"
        assert json_path.exists(), f"JSON file not created: {json_path}"

    def test_metadata_output_exists(self, tmp_path: Path):
        """Verify that metadata file is created."""
        generate_synthetic_dataset(n_records=100, output_dir=tmp_path)
        metadata_path = tmp_path / "synthetic_metadata.json"
        assert metadata_path.exists(), f"Metadata file not created: {metadata_path}"

        with open(metadata_path, "r") as f:
            metadata = json.load(f)

        assert "total_records" in metadata
        assert "binary_count" in metadata
        assert "continuous_count" in metadata
        assert metadata["total_records"] >= 100

    def test_reproducibility(self, tmp_path: Path):
        """Verify that generation is reproducible with same seed."""
        set_all_seeds(SEED)
        summaries1 = generate_synthetic_dataset(n_records=50, output_dir=tmp_path / "run1")

        set_all_seeds(SEED)
        summaries2 = generate_synthetic_dataset(n_records=50, output_dir=tmp_path / "run2")

        # Compare a few key fields
        for i in range(min(10, len(summaries1))):
            assert summaries1[i]["prop_control"] == summaries2[i]["prop_control"]
            assert summaries1[i]["p_value"] == summaries2[i]["p_value"]

    def test_sample_size_ranges(self, tmp_path: Path):
        """Verify that sample sizes are within expected ranges."""
        summaries = generate_synthetic_dataset(n_records=100, output_dir=tmp_path)

        for summary in summaries:
            assert summary["n_control"] >= 100
            assert summary["n_control"] <= 50000
            assert summary["n_treatment"] >= 100
            assert summary["n_treatment"] <= 50000

    def test_p_value_range(self, tmp_path: Path):
        """Verify that p-values are in valid range [0, 1]."""
        summaries = generate_synthetic_dataset(n_records=100, output_dir=tmp_path)

        for summary in summaries:
            p_value = summary["p_value"]
            assert 0 <= p_value <= 1, f"P-value {p_value} out of range"

    def test_effect_size_calculation(self, tmp_path: Path):
        """Verify that effect sizes are calculated correctly."""
        summaries = generate_synthetic_dataset(n_records=100, output_dir=tmp_path)

        for summary in summaries:
            if summary["outcome_type"] == "binary":
                expected_effect = (
                    summary["prop_treatment"] - summary["prop_control"]
                )
                assert abs(summary["effect_size"] - expected_effect) < 1e-6
            else:
                expected_effect = (
                    summary["mean_treatment"] - summary["mean_control"]
                )
                assert abs(summary["effect_size"] - expected_effect) < 1e-6

    def test_domain_distribution(self, tmp_path: Path):
        """Verify that domains are distributed across summaries."""
        summaries = generate_synthetic_dataset(n_records=100, output_dir=tmp_path)

        domains = set(s["domain"] for s in summaries)
        # Should have multiple domains
        assert len(domains) > 1

    def test_year_distribution(self, tmp_path: Path):
        """Verify that years are distributed across summaries."""
        summaries = generate_synthetic_dataset(n_records=100, output_dir=tmp_path)

        years = set(s["year"] for s in summaries)
        # Should have multiple years
        assert len(years) > 1

    def test_csv_content_valid(self, tmp_path: Path):
        """Verify that CSV file contains valid data."""
        generate_synthetic_dataset(n_records=100, output_dir=tmp_path)
        csv_path = tmp_path / "synthetic_summaries.csv"

        with open(csv_path, "r", newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        assert len(rows) == 100

        # Check first row has all required fields
        required_fields = [
            "outcome_type",
            "n_control",
            "n_treatment",
            "p_value",
            "effect_size",
            "domain",
            "year",
        ]
        for field in required_fields:
            assert field in rows[0], f"Missing field in CSV: {field}"

    def test_json_content_valid(self, tmp_path: Path):
        """Verify that JSON file contains valid data."""
        generate_synthetic_dataset(n_records=100, output_dir=tmp_path)
        json_path = tmp_path / "synthetic_summaries.json"

        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        assert isinstance(data, list)
        assert len(data) == 100

        # Check first record has all required fields
        required_fields = [
            "outcome_type",
            "n_control",
            "n_treatment",
            "p_value",
            "effect_size",
            "domain",
            "year",
        ]
        for field in required_fields:
            assert field in data[0], f"Missing field in JSON: {field}"
