"""
Unit tests for the synthetic dataset generator (Task T026).
"""
import json
import csv
import os
from pathlib import Path
import pytest

# Import the generator functions
from code.src.audit.synthetic import (
    generate_synthetic_dataset,
    verify_outcome_types,
    write_csv_output,
    write_json_output,
    main
)


class TestSyntheticGenerator:
    """Tests for synthetic dataset generation logic."""

    def test_generate_minimum_records(self):
        """Verify that at least 10,000 records are generated."""
        records = generate_synthetic_dataset(total_records=10000)
        assert len(records) >= 10000, f"Expected >= 10000 records, got {len(records)}"

    def test_both_outcome_types_present(self):
        """Verify that both binary and continuous outcomes are present."""
        records = generate_synthetic_dataset(total_records=10000)
        binary_count, continuous_count = verify_outcome_types(records)
        
        assert binary_count > 0, "Binary outcomes must be present"
        assert continuous_count > 0, "Continuous outcomes must be present"

    def test_record_structure_binary(self):
        """Verify structure of binary outcome records."""
        records = generate_synthetic_dataset(total_records=100)
        binary_records = [r for r in records if r["outcome_type"] == "binary"]
        
        assert len(binary_records) > 0
        
        required_fields = [
            "id", "outcome_type", "domain", "year", "is_inconsistent",
            "n_control", "n_treatment", "successes_control", "successes_treatment",
            "rate_control", "rate_treatment", "lift", "p_value"
        ]
        
        for rec in binary_records[:5]: # Check first 5
            for field in required_fields:
                assert field in rec, f"Missing field {field} in binary record"

    def test_record_structure_continuous(self):
        """Verify structure of continuous outcome records."""
        records = generate_synthetic_dataset(total_records=100)
        continuous_records = [r for r in records if r["outcome_type"] == "continuous"]
        
        assert len(continuous_records) > 0
        
        required_fields = [
            "id", "outcome_type", "domain", "year", "is_inconsistent",
            "n_control", "n_treatment", "mean_control", "mean_treatment",
            "std_control", "std_treatment", "difference", "p_value"
        ]
        
        for rec in continuous_records[:5]:
            for field in required_fields:
                assert field in rec, f"Missing field {field} in continuous record"

    def test_data_types_valid(self):
        """Verify data types are valid (integers for N, floats for rates/p-values)."""
        records = generate_synthetic_dataset(total_records=100)
        
        for rec in records:
            assert isinstance(rec["n_control"], int)
            assert isinstance(rec["n_treatment"], int)
            assert 0.0 <= rec["p_value"] <= 1.0
            assert isinstance(rec["is_inconsistent"], bool)

    def test_csv_output_creation(self, tmp_path):
        """Test that CSV output file is created and valid."""
        records = generate_synthetic_dataset(total_records=100)
        csv_path = tmp_path / "test_output.csv"
        
        write_csv_output(records, csv_path)
        
        assert csv_path.exists()
        
        with open(csv_path, "r") as f:
            reader = csv.DictReader(f)
            rows = list(reader)
        
        assert len(rows) == len(records)

    def test_json_output_creation(self, tmp_path):
        """Test that JSON output file is created and valid."""
        records = generate_synthetic_dataset(total_records=100)
        json_path = tmp_path / "test_output.json"
        
        write_json_output(records, json_path)
        
        assert json_path.exists()
        
        with open(json_path, "r") as f:
            loaded_records = json.load(f)
        
        assert len(loaded_records) == len(records)

    def test_inconsistency_flag_present(self):
        """Verify that is_inconsistent flag is present and boolean."""
        records = generate_synthetic_dataset(total_records=100)
        
        for rec in records:
            assert "is_inconsistent" in rec
            assert isinstance(rec["is_inconsistent"], bool)

    def test_reproducibility(self):
        """Verify that generation is reproducible with same seed."""
        # Note: This test relies on the global seed setting in generate_synthetic_dataset
        # which sets SEED=42 by default.
        records1 = generate_synthetic_dataset(total_records=50)
        records2 = generate_synthetic_dataset(total_records=50)
        
        # Since set_all_seeds is called inside, they should be identical
        # We compare a few key fields to avoid deep comparison of all dicts
        assert records1[0]["id"] == records2[0]["id"]
        assert records1[0]["p_value"] == records2[0]["p_value"]
        assert records1[0]["outcome_type"] == records2[0]["outcome_type"]

if __name__ == "__main__":
    pytest.main([__file__, "-v"])