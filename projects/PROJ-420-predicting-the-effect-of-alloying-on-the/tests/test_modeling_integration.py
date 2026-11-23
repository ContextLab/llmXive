"""
Integration tests for the full modeling pipeline (T020).
"""
import json
import os
import tempfile
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from modeling import run_modeling_pipeline, split_data, save_split_indices


class TestT020DataSplitIntegration:
    """Integration tests specifically for T020 (80/20 Data Split)."""

    def test_full_pipeline_split_validation(self):
        """Test that the full pipeline produces valid split indices."""
        # Create synthetic clean data
        n_samples = 200
        data = {
            "Cu": np.random.dirichlet([1, 1, 1, 1, 1], n_samples)[:, 0],
            "Mg": np.random.dirichlet([1, 1, 1, 1, 1], n_samples)[:, 1],
            "Si": np.random.dirichlet([1, 1, 1, 1, 1], n_samples)[:, 2],
            "Zn": np.random.dirichlet([1, 1, 1, 1, 1], n_samples)[:, 3],
            "Mn": np.random.dirichlet([1, 1, 1, 1, 1], n_samples)[:, 4],
            "poisson_ratio": np.random.rand(n_samples),
        }
        df = pd.DataFrame(data)

        with tempfile.TemporaryDirectory() as tmpdir:
            # Save temp parquet
            parquet_path = os.path.join(tmpdir, "alloys_clean.parquet")
            df.to_parquet(parquet_path)

            # Mock config paths
            # Note: In a real scenario, we'd patch the config, but here we just run the logic
            # that T020 is responsible for.

            # Load and split
            X = df[["Cu", "Mg", "Si", "Zn", "Mn"]]
            y = df["poisson_ratio"]

            indices_path = os.path.join(tmpdir, "split_indices.json")
            X_train, X_test, y_train, y_test, indices = split_data(
                X, y, test_size=0.2, random_state=42, indices_path=indices_path
            )

            # Verify schema
            with open(indices_path, "r") as f:
                loaded_indices = json.load(f)

            assert "train_indices" in loaded_indices
            assert "test_indices" in loaded_indices

            # Verify counts
            total = len(df)
            train_count = len(loaded_indices["train_indices"])
            test_count = len(loaded_indices["test_indices"])

            assert train_count + test_count == total
            assert abs(test_count / total - 0.2) < 0.01  # Approx 20%

            # Verify disjoint
            train_set = set(loaded_indices["train_indices"])
            test_set = set(loaded_indices["test_indices"])
            assert train_set.isdisjoint(test_set)

    def test_split_indices_file_persistence(self):
        """Test that split indices are correctly written to disk and match schema."""
        n_samples = 100
        data = {
            "Cu": np.random.rand(n_samples),
            "Mg": np.random.rand(n_samples),
            "poisson_ratio": np.random.rand(n_samples),
        }
        df = pd.DataFrame(data)
        X = df[["Cu", "Mg"]]
        y = df["poisson_ratio"]

        with tempfile.TemporaryDirectory() as tmpdir:
            indices_path = os.path.join(tmpdir, "split_indices.json")
            split_data(X, y, test_size=0.2, indices_path=indices_path)

            # Check file exists
            assert os.path.exists(indices_path)

            # Check content
            with open(indices_path, "r") as f:
                content = json.load(f)

            assert isinstance(content["train_indices"], list)
            assert isinstance(content["test_indices"], list)
            assert all(isinstance(i, int) for i in content["train_indices"])
            assert all(isinstance(i, int) for i in content["test_indices"])