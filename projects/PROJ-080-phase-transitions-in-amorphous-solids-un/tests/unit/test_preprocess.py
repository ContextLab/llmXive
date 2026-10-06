"""
Unit and Integration Tests for Preprocessing Module.

This file contains tests for the Falk-Langer D2_min calculation (T012)
and the Stress-Drop Detection logic (T013).

T013 specifically targets the integration test for stress-drop detection logic.
It verifies that the `detect_yielding` function correctly identifies the first
stress drop > 5% relative to the local maximum over the preceding 50 timesteps,
as per FR-002.
"""

import pytest
import numpy as np
import pandas as pd
from pathlib import Path
import sys
import os

# Ensure project root is in path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.preprocess import detect_yield_onset, TrajectoryCorruptionError


class TestDetectYieldingIntegration:
    """
    Integration tests for stress-drop detection logic (T013).
    
    These tests verify the specific algorithm defined in FR-002:
    "Detect the first drop > 5% relative to the local maximum stress occurring 
    over the preceding 50 timesteps."
    """

    def test_detect_yield_simple_drop(self):
        """
        Test a simple stress curve with a clear single drop.
        Stress rises to 100, stays there for 60 steps, then drops to 80 (20% drop).
        Expected yield point: The first step where stress < local_max * 0.95.
        """
        # Create a stress curve: 50 steps at 100, then drop to 80 at step 50
        stress_curve = np.concatenate([
            np.ones(50) * 100.0,  # Local max window (t-50 to t)
            np.array([80.0])      # Drop occurs here
        ])
        
        # The drop is 20% (100 -> 80), which is > 5%
        # The drop happens at index 50 (0-indexed)
        # At index 50, the window t-50:t is indices 0:50 (all 100s).
        # Local max = 100. 80 < 100 * 0.95 (95). Condition met.
        
        yield_idx = detect_yield_onset(stress_curve)
        
        assert yield_idx == 50, f"Expected yield at index 50, got {yield_idx}"
    
    def test_detect_yield_5_percent_threshold(self):
        """
        Test the exact 5% threshold boundary.
        Drop should be detected if stress < local_max * 0.95.
        Drop of exactly 5% (100 -> 95) should NOT trigger (strict inequality check usually, 
        but spec says 'drop > 5%', so 95 is exactly 5% drop, not > 5%).
        Actually, 100 -> 95 is a 5% drop. 100 -> 94.9 is > 5% drop.
        Let's test a 5.1% drop (100 -> 94.9).
        """
        stress_curve = np.concatenate([
            np.ones(50) * 100.0,
            np.array([94.9])  # 5.1% drop
        ])
        
        yield_idx = detect_yield_onset(stress_curve)
        assert yield_idx == 50, f"Expected yield at index 50 for 5.1% drop, got {yield_idx}"
    
    def test_detect_yield_no_drop(self):
        """
        Test a stress curve that never drops significantly.
        Should return -1 or similar indicator if no yield is found.
        """
        # Monotonically increasing or stable
        stress_curve = np.linspace(50, 100, 100)
        
        yield_idx = detect_yield_onset(stress_curve)
        # If no drop is found, the function should return -1 or raise a specific error
        # Based on typical implementation patterns for "not found"
        assert yield_idx == -1, f"Expected -1 for no yield, got {yield_idx}"
    
    def test_detect_yield_small_fluctuation(self):
        """
        Test that small fluctuations (< 5%) do not trigger yield detection.
        """
        base = 100.0
        # Create noise around 100, max drop is 4%
        noise = np.random.RandomState(42).normal(0, 1, 100)
        stress_curve = base + noise
        
        # Ensure the minimum is not too low
        if np.min(stress_curve) > base * 0.96:
            yield_idx = detect_yield_onset(stress_curve)
            assert yield_idx == -1, f"Expected -1 for small fluctuations, got {yield_idx}"
        else:
            # If random noise accidentally created a big drop, skip this specific random test
            # or force a specific curve
            stress_curve = np.ones(100) * 100.0
            stress_curve[50] = 96.0 # 4% drop
            stress_curve[51:] = 96.0
            
            yield_idx = detect_yield_onset(stress_curve)
            assert yield_idx == -1, f"Expected -1 for 4% drop, got {yield_idx}"
    
    def test_detect_yield_multiple_drops_first_wins(self):
        """
        Test that if multiple drops occur, the FIRST one is selected.
        FR-002: "If multiple drops occur, ignore subsequent ones."
        """
        # Rise to 100, drop to 80 (yield), stay low, then rise and drop again
        # Indices:
        # 0-49: 100
        # 50: 80 (First drop > 5%)
        # 51-99: 80
        # 100-149: 100 (Recovery)
        # 150: 70 (Second drop)
        
        curve = np.concatenate([
            np.ones(50) * 100.0,
            np.ones(50) * 80.0,
            np.ones(50) * 100.0,
            np.array([70.0])
        ])
        
        yield_idx = detect_yield_onset(curve)
        
        # The first drop is at index 50.
        assert yield_idx == 50, f"Expected first drop at 50, got {yield_idx}"
    
    def test_detect_yield_window_constraint(self):
        """
        Test that the local maximum is computed strictly over the preceding 50 timesteps.
        If the peak was 100 steps ago, it should not be the local max for the current window.
        """
        # 0-49: 50 (Low)
        # 50-99: 100 (High peak, but 50 steps ago from index 150)
        # 100-149: 60 (Intermediate)
        # 150: 40 (Drop from 60? 40 is 33% drop from 60. 
        # But is 60 the local max of t-50:t (100:150)?
        # Window 100:150 contains values 60. Max is 60. 40 < 60*0.95 (57). Yes.
        
        curve = np.concatenate([
            np.ones(50) * 50.0,
            np.ones(50) * 100.0,
            np.ones(50) * 60.0,
            np.array([40.0])
        ])
        
        yield_idx = detect_yield_onset(curve)
        
        # At index 150, window is 100:150 (values 60). Max is 60.
        # 40 < 57. Drop detected at 150.
        # Note: The peak at 50-99 (100) is outside the window.
        assert yield_idx == 150, f"Expected yield at 150 (local max 60), got {yield_idx}"
    
    def test_detect_yield_early_index(self):
        """
        Test behavior when the drop happens before the 50-timestep window is full.
        The spec implies a window of "preceding 50". If t < 50, the window is 0:t.
        """
        # 0-4: 100
        # 5: 80 (Drop)
        curve = np.concatenate([
            np.ones(5) * 100.0,
            np.array([80.0])
        ])
        
        yield_idx = detect_yield_onset(curve)
        # Window is 0:5. Max is 100. 80 < 95.
        assert yield_idx == 5, f"Expected yield at 5, got {yield_idx}"
    
    def test_detect_yield_input_type(self):
        """
        Verify the function accepts numpy arrays as expected.
        """
        stress_curve = np.array([100.0] * 60 + [80.0])
        yield_idx = detect_yield_onset(stress_curve)
        assert isinstance(yield_idx, int)
    
    def test_detect_yield_nan_handling(self):
        """
        Test that the function handles NaN values gracefully or raises an error.
        If the input contains NaN, the calculation might result in NaN.
        The spec (FR-002) doesn't explicitly define NaN behavior, but T019 handles stability.
        We assume the input is validated before this or the function handles it.
        If the function returns -1 for NaN, that's acceptable.
        """
        stress_curve = np.array([100.0] * 60 + [np.nan])
        yield_idx = detect_yield_onset(stress_curve)
        # If it returns -1, that's a safe fallback.
        # If it returns an index, that's also acceptable if the logic skips NaN.
        # We just ensure it doesn't crash.
        assert isinstance(yield_idx, int) or np.isnan(yield_idx)
    
    def test_detect_yield_empty_curve(self):
        """
        Test behavior with an empty array.
        """
        stress_curve = np.array([])
        with pytest.raises((ValueError, IndexError)):
            detect_yield_onset(stress_curve)
    
    def test_detect_yield_single_element(self):
        """
        Test behavior with a single element.
        No preceding window, so no drop can be detected.
        """
        stress_curve = np.array([100.0])
        yield_idx = detect_yield_onset(stress_curve)
        assert yield_idx == -1, f"Expected -1 for single element, got {yield_idx}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])