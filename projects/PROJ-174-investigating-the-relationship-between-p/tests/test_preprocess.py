"""
Unit tests for blink interpolation logic in the preprocessing pipeline.

This module tests the blink detection and interpolation functionality
required for User Story 1 (US1). It validates that:
1. Blinks are correctly identified based on pupil diameter thresholds
2. Interpolation correctly fills missing data points
3. Edge cases (all blinks, no blinks, single blink) are handled properly
"""

import pytest
import numpy as np
import pandas as pd
from typing import Tuple, List

# Import the preprocessing module (assuming it will be created in T014)
# For now, we define a mock implementation to test the logic
# In the actual implementation, this would import from code/preprocessing/filter.py

def detect_blinks(
    pupil_diameter: np.ndarray,
    threshold: float = 2.0,
    min_duration: int = 3
) -> np.ndarray:
    """
    Detect blinks based on pupil diameter threshold.
    
    A blink is identified when pupil diameter drops below a threshold
    for at least min_duration consecutive samples.
    
    Args:
        pupil_diameter: Array of pupil diameter measurements
        threshold: Minimum drop in pupil diameter to consider a blink
        min_duration: Minimum number of consecutive samples below threshold
    
    Returns:
        Boolean array where True indicates a blink sample
    """
    # Identify samples below threshold
    below_threshold = pupil_diameter < (np.mean(pupil_diameter) - threshold)
    
    # Find consecutive runs of blinks
    blink_mask = np.zeros_like(below_threshold, dtype=bool)
    run_length = 0
    
    for i in range(len(below_threshold)):
        if below_threshold[i]:
            run_length += 1
            if run_length >= min_duration:
                # Mark this sample and previous min_duration-1 samples as blink
                start_idx = max(0, i - min_duration + 1)
                blink_mask[start_idx:i+1] = True
        else:
            run_length = 0
    
    return blink_mask

def interpolate_blinks(
    pupil_diameter: np.ndarray,
    blink_mask: np.ndarray,
    method: str = 'linear'
) -> np.ndarray:
    """
    Interpolate blink artifacts in pupil diameter data.
    
    Args:
        pupil_diameter: Original pupil diameter array
        blink_mask: Boolean array indicating blink samples
        method: Interpolation method ('linear', 'nearest', 'cubic')
    
    Returns:
        Interpolated pupil diameter array with blink artifacts filled
    """
    if not np.any(blink_mask):
        return pupil_diameter.copy()
    
    # Create a copy to avoid modifying original
    interpolated = pupil_diameter.copy()
    
    # Get indices of blink and non-blink samples
    blink_indices = np.where(blink_mask)[0]
    valid_indices = np.where(~blink_mask)[0]
    valid_values = pupil_diameter[valid_indices]
    
    if len(valid_indices) == 0:
        # All samples are blinks - return mean value
        return np.full_like(interpolated, np.mean(pupil_diameter))
    
    if method == 'linear':
        # Linear interpolation
        interpolated[blink_indices] = np.interp(
            blink_indices, valid_indices, valid_values
        )
    elif method == 'nearest':
        # Nearest neighbor interpolation
        for idx in blink_indices:
            # Find closest valid index
            closest_idx = valid_indices[np.argmin(np.abs(valid_indices - idx))]
            interpolated[idx] = valid_values[np.argmin(np.abs(valid_indices - idx))]
    elif method == 'cubic':
        # Cubic interpolation (requires scipy)
        try:
            from scipy.interpolate import interp1d
            f = interp1d(valid_indices, valid_values, kind='cubic', 
                       fill_value="extrapolate")
            interpolated[blink_indices] = f(blink_indices)
        except ImportError:
            # Fallback to linear if scipy not available
            interpolated[blink_indices] = np.interp(
                blink_indices, valid_indices, valid_values
            )
    
    return interpolated

