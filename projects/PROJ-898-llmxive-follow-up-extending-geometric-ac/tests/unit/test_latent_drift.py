import pytest
import numpy as np
import torch
import json
import os
import sys
import logging

# Ensure code/ is in path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from code.latent_drift import LatentDriftDetector, load_reference_stats, compute_reference_stats_from_latents
from code.utils import set_deterministic_seed
from code.config import load_config

@pytest.fixture
def reference_stats():
    """Create mock reference statistics for testing."""
    set_deterministic_seed(42)
    n_samples = 1000
    n_dims = 64  # Typical latent dimension size
    
    # Generate mock reference data
    mean = np.random.randn(n_dims).astype(np.float32)
    cov = np.eye(n_dims) * 0.1  # Small variance around mean
    
    return {
        'mean': mean.tolist(),
        'covariance': cov.tolist(),
        'n_samples': n_samples
    }

@pytest.fixture
def drift_detector(reference_stats, tmp_path):
    """Create a LatentDriftDetector with reference stats."""
    # Save reference stats to temp file
    stats_path = tmp_path / "reference_stats.json"
    with open(stats_path, 'w') as f:
        json.dump(reference_stats, f)
    
    detector = LatentDriftDetector(str(stats_path))
    return detector

@pytest.fixture
def sample_latents():
    """Generate sample latent vectors for testing."""
    set_deterministic_seed(123)
    n_samples = 100
    n_dims = 64
    
    # Generate latents close to reference (in-distribution)
    in_dist = np.random.randn(n_samples, n_dims).astype(np.float32) * 0.1
    
    # Generate latents far from reference (out-of-distribution)
    out_dist = np.random.randn(n_samples, n_dims).astype(np.float32) * 5.0 + 10.0
    
    return {
        'in_distribution': in_dist,
        'out_distribution': out_dist
    }

class TestLatentDriftDetector:
    """Unit tests for LatentDriftDetector functionality."""

    def test_initialization(self, drift_detector):
        """Test detector initialization with valid stats file."""
        assert drift_detector.reference_mean is not None
        assert drift_detector.reference_cov is not None
        assert drift_detector.threshold is not None
        assert drift_detector.n_dims == 64

    def test_initialization_missing_file(self, tmp_path):
        """Test detector initialization with missing stats file."""
        missing_path = tmp_path / "nonexistent.json"
        
        with pytest.raises(FileNotFoundError):
            LatentDriftDetector(str(missing_path))

    def test_initialization_invalid_json(self, tmp_path):
        """Test detector initialization with invalid JSON."""
        invalid_path = tmp_path / "invalid.json"
        with open(invalid_path, 'w') as f:
            f.write("not valid json")
        
        with pytest.raises(json.JSONDecodeError):
            LatentDriftDetector(str(invalid_path))

    def test_initialization_missing_keys(self, tmp_path):
        """Test detector initialization with missing required keys."""
        invalid_path = tmp_path / "missing_keys.json"
        with open(invalid_path, 'w') as f:
            json.dump({'mean': [1, 2, 3]}, f)  # Missing covariance
        
        with pytest.raises(KeyError):
            LatentDriftDetector(str(invalid_path))

    def test_mahalanobis_distance_computation(self, drift_detector, sample_latents):
        """Test Mahalanobis distance calculation."""
        # In-distribution should have lower distances
        in_dist_distances = drift_detector.compute_distances(sample_latents['in_distribution'])
        
        # Out-distribution should have higher distances
        out_dist_distances = drift_detector.compute_distances(sample_latents['out_distribution'])
        
        assert len(in_dist_distances) == len(sample_latents['in_distribution'])
        assert len(out_dist_distances) == len(sample_latents['out_distribution'])
        
        # In-distribution distances should be generally smaller
        assert np.mean(in_dist_distances) < np.mean(out_dist_distances)

    def test_drift_detection(self, drift_detector, sample_latents):
        """Test drift detection logic."""
        # Test in-distribution data
        in_dist_results = drift_detector.detect_drift(sample_latents['in_distribution'])
        
        assert len(in_dist_results) == len(sample_latents['in_distribution'])
        in_drift_count = sum(1 for r in in_dist_results if r['drift_detected'])
        
        # Most in-distribution samples should not trigger drift
        assert in_drift_count < len(in_dist_results) * 0.1  # Less than 10%

        # Test out-distribution data
        out_dist_results = drift_detector.detect_drift(sample_latents['out_distribution'])
        
        out_drift_count = sum(1 for r in out_dist_results if r['drift_detected'])
        
        # Most out-distribution samples should trigger drift
        assert out_drift_count > len(out_dist_results) * 0.8  # More than 80%

    def test_threshold_validation(self, drift_detector):
        """Test that threshold is a valid positive value."""
        assert drift_detector.threshold > 0
        assert isinstance(drift_detector.threshold, float)

    def test_covariance_inversion(self, drift_detector):
        """Test that covariance matrix inversion works correctly."""
        # The inverse should exist and be symmetric
        cov_inv = drift_detector.covariance_inverse
        
        assert cov_inv is not None
        assert cov_inv.shape == (drift_detector.n_dims, drift_detector.n_dims)
        
        # Check symmetry
        np.testing.assert_array_almost_equal(cov_inv, cov_inv.T)

    def test_single_sample_detection(self, drift_detector):
        """Test drift detection on a single sample."""
        single_sample = np.random.randn(1, 64).astype(np.float32)
        
        results = drift_detector.detect_drift(single_sample)
        
        assert len(results) == 1
        assert 'distance' in results[0]
        assert 'drift_detected' in results[0]
        assert 'threshold' in results[0]

    def test_batch_detection(self, drift_detector, sample_latents):
        """Test batch drift detection performance."""
        batch_size = 50
        
        # Test with various batch sizes
        for size in [1, 10, batch_size, 100]:
            samples = sample_latents['in_distribution'][:size]
            results = drift_detector.detect_drift(samples)
            
            assert len(results) == size
            assert all('distance' in r for r in results)
            assert all('drift_detected' in r for r in results)

