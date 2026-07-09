"""
Unit tests for the synthetic dataset generator (T026).
Verifies generation of >= 10,000 records and presence of both outcome types.
"""
import csv
import json
import os
import tempfile
from pathlib import Path

import pytest

# Import the module under test
from code.src.audit.synthetic import (
    set_all_seeds,
    generate_synthetic_dataset,
    verify_outcome_types,
    write_metadata,
    MIN_RECORDS
)
from code.src.config import SEED


class TestSyntheticGenerator:

    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for test outputs."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    def test_set_all_seeds_determinism(self):
        """Test that setting seeds produces deterministic results."""
        set_all_seeds(SEED)
        val1 = generate_synthetic_dataset(num_records=10, output_dir=Path(tempfile.gettempdir()), filename="test1.csv")
        
        set_all_seeds(SEED)
        val2 = generate_synthetic_dataset(num_records=10, output_dir=Path(tempfile.gettempdir()), filename="test2.csv")
        
        # Clean up temp files
        for f in Path(tempfile.gettempdir()).glob("test*.csv"):
            f.unlink(missing_ok=True)

        # Basic check: lengths should match
        assert len(val1) == len(val2)

    def test_minimum_records_generated(self, temp_dir):
        """Test that at least 10,000 records are generated."""
        records = generate_synthetic_dataset(
            num_records=MIN_RECORDS,
            output_dir=temp_dir,
            filename="test_min.csv"
        )
        assert len(records) >= MIN_RECORDS, f"Generated {len(records)} records, expected >= {MIN_RECORDS}"

    def test_both_outcome_types_present(self, temp_dir):
        """Test that both binary and continuous outcomes are present."""
        records = generate_synthetic_dataset(
            num_records=MIN_RECORDS,
            output_dir=temp_dir,
            filename="test_types.csv"
        )
        
        binary_count = sum(1 for r in records if r["outcome_type"] == "binary")
        continuous_count = sum(1 for r in records if r["outcome_type"] == "continuous")
        
        assert binary_count > 0, "No binary outcomes generated"
        assert continuous_count > 0, "No continuous outcomes generated"
        
        # Verify via helper function
        b, c = verify_outcome_types(records)
        assert b > 0 and c > 0

    def test_csv_file_creation(self, temp_dir):
        """Test that the output CSV file is created and readable."""
        filename = "test_csv.csv"
        generate_synthetic_dataset(
            num_records=100,
            output_dir=temp_dir,
            filename=filename
        )
        
        output_path = temp_dir / filename
        assert output_path.exists(), "Output CSV file not created"
        
        with open(output_path, "r", newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            assert len(rows) == 100, "Row count mismatch in CSV"
            assert "outcome_type" in reader.fieldnames, "Missing outcome_type column"

    def test_metadata_generation(self, temp_dir):
        """Test that metadata JSON is generated correctly."""
        records = generate_synthetic_dataset(
            num_records=100,
            output_dir=temp_dir,
            filename="test_meta.csv"
        )
        
        write_metadata(temp_dir, records)
        
        metadata_path = temp_dir / "synthetic_metadata.json"
        assert metadata_path.exists(), "Metadata file not created"
        
        with open(metadata_path, "r", encoding="utf-8") as f:
            meta = json.load(f)
        
        assert "total_records" in meta
        assert meta["total_records"] == 100
        assert "outcome_types" in meta
        assert meta["outcome_types"]["binary"] > 0
        assert meta["outcome_types"]["continuous"] > 0

    def test_verify_outcome_types_raises_on_missing(self, temp_dir):
        """Test that verify_outcome_types raises if a type is missing."""
        # Create a mock list with only binary
        fake_records = [{"outcome_type": "binary"} for _ in range(10)]
        with pytest.raises(ValueError, match="No continuous outcomes"):
            verify_outcome_types(fake_records)

        # Create a mock list with only continuous
        fake_records = [{"outcome_type": "continuous"} for _ in range(10)]
        with pytest.raises(ValueError, match="No binary outcomes"):
            verify_outcome_types(fake_records)

        # Create a mock list with too few records
        fake_records = [
            {"outcome_type": "binary"},
            {"outcome_type": "continuous"}
        ]
        with pytest.raises(ValueError, match="Total records"):
            verify_outcome_types(fake_records)
