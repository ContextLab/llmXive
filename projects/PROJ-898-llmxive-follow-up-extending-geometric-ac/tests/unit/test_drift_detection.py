import pytest
import numpy as np
import torch
import json
import os
import sys
import tempfile
import logging

# Add project root to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from latent_drift import LatentDriftDetector, load_reference_stats, compute_reference_stats_from_latents
from utils import set_deterministic_seed

logger = logging.getLogger(__name__)

class TestLatentDriftDetector:
    """Unit tests for the LatentDriftDetector class."""

    @pytest.fixture
    def sample_mean(self):
        """Sample mean vector for testing."""
        return np.zeros(32, dtype=np.float32)

    @pytest.fixture
    def sample_cov_inv(self):
        """Sample inverse covariance matrix for testing."""
        return np.eye(32, dtype=np.float32)

    @pytest.fixture
    def detector(self, sample_mean, sample_cov_inv):
        """Create a LatentDriftDetector instance."""
        return LatentDriftDetector(sample_mean, sample_cov_inv)

    def test_initialization(self, sample_mean, sample_cov_inv):
        """Test that the detector initializes correctly."""
        detector = LatentDriftDetector(sample_mean, sample_cov_inv)
        
        assert detector.mean.shape == (32,)
        assert detector.cov_inv.shape == (32, 32)
        assert np.allclose(detector.mean, sample_mean)
        assert np.allclose(detector.cov_inv, sample_cov_inv)

    def test_mahalanobis_distance_with_identity_cov(self, detector):
        """Test Mahalanobis distance with identity covariance matrix."""
        # For identity covariance, Mahalanobis distance equals Euclidean distance
        sample = np.array([1.0, 2.0, 3.0] + [0.0] * 29, dtype=np.float32)
        expected_distance = np.sqrt(1**2 + 2**2 + 3**2)
        
        actual_distance = detector.compute_mahalanobis(sample)
        
        assert np.isclose(actual_distance, expected_distance, rtol=1e-5)

    def test_mahalanobis_distance_with_non_identity_cov(self):
        """Test Mahalanobis distance with non-identity covariance."""
        mean = np.zeros(32, dtype=np.float32)
        # Create a diagonal covariance matrix with different variances
        cov_diag = np.array([1.0, 4.0, 9.0] + [1.0] * 29, dtype=np.float32)
        cov_inv = np.diag(1.0 / cov_diag)
        
        detector = LatentDriftDetector(mean, cov_inv)
        
        # Sample: [1, 2, 3, 0, ..., 0]
        sample = np.array([1.0, 2.0, 3.0] + [0.0] * 29, dtype=np.float32)
        
        # Mahalanobis distance: sqrt(sum((x_i - mean_i)^2 / var_i))
        expected_distance = np.sqrt(1**2/1 + 2**2/4 + 3**2/9)
        
        actual_distance = detector.compute_mahalanobis(sample)
        
        assert np.isclose(actual_distance, expected_distance, rtol=1e-5)

    def test_drift_detection_with_threshold(self, detector):
        """Test drift detection with various thresholds."""
        sample = np.zeros(32, dtype=np.float32)
        
        # At mean, distance should be 0
        is_drift, distance = detector.detect_drift(sample, threshold=1.0)
        assert is_drift is False
        assert distance == 0.0

    def test_drift_detection_with_outlier(self, detector):
        """Test drift detection with an outlier sample."""
        # Create an outlier: 5 standard deviations away
        sample = np.full(32, 5.0, dtype=np.float32)
        
        is_drift, distance = detector.detect_drift(sample, threshold=3.0)
        
        assert is_drift is True
        assert distance > 3.0

    def test_invalid_threshold_raises_error(self, detector):
        """Test that invalid thresholds raise appropriate errors."""
        sample = np.zeros(32, dtype=np.float32)
        
        with pytest.raises(ValueError):
            detector.detect_drift(sample, threshold=-1.0)
        
        with pytest.raises(ValueError):
            detector.detect_drift(sample, threshold=0.0)

    def test_numerical_stability_with_large_values(self, detector):
        """Test numerical stability with large input values."""
        large_sample = np.full(32, 1e6, dtype=np.float32)
        
        distance = detector.compute_mahalanobis(large_sample)
        
        assert not np.isnan(distance)
        assert not np.isinf(distance)
        assert distance > 0.0

    def test_batch_mahalanobis_computation(self, detector):
        """Test Mahalanobis distance computation for a batch of samples."""
        batch_size = 10
        samples = np.random.randn(batch_size, 32).astype(np.float32)
        
        distances = []
        for sample in samples:
            distance = detector.compute_mahalanobis(sample)
            distances.append(distance)
        
        assert len(distances) == batch_size
        assert all(not np.isnan(d) and not np.isinf(d) for d in distances)
        assert all(d >= 0.0 for d in distances)

    def test_detector_with_different_distributions(self):
        """Test detector sensitivity to different data distributions."""
        mean = np.zeros(32, dtype=np.float32)
        cov_inv = np.eye(32, dtype=np.float32)
        detector = LatentDriftDetector(mean, cov_inv)
        
        # In-distribution sample (close to mean)
        in_dist = np.random.randn(32).astype(np.float32) * 0.5
        is_drift_in, dist_in = detector.detect_drift(in_dist, threshold=3.0)
        
        # Out-of-distribution sample (far from mean)
        ood = np.random.randn(32).astype(np.float32) * 10.0
        is_drift_ood, dist_ood = detector.detect_drift(ood, threshold=3.0)
        
        assert is_drift_in is False
        assert is_drift_ood is True
        assert dist_ood > dist_in