class TestReferenceStatsLoading:
    """Unit tests for reference stats loading functions."""

    def test_load_reference_stats_valid(self, reference_stats, tmp_path):
        """Test loading valid reference statistics."""
        stats_path = tmp_path / "valid_stats.json"
        with open(stats_path, 'w') as f:
            json.dump(reference_stats, f)
        
        loaded = load_reference_stats(str(stats_path))
        
        assert 'mean' in loaded
        assert 'covariance' in loaded
        assert 'n_samples' in loaded
        assert len(loaded['mean']) == len(reference_stats['mean'])

    def test_load_reference_stats_missing_file(self, tmp_path):
        """Test loading from missing file."""
        missing_path = tmp_path / "missing.json"
        
        with pytest.raises(FileNotFoundError):
            load_reference_stats(str(missing_path))

    def test_load_reference_stats_invalid_format(self, tmp_path):
        """Test loading invalid format."""
        invalid_path = tmp_path / "invalid.json"
        with open(invalid_path, 'w') as f:
            json.dump({'wrong': 'format'}, f)
        
        with pytest.raises((KeyError, ValueError)):
            load_reference_stats(str(invalid_path))

    def test_compute_reference_stats_from_latents(self, sample_latents):
        """Test computing stats from latent vectors."""
        latents = sample_latents['in_distribution']
        
        stats = compute_reference_stats_from_latents(latents)
        
        assert 'mean' in stats
        assert 'covariance' in stats
        assert 'n_samples' in stats
        
        assert len(stats['mean']) == latents.shape[1]
        assert stats['n_samples'] == latents.shape[0]
        
        # Check covariance is symmetric
        cov = np.array(stats['covariance'])
        np.testing.assert_array_almost_equal(cov, cov.T)

    def test_compute_reference_stats_empty(self):
        """Test computing stats from empty array."""
        empty_latents = np.array([]).reshape(0, 64)
        
        with pytest.raises(ValueError):
            compute_reference_stats_from_latents(empty_latents)

