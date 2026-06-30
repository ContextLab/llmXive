"""
Unit tests for ICA artifact flagging logic in preprocess.py.

This module tests the specific logic for identifying ICA components
as artifacts based on:
1. Kurtosis > 5.0
2. High-frequency power > 3x baseline

Since the main 'preprocess.py' module is not yet implemented (T013-T015),
this test file defines the reference implementation of the flagging logic
to ensure the algorithm is correct and testable once the full pipeline is built.
"""

import numpy as np
import pytest
from typing import Tuple, List

# Reference implementation of the ICA flagging logic to be used in preprocess.py
# This function is defined here for testing purposes and will be moved to preprocess.py
# when T014 is implemented.
def flag_ica_artifacts(
    component_data: np.ndarray,
    sampling_rate: float,
    kurtosis_threshold: float = 5.0,
    high_freq_ratio_threshold: float = 3.0
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Flags ICA components as artifacts based on statistical properties.

    Args:
        component_data: 2D numpy array of shape (n_components, n_samples).
        sampling_rate: Sampling rate in Hz.
        kurtosis_threshold: Threshold for kurtosis to flag an artifact.
        high_freq_ratio_threshold: Threshold for high-freq power vs baseline ratio.

    Returns:
        Tuple of (kurtosis_scores, high_freq_ratios) for all components.
        A component is flagged as an artifact if:
        - kurtosis > kurtosis_threshold OR
        - high_freq_ratio > high_freq_ratio_threshold
    """
    n_components = component_data.shape[0]
    kurtosis_scores = np.zeros(n_components)
    high_freq_ratios = np.zeros(n_components)

    # Calculate kurtosis for each component
    # Using scipy.stats.kurtosis would be ideal, but to avoid external dependency
    # for this specific unit test logic, we calculate it manually or use numpy
    # Note: numpy does not have a direct kurtosis function, so we implement the formula
    # Kurtosis = (m4 / m2^2) - 3
    for i in range(n_components):
        data = component_data[i]
        mean = np.mean(data)
        var = np.var(data)
        if var == 0:
            kurtosis_scores[i] = 0
            continue
        
        m4 = np.mean((data - mean) ** 4)
        kurtosis = (m4 / (var ** 2)) - 3
        kurtosis_scores[i] = kurtosis

    # Calculate high-frequency power ratio
    # Define frequency bands: Baseline (1-4 Hz), High (30-45 Hz)
    # We simulate the frequency analysis by creating synthetic spectral data
    # In the real implementation, this would use mne.time_frequency.psd_welch
    
    # For the purpose of this unit test, we simulate the PSD calculation
    # by assuming the component_data is time-domain and we need to compute PSD.
    # However, to keep the test self-contained and fast, we will mock the PSD
    # calculation or assume the function receives pre-computed PSDs if that were the case.
    # But the task description implies flagging based on the component data itself.
    # Let's implement a simple FFT-based power estimation.
    
    n_samples = component_data.shape[1]
    freqs = np.fft.rfftfreq(n_samples, d=1/sampling_rate)
    
    for i in range(n_components):
        data = component_data[i]
        # Perform FFT
        fft_vals = np.fft.rfft(data)
        psd = np.abs(fft_vals) ** 2
        
        # Define frequency bands
        # Baseline: 1-4 Hz
        baseline_mask = (freqs >= 1) & (freqs < 4)
        # High freq: 30-45 Hz
        high_freq_mask = (freqs >= 30) & (freqs <= 45)
        
        if np.sum(baseline_mask) == 0 or np.sum(high_freq_mask) == 0:
            high_freq_ratios[i] = 0
            continue
        
        baseline_power = np.mean(psd[baseline_mask])
        high_freq_power = np.mean(psd[high_freq_mask])
        
        if baseline_power == 0:
            high_freq_ratios[i] = 0
        else:
            high_freq_ratios[i] = high_freq_power / baseline_power

    return kurtosis_scores, high_freq_ratios


def is_artifact(kurtosis: float, high_freq_ratio: float) -> bool:
    """Helper to determine if a component is an artifact."""
    return kurtosis > 5.0 or high_freq_ratio > 3.0


class TestICAArtifactFlagging:
    """Tests for the ICA artifact flagging logic."""

    def test_kurtosis_threshold_flagging(self):
        """Test that components with kurtosis > 5.0 are flagged."""
        # Create synthetic data with high kurtosis (spiky signal)
        # A signal with a few extreme outliers will have high kurtosis
        n_components = 3
        n_samples = 1000
        sampling_rate = 256.0
        
        # Component 0: Normal (low kurtosis)
        # Component 1: High kurtosis (spiky)
        # Component 2: Normal
        data = np.random.randn(n_components, n_samples)
        data[1, 50] = 100.0  # Add a spike
        data[1, 51] = 100.0
        data[1, 52] = 100.0
        
        kurtosis_scores, _ = flag_ica_artifacts(data, sampling_rate)
        
        # Verify kurtosis of component 1 is high
        assert kurtosis_scores[1] > 5.0, f"Expected kurtosis > 5.0, got {kurtosis_scores[1]}"
        assert kurtosis_scores[0] <= 5.0, "Component 0 should not have high kurtosis"
        assert kurtosis_scores[2] <= 5.0, "Component 2 should not have high kurtosis"

    def test_high_freq_power_threshold_flagging(self):
        """Test that components with high-freq power > 3x baseline are flagged."""
        n_components = 2
        n_samples = 4096  # Large enough for frequency resolution
        sampling_rate = 256.0
        
        # Component 0: Normal noise
        data = np.random.randn(n_components, n_samples)
        
        # Component 1: Add high frequency noise (30-45 Hz)
        t = np.arange(n_samples) / sampling_rate
        high_freq_signal = np.sin(2 * np.pi * 35 * t)  # 35 Hz sine wave
        # Add some noise to make it realistic
        data[1] += high_freq_signal * 5.0  # Amplify the high freq component
        
        _, high_freq_ratios = flag_ica_artifacts(data, sampling_rate)
        
        # Component 1 should have a high ratio
        assert high_freq_ratios[1] > 3.0, f"Expected high freq ratio > 3.0, got {high_freq_ratios[1]}"
        # Component 0 should be normal (ratio ~ 1 or less)
        assert high_freq_ratios[0] <= 3.0, "Component 0 should not have high freq ratio > 3.0"

    def test_combined_flagging_logic(self):
        """Test the combined logic: flag if EITHER condition is met."""
        n_components = 3
        n_samples = 1000
        sampling_rate = 256.0
        
        data = np.random.randn(n_components, n_samples)
        
        # Component 0: Normal
        # Component 1: High kurtosis only
        data[1, 10] = 20.0
        data[1, 11] = 20.0
        # Component 2: High freq power only
        t = np.arange(n_samples) / sampling_rate
        data[2] += np.sin(2 * np.pi * 40 * t) * 5.0
        
        kurtosis_scores, high_freq_ratios = flag_ica_artifacts(data, sampling_rate)
        
        # Component 0: Should NOT be flagged
        assert not is_artifact(kurtosis_scores[0], high_freq_ratios[0])
        
        # Component 1: Should be flagged (high kurtosis)
        assert is_artifact(kurtosis_scores[1], high_freq_ratios[1])
        
        # Component 2: Should be flagged (high freq power)
        assert is_artifact(kurtosis_scores[2], high_freq_ratios[2])

    def test_edge_case_zero_variance(self):
        """Test handling of components with zero variance."""
        n_components = 2
        n_samples = 100
        sampling_rate = 256.0
        
        data = np.zeros((n_components, n_samples))
        data[0] = 1.0  # Constant signal
        
        kurtosis_scores, high_freq_ratios = flag_ica_artifacts(data, sampling_rate)
        
        # Zero variance should not crash and should result in low scores
        assert kurtosis_scores[0] == 0.0
        assert high_freq_ratios[0] == 0.0
        
    def test_artifact_detection_integration(self):
        """Integration test: simulate a realistic ICA component matrix and check flags."""
        n_components = 5
        n_samples = 2048
        sampling_rate = 256.0
        
        # Simulate 5 components
        # 0: Brain signal (normal)
        # 1: Eye blink (high kurtosis)
        # 2: Muscle artifact (high freq)
        # 3: Heart beat (periodic, might not be flagged by these specific rules, but let's see)
        # 4: Normal brain signal
        
        data = np.random.randn(n_components, n_samples)
        
        # Simulate eye blink: sharp transient
        data[1, 500] = 50.0
        data[1, 501] = 50.0
        data[1, 502] = 50.0
        
        # Simulate muscle artifact: high freq oscillation
        t = np.arange(n_samples) / sampling_rate
        data[2] += np.sin(2 * np.pi * 35 * t) * 10.0
        
        kurtosis_scores, high_freq_ratios = flag_ica_artifacts(data, sampling_rate)
        
        # Check that blink is flagged by kurtosis
        assert kurtosis_scores[1] > 5.0
        
        # Check that muscle is flagged by high freq power
        assert high_freq_ratios[2] > 3.0

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
