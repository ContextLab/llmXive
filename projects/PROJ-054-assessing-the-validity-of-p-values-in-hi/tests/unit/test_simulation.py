"""
Unit tests for simulation utilities.
Tests for code/utils/simulation.py
"""
import numpy as np
import pytest
from utils.simulation import SimulationConfig, SyntheticDataset, MemoryMonitor
from utils.exceptions import HighDimensionalInstabilityError, SimulationError


class TestSimulationConfig:
    def test_default_values(self):
        """Test that default values are set correctly."""
        config = SimulationConfig()
        assert config.n_iterations == 1000
        assert config.seed is not None
        assert config.n_samples == 100
        assert config.n_features == 500

    def test_custom_values(self):
        """Test that custom values are set correctly."""
        config = SimulationConfig(
            n_iterations=500,
            seed=42,
            n_samples=200,
            n_features=1000
        )
        assert config.n_iterations == 500
        assert config.seed == 42
        assert config.n_samples == 200
        assert config.n_features == 1000

    def test_invalid_iterations(self):
        """Test that negative iterations raise an error."""
        with pytest.raises(ValueError):
            SimulationConfig(n_iterations=-1)

    def test_invalid_seed(self):
        """Test that invalid seed types raise an error."""
        with pytest.raises(TypeError):
            SimulationConfig(seed="invalid")


class TestSyntheticDataset:
    def test_creation_with_params(self):
        """Test creating a dataset with specific parameters."""
        dataset = SyntheticDataset(
            n_samples=100,
            n_features=50,
            correlation=0.5,
            distribution="normal"
        )
        assert dataset.n_samples == 100
        assert dataset.n_features == 50
        assert dataset.correlation == 0.5
        assert dataset.distribution == "normal"

    def test_data_shape(self):
        """Test that generated data has correct shape."""
        dataset = SyntheticDataset(
            n_samples=100,
            n_features=50,
            correlation=0.0,
            distribution="normal"
        )
        assert dataset.data.shape == (100, 50)

    def test_hash_computation(self):
        """Test that hash is computed and is consistent."""
        dataset1 = SyntheticDataset(
            n_samples=100,
            n_features=50,
            correlation=0.5,
            distribution="normal",
            seed=42
        )
        dataset2 = SyntheticDataset(
            n_samples=100,
            n_features=50,
            correlation=0.5,
            distribution="normal",
            seed=42
        )
        dataset3 = SyntheticDataset(
            n_samples=100,
            n_features=50,
            correlation=0.5,
            distribution="normal",
            seed=43
        )

        assert dataset1.sha256 == dataset2.sha256
        assert dataset1.sha256 != dataset3.sha256

    def test_to_dict(self):
        """Test that to_dict returns all required fields."""
        dataset = SyntheticDataset(
            n_samples=100,
            n_features=50,
            correlation=0.5,
            distribution="normal",
            seed=42
        )
        data_dict = dataset.to_dict()

        assert "sha256" in data_dict
        assert "n_samples" in data_dict
        assert "n_features" in data_dict
        assert "correlation" in data_dict
        assert "distribution" in data_dict
        assert "seed" in data_dict


class TestMemoryMonitor:
    def test_initial_state(self):
        """Test initial memory state."""
        monitor = MemoryMonitor(limit_mb=1000)
        assert monitor.current_mb > 0
        assert monitor.limit_mb == 1000
        assert not monitor.exceeded

    def test_within_limit(self):
        """Test that memory usage within limit doesn't raise."""
        monitor = MemoryMonitor(limit_mb=10000)  # High limit
        # Should not raise
        monitor.check()
        assert not monitor.exceeded

    def test_exceeds_limit(self):
        """Test that exceeding limit raises MemoryLimitError."""
        # Set a very low limit that will be exceeded immediately
        monitor = MemoryMonitor(limit_mb=0.001)  # 1KB
        with pytest.raises(Exception) as exc_info:
            monitor.check()
        assert "MemoryLimitError" in str(type(exc_info.value)) or "Memory" in str(exc_info.value)

    def test_limit_persistent(self):
        """Test that limit is persistent across checks."""
        monitor = MemoryMonitor(limit_mb=10000)
        monitor.check()
        first_check = monitor.current_mb

        monitor.check()
        second_check = monitor.current_mb

        # Limit should still be the same
        assert monitor.limit_mb == 10000
        # Current memory should be roughly similar (may vary slightly)
        assert abs(first_check - second_check) < 100  # Within 100MB tolerance

    def test_custom_limit(self):
        """Test setting a custom memory limit."""
        monitor = MemoryMonitor(limit_mb=5000)
        assert monitor.limit_mb == 5000

def test_synthetic_dataset_distribution_types():
    """Test that different distribution types are handled correctly."""
    distributions = ["normal", "t", "skew_normal"]
    for dist_type in distributions:
        dataset = SyntheticDataset(
            n_samples=50,
            n_features=20,
            correlation=0.0,
            distribution=dist_type,
            seed=42
        )
        assert dataset.distribution == dist_type
        assert dataset.data.shape == (50, 20)
        # Verify data is not all zeros
        assert np.any(dataset.data != 0)
