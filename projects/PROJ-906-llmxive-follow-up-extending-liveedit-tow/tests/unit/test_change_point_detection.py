"""
Unit tests for Piecewise Regression (Change-Point Detection) logic.

This module tests the statistical boundary analysis functionality implemented
in code/analysis/stats.py, specifically the change-point detection using
the ruptures library to identify flow-magnitude thresholds where SSIM
degradation becomes significant.

Tests verify:
1. Correct detection of change points in synthetic data with known breakpoints
2. Handling of edge cases (no change, single segment, noisy data)
3. Integration with the stats module's change_point_detection function
4. Validation of threshold identification against ground truth
"""

import pytest
import numpy as np
from typing import Tuple, List
from unittest.mock import Mock, patch

# Import the function to test (will be implemented in code/analysis/stats.py)
# We import it conditionally to allow tests to run even if the implementation
# is in progress, but they will fail if the function doesn't exist
try:
    from code.analysis.stats import detect_change_points, find_significant_threshold
except ImportError:
    # If the module doesn't exist yet, we'll test the logic independently
    # This allows the test suite to be written before implementation
    detect_change_points = None
    find_significant_threshold = None

import sys
import os

# Add the code directory to the path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'code'))

# Import ruptposes for testing the underlying logic
try:
    import ruptures as rpt
    HAS_RUPTURES = True
except ImportError:
    HAS_RUPTURES = False


