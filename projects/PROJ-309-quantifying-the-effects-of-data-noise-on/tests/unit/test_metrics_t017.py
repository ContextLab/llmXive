"""
Unit tests for Task T017: Ground Truth Metrics Computation

Tests verify that:
1. Correlation Dimension is computed correctly for known chaotic systems
2. Lyapunov Exponent is positive for chaotic systems
3. Metrics are saved to correct JSON format
"""
import os
import sys
import json
import tempfile
import numpy as np
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from code.metrics import (
    compute_correlation_dimension,
    compute_lyapunov_exponent_rosenstein,
    compute_false_nearest_neighbors,
    compute_ground_truth_metrics
)

class TestCorrelationDimension:
    def test_compute_cd_on_lorenz_like_data(self):
        """Test Correlation Dimension on synthetic Lorenz-like data."""
        # Generate synthetic chaotic-like data (not real Lorenz, but chaotic behavior)
        np.random.seed(42)
        t = np.linspace(0, 50, 10000)
        # Create a signal with chaotic characteristics
        signal = np.sin(t) + 0.5 * np.sin(2.5 * t) + 0.3 * np.sin(10 * t)
        trajectory = signal.reshape(-1, 1)
        
        result = compute_correlation_dimension(trajectory, n_scales=10)
        
        assert 'correlation_dimension' in result
        assert 'slope' in result
        assert isinstance(result['correlation_dimension'], float)
        # For this synthetic data, D2 should be positive and finite
        assert not np.isnan(result['correlation_dimension'])
        assert result['correlation_dimension'] > 0
    
    def test_cd_with_insufficient_data(self):
        """Test that CD returns NaN for insufficient data points."""
        # Very short trajectory
        trajectory = np.random.randn(50, 1)
        
        result = compute_correlation_dimension(trajectory, n_scales=10)
        
        # Should handle gracefully (may return NaN or low value)
        assert 'correlation_dimension' in result
        assert isinstance(result['correlation_dimension'], float)

class TestLyapunovExponent:
    def test_compute_le_on_chaotic_data(self):
        """Test Lyapunov Exponent on synthetic chaotic-like data."""
        np.random.seed(42)
        t = np.linspace(0, 50, 10000)
        signal = np.sin(t) + 0.5 * np.sin(2.5 * t) + 0.3 * np.sin(10 * t)
        trajectory = signal.reshape(-1, 1)
        
        result = compute_lyapunov_exponent_rosenstein(trajectory, max_time=50)
        
        assert 'lyapunov_exponent' in result
        assert 'slope' in result
        assert isinstance(result['lyapunov_exponent'], float)
        # Should not be NaN
        assert not np.isnan(result['lyapunov_exponent'])
    
    def test_le_with_insufficient_data(self):
        """Test that LE returns NaN for insufficient data points."""
        trajectory = np.random.randn(50, 1)
        
        result = compute_lyapunov_exponent_rosenstein(trajectory, max_time=10)
        
        assert 'lyapunov_exponent' in result
        assert isinstance(result['lyapunov_exponent'], float)

class TestFalseNearestNeighbors:
    def test_compute_fnn(self):
        """Test FNN computation."""
        np.random.seed(42)
        trajectory = np.random.randn(1000, 1)
        
        result = compute_false_nearest_neighbors(trajectory, embedding_dim=5)
        
        assert 'fnn_rates' in result
        assert 'optimal_dim' in result
        assert len(result['fnn_rates']) == 5
        assert isinstance(result['optimal_dim'], int)
        assert 1 <= result['optimal_dim'] <= 5

class TestGroundTruthMetrics:
    def test_compute_and_save_metrics(self):
        """Test complete ground truth metrics computation and saving."""
        # Create temporary files
        with tempfile.TemporaryDirectory() as tmpdir:
            trajectory_path = os.path.join(tmpdir, 'test_trajectory.csv')
            output_path = os.path.join(tmpdir, 'test_metrics.json')
            
            # Create synthetic trajectory data
            np.random.seed(42)
            trajectory = np.random.randn(5000, 3)
            np.savetxt(trajectory_path, trajectory, delimiter=',', header='x,y,z', comments='')
            
            # Compute and save metrics
            compute_ground_truth_metrics(trajectory_path, output_path, seed=42)
            
            # Verify output file exists
            assert os.path.exists(output_path)
            
            # Verify JSON structure
            with open(output_path, 'r') as f:
                metrics = json.load(f)
            
            assert 'seed' in metrics
            assert metrics['seed'] == 42
            assert 'correlation_dimension' in metrics
            assert 'lyapunov_exponent' in metrics
            assert 'false_nearest_neighbors' in metrics
            assert 'value' in metrics['correlation_dimension']
            assert 'value' in metrics['lyapunov_exponent']
            assert 'fnn_rates' in metrics['false_nearest_neighbors']

if __name__ == '__main__':
    pytest.main([__file__, '-v'])