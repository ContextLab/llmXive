"""
Unit tests for synthetic dataset generator (T026).

Verifies:
- Generation of at least 10,000 records
- Presence of both binary and continuous outcomes
- Correct output file creation
- Data integrity and schema compliance
"""
import csv
import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest
import numpy as np

from code.src.audit.synthetic import (
    set_all_seeds,
    generate_sample_sizes,
    generate_binary_outcome,
    generate_continuous_outcome,
    generate_synthetic_dataset,
    verify_outcome_types
)
from code.src.config import SEED

class TestSyntheticGenerator:
    """Test suite for synthetic dataset generation."""

    def test_set_all_seeds_reproducibility(self):
        """Test that setting seeds produces reproducible results."""
        set_all_seeds(SEED)
        result1 = np.random.random()
        
        set_all_seeds(SEED)
        result2 = np.random.random()
        
        assert result1 == result2, "Seeding should produce reproducible random values"

    def test_generate_sample_sizes_range(self):
        """Test that sample sizes are within expected ranges."""
        for _ in range(100):
            n_control, n_treatment = generate_sample_sizes()
            assert 50 <= n_control <= 5000, f"Control size {n_control} out of range"
            assert 50 <= n_treatment <= 5000, f"Treatment size {n_treatment} out of range"

    def test_generate_binary_outcome_structure(self):
        """Test binary outcome generation produces correct structure."""
        result = generate_binary_outcome(100, 100)
        
        required_fields = [
            "outcome_type", "n_control", "n_treatment",
            "successes_control", "successes_treatment",
            "baseline_rate", "treatment_rate", "effect_size",
            "p_value_reported", "p_value_reconstructed",
            "z_statistic", "true_baseline_rate", "true_effect_size"
        ]
        
        for field in required_fields:
            assert field in result, f"Missing required field: {field}"
        
        assert result["outcome_type"] == "binary"
        assert 0 <= result["successes_control"] <= result["n_control"]
        assert 0 <= result["successes_treatment"] <= result["n_treatment"]

    def test_generate_continuous_outcome_structure(self):
        """Test continuous outcome generation produces correct structure."""
        result = generate_continuous_outcome(100, 100)
        
        required_fields = [
            "outcome_type", "n_control", "n_treatment",
            "mean_control", "mean_treatment", "std_control", "std_treatment",
            "baseline_mean", "effect_size", "p_value_reported",
            "p_value_reconstructed", "t_statistic", "true_baseline_mean",
            "true_effect_size"
        ]
        
        for field in required_fields:
            assert field in result, f"Missing required field: {field}"
        
        assert result["outcome_type"] == "continuous"
        assert result["std_control"] >= 0
        assert result["std_treatment"] >= 0

    @pytest.mark.integration
    def test_generate_synthetic_dataset_minimum_records(self):
        """Test that dataset generation produces at least 10,000 records."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            records = generate_synthetic_dataset(
                total_records=10000,
                output_dir=output_dir
            )
            
            assert len(records) >= 10000, f"Expected >= 10000 records, got {len(records)}"

    @pytest.mark.integration
    def test_generate_synthetic_dataset_both_outcome_types(self):
        """Test that both binary and continuous outcomes are present."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            records = generate_synthetic_dataset(
                total_records=10000,
                binary_ratio=0.5,
                output_dir=output_dir
            )
            
            binary_count = sum(1 for r in records if r["outcome_type"] == "binary")
            continuous_count = sum(1 for r in records if r["outcome_type"] == "continuous")
            
            assert binary_count > 0, "No binary outcomes generated"
            assert continuous_count > 0, "No continuous outcomes generated"
            assert binary_count + continuous_count == len(records)

    @pytest.mark.integration
    def test_generate_synthetic_dataset_output_files(self):
        """Test that output files are created correctly."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            generate_synthetic_dataset(
                total_records=10000,
                output_dir=output_dir
            )
            
            csv_path = output_dir / "synthetic_summaries.csv"
            json_path = output_dir / "synthetic_summaries.json"
            
            assert csv_path.exists(), f"CSV file not created: {csv_path}"
            assert json_path.exists(), f"JSON file not created: {json_path}"
            
            # Verify CSV is readable
            with open(csv_path, 'r') as f:
                reader = csv.DictReader(f)
                rows = list(reader)
                assert len(rows) >= 10000, f"CSV has {len(rows)} rows, expected >= 10000"
            
            # Verify JSON is readable
            with open(json_path, 'r') as f:
                data = json.load(f)
                assert len(data) >= 10000, f"JSON has {len(data)} records, expected >= 10000"

    @pytest.mark.integration
    def test_generate_synthetic_dataset_inconsistency_flag(self):
        """Test that inconsistency flags are set correctly."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            records = generate_synthetic_dataset(
                total_records=10000,
                inconsistency_rate=0.20,
                output_dir=output_dir
            )
            
            inconsistent_count = sum(1 for r in records if r.get("is_inconsistent", False))
            expected_min = int(10000 * 0.15)  # Allow some variance
            
            assert inconsistent_count >= expected_min, \
                f"Expected at least {expected_min} inconsistent records, got {inconsistent_count}"

    def test_verify_outcome_types_success(self):
        """Test verification passes with correct data."""
        records = [
            {"outcome_type": "binary"},
            {"outcome_type": "binary"},
            {"outcome_type": "continuous"}
        ]
        
        # Should not raise
        verify_outcome_types(records, 2, 1)

    def test_verify_outcome_types_missing_binary(self):
        """Test verification fails when binary outcomes are missing."""
        records = [
            {"outcome_type": "continuous"},
            {"outcome_type": "continuous"}
        ]
        
        with pytest.raises(AssertionError, match="No binary outcomes"):
            verify_outcome_types(records, 0, 2)

    def test_verify_outcome_types_missing_continuous(self):
        """Test verification fails when continuous outcomes are missing."""
        records = [
            {"outcome_type": "binary"},
            {"outcome_type": "binary"}
        ]
        
        with pytest.raises(AssertionError, match="No continuous outcomes"):
            verify_outcome_types(records, 2, 0)

    def test_verify_outcome_types_insufficient_records(self):
        """Test verification fails with insufficient records."""
        records = [
            {"outcome_type": "binary"},
            {"outcome_type": "continuous"}
        ]
        
        with pytest.raises(AssertionError, match="Insufficient records"):
            verify_outcome_types(records, 1, 1)

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
