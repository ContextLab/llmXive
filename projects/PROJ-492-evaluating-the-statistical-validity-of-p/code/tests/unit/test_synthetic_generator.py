"""
Unit tests for the synthetic dataset generator (T026).
Verifies that the generator produces valid data, correct file formats,
and meets the volume and diversity constraints.
"""
import csv
import json
import os
import sys
from pathlib import Path
import tempfile
import pytest

# Add code to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from src.audit.synthetic import (
    generate_synthetic_dataset,
    write_csv_output,
    write_json_output,
    verify_outcome_types,
    generate_binary_outcome,
    generate_continuous_outcome,
    generate_sample_sizes
)

class TestSyntheticGenerator:
    """Tests for the synthetic dataset generation logic."""

    def test_generate_sample_sizes_returns_positive_integers(self):
        """Test that sample sizes are positive integers."""
        n1, n2 = generate_sample_sizes()
        assert isinstance(n1, int)
        assert isinstance(n2, int)
        assert n1 > 0
        assert n2 > 0

    def test_generate_binary_outcome_structure(self):
        """Test that binary outcome generation returns correct fields."""
        record = generate_binary_outcome(100, 100, 0.5, 0.1, False)
        
        assert record["outcome_type"] == "binary"
        assert "n_control" in record
        assert "n_treatment" in record
        assert "x_control" in record
        assert "x_treatment" in record
        assert "p_control_reported" in record
        assert "p_treatment_reported" in record
        assert "p_value_reported" in record
        assert "effect_size_reported" in record
        assert "is_inconsistent" in record
        
        # Check types
        assert isinstance(record["x_control"], int)
        assert isinstance(record["x_treatment"], int)
        assert 0.0 <= record["p_control_reported"] <= 1.0
        assert 0.0 <= record["p_treatment_reported"] <= 1.0
        assert 0.0 <= record["p_value_reported"] <= 1.0

    def test_generate_continuous_outcome_structure(self):
        """Test that continuous outcome generation returns correct fields."""
        record = generate_continuous_outcome(100, 100, 50.0, 5.0, 10.0, False)
        
        assert record["outcome_type"] == "continuous"
        assert "n_control" in record
        assert "n_treatment" in record
        assert "mean_control_reported" in record
        assert "mean_treatment_reported" in record
        assert "std_control_reported" in record
        assert "std_treatment_reported" in record
        assert "p_value_reported" in record
        assert "effect_size_reported" in record
        assert "is_inconsistent" in record

    def test_verify_outcome_types_true(self):
        """Test verification passes with mixed types."""
        records = [
            {"outcome_type": "binary"},
            {"outcome_type": "continuous"}
        ]
        assert verify_outcome_types(records) is True

    def test_verify_outcome_types_false_missing_binary(self):
        """Test verification fails if binary is missing."""
        records = [
            {"outcome_type": "continuous"},
            {"outcome_type": "continuous"}
        ]
        assert verify_outcome_types(records) is False

    def test_verify_outcome_types_false_missing_continuous(self):
        """Test verification fails if continuous is missing."""
        records = [
            {"outcome_type": "binary"},
            {"outcome_type": "binary"}
        ]
        assert verify_outcome_types(records) is False

    def test_generate_synthetic_dataset_volume(self):
        """Test that the generator produces the requested number of records."""
        target_count = 100
        records, metadata = generate_synthetic_dataset(total_records=target_count, inconsistency_rate=0.1)
        
        assert len(records) == target_count
        assert metadata["total_records"] == target_count

    def test_generate_synthetic_dataset_diversity(self):
        """Test that the generator produces both binary and continuous outcomes."""
        records, metadata = generate_synthetic_dataset(total_records=200, binary_ratio=0.5)
        
        types = set(r["outcome_type"] for r in records)
        assert "binary" in types
        assert "continuous" in types
        assert metadata["binary_count"] + metadata["continuous_count"] == len(records)

    def test_write_csv_output_format(self, tmp_path):
        """Test that CSV output is written correctly."""
        records, _ = generate_synthetic_dataset(total_records=50, inconsistency_rate=0.1)
        csv_path = tmp_path / "test.csv"
        
        write_csv_output(records, csv_path)
        
        assert csv_path.exists()
        with open(csv_path, 'r') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            
        assert len(rows) == 50
        # Check header
        assert "outcome_type" in reader.fieldnames
        assert "p_value_reported" in reader.fieldnames

    def test_write_json_output_format(self, tmp_path):
        """Test that JSON output is written correctly."""
        records, metadata = generate_synthetic_dataset(total_records=50, inconsistency_rate=0.1)
        json_path = tmp_path / "test.json"
        
        write_json_output(metadata, records, json_path)
        
        assert json_path.exists()
        with open(json_path, 'r') as f:
            data = json.load(f)
            
        assert "metadata" in data
        assert "records" in data
        assert len(data["records"]) == 50
        assert data["metadata"]["total_records"] == 50

    def test_full_pipeline_integration(self, tmp_path):
        """Integration test: Generate, write, and verify files."""
        target_count = 1000
        records, metadata = generate_synthetic_dataset(
            total_records=target_count, 
            binary_ratio=0.5,
            inconsistency_rate=0.15
        )
        
        csv_path = tmp_path / "synthetic_validation.csv"
        json_path = tmp_path / "synthetic_ground_truth.json"
        
        write_csv_output(records, csv_path)
        write_json_output(metadata, records, json_path)
        
        # Verify file existence
        assert csv_path.exists()
        assert json_path.exists()
        
        # Verify CSV content
        with open(csv_path, 'r') as f:
            reader = csv.DictReader(f)
            csv_rows = list(reader)
        assert len(csv_rows) >= 1000
        
        # Verify JSON content
        with open(json_path, 'r') as f:
            json_data = json.load(f)
        assert len(json_data["records"]) >= 1000
        
        # Verify diversity
        csv_types = set(r["outcome_type"] for r in csv_rows)
        assert "binary" in csv_types
        assert "continuous" in csv_types