"""
Unit tests for the user patience modeling logic (T022).
"""

import pytest
import numpy as np
from simulation.patience import sample_patience

class TestSamplePatience:
    """Tests for the sample_patience function."""

    def test_returns_positive_float(self):
        """Patience time must always be positive."""
        patience = sample_patience(mean_seconds=2.0)
        assert isinstance(patience, float)
        assert patience > 0.0

    def test_default_mean_is_2_seconds(self):
        """Verify the default mean parameter aligns with FR-003."""
        # Run multiple samples to approximate the mean statistically
        samples = [sample_patience(mean_seconds=2.0) for _ in range(10000)]
        empirical_mean = np.mean(samples)
        # Allow 10% tolerance for statistical variance
        assert 1.8 <= empirical_mean <= 2.2

    def test_custom_mean(self):
        """Verify scaling with a custom mean."""
        custom_mean = 5.0
        samples = [sample_patience(mean_seconds=custom_mean) for _ in range(10000)]
        empirical_mean = np.mean(samples)
        assert 4.5 <= empirical_mean <= 5.5

    def test_reproducibility_with_rng(self):
        """Ensure deterministic results when a specific RNG seed is used."""
        seed = 42
        rng1 = np.random.default_rng(seed)
        rng2 = np.random.default_rng(seed)

        val1 = sample_patience(rng=rng1)
        val2 = sample_patience(rng=rng2)

        assert val1 == val2

    def test_invalid_mean_raises_error(self):
        """Ensure negative or zero mean raises ValueError."""
        with pytest.raises(ValueError):
            sample_patience(mean_seconds=-1.0)
        
        with pytest.raises(ValueError):
            sample_patience(mean_seconds=0.0)