class TestDriftThresholdValidation:
    """Tests for drift threshold validation logic."""

    def test_threshold_calculation(self, drift_detector):
        """Test that threshold is calculated correctly."""
        # Threshold should be based on chi-squared distribution
        # For 99th percentile with 64 degrees of freedom
        from scipy.stats import chi2
        
        expected_threshold = chi2.ppf(0.99, drift_detector.n_dims)
        
        # Allow small numerical differences
        assert abs(drift_detector.threshold - expected_threshold) < 0.01

    def test_threshold_sensitivity(self, drift_detector, sample_latents):
        """Test threshold sensitivity to different confidence levels."""
        # Create detector with different thresholds
        base_threshold = drift_detector.threshold
        
        # In-distribution should mostly pass
        in_results = drift_detector.detect_drift(sample_latents['in_distribution'])
        in_pass_rate = sum(1 for r in in_results if not r['drift_detected']) / len(in_results)
        
        # Out-distribution should mostly fail
        out_results = drift_detector.detect_drift(sample_latents['out_distribution'])
        out_fail_rate = sum(1 for r in out_results if r['drift_detected']) / len(out_results)
        
        assert in_pass_rate > 0.9  # 90% of in-distribution should pass
        assert out_fail_rate > 0.8  # 80% of out-distribution should fail

class TestLatentDriftIntegration:
    """Integration tests for latent drift detection in pipeline."""

    def test_drift_logging(self, drift_detector, sample_latents, tmp_path):
        """Test that drift results are properly formatted for logging."""
        results = drift_detector.detect_drift(sample_latents['in_distribution'])
        
        # Check result structure matches expected log format
        for result in results:
            assert 'distance' in result
            assert 'drift_detected' in result
            assert 'threshold' in result
            assert 'sample_index' in result
            
            assert isinstance(result['distance'], float)
            assert isinstance(result['drift_detected'], bool)
            assert isinstance(result['threshold'], float)
            assert isinstance(result['sample_index'], int)

    def test_drift_with_config(self, sample_latents, tmp_path):
        """Test drift detection with project configuration."""
        config = load_config()
        
        # Create reference stats file
        reference_stats = {
            'mean': np.random.randn(64).tolist(),
            'covariance': np.eye(64).tolist(),
            'n_samples': 1000
        }
        
        stats_path = tmp_path / "config_stats.json"
        with open(stats_path, 'w') as f:
            json.dump(reference_stats, f)
        
        detector = LatentDriftDetector(str(stats_path))
        results = detector.detect_drift(sample_latents['in_distribution'][:10])
        
        assert len(results) == 10
        assert all('drift_detected' in r for r in results)

    def test_drift_alert_format(self, drift_detector, sample_latents):
        """Test drift alert data structure for pipeline integration."""
        results = drift_detector.detect_drift(sample_latents['out_distribution'])
        
        # Filter for drift detections
        drift_alerts = [r for r in results if r['drift_detected']]
        
        if drift_alerts:
            alert = drift_alerts[0]
            
            # Check alert structure
            assert 'distance' in alert
            assert 'threshold' in alert
            assert 'sample_index' in alert
            assert 'drift_detected' in alert
            
            # Alert should indicate need for review
            assert alert['drift_detected'] is True
            assert alert['distance'] > alert['threshold']

    def test_drift_with_different_dimensions(self, tmp_path):
        """Test drift detection with different latent dimensions."""
        for dim in [32, 64, 128, 256]:
            # Create reference stats for different dimensions
            reference_stats = {
                'mean': np.random.randn(dim).tolist(),
                'covariance': np.eye(dim).tolist(),
                'n_samples': 500
            }
            
            stats_path = tmp_path / f"stats_{dim}.json"
            with open(stats_path, 'w') as f:
                json.dump(reference_stats, f)
            
            detector = LatentDriftDetector(str(stats_path))
            
            assert detector.n_dims == dim
            
            # Test with matching dimension latents
            test_latents = np.random.randn(10, dim).astype(np.float32)
            results = detector.detect_drift(test_latents)
            
            assert len(results) == 10
            assert all('distance' in r for r in results)
            
            # Different dimensions should fail
            wrong_dim_latents = np.random.randn(10, dim + 10).astype(np.float32)
            with pytest.raises(ValueError):
                detector.detect_drift(wrong_dim_latents)
