import json
import os
import tempfile
from pathlib import Path

import pandas as pd
import pytest

from generate_synthetic_zreward import generate_synthetic_dataset, save_config


class TestGenerateSyntheticZReward:
    def test_generate_synthetic_dataset_schema(self):
        """Test that generated dataset matches the expected schema."""
        n_samples = 10
        df = generate_synthetic_dataset(n_samples=n_samples, seed=42)

        # Check columns exist
        expected_columns = [
            "prompt",
            "image_url",
            "teacher_scores",
            "student_scalar",
            "human_annotations",
            "primary_dimension",
        ]
        assert list(df.columns) == expected_columns

        # Check row count
        assert len(df) == n_samples

        # Check teacher_scores structure
        for i in range(n_samples):
            scores = df.loc[i, "teacher_scores"]
            assert isinstance(scores, dict)
            assert set(scores.keys()) == {"Alignment", "Realism", "Aesthetics", "Plausibility"}
            for val in scores.values():
                assert isinstance(val, float)

        # Check human_annotations structure
        for i in range(n_samples):
            annotations = df.loc[i, "human_annotations"]
            assert isinstance(annotations, dict)
            assert set(annotations.keys()) == {"Alignment", "Realism", "Aesthetics", "Plausibility"}
            for val in annotations.values():
                assert isinstance(val, float)

        # Check primary_dimension values
        valid_dimensions = {"Alignment", "Realism", "Aesthetics", "Plausibility"}
        for i in range(n_samples):
            assert df.loc[i, "primary_dimension"] in valid_dimensions

    def test_noise_independence(self):
        """Test that teacher scores and human annotations have independent noise."""
        n_samples = 100
        df = generate_synthetic_dataset(n_samples=n_samples, seed=42)

        # Extract teacher and human scores for Alignment dimension
        teacher_alignment = [row["teacher_scores"]["Alignment"] for _, row in df.iterrows()]
        human_alignment = [row["human_annotations"]["Alignment"] for _, row in df.iterrows()]

        # Calculate correlation - should be low due to independent seeds
        import numpy as np

        correlation = np.corrcoef(teacher_alignment, human_alignment)[0, 1]

        # With independent noise, correlation should be close to 0
        # Allow some tolerance due to randomness
        assert abs(correlation) < 0.5, f"Correlation {correlation} suggests dependent noise"

    def test_save_config_creates_json(self):
        """Test that save_config creates a valid JSON file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            save_config(output_dir, is_mock=True)

            config_path = output_dir / "config.json"
            assert config_path.exists()

            with open(config_path, "r") as f:
                config = json.load(f)

            assert config["is_synthetic_run"] is True
            assert config["is_mock_data"] is True
            assert "source" in config
            assert "note" in config

    def test_deterministic_output(self):
        """Test that same seed produces same output."""
        df1 = generate_synthetic_dataset(n_samples=10, seed=123)
        df2 = generate_synthetic_dataset(n_samples=10, seed=123)

        # Compare teacher scores
        for i in range(10):
            assert df1.loc[i, "teacher_scores"] == df2.loc[i, "teacher_scores"]
            assert df1.loc[i, "human_annotations"] == df2.loc[i, "human_annotations"]
            assert df1.loc[i, "student_scalar"] == df2.loc[i, "student_scalar"]
            assert df1.loc[i, "primary_dimension"] == df2.loc[i, "primary_dimension"]
