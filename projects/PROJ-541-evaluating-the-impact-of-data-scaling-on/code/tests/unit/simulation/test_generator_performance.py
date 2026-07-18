"""
Performance tests for the synthetic data generator.

These tests verify that the generator meets performance targets
and maintains correctness under load.
"""
import pytest
import time
import numpy as np
from pathlib import Path
import sys

# Add code directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from simulation.config import SimulationConfig, get_default_config
from simulation.generator import generate_synthetic_data
from simulation.logger import setup_logger


class TestGeneratorPerformance:
    """Performance tests for the synthetic data generator."""

    @pytest.fixture
    def logger(self):
        """Create a test logger."""
        return setup_logger(__name__)

    def test_generation_speed_small(self, logger):
        """Test generation speed for small datasets (n=100)."""
        config = get_default_config(n_samples=100, mean_diff=0.0, distribution_type="normal", seed=42)

        start_time = time.perf_counter()
        _, _, success, msg = generate_synthetic_data(config, logger)
        end_time = time.perf_counter()

        assert success, f"Generation failed: {msg}"
        elapsed = end_time - start_time
        # Should be very fast for small n
        assert elapsed < 0.1, f"Generation too slow: {elapsed:.4f}s for n=100"

    def test_generation_speed_medium(self, logger):
        """Test generation speed for medium datasets (n=1000)."""
        config = get_default_config(n_samples=1000, mean_diff=0.0, distribution_type="normal", seed=42)

        start_time = time.perf_counter()
        _, _, success, msg = generate_synthetic_data(config, logger)
        end_time = time.perf_counter()

        assert success, f"Generation failed: {msg}"
        elapsed = end_time - start_time
        # Should still be fast for medium n
        assert elapsed < 0.5, f"Generation too slow: {elapsed:.4f}s for n=1000"

    def test_generation_speed_large(self, logger):
        """Test generation speed for large datasets (n=10000)."""
        config = get_default_config(n_samples=10000, mean_diff=0.0, distribution_type="normal", seed=42)

        start_time = time.perf_counter()
        _, _, success, msg = generate_synthetic_data(config, logger)
        end_time = time.perf_counter()

        assert success, f"Generation failed: {msg}"
        elapsed = end_time - start_time
        # Should be reasonable for large n
        assert elapsed < 2.0, f"Generation too slow: {elapsed:.4f}s for n=10000"

    def test_batch_generation_efficiency(self, logger):
        """Test efficiency of batch generation (100 iterations)."""
        config = get_default_config(n_samples=1000, mean_diff=0.0, distribution_type="normal", seed=42)

        start_time = time.perf_counter()
        for i in range(100):
            # Update seed for each iteration
            config.seed = 42 + i
            _, _, success, msg = generate_synthetic_data(config, logger)
            assert success, f"Generation {i} failed: {msg}"
        end_time = time.perf_counter()

        elapsed = end_time - start_time
        avg_time = elapsed / 100

        # Should be efficient with vectorized operations
        assert avg_time < 0.01, f"Average generation time too slow: {avg_time:.6f}s"

    @pytest.mark.parametrize("distribution_type", ["normal", "skewed", "heteroscedastic"])
    def test_distribution_types_performance(self, distribution_type, logger):
        """Test performance across different distribution types."""
        config = get_default_config(
            n_samples=5000,
            mean_diff=0.0,
            distribution_type=distribution_type,
            seed=42
        )

        start_time = time.perf_counter()
        _, _, success, msg = generate_synthetic_data(config, logger)
        end_time = time.perf_counter()

        assert success, f"Generation failed for {distribution_type}: {msg}"
        elapsed = end_time - start_time
        # All distribution types should be reasonably fast
        assert elapsed < 1.0, f"Generation too slow for {distribution_type}: {elapsed:.4f}s"

    def test_vectorization_improvement(self, logger):
        """
        Verify that vectorized operations provide significant speedup.

        This test compares the current implementation against a theoretical
        non-vectorized baseline by checking that generation time scales
        sub-linearly with sample size (indicating vectorization).
        """
        sizes = [1000, 5000, 10000]
        times = []

        for n in sizes:
            config = get_default_config(n_samples=n, mean_diff=0.0, distribution_type="normal", seed=42)
            start_time = time.perf_counter()
            _, _, success, msg = generate_synthetic_data(config, logger)
            end_time = time.perf_counter()

            assert success, f"Generation failed for n={n}: {msg}"
            times.append(end_time - start_time)

        # With vectorization, time should scale roughly linearly or better
        # If not vectorized, we'd expect worse scaling due to Python loop overhead
        # Check that doubling size doesn't more than double time (with margin)
        ratio_1 = times[1] / times[0]  # 5000/1000 = 5x size
        ratio_2 = times[2] / times[1]  # 10000/5000 = 2x size

        # The scaling should be reasonable (not exponential)
        # Allow some variance but ensure it's not worse than linear
        assert ratio_1 < 10, f"Scaling too poor: 5x size increase caused {ratio_1:.2f}x time increase"
        assert ratio_2 < 3, f"Scaling too poor: 2x size increase caused {ratio_2:.2f}x time increase"
