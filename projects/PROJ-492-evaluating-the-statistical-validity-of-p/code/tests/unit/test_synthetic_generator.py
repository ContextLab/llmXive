"""
Unit tests for the synthetic dataset generator (T026).

Verifies that:
1. The generator produces the required number of records (>= 10,000).
2. Both binary and continuous outcomes are generated.
3. Statistical values are within valid ranges.
4. The output files are created correctly.
"""
import csv
import json
import os
import tempfile
from pathlib import Path
from typing import Dict, Any, List

import pytest
import numpy as np

from code.src.audit.synthetic import (
    generate_synthetic_dataset,
    verify_outcome_types,
    write_summaries_to_csv,
    write_metadata,
    generate_sample_sizes,
    generate_binary_outcome,
    generate_continuous_outcome,
    set_all_seeds,
    MIN_SAMPLE_SIZE,
    MAX_SAMPLE_SIZE,
    BINARY_RATIO,
    TOTAL_RECORDS
)
from code.src.config import SEED


class TestSyntheticGenerator:
    """Tests for the synthetic dataset generator."""

    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for test outputs."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    def test_generate_sample_sizes_range(self):
        """Test that sample sizes are within valid bounds."""
        sizes = generate_sample_sizes(100)
        assert len(sizes) == 100
        assert all(MIN_SAMPLE_SIZE <= s <= MAX_SAMPLE_SIZE for s in sizes)

    def test_generate_binary_outcome_validity(self):
        """Test that binary outcome generation produces valid statistics."""
        n_c, n_t = 1000, 1000
        base_rate, lift = 0.1, 0.05
        
        successes_c, successes_t, n_c_out, n_t_out, p_val = generate_binary_outcome(
            n_c, n_t, base_rate, lift
        )
        
        assert 0 <= successes_c <= n_c
        assert 0 <= successes_t <= n_t
        assert 0.0 <= p_val <= 1.0
        assert n_c_out == n_c
        assert n_t_out == n_t

    def test_generate_continuous_outcome_validity(self):
        """Test that continuous outcome generation produces valid statistics."""
        n_c, n_t = 1000, 1000
        base_mean, lift, std_dev = 200.0, 0.05, 100.0
        
        mean_c, mean_t, std_c, std_t, p_val = generate_continuous_outcome(
            n_c, n_t, base_mean, lift, std_dev
        )
        
        assert mean_c > 0
        assert mean_t > 0
        assert std_c > 0
        assert std_t > 0
        assert 0.0 <= p_val <= 1.0

    def test_generate_synthetic_dataset_count(self):
        """Test that the generated dataset has at least 10,000 records."""
        records = generate_synthetic_dataset(n_records=TOTAL_RECORDS, seed=SEED)
        assert len(records) >= 10000

    def test_generate_synthetic_dataset_outcome_types(self):
        """Test that both binary and continuous outcomes are present."""
        records = generate_synthetic_dataset(n_records=TOTAL_RECORDS, seed=SEED)
        outcome_counts = verify_outcome_types(records)
        
        assert outcome_counts["binary"] > 0
        assert outcome_counts["continuous"] > 0
        
        # Check approximate ratio (allowing some variance)
        total = outcome_counts["binary"] + outcome_counts["continuous"]
        binary_ratio = outcome_counts["binary"] / total
        assert 0.5 < binary_ratio < 0.7  # Around 60%

    def test_generate_synthetic_dataset_required_fields(self):
        """Test that all required fields are present in each record."""
        records = generate_synthetic_dataset(n_records=100, seed=SEED)
        
        required_fields = [
            "id", "outcome_type", "n_control", "n_treatment",
            "p_value", "effect_size", "statistical_test", "domain", "year"
        ]
        
        for record in records:
            for field in required_fields:
                assert field in record, f"Missing field: {field}"

    def test_write_summaries_to_csv(self, temp_dir):
        """Test that CSV output is written correctly."""
        records = generate_synthetic_dataset(n_records=100, seed=SEED)
        output_path = temp_dir / "test_output.csv"
        
        write_summaries_to_csv(records, output_path)
        
        assert output_path.exists()
        
        with open(output_path, "r", newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            rows = list(reader)
        
        assert len(rows) == len(records)
        assert len(rows[0]) >= 10  # At least 10 columns

    def test_write_metadata(self, temp_dir):
        """Test that metadata JSON is written correctly."""
        records = generate_synthetic_dataset(n_records=100, seed=SEED)
        output_path = temp_dir / "test_metadata.json"
        
        write_metadata(records, output_path)
        
        assert output_path.exists()
        
        with open(output_path, "r", encoding="utf-8") as f:
            metadata = json.load(f)
        
        assert "total_records" in metadata
        assert "outcome_type_distribution" in metadata
        assert metadata["total_records"] == len(records)

    def test_deterministic_generation(self):
        """Test that generation is deterministic with the same seed."""
        set_all_seeds(SEED)
        records1 = generate_synthetic_dataset(n_records=50, seed=SEED)
        
        set_all_seeds(SEED)
        records2 = generate_synthetic_dataset(n_records=50, seed=SEED)
        
        # Check that IDs and key values match
        for r1, r2 in zip(records1, records2):
            assert r1["id"] == r2["id"]
            assert r1["p_value"] == r2["p_value"]
            assert r1["effect_size"] == r2["effect_size"]

    def test_sample_size_constraints(self):
        """Test that all sample sizes respect the defined constraints."""
        records = generate_synthetic_dataset(n_records=1000, seed=SEED)
        
        for record in records:
            assert record["n_control"] >= MIN_SAMPLE_SIZE
            assert record["n_control"] <= MAX_SAMPLE_SIZE
            assert record["n_treatment"] >= MIN_SAMPLE_SIZE
            assert record["n_treatment"] <= MAX_SAMPLE_SIZE

    def test_p_value_range(self):
        """Test that all p-values are in the valid range [0, 1]."""
        records = generate_synthetic_dataset(n_records=1000, seed=SEED)
        
        for record in records:
            assert 0.0 <= record["p_value"] <= 1.0

    def test_domain_distribution(self):
        """Test that records are distributed across multiple domains."""
        records = generate_synthetic_dataset(n_records=1000, seed=SEED)
        domains = set(record["domain"] for record in records)
        
        # We expect at least 3 different domains
        assert len(domains) >= 3

    def test_year_distribution(self):
        """Test that records are distributed across multiple years."""
        records = generate_synthetic_dataset(n_records=1000, seed=SEED)
        years = set(record["year"] for record in records)
        
        # We expect at least 2 different years
        assert len(years) >= 2