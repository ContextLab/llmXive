"""
Unit tests for the synthetic dataset generator (T026).
"""

import json
import csv
import os
import tempfile
from pathlib import Path
import pytest

from code.src.audit.synthetic import (
    generate_synthetic_dataset,
    verify_outcome_types,
    write_csv_output,
    write_json_output,
    write_metadata,
    main
)
from code.src.config import SEED


class TestSyntheticGenerator:
    """Tests for synthetic data generation logic."""

    def test_generation_creates_expected_count(self):
        """Verify that the generator creates the requested number of records."""
        target_count = 100
        records = generate_synthetic_dataset(total_records=target_count, seed=SEED)
        assert len(records) == target_count

    def test_both_outcome_types_present(self):
        """Verify that both binary and continuous outcomes are generated."""
        records = generate_synthetic_dataset(total_records=1000, seed=SEED)
        binary_count, continuous_count = verify_outcome_types(records)
        
        assert binary_count > 0, "No binary outcomes generated"
        assert continuous_count > 0, "No continuous outcomes generated"
        assert binary_count + continuous_count == len(records)

    def test_binary_record_structure(self):
        """Verify structure of binary outcome records."""
        records = generate_synthetic_dataset(total_records=100, binary_ratio=1.0, seed=SEED)
        for record in records:
            assert record["outcome_type"] == "binary"
            assert "successes_control" in record
            assert "successes_treatment" in record
            assert "rate_control" in record
            assert "rate_treatment" in record

    def test_continuous_record_structure(self):
        """Verify structure of continuous outcome records."""
        records = generate_synthetic_dataset(total_records=100, binary_ratio=0.0, seed=SEED)
        for record in records:
            assert record["outcome_type"] == "continuous"
            assert "mean_control" in record
            assert "mean_treatment" in record
            assert "std_control" in record
            assert "std_treatment" in record

    def test_inconsistency_flagging(self):
        """Verify that inconsistency flags are set correctly."""
        # High inconsistency rate to ensure some are generated
        records = generate_synthetic_dataset(
            total_records=200, 
            inconsistency_rate=0.5, 
            seed=SEED
        )
        inconsistent_count = sum(1 for r in records if r.get("is_inconsistent", False))
        # Should be roughly 50%
        assert inconsistent_count > 0

    def test_csv_output_creation(self):
        """Verify CSV output file is created and readable."""
        records = generate_synthetic_dataset(total_records=50, seed=SEED)
        
        with tempfile.TemporaryDirectory() as tmpdir:
            csv_path = Path(tmpdir) / "test.csv"
            write_csv_output(records, csv_path)
            
            assert csv_path.exists()
            
            with open(csv_path, 'r', newline='', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                rows = list(reader)
                
            assert len(rows) == 50
            assert "outcome_type" in rows[0]

    def test_json_output_creation(self):
        """Verify JSON output file is created and readable."""
        records = generate_synthetic_dataset(total_records=50, seed=SEED)
        
        with tempfile.TemporaryDirectory() as tmpdir:
            json_path = Path(tmpdir) / "test.json"
            write_json_output(records, json_path)
            
            assert json_path.exists()
            
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            assert len(data) == 50
            assert data[0]["outcome_type"] in ["binary", "continuous"]

    def test_metadata_creation(self):
        """Verify metadata file contains correct counts."""
        records = generate_synthetic_dataset(total_records=100, seed=SEED)
        
        with tempfile.TemporaryDirectory() as tmpdir:
            meta_path = Path(tmpdir) / "meta.json"
            write_metadata(records, meta_path)
            
            assert meta_path.exists()
            
            with open(meta_path, 'r', encoding='utf-8') as f:
                meta = json.load(f)
                
            assert meta["total_records"] == 100
            assert "binary_outcomes" in meta
            assert "continuous_outcomes" in meta

    def test_minimum_record_threshold(self):
        """Verify that the generator can produce >= 10,000 records."""
        records = generate_synthetic_dataset(total_records=10000, seed=SEED)
        assert len(records) >= 10000

    def test_deterministic_seed(self):
        """Verify that same seed produces same results."""
        records1 = generate_synthetic_dataset(total_records=100, seed=42)
        records2 = generate_synthetic_dataset(total_records=100, seed=42)
        
        assert len(records1) == len(records2)
        assert records1[0]["id"] == records2[0]["id"]
        assert records1[0]["outcome_type"] == records2[0]["outcome_type"]

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