class TestBlinkDetection:
    """Tests for blink detection logic."""
    
    def test_no_blinks(self):
        """Test detection when there are no blinks."""
        pupil_data = np.array([5.0, 5.1, 4.9, 5.0, 5.2, 4.8, 5.1])
        blink_mask = detect_blinks(pupil_data, threshold=2.0, min_duration=3)
        assert not np.any(blink_mask), "Should not detect blinks in normal data"
    
    def test_single_blink_detection(self):
        """Test detection of a single blink event."""
        pupil_data = np.array([5.0, 5.1, 0.5, 0.4, 0.6, 5.0, 5.1])
        blink_mask = detect_blinks(pupil_data, threshold=2.0, min_duration=3)
        
        expected_blinks = [False, False, True, True, True, False, False]
        assert np.array_equal(blink_mask, expected_blinks), \
            f"Expected {expected_blinks}, got {blink_mask.tolist()}"
    
    def test_multiple_blinks(self):
        """Test detection of multiple blink events."""
        pupil_data = np.array([5.0, 0.3, 0.4, 0.5, 5.0, 5.1, 0.2, 0.3, 0.4, 5.0])
        blink_mask = detect_blinks(pupil_data, threshold=2.0, min_duration=3)
        
        expected_blinks = [False, True, True, True, False, False, True, True, True, False]
        assert np.array_equal(blink_mask, expected_blinks), \
            f"Expected {expected_blinks}, got {blink_mask.tolist()}"
    
    def test_short_blink_not_detected(self):
        """Test that short blinks (< min_duration) are not detected."""
        pupil_data = np.array([5.0, 0.5, 0.6, 5.0, 5.1])
        blink_mask = detect_blinks(pupil_data, threshold=2.0, min_duration=3)
        
        expected_blinks = [False, False, False, False, False]
        assert np.array_equal(blink_mask, expected_blinks), \
            "Short blinks should not be detected"
    
    def test_threshold_sensitivity(self):
        """Test that threshold parameter affects detection."""
        pupil_data = np.array([5.0, 3.0, 3.1, 3.2, 5.0])
        
        # High threshold - no detection
        blink_mask_high = detect_blinks(pupil_data, threshold=2.5, min_duration=3)
        assert not np.any(blink_mask_high), "High threshold should not detect"
        
        # Low threshold - detection
        blink_mask_low = detect_blinks(pupil_data, threshold=1.5, min_duration=3)
        assert np.any(blink_mask_low), "Low threshold should detect"

class TestBlinkInterpolation:
    """Tests for blink interpolation logic."""
    
    def test_no_blinks_no_change(self):
        """Test that data without blinks remains unchanged."""
        pupil_data = np.array([5.0, 5.1, 4.9, 5.0, 5.2])
        blink_mask = np.zeros_like(pupil_data, dtype=bool)
        
        interpolated = interpolate_blinks(pupil_data, blink_mask)
        assert np.array_equal(interpolated, pupil_data), \
            "Data without blinks should remain unchanged"
    
    def test_linear_interpolation(self):
        """Test linear interpolation of blink artifacts."""
        pupil_data = np.array([5.0, 5.1, 0.5, 0.4, 0.6, 5.0, 5.1])
        blink_mask = np.array([False, False, True, True, True, False, False])
        
        interpolated = interpolate_blinks(pupil_data, blink_mask, method='linear')
        
        # Interpolated values should be between 5.1 and 5.0
        assert interpolated[2] > 4.0 and interpolated[2] < 5.2, \
            f"Interpolated value {interpolated[2]} out of expected range"
        assert interpolated[3] > 4.0 and interpolated[3] < 5.2, \
            f"Interpolated value {interpolated[3]} out of expected range"
        assert interpolated[4] > 4.0 and interpolated[4] < 5.2, \
            f"Interpolated value {interpolated[4]} out of expected range"
    
    def test_nearest_interpolation(self):
        """Test nearest neighbor interpolation."""
        pupil_data = np.array([5.0, 5.1, 0.5, 0.4, 0.6, 5.0, 5.1])
        blink_mask = np.array([False, False, True, True, True, False, False])
        
        interpolated = interpolate_blinks(pupil_data, blink_mask, method='nearest')
        
        # Nearest values should be 5.1 or 5.0
        assert interpolated[2] in [5.1, 5.0], \
            f"Nearest interpolation should use 5.1 or 5.0, got {interpolated[2]}"
        assert interpolated[3] in [5.1, 5.0], \
            f"Nearest interpolation should use 5.1 or 5.0, got {interpolated[3]}"
        assert interpolated[4] in [5.1, 5.0], \
            f"Nearest interpolation should use 5.1 or 5.0, got {interpolated[4]}"
    
    def test_all_blinks(self):
        """Test interpolation when all samples are blinks."""
        pupil_data = np.array([0.5, 0.4, 0.6, 0.3, 0.5])
        blink_mask = np.ones_like(pupil_data, dtype=bool)
        
        interpolated = interpolate_blinks(pupil_data, blink_mask)
        
        # Should return mean value
        expected_mean = np.mean(pupil_data)
        assert np.allclose(interpolated, expected_mean), \
            f"All blinks should be replaced with mean {expected_mean}, got {interpolated}"
    
    def test_boundary_blinks(self):
        """Test interpolation of blinks at array boundaries."""
        pupil_data = np.array([0.5, 0.4, 5.0, 5.1, 5.2])
        blink_mask = np.array([True, True, False, False, False])
        
        interpolated = interpolate_blinks(pupil_data, blink_mask, method='linear')
        
        # Boundary values should be interpolated from nearest valid point
        assert interpolated[0] > 4.0 and interpolated[0] < 5.2, \
            f"Boundary interpolation failed: {interpolated[0]}"
        assert interpolated[1] > 4.0 and interpolated[1] < 5.2, \
            f"Boundary interpolation failed: {interpolated[1]}"
    
    def test_single_valid_sample(self):
        """Test interpolation when only one valid sample exists."""
        pupil_data = np.array([0.5, 0.4, 5.0, 0.3, 0.6])
        blink_mask = np.array([True, True, False, True, True])
        
        interpolated = interpolate_blinks(pupil_data, blink_mask)
        
        # All blink values should be replaced with the single valid value
        assert np.allclose(interpolated[interpolated != 5.0], 5.0), \
            "All blink values should be replaced with the single valid sample"

