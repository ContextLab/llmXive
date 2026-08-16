import json
import os
import tempfile
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

# Import the module functions
# Note: We assume the module is in code/ and we can import it directly or via sys.path manipulation
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))
from generate_synthetic_zreward import generate_synthetic_dataset, save_config

class TestGenerateSyntheticZReward:
    def test_generates_correct_columns(self, tmp_path):
        """Test that the generated dataset has all required columns."""
        output_dir = str(tmp_path)
        df = generate_synthetic_dataset(n_samples=100, seed=42, output_dir=output_dir)

        expected_columns = [
            "prompt", "image_url", "teacher_scores",
            "student_scalar", "human_annotations", "primary_dimension"
        ]
        assert list(df.columns) == expected_columns, f"Expected columns {expected_columns}, got {list(df.columns)}"

    def test_teacher_scores_structure(self, tmp_path):
        """Test that teacher_scores column contains dicts with correct keys."""
        output_dir = str(tmp_path)
        df = generate_synthetic_dataset(n_samples=10, seed=42, output_dir=output_dir)

        required_keys = {"Alignment", "Realism", "Aesthetics", "Plausibility"}
        for i, row in df.iterrows():
            scores = row["teacher_scores"]
            assert isinstance(scores, dict), "teacher_scores must be a dict"
            assert set(scores.keys()) == required_keys, f"Missing keys in teacher_scores: {required_keys - set(scores.keys())}"
            for v in scores.values():
                assert isinstance(v, (int, float)), "Scores must be numeric"

    def test_human_annotations_structure(self, tmp_path):
        """Test that human_annotations column contains dicts with correct keys."""
        output_dir = str(tmp_path)
        df = generate_synthetic_dataset(n_samples=10, seed=42, output_dir=output_dir)

        required_keys = {"Alignment", "Realism", "Aesthetics", "Plausibility"}
        for i, row in df.iterrows():
            annotations = row["human_annotations"]
            assert isinstance(annotations, dict), "human_annotations must be a dict"
            assert set(annotations.keys()) == required_keys, f"Missing keys in human_annotations: {required_keys - set(annotations.keys())}"
            for v in annotations.values():
                assert isinstance(v, (int, float)), "Annotations must be numeric"

    def test_primary_dimension_values(self, tmp_path):
        """Test that primary_dimension contains valid dimension names."""
        output_dir = str(tmp_path)
        df = generate_synthetic_dataset(n_samples=100, seed=42, output_dir=output_dir)

        valid_dims = {"Alignment", "Realism", "Aesthetics", "Plausibility"}
        assert df["primary_dimension"].isin(valid_dims).all(), "All primary_dimension values must be valid"

    def test_file_output(self, tmp_path):
        """Test that the parquet file and config file are created."""
        output_dir = str(tmp_path)
        generate_synthetic_dataset(n_samples=10, seed=42, output_dir=output_dir)

        parquet_file = Path(output_dir) / "mock_z_reward.parquet"
        config_file = Path(output_dir) / "config.json"

        assert parquet_file.exists(), "Parquet file not created"
        assert config_file.exists(), "Config file not created"

    def test_config_is_mock_flag(self, tmp_path):
        """Test that the config file sets IS_MOCK_DATA to True."""
        output_dir = str(tmp_path)
        generate_synthetic_dataset(n_samples=10, seed=42, output_dir=output_dir)

        config_file = Path(output_dir) / "config.json"
        with open(config_file, "r") as f:
            config = json.load(f)

        assert config.get("IS_MOCK_DATA") is True, "IS_MOCK_DATA should be True"

    def test_reproducibility(self, tmp_path):
        """Test that running with the same seed produces the same data."""
        output_dir = str(tmp_path)
        df1 = generate_synthetic_dataset(n_samples=100, seed=42, output_dir=output_dir)
        
        # Clear output to regenerate
        (Path(output_dir) / "mock_z_reward.parquet").unlink()
        
        df2 = generate_synthetic_dataset(n_samples=100, seed=42, output_dir=output_dir)

        pd.testing.assert_frame_equal(df1, df2, check_exact=False, rtol=1e-5)

    def test_noise_independence(self, tmp_path):
        """Test that teacher scores and human annotations are independent (different seeds)."""
        output_dir = str(tmp_path)
        df = generate_synthetic_dataset(n_samples=1000, seed=42, output_dir=output_dir)

        # Extract arrays
        teacher_alignment = np.array([row["teacher_scores"]["Alignment"] for _, row in df.iterrows()])
        human_alignment = np.array([row["human_annotations"]["Alignment"] for _, row in df.iterrows()])

        # Calculate correlation; it should be low (near 0) due to independent seeds
        correlation = np.corrcoef(teacher_alignment, human_alignment)[0, 1]
        
        # Allow some noise, but it should not be perfectly correlated (1.0) or anti-correlated (-1.0)
        assert abs(correlation) < 0.9, f"Teacher and Human scores should be independent, but correlation is {correlation}"
