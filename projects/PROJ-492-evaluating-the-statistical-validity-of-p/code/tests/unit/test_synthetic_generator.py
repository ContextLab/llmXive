"""
Unit tests for synthetic dataset generator (T026).
Verifies generation of 10,000+ records with both binary and continuous outcomes.
"""
import csv
import json
import tempfile
from pathlib import Path
from typing import Dict, Any, List

import pytest
import numpy as np

from code.src.audit.synthetic import (
    generate_synthetic_dataset,
    generate_binary_outcome,
    generate_continuous_outcome,
    verify_outcome_types,
    write_csv_output,
    write_json_output,
    TOTAL_RECORDS
)


class TestSyntheticGenerator:
    """Test suite for synthetic dataset generation."""

    def test_generate_synthetic_dataset_creates_expected_count(self):
        """Verify dataset contains at least 10,000 records."""
        records, ground_truth = generate_synthetic_dataset(total_records=TOTAL_RECORDS)
        
        assert len(records) >= TOTAL_RECORDS, f"Expected at least {TOTAL_RECORDS} records, got {len(records)}"
        assert ground_truth["total_records"] == TOTAL_RECORDS

    def test_generate_synthetic_dataset_includes_both_outcome_types(self):
        """Verify both binary and continuous outcome types are present."""
        records, _ = generate_synthetic_dataset(total_records=TOTAL_RECORDS)
        
        binary_count, continuous_count = verify_outcome_types(records)
        
        assert binary_count > 0, "No binary outcome records found"
        assert continuous_count > 0, "No continuous outcome records found"
        assert binary_count + continuous_count == len(records)

    def test_binary_outcome_structure(self):
        """Verify binary outcome records have required fields."""
        record = generate_binary_outcome(
            n=0,
            control_size=100,
            treatment_size=120,
            baseline_rate=0.25,
            effect_size=0.05,
            inject_inconsistency=False
        )
        
        required_fields = [
            "record_id", "outcome_type", "control_sample_size", "treatment_sample_size",
            "control_successes", "treatment_successes", "control_rate", "treatment_rate",
            "reported_p_value", "effect_size", "baseline_rate", "is_inconsistent"
        ]
        
        for field in required_fields:
            assert field in record, f"Missing required field: {field}"
        
        assert record["outcome_type"] == "binary"
        assert 0 <= record["control_rate"] <= 1
        assert 0 <= record["treatment_rate"] <= 1
        assert 0 <= record["reported_p_value"] <= 1

    def test_continuous_outcome_structure(self):
        """Verify continuous outcome records have required fields."""
        record = generate_continuous_outcome(
            n=0,
            control_size=100,
            treatment_size=120,
            control_mean=50.0,
            treatment_mean=52.0,
            control_std=10.0,
            treatment_std=11.0,
            inject_inconsistency=False
        )
        
        required_fields = [
            "record_id", "outcome_type", "control_sample_size", "treatment_sample_size",
            "control_mean", "treatment_mean", "control_std", "treatment_std",
            "reported_p_value", "effect_size", "is_inconsistent"
        ]
        
        for field in required_fields:
            assert field in record, f"Missing required field: {field}"
        
        assert record["outcome_type"] == "continuous"
        assert 0 <= record["reported_p_value"] <= 1

    def test_csv_output_file_creation(self):
        """Verify CSV output file is created with correct structure."""
        records, _ = generate_synthetic_dataset(total_records=100)
        
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test_output.csv"
            write_csv_output(records, output_path)
            
            assert output_path.exists(), "CSV output file not created"
            
            with open(output_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                rows = list(reader)
            
            assert len(rows) == len(records), f"Expected {len(records)} rows, got {len(rows)}"
            
            # Verify header contains expected fields
            expected_fields = ["record_id", "outcome_type", "control_sample_size"]
            for field in expected_fields:
                assert field in reader.fieldnames, f"Missing field in CSV header: {field}"

    def test_json_output_file_creation(self):
        """Verify JSON ground truth file is created with correct structure."""
        _, ground_truth = generate_synthetic_dataset(total_records=100)
        
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test_ground_truth.json"
            write_json_output(ground_truth, output_path)
            
            assert output_path.exists(), "JSON output file not created"
            
            with open(output_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            assert data["total_records"] == 100
            assert "outcome_types" in data
            assert "binary" in data["outcome_types"]
            assert "continuous" in data["outcome_types"]
            assert data["outcome_types"]["binary"]["count"] > 0
            assert data["outcome_types"]["continuous"]["count"] > 0

    def test_inconsistency_injection(self):
        """Verify that inconsistency injection works correctly."""
        # Generate with high inconsistency rate
        records, ground_truth = generate_synthetic_dataset(
            total_records=200,
            inconsistency_rate=0.5
        )
        
        inconsistent_count = sum(1 for r in records if r.get("is_inconsistent"))
        
        # Should be approximately 50% inconsistent (with some variance)
        expected_min = 0.4 * 200  # 80
        expected_max = 0.6 * 200  # 120
        
        assert expected_min <= inconsistent_count <= expected_max, \
            f"Inconsistent count {inconsistent_count} outside expected range"

    def test_sample_size_constraints(self):
        """Verify sample sizes are within expected bounds."""
        records, _ = generate_synthetic_dataset(total_records=100)
        
        for record in records:
            assert MIN_SAMPLE_SIZE <= record["control_sample_size"] <= MAX_SAMPLE_SIZE
            assert MIN_SAMPLE_SIZE <= record["treatment_sample_size"] <= MAX_SAMPLE_SIZE

    def test_deterministic_seed(self):
        """Verify that same seed produces same results."""
        from code.src.config import SEED
        
        records1, _ = generate_synthetic_dataset(total_records=50)
        records2, _ = generate_synthetic_dataset(total_records=50)
        
        # Records should be identical due to seeding
        assert len(records1) == len(records2)
        for r1, r2 in zip(records1, records2):
            assert r1["record_id"] == r2["record_id"]
            assert r1["outcome_type"] == r2["outcome_type"]
            assert r1["control_sample_size"] == r2["control_sample_size"]

# Constants for tests
MIN_SAMPLE_SIZE = 50
MAX_SAMPLE_SIZE = 5000