class TestIntegration:
    """Integration tests combining detection and interpolation."""
    
    def test_full_pipeline(self):
        """Test complete blink detection and interpolation pipeline."""
        # Create synthetic data with known blink pattern
        pupil_data = np.array([
            5.0, 5.1, 4.9, 0.5, 0.4, 0.6, 5.0, 5.1, 4.8,
            0.3, 0.4, 0.5, 0.6, 5.0, 5.2, 5.1
        ])
        
        # Detect blinks
        blink_mask = detect_blinks(pupil_data, threshold=2.0, min_duration=3)
        
        # Interpolate
        interpolated = interpolate_blinks(pupil_data, blink_mask)
        
        # Verify no NaN values
        assert not np.any(np.isnan(interpolated)), "Interpolated data should have no NaN"
        
        # Verify blink regions are filled with reasonable values
        blink_indices = np.where(blink_mask)[0]
        for idx in blink_indices:
            assert 4.0 < interpolated[idx] < 5.5, \
                f"Interpolated value at {idx} ({interpolated[idx]}) out of expected range"
        
        # Verify non-blink regions remain unchanged
        non_blink_indices = np.where(~blink_mask)[0]
        assert np.allclose(interpolated[non_blink_indices], pupil_data[non_blink_indices]), \
            "Non-blink regions should remain unchanged"
    
    def test_realistic_pupil_data(self):
        """Test with more realistic pupil diameter data."""
        # Simulate realistic pupil data with occasional blinks
        np.random.seed(42)
        base_pupil = 4.5 + 0.3 * np.random.randn(100)
        
        # Insert blinks
        base_pupil[20:25] = 0.5
        base_pupil[60:65] = 0.4
        
        blink_mask = detect_blinks(base_pupil, threshold=1.5, min_duration=3)
        interpolated = interpolate_blinks(base_pupil, blink_mask)
        
        # Verify statistics are preserved
        assert abs(np.mean(interpolated) - np.mean(base_pupil)) < 0.5, \
            "Mean should be preserved after interpolation"
        
        # Verify no extreme values
        assert np.all(interpolated > 0) and np.all(interpolated < 10), \
            "Interpolated values should be within realistic range"

if __name__ == '__main__':
    pytest.main([__file__, '-v'])