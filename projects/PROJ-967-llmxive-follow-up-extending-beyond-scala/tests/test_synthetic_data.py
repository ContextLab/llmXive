"""
Unit tests for synthetic data generation (T037b).
"""

import json
import os
import tempfile
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

# Import the generator functions
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))
from synthetic_data import (
    generate_synthetic_dataset,
    generate_teacher_scores,
    generate_human_annotations,
    save_config,
)


class TestSyntheticGeneration:
    def test_schema_compliance(self):
        """Test that generated data matches the provisional schema."""
        df = generate_synthetic_dataset(n_samples=10, seed=42)

        required_columns = [
            "prompt",
            "image_url",
            "teacher_scores",
            "student_scalar",
            "human_annotations",
            "primary_dimension",
        ]

        for col in required_columns:
            assert col in df.columns, f"Missing column: {col}"

        # Check types
        assert df["prompt"].dtype == "object"
        assert df["image_url"].dtype == "object"
        assert df["student_scalar"].dtype in ["float64", "float32"]
        assert df["primary_dimension"].dtype == "object"

        # Check list structure in dicts
        for _, row in df.iterrows():
            assert isinstance(row["teacher_scores"], dict)
            assert isinstance(row["human_annotations"], dict)
            assert set(row["teacher_scores"].keys()) == {
                "Alignment",
                "Realism",
                "Aesthetics",
                "Plausibility",
            }
            assert set(row["human_annotations"].keys()) == {
                "Alignment",
                "Realism",
                "Aesthetics",
                "Plausibility",
            }

    def test_noise_independence(self):
        """Test that teacher and human scores have independent noise structures."""
        # Use a fixed seed to ensure reproducibility
        df = generate_synthetic_dataset(n_samples=100, seed=42)

        # Extract values
        teacher_vals = np.array([list(row.values()) for row in df["teacher_scores"]])
        human_vals = np.array([list(row.values()) for row in df["human_annotations"]])

        # They should not be identical (due to different seeds)
        assert not np.array_equal(teacher_vals, human_vals), (
            "Teacher and human scores should be independent."
        )

        # Check correlation is not perfect (should be low due to independent seeds)
        corr_matrix = np.corrcoef(teacher_vals.flatten(), human_vals.flatten())
        # Correlation should not be 1.0
        assert abs(corr_matrix[0, 1]) < 0.99, (
            "Teacher and human scores should not be perfectly correlated."
        )

    def test_primary_dimension_validity(self):
        """Test that primary_dimension is one of the valid options."""
        df = generate_synthetic_dataset(n_samples=50, seed=42)
        valid_dims = ["Alignment", "Realism", "Aesthetics", "Plausibility"]
        for dim in df["primary_dimension"]:
            assert dim in valid_dims, f"Invalid primary_dimension: {dim}"

    def test_config_flag_set(self):
        """Test that save_config sets IS_MOCK_DATA correctly."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "data" / "raw" / "test.parquet"
            output_path.parent.mkdir(parents=True, exist_ok=True)

            # Create dummy df
            df = generate_synthetic_dataset(10, 42)
            df.to_parquet(output_path, index=False)

            # Save config
            save_config(output_path, 10, 42)

            config_path = Path(tmpdir) / "data" / "processed" / "config.json"
            assert config_path.exists()

            with open(config_path, "r") as f:
                config = json.load(f)

            assert config.get("IS_MOCK_DATA") is True
            assert config.get("synthetic_n_samples") == 10
            assert config.get("synthetic_seed") == 42

    def test_reproducibility(self):
        """Test that same seed produces same results."""
        df1 = generate_synthetic_dataset(n_samples=10, seed=123)
        df2 = generate_synthetic_dataset(n_samples=10, seed=123)

        # Compare teacher scores specifically
        t1 = [list(row.values()) for row in df1["teacher_scores"]]
        t2 = [list(row.values()) for row in df2["teacher_scores"]]

        assert t1 == t2, "Same seed should produce identical results."

if __name__ == "__main__":
    pytest.main([__file__, "-v"])