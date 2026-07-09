"""
Unit tests for synthetic dataset generator (T026).
Verifies both binary and continuous outcome types are present with ≥10,000 records.
"""
import csv
import json
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
    verify_outcome_types,
    MIN_RECORDS_PER_TYPE
)
from code.src.config import SEED


class TestSyntheticGenerator:
    """Tests for synthetic dataset generation."""

    def test_set_all_seeds(self):
        """Test that all seeds are set correctly."""
        set_all_seeds(SEED)
        # Verify reproducibility
        val1 = np.random.random()
        set_all_seeds(SEED)
        val2 = np.random.random()
        assert val1 == val2

    def test_generate_sample_sizes(self):
        """Test sample size generation."""
        total = 1000
        control, treatment = generate_sample_sizes(total)
        assert control + treatment == total
        assert 400 <= control <= 600
        assert 400 <= treatment <= 600

    def test_generate_binary_outcome(self):
        """Test binary outcome generation."""
        data = generate_binary_outcome(
            n_control=1000,
            n_treatment=1000,
            baseline_rate=0.2,
            effect_size=0.1,
            seed=42
        )
        
        assert "control_conversions" in data
        assert "treatment_conversions" in data
        assert "p_value" in data
        assert 0 <= data["control_rate"] <= 1
        assert 0 <= data["treatment_rate"] <= 1
        assert 0 <= data["p_value"] <= 1

    def test_generate_continuous_outcome(self):
        """Test continuous outcome generation."""
        data = generate_continuous_outcome(
            n_control=1000,
            n_treatment=1000,
            baseline_mean=50.0,
            baseline_std=10.0,
            effect_size=5.0,
            seed=42
        )
        
        assert "control_mean" in data
        assert "treatment_mean" in data
        assert "p_value" in data
        assert data["control_mean"] > 0
        assert data["treatment_mean"] > 0
        assert 0 <= data["p_value"] <= 1

    def test_generate_synthetic_dataset_creates_files(self):
        """Test that dataset generation creates expected files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            binary_path, continuous_path = generate_synthetic_dataset(
                n_binary=100,
                n_continuous=100,
                output_dir=output_dir,
                seed=42
            )
            
            assert binary_path.exists()
            assert continuous_path.exists()
            
            # Check metadata file
            metadata_path = output_dir / "synthetic_metadata.json"
            assert metadata_path.exists()

    def test_verify_outcome_types_passes(self):
        """Test verification passes with sufficient records."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            generate_synthetic_dataset(
                n_binary=MIN_RECORDS_PER_TYPE + 100,
                n_continuous=MIN_RECORDS_PER_TYPE + 100,
                output_dir=output_dir,
                seed=42
            )
            
            binary_path = output_dir / "synthetic_binary.csv"
            continuous_path = output_dir / "synthetic_continuous.csv"
            
            assert verify_outcome_types(binary_path, continuous_path)

    def test_verify_outcome_types_fails_insufficient_records(self):
        """Test verification fails with insufficient records."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            generate_synthetic_dataset(
                n_binary=MIN_RECORDS_PER_TYPE - 100,
                n_continuous=MIN_RECORDS_PER_TYPE - 100,
                output_dir=output_dir,
                seed=42
            )
            
            binary_path = output_dir / "synthetic_binary.csv"
            continuous_path = output_dir / "synthetic_continuous.csv"
            
            assert not verify_outcome_types(binary_path, continuous_path)

    def test_synthetic_dataset_record_count(self):
        """Test that generated dataset has correct record counts."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            n_binary = 15000
            n_continuous = 12000
            
            generate_synthetic_dataset(
                n_binary=n_binary,
                n_continuous=n_continuous,
                output_dir=output_dir,
                seed=42
            )
            
            # Count binary records
            binary_path = output_dir / "synthetic_binary.csv"
            with open(binary_path, "r") as f:
                reader = csv.DictReader(f)
                count = sum(1 for _ in reader)
            assert count == n_binary
            
            # Count continuous records
            continuous_path = output_dir / "synthetic_continuous.csv"
            with open(continuous_path, "r") as f:
                reader = csv.DictReader(f)
                count = sum(1 for _ in reader)
            assert count == n_continuous

    def test_metadata_contains_required_fields(self):
        """Test that metadata file contains required fields."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            generate_synthetic_dataset(
                n_binary=100,
                n_continuous=100,
                output_dir=output_dir,
                seed=42
            )
            
            metadata_path = output_dir / "synthetic_metadata.json"
            with open(metadata_path, "r") as f:
                metadata = json.load(f)
            
            assert "generated_at" in metadata
            assert "seed" in metadata
            assert "binary_count" in metadata
            assert "continuous_count" in metadata
            assert "total_count" in metadata
            assert metadata["binary_count"] == 100
            assert metadata["continuous_count"] == 100
            assert metadata["total_count"] == 200

    def test_both_outcome_types_present(self):
        """Test that both outcome types are present in generated data."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            generate_synthetic_dataset(
                n_binary=MIN_RECORDS_PER_TYPE,
                n_continuous=MIN_RECORDS_PER_TYPE,
                output_dir=output_dir,
                seed=42
            )
            
            # Check binary file has outcome_type column
            binary_path = output_dir / "synthetic_binary.csv"
            with open(binary_path, "r") as f:
                reader = csv.DictReader(f)
                first_row = next(reader)
                assert "outcome_type" in first_row
                assert first_row["outcome_type"] == "binary"
            
            # Check continuous file has outcome_type column
            continuous_path = output_dir / "synthetic_continuous.csv"
            with open(continuous_path, "r") as f:
                reader = csv.DictReader(f)
                first_row = next(reader)
                assert "outcome_type" in first_row
                assert first_row["outcome_type"] == "continuous"

    def test_minimum_record_requirement(self):
        """Test that minimum record requirement is met."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            generate_synthetic_dataset(
                n_binary=MIN_RECORDS_PER_TYPE,
                n_continuous=MIN_RECORDS_PER_TYPE,
                output_dir=output_dir,
                seed=42
            )
            
            binary_path = output_dir / "synthetic_binary.csv"
            continuous_path = output_dir / "synthetic_continuous.csv"
            
            # Verify counts
            binary_count = sum(1 for _ in csv.DictReader(open(binary_path)))
            continuous_count = sum(1 for _ in csv.DictReader(open(continuous_path)))
            
            assert binary_count >= MIN_RECORDS_PER_TYPE
            assert continuous_count >= MIN_RECORDS_PER_TYPE
