"""
Unit tests for synthetic dataset generator (T026).
"""
import json
import csv
from pathlib import Path
import pytest

from code.src.audit.synthetic import (
    set_all_seeds,
    generate_sample_sizes,
    generate_binary_outcome,
    generate_continuous_outcome,
    generate_synthetic_dataset,
    verify_outcome_types,
    write_csv_output,
    write_json_output,
    write_metadata
)


class TestSyntheticGenerator:
    """Test suite for synthetic dataset generation."""

    def test_set_all_seeds_determinism(self):
        """Verify that setting seeds produces deterministic results."""
        set_all_seeds(42)
        result1 = generate_sample_sizes()

        set_all_seeds(42)
        result2 = generate_sample_sizes()

        assert result1 == result2, "Seed setting should produce deterministic results"

    def test_generate_sample_sizes_range(self):
        """Verify sample sizes are within expected range."""
        n_control, n_treatment = generate_sample_sizes(100, 1000)

        assert 100 <= n_control <= 1000, "Control sample size out of range"
        assert 100 <= n_treatment <= 1100, "Treatment sample size out of range"
        assert abs(n_treatment - n_control) <= n_control * 0.15, "Treatment size too different from control"

    def test_generate_binary_outcome_structure(self):
        """Verify binary outcome has all required fields."""
        record = generate_binary_outcome(1000, 1000, 0.1, 0.02)

        required_fields = [
            "outcome_type", "n_control", "n_treatment",
            "control_conversions", "treatment_conversions",
            "baseline_rate", "treatment_rate", "effect_size",
            "true_p_value", "reported_p_value", "is_inconsistent"
        ]

        for field in required_fields:
            assert field in record, f"Missing required field: {field}"

        assert record["outcome_type"] == "binary"
        assert 0 <= record["baseline_rate"] <= 1
        assert 0 <= record["treatment_rate"] <= 1

    def test_generate_continuous_outcome_structure(self):
        """Verify continuous outcome has all required fields."""
        record = generate_continuous_outcome(1000, 1000, 50.0, 10.0, 2.0)

        required_fields = [
            "outcome_type", "n_control", "n_treatment",
            "control_mean", "treatment_mean", "control_std", "treatment_std",
            "effect_size", "true_p_value", "reported_p_value", "is_inconsistent"
        ]

        for field in required_fields:
            assert field in record, f"Missing required field: {field}"

        assert record["outcome_type"] == "continuous"
        assert record["control_std"] > 0
        assert record["treatment_std"] > 0

    def test_generate_synthetic_dataset_minimum_records(self):
        """Verify dataset meets minimum record count."""
        records = generate_synthetic_dataset(n_records=10000)

        assert len(records) >= 10000, f"Expected at least 10000 records, got {len(records)}"

    def test_generate_synthetic_dataset_both_outcome_types(self):
        """Verify both binary and continuous outcomes are present."""
        records = generate_synthetic_dataset(n_records=10000)

        outcome_counts = verify_outcome_types(records)

        assert outcome_counts["binary"] > 0, "No binary outcomes generated"
        assert outcome_counts["continuous"] > 0, "No continuous outcomes generated"
        assert outcome_counts["binary"] + outcome_counts["continuous"] == len(records)

    def test_generate_synthetic_dataset_required_fields(self):
        """Verify all records have required metadata fields."""
        records = generate_synthetic_dataset(n_records=100)

        required_fields = ["id", "outcome_type", "domain", "year"]

        for record in records:
            for field in required_fields:
                assert field in record, f"Missing field {field} in record {record.get('id')}"

            assert record["domain"] in ["ecommerce", "finance", "healthcare", "tech", "education"]
            assert 2020 <= record["year"] <= 2024

    def test_write_csv_output(self, tmp_path):
        """Verify CSV output is correctly formatted."""
        records = generate_synthetic_dataset(n_records=100)
        csv_path = tmp_path / "test.csv"

        write_csv_output(records, csv_path)

        assert csv_path.exists(), "CSV file not created"

        with open(csv_path, 'r') as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        assert len(rows) == 100, f"Expected 100 rows, got {len(rows)}"
        assert "outcome_type" in rows[0], "Missing outcome_type column"

    def test_write_json_output(self, tmp_path):
        """Verify JSON output is valid and contains all records."""
        records = generate_synthetic_dataset(n_records=100)
        json_path = tmp_path / "test.json"

        write_json_output(records, json_path)

        assert json_path.exists(), "JSON file not created"

        with open(json_path, 'r') as f:
            loaded_records = json.load(f)

        assert len(loaded_records) == 100, f"Expected 100 records, got {len(loaded_records)}"

    def test_verify_outcome_types_raises_on_missing_type(self):
        """Verify function raises error if a type is missing."""
        # Create records with only binary outcomes
        binary_only = [
            {"outcome_type": "binary", "id": "1"},
            {"outcome_type": "binary", "id": "2"}
        ]

        with pytest.raises(ValueError, match="No continuous outcomes generated"):
            verify_outcome_types(binary_only)

    def test_inconsistent_flag_distribution(self):
        """Verify inconsistency rate is approximately as specified."""
        records = generate_synthetic_dataset(n_records=1000, inconsistency_rate=0.2)

        inconsistent_count = sum(1 for r in records if r.get("is_inconsistent"))
        actual_rate = inconsistent_count / len(records)

        # Allow 10% tolerance
        assert 0.18 <= actual_rate <= 0.22, f"Inconsistency rate {actual_rate} outside expected range"

    def test_p_value_range(self):
        """Verify p-values are in valid range [0, 1]."""
        records = generate_synthetic_dataset(n_records=100)

        for record in records:
            assert 0 <= record["true_p_value"] <= 1, f"Invalid true_p_value: {record['true_p_value']}"
            assert 0 <= record["reported_p_value"] <= 1, f"Invalid reported_p_value: {record['reported_p_value']}"
