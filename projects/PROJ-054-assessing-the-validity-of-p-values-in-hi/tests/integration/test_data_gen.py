"""
Integration tests for data generation pipeline.
Tests for code/generate_data.py
"""
import numpy as np
import pytest
import json
import os
import tempfile
from pathlib import Path
from generate_data import generate_correlated_data, generate_distribution_violations, write_dataset_metadata


class TestDataGenerationIntegration:
    def test_full_data_generation_pipeline(self):
        """Test complete data generation pipeline from parameters to metadata."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir) / "synthetic"
            output_dir.mkdir()

            # Generate data
            n_samples, n_features = 100, 50
            data = generate_correlated_data(n_samples, n_features, rho=0.5, seed=42)

            # Write metadata
            metadata = write_dataset_metadata(
                data,
                seed=42,
                n_samples=n_samples,
                n_features=n_features,
                correlation=0.5,
                distribution_type="normal",
                output_path=output_dir
            )

            # Verify metadata file exists
            assert metadata is not None
            assert "sha256" in metadata
            assert metadata["n_samples"] == n_samples
            assert metadata["n_features"] == n_features
            assert metadata["correlation"] == 0.5
            assert metadata["distribution_type"] == "normal"

            # Verify file exists
            metadata_file = output_dir / f"{metadata['seed']}.json"
            assert metadata_file.exists()

            # Verify file content matches metadata
            with open(metadata_file) as f:
                saved_metadata = json.load(f)

            assert saved_metadata["sha256"] == metadata["sha256"]

    def test_distribution_violation_pipeline(self):
        """Test complete distribution violation generation pipeline."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir) / "synthetic"
            output_dir.mkdir()

            # Generate correlated base data
            n_samples, n_features = 100, 50
            base_data = generate_correlated_data(n_samples, n_features, rho=0.3, seed=42)

            # Apply distribution violation
            violated_data = generate_distribution_violations(
                n_samples, n_features,
                dist_type="t", df=3,
                seed=42,
                base_data=base_data
            )

            # Write metadata
            metadata = write_dataset_metadata(
                violated_data,
                seed=42,
                n_samples=n_samples,
                n_features=n_features,
                correlation=0.3,
                distribution_type="t",
                output_path=output_dir
            )

            # Verify
            assert metadata is not None
            assert metadata["distribution_type"] == "t"

    def test_large_scale_generation(self):
        """Test generation with larger dimensions."""
        n_samples, n_features = 500, 200
        data = generate_correlated_data(n_samples, n_features, rho=0.7, seed=42)

        assert data.shape == (n_samples, n_features)

        # Check correlation structure
        corr_matrix = np.corrcoef(data.T)
        off_diag = corr_matrix[np.triu_indices(n_features, k=1)]
        assert np.mean(off_diag) > 0.5

    def test_parameter_sweep_compatibility(self):
        """Test that generated data is compatible with parameter sweep."""
        params = [
            {"n": 100, "p": 50, "rho": 0.0},
            {"n": 100, "p": 50, "rho": 0.5},
            {"n": 100, "p": 50, "rho": 0.9},
        ]

        for param in params:
            data = generate_correlated_data(
                param["n"], param["p"],
                rho=param["rho"],
                seed=42
            )
            assert data.shape == (param["n"], param["p"])

    def test_multiple_seeds_consistency(self):
        """Test that multiple seeds produce consistent results."""
        seeds = [42, 123, 456, 789]
        results = []

        for seed in seeds:
            data = generate_correlated_data(100, 50, rho=0.5, seed=seed)
            results.append(data)

        # All results should have same shape
        assert all(r.shape == (100, 50) for r in results)

        # Different seeds should produce different data
        for i in range(len(results)):
            for j in range(i + 1, len(results)):
                assert not np.array_equal(results[i], results[j])

    def test_null_hypothesis_validity(self):
        """Test that generated data satisfies null hypothesis (no mean difference)."""
        n_samples, n_features = 100, 50
        data = generate_correlated_data(n_samples, n_features, rho=0.0, seed=42)

        # Split data into two groups
        half = n_samples // 2
        group1 = data[:half, :]
        group2 = data[half:, :]

        # Calculate means for each feature
        mean_diff = np.mean(group1, axis=0) - np.mean(group2, axis=0)

        # Mean differences should be close to zero (null hypothesis true)
        assert np.allclose(mean_diff, 0, atol=0.5)

    def test_data_integrity_across_operations(self):
        """Test data integrity through multiple operations."""
        n_samples, n_features = 100, 50

        # Generate data
        data1 = generate_correlated_data(n_samples, n_features, rho=0.5, seed=42)

        # Apply distribution violation
        data2 = generate_distribution_violations(
            n_samples, n_features,
            dist_type="t", df=3,
            seed=42,
            base_data=data1
        )

        # Generate again with same parameters
        data3 = generate_correlated_data(n_samples, n_features, rho=0.5, seed=42)
        data4 = generate_distribution_violations(
            n_samples, n_features,
            dist_type="t", df=3,
            seed=42,
            base_data=data3
        )

        # data2 and data4 should be identical (reproducible)
        np.testing.assert_array_equal(data2, data4)

    def test_memory_efficiency(self):
        """Test that data generation doesn't exceed memory limits."""
        # Generate moderately large dataset
        n_samples, n_features = 1000, 500
        data = generate_correlated_data(n_samples, n_features, rho=0.3, seed=42)

        # Check data size
        data_size_mb = data.nbytes / (1024 * 1024)
        assert data_size_mb < 100  # Should be less than 100MB

    def test_edge_cases(self):
        """Test edge cases in data generation."""
        # Minimum dimensions
        data_min = generate_correlated_data(2, 2, rho=0.0, seed=42)
        assert data_min.shape == (2, 2)

        # Maximum correlation
        data_max_rho = generate_correlated_data(50, 50, rho=0.99, seed=42)
        assert data_max_rho.shape == (50, 50)

        # No correlation
        data_zero_rho = generate_correlated_data(50, 50, rho=0.0, seed=42)
        assert data_zero_rho.shape == (50, 50)
