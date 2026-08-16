"""
Tests for T037b: Synthetic dataset generation.
"""
import json
import os
import tempfile
from pathlib import Path
import pytest
import pandas as pd
import numpy as np

# Import the module under test
from generate_synthetic_zreward import generate_synthetic_dataset, save_config


class TestSyntheticDatasetGeneration:
    """Test suite for synthetic dataset generation."""

    def test_generate_synthetic_dataset_creates_file(self, tmp_path):
        """Test that the function creates the output parquet file."""
        output_path = tmp_path / "mock_z_reward.parquet"
        config_dir = tmp_path / "config"

        df = generate_synthetic_dataset(
            n_samples=100,
            seed=42,
            output_path=str(output_path)
        )

        save_config(output_dir=str(config_dir), is_mock=True)

        assert output_path.exists(), "Output parquet file was not created"
        assert config_dir.exists(), "Config directory was not created"

    def test_generate_synthetic_dataset_columns(self, tmp_path):
        """Test that the generated dataset has all required columns."""
        output_path = tmp_path / "mock_z_reward.parquet"

        df = generate_synthetic_dataset(
            n_samples=100,
            seed=42,
            output_path=str(output_path)
        )

        required_columns = [
            "prompt",
            "image_url",
            "teacher_scores",
            "student_scalar",
            "human_annotations",
            "primary_dimension"
        ]

        for col in required_columns:
            assert col in df.columns, f"Missing required column: {col}"

    def test_generate_synthetic_dataset_teacher_scores_structure(self, tmp_path):
        """Test that teacher_scores column has correct nested structure."""
        output_path = tmp_path / "mock_z_reward.parquet"

        df = generate_synthetic_dataset(
            n_samples=100,
            seed=42,
            output_path=str(output_path)
        )

        # Check first row
        first_teacher_scores = df.iloc[0]["teacher_scores"]
        assert isinstance(first_teacher_scores, dict), "teacher_scores should be a dict"

        required_keys = ["Alignment", "Realism", "Aesthetics", "Plausibility"]
        for key in required_keys:
            assert key in first_teacher_scores, f"Missing key in teacher_scores: {key}"
            assert isinstance(first_teacher_scores[key], (int, float)), f"{key} should be numeric"

    def test_generate_synthetic_dataset_human_annotations_structure(self, tmp_path):
        """Test that human_annotations column has correct nested structure."""
        output_path = tmp_path / "mock_z_reward.parquet"

        df = generate_synthetic_dataset(
            n_samples=100,
            seed=42,
            output_path=str(output_path)
        )

        # Check first row
        first_annotations = df.iloc[0]["human_annotations"]
        assert isinstance(first_annotations, dict), "human_annotations should be a dict"

        required_keys = ["Alignment", "Realism", "Aesthetics", "Plausibility"]
        for key in required_keys:
            assert key in first_annotations, f"Missing key in human_annotations: {key}"
            assert isinstance(first_annotations[key], (int, float)), f"{key} should be numeric"

    def test_generate_synthetic_dataset_independence(self, tmp_path):
        """Test that teacher scores and human annotations have independent noise."""
        output_path = tmp_path / "mock_z_reward.parquet"

        df = generate_synthetic_dataset(
            n_samples=1000,
            seed=42,
            output_path=str(output_path)
        )

        # Extract teacher and human scores for Alignment dimension
        teacher_alignment = np.array([row["Alignment"] for row in df["teacher_scores"]])
        human_alignment = np.array([row["Alignment"] for row in df["human_annotations"]])

        # Calculate correlation (should be low due to independent noise)
        correlation = np.corrcoef(teacher_alignment, human_alignment)[0, 1]

        # With independent noise, correlation should be close to 0 (allowing for some randomness)
        # We use a loose threshold since this is synthetic data with small sample size
        assert abs(correlation) < 0.3, f"Teacher and human scores should be independent (correlation={correlation})"

    def test_save_config_creates_file(self, tmp_path):
        """Test that save_config creates the config.json file."""
        config_dir = tmp_path / "config"

        save_config(output_dir=str(config_dir), is_mock=True)

        config_path = config_dir / "config.json"
        assert config_path.exists(), "Config file was not created"

        with open(config_path, "r") as f:
            config = json.load(f)

        assert "IS_MOCK_DATA" in config, "Config should contain IS_MOCK_DATA"
        assert config["IS_MOCK_DATA"] is True, "IS_MOCK_DATA should be True"

    def test_save_config_is_mock_false(self, tmp_path):
        """Test that save_config can set IS_MOCK_DATA to False."""
        config_dir = tmp_path / "config"

        save_config(output_dir=str(config_dir), is_mock=False)

        config_path = config_dir / "config.json"

        with open(config_path, "r") as f:
            config = json.load(f)

        assert config["IS_MOCK_DATA"] is False, "IS_MOCK_DATA should be False"

    def test_generate_synthetic_dataset_reproducibility(self, tmp_path):
        """Test that the same seed produces the same results."""
        output_path1 = tmp_path / "mock1.parquet"
        output_path2 = tmp_path / "mock2.parquet"

        df1 = generate_synthetic_dataset(n_samples=100, seed=42, output_path=str(output_path1))
        df2 = generate_synthetic_dataset(n_samples=100, seed=42, output_path=str(output_path2))

        # Compare a few values
        assert df1.iloc[0]["student_scalar"] == df2.iloc[0]["student_scalar"], "Same seed should produce same results"
        assert df1.iloc[0]["teacher_scores"]["Alignment"] == df2.iloc[0]["teacher_scores"]["Alignment"]
        assert df1.iloc[0]["human_annotations"]["Alignment"] == df2.iloc[0]["human_annotations"]["Alignment"]

    def test_generate_synthetic_dataset_primary_dimension_values(self, tmp_path):
        """Test that primary_dimension contains valid dimension names."""
        output_path = tmp_path / "mock_z_reward.parquet"

        df = generate_synthetic_dataset(
            n_samples=100,
            seed=42,
            output_path=str(output_path)
        )

        valid_dimensions = ["Alignment", "Realism", "Aesthetics", "Plausibility"]

        for dim in df["primary_dimension"]:
            assert dim in valid_dimensions, f"Invalid primary_dimension value: {dim}"