class TestLoadReferenceStats:
    """Unit tests for loading reference statistics from JSON files."""

    def test_load_valid_stats(self):
        """Test loading valid reference statistics."""
        stats = {
            "mean": [0.0] * 32,
            "cov_inv": [[1.0 if i == j else 0.0 for j in range(32)] for i in range(32)]
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(stats, f)
            stats_file = f.name
        
        try:
            mean, cov_inv = load_reference_stats(stats_file)
            
            assert len(mean) == 32
            assert cov_inv.shape == (32, 32)
            assert np.allclose(mean, stats["mean"])
            assert np.allclose(cov_inv, stats["cov_inv"])
        finally:
            os.unlink(stats_file)

    def test_load_invalid_file_raises_error(self):
        """Test that loading from an invalid file raises an error."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write("invalid json content")
            stats_file = f.name
        
        try:
            with pytest.raises((json.JSONDecodeError, KeyError)):
                load_reference_stats(stats_file)
        finally:
            os.unlink(stats_file)

    def test_load_missing_file_raises_error(self):
        """Test that loading from a missing file raises an error."""
        with pytest.raises(FileNotFoundError):
            load_reference_stats("/nonexistent/path/to/stats.json")

    def test_load_with_malformed_structure(self):
        """Test loading with malformed JSON structure."""
        malformed_stats = {
            "mean": [0.0] * 10,  # Wrong size
            "cov_inv": [[1.0]]  # Wrong shape
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(malformed_stats, f)
            stats_file = f.name
        
        try:
            # This should raise an error due to dimension mismatch
            with pytest.raises((ValueError, KeyError)):
                load_reference_stats(stats_file)
        finally:
            os.unlink(stats_file)

class TestComputeReferenceStatsFromLatents:
    """Unit tests for computing reference statistics from latent vectors."""

    def test_compute_stats_from_valid_latents(self):
        """Test computing statistics from a valid set of latent vectors."""
        set_deterministic_seed(42)
        
        n_samples = 1000
        dim = 32
        latents = np.random.randn(n_samples, dim).astype(np.float32)
        
        mean, cov_inv = compute_reference_stats_from_latents(latents)
        
        assert len(mean) == dim
        assert cov_inv.shape == (dim, dim)
        
        # Verify mean is close to zero (for standard normal data)
        assert np.allclose(mean, 0.0, atol=0.1)
        
        # Verify covariance inverse is positive definite
        eigenvalues = np.linalg.eigvalsh(cov_inv)
        assert np.all(eigenvalues > 0)

    def test_compute_stats_with_small_sample(self):
        """Test computing statistics with a small sample size."""
        n_samples = 10
        dim = 32
        latents = np.random.randn(n_samples, dim).astype(np.float32)
        
        # This should work but might be numerically unstable
        mean, cov_inv = compute_reference_stats_from_latents(latents)
        
        assert len(mean) == dim
        assert cov_inv.shape == (dim, dim)

    def test_compute_stats_with_constant_latents(self):
        """Test computing statistics when all latents are identical."""
        dim = 32
        constant_value = 5.0
        latents = np.full((100, dim), constant_value, dtype=np.float32)
        
        # This should result in a singular covariance matrix
        # The function should handle this gracefully (e.g., by adding regularization)
        mean, cov_inv = compute_reference_stats_from_latents(latents)
        
        assert len(mean) == dim
        assert cov_inv.shape == (dim, dim)
        assert np.allclose(mean, constant_value)

    def test_compute_stats_with_outliers(self):
        """Test computing statistics with outliers in the data."""
        n_samples = 1000
        dim = 32
        latents = np.random.randn(n_samples, dim).astype(np.float32)
        
        # Add some outliers
        latents[0] = np.full(dim, 100.0, dtype=np.float32)
        latents[1] = np.full(dim, -100.0, dtype=np.float32)
        
        mean, cov_inv = compute_reference_stats_from_latents(latents)
        
        assert len(mean) == dim
        assert cov_inv.shape == (dim, dim)
        
        # The mean should be slightly shifted due to outliers
        assert not np.allclose(mean, 0.0, atol=0.01)

    def test_compute_stats_with_different_dimensions(self):
        """Test computing statistics with different latent dimensions."""
        for dim in [16, 32, 64, 128]:
            n_samples = 500
            latents = np.random.randn(n_samples, dim).astype(np.float32)
            
            mean, cov_inv = compute_reference_stats_from_latents(latents)
            
            assert len(mean) == dim
            assert cov_inv.shape == (dim, dim)

class TestDriftDetectorEdgeCases:
    """Edge case tests for drift detection."""

    def test_detector_with_zero_variance(self):
        """Test detector behavior when variance is zero."""
        mean = np.zeros(32, dtype=np.float32)
        # Create a covariance inverse with very large values (near-zero variance)
        cov_inv = np.eye(32, dtype=np.float32) * 1e10
        
        detector = LatentDriftDetector(mean, cov_inv)
        
        sample = np.zeros(32, dtype=np.float32)
        distance = detector.compute_mahalanobis(sample)
        
        assert distance == 0.0

    def test_detector_with_very_small_variance(self):
        """Test detector with very small variance."""
        mean = np.zeros(32, dtype=np.float32)
        cov_inv = np.eye(32, dtype=np.float32) * 1e-10
        
        detector = LatentDriftDetector(mean, cov_inv)
        
        sample = np.ones(32, dtype=np.float32)
        distance = detector.compute_mahalanobis(sample)
        
        # Should be very large due to small variance
        assert distance > 1e5

    def test_detector_with_singular_covariance(self):
        """Test detector with singular covariance matrix."""
        mean = np.zeros(32, dtype=np.float32)
        # Create a singular matrix (rank 1)
        cov_inv = np.ones((32, 32), dtype=np.float32)
        
        detector = LatentDriftDetector(mean, cov_inv)
        
        sample = np.random.randn(32).astype(np.float32)
        
        # This might raise an error or produce unexpected results
        # The detector should handle this gracefully
        try:
            distance = detector.compute_mahalanobis(sample)
            # If it doesn't raise, the distance should be a valid number
            assert not np.isnan(distance)
        except np.linalg.LinAlgError:
            # Singular matrix error is acceptable
            pass

    def test_detector_with_very_high_dimension(self):
        """Test detector with very high dimensional data."""
        dim = 1000
        mean = np.zeros(dim, dtype=np.float32)
        cov_inv = np.eye(dim, dtype=np.float32)
        
        detector = LatentDriftDetector(mean, cov_inv)
        
        sample = np.random.randn(dim).astype(np.float32)
        distance = detector.compute_mahalanobis(sample)
        
        assert not np.isnan(distance)
        assert not np.isinf(distance)
        assert distance > 0.0