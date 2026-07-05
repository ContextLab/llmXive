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
    write_csv_output,
    write_json_output,
    verify_outcome_types
)


class TestSyntheticGenerator:
    """Test suite for synthetic dataset generation."""

    def test_set_all_seeds_reproducibility(self):
        """Test that setting seeds produces reproducible results."""
        set_all_seeds(42)
        result1 = generate_sample_sizes()

        set_all_seeds(42)
        result2 = generate_sample_sizes()

        assert result1 == result2, "Seed setting should produce reproducible results"

    def test_generate_sample_sizes_bounds(self):
        """Test that sample sizes are within expected bounds."""
        n_control, n_treatment = generate_sample_sizes()
        assert n_control >= 100, "Control sample size should be at least 100"
        assert n_treatment >= 100, "Treatment sample size should be at least 100"

    def test_binary_outcome_structure(self):
        """Test binary outcome generation produces correct structure."""
        result = generate_binary_outcome(1000, 1000, 0.1, 0.05, False)

        required_fields = [
            "outcome_type", "n_control", "n_treatment",
            "successes_control", "successes_treatment",
            "observed_p_control", "observed_p_treatment",
            "observed_effect", "true_p_value", "reported_p_value",
            "reported_effect", "is_inconsistent",
            "true_baseline_rate", "true_effect_size"
        ]

        for field in required_fields:
            assert field in result, f"Missing field: {field}"

        assert result["outcome_type"] == "binary"
        assert isinstance(result["successes_control"], int)
        assert isinstance(result["successes_treatment"], int)
        assert 0 <= result["true_p_value"] <= 1

    def test_continuous_outcome_structure(self):
        """Test continuous outcome generation produces correct structure."""
        result = generate_continuous_outcome(1000, 1000, 50.0, 5.0, 10.0, False)

        required_fields = [
            "outcome_type", "n_control", "n_treatment",
            "observed_mean_control", "observed_mean_treatment",
            "observed_std_control", "observed_std_treatment",
            "observed_effect", "true_p_value", "reported_p_value",
            "reported_effect", "is_inconsistent",
            "true_baseline_mean", "true_effect_size", "true_baseline_std"
        ]

        for field in required_fields:
            assert field in result, f"Missing field: {field}"

        assert result["outcome_type"] == "continuous"
        assert 0 <= result["true_p_value"] <= 1

    def test_inconsistency_injection(self):
        """Test that inconsistency flag affects reported values."""
        consistent = generate_binary_outcome(1000, 1000, 0.1, 0.05, False)
        inconsistent = generate_binary_outcome(1000, 1000, 0.1, 0.05, True)

        assert consistent["is_inconsistent"] == False
        assert inconsistent["is_inconsistent"] == True

        # Inconsistent should have different reported values
        assert consistent["reported_p_value"] != inconsistent["reported_p_value"]

    def test_generate_synthetic_dataset_size(self):
        """Test that dataset generation produces correct number of records."""
        csv_records, ground_truth_records = generate_synthetic_dataset(n_records=100)

        assert len(csv_records) == 100
        assert len(ground_truth_records) == 100

    def test_generate_synthetic_dataset_outcome_types(self):
        """Test that both outcome types are present in generated dataset."""
        csv_records, ground_truth_records = generate_synthetic_dataset(n_records=1000)

        binary_count, continuous_count = verify_outcome_types(ground_truth_records)

        assert binary_count > 0, "Should have binary outcomes"
        assert continuous_count > 0, "Should have continuous outcomes"
        assert binary_count + continuous_count == 1000

    def test_write_csv_output(self, tmp_path):
        """Test CSV output writing."""
        records = [
            {"id": "1", "value": 10, "outcome_type": "binary"},
            {"id": "2", "value": 20, "outcome_type": "continuous"}
        ]

        output_path = tmp_path / "test.csv"
        write_csv_output(records, output_path)

        assert output_path.exists()

        with open(output_path, 'r') as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        assert len(rows) == 2
        assert rows[0]["id"] == "1"
        assert rows[1]["id"] == "2"

    def test_write_json_output(self, tmp_path):
        """Test JSON output writing."""
        records = [
            {"id": "1", "value": 10, "outcome_type": "binary"},
            {"id": "2", "value": 20, "outcome_type": "continuous"}
        ]

        output_path = tmp_path / "test.json"
        write_json_output(records, output_path)

        assert output_path.exists()

        with open(output_path, 'r') as f:
            data = json.load(f)

        assert "metadata" in data
        assert "records" in data
        assert len(data["records"]) == 2

    def test_verify_outcome_types_raises_on_missing(self):
        """Test that verification raises error if outcome type is missing."""
        binary_only = [{"outcome_type": "binary"}]
        continuous_only = [{"outcome_type": "continuous"}]

        with pytest.raises(ValueError, match="No continuous outcomes"):
            verify_outcome_types(binary_only)

        with pytest.raises(ValueError, match="No binary outcomes"):
            verify_outcome_types(continuous_only)

    def test_full_pipeline_integration(self, tmp_path):
        """Test full synthetic dataset generation pipeline."""
        csv_path = tmp_path / "synthetic_validation.csv"
        json_path = tmp_path / "synthetic_ground_truth.json"

        # Generate dataset
        csv_records, ground_truth_records = generate_synthetic_dataset(n_records=500)

        # Write outputs
        write_csv_output(csv_records, csv_path)
        write_json_output(ground_truth_records, json_path)

        # Verify files exist
        assert csv_path.exists()
        assert json_path.exists()

        # Verify CSV content
        with open(csv_path, 'r') as f:
            reader = csv.DictReader(f)
            csv_rows = list(reader)
        assert len(csv_rows) == 500

        # Verify JSON content
        with open(json_path, 'r') as f:
            data = json.load(f)
        assert len(data["records"]) == 500
        assert data["metadata"]["total_records"] == 500
        assert data["metadata"]["binary_count"] > 0
        assert data["metadata"]["continuous_count"] > 0