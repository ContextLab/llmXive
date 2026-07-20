"""
Unit tests for epsilon sweep generation utility.
"""
import pytest
import numpy as np
from data_generation.utils import generate_epsilon_sweep_values

class TestEpsilonSweep:
    def test_basic_sweep_generation(self):
        """Test that a basic sweep generates the correct number of values."""
        start = 1e-8
        end = 1e-2
        steps = 5
        values = generate_epsilon_sweep_values(start, end, steps)

        assert len(values) == steps
        assert isinstance(values, list)
        assert all(isinstance(v, float) for v in values)

    def test_sweep_monotonicity(self):
        """Test that the sweep values are monotonically increasing."""
        start = 1e-8
        end = 1e-2
        steps = 10
        values = generate_epsilon_sweep_values(start, end, steps)

        for i in range(1, len(values)):
            assert values[i] >= values[i-1], "Sweep values must be non-decreasing"

    def test_sweep_bounds(self):
        """Test that the sweep includes the start and end values."""
        start = 1e-8
        end = 1e-2
        steps = 10
        values = generate_epsilon_sweep_values(start, end, steps)

        assert values[0] == start
        assert values[-1] == end

    def test_two_steps(self):
        """Test the minimum valid case of 2 steps."""
        start = 1e-8
        end = 1e-2
        steps = 2
        values = generate_epsilon_sweep_values(start, end, steps)

        assert len(values) == 2
        assert values[0] == start
        assert values[1] == end

    def test_invalid_steps_less_than_two(self):
        """Test that steps < 2 raises ValueError."""
        with pytest.raises(ValueError, match="steps must be at least 2"):
            generate_epsilon_sweep_values(1e-8, 1e-2, 1)

    def test_invalid_start_greater_than_end(self):
        """Test that start > end raises ValueError."""
        with pytest.raises(ValueError, match="start .* must be <= end"):
            generate_epsilon_sweep_values(1e-2, 1e-8, 5)

    def test_float_precision(self):
        """Test that the values maintain expected floating point precision."""
        start = 1e-8
        end = 1e-2
        steps = 5
        values = generate_epsilon_sweep_values(start, end, steps)

        # Check that intermediate values are reasonable
        expected_step_size = (end - start) / (steps - 1)
        for i in range(1, steps - 1):
            expected = start + i * expected_step_size
            assert np.isclose(values[i], expected, rtol=1e-9)
