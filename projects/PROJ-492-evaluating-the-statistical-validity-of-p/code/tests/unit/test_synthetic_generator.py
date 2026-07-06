"""
Unit tests for the synthetic dataset generator (T026).

Verifies:
- Dataset generation produces at least 10,000 records
- Both binary and continuous outcomes are present
- Data types and ranges are valid
"""
import pytest
from pathlib import Path
import json
import csv
import sys
import os

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.src.audit.synthetic import (
    generate_synthetic_dataset,
    verify_outcome_types,
    write_csv_output,
    write_json_output,
    MIN_RECORDS
)
from code.src.config import SEED

class TestSyntheticDatasetGenerator:
    """Tests for the synthetic dataset generator."""

    def test_minimum_record_count(self):
        """Test that the generator produces at least 10,000 records."""
        records = generate_synthetic_dataset(MIN_RECORDS)
        assert len(records) >= MIN_RECORDS, f"Expected at least {MIN_RECORDS} records, got {len(records)}"

    def test_both_outcome_types_present(self):
        """Test that both binary and continuous outcomes are present."""
        records = generate_synthetic_dataset(MIN_RECORDS)
        outcome_counts = verify_outcome_types(records)
        
        assert outcome_counts["binary"] > 0, "Binary outcomes must be present"
        assert outcome_counts["continuous"] > 0, "Continuous outcomes must be present"

    def test_record_structure_binary(self):
        """Test that binary outcome records have correct structure."""
        records = generate_synthetic_dataset(100)
        binary_records = [r for r in records if r["outcome_type"] == "binary"]
        
        assert len(binary_records) > 0, "No binary records found"
        
        required_fields = [
            "id", "url", "domain", "year", "title", "description",
            "outcome_type", "n_control", "n_treatment",
            "p_value", "effect_size",
            "successes_control", "successes_treatment", "rate_control", "rate_treatment"
        ]
        
        for record in binary_records[:5]:  # Check first 5
            for field in required_fields:
                assert field in record, f"Missing field {field} in binary record"
            
            # Validate numeric ranges
            assert 0 <= record["rate_control"] <= 1, "Rate must be between 0 and 1"
            assert 0 <= record["rate_treatment"] <= 1, "Rate must be between 0 and 1"
            assert 0 <= record["p_value"] <= 1, "P-value must be between 0 and 1"
            assert record["n_control"] > 0, "n_control must be positive"
            assert record["n_treatment"] > 0, "n_treatment must be positive"

    def test_record_structure_continuous(self):
        """Test that continuous outcome records have correct structure."""
        records = generate_synthetic_dataset(100)
        continuous_records = [r for r in records if r["outcome_type"] == "continuous"]
        
        assert len(continuous_records) > 0, "No continuous records found"
        
        required_fields = [
            "id", "url", "domain", "year", "title", "description",
            "outcome_type", "n_control", "n_treatment",
            "p_value", "effect_size",
            "mean_control", "mean_treatment", "std_control", "std_treatment"
        ]
        
        for record in continuous_records[:5]:  # Check first 5
            for field in required_fields:
                assert field in record, f"Missing field {field} in continuous record"
            
            # Validate numeric ranges
            assert record["mean_control"] > 0, "Mean must be positive"
            assert record["mean_treatment"] > 0, "Mean must be positive"
            assert record["std_control"] > 0, "Std dev must be positive"
            assert record["std_treatment"] > 0, "Std dev must be positive"
            assert 0 <= record["p_value"] <= 1, "P-value must be between 0 and 1"
            assert record["n_control"] > 0, "n_control must be positive"
            assert record["n_treatment"] > 0, "n_treatment must be positive"

    def test_csv_output_creation(self, tmp_path):
        """Test that CSV output is created correctly."""
        records = generate_synthetic_dataset(100)
        output_path = tmp_path / "test_synthetic.csv"
        
        write_csv_output(records, output_path)
        
        assert output_path.exists(), "CSV file was not created"
        
        with open(output_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
        
        assert len(rows) == len(records), "CSV row count mismatch"
        assert "outcome_type" in rows[0], "CSV missing outcome_type column"

    def test_json_output_creation(self, tmp_path):
        """Test that JSON output is created correctly."""
        records = generate_synthetic_dataset(100)
        output_path = tmp_path / "test_synthetic.json"
        
        write_json_output(records, output_path)
        
        assert output_path.exists(), "JSON file was not created"
        
        with open(output_path, 'r', encoding='utf-8') as f:
            loaded_records = json.load(f)
        
        assert len(loaded_records) == len(records), "JSON record count mismatch"
        assert loaded_records[0]["outcome_type"] in ["binary", "continuous"]

    def test_deterministic_with_seed(self):
        """Test that generation is deterministic with the same seed."""
        # First run
        records1 = generate_synthetic_dataset(50)
        
        # Second run (should be identical due to seed reset in function)
        records2 = generate_synthetic_dataset(50)
        
        # Compare key fields
        assert len(records1) == len(records2)
        for r1, r2 in zip(records1[:10], records2[:10]):
            assert r1["p_value"] == r2["p_value"], "P-values should be identical"
            assert r1["outcome_type"] == r2["outcome_type"], "Outcome types should be identical"

    def test_outcome_ratio_reasonable(self):
        """Test that the ratio of binary to continuous outcomes is reasonable."""
        records = generate_synthetic_dataset(MIN_RECORDS)
        outcome_counts = verify_outcome_types(records)
        
        total = outcome_counts["binary"] + outcome_counts["continuous"]
        binary_ratio = outcome_counts["binary"] / total
        
        # Should be close to 0.5 (allowing for some randomness)
        assert 0.4 <= binary_ratio <= 0.6, f"Binary ratio {binary_ratio} is outside expected range"

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
