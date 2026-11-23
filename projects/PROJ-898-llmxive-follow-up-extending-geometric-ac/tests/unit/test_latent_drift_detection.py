import pytest
import numpy as np
import torch
import json
import os
import sys
from unittest.mock import MagicMock, patch

# Add code directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'code'))

from latent_drift import LatentDriftDetector, load_reference_stats, compute_reference_stats_from_latents
from utils import set_deterministic_seed

class TestLatentDriftDetector:
    """Unit tests for LatentDriftDetector class."""

    def setup_method(self):
        """Set up test fixtures."""
        set_deterministic_seed(42)
        
        # Create mock reference statistics
        self.mock_reference_stats = {
            'latent_mean': np.random.randn(64).astype(np.float32),
            'latent_cov': np.eye(64).astype(np.float32) + 0.1 * np.random.randn(64, 64).astype(np.float32),
            'threshold': 15.0  # 99th percentile of chi-squared with 64 dof
        }
        
        # Ensure covariance is positive definite
        self.mock_reference_stats['latent_cov'] = (
            self.mock_reference_stats['latent_cov'].T @ 
            self.mock_reference_stats['latent_cov'] + 
            0.01 * np.eye(64)
        )
        
        self.detector = LatentDriftDetector(self.mock_reference_stats)

    def test_detector_initialization(self):
        """Test that detector initializes with correct parameters."""
        assert self.detector.reference_mean is not None
        assert self.detector.reference_cov is not None
        assert self.detector.threshold == 15.0
        assert self.detector.reference_mean.shape[0] == 64

    def test_mahalanobis_distance_computation(self):
        """Test Mahalanobis distance calculation."""
        # Create a latent vector at the mean (should have distance ~ 0)
        latent_at_mean = self.mock_reference_stats['latent_mean'].copy()
        
        distance = self.detector.compute_mahalanobis_distance(latent_at_mean)
        
        # Distance should be very small (close to 0)
        assert distance < 1.0
        
        # Create a latent vector far from the mean
        latent_far = latent_at_mean + 5.0 * np.ones(64, dtype=np.float32)
        
        distance_far = self.detector.compute_mahalanobis_distance(latent_far)
        
        # Distance should be large
        assert distance_far > distance
        assert distance_far > self.detector.threshold

    def test_drift_detection_in_distribution(self):
        """Test detection of in-distribution samples."""
        # Generate samples from the reference distribution
        n_samples = 100
        samples = np.random.multivariate_normal(
            self.mock_reference_stats['latent_mean'],
            self.mock_reference_stats['latent_cov'],
            size=n_samples
        ).astype(np.float32)
        
        drift_flags = []
        for sample in samples:
            is_drift = self.detector.detect_drift(sample)
            drift_flags.append(is_drift)
        
        # Most samples should not be flagged as drift
        drift_rate = sum(drift_flags) / len(drift_flags)
        assert drift_rate < 0.1  # Less than 10% should be flagged

    def test_drift_detection_out_of_distribution(self):
        """Test detection of out-of-distribution samples."""
        # Generate samples far from the reference distribution
        n_samples = 50
        base_samples = np.random.randn(n_samples, 64).astype(np.float32)
        ood_samples = base_samples + 3.0  # Shift mean significantly
        
        drift_flags = []
        for sample in ood_samples:
            is_drift = self.detector.detect_drift(sample)
            drift_flags.append(is_drift)
        
        # Most OOD samples should be flagged as drift
        drift_rate = sum(drift_flags) / len(drift_flags)
        assert drift_rate > 0.8  # More than 80% should be flagged

    def test_threshold_adjustment(self):
        """Test that threshold can be adjusted."""
        new_threshold = 20.0
        self.detector.set_threshold(new_threshold)
        
        assert self.detector.threshold == new_threshold

    def test_batch_drift_detection(self):
        """Test batch processing of latent vectors."""
        n_samples = 50
        samples = np.random.randn(n_samples, 64).astype(np.float32)
        
        results = self.detector.detect_batch_drift(samples)
        
        assert len(results['flags']) == n_samples
        assert len(results['distances']) == n_samples
        assert results['drift_count'] <= n_samples

    def test_invalid_input_handling(self):
        """Test handling of invalid input dimensions."""
        # Test with wrong dimension
        invalid_latent = np.random.randn(32).astype(np.float32)
        
        with pytest.raises(ValueError):
            self.detector.compute_mahalanobis_distance(invalid_latent)
        
        # Test with non-array input
        with pytest.raises(TypeError):
            self.detector.compute_mahalanobis_distance("invalid")

    def test_covariance_inversion_stability(self):
        """Test that covariance inversion is numerically stable."""
        # Create a nearly singular covariance matrix
        nearly_singular_cov = np.eye(64, dtype=np.float32)
        nearly_singular_cov[0, 0] = 1e-10
        
        stats = {
            'latent_mean': np.zeros(64, dtype=np.float32),
            'latent_cov': nearly_singular_cov,
            'threshold': 15.0
        }
        
        detector = LatentDriftDetector(stats)
        
        # Should not raise an exception
        latent = np.random.randn(64).astype(np.float32)
        distance = detector.compute_mahalanobis_distance(latent)
        
        assert not np.isnan(distance)
        assert not np.isinf(distance)

