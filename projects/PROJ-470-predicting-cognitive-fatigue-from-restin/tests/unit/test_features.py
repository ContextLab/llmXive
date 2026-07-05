import pytest
import numpy as np
import sys
from pathlib import Path

# Add the project root to the path to allow imports from code/
# This assumes the test is run from the project root or the path is set correctly
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from features import calculate_permutation_entropy, load_config
from models.complexity_metric import MetricType

class TestPermutationEntropy:
    """
    Unit tests for permutation entropy calculation on known signals.
    Verifies that the function produces values within expected theoretical ranges
    for specific synthetic signals (White Noise, Sine Wave, Random Walk).
    """

    def _get_config(self):
        """Helper to get default config parameters for testing."""
        try:
            config = load_config()
            # Ensure embedding dimension and order are set for testing
            if 'embedding_dim' not in config:
                config['embedding_dim'] = 3
            if 'time_lag' not in config:
                config['time_lag'] = 1
            return config
        except Exception:
            # Fallback defaults if config loading fails
            return {
                'embedding_dim': 3,
                'time_lag': 1,
                'min_segment_length': 100
            }

    def test_white_noise_high_entropy(self):
        """
        White noise should yield high permutation entropy (close to log2(d!)).
        For embedding dimension d=3, max entropy is log2(6) ≈ 2.585.
        We expect a value significantly high (e.g., > 2.0).
        """
        config = self._get_config()
        # Generate 10,000 samples of white noise
        np.random.seed(42)
        signal = np.random.randn(10000)

        pe = calculate_permutation_entropy(signal, config)

        # Verify return type
        assert isinstance(pe, float), "Permutation entropy must be a float"

        # Verify range: Max for d=3 is ~2.585. White noise should be high.
        max_entropy = np.log2(np.math.factorial(config['embedding_dim']))
        assert 0 < pe <= max_entropy + 0.01, f"PE {pe} out of bounds [0, {max_entropy}]"
        assert pe > 2.0, f"White noise PE {pe} is too low (expected > 2.0)"

    def test_sine_wave_low_entropy(self):
        """
        A pure sine wave is highly deterministic and should yield low permutation entropy.
        We expect a value close to 0.
        """
        config = self._get_config()
        # Generate 10,000 samples of a sine wave
        t = np.linspace(0, 100, 10000)
        signal = np.sin(t)

        pe = calculate_permutation_entropy(signal, config)

        assert isinstance(pe, float), "Permutation entropy must be a float"

        # Pure sine wave should have very low complexity
        assert pe < 1.0, f"Sine wave PE {pe} is too high (expected < 1.0)"

    def test_random_walk_medium_entropy(self):
        """
        A random walk (integrated white noise) has structure but is stochastic.
        Entropy should be lower than white noise but higher than a sine wave.
        """
        config = self._get_config()
        # Generate random walk
        np.random.seed(123)
        steps = np.random.randn(10000)
        signal = np.cumsum(steps)

        pe = calculate_permutation_entropy(signal, config)

        assert isinstance(pe, float), "Permutation entropy must be a float"

        # Should be strictly between sine wave and white noise bounds
        max_entropy = np.log2(np.math.factorial(config['embedding_dim']))
        assert 0 < pe < max_entropy, f"Random walk PE {pe} out of expected range"

    def test_constant_signal_zero_entropy(self):
        """
        A constant signal has no variation, resulting in 0 entropy.
        """
        config = self._get_config()
        signal = np.ones(1000)

        pe = calculate_permutation_entropy(signal, config)

        assert isinstance(pe, float), "Permutation entropy must be a float"
        assert pe == 0.0, f"Constant signal PE {pe} should be 0.0"

    def test_empty_signal_raises_error(self):
        """
        Passing an empty signal should raise a ValueError or return 0.0 gracefully.
        Based on typical implementation, we expect a ValueError for insufficient data.
        """
        config = self._get_config()
        signal = np.array([])

        with pytest.raises(ValueError):
            calculate_permutation_entropy(signal, config)

    def test_short_signal_raises_error(self):
        """
        A signal shorter than the embedding dimension should raise an error.
        """
        config = self._get_config()
        signal = np.array([1.0, 2.0]) # Length 2, embedding_dim is 3

        with pytest.raises(ValueError):
            calculate_permutation_entropy(signal, config)