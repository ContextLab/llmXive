"""
Unit tests for the features.py module.

Tests statistical calculations (variance, entropy, skewness, kurtosis)
and matrix operations (covariance, eigenvalues).
"""

import json
import os
import tempfile
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
from scipy import stats

# Import the module under test
# We assume the test runs from the project root or tests directory
# Adjusting import path dynamically
import sys
import importlib.util

# Load features module from the parent directory
spec = importlib.util.spec_from_file_location(
    "features",
    Path(__file__).parent.parent / "code" / "features.py"
)
features = importlib.util.module_from_spec(spec)
spec.loader.exec_module(features)


class TestStatisticalHelpers:
    """Tests for calculate_variance_and_range, calculate_entropy, etc."""

    def test_variance_and_range(self):
        values = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
        var, range_val = features.calculate_variance_and_range(values)
        # Population variance: 2.0
        assert np.isclose(var, 2.0)
        assert np.isclose(range_val, 4.0)

    def test_variance_and_range_zero(self):
        values = np.array([5.0, 5.0, 5.0])
        var, range_val = features.calculate_variance_and_range(values)
        assert var == 0.0
        assert range_val == 0.0

    def test_entropy(self):
        # Uniform distribution over 2 bins
        values = np.array([1, 1, 2, 2])
        ent = features.calculate_entropy(values)
        # Should be 1.0 (log2(2))
        assert np.isclose(ent, 1.0, atol=0.1)

    def test_entropy_zero_variance(self):
        values = np.array([5.0, 5.0, 5.0])
        ent = features.calculate_entropy(values)
        assert ent == 0.0

    def test_skewness_and_kurtosis(self):
        # Normal distribution
        np.random.seed(42)
        values = np.random.normal(0, 1, 1000)
        skew, kurt = features.calculate_skewness_and_kurtosis(values)
        # Skew ~ 0, Kurtosis ~ 0 (excess kurtosis)
        assert np.isclose(skew, 0.0, atol=0.2)
        assert np.isclose(kurt, 0.0, atol=0.3)

    def test_skewness_and_kurtosis_small_sample(self):
        values = np.array([1.0, 2.0])
        skew, kurt = features.calculate_skewness_and_kurtosis(values)
        assert skew == 0.0
        assert kurt == 0.0


class TestGlobalCovariance:
    """Tests for calculate_global_covariance_and_eigenvalue."""

    def test_covariance_calculation(self):
        # Create a simple 4x4 covariance structure
        data = np.array([
            [1, 2, 3, 4],
            [1, 2, 3, 4],
            [2, 3, 4, 5],
            [2, 3, 4, 5]
        ], dtype=float)
        # Note: This data has perfect correlation, so eigenvalues will be specific
        cov, eig = features.calculate_global_covariance_and_eigenvalue(data)
        assert cov.shape == (4, 4)
        assert eig > 0

    def test_single_sample(self):
        data = np.array([[1, 2, 3, 4]], dtype=float)
        cov, eig = features.calculate_global_covariance_and_eigenvalue(data)
        assert cov.shape == (4, 4)
        assert eig == 0.0  # No variance with single sample


class TestPerSampleStats:
    """Tests for compute_per_sample_stats."""

    def test_per_sample_stats(self):
        # Create 2 samples, 4 dimensions
        data = np.array([
            [1, 2, 3, 4],
            [10, 20, 30, 40]
        ], dtype=float)
        df_stats = features.compute_per_sample_stats(data)

        assert df_stats.shape == (2, 4)
        assert "variance" in df_stats.columns
        assert "entropy" in df_stats.columns
        assert "skewness" in df_stats.columns
        assert "kurtosis" in df_stats.columns

        # Sample 0: 1,2,3,4 -> mean 2.5, var 1.25
        assert np.isclose(df_stats.iloc[0]["variance"], 1.25)


class TestIntegration:
    """Integration tests for the main pipeline functions."""

    def test_extract_teacher_scores_matrix_flat(self):
        df = pd.DataFrame({
            "Alignment": [1.0, 2.0],
            "Realism": [3.0, 4.0],
            "Aesthetics": [5.0, 6.0],
            "Plausibility": [7.0, 8.0]
        })
        matrix = features.extract_teacher_scores_matrix(df)
        assert matrix.shape == (2, 4)
        assert matrix[0, 0] == 1.0

    def test_extract_teacher_scores_matrix_nested(self):
        df = pd.DataFrame({
            "teacher_scores": [
                {"Alignment": 1.0, "Realism": 2.0, "Aesthetics": 3.0, "Plausibility": 4.0},
                {"Alignment": 5.0, "Realism": 6.0, "Aesthetics": 7.0, "Plausibility": 8.0}
            ]
        })
        matrix = features.extract_teacher_scores_matrix(df)
        assert matrix.shape == (2, 4)
        assert matrix[0, 0] == 1.0

    def test_integrate_features(self):
        df = pd.DataFrame({"id": [1, 2]})
        features_df = pd.DataFrame({"var": [1.0, 2.0], "ent": [0.5, 0.6]})
        combined = features.integrate_features(df, features_df)
        assert combined.shape == (2, 4)
        assert "var" in combined.columns

    def test_save_global_stats(self, tmp_path):
        cov = np.eye(4)
        eig = 1.0
        features.save_global_stats(cov, eig, tmp_path)

        assert (tmp_path / "covariance_matrix.json").exists()
        assert (tmp_path / "dominant_eigenvalue.json").exists()

        with open(tmp_path / "dominant_eigenvalue.json") as f:
            data = json.load(f)
            assert data["dominant_eigenvalue"] == 1.0

class TestMainExecution:
    """Tests for the main() function execution flow."""

    def test_main_missing_input(self, caplog):
        # Create a temp dir with no data
        with tempfile.TemporaryDirectory() as tmpdir:
            processed = Path(tmpdir) / "data" / "processed"
            processed.mkdir(parents=True)
            # No cleaned_data.parquet exists
            args = ["--input", str(processed / "cleaned_data.parquet")]
            # Mock sys.argv
            original_argv = sys.argv
            sys.argv = ["test"] + args
            try:
                with pytest.raises(SystemExit):
                    features.main()
            finally:
                sys.argv = original_argv