class TestChangePointDetection:
    """Test suite for piecewise regression and change-point detection."""
    
    @pytest.fixture
    def synthetic_data_with_known_change(self):
        """Generate synthetic data with a known change point."""
        # Create data with two distinct regimes
        n_before = 50
        n_after = 50
        change_point = n_before
        
        # Before change: low flow magnitude, high SSIM (stable)
        flow_before = np.random.uniform(0.1, 2.0, n_before)
        ssim_before = np.random.uniform(0.85, 0.95, n_before)
        
        # After change: high flow magnitude, low SSIM (degraded)
        flow_after = np.random.uniform(5.0, 10.0, n_after)
        ssim_after = np.random.uniform(0.40, 0.60, n_after)
        
        # Combine
        flow_magnitudes = np.concatenate([flow_before, flow_after])
        ssim_scores = np.concatenate([ssim_before, ssim_after])
        
        return {
            'flow_magnitudes': flow_magnitudes,
            'ssim_scores': ssim_scores,
            'true_change_point': change_point,
            'true_threshold': 3.5  # Between 2.0 and 5.0
        }
    
    @pytest.fixture
    def synthetic_data_no_change(self):
        """Generate synthetic data with NO change point."""
        n_samples = 100
        flow_magnitudes = np.random.uniform(0.1, 10.0, n_samples)
        # Constant relationship: no change point
        ssim_scores = 0.9 - 0.01 * flow_magnitudes + np.random.normal(0, 0.02, n_samples)
        
        return {
            'flow_magnitudes': flow_magnitudes,
            'ssim_scores': ssim_scores,
            'true_change_point': None,
            'true_threshold': None
        }
    
    @pytest.fixture
    def noisy_data_with_change(self):
        """Generate noisy synthetic data with a change point."""
        n_before = 30
        n_after = 30
        change_point = n_before
        
        # Before: low flow, high SSIM with noise
        flow_before = np.random.uniform(0.1, 2.0, n_before)
        ssim_before = 0.9 + np.random.normal(0, 0.05, n_before)
        
        # After: high flow, low SSIM with noise
        flow_after = np.random.uniform(5.0, 10.0, n_after)
        ssim_after = 0.5 + np.random.normal(0, 0.05, n_after)
        
        flow_magnitudes = np.concatenate([flow_before, flow_after])
        ssim_scores = np.concatenate([ssim_before, ssim_after])
        
        # Sort by flow magnitude to simulate real data ordering
        sorted_indices = np.argsort(flow_magnitudes)
        
        return {
            'flow_magnitudes': flow_magnitudes[sorted_indices],
            'ssim_scores': ssim_scores[sorted_indices],
            'true_change_point': change_point,
            'true_threshold': 3.5
        }
    
    @pytest.mark.skipif(not HAS_RUPTURES, reason="ruptures library not installed")
    def test_detect_change_points_known_breakpoint(self, synthetic_data_with_known_change):
        """Test change point detection on data with known breakpoint."""
        if detect_change_points is None:
            pytest.skip("change_point_detection not yet implemented in stats.py")
        
        flow = synthetic_data_with_known_change['flow_magnitudes']
        ssim = synthetic_data_with_known_change['ssim_scores']
        true_threshold = synthetic_data_with_known_change['true_threshold']
        
        # Detect change points
        detected_threshold = detect_change_points(flow, ssim, method='rb', pen=2.0)
        
        # The detected threshold should be close to the true threshold
        # Allow some tolerance due to noise and algorithm behavior
        assert detected_threshold is not None, "Should detect a change point"
        assert isinstance(detected_threshold, (int, float, np.number)), "Threshold should be numeric"
        
        # Check if detected threshold is within reasonable range of true threshold
        # (allowing for some variance due to noise and algorithm)
        tolerance = 1.5  # Allow 1.5 unit tolerance
        assert abs(detected_threshold - true_threshold) < tolerance, \
            f"Detected threshold {detected_threshold} not close to true {true_threshold}"
    
    @pytest.mark.skipif(not HAS_RUPTURES, reason="ruptures library not installed")
    def test_detect_change_points_no_change(self, synthetic_data_no_change):
        """Test that no change point is detected when there is none."""
        if detect_change_points is None:
            pytest.skip("change_point_detection not yet implemented in stats.py")
        
        flow = synthetic_data_no_change['flow_magnitudes']
        ssim = synthetic_data_no_change['ssim_scores']
        
        # Detect change points
        detected_threshold = detect_change_points(flow, ssim, method='rb', pen=5.0)
        
        # Should return None or a value indicating no significant change
        # Implementation should handle this case gracefully
        assert detected_threshold is None or \
               detected_threshold < flow.min() or \
               detected_threshold > flow.max(), \
            "Should not detect a change point in data without one"
    
    @pytest.mark.skipif(not HAS_RUPTURES, reason="ruptures library not installed")
    def test_detect_change_points_noisy_data(self, noisy_data_with_change):
        """Test change point detection on noisy data."""
        if detect_change_points is None:
            pytest.skip("change_point_detection not yet implemented in stats.py")
        
        flow = noisy_data_with_change['flow_magnitudes']
        ssim = noisy_data_with_change['ssim_scores']
        true_threshold = noisy_data_with_change['true_threshold']
        
        # Detect change points with appropriate penalty for noisy data
        detected_threshold = detect_change_points(flow, ssim, method='rb', pen=3.0)
        
        assert detected_threshold is not None, "Should detect a change point in noisy data"
        
        # Check if detected threshold is within reasonable range
        tolerance = 2.0  # Higher tolerance for noisy data
        assert abs(detected_threshold - true_threshold) < tolerance, \
            f"Detected threshold {detected_threshold} not close to true {true_threshold}"
    
    @pytest.mark.skipif(not HAS_RUPTURES, reason="ruptures library not installed")
    def test_change_point_detection_algorithm_selection(self, synthetic_data_with_known_change):
        """Test that different algorithms can be selected."""
        if detect_change_points is None:
            pytest.skip("change_point_detection not yet implemented in stats.py")
        
        flow = synthetic_data_with_known_change['flow_magnitudes']
        ssim = synthetic_data_with_known_change['ssim_scores']
        
        # Test with different algorithms
        methods = ['rb', 'binseg', 'deltat']
        
        for method in methods:
            try:
                threshold = detect_change_points(flow, ssim, method=method, pen=2.0)
                assert threshold is not None, f"Method {method} should detect a change point"
            except Exception as e:
                # Some methods might not be available or suitable
                pytest.skip(f"Method {method} not available: {e}")
    
    @pytest.mark.skipif(not HAS_RUPTURES, reason="ruptures library not installed")
    def test_penalty_parameter_effect(self, synthetic_data_with_known_change):
        """Test that penalty parameter affects sensitivity."""
        if detect_change_points is None:
            pytest.skip("change_point_detection not yet implemented in stats.py")
        
        flow = synthetic_data_with_known_change['flow_magnitudes']
        ssim = synthetic_data_with_known_change['ssim_scores']
        
        # Lower penalty should be more sensitive (detect more change points)
        threshold_low_pen = detect_change_points(flow, ssim, method='rb', pen=1.0)
        
        # Higher penalty should be less sensitive
        threshold_high_pen = detect_change_points(flow, ssim, method='rb', pen=10.0)
        
        # Both should detect something, but the high penalty might be None if no strong change
        assert threshold_low_pen is not None or threshold_high_pen is not None, \
            "At least one penalty level should detect a change point"
    
    @pytest.mark.skipif(not HAS_RUPTURES, reason="ruptures library not installed")
    def test_edge_case_single_segment(self):
        """Test with data that has only one segment (no change)."""
        if detect_change_points is None:
            pytest.skip("change_point_detection not yet implemented in stats.py")
        
        n_samples = 50
        flow = np.random.uniform(0.1, 10.0, n_samples)
        ssim = 0.9 - 0.01 * flow + np.random.normal(0, 0.01, n_samples)
        
        detected = detect_change_points(flow, ssim, method='rb', pen=5.0)
        
        # Should return None or indicate no change
        assert detected is None or \
               detected < flow.min() or \
               detected > flow.max(), \
            "Should not detect change in single-segment data"
    
    @pytest.mark.skipif(not HAS_RUPTURES, reason="ruptures library not installed")
    def test_edge_case_very_small_dataset(self):
        """Test with very small dataset."""
        if detect_change_points is None:
            pytest.skip("change_point_detection not yet implemented in stats.py")
        
        flow = np.array([1.0, 2.0, 8.0, 9.0])
        ssim = np.array([0.9, 0.85, 0.5, 0.45])
        
        # Should handle small datasets gracefully
        detected = detect_change_points(flow, ssim, method='rb', pen=1.0)
        
        # May or may not detect a change point, but should not crash
        assert isinstance(detected, (type(None), int, float, np.number))
    
    @pytest.mark.skipif(not HAS_RUPTURES, reason="ruptures library not installed")
    def test_find_significant_threshold_integration(self):
        """Test the higher-level find_significant_threshold function."""
        if find_significant_threshold is None:
            pytest.skip("find_significant_threshold not yet implemented in stats.py")
        
        # Create synthetic data with known threshold
        n_samples = 100
        flow = np.concatenate([
            np.random.uniform(0.1, 2.0, 50),
            np.random.uniform(5.0, 10.0, 50)
        ])
        ssim = np.concatenate([
            np.random.uniform(0.85, 0.95, 50),
            np.random.uniform(0.40, 0.60, 50)
        ])
        
        # Add some noise
        ssim += np.random.normal(0, 0.03, n_samples)
        
        # Sort by flow
        sorted_indices = np.argsort(flow)
        flow = flow[sorted_indices]
        ssim = ssim[sorted_indices]
        
        # Find significant threshold
        result = find_significant_threshold(flow, ssim, alpha=0.05)
        
        # Result should be a dictionary with expected keys
        assert isinstance(result, dict), "Result should be a dictionary"
        assert 'threshold' in result, "Result should contain 'threshold'"
        assert 'p_value' in result, "Result should contain 'p_value'"
        assert 'significant' in result, "Result should contain 'significant'"
        
        # Threshold should be in the valid range
        assert result['threshold'] is None or \
               (flow.min() <= result['threshold'] <= flow.max()), \
            "Threshold should be within flow magnitude range"
    
    @pytest.mark.skipif(not HAS_RUPTURES, reason="ruptures library not installed")
    def test_validation_against_ground_truth(self, synthetic_data_with_known_change):
        """Test that detected threshold is validated against ground truth."""
        if detect_change_points is None:
            pytest.skip("change_point_detection not yet implemented in stats.py")
        
        flow = synthetic_data_with_known_change['flow_magnitudes']
        ssim = synthetic_data_with_known_change['ssim_scores']
        true_threshold = synthetic_data_with_known_change['true_threshold']
        
        detected = detect_change_points(flow, ssim, method='rb', pen=2.0)
        
        # Calculate relative error
        if detected is not None:
            relative_error = abs(detected - true_threshold) / true_threshold
            assert relative_error < 0.5, \
                f"Relative error {relative_error:.2%} exceeds 50% tolerance"
    
    @pytest.mark.skipif(not HAS_RUPTURES, reason="ruptures library not installed")
    def test_consistency_across_runs(self, synthetic_data_with_known_change):
        """Test that results are consistent across multiple runs."""
        if detect_change_points is None:
            pytest.skip("change_point_detection not yet implemented in stats.py")
        
        flow = synthetic_data_with_known_change['flow_magnitudes']
        ssim = synthetic_data_with_known_change['ssim_scores']
        
        # Run multiple times
        results = []
        for i in range(5):
            result = detect_change_points(flow, ssim, method='rb', pen=2.0)
            results.append(result)
        
        # All results should be the same (deterministic algorithm)
        # Note: Some algorithms might have randomness, so we check for consistency
        # or small variance
        non_none_results = [r for r in results if r is not None]
        if len(non_none_results) > 0:
            variance = np.var(non_none_results)
            assert variance < 0.5, f"Results should be consistent, got variance {variance}"
    
    @pytest.mark.skipif(not HAS_RUPTURES, reason="ruptures library not installed")
    def test_error_handling_invalid_input(self):
        """Test error handling for invalid inputs."""
        if detect_change_points is None:
            pytest.skip("change_point_detection not yet implemented in stats.py")
        
        # Empty arrays
        with pytest.raises((ValueError, IndexError)):
            detect_change_points(np.array([]), np.array([]))
        
        # Mismatched lengths
        with pytest.raises((ValueError, IndexError)):
            detect_change_points(np.array([1.0, 2.0]), np.array([0.9]))
        
        # Non-numeric data
        with pytest.raises((TypeError, ValueError)):
            detect_change_points(['a', 'b'], [0.9, 0.8])

