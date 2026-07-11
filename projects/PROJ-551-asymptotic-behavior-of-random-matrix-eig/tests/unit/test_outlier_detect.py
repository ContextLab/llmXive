"""
Unit tests for outlier detection logic.
"""
import numpy as np
import pytest

from data_models import PerturbationConfig
from analysis.outlier_detect import (
    calculate_bbp_threshold,
    detect_outliers,
    OutlierResult
)

class TestBBPThreshold:
    """Tests for BBP threshold calculation."""

    def test_subcritical_theta(self):
        """Test threshold for theta <= 1 (no outlier)."""
        assert calculate_bbp_threshold(0.5) == 2.0
        assert calculate_bbp_threshold(1.0) == 2.0

    def test_supercritical_theta(self):
        """Test threshold for theta > 1."""
        theta = 2.0
        expected = theta + 1.0 / theta
        assert calculate_bbp_threshold(theta) == pytest.approx(expected)

        theta = 3.0
        expected = theta + 1.0 / theta
        assert calculate_bbp_threshold(theta) == pytest.approx(expected)

class TestDetectOutliers:
    """Tests for outlier detection logic."""

    def test_no_outliers_bulk_only(self):
        """Test detection when all eigenvalues are within bulk."""
        # Simulate bulk eigenvalues (all < 2.0)
        eigenvalues = np.array([1.95, 1.90, 1.85, 1.5, 1.0, -1.0, -1.5, -1.8, -1.9, -1.95])
        config = PerturbationConfig(norm=0.5, rank=1) # Subcritical

        result = detect_outliers(eigenvalues, config, matrix_size=1000)

        assert result.is_outlier_present is False
        assert len(result.outlier_indices) == 0
        assert len(result.outlier_values) == 0
        assert len(result.bulk_indices) == 10

    def test_single_outlier_supercritical(self):
        """Test detection of a single outlier with supercritical theta."""
        # Simulate an outlier at 2.5 (BBP for theta=2.5 is 2.9, but finite N might vary)
        # We just need it > 2.0 to be detected as outlier in strict mode
        eigenvalues = np.array([2.85, 1.95, 1.90, 1.85, 1.5, 1.0, -1.0, -1.5, -1.8, -1.9])
        config = PerturbationConfig(norm=2.5, rank=1) # Supercritical

        result = detect_outliers(eigenvalues, config, matrix_size=1000)

        assert result.is_outlier_present is True
        assert len(result.outlier_indices) == 1
        assert result.outlier_values[0] == pytest.approx(2.85)
        assert len(result.bulk_indices) == 9

    def test_multiple_outliers_rank_k(self):
        """Test detection with rank-k perturbation (multiple outliers)."""
        # Simulate 2 outliers
        eigenvalues = np.array([3.0, 2.9, 1.95, 1.90, 1.85, 1.5, 1.0, -1.0, -1.5, -1.8])
        config = PerturbationConfig(norm=2.5, rank=2)

        result = detect_outliers(eigenvalues, config, matrix_size=1000)

        assert result.is_outlier_present is True
        assert len(result.outlier_indices) == 2
        assert len(result.bulk_indices) == 8

    def test_boundary_case(self):
        """Test eigenvalue exactly at bulk edge + tolerance."""
        # Create a value slightly above 2.0
        eigenvalues = np.array([2.000001, 1.99, 1.98])
        config = PerturbationConfig(norm=2.0, rank=1)

        result = detect_outliers(eigenvalues, config, matrix_size=1000)

        # Should be detected as outlier if > 2.0 + tolerance
        # Tolerance is max(1e-8, 2.0 * 1e-6 * sqrt(1000)) ~ 0.000063
        # 2.000001 is less than 2.000063, so it should be bulk
        assert result.is_outlier_present is False
        assert len(result.bulk_indices) == 3

    def test_empty_eigenvalues(self):
        """Test with empty eigenvalue array."""
        eigenvalues = np.array([])
        config = PerturbationConfig(norm=2.0, rank=1)

        result = detect_outliers(eigenvalues, config, matrix_size=1000)

        assert result.is_outlier_present is False
        assert len(result.outlier_indices) == 0
        assert len(result.bulk_indices) == 0

class TestOutlierResult:
    """Tests for OutlierResult data structure."""

    def test_to_dict(self):
        """Test serialization to dictionary."""
        eigenvalues = np.array([2.5, 1.9, 1.8])
        result = OutlierResult(
            eigenvalues=eigenvalues,
            outlier_indices=[0],
            outlier_values=np.array([2.5]),
            bulk_indices=[1, 2],
            bulk_values=np.array([1.9, 1.8]),
            bbp_threshold=2.5,
            is_outlier_present=True
        )

        data = result.to_dict()

        assert "eigenvalues" in data
        assert "outlier_indices" in data
        assert "outlier_values" in data
        assert "bulk_indices" in data
        assert "bulk_values" in data
        assert "bbp_threshold" in data
        assert "is_outlier_present" in data
        assert data["is_outlier_present"] is True
        assert len(data["outlier_indices"]) == 1