"""
Unit tests for the synthetic dataset generator (T026).
Verifies that the generator produces the required volume and types of data.
"""
import csv
import json
import os
import tempfile
from pathlib import Path

import pytest
import numpy as np

# Import the module under test
from code.src.audit.synthetic import (
    generate_synthetic_dataset,
    verify_outcome_types,
    write_csv_output,
    write_metadata,
    OUTPUT_DIR,
    SEED
)

class TestSyntheticGeneration:
    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for test outputs."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    def test_generate_synthetic_dataset_volume(self):
        """Test that the generator creates at least 10,000 records."""
        records = generate_synthetic_dataset(n_records=10000, seed=42)
        assert len(records) == 10000, f"Expected 10000 records, got {len(records)}"

    def test_generate_synthetic_dataset_outcome_types(self):
        """Test that both binary and continuous outcomes are present."""
        records = generate_synthetic_dataset(n_records=10000, binary_ratio=0.5, seed=42)
        binary_count, continuous_count = verify_outcome_types(records)

        assert binary_count > 0, "Binary outcomes must be present."
        assert continuous_count > 0, "Continuous outcomes must be present."
        assert binary_count + continuous_count == 10000

    def test_write_csv_output(self, temp_dir):
        """Test that CSV output is written correctly."""
        records = generate_synthetic_dataset(n_records=100, seed=42)
        csv_path = temp_dir / "test_summaries.csv"

        write_csv_output(records, csv_path)

        assert csv_path.exists(), "CSV file was not created."

        with open(csv_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        assert len(rows) == 100
        assert "outcome_type" in reader.fieldnames
        assert "record_id" in reader.fieldnames

    def test_write_metadata(self, temp_dir):
        """Test that metadata JSON is written correctly."""
        records = generate_synthetic_dataset(n_records=100, seed=42)
        b_count, c_count = verify_outcome_types(records)
        json_path = temp_dir / "test_metadata.json"

        write_metadata(len(records), b_count, c_count, 42, json_path)

        assert json_path.exists(), "Metadata file was not created."

        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        assert data["total_records"] == 100
        assert "binary" in data["outcome_distribution"]
        assert "continuous" in data["outcome_distribution"]
        assert data["seed"] == 42

    def test_reproducibility(self):
        """Test that the same seed produces the same results."""
        records1 = generate_synthetic_dataset(n_records=100, seed=123)
        records2 = generate_synthetic_dataset(n_records=100, seed=123)

        # Compare a few key fields to ensure determinism
        for r1, r2 in zip(records1, records2):
            assert r1["record_id"] == r2["record_id"]
            assert r1["outcome_type"] == r2["outcome_type"]
            if r1["outcome_type"] == "binary":
                assert r1["metric_control"] == r2["metric_control"]
            else:
                assert r1["metric_control"] == r2["metric_control"]

    def test_sample_size_distribution(self):
        """Test that sample sizes are within expected bounds."""
        records = generate_synthetic_dataset(n_records=1000, seed=42)
        
        sizes = []
        for r in records:
            sizes.append(r["sample_size_control"])
            sizes.append(r["sample_size_treatment"])

        min_size = min(sizes)
        max_size = max(sizes)

        # According to synthetic.py, sizes are clipped between 50 and 50000
        assert min_size >= 50, f"Sample size too small: {min_size}"
        assert max_size <= 50000, f"Sample size too large: {max_size}"