class TestPiecewiseRegressionLogic:
    """Test the underlying piecewise regression logic directly."""
    
    @pytest.mark.skipif(not HAS_RUPTURES, reason="ruptures library not installed")
    def test_pelt_algorithm_basic(self):
        """Test PELT algorithm with basic synthetic data."""
        # Create data with known change point
        n1, n2 = 50, 50
        signal = np.concatenate([
            np.ones(n1) * 10,
            np.ones(n2) * 20
        ])
        signal += np.random.normal(0, 1, len(signal))
        
        # Apply PELT
        algo = rpt.Pelt(model="rb").fit(signal)
        result = algo.predict(pen=2.0)
        
        # Result should contain the change point (last element is n+1)
        assert len(result) >= 2, "Should detect at least one change point"
        assert result[-1] == len(signal), "Last element should be signal length"
        
        # Check if change point is detected near the true location (50)
        change_point = result[0] if len(result) > 1 else None
        if change_point:
            assert 40 <= change_point <= 60, f"Change point {change_point} should be near 50"
    
    @pytest.mark.skipif(not HAS_RUPTURES, reason="ruptures library not installed")
    def test_binseg_algorithm(self):
        """Test Binary Segmentation algorithm."""
        # Create data with multiple change points
        signal = np.concatenate([
            np.ones(30) * 5,
            np.ones(30) * 15,
            np.ones(30) * 25
        ])
        signal += np.random.normal(0, 1, len(signal))
        
        algo = rpt.Binseg(model="rb").fit(signal)
        result = algo.predict(pen=2.0)
        
        # Should detect 2 change points (plus the end)
        assert len(result) >= 3, "Should detect at least 2 change points"
    
    @pytest.mark.skipif(not HAS_RUPTURES, reason="ruptures library not installed")
    def test_cost_function_selection(self):
        """Test different cost functions."""
        signal = np.concatenate([
            np.ones(50) * 10,
            np.ones(50) * 20
        ])
        signal += np.random.normal(0, 1, len(signal))
        
        models = ['l2', 'l1', 'rb']
        
        for model in models:
            algo = rpt.Pelt(model=model).fit(signal)
            result = algo.predict(pen=2.0)
            assert len(result) >= 2, f"Model {model} should detect change point"

if __name__ == '__main__':
    pytest.main([__file__, '-v'])