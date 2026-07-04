"""
Unit tests for the synthetic dataset generator (T026).

Verifies:
- Both binary and continuous outcome types are present
- Output files are created with correct structure
- Record count meets minimum requirement (>= 10,000)
- Statistical properties are reasonable
"""
import csv
import json
import os
import sys
from pathlib import Path
import pytest

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.src.audit.synthetic import (
    generate_synthetic_dataset,
    verify_outcome_types,
    write_csv_output,
    write_json_output,
    DEFAULT_TOTAL_RECORDS
)

class TestSyntheticGenerator:
    """Tests for synthetic dataset generation."""

    def test_generate_dataset_creates_records(self):
        """Test that dataset generation creates the expected number of records."""
        records = generate_synthetic_dataset(total_records=100, seed=42)
        assert len(records) == 100
        assert all(isinstance(r, dict) for r in records)

    def test_outcome_types_present(self):
        """Test that both binary and continuous outcomes are generated."""
        records = generate_synthetic_dataset(total_records=1000, seed=42)
        binary_count, continuous_count = verify_outcome_types(records)
        
        assert binary_count > 0, "Binary outcomes must be present"
        assert continuous_count > 0, "Continuous outcomes must be present"
        assert binary_count + continuous_count == len(records)

    def test_minimum_record_count(self):
        """Test that the default dataset meets the minimum record requirement."""
        records = generate_synthetic_dataset(total_records=DEFAULT_TOTAL_RECORDS, seed=42)
        assert len(records) >= 10000, f"Must have at least 10,000 records, got {len(records)}"

    def test_record_structure_binary(self):
        """Test structure of binary outcome records."""
        records = generate_synthetic_dataset(total_records=100, seed=42)
        binary_records = [r for r in records if r["outcome_type"] == "binary"]
        
        assert len(binary_records) > 0
        
        required_fields = [
            "id", "outcome_type", "is_consistent", "baseline_rate",
            "control_successes", "control_total", "treatment_successes",
            "treatment_total", "reported_p_value", "true_p_value",
            "effect_size", "domain", "year"
        ]
        
        for record in binary_records[:5]:  # Check first 5
            for field in required_fields:
                assert field in record, f"Missing field: {field}"
            assert record["outcome_type"] == "binary"
            assert 0 <= record["reported_p_value"] <= 1
            assert 0 <= record["true_p_value"] <= 1

    def test_record_structure_continuous(self):
        """Test structure of continuous outcome records."""
        records = generate_synthetic_dataset(total_records=100, seed=42)
        continuous_records = [r for r in records if r["outcome_type"] == "continuous"]
        
        assert len(continuous_records) > 0
        
        required_fields = [
            "id", "outcome_type", "is_consistent", "baseline_mean",
            "baseline_std", "control_mean", "control_std", "treatment_mean",
            "treatment_std", "control_total", "treatment_total",
            "reported_p_value", "true_p_value", "effect_size", "domain", "year"
        ]
        
        for record in continuous_records[:5]:  # Check first 5
            for field in required_fields:
                assert field in record, f"Missing field: {field}"
            assert record["outcome_type"] == "continuous"
            assert 0 <= record["reported_p_value"] <= 1
            assert 0 <= record["true_p_value"] <= 1

    def test_csv_output_creation(self, tmp_path):
        """Test that CSV output is created correctly."""
        records = generate_synthetic_dataset(total_records=100, seed=42)
        output_path = tmp_path / "test_output.csv"
        
        write_csv_output(records, output_path)
        
        assert output_path.exists(), "CSV file should be created"
        
        with open(output_path, 'r', newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
        
        assert len(rows) == 100
        assert "outcome_type" in rows[0]
        assert "reported_p_value" in rows[0]

    def test_json_output_creation(self, tmp_path):
        """Test that JSON output is created correctly."""
        records = generate_synthetic_dataset(total_records=100, seed=42)
        output_path = tmp_path / "test_output.json"
        
        write_json_output(records, output_path)
        
        assert output_path.exists(), "JSON file should be created"
        
        with open(output_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        assert "metadata" in data
        assert "records" in data
        assert len(data["records"]) == 100
        assert data["metadata"]["total_records"] == 100

    def test_consistency_flags(self):
        """Test that consistency flags are properly set."""
        records = generate_synthetic_dataset(total_records=1000, seed=42)
        
        consistent_count = sum(1 for r in records if r["is_consistent"])
        inconsistent_count = sum(1 for r in records if not r["is_consistent"])
        
        assert consistent_count + inconsistent_count == len(records)
        # With CONSISTENT_RATIO = 0.85, expect roughly 85% consistent
        assert 0.80 <= consistent_count / len(records) <= 0.90

    def test_p_value_ranges(self):
        """Test that p-values are within valid ranges."""
        records = generate_synthetic_dataset(total_records=100, seed=42)
        
        for record in records:
            assert 0.0 <= record["reported_p_value"] <= 1.0
            assert 0.0 <= record["true_p_value"] <= 1.0

    def test_sample_sizes_reasonable(self):
        """Test that sample sizes are within expected ranges."""
        records = generate_synthetic_dataset(total_records=100, seed=42)
        
        for record in records:
            if "control_total" in record:
                assert record["control_total"] >= 100
                assert record["control_total"] <= 50000
            if "treatment_total" in record:
                assert record["treatment_total"] >= 100
                assert record["treatment_total"] <= 50000

    def test_domains_and_years(self):
        """Test that domains and years are from expected sets."""
        records = generate_synthetic_dataset(total_records=100, seed=42)
        
        valid_domains = {"tech", "health", "finance", "education", "retail"}
        valid_years = {2020, 2021, 2022, 2023, 2024}
        
        for record in records:
            assert record["domain"] in valid_domains
            assert record["year"] in valid_years

    def test_deterministic_with_seed(self):
        """Test that same seed produces same results."""
        records1 = generate_synthetic_dataset(total_records=50, seed=123)
        records2 = generate_synthetic_dataset(total_records=50, seed=123)
        
        # Compare first few fields
        for r1, r2 in zip(records1, records2):
            assert r1["id"] == r2["id"]
            assert r1["outcome_type"] == r2["outcome_type"]
            assert r1["reported_p_value"] == r2["reported_p_value"]
            assert r1["true_p_value"] == r2["true_p_value"]

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
