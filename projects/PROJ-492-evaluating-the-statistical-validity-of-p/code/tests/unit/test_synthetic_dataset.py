"""
Unit tests for synthetic dataset generator (T026).

Verifies:
- At least 10,000 records are generated
- Both binary and continuous outcomes are present
- Data structure matches expected schema
"""
import csv
import json
import os
import tempfile
from pathlib import Path

import pytest

from code.src.audit.synthetic import (
    generate_synthetic_dataset,
    verify_outcome_types,
    TOTAL_RECORDS,
    SEED
)


class TestSyntheticDatasetGeneration:
    """Tests for the synthetic dataset generator."""

    def test_minimum_record_count(self):
        """Test that at least 10,000 records are generated."""
        with tempfile.TemporaryDirectory() as tmpdir:
            summaries, _ = generate_synthetic_dataset(
                n_records=TOTAL_RECORDS,
                output_dir=tmpdir,
                seed=SEED
            )
            
            assert len(summaries) >= 10000, f"Expected at least 10,000 records, got {len(summaries)}"

    def test_both_outcome_types_present(self):
        """Test that both binary and continuous outcomes are present."""
        with tempfile.TemporaryDirectory() as tmpdir:
            summaries, _ = generate_synthetic_dataset(
                n_records=TOTAL_RECORDS,
                output_dir=tmpdir,
                seed=SEED
            )
            
            assert verify_outcome_types(summaries), "Verification failed: Not all outcome types present"
            
            outcome_types = set(s["outcome_type"] for s in summaries)
            assert "binary" in outcome_types, "Binary outcomes missing"
            assert "continuous" in outcome_types, "Continuous outcomes missing"

    def test_csv_file_created(self):
        """Test that CSV file is created with correct content."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir)
            summaries, _ = generate_synthetic_dataset(
                n_records=100,  # Small sample for testing
                output_dir=tmpdir,
                seed=SEED
            )
            
            csv_file = output_path / "synthetic_summaries.csv"
            assert csv_file.exists(), "CSV file not created"
            
            with open(csv_file, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                rows = list(reader)
            
            assert len(rows) == 100, f"Expected 100 rows, got {len(rows)}"
            
            # Check required columns
            required_columns = [
                "id", "domain", "year", "outcome_type", 
                "n_control", "n_treatment", "reported_p_value", 
                "reconstructed_p_value", "is_inconsistent"
            ]
            
            for col in required_columns:
                assert col in rows[0], f"Missing column: {col}"

    def test_metadata_file_created(self):
        """Test that metadata JSON file is created."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir)
            summaries, metadata = generate_synthetic_dataset(
                n_records=100,
                output_dir=tmpdir,
                seed=SEED
            )
            
            metadata_file = output_path / "synthetic_metadata.json"
            assert metadata_file.exists(), "Metadata file not created"
            
            with open(metadata_file, "r", encoding="utf-8") as f:
                loaded_metadata = json.load(f)
            
            assert loaded_metadata["total_records"] == 100
            assert "binary" in loaded_metadata["outcome_types"]
            assert "continuous" in loaded_metadata["outcome_types"]
            assert loaded_metadata["seed"] == SEED

    def test_data_types_correct(self):
        """Test that generated data has correct types."""
        with tempfile.TemporaryDirectory() as tmpdir:
            summaries, _ = generate_synthetic_dataset(
                n_records=100,
                output_dir=tmpdir,
                seed=SEED
            )
            
            for summary in summaries:
                # Numeric fields
                assert isinstance(summary["n_control"], int)
                assert isinstance(summary["n_treatment"], int)
                assert isinstance(summary["reported_p_value"], float)
                assert isinstance(summary["reconstructed_p_value"], float)
                assert isinstance(summary["year"], int)
                
                # String fields
                assert isinstance(summary["id"], str)
                assert isinstance(summary["domain"], str)
                assert isinstance(summary["outcome_type"], str)
                
                # Boolean field
                assert isinstance(summary["is_inconsistent"], bool)
                
                # Value constraints
                assert summary["outcome_type"] in ["binary", "continuous"]
                assert 0.0 <= summary["reported_p_value"] <= 1.0
                assert 0.0 <= summary["reconstructed_p_value"] <= 1.0
                assert summary["n_control"] >= 50
                assert summary["n_treatment"] >= 50

    def test_deterministic_with_seed(self):
        """Test that generation is deterministic with fixed seed."""
        with tempfile.TemporaryDirectory() as tmpdir:
            summaries1, _ = generate_synthetic_dataset(
                n_records=50,
                output_dir=tmpdir,
                seed=42
            )
            
            summaries2, _ = generate_synthetic_dataset(
                n_records=50,
                output_dir=tmpdir,
                seed=42
            )
            
            # Compare first few records
            for s1, s2 in zip(summaries1[:5], summaries2[:5]):
                assert s1["id"] == s2["id"]
                assert s1["outcome_type"] == s2["outcome_type"]
                assert s1["reported_p_value"] == s2["reported_p_value"]
                assert s1["is_inconsistent"] == s2["is_inconsistent"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
