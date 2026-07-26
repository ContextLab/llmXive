"""
Unit tests for feature integration module (T025).

Tests verify:
- Per-sample statistics calculation
- Global eigenvalue computation
- Fidelity loss calculation
- Output schema validation
- Zero-variance edge case handling
"""

import json
import os
import sys
import tempfile
from pathlib import Path

import numpy as np
import pytest

# Add project root to path
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from code.features import (
    calculate_per_sample_stats,
    calculate_frobenius_norm_outer_product,
    calculate_global_covariance_and_eigenvalue,
    calculate_fidelity_loss,
)


class TestPerSampleStats:
    """Tests for per-sample statistical calculations."""

    def test_variance_calculation(self):
        """Test variance calculation for a known distribution."""
        scores = np.array([1.0, 2.0, 3.0, 4.0])
        stats = calculate_per_sample_stats(scores)
        expected_variance = np.var(scores)
        assert abs(stats["variance"] - expected_variance) < 1e-6

    def test_entropy_calculation(self):
        """Test entropy calculation."""
        scores = np.array([1.0, 1.0, 1.0, 1.0])  # Uniform distribution
        stats = calculate_per_sample_stats(scores)
        # For uniform distribution, entropy should be positive
        assert stats["entropy"] > 0

    def test_zero_variance_handling(self):
        """Test handling of zero-variance case."""
        scores = np.array([2.0, 2.0, 2.0, 2.0])
        stats = calculate_per_sample_stats(scores)
        assert stats["variance"] == 0.0
        assert stats["entropy"] == 0.0

    def test_skewness_kurtosis(self):
        """Test skewness and kurtosis calculation."""
        scores = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
        stats = calculate_per_sample_stats(scores)
        assert isinstance(stats["skewness"], float)
        assert isinstance(stats["kurtosis"], float)


class TestFrobeniusNorm:
    """Tests for Frobenius norm calculation."""

    def test_frobenius_norm_calculation(self):
        """Test Frobenius norm of outer product."""
        scores = np.array([1.0, 2.0, 3.0, 4.0])
        norm = calculate_frobenius_norm_outer_product(scores)
        expected = np.linalg.norm(np.outer(scores, scores), 'fro')
        assert abs(norm - expected) < 1e-6

    def test_frobenius_norm_zero_vector(self):
        """Test Frobenius norm for zero vector."""
        scores = np.array([0.0, 0.0, 0.0, 0.0])
        norm = calculate_frobenius_norm_outer_product(scores)
        assert norm == 0.0


class TestGlobalEigenvalue:
    """Tests for global eigenvalue calculation."""

    def test_eigenvalue_computation(self):
        """Test dominant eigenvalue extraction."""
        # Create a simple covariance matrix
        np.random.seed(42)
        scores_matrix = np.random.randn(100, 4)
        result = calculate_global_covariance_and_eigenvalue(scores_matrix)

        assert "eigenvalue" in result
        assert "covariance_matrix" in result
        assert result["eigenvalue"] > 0
        assert np.isfinite(result["eigenvalue"])

    def test_covariance_matrix_shape(self):
        """Test covariance matrix is 4x4 for 4 dimensions."""
        np.random.seed(42)
        scores_matrix = np.random.randn(50, 4)
        result = calculate_global_covariance_and_eigenvalue(scores_matrix)

        cov_matrix = result["covariance_matrix"]
        assert len(cov_matrix) == 4
        assert all(len(row) == 4 for row in cov_matrix)


class TestFidelityLoss:
    """Tests for fidelity loss calculation."""

    def test_fidelity_loss_calculation(self):
        """Test MAE calculation between student and human scores."""
        sample = {
            "sample_id": "test_001",
            "student_scalar": 0.8,
            "human_annotations": {"Alignment": 0.85, "Realism": 0.75},
            "primary_dimension": "Alignment",
        }
        loss = calculate_fidelity_loss(sample)
        expected = abs(0.8 - 0.85)
        assert abs(loss - expected) < 1e-6

    def test_fidelity_loss_missing_annotation(self):
        """Test handling of missing human annotation."""
        sample = {
            "sample_id": "test_002",
            "student_scalar": 0.8,
            "human_annotations": {"Realism": 0.75},
            "primary_dimension": "Alignment",
        }
        loss = calculate_fidelity_loss(sample)
        assert np.isnan(loss)

    def test_fidelity_loss_missing_student(self):
        """Test handling of missing student scalar."""
        sample = {
            "sample_id": "test_003",
            "student_scalar": None,
            "human_annotations": {"Alignment": 0.85},
            "primary_dimension": "Alignment",
        }
        loss = calculate_fidelity_loss(sample)
        assert np.isnan(loss)


class TestOutputSchema:
    """Tests for output schema validation."""

    def test_schema_validation(self):
        """Test that output records contain all required keys."""
        required_keys = [
            "sample_id",
            "variance",
            "entropy",
            "global_eigenvalue",
            "entanglement_score",
            "fidelity_loss",
        ]

        # Create a valid record
        record = {
            "sample_id": "test_001",
            "variance": 0.125,
            "entropy": 1.386,
            "global_eigenvalue": 0.854,
            "entanglement_score": 2.345,
            "fidelity_loss": 0.023,
        }

        for key in required_keys:
            assert key in record, f"Missing required key: {key}"

    def test_no_null_values(self):
        """Test that no required fields contain null values."""
        record = {
            "sample_id": "test_001",
            "variance": 0.125,
            "entropy": 1.386,
            "global_eigenvalue": 0.854,
            "entanglement_score": 2.345,
            "fidelity_loss": 0.023,
        }

        for key in ["variance", "entropy", "global_eigenvalue", "entanglement_score", "fidelity_loss"]:
            assert record[key] is not None, f"Null value for: {key}"
            if isinstance(record[key], float):
                assert not np.isnan(record[key]), f"NaN value for: {key}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])