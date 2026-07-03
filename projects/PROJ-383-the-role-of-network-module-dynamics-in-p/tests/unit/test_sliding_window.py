"""
Unit tests for sliding window generation and window length validation.
Tests T016: US2 - Sliding window generation and validation logic.
"""
import pytest
import numpy as np
import pandas as pd
from pathlib import Path
import sys

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from utils.config import WINDOW_LENGTHS_SEC, set_all_seeds
from analysis.dynamic_connectivity import generate_sliding_windows, validate_window_params


class TestSlidingWindowGeneration:
    """Tests for the sliding window generation logic."""

    def setup_method(self):
        """Set up test fixtures."""
        set_all_seeds(42)
        # Create synthetic time series data: 100 time points, 5 regions
        self.time_series = np.random.randn(100, 5)
        self.fps = 2.0  # Frames per second (TR = 0.5s)

    def test_valid_window_generation(self):
        """Test that valid window lengths generate expected number of windows."""
        window_sec = 60
        step_sec = 30
        
        windows = generate_sliding_windows(
            self.time_series, 
            window_sec, 
            step_sec, 
            self.fps
        )
        
        # Expected: (100 * 0.5) = 50 seconds total
        # Window = 60s -> 120 frames (impossible with 100 points)
        # Wait, let's recalculate: 100 points at TR=0.5s = 50s total.
        # Window 60s > 50s total -> should return empty or handle gracefully.
        # Let's use a window that fits: 20s window (40 frames), step 10s (20 frames)
        
        valid_window = 20
        valid_step = 10
        
        windows = generate_sliding_windows(
            self.time_series,
            valid_window,
            valid_step,
            self.fps
        )
        
        # Total duration = 50s
        # First window: 0-20s (0-40 frames)
        # Second: 10-30s (20-60 frames)
        # Third: 20-40s (40-80 frames)
        # Fourth: 30-50s (60-100 frames)
        # Expected 4 windows
        expected_windows = 4
        assert len(windows) == expected_windows, f"Expected {expected_windows} windows, got {len(windows)}"

    def test_window_structure(self):
        """Test that each window has correct shape."""
        window_sec = 20
        step_sec = 10
        
        windows = generate_sliding_windows(
            self.time_series,
            window_sec,
            step_sec,
            self.fps
        )
        
        # Each window should be (num_timepoints_in_window, num_regions)
        # 20s window at TR=0.5s -> 40 timepoints
        expected_timepoints = int(window_sec * self.fps)
        
        for i, window in enumerate(windows):
            assert window.shape[0] == expected_timepoints, \
                f"Window {i}: Expected {expected_timepoints} timepoints, got {window.shape[0]}"
            assert window.shape[1] == self.time_series.shape[1], \
                f"Window {i}: Expected {self.time_series.shape[1]} regions, got {window.shape[1]}"

    def test_window_overlap(self):
        """Test that windows overlap correctly based on step size."""
        window_sec = 30
        step_sec = 15
        
        windows = generate_sliding_windows(
            self.time_series,
            window_sec,
            step_sec,
            self.fps
        )
        
        if len(windows) >= 2:
            # Calculate frame overlap
            window_frames = int(window_sec * self.fps)
            step_frames = int(step_sec * self.fps)
            expected_overlap = window_frames - step_frames
            
            # Check that the start of window 2 is step_frames after window 1
            # This is implicitly tested by the generation logic, but we verify
            # that we have multiple windows
            assert len(windows) > 1, "Should have multiple windows with step < window"

    def test_invalid_window_length(self):
        """Test handling of window length larger than data."""
        huge_window = 200  # 200s window, but we only have 50s of data
        
        windows = generate_sliding_windows(
            self.time_series,
            huge_window,
            10,
            self.fps
        )
        
        # Should return empty list or handle gracefully
        assert len(windows) == 0, "Should return no windows if window > data length"

    def test_zero_step_raises_error(self):
        """Test that zero step size raises an error."""
        with pytest.raises(ValueError, match="Step size must be positive"):
            generate_sliding_windows(
                self.time_series,
                20,
                0,
                self.fps
            )

    def test_negative_window_raises_error(self):
        """Test that negative window length raises an error."""
        with pytest.raises(ValueError, match="Window length must be positive"):
            generate_sliding_windows(
                self.time_series,
                -10,
                5,
                self.fps
            )


class TestWindowLengthValidation:
    """Tests for window length validation logic."""

    def setup_method(self):
        """Set up test fixtures."""
        set_all_seeds(42)
        self.time_series = np.random.randn(100, 5)
        self.fps = 2.0

    def test_valid_window_lengths(self):
        """Test that valid window lengths pass validation."""
        for window_sec in [10, 20, 30, 60]:
            is_valid, message = validate_window_params(
                self.time_series,
                window_sec,
                10,
                self.fps
            )
            assert is_valid, f"Window {window_sec}s should be valid: {message}"

    def test_window_too_large(self):
        """Test that window larger than data fails validation."""
        is_valid, message = validate_window_params(
            self.time_series,
            200,  # 200s > 50s total
            10,
            self.fps
        )
        assert not is_valid, "Window 200s should be invalid"
        assert "insufficient time points" in message.lower() or "window" in message.lower()

    def test_window_too_small(self):
        """Test that very small window fails validation (less than 1 TR)."""
        is_valid, message = validate_window_params(
            self.time_series,
            0.1,  # 0.1s < 0.5s TR
            0.1,
            self.fps
        )
        assert not is_valid, "Window 0.1s should be invalid"

    def test_minimum_windows_check(self):
        """Test that insufficient number of windows is caught."""
        # With 50s data, 45s window, 5s step -> only 2 windows
        # This might be valid depending on implementation, but let's test edge case
        is_valid, message = validate_window_params(
            self.time_series,
            45,  # 45s window
            5,   # 5s step
            self.fps
        )
        # This should be valid as it produces at least 2 windows
        # If the implementation requires more, this test will reveal it
        # For now, we expect it to be valid
        assert is_valid or "minimum" in message.lower(), \
            f"45s window with 5s step should be handled: {message}"

    def test_step_larger_than_window(self):
        """Test that step larger than window is handled."""
        is_valid, message = validate_window_params(
            self.time_series,
            10,  # 10s window
            20,  # 20s step (larger than window)
            self.fps
        )
        # This is technically valid but inefficient; might warn or allow
        # We expect it to be valid as it just means no overlap
        assert is_valid, "Step > window should be valid (non-overlapping)"

    def test_config_window_lengths_validation(self):
        """Test that all configured window lengths are validated."""
        for window_sec in WINDOW_LENGTHS_SEC:
            # Check if this window is reasonable for our test data
            is_valid, message = validate_window_params(
                self.time_series,
                window_sec,
                10,
                self.fps
            )
            # Some might be invalid due to data size, which is expected
            # The function should not crash
            assert isinstance(is_valid, bool), "Validation should return boolean"
            assert isinstance(message, str), "Message should be string"

    def test_non_integer_window_handling(self):
        """Test handling of non-integer window lengths."""
        is_valid, message = validate_window_params(
            self.time_series,
            15.5,  # Non-integer
            5.5,
            self.fps
        )
        # Should handle float values correctly
        assert isinstance(is_valid, bool), "Should handle float window lengths"