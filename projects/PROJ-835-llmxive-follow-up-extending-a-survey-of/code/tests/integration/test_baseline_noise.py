"""
Integration test for T023: Generate synthetic random noise baseline.

Verifies that the baseline noise generation script:
1. Generates noise of the correct dimensionality
2. Calculates Mahalanobis distances correctly
3. Produces a valid output file
4. Generates reasonable anomaly rates for random noise
"""
import os
import sys
import json
import tempfile
import shutil
from pathlib import Path
import pytest
import numpy as np
import pandas as pd

# Add project root to path
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.models.baseline_noise import generate_gaussian_noise_baseline, calculate_baseline_distances
from src.utils.config import ensure_dir


class TestBaselineNoise:
    """Test suite for T023 baseline noise generation."""

    def test_generate_noise_correct_dimensions(self):
        """Test that generated noise has correct shape."""
        n_samples = 100
        dimension = 512  # Typical embedding dimension
        noise = generate_gaussian_noise_baseline(n_samples, dimension, seed=42)

        assert noise.shape == (n_samples, dimension), f"Expected shape ({n_samples}, {dimension}), got {noise.shape}"
        assert noise.dtype in [np.float32, np.float64], f"Expected float dtype, got {noise.dtype}"

    def test_generate_noise_reproducibility(self):
        """Test that noise generation is reproducible with same seed."""
        dimension = 128
        noise1 = generate_gaussian_noise_baseline(10, dimension, seed=123)
        noise2 = generate_gaussian_noise_baseline(10, dimension, seed=123)
        noise3 = generate_gaussian_noise_baseline(10, dimension, seed=456)

        # Same seed should produce identical results
        assert np.array_equal(noise1, noise2), "Same seed should produce identical noise"
        # Different seed should produce different results
        assert not np.array_equal(noise1, noise3), "Different seeds should produce different noise"

    def test_generate_noise_distribution(self):
        """Test that generated noise approximates standard normal distribution."""
        n_samples = 10000
        dimension = 64
        noise = generate_gaussian_noise_baseline(n_samples, dimension, seed=42)

        # Flatten to check overall distribution
        flat_noise = noise.flatten()

        # Mean should be close to 0
        assert np.abs(np.mean(flat_noise)) < 0.1, f"Mean should be close to 0, got {np.mean(flat_noise)}"
        # Std should be close to 1
        assert 0.9 < np.std(flat_noise) < 1.1, f"Std should be close to 1, got {np.std(flat_noise)}"

    def test_calculate_baseline_distances_output_format(self):
        """Test that distance calculation produces correct output format."""
        # Create mock benign statistics
        dimension = 10
        benign_mean = np.zeros(dimension)
        benign_cov = np.eye(dimension)  # Identity covariance

        # Generate some noise
        noise_data = generate_gaussian_noise_baseline(50, dimension, seed=42)

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test_scores.parquet"

            results_df = calculate_baseline_distances(noise_data, benign_mean, benign_cov, output_path)

            # Check DataFrame structure
            expected_columns = ['sample_id', 'mahalanobis_distance', 'threshold_95', 'is_anomaly', 'label']
            assert list(results_df.columns) == expected_columns, f"Expected columns {expected_columns}, got {list(results_df.columns)}"

            # Check data types
            assert results_df['sample_id'].dtype == object
            assert results_df['mahalanobis_distance'].dtype in [np.float32, np.float64]
            assert results_df['threshold_95'].dtype in [np.float32, np.float64]
            assert results_df['is_anomaly'].dtype == bool
            assert results_df['label'].dtype == object

            # Check file was created
            assert output_path.exists(), "Output file should be created"

            # Check parquet can be read
            loaded_df = pd.read_parquet(output_path)
            assert len(loaded_df) == 50, "Loaded DataFrame should have 50 rows"

    def test_baseline_anomaly_rate_reasonable(self):
        """Test that random noise has a reasonable anomaly rate (should be ~5% for 95% threshold)."""
        dimension = 100
        n_samples = 1000
        benign_mean = np.zeros(dimension)
        benign_cov = np.eye(dimension)

        noise_data = generate_gaussian_noise_baseline(n_samples, dimension, seed=42)

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test_scores.parquet"
            results_df = calculate_baseline_distances(noise_data, benign_mean, benign_cov, output_path)

            anomaly_rate = results_df['is_anomaly'].mean()

            # For a 95% threshold on true Gaussian data, anomaly rate should be around 5%
            # Allow some variance due to finite sample size
            assert 0.01 < anomaly_rate < 0.15, f"Anomaly rate should be around 5%, got {anomaly_rate:.2%}"

    def test_baseline_distance_values_positive(self):
        """Test that all calculated Mahalanobis distances are non-negative."""
        dimension = 50
        benign_mean = np.zeros(dimension)
        benign_cov = np.eye(dimension)

        noise_data = generate_gaussian_noise_baseline(100, dimension, seed=42)

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test_scores.parquet"
            results_df = calculate_baseline_distances(noise_data, benign_mean, benign_cov, output_path)

            assert all(results_df['mahalanobis_distance'] >= 0), "All Mahalanobis distances should be non-negative"

    def test_baseline_threshold_correct(self):
        """Test that the 95% threshold is correctly calculated from chi2 distribution."""
        from scipy.stats import chi2

        dimension = 20
        expected_threshold = chi2.ppf(0.95, dimension)

        benign_mean = np.zeros(dimension)
        benign_cov = np.eye(dimension)
        noise_data = generate_gaussian_noise_baseline(10, dimension, seed=42)

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test_scores.parquet"
            results_df = calculate_baseline_distances(noise_data, benign_mean, benign_cov, output_path)

            actual_threshold = results_df['threshold_95'].iloc[0]
            assert abs(actual_threshold - expected_threshold) < 1e-6, f"Threshold mismatch: expected {expected_threshold}, got {actual_threshold}"