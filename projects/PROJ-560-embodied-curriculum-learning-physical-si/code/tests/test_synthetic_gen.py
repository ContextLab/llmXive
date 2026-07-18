"""
Unit Tests for Synthetic Data Generator in the Embodied Curriculum Learning Pipeline.

This module contains tests for the SyntheticDataGenerator class to ensure
it produces valid synthetic datasets with the expected schema.
"""
import pytest
import os
import sys
import json
import tempfile
import shutil

from src.synthetic_gen import SyntheticDataGenerator, generate_mapping_log
from src.models import DatasetRecord


class TestSyntheticDataGenerator:
    """Tests for SyntheticDataGenerator class."""

    def test_generate_default_samples(self):
        """Test generating default number of samples."""
        generator = SyntheticDataGenerator(seed=42)
        records = generator.generate(n_samples=100)

        assert len(records) == 100
        assert all(isinstance(r, DatasetRecord) for r in records)

    def test_generate_with_custom_seed(self):
        """Test that custom seed produces deterministic results."""
        generator1 = SyntheticDataGenerator(seed=123)
        generator2 = SyntheticDataGenerator(seed=123)

        records1 = generator1.generate(n_samples=50)
        records2 = generator2.generate(n_samples=50)

        # Check that records are identical
        for r1, r2 in zip(records1, records2):
            assert r1.id == r2.id
            assert r1.pre_test_score == r2.pre_test_score
            assert r1.post_test_score == r2.post_test_score
            assert r1.instruction_type == r2.instruction_type

    def test_generate_balanced_groups(self):
        """Test that generated data has roughly equal group sizes."""
        generator = SyntheticDataGenerator(seed=42)
        records = generator.generate(n_samples=200)

        embodied_count = sum(1 for r in records if r.instruction_type == "embodied")
        static_count = sum(1 for r in records if r.instruction_type == "static")

        assert embodied_count == static_count

    def test_generate_with_custom_parameters(self):
        """Test generating data with custom mean and std parameters."""
        generator = SyntheticDataGenerator(
            seed=42,
            embodied_mean=5.0,
            static_mean=2.0,
            std_dev=1.0
        )
        records = generator.generate(n_samples=100)

        embodied_gains = [r.gain_score for r in records if r.instruction_type == "embodied"]
        static_gains = [r.gain_score for r in records if r.instruction_type == "static"]

        # Embodied mean should be higher than static mean
        assert sum(embodied_gains) / len(embodied_gains) > sum(static_gains) / len(static_gains)

    def test_generate_mapping_log(self):
        """Test that generate_mapping_log creates a valid file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_path = os.path.join(tmpdir, "mapping_log.json")
            generate_mapping_log(log_path)

            assert os.path.exists(log_path)
            with open(log_path, "r") as f:
                data = json.load(f)
            assert "description" in data
            assert "embodied_condition" in data
            assert "static_condition" in data
            assert "ground_truth" in data

    def test_generate_schema_compliance(self):
        """Test that generated records have all required fields."""
        generator = SyntheticDataGenerator(seed=42)
        records = generator.generate(n_samples=50)

        for record in records:
            assert record.id is not None
            assert record.pre_test_score is not None
            assert record.post_test_score is not None
            assert record.instruction_type in ["embodied", "static"]
            assert isinstance(record.covariates, dict)
            assert record.gain_score is not None