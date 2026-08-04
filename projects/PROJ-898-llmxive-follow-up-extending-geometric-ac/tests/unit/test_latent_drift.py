"""
Unit tests for latent drift detection functionality.
Tests the LatentDriftDetector and related utilities from code/latent_drift.py
"""
import os
import sys
import unittest
import json
import tempfile
import numpy as np
from unittest.mock import patch, MagicMock

# Add code directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'code'))

from latent_drift import LatentDriftDetector, load_reference_stats, compute_reference_stats_from_latents


class TestLatentDriftDetector(unittest.TestCase):
    """Tests for the LatentDriftDetector class."""

    def setUp(self):
        """Set up test fixtures."""
        # Create reference statistics
        self.reference_mean = np.array([0.0, 0.0, 0.0])
        self.reference_cov = np.array([
            [1.0, 0.1, 0.1],
            [0.1, 1.0, 0.1],
            [0.1, 0.1, 1.0]
        ])
        
        self.detector = LatentDriftDetector(
            reference_mean=self.reference_mean,
            reference_cov=self.reference_cov,
            threshold=5.99  # ~95th percentile for chi-squared with 3 dof
        )

    def test_init_with_valid_stats(self):
        """Test initialization with valid reference statistics."""
        self.assertIsInstance(self.detector, LatentDriftDetector)
        np.testing.assert_array_almost_equal(self.detector.reference_mean, self.reference_mean)
        np.testing.assert_array_almost_equal(self.detector.reference_cov, self.reference_cov)

    def test_init_with_invalid_covariance(self):
        """Test that invalid covariance matrix raises error."""
        # Non-positive definite covariance
        invalid_cov = np.array([
            [1.0, 2.0, 2.0],
            [2.0, 1.0, 2.0],
            [2.0, 2.0, 1.0]
        ])
        
        with self.assertRaises(ValueError):
            LatentDriftDetector(
                reference_mean=self.reference_mean,
                reference_cov=invalid_cov,
                threshold=5.99
            )

    def test_compute_mahalanobis_distance(self):
        """Test Mahalanobis distance calculation."""
        # Point at mean should have distance 0
        point_at_mean = np.array([0.0, 0.0, 0.0])
        distance = self.detector.compute_mahalanobis_distance(point_at_mean)
        self.assertAlmostEqual(distance, 0.0, places=5)
        
        # Point far from mean should have large distance
        point_far = np.array([3.0, 3.0, 3.0])
        distance_far = self.detector.compute_mahalanobis_distance(point_far)
        self.assertGreater(distance_far, 5.99)  # Should exceed threshold

    def test_detect_drift(self):
        """Test drift detection logic."""
        # In-distribution point
        point_in_dist = np.array([0.5, 0.5, 0.5])
        is_drift, distance = self.detector.detect_drift(point_in_dist)
        self.assertFalse(is_drift)
        self.assertLess(distance, self.detector.threshold)
        
        # Out-of-distribution point
        point_out_dist = np.array([3.0, 3.0, 3.0])
        is_drift, distance = self.detector.detect_drift(point_out_dist)
        self.assertTrue(is_drift)
        self.assertGreater(distance, self.detector.threshold)

    def test_batch_detection(self):
        """Test batch drift detection."""
        points = np.array([
            [0.0, 0.0, 0.0],  # In distribution
            [0.5, 0.5, 0.5],  # In distribution
            [3.0, 3.0, 3.0],  # Out of distribution
            [0.1, 0.1, 0.1]   # In distribution
        ])
        
        results = self.detector.detect_batch_drift(points)
        
        self.assertEqual(len(results), len(points))
        self.assertFalse(results[0]['is_drift'])
        self.assertFalse(results[1]['is_drift'])
        self.assertTrue(results[2]['is_drift'])
        self.assertFalse(results[3]['is_drift'])

    def test_update_threshold(self):
        """Test threshold update functionality."""
        new_threshold = 10.0
        self.detector.update_threshold(new_threshold)
        self.assertEqual(self.detector.threshold, new_threshold)


