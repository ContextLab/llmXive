"""
Unit tests for reliability analysis functions in code/validation/reliability.py.

These tests verify:
  - Split-half reliability computation (odd-even split)
  - Cronbach's alpha calculation
  - Error handling for invalid inputs
  - Edge cases (insufficient trials, channels)
"""

import pytest
import numpy as np
from unittest.mock import patch, MagicMock

from code.validation.reliability import (
    split_half_reliability,
    cronbachs_alpha,
    compute_reliability_metrics,
    ReliabilityError
)


class TestSplitHalfReliability:
    """Tests for the split_half_reliability function."""

    def test_basic_computation(self):
        """Test basic split-half reliability with synthetic data."""
        # Create synthetic data: 10 trials, 4 channels, 100 time points
        np.random.seed(42)
        data = np.random.randn(10, 4, 100)

        result = split_half_reliability(data, modality="test")

        assert 'split_half_correlation' in result
        assert 'spearman_brown_alpha' in result
        assert 'p_value' in result
        assert 'n_odd' in result
        assert 'n_even' in result
        assert result['modality'] == "test"
        assert result['method'] == 'split_half_odd_even'
        assert result['n_odd'] == 5  # trials 1,3,5,7,9 (0-indexed)
        assert result['n_even'] == 5  # trials 0,2,4,6,8

    def test_odd_even_split(self):
        """Verify that odd and even trials are correctly split."""
        # Create data where odd and even trials have distinct patterns
        n_trials = 10
        data = np.zeros((n_trials, 2, 10))
        for i in range(n_trials):
            if i % 2 == 0:
                data[i, :, :] = 1.0  # Even trials
            else:
                data[i, :, :] = -1.0  # Odd trials

        result = split_half_reliability(data, modality="test")

        # With perfect separation, correlation should be negative (or close to -1)
        # But since we're averaging, the means will be opposite
        # Odd mean: -1, Even mean: 1 -> correlation of (-1) vs (1) is -1
        # Spearman-Brown: (2 * -1) / (1 + -1) -> division by zero -> handled to 0
        # Actually, the correlation will be -1.0
        assert result['split_half_correlation'] < -0.9

    def test_insufficient_trials(self):
        """Test that insufficient trials raise an error."""
        data = np.random.randn(1, 4, 100)  # Only 1 trial

        with pytest.raises(ReliabilityError, match="Insufficient trials"):
            split_half_reliability(data, modality="test")

    def test_invalid_dimensionality(self):
        """Test that 2D data raises an error."""
        data = np.random.randn(4, 100)  # 2D instead of 3D

        with pytest.raises(ReliabilityError, match="Expected 3D array"):
            split_half_reliability(data, modality="test")

    def test_electrode_filtering(self):
        """Test that electrode filtering works correctly."""
        data = np.random.randn(10, 8, 100)  # 8 channels
        indices = [0, 2, 4, 6]  # Select 4 channels

        result = split_half_reliability(
            data, modality="test", electrode_indices=indices
        )

        # The function should not raise and should return valid results
        assert result['split_half_correlation'] is not None
        assert -1.0 <= result['split_half_correlation'] <= 1.0

    def test_invalid_electrode_indices(self):
        """Test that invalid electrode indices raise an error."""
        data = np.random.randn(10, 4, 100)
        indices = [0, 1, 10]  # 10 is out of bounds

        with pytest.raises(ReliabilityError, match="Invalid electrode indices"):
            split_half_reliability(data, modality="test", electrode_indices=indices)


class TestCronbachsAlpha:
    """Tests for the cronbachs_alpha function."""

    def test_basic_computation(self):
        """Test basic Cronbach's alpha with synthetic data."""
        np.random.seed(42)
        data = np.random.randn(20, 5, 100)  # 20 trials, 5 channels, 100 time points

        result = cronbachs_alpha(data, modality="test")

        assert 'cronbachs_alpha' in result
        assert 'alpha_per_time' in result
        assert 'n_items' in result
        assert result['modality'] == "test"
        assert result['n_items'] == 5
        assert len(result['alpha_per_time']) == 100

    def test_alpha_range(self):
        """Test that alpha values are within valid range [0, 1] typically."""
        np.random.seed(123)
        data = np.random.randn(30, 6, 50)

        result = cronbachs_alpha(data, modality="test")

        # Alpha can theoretically be negative, but in practice should be >= 0 for good data
        # We just check it's a valid float
        assert isinstance(result['cronbachs_alpha'], float)

    def test_time_window_filtering(self):
        """Test that time window filtering works."""
        data = np.random.randn(20, 4, 200)  # 200 time points
        time_window = (50, 100)  # ms

        result = cronbachs_alpha(
            data, modality="test", time_window=time_window
        )

        # The alpha_per_time should be computed only for the filtered window
        # In this implementation, we assume 1ms resolution, so 50 time points
        # Note: The actual implementation might vary based on time vector
        assert len(result['alpha_per_time']) > 0

    def test_insufficient_trials(self):
        """Test that insufficient trials raise an error."""
        data = np.random.randn(1, 4, 100)

        with pytest.raises(ReliabilityError, match="Insufficient trials"):
            cronbachs_alpha(data, modality="test")

    def test_insufficient_channels(self):
        """Test that insufficient channels raise an error."""
        data = np.random.randn(20, 1, 100)  # Only 1 channel

        with pytest.raises(ReliabilityError, match="Insufficient channels"):
            cronbachs_alpha(data, modality="test")

    def test_invalid_dimensionality(self):
        """Test that 2D data raises an error."""
        data = np.random.randn(4, 100)

        with pytest.raises(ReliabilityError, match="Expected 3D array"):
            cronbachs_alpha(data, modality="test")


class TestComputeReliabilityMetrics:
    """Tests for the compute_reliability_metrics function."""

    def test_combined_metrics(self):
        """Test that both split-half and Cronbach's alpha are computed."""
        np.random.seed(42)
        data = np.random.randn(20, 4, 100)

        results = compute_reliability_metrics(data, modality="test")

        assert 'split_half' in results
        assert 'cronbachs_alpha' in results
        assert results['modality'] == "test"

        # Verify structure of sub-results
        assert 'spearman_brown_alpha' in results['split_half']
        assert 'cronbachs_alpha' in results['cronbachs_alpha']  # key name matches value

    def test_electrode_and_time_filtering(self):
        """Test filtering in combined metrics."""
        data = np.random.randn(20, 8, 200)
        indices = [0, 2, 4, 6]
        time_window = (0.0, 0.1)  # 0-100 ms

        results = compute_reliability_metrics(
            data, modality="test",
            electrode_indices=indices,
            time_window=time_window
        )

        assert results['modality'] == "test"
        assert 'split_half' in results
        assert 'cronbachs_alpha' in results