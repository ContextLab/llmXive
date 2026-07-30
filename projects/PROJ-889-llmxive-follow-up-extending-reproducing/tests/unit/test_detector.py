"""
Unit tests for the detector module.
"""
import pytest
import numpy as np
import pandas as pd
from pathlib import Path

# Import the functions to test
from detector import (
    calculate_sliding_zscore,
    calculate_dynamic_threshold,
    detect_hacking_events
)


class TestCalculateSlidingZscore:
    """Tests for the sliding window z-score calculation."""

    def test_basic_zscore_calculation(self):
        """Test basic z-score calculation with known values."""
        # Create a simple array with a known outlier
        values = np.array([1.0, 1.0, 1.0, 1.0, 10.0])  # Last value is an outlier
        z_scores = calculate_sliding_zscore(values, window_size=5, min_samples=2)

        # The last value should have a high z-score
        assert z_scores[-1] > 2.0, f"Expected high z-score for outlier, got {z_scores[-1]}"

    def test_insufficient_samples(self):
        """Test that z-score is 0 when insufficient samples exist."""
        values = np.array([1.0, 1.0])
        z_scores = calculate_sliding_zscore(values, window_size=5, min_samples=3)

        # First two should be 0 due to insufficient samples
        assert z_scores[0] == 0.0
        assert z_scores[1] == 0.0

    def test_zero_variance_handling(self):
        """Test handling of zero variance (constant values)."""
        values = np.array([5.0, 5.0, 5.0, 5.0, 5.0])
        z_scores = calculate_sliding_zscore(values, window_size=3, min_samples=2)

        # All z-scores should be 0 or very small (safe_z_score handles this)
        assert np.allclose(z_scores, 0.0, atol=1e-9)

    def test_window_size_effect(self):
        """Test that larger windows produce different z-scores."""
        values = np.array([1.0, 1.0, 1.0, 1.0, 10.0])

        z_small = calculate_sliding_zscore(values, window_size=3, min_samples=2)
        z_large = calculate_sliding_zscore(values, window_size=5, min_samples=2)

        # Z-scores should differ based on window size
        assert not np.array_equal(z_small, z_large)


class TestCalculateDynamicThreshold:
    """Tests for dynamic threshold calculation."""

    def test_basic_threshold_calculation(self):
        """Test basic threshold calculation."""
        dG_values = np.array([0.1, 0.2, 0.15, 0.18, 0.12])
        threshold = calculate_dynamic_threshold(dG_values, multiplier=2.0)

        # Threshold should be positive and proportional to std
        assert threshold > 0

    def test_zero_variance_threshold(self):
        """Test threshold calculation with zero variance."""
        dG_values = np.array([0.5, 0.5, 0.5, 0.5])
        threshold = calculate_dynamic_threshold(dG_values, multiplier=2.0)

        # Should not be zero (uses 1e-9 floor)
        assert threshold > 0

    def test_empty_array(self):
        """Test threshold calculation with empty array."""
        dG_values = np.array([])
        threshold = calculate_dynamic_threshold(dG_values, multiplier=2.0)

        assert threshold == 0.0

    def test_multiplier_effect(self):
        """Test that multiplier affects threshold."""
        dG_values = np.array([0.1, 0.2, 0.3, 0.4])

        threshold_small = calculate_dynamic_threshold(dG_values, multiplier=1.0)
        threshold_large = calculate_dynamic_threshold(dG_values, multiplier=5.0)

        assert threshold_large > threshold_small


class TestDetectHackingEvents:
    """Tests for the full hacking detection pipeline."""

    def create_sample_dataframe(self):
        """Create a sample DataFrame for testing."""
        data = {
            'seed_id': ['seed1'] * 10 + ['seed2'] * 10,
            'bias_type': ['lexical'] * 20,
            'timestep': list(range(10)) + list(range(10)),
            'G_t': [1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 10.0] * 2,
            'dG_t': [0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 9.0] * 2
        }
        return pd.DataFrame(data)

    def test_basic_detection(self):
        """Test basic hacking detection on sample data."""
        df = self.create_sample_dataframe()
        result = detect_hacking_events(df, zscore_threshold=3.0)

        # Check that z_score column was added
        assert 'z_score' in result.columns
        assert 'hacked_label' in result.columns

        # The outlier timestep (9) should be flagged
        # We expect at least one hacked event
        assert result['hacked_label'].sum() > 0

    def test_multiple_seeds(self):
        """Test detection across multiple seeds."""
        df = self.create_sample_dataframe()
        result = detect_hacking_events(df)

        # Should process both seeds
        assert len(result) == len(df)
        assert result['seed_id'].nunique() == 2

    def test_missing_columns(self):
        """Test error handling for missing columns."""
        df = pd.DataFrame({'seed_id': ['seed1'], 'bias_type': ['lexical']})

        with pytest.raises(ValueError):
            detect_hacking_events(df)

    def test_different_thresholds(self):
        """Test that different thresholds produce different results."""
        df = self.create_sample_dataframe()

        result_strict = detect_hacking_events(df, zscore_threshold=10.0)
        result_loose = detect_hacking_events(df, zscore_threshold=1.0)

        # Loose threshold should flag more events
        assert result_loose['hacked_label'].sum() >= result_strict['hacked_label'].sum()

    def test_zscore_calculation_consistency(self):
        """Test that z-scores are calculated correctly."""
        df = self.create_sample_dataframe()
        result = detect_hacking_events(df)

        # The outlier should have a high z-score
        outlier_mask = result['timestep'] == 9
        outlier_zscores = result.loc[outlier_mask, 'z_score']

        # At least one outlier should have z-score > 2
        assert (outlier_zscores > 2.0).any(), f"Expected high z-score for outlier, got {outlier_zscores}"