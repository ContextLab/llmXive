"""
Unit tests for the synthetic dataset generator (Task T026).
Verifies generation of >= 10,000 records and presence of both outcome types.
"""
import csv
import json
import os
import tempfile
from pathlib import Path

import pytest
import numpy as np

from code.src.audit.synthetic import (
    generate_synthetic_dataset,
    verify_outcome_types,
    set_all_seeds,
    generate_binary_outcome,
    generate_continuous_outcome
)
from code.src.config import SEED


class TestSyntheticGenerator:
    """Tests for synthetic data generation logic."""

    @pytest.fixture
    def temp_output_dir(self):
        """Create a temporary directory for test outputs."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    def test_seed_reproducibility(self):
        """Test that setting seeds produces deterministic results."""
        set_all_seeds(SEED)
        rec1 = generate_binary_outcome(100, 100, 0.5, 0.1, 100)

        set_all_seeds(SEED)
        rec2 = generate_binary_outcome(100, 100, 0.5, 0.1, 100)

        assert rec1["successes_control"] == rec2["successes_control"]
        assert rec1["p_value"] == pytest.approx(rec2["p_value"], rel=1e-5)

    def test_binary_outcome_generation(self):
        """Test binary outcome generation logic."""
        set_all_seeds(SEED)
        n_c, n_t = 1000, 1000
        base_rate = 0.2
        effect = 0.0 # Null effect

        record = generate_binary_outcome(n_c, n_t, base_rate, effect, 42)

        assert record["outcome_type"] == "binary"
        assert record["n_control"] == n_c
        assert record["n_treatment"] == n_t
        assert 0 <= record["rate_control"] <= 1
        assert 0 <= record["rate_treatment"] <= 1
        assert record["p_value"] >= 0 and record["p_value"] <= 1

    def test_continuous_outcome_generation(self):
        """Test continuous outcome generation logic."""
        set_all_seeds(SEED)
        n_c, n_t = 100, 100
        base_mean = 50.0
        base_std = 10.0
        effect = 5.0

        record = generate_continuous_outcome(n_c, n_t, base_mean, base_std, effect, 42)

        assert record["outcome_type"] == "continuous"
        assert record["n_control"] == n_c
        assert record["n_treatment"] == n_t
        assert record["mean_control"] > 0
        assert record["p_value"] >= 0 and record["p_value"] <= 1

    def test_generate_dataset_minimum_count(self, temp_output_dir):
        """Verify that the generator creates at least 10,000 records."""
        records = generate_synthetic_dataset(
            total_records=10000,
            binary_ratio=0.5,
            output_dir=temp_output_dir
        )

        assert len(records) >= 10000, f"Expected >= 10000 records, got {len(records)}"

    def test_generate_dataset_both_outcomes_present(self, temp_output_dir):
        """Verify that both binary and continuous outcomes are present."""
        records = generate_synthetic_dataset(
            total_records=10000,
            binary_ratio=0.5,
            output_dir=temp_output_dir
        )

        binary_count, continuous_count = verify_outcome_types(records)

        assert binary_count > 0, "Binary outcomes must be present"
        assert continuous_count > 0, "Continuous outcomes must be present"
        assert binary_count + continuous_count == len(records)

    def test_csv_file_created(self, temp_output_dir):
        """Verify that the CSV output file is created and readable."""
        records = generate_synthetic_dataset(
            total_records=1000, # Small count for speed
            binary_ratio=0.5,
            output_dir=temp_output_dir
        )

        csv_path = temp_output_dir / "synthetic_summaries.csv"
        assert csv_path.exists(), "CSV file should be created"

        with open(csv_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        assert len(rows) == len(records)
        # Check for expected columns
        assert "outcome_type" in rows[0]
        assert "p_value" in rows[0]
        assert "n_control" in rows[0]

    def test_metadata_json_created(self, temp_output_dir):
        """Verify that the metadata JSON file is created."""
        records = generate_synthetic_dataset(
            total_records=1000,
            binary_ratio=0.5,
            output_dir=temp_output_dir
        )

        meta_path = temp_output_dir / "synthetic_metadata.json"
        assert meta_path.exists(), "Metadata JSON should be created"

        with open(meta_path, "r", encoding="utf-8") as f:
            meta = json.load(f)

        assert "total_records" in meta
        assert meta["total_records"] == 1000
        assert meta["binary_count"] > 0
        assert meta["continuous_count"] > 0

    def test_outcome_type_verification_failure(self):
        """Test that verify_outcome_types raises on missing types."""
        # Create a list with only binary outcomes
        fake_records = [{"outcome_type": "binary"} for _ in range(10)]
        with pytest.raises(ValueError, match="No continuous outcomes found"):
            verify_outcome_types(fake_records)

        # Create a list with only continuous outcomes
        fake_records = [{"outcome_type": "continuous"} for _ in range(10)]
        with pytest.raises(ValueError, match="No binary outcomes found"):
            verify_outcome_types(fake_records)
