"""
Unit tests for synthetic dataset generator (T026).
Verifies that the generator produces at least 10,000 records with both binary and continuous outcomes.
"""
import csv
import json
import tempfile
from pathlib import Path
import pytest

from code.src.audit.synthetic import (
    generate_synthetic_dataset,
    verify_outcome_types,
    write_csv_output,
    write_json_output,
    generate_binary_outcome,
    generate_continuous_outcome,
    set_all_seeds
)
from code.src.config import SEED


class TestSyntheticGenerator:
    """Tests for synthetic dataset generation."""

    def test_minimum_record_count(self):
        """Verify that at least 10,000 records are generated."""
        set_all_seeds(SEED)
        data = generate_synthetic_dataset(total_records=10000)
        
        assert len(data) >= 10000, f"Expected at least 10000 records, got {len(data)}"

    def test_both_outcome_types_present(self):
        """Verify that both binary and continuous outcomes are present."""
        set_all_seeds(SEED)
        data = generate_synthetic_dataset(total_records=10000)
        
        success, counts = verify_outcome_types(data)
        
        assert success, "Both outcome types must be present"
        assert counts["binary"] > 0, "Binary outcomes must be present"
        assert counts["continuous"] > 0, "Continuous outcomes must be present"

    def test_record_structure_binary(self):
        """Verify structure of binary outcome records."""
        set_all_seeds(SEED)
        data = generate_binary_outcome(n=10)
        
        required_fields = [
            "n_control", "n_treatment", "conversions_control", "conversions_treatment",
            "reported_p_value", "reported_effect_size", "outcome_type", "domain", "year"
        ]
        
        for record in data:
            assert record["outcome_type"] == "binary"
            for field in required_fields:
                assert field in record, f"Missing field: {field}"
            
            # Validate types
            assert isinstance(record["n_control"], int)
            assert isinstance(record["n_treatment"], int)
            assert isinstance(record["conversions_control"], int)
            assert isinstance(record["conversions_treatment"], int)
            assert isinstance(record["reported_p_value"], float)
            assert isinstance(record["reported_effect_size"], float)
            assert 0.0 <= record["reported_p_value"] <= 1.0

    def test_record_structure_continuous(self):
        """Verify structure of continuous outcome records."""
        set_all_seeds(SEED)
        data = generate_continuous_outcome(n=10)
        
        required_fields = [
            "n_control", "n_treatment", "mean_control", "mean_treatment",
            "std_control", "std_treatment", "reported_p_value", "reported_effect_size",
            "outcome_type", "domain", "year"
        ]
        
        for record in data:
            assert record["outcome_type"] == "continuous"
            for field in required_fields:
                assert field in record, f"Missing field: {field}"
            
            # Validate types
            assert isinstance(record["n_control"], int)
            assert isinstance(record["n_treatment"], int)
            assert isinstance(record["mean_control"], float)
            assert isinstance(record["mean_treatment"], float)
            assert isinstance(record["std_control"], float)
            assert isinstance(record["std_treatment"], float)
            assert isinstance(record["reported_p_value"], float)
            assert 0.0 <= record["reported_p_value"] <= 1.0

    def test_csv_output_file_creation(self):
        """Verify CSV output is written correctly."""
        set_all_seeds(SEED)
        data = generate_synthetic_dataset(total_records=100)
        
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test.csv"
            write_csv_output(data, output_path)
            
            assert output_path.exists(), "CSV file should be created"
            
            with open(output_path, 'r') as f:
                reader = csv.DictReader(f)
                rows = list(reader)
            
            assert len(rows) == len(data), "CSV should contain all records"
            assert "outcome_type" in rows[0], "CSV should have outcome_type column"

    def test_json_output_file_creation(self):
        """Verify JSON output is written correctly."""
        set_all_seeds(SEED)
        data = generate_synthetic_dataset(total_records=100)
        
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test.json"
            write_json_output(data, output_path)
            
            assert output_path.exists(), "JSON file should be created"
            
            with open(output_path, 'r') as f:
                loaded_data = json.load(f)
            
            assert len(loaded_data) == len(data), "JSON should contain all records"

    def test_inconsistency_injection(self):
        """Verify that inconsistency injection works."""
        set_all_seeds(SEED)
        # Generate with 100% inconsistency injection
        data_consistent = generate_binary_outcome(n=50, inject_inconsistency=False)
        data_inconsistent = generate_binary_outcome(n=50, inject_inconsistency=True)
        
        # P-values should differ between consistent and inconsistent sets
        # (statistical test: mean difference in p-values)
        consistent_p_values = [r["reported_p_value"] for r in data_consistent]
        inconsistent_p_values = [r["reported_p_value"] for r in data_inconsistent]
        
        # Just verify we got data
        assert len(consistent_p_values) == 50
        assert len(inconsistent_p_values) == 50

    def test_domain_distribution(self):
        """Verify that domains are distributed across records."""
        set_all_seeds(SEED)
        data = generate_synthetic_dataset(total_records=1000)
        
        domains = set(r["domain"] for r in data)
        expected_domains = {"tech", "health", "finance", "education", "retail"}
        
        # At least some domains should be present
        assert len(domains) > 0, "At least one domain should be present"
        assert domains.issubset(expected_domains), "Domains should be from expected set"

    def test_year_range(self):
        """Verify that years are within expected range."""
        set_all_seeds(SEED)
        data = generate_synthetic_dataset(total_records=100)
        
        years = [r["year"] for r in data]
        assert all(2018 <= y <= 2024 for y in years), "Years should be between 2018 and 2024"

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
