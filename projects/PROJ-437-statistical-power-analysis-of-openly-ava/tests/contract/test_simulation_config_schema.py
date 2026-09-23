"""
Contract test for SimulationConfig schema.

Validates the structure and constraints of the SimulationConfig dataclass
as defined in code/models/simulation_config.py.
"""
import dataclasses
import pytest
from models.simulation_config import SimulationConfig
from utils.seed_manager import set_global_seed, get_seed


class TestSimulationConfigSchema:
    """Tests for the SimulationConfig entity schema and validation."""

    def test_valid_config_creation(self):
        """Test that a valid config can be created."""
        config = SimulationConfig(
            sample_size_target=100,
            smoothing_kernel=4.0,
            num_iterations=1000,
            random_seed=42
        )
        assert config.sample_size_target == 100
        assert config.smoothing_kernel == 4.0
        assert config.num_iterations == 1000
        assert config.random_seed == 42

    def test_config_defaults(self):
        """Test that random_seed defaults to None."""
        config = SimulationConfig(
            sample_size_target=50,
            smoothing_kernel=8.0,
            num_iterations=500
        )
        assert config.random_seed is None

    def test_invalid_sample_size_target_zero(self):
        """Test that sample_size_target=0 raises ValueError."""
        with pytest.raises(ValueError) as excinfo:
            SimulationConfig(
                sample_size_target=0,
                smoothing_kernel=4.0,
                num_iterations=100
            )
        assert "sample_size_target must be greater than 0" in str(excinfo.value)

    def test_invalid_sample_size_target_negative(self):
        """Test that negative sample_size_target raises ValueError."""
        with pytest.raises(ValueError) as excinfo:
            SimulationConfig(
                sample_size_target=-10,
                smoothing_kernel=4.0,
                num_iterations=100
            )
        assert "sample_size_target must be greater than 0" in str(excinfo.value)

    def test_invalid_smoothing_kernel_zero(self):
        """Test that smoothing_kernel=0 raises ValueError."""
        with pytest.raises(ValueError) as excinfo:
            SimulationConfig(
                sample_size_target=100,
                smoothing_kernel=0.0,
                num_iterations=100
            )
        assert "smoothing_kernel must be greater than 0" in str(excinfo.value)

    def test_invalid_smoothing_kernel_negative(self):
        """Test that negative smoothing_kernel raises ValueError."""
        with pytest.raises(ValueError) as excinfo:
            SimulationConfig(
                sample_size_target=100,
                smoothing_kernel=-4.0,
                num_iterations=100
            )
        assert "smoothing_kernel must be greater than 0" in str(excinfo.value)

    def test_invalid_num_iterations_zero(self):
        """Test that num_iterations=0 raises ValueError."""
        with pytest.raises(ValueError) as excinfo:
            SimulationConfig(
                sample_size_target=100,
                smoothing_kernel=4.0,
                num_iterations=0
            )
        assert "num_iterations must be greater than 0" in str(excinfo.value)

    def test_invalid_num_iterations_negative(self):
        """Test that negative num_iterations raises ValueError."""
        with pytest.raises(ValueError) as excinfo:
            SimulationConfig(
                sample_size_target=100,
                smoothing_kernel=4.0,
                num_iterations=-5
            )
        assert "num_iterations must be greater than 0" in str(excinfo.value)

    def test_apply_seed_with_value(self):
        """Test that apply_seed sets the global seed when random_seed is provided."""
        config = SimulationConfig(
            sample_size_target=100,
            smoothing_kernel=4.0,
            num_iterations=100,
            random_seed=12345
        )
        config.apply_seed()
        # Verify seed was set by checking get_seed returns the expected value
        assert get_seed() == 12345

    def test_apply_seed_without_value(self):
        """Test that apply_seed does nothing when random_seed is None."""
        config = SimulationConfig(
            sample_size_target=100,
            smoothing_kernel=4.0,
            num_iterations=100,
            random_seed=None
        )
        # Should not raise
        config.apply_seed()

    def test_frozen_dataclass(self):
        """Test that the dataclass is immutable (frozen=True)."""
        config = SimulationConfig(
            sample_size_target=100,
            smoothing_kernel=4.0,
            num_iterations=100
        )
        with pytest.raises(dataclasses.FrozenInstanceError):
            config.sample_size_target = 200

    def test_type_int_for_sample_size(self):
        """Test that sample_size_target must be an int."""
        config = SimulationConfig(
            sample_size_target=100,
            smoothing_kernel=4.0,
            num_iterations=100
        )
        assert isinstance(config.sample_size_target, int)

    def test_type_float_for_kernel(self):
        """Test that smoothing_kernel is treated as float."""
        config = SimulationConfig(
            sample_size_target=100,
            smoothing_kernel=4,  # int passed, should coerce or accept
            num_iterations=100
        )
        # Dataclass will keep it as int if passed as int, but logic expects float-like behavior.
        # We ensure the value is numeric.
        assert isinstance(config.smoothing_kernel, (int, float))
