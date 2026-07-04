"""
Unit tests for the synthetic dataset generator (T026).
Verifies:
  - File creation
  - Record count >= 10,000
  - Presence of both binary and continuous outcomes
  - Data integrity (numeric fields are numeric, etc.)
"""

import csv
import json
import os
import sys
from pathlib import Path
import tempfile
import pytest

# Add code to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.src.audit.synthetic import (
    generate_synthetic_dataset,
    write_csv_output,
    write_json_output,
    verify_outcome_types,
    NUM_RECORDS,
    BINARY_RATIO
)


class TestSyntheticGenerator:
    """Tests for synthetic data generation logic."""

    def test_generate_synthetic_dataset_count(self):
        """Verify that the generator produces at least NUM_RECORDS records."""
        records, _ = generate_synthetic_dataset(n_records=NUM_RECORDS)
        assert len(records) == NUM_RECORDS

    def test_generate_synthetic_dataset_outcome_types(self):
        """Verify that both binary and continuous outcomes are present."""
        records, _ = generate_synthetic_dataset(n_records=NUM_RECORDS)
        assert verify_outcome_types(records) is True

    def test_record_structure_binary(self):
        """Verify structure of a binary record."""
        records, _ = generate_synthetic_dataset(n_records=10)
        binary_records = [r for r in records if r["outcome_type"] == "binary"]
        assert len(binary_records) > 0

        r = binary_records[0]
        assert "n_control" in r
        assert "n_treatment" in r
        assert "successes_control" in r
        assert "successes_treatment" in r
        assert "reported_p_value" in r
        assert "is_inconsistent" in r
        assert isinstance(r["n_control"], int)
        assert isinstance(r["reported_p_value"], float)

    def test_record_structure_continuous(self):
        """Verify structure of a continuous record."""
        records, _ = generate_synthetic_dataset(n_records=10)
        continuous_records = [r for r in records if r["outcome_type"] == "continuous"]
        assert len(continuous_records) > 0

        r = continuous_records[0]
        assert "n_control" in r
        assert "n_treatment" in r
        assert "obs_mean_control" in r
        assert "obs_mean_treatment" in r
        assert "reported_p_value" in r
        assert isinstance(r["obs_mean_control"], float)


class TestSyntheticIO:
    """Tests for file I/O operations."""

    def test_write_csv_and_json_creates_files(self, tmp_path):
        """Verify that write functions create files with content."""
        records, ground_truth = generate_synthetic_dataset(n_records=100)

        csv_path = tmp_path / "test.csv"
        json_path = tmp_path / "test.json"

        write_csv_output(records, csv_path)
        write_json_output(ground_truth, json_path)

        assert csv_path.exists()
        assert json_path.exists()
        assert csv_path.stat().st_size > 0
        assert json_path.stat().st_size > 0

    def test_csv_content_valid(self, tmp_path):
        """Verify CSV content can be read back and matches record count."""
        records, _ = generate_synthetic_dataset(n_records=500)
        csv_path = tmp_path / "out.csv"
        write_csv_output(records, csv_path)

        with open(csv_path, 'r', newline='') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            assert len(rows) == 500
            # Check a few fields
            assert "outcome_type" in rows[0]
            assert "reported_p_value" in rows[0]

    def test_json_content_valid(self, tmp_path):
        """Verify JSON content can be read back and matches ground truth count."""
        _, ground_truth = generate_synthetic_dataset(n_records=200)
        json_path = tmp_path / "out.json"
        write_json_output(ground_truth, json_path)

        with open(json_path, 'r') as f:
            data = json.load(f)
            assert len(data) == 200
            assert "true_significant" in data[0]
            assert "is_inconsistent" in data[0]

    def test_verification_fails_missing_type(self):
        """Verify that verify_outcome_types returns False if a type is missing."""
        # Manually construct a list with only binary
        fake_records = [{"outcome_type": "binary"} for _ in range(10)]
        assert verify_outcome_types(fake_records) is False

        fake_records = [{"outcome_type": "continuous"} for _ in range(10)]
        assert verify_outcome_types(fake_records) is False

        # Mixed should pass
        fake_records = [{"outcome_type": "binary"}, {"outcome_type": "continuous"}]
        assert verify_outcome_types(fake_records) is True
