"""
Unit tests for split-half reliability calculation in code/validation/reliability.py.

These tests verify the correctness of the split-half reliability (Odd/Even trials)
and Cronbach's alpha calculation as described in US3.

Note: As per the project's Constitution Amendment VII (T055), Split-Half Reliability
is used as a proxy for Validation Independence in passive oddball paradigms.
"""
import pytest
import numpy as np
from pathlib import Path
import sys
import os

# Ensure code directory is in path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.validation.reliability import (
    compute_split_half_reliability,
    compute_cronbach_alpha,
    ReliabilityError
)


class TestSplitHalfReliability:
    """Tests for the split-half reliability calculation functions."""

    def test_split_half_perfect_correlation(self):
        """Test that identical halves yield a reliability of 1.0."""
        # Create a signal where odd and even halves are identical
        n_trials = 100
        n_channels = 5
        n_times = 200
        
        # Create data where odd and even trials are copies of each other
        data = np.random.randn(n_trials // 2, n_channels, n_times)
        full_data = np.zeros((n_trials, n_channels, n_times))
        full_data[0::2] = data  # Odd indices (0, 2, ...)
        full_data[1::2] = data  # Even indices (1, 3, ...)
        
        reliability = compute_split_half_reliability(full_data)
        
        # With identical halves, correlation should be 1.0 (or very close)
        assert np.isclose(reliability, 1.0, atol=1e-5)

    def test_split_half_zero_correlation(self):
        """Test that uncorrelated halves yield low reliability."""
        # Create data where odd and even halves are completely different
        n_trials = 100
        n_channels = 5
        n_times = 200
        
        odd_data = np.random.randn(n_trials // 2, n_channels, n_times)
        even_data = np.random.randn(n_trials // 2, n_channels, n_times)
        
        full_data = np.zeros((n_trials, n_channels, n_times))
        full_data[0::2] = odd_data
        full_data[1::2] = even_data
        
        reliability = compute_split_half_reliability(full_data)
        
        # With random data, correlation should be near 0 (but not exactly 0)
        # We check that it's within a reasonable range for random data
        assert -0.2 < reliability < 0.2

    def test_split_half_negative_correlation(self):
        """Test that negatively correlated halves yield negative reliability."""
        n_trials = 100
        n_channels = 5
        n_times = 200
        
        # Create data where even halves are negative of odd halves
        odd_data = np.random.randn(n_trials // 2, n_channels, n_times)
        even_data = -odd_data
        
        full_data = np.zeros((n_trials, n_channels, n_times))
        full_data[0::2] = odd_data
        full_data[1::2] = even_data
        
        reliability = compute_split_half_reliability(full_data)
        
        # With perfectly negative correlation, reliability should be -1.0
        assert np.isclose(reliability, -1.0, atol=1e-5)

    def test_split_half_small_dataset(self):
        """Test reliability calculation with a minimal dataset."""
        n_trials = 4  # Minimal even number
        n_channels = 2
        n_times = 10
        
        data = np.random.randn(n_trials, n_channels, n_times)
        reliability = compute_split_half_reliability(data)
        
        # Should return a valid float between -1 and 1
        assert -1.0 <= reliability <= 1.0
        assert isinstance(reliability, float)

    def test_split_half_odd_trials(self):
        """Test that odd number of trials raises an error."""
        n_trials = 5  # Odd number
        n_channels = 2
        n_times = 10
        
        data = np.random.randn(n_trials, n_channels, n_times)
        
        with pytest.raises(ReliabilityError):
            compute_split_half_reliability(data)

    def test_split_half_empty_data(self):
        """Test that empty data raises an error."""
        with pytest.raises(ReliabilityError):
            compute_split_half_reliability(np.array([]))

    def test_split_half_wrong_dimensions(self):
        """Test that data with wrong dimensions raises an error."""
        # Data should be 3D: (trials, channels, times)
        data_2d = np.random.randn(10, 20)
        
        with pytest.raises(ReliabilityError):
            compute_split_half_reliability(data_2d)

    def test_split_half_single_channel(self):
        """Test reliability with a single channel."""
        n_trials = 100
        n_channels = 1
        n_times = 200
        
        data = np.random.randn(n_trials, n_channels, n_times)
        reliability = compute_split_half_reliability(data)
        
        assert -1.0 <= reliability <= 1.0

    def test_split_half_single_timepoint(self):
        """Test reliability with a single timepoint."""
        n_trials = 100
        n_channels = 5
        n_times = 1
        
        data = np.random.randn(n_trials, n_channels, n_times)
        reliability = compute_split_half_reliability(data)
        
        assert -1.0 <= reliability <= 1.0


class TestCronbachAlpha:
    """Tests for the Cronbach's alpha calculation function."""

    def test_cronbach_perfect_reliability(self):
        """Test that perfectly correlated items yield alpha of 1.0."""
        # Create data where all items are identical
        n_items = 10
        n_participants = 50
        
        data = np.ones((n_participants, n_items))
        alpha = compute_cronbach_alpha(data)
        
        # Perfect correlation should yield alpha = 1.0
        assert np.isclose(alpha, 1.0, atol=1e-5)

    def test_cronbach_zero_reliability(self):
        """Test that uncorrelated items yield alpha near 0."""
        n_items = 10
        n_participants = 100
        
        # Random data with no correlation
        data = np.random.randn(n_participants, n_items)
        alpha = compute_cronbach_alpha(data)
        
        # With random data, alpha should be near 0
        assert -0.2 < alpha < 0.2

    def test_cronbach_negative_reliability(self):
        """Test that negatively correlated items can yield negative alpha."""
        n_items = 5
        n_participants = 50
        
        # Create data where items are negatively correlated
        base = np.random.randn(n_participants, 1)
        data = np.hstack([base * (i + 1) * (-1)**i for i in range(n_items)])
        
        alpha = compute_cronbach_alpha(data)
        
        # Alpha can be negative if items are negatively correlated
        assert alpha >= -1.0

    def test_cronbach_two_items(self):
        """Test Cronbach's alpha with minimum number of items (2)."""
        n_items = 2
        n_participants = 50
        
        # Perfectly correlated
        data = np.column_stack([np.random.randn(n_participants)] * 2)
        alpha = compute_cronbach_alpha(data)
        
        assert np.isclose(alpha, 1.0, atol=1e-5)

    def test_cronbach_small_sample(self):
        """Test Cronbach's alpha with small sample size."""
        n_items = 5
        n_participants = 10
        
        data = np.random.randn(n_participants, n_items)
        alpha = compute_cronbach_alpha(data)
        
        # Should return a valid alpha value
        assert -1.0 <= alpha <= 1.0

    def test_cronbach_empty_data(self):
        """Test that empty data raises an error."""
        with pytest.raises(ReliabilityError):
            compute_cronbach_alpha(np.array([]))

    def test_cronbach_single_item(self):
        """Test that single item raises an error (need at least 2)."""
        n_participants = 50
        data = np.random.randn(n_participants, 1)
        
        with pytest.raises(ReliabilityError):
            compute_cronbach_alpha(data)

    def test_cronbach_wrong_dimensions(self):
        """Test that data with wrong dimensions raises an error."""
        # Data should be 2D: (participants, items)
        data_3d = np.random.randn(10, 5, 3)
        
        with pytest.raises(ReliabilityError):
            compute_cronbach_alpha(data_3d)

    def test_cronbach_vs_manual_calculation(self):
        """Verify Cronbach's alpha matches manual calculation."""
        # Create a simple dataset
        n_items = 4
        n_participants = 20
        
        # Create data with known variance and covariance
        np.random.seed(42)
        data = np.random.randn(n_participants, n_items) * 2 + 5
        
        # Manual calculation of Cronbach's alpha
        k = n_items
        item_variances = np.var(data, axis=0, ddof=1)
        total_variance = np.var(np.sum(data, axis=1), ddof=1)
        
        # Cronbach's alpha formula: (k / (k-1)) * (1 - sum(var_i) / var_total)
        manual_alpha = (k / (k - 1)) * (1 - np.sum(item_variances) / total_variance)
        
        computed_alpha = compute_cronbach_alpha(data)
        
        assert np.isclose(computed_alpha, manual_alpha, atol=1e-10)


class TestReliabilityIntegration:
    """Integration tests combining split-half and Cronbach's alpha."""

    def test_reliability_pipeline(self):
        """Test the full reliability calculation pipeline."""
        # Generate synthetic ERP-like data
        np.random.seed(123)
        n_trials = 100
        n_channels = 10
        n_times = 200
        
        # Create realistic ERP data with some structure
        data = np.random.randn(n_trials, n_channels, n_times)
        # Add a common component to increase reliability
        common = np.sin(np.linspace(0, 2*np.pi, n_times)).reshape(1, 1, -1)
        data += 0.5 * common
        
        # Calculate split-half reliability
        split_half_rel = compute_split_half_reliability(data)
        
        # Calculate Cronbach's alpha across channels (treating channels as items)
        # Reshape to (trials, channels) for each time point and average
        alpha_values = []
        for t in range(n_times):
            channel_data = data[:, :, t]  # (trials, channels)
            alpha = compute_cronbach_alpha(channel_data)
            alpha_values.append(alpha)
        
        mean_alpha = np.mean(alpha_values)
        
        # Both metrics should be positive for structured data
        assert split_half_rel > 0
        assert mean_alpha > 0

    def test_reliability_with_noise(self):
        """Test reliability decreases with increasing noise."""
        n_trials = 200
        n_channels = 5
        n_times = 100
        
        # Base signal
        signal = np.sin(np.linspace(0, 4*np.pi, n_times)).reshape(1, 1, -1)
        
        # Calculate reliability at different noise levels
        noise_levels = [0.1, 0.5, 1.0, 2.0, 5.0]
        reliabilities = []
        
        for noise_level in noise_levels:
            noise = np.random.randn(n_trials, n_channels, n_times) * noise_level
            data = signal + noise
            rel = compute_split_half_reliability(data)
            reliabilities.append(rel)
        
        # Reliability should decrease as noise increases
        # (though not strictly monotonic due to randomness)
        assert reliabilities[0] > reliabilities[-1]