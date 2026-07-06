"""
Unit tests for T026 Synthetic Dataset Generator.
Verifies generation of >= 10,000 records with both binary and continuous outcomes.
"""
import csv
import json
import sys
from pathlib import Path
from datetime import datetime

import pytest

# Add project root to path
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from code.src.audit.synthetic import (
    generate_synthetic_dataset,
    verify_outcome_types,
    write_csv_output,
    write_json_output,
    main
)
from code.src.config import SEED


class TestSyntheticGenerator:
    """Tests for the synthetic dataset generator."""

    def test_generates_minimum_records(self):
        """Verify that at least 10,000 records are generated."""
        records = generate_synthetic_dataset(total_records=10000, seed=SEED)
        assert len(records) >= 10000, f"Expected >= 10000 records, got {len(records)}"

    def test_generates_binary_outcomes(self):
        """Verify that binary outcomes are present."""
        records = generate_synthetic_dataset(total_records=10000, seed=SEED)
        binary, continuous = verify_outcome_types(records)
        assert binary > 0, "No binary outcomes generated"

    def test_generates_continuous_outcomes(self):
        """Verify that continuous outcomes are present."""
        records = generate_synthetic_dataset(total_records=10000, seed=SEED)
        binary, continuous = verify_outcome_types(records)
        assert continuous > 0, "No continuous outcomes generated"

    def test_mixed_outcome_types(self):
        """Verify that the dataset contains a mix of outcome types."""
        records = generate_synthetic_dataset(total_records=10000, binary_ratio=0.5, seed=SEED)
        binary, continuous = verify_outcome_types(records)
        
        # Should be roughly 50/50 with some tolerance
        total = len(records)
        assert 0.4 * total <= binary <= 0.6 * total, f"Binary ratio out of expected range: {binary/total}"
        assert 0.4 * total <= continuous <= 0.6 * total, f"Continuous ratio out of expected range: {continuous/total}"

    def test_record_structure_binary(self):
        """Verify structure of binary outcome records."""
        records = generate_synthetic_dataset(total_records=100, binary_ratio=1.0, seed=SEED)
        for rec in records:
            assert "outcome_type" in rec
            assert rec["outcome_type"] == "binary"
            assert "n_control" in rec
            assert "n_treatment" in rec
            assert "x_control" in rec
            assert "x_treatment" in rec
            assert "p_value_reported" in rec
            assert "is_inconsistent" in rec

    def test_record_structure_continuous(self):
        """Verify structure of continuous outcome records."""
        records = generate_synthetic_dataset(total_records=100, binary_ratio=0.0, seed=SEED)
        for rec in records:
            assert "outcome_type" in rec
            assert rec["outcome_type"] == "continuous"
            assert "mean_control" in rec
            assert "mean_treatment" in rec
            assert "std_control" in rec
            assert "std_treatment" in rec
            assert "p_value_reported" in rec

    def test_csv_output_creation(self, tmp_path):
        """Verify CSV output is created and readable."""
        records = generate_synthetic_dataset(total_records=100, seed=SEED)
        output_path = tmp_path / "test_output.csv"
        
        write_csv_output(records, output_path)
        
        assert output_path.exists(), "CSV file not created"
        
        with open(output_path, "r", newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            rows = list(reader)
        
        assert len(rows) == len(records), "CSV row count mismatch"

    def test_json_output_creation(self, tmp_path):
        """Verify JSON output is created and readable."""
        records = generate_synthetic_dataset(total_records=100, seed=SEED)
        output_path = tmp_path / "test_output.json"
        
        write_json_output(records, output_path)
        
        assert output_path.exists(), "JSON file not created"
        
        with open(output_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        assert len(data) == len(records), "JSON record count mismatch"

    def test_deterministic_seed(self):
        """Verify that the same seed produces the same results."""
        seed_val = 12345
        records1 = generate_synthetic_dataset(total_records=100, seed=seed_val)
        records2 = generate_synthetic_dataset(total_records=100, seed=seed_val)
        
        # Compare key fields
        for r1, r2 in zip(records1, records2):
            assert r1["n_control"] == r2["n_control"]
            assert r1["p_value_reported"] == r2["p_value_reported"]
            assert r1["is_inconsistent"] == r2["is_inconsistent"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
