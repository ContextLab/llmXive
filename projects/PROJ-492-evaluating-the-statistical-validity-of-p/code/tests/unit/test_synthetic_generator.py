"""
Unit tests for the synthetic dataset generator (T026).

Verifies:
- Generation of at least 10,000 records
- Presence of both binary and continuous outcomes
- Correct data structure and field types
"""
import csv
import json
import tempfile
from pathlib import Path
import pytest

from code.src.audit.synthetic import (
    set_all_seeds,
    generate_sample_sizes,
    generate_binary_outcome,
    generate_continuous_outcome,
    generate_synthetic_dataset,
    verify_outcome_types,
    write_metadata
)
from code.src.config import SEED


class TestSyntheticGenerator:
    """Tests for synthetic dataset generation functionality."""

    def test_set_all_seeds_deterministic(self):
        """Test that setting seeds produces deterministic results."""
        set_all_seeds(SEED)
        val1 = generate_sample_sizes()
        
        set_all_seeds(SEED)
        val2 = generate_sample_sizes()
        
        assert val1 == val2, "Seeds should produce deterministic output"

    def test_generate_sample_sizes_range(self):
        """Test that sample sizes are within expected range."""
        for _ in range(10):
            n_control, n_treatment = generate_sample_sizes()
            assert 100 <= n_control <= 10000
            assert 100 <= n_treatment <= 10000

    def test_generate_binary_outcome_structure(self):
        """Test binary outcome generation produces correct structure."""
        record = generate_binary_outcome(1000, 1000)
        
        required_fields = [
            "n_control", "n_treatment", "successes_control", "successes_treatment",
            "rate_control", "rate_treatment", "effect_size", "outcome_type", "test_type"
        ]
        
        for field in required_fields:
            assert field in record, f"Missing field: {field}"
        
        assert record["outcome_type"] == "binary"
        assert record["test_type"] == "two_proportion_z"
        assert 0 <= record["successes_control"] <= record["n_control"]
        assert 0 <= record["successes_treatment"] <= record["n_treatment"]

    def test_generate_continuous_outcome_structure(self):
        """Test continuous outcome generation produces correct structure."""
        record = generate_continuous_outcome(1000, 1000)
        
        required_fields = [
            "n_control", "n_treatment", "mean_control", "mean_treatment",
            "std_control", "std_treatment", "effect_size", "outcome_type", "test_type"
        ]
        
        for field in required_fields:
            assert field in record, f"Missing field: {field}"
        
        assert record["outcome_type"] == "continuous"
        assert record["test_type"] == "welch_t"
        assert record["std_control"] > 0
        assert record["std_treatment"] > 0

    def test_generate_synthetic_dataset_minimum_records(self):
        """Test that dataset generation creates at least 10,000 records."""
        with tempfile.TemporaryDirectory() as tmpdir:
            csv_path = generate_synthetic_dataset(
                n_records=10000,
                output_dir=tmpdir,
                filename="test.csv"
            )
            
            with open(csv_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                record_count = sum(1 for _ in reader)
            
            assert record_count >= 10000, f"Expected at least 10000 records, got {record_count}"

    def test_verify_outcome_types_both_present(self):
        """Test verification confirms both outcome types are present."""
        with tempfile.TemporaryDirectory() as tmpdir:
            csv_path = generate_synthetic_dataset(
                n_records=10000,
                binary_ratio=0.5,
                output_dir=tmpdir,
                filename="test.csv"
            )
            
            is_valid, counts = verify_outcome_types(csv_path)
            
            assert is_valid, "Both outcome types should be present"
            assert counts["binary"] >= 1000
            assert counts["continuous"] >= 1000

    def test_write_metadata_creates_file(self):
        """Test that metadata file is created correctly."""
        with tempfile.TemporaryDirectory() as tmpdir:
            metadata_path = write_metadata(output_dir=tmpdir)
            
            assert metadata_path.exists()
            
            with open(metadata_path, 'r', encoding='utf-8') as f:
                metadata = json.load(f)
            
            assert "generated_at" in metadata
            assert metadata["total_records"] == 10000
            assert "binary" in metadata["outcome_types"]
            assert "continuous" in metadata["outcome_types"]

    def test_csv_field_consistency(self):
        """Test that all records have consistent fields in CSV."""
        with tempfile.TemporaryDirectory() as tmpdir:
            csv_path = generate_synthetic_dataset(
                n_records=100,
                output_dir=tmpdir,
                filename="test.csv"
            )
            
            expected_fields = [
                "id", "outcome_type", "test_type", "n_control", "n_treatment",
                "rate_control", "rate_treatment", "successes_control", "successes_treatment",
                "mean_control", "mean_treatment", "std_control", "std_treatment",
                "effect_size", "domain", "generated_at"
            ]
            
            with open(csv_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    for field in expected_fields:
                        assert field in row, f"Missing field {field} in row"

    def test_binary_outcome_rate_constraints(self):
        """Test that binary outcome rates are valid probabilities."""
        for _ in range(20):
            record = generate_binary_outcome(1000, 1000)
            assert 0.0 <= record["rate_control"] <= 1.0
            assert 0.0 <= record["rate_treatment"] <= 1.0

    def test_continuous_outcome_positive_values(self):
        """Test that continuous outcome means and stds are positive."""
        for _ in range(20):
            record = generate_continuous_outcome(1000, 1000)
            assert record["mean_control"] > 0
            assert record["mean_treatment"] > 0
            assert record["std_control"] > 0
            assert record["std_treatment"] > 0
