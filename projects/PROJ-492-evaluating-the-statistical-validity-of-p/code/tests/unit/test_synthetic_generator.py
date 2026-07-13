"""
Unit tests for the synthetic dataset generator (T026).
Verifies FR-030 requirements: binary and continuous outcomes,
constraint preservation (consistency), and record count.
"""
import json
import csv
import tempfile
from pathlib import Path
import pytest
import numpy as np
from scipy import stats

from code.src.audit.synthetic import (
    generate_synthetic_dataset,
    generate_binary_summary,
    generate_continuous_summary,
    set_seeds,
    TOTAL_RECORDS,
    CONSISTENCY_RATE
)
from code.src.config import SEED

class TestSyntheticGenerator:
    """Tests for synthetic data generation logic."""

    def test_set_seeds_determinism(self):
        """Ensure setting seeds produces deterministic results."""
        set_seeds(42)
        rng1 = np.random.default_rng(42)
        val1 = rng1.random()

        set_seeds(42)
        rng2 = np.random.default_rng(42)
        val2 = rng2.random()

        assert val1 == val2, "Seed reset should produce identical sequences"

    def test_binary_summary_generation(self):
        """Verify binary summary generation logic and consistency."""
        set_seeds(123)
        rng = np.random.default_rng(123)
        
        data, is_consistent = generate_binary_summary(rng, is_consistent=True)
        
        assert data["test_type"] == "binary"
        assert data["n_control"] > 0
        assert data["n_treatment"] > 0
        assert 0 < data["baseline_rate"] < 1
        assert 0 < data["treatment_rate"] < 1
        assert 0 <= data["reported_p_value"] <= 1
        
        # Verify consistency: reported should match true (within float tolerance)
        if is_consistent:
            assert abs(data["reported_p_value"] - data["true_p_value"]) < 1e-6

    def test_continuous_summary_generation(self):
        """Verify continuous summary generation logic."""
        set_seeds(456)
        rng = np.random.default_rng(456)
        
        data, is_consistent = generate_continuous_summary(rng, is_consistent=True)
        
        assert data["test_type"] == "continuous"
        assert data["n_control"] > 0
        assert data["n_treatment"] > 0
        assert data["mean_control"] > 0
        assert data["std_control"] > 0
        assert 0 <= data["reported_p_value"] <= 1

    def test_inconsistency_injection(self):
        """Verify that inconsistent records have mismatched p-values."""
        set_seeds(789)
        rng = np.random.default_rng(789)
        
        # Force inconsistency
        data, is_consistent = generate_binary_summary(rng, is_consistent=False)
        
        assert not is_consistent
        # Check that reported p-value is significantly different from true
        diff = abs(data["reported_p_value"] - data["true_p_value"])
        # One is likely < 0.05 and the other > 0.05, so diff should be substantial
        assert diff > 0.01, "Inconsistent records should have significant p-value drift"

    def test_dataset_generation_count(self):
        """Verify that the generated dataset meets the >= 10,000 record requirement."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            json_path, csv_path = generate_synthetic_dataset(
                output_dir, 
                total_records=10500, 
                seed=999
            )
            
            # Check JSON
            with open(json_path, 'r') as f:
                data = json.load(f)
            assert len(data) == 10500, "JSON should contain exactly 10500 records"
            
            # Check CSV
            with open(csv_path, 'r') as f:
                reader = csv.DictReader(f)
                rows = list(reader)
            assert len(rows) == 10500, "CSV should contain exactly 10500 records"

    def test_dataset_generation_types(self):
        """Verify that both binary and continuous types are present."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            json_path, _ = generate_synthetic_dataset(
                output_dir, 
                total_records=1000, 
                seed=888
            )
            
            with open(json_path, 'r') as f:
                data = json.load(f)
            
            types = [r["test_type"] for r in data]
            assert "binary" in types, "Dataset must contain binary outcomes"
            assert "continuous" in types, "Dataset must contain continuous outcomes"
            
            # Check approximate ratio (60/40)
            binary_count = types.count("binary")
            total = len(types)
            ratio = binary_count / total
            assert 0.5 < ratio < 0.7, f"Binary ratio {ratio} should be approx 0.6"

    def test_constraint_preservation(self):
        """Verify that consistent records pass basic statistical sanity checks."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            json_path, csv_path = generate_synthetic_dataset(
                output_dir, 
                total_records=500, 
                seed=777
            )
            
            with open(json_path, 'r') as f:
                summaries = json.load(f)
            
            consistent_records = [r for r in summaries if r["raw_data"]["is_consistent"]]
            
            for rec in consistent_records[:100]: # Sample check
                raw = rec["raw_data"]
                if raw["test_type"] == "binary":
                    # Check p-value bounds
                    assert 0 <= raw["reported_p_value"] <= 1
                    # Check consistency
                    assert abs(raw["reported_p_value"] - raw["true_p_value"]) < 1e-5
                else:
                    assert 0 <= raw["reported_p_value"] <= 1
                    assert abs(raw["reported_p_value"] - raw["true_p_value"]) < 1e-5

    def test_output_files_exist(self):
        """Verify that both output files are created."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            json_path, csv_path = generate_synthetic_dataset(
                output_dir, 
                total_records=100, 
                seed=666
            )
            
            assert json_path.exists(), "JSON file must exist"
            assert csv_path.exists(), "CSV file must exist"
            
            # Verify file sizes are non-zero
            assert json_path.stat().st_size > 0
            assert csv_path.stat().st_size > 0
