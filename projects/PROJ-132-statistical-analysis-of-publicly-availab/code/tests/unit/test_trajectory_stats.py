"""
Unit tests for trajectory statistics computation.
"""
import json
import tempfile
from pathlib import Path

import numpy as np
import pytest

from src.models.trajectory_stats import (
    compute_frechet_variance,
    geodesic_regression,
    compute_trajectory_statistics,
    _ensure_sphere_metric,
    run_trajectory_statistics_pipeline
)
from geomstats.geometry.sphere import Sphere


@pytest.fixture
def sphere():
    return Sphere(dim=2, metric='intrinsic')


@pytest.fixture
def sample_centroids():
    # Create synthetic points on the sphere (unit vectors)
    # 5 weeks, 3D coordinates
    np.random.seed(42)
    points = np.random.randn(5, 3)
    points = points / np.linalg.norm(points, axis=1, keepdims=True)
    return points


@pytest.fixture
def sample_weeks():
    return np.array([0, 1, 2, 3, 4])


def test_ensure_sphere_metric():
    """Test that the sphere metric is correctly initialized."""
    sphere = _ensure_sphere_metric()
    assert sphere.dim == 2
    assert sphere.metric is not None


def test_compute_frechet_variance_empty(sphere):
    """Test variance computation with empty input."""
    points = np.array([]).reshape(0, 3)
    variance = compute_frechet_variance(points, sphere)
    assert variance == 0.0


def test_compute_frechet_variance_single_point(sphere):
    """Test variance with a single point (should be 0)."""
    point = np.array([[1.0, 0.0, 0.0]])
    variance = compute_frechet_variance(point, sphere)
    assert variance == 0.0


def test_compute_frechet_variance_multiple_points(sphere, sample_centroids):
    """Test variance computation with multiple points."""
    variance = compute_frechet_variance(sample_centroids, sphere)
    assert isinstance(variance, float)
    assert variance >= 0.0


def test_geodesic_regression_empty(sphere):
    """Test regression with empty input."""
    points = np.array([]).reshape(0, 3)
    times = np.array([])
    results = geodesic_regression(points, times, sphere)
    assert 'intercept' in results
    assert 'velocity' in results
    assert results['residual_variance'] == 0.0


def test_geodesic_regression_basic(sphere, sample_centroids, sample_weeks):
    """Test basic geodesic regression."""
    results = geodesic_regression(sample_centroids, sample_weeks, sphere)
    assert 'intercept' in results
    assert 'velocity' in results
    assert 'residual_variance' in results
    assert isinstance(results['intercept'], list)
    assert len(results['intercept']) == 3


def test_compute_trajectory_statistics(sphere, sample_centroids, sample_weeks):
    """Test full trajectory statistics computation."""
    stats = compute_trajectory_statistics("TestSpecies", 2023, sample_centroids, sample_weeks)

    assert stats['species'] == "TestSpecies"
    assert stats['year'] == 2023
    assert 'fréchet_variance' in stats
    assert 'geodesic_regression_coefficients' in stats
    assert 'parallel_transport_vectors' in stats

    # Check regression coefficients
    reg = stats['geodesic_regression_coefficients']
    assert 'intercept' in reg
    assert 'velocity' in reg
    assert 'residual_variance' in reg


def test_run_trajectory_statistics_pipeline():
    """Test the full pipeline with temporary data."""
    # Create a temporary directory and mock data file
    with tempfile.TemporaryDirectory() as tmpdir:
        input_path = Path(tmpdir) / "weekly_centroids.parquet"
        output_path = Path(tmpdir) / "trajectory_statistics.json"

        # Since we don't have the actual parquet file, we test the function structure
        # by checking that it doesn't crash on missing file (it should handle gracefully or fail loudly)
        # For this test, we just verify the function exists and has the right signature
        # The actual integration test would require real data

        # We expect a FileNotFoundError since the file doesn't exist
        with pytest.raises(FileNotFoundError):
            run_trajectory_statistics_pipeline(
                input_path=str(input_path),
                output_path=str(output_path)
            )