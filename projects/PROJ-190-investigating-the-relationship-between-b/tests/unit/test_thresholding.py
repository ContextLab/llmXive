"""
Unit tests for graph thresholding functionality.
"""

import numpy as np
import pytest
from pathlib import Path
import tempfile
import os

# Add parent directory to path for imports
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from graph.thresholding import (
    apply_proportional_threshold,
    threshold_connectivity_matrices,
    validate_thresholding,
    TARGET_DENSITIES
)


class TestProportionalThreshold:
    """Tests for apply_proportional_threshold function."""

    def test_basic_thresholding(self):
        """Test basic thresholding with a simple correlation matrix."""
        # Create a simple 5x5 correlation matrix
        np.random.seed(42)
        n = 5
        corr_matrix = np.random.rand(n, n)
        corr_matrix = (corr_matrix + corr_matrix.T) / 2
        np.fill_diagonal(corr_matrix, 1.0)

        # Apply threshold for 20% density
        binary_matrix, actual_density, num_edges = apply_proportional_threshold(
            corr_matrix,
            target_density=0.20,
            retain_positive_only=True
        )

        # Check matrix is binary
        assert np.all((binary_matrix == 0) | (binary_matrix == 1))

        # Check diagonal is zero (no self-loops)
        assert np.all(np.diag(binary_matrix) == 0)

        # Check symmetry
        assert np.allclose(binary_matrix, binary_matrix.T)

        # Check density is reasonable
        total_possible_edges = n * (n - 1) / 2
        expected_edges = int(np.ceil(total_possible_edges * 0.20))
        actual_edges = np.sum(binary_matrix) / 2

        # Allow some tolerance due to discrete edges
        assert abs(actual_edges - expected_edges) <= 1

    def test_density_accuracy(self):
        """Test that thresholding achieves target density within tolerance."""
        # Create a larger correlation matrix
        np.random.seed(42)
        n = 100
        corr_matrix = np.random.rand(n, n) * 2 - 1  # Range [-1, 1]
        corr_matrix = (corr_matrix + corr_matrix.T) / 2
        np.fill_diagonal(corr_matrix, 1.0)

        target_density = 0.15
        binary_matrix, actual_density, _ = apply_proportional_threshold(
            corr_matrix,
            target_density=target_density,
            retain_positive_only=True
        )

        # Check density is close to target (within 1%)
        assert abs(actual_density - target_density) < 0.01

    def test_invalid_density(self):
        """Test that invalid density values raise errors."""
        corr_matrix = np.eye(5)

        with pytest.raises(ValueError):
            apply_proportional_threshold(corr_matrix, target_density=1.5)

        with pytest.raises(ValueError):
            apply_proportional_threshold(corr_matrix, target_density=-0.1)

    def test_non_square_matrix(self):
        """Test that non-square matrices raise errors."""
        corr_matrix = np.random.rand(5, 6)

        with pytest.raises(ValueError):
            apply_proportional_threshold(corr_matrix, target_density=0.20)

    def test_all_negative_edges(self):
        """Test handling when no positive edges exist."""
        # Create a matrix with all negative off-diagonal values
        n = 5
        corr_matrix = np.full((n, n), -0.5)
        np.fill_diagonal(corr_matrix, 1.0)

        binary_matrix, actual_density, num_edges = apply_proportional_threshold(
            corr_matrix,
            target_density=0.20,
            retain_positive_only=True
        )

        # Should return all zeros
        assert np.sum(binary_matrix) == 0
        assert actual_density == 0.0
        assert num_edges == 0


class TestThresholdConnectivityMatrices:
    """Tests for threshold_connectivity_matrices function."""

    def test_multiple_subjects_multiple_densities(self):
        """Test thresholding for multiple subjects at multiple densities."""
        np.random.seed(42)
        n_nodes = 20

        # Create synthetic connectivity data
        connectivity_data = {
            f"subject_{i}": np.random.rand(n_nodes, n_nodes)
            for i in range(3)
        }

        densities = [0.10, 0.20]

        results = threshold_connectivity_matrices(
            connectivity_data,
            densities=densities,
            output_dir=None,
            retain_positive_only=True
        )

        # Check structure
        assert len(results) == 3
        for subject_id, density_results in results.items():
            assert len(density_results) == 2
            for density_str, data in density_results.items():
                assert 'matrix' in data
                assert 'actual_density' in data
                assert 'num_edges' in data
                assert data['matrix'].shape == (n_nodes, n_nodes)

    def test_output_directory(self):
        """Test saving to output directory."""
        np.random.seed(42)
        n_nodes = 10

        connectivity_data = {
            "test_subject": np.random.rand(n_nodes, n_nodes)
        }

        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            results = threshold_connectivity_matrices(
                connectivity_data,
                densities=[0.15],
                output_dir=output_dir,
                retain_positive_only=True
            )

            # Check files were created
            expected_file = output_dir / "test_subject_density_0.15.npy"
            assert expected_file.exists()

            # Check content
            loaded_matrix = np.load(expected_file)
            assert np.array_equal(loaded_matrix, results["test_subject"]["0.15"]["matrix"])


class TestValidateThresholding:
    """Tests for validate_thresholding function."""

    def test_validation_within_tolerance(self):
        """Test validation when densities are within tolerance."""
        thresholded_graphs = {
            "subject_1": {
                "0.15": {
                    "matrix": np.eye(10),
                    "actual_density": 0.151,
                    "num_edges": 10
                }
            }
        }

        validation = validate_thresholding(thresholded_graphs, tolerance=0.01)

        assert "subject_1" in validation
        assert any("OK" in msg for msg in validation["subject_1"])

    def test_validation_outside_tolerance(self):
        """Test validation when densities exceed tolerance."""
        thresholded_graphs = {
            "subject_1": {
                "0.15": {
                    "matrix": np.eye(10),
                    "actual_density": 0.20,
                    "num_edges": 10
                }
            }
        }

        validation = validate_thresholding(thresholded_graphs, tolerance=0.01)

        assert "subject_1" in validation
        assert any("deviation" in msg.lower() for msg in validation["subject_1"])


class TestTargetDensities:
    """Tests for target density constants."""

    def test_target_densities_defined(self):
        """Test that target densities are defined correctly."""
        assert 0.15 in TARGET_DENSITIES
        assert 0.20 in TARGET_DENSITIES
        assert 0.25 in TARGET_DENSITIES
        assert len(TARGET_DENSITIES) == 3

        # Check they are in ascending order
        assert TARGET_DENSITIES == sorted(TARGET_DENSITIES)