class TestLoadReferenceStats(unittest.TestCase):
    """Tests for loading reference statistics from file."""

    def test_load_valid_stats(self):
        """Test loading valid reference statistics."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            stats = {
                'mean': [0.0, 0.0, 0.0],
                'covariance': [[1.0, 0.1, 0.1], [0.1, 1.0, 0.1], [0.1, 0.1, 1.0]],
                'threshold': 5.99
            }
            json.dump(stats, f)
            f.flush()
            
            loaded_stats = load_reference_stats(f.name)
            
            self.assertIn('mean', loaded_stats)
            self.assertIn('covariance', loaded_stats)
            self.assertIn('threshold', loaded_stats)
            
            np.testing.assert_array_almost_equal(
                np.array(loaded_stats['mean']),
                np.array([0.0, 0.0, 0.0])
            )

    def test_load_invalid_file(self):
        """Test loading from non-existent file."""
        with self.assertRaises(FileNotFoundError):
            load_reference_stats('/nonexistent/path/stats.json')

    def test_load_invalid_format(self):
        """Test loading invalid JSON format."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write('invalid json content')
            f.flush()
            
            with self.assertRaises(json.JSONDecodeError):
                load_reference_stats(f.name)


class TestComputeReferenceStats(unittest.TestCase):
    """Tests for computing reference statistics from latents."""

    def test_compute_from_latents(self):
        """Test computing statistics from a set of latent vectors."""
        # Generate synthetic latent vectors
        np.random.seed(42)
        latents = np.random.multivariate_normal(
            mean=[0.0, 0.0, 0.0],
            cov=np.eye(3),
            size=1000
        )
        
        stats = compute_reference_stats_from_latents(latents)
        
        self.assertIn('mean', stats)
        self.assertIn('covariance', stats)
        self.assertIn('threshold', stats)
        
        # Mean should be close to zero
        np.testing.assert_array_almost_equal(stats['mean'], [0.0, 0.0, 0.0], decimal=1)
        
        # Covariance should be close to identity
        np.testing.assert_array_almost_equal(stats['covariance'], np.eye(3), decimal=0)

    def test_compute_from_small_sample(self):
        """Test computing statistics from a small sample."""
        np.random.seed(42)
        latents = np.random.multivariate_normal(
            mean=[1.0, 1.0, 1.0],
            cov=np.eye(3),
            size=10
        )
        
        stats = compute_reference_stats_from_latents(latents)
        
        self.assertIn('mean', stats)
        self.assertIn('covariance', stats)
        
        # Mean should be close to [1, 1, 1]
        np.testing.assert_array_almost_equal(stats['mean'], [1.0, 1.0, 1.0], decimal=0)


class TestLatentDriftIntegration(unittest.TestCase):
    """Integration tests for latent drift detection pipeline."""

    def test_full_drift_detection_pipeline(self):
        """Test the full pipeline from stats loading to drift detection."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            stats = {
                'mean': [0.0, 0.0, 0.0],
                'covariance': [[1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]],
                'threshold': 5.99
            }
            json.dump(stats, f)
            f.flush()
            
            # Load stats
            loaded_stats = load_reference_stats(f.name)
            
            # Create detector
            detector = LatentDriftDetector(
                reference_mean=np.array(loaded_stats['mean']),
                reference_cov=np.array(loaded_stats['covariance']),
                threshold=loaded_stats['threshold']
            )
            
            # Test detection
            test_point = np.array([0.5, 0.5, 0.5])
            is_drift, distance = detector.detect_drift(test_point)
            
            self.assertFalse(is_drift)
            self.assertLess(distance, loaded_stats['threshold'])

    def test_drift_alert_generation(self):
        """Test that drift alerts are properly generated."""
        detector = LatentDriftDetector(
            reference_mean=np.array([0.0, 0.0, 0.0]),
            reference_cov=np.eye(3),
            threshold=5.99
        )
        
        # Generate out-of-distribution point
        outlier = np.array([3.0, 3.0, 3.0])
        is_drift, distance = detector.detect_drift(outlier)
        
        self.assertTrue(is_drift)
        self.assertGreater(distance, detector.threshold)


if __name__ == '__main__':
    unittest.main()