class TestReferenceStatsLoading:
    """Unit tests for reference statistics loading."""

    def test_load_reference_stats_from_file(self, tmp_path):
        """Test loading reference stats from a JSON file."""
        # Create a temporary stats file
        stats_data = {
            'latent_mean': np.random.randn(64).tolist(),
            'latent_cov': np.eye(64).tolist(),
            'threshold': 15.0
        }
        
        stats_file = tmp_path / "reference_stats.json"
        with open(stats_file, 'w') as f:
            json.dump(stats_data, f)
        
        # Load the stats
        loaded_stats = load_reference_stats(str(stats_file))
        
        assert loaded_stats is not None
        assert 'latent_mean' in loaded_stats
        assert 'latent_cov' in loaded_stats
        assert 'threshold' in loaded_stats
        assert len(loaded_stats['latent_mean']) == 64

    def test_load_reference_stats_missing_file(self, tmp_path):
        """Test handling of missing stats file."""
        with pytest.raises(FileNotFoundError):
            load_reference_stats(str(tmp_path / "nonexistent.json"))

    def test_load_reference_stats_invalid_format(self, tmp_path):
        """Test handling of invalid stats file format."""
        stats_file = tmp_path / "invalid_stats.json"
        with open(stats_file, 'w') as f:
            f.write("invalid json content")
        
        with pytest.raises((json.JSONDecodeError, ValueError)):
            load_reference_stats(str(stats_file))

class TestReferenceStatsComputation:
    """Unit tests for computing reference statistics from latents."""

    def setup_method(self):
        """Set up test fixtures."""
        set_deterministic_seed(42)

    def test_compute_stats_from_latents(self):
        """Test computing statistics from a set of latent vectors."""
        n_samples = 1000
        n_dims = 64
        
        # Generate random latent vectors
        latents = np.random.randn(n_samples, n_dims).astype(np.float32)
        
        # Compute statistics
        mean, cov = compute_reference_stats_from_latents(latents)
        
        assert mean.shape == (n_dims,)
        assert cov.shape == (n_dims, n_dims)
        
        # Mean should be close to zero for random data
        assert np.allclose(mean, 0, atol=0.1)
        
        # Covariance should be close to identity for random data
        assert np.allclose(cov, np.eye(n_dims), atol=0.1)

    def test_compute_stats_small_sample(self):
        """Test computing statistics with a small sample size."""
        n_samples = 10
        n_dims = 64
        
        latents = np.random.randn(n_samples, n_dims).astype(np.float32)
        
        # Should not raise an exception
        mean, cov = compute_reference_stats_from_latents(latents)
        
        assert mean.shape == (n_dims,)
        assert cov.shape == (n_dims, n_dims)

    def test_compute_stats_single_sample(self):
        """Test computing statistics with a single sample."""
        n_dims = 64
        
        latents = np.random.randn(1, n_dims).astype(np.float32)
        
        # With single sample, covariance should be zero
        mean, cov = compute_reference_stats_from_latents(latents)
        
        assert mean.shape == (n_dims,)
        assert cov.shape == (n_dims, n_dims)
        assert np.allclose(cov, 0)

class TestDriftThresholdValidation:
    """Unit tests for drift threshold validation."""

    def setup_method(self):
        """Set up test fixtures."""
        set_deterministic_seed(42)
        self.n_dims = 64

    def test_threshold_calculation_from_chi_squared(self):
        """Test that threshold corresponds to correct chi-squared percentile."""
        from scipy.stats import chi2
        
        # 99th percentile of chi-squared with 64 degrees of freedom
        expected_threshold = chi2.ppf(0.99, self.n_dims)
        
        # Our detector uses this threshold
        mock_stats = {
            'latent_mean': np.zeros(self.n_dims, dtype=np.float32),
            'latent_cov': np.eye(self.n_dims, dtype=np.float32),
            'threshold': expected_threshold
        }
        
        detector = LatentDriftDetector(mock_stats)
        
        assert detector.threshold == expected_threshold

    def test_threshold_positive(self):
        """Test that threshold is always positive."""
        mock_stats = {
            'latent_mean': np.zeros(self.n_dims, dtype=np.float32),
            'latent_cov': np.eye(self.n_dims, dtype=np.float32),
            'threshold': 15.0
        }
        
        detector = LatentDriftDetector(mock_stats)
        
        assert detector.threshold > 0
