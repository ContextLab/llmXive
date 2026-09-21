"""
Contract tests for the SimulationConfig schema.

This module implements Test-Driven Development (TDD) contract tests
to validate the `SimulationConfig` entity constraints and structure
before the full implementation is integrated.

Tests verify:
1. Valid configuration creation.
2. Validation of `sample_size_target` (must be > 0).
3. Validation of `smoothing_kernel` (must be > 0).
4. Validation of `num_iterations` (must be > 0).
5. Type validation for `random_seed` (must be int if provided).
"""
import pytest
from dataclasses import FrozenInstanceError

from models.simulation_config import SimulationConfig


class TestSimulationConfigSchema:
    """Contract tests for SimulationConfig entity."""

    def test_valid_config_creation(self):
        """Test that a valid configuration can be created."""
        config = SimulationConfig(
            sample_size_target=50,
            smoothing_kernel=4.0,
            num_iterations=1000,
            random_seed=42
        )
        assert config.sample_size_target == 50
        assert config.smoothing_kernel == 4.0
        assert config.num_iterations == 1000
        assert config.random_seed == 42

    def test_valid_config_no_seed(self):
        """Test creation without an explicit random seed."""
        config = SimulationConfig(
            sample_size_target=20,
            smoothing_kernel=8.0,
            num_iterations=500
        )
        assert config.random_seed is None

    def test_invalid_sample_size_target_zero(self):
        """Test that sample_size_target must be greater than 0."""
        with pytest.raises(ValueError) as exc_info:
            SimulationConfig(
                sample_size_target=0,
                smoothing_kernel=4.0,
                num_iterations=100
            )
        assert "sample_size_target must be greater than 0" in str(exc_info.value)

    def test_invalid_sample_size_target_negative(self):
        """Test that sample_size_target cannot be negative."""
        with pytest.raises(ValueError) as exc_info:
            SimulationConfig(
                sample_size_target=-10,
                smoothing_kernel=4.0,
                num_iterations=100
            )
        assert "sample_size_target must be greater than 0" in str(exc_info.value)

    def test_invalid_smoothing_kernel_zero(self):
        """Test that smoothing_kernel must be greater than 0."""
        with pytest.raises(ValueError) as exc_info:
            SimulationConfig(
                sample_size_target=50,
                smoothing_kernel=0.0,
                num_iterations=100
            )
        assert "smoothing_kernel must be greater than 0" in str(exc_info.value)

    def test_invalid_smoothing_kernel_negative(self):
        """Test that smoothing_kernel cannot be negative."""
        with pytest.raises(ValueError) as exc_info:
            SimulationConfig(
                sample_size_target=50,
                smoothing_kernel=-4.0,
                num_iterations=100
            )
        assert "smoothing_kernel must be greater than 0" in str(exc_info.value)

    def test_invalid_num_iterations_zero(self):
        """Test that num_iterations must be greater than 0."""
        with pytest.raises(ValueError) as exc_info:
            SimulationConfig(
                sample_size_target=50,
                smoothing_kernel=4.0,
                num_iterations=0
            )
        assert "num_iterations must be greater than 0" in str(exc_info.value)

    def test_invalid_num_iterations_negative(self):
        """Test that num_iterations cannot be negative."""
        with pytest.raises(ValueError) as exc_info:
            SimulationConfig(
                sample_size_target=50,
                smoothing_kernel=4.0,
                num_iterations=-5
            )
        assert "num_iterations must be greater than 0" in str(exc_info.value)

    def test_config_is_frozen(self):
        """Test that SimulationConfig instances are immutable (frozen)."""
        config = SimulationConfig(
            sample_size_target=50,
            smoothing_kernel=4.0,
            num_iterations=100
        )
        with pytest.raises(FrozenInstanceError):
            config.sample_size_target = 100

    def test_random_seed_type_int(self):
        """Test that random_seed accepts integer values."""
        config = SimulationConfig(
            sample_size_target=50,
            smoothing_kernel=4.0,
            num_iterations=100,
            random_seed=12345
        )
        assert isinstance(config.random_seed, int)

    def test_random_seed_type_none(self):
        """Test that random_seed accepts None."""
        config = SimulationConfig(
            sample_size_target=50,
            smoothing_kernel=4.0,
            num_iterations=100,
            random_seed=None
        )
        assert config.random_seed is None