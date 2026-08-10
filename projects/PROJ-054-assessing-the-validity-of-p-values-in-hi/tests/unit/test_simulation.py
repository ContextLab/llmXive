"""
Unit tests for simulation utilities.
Tests added as part of T043 to ensure comprehensive test coverage.
"""
import pytest
import numpy as np
from pathlib import Path
import sys
import os

# Add code directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'code'))

from utils.simulation import SimulationConfig, SyntheticDataset, MemoryMonitor
from utils.exceptions import SimulationError

class TestSimulationConfig:
    """Tests for SimulationConfig class."""

    def test_default_initialization(self):
        """Test that default values are set correctly."""
        config = SimulationConfig()
        assert config.n == 100
        assert config.p == 1000
        assert config.rho == 0.5
        assert config.distribution_type == 'normal'
        assert config.seed is not None

    def test_custom_initialization(self):
        """Test custom parameter values."""
        config = SimulationConfig(n=50, p=500, rho=0.7, seed=42)
        assert config.n == 50
        assert config.p == 500
        assert config.rho == 0.7
        assert config.seed == 42

    def test_invalid_parameters(self):
        """Test that invalid parameters raise errors."""
        with pytest.raises(ValueError):
            SimulationConfig(n=-1, p=100)  # n must be positive
        
        with pytest.raises(ValueError):
            SimulationConfig(n=100, p=-1)  # p must be positive
        
        with pytest.raises(ValueError):
            SimulationConfig(n=100, p=1000, rho=1.5)  # rho must be in [0, 1]

class TestSyntheticDataset:
    """Tests for SyntheticDataset class."""

    def test_dataset_creation(self):
        """Test that a dataset can be created and has expected properties."""
        config = SimulationConfig(n=100, p=100, rho=0.5, seed=42)
        dataset = SyntheticDataset(config)
        
        assert dataset.data.shape == (100, 100)
        assert dataset.config.n == 100
        assert dataset.config.p == 100
        assert dataset.seed == 42

    def test_data_generation_determinism(self):
        """Test that same seed produces same data."""
        config1 = SimulationConfig(n=50, p=50, rho=0.3, seed=123)
        config2 = SimulationConfig(n=50, p=50, rho=0.3, seed=123)
        
        dataset1 = SyntheticDataset(config1)
        dataset2 = SyntheticDataset(config2)
        
        assert np.array_equal(dataset1.data, dataset2.data)

    def test_different_seeds_different_data(self):
        """Test that different seeds produce different data."""
        config1 = SimulationConfig(n=50, p=50, rho=0.3, seed=123)
        config2 = SimulationConfig(n=50, p=50, rho=0.3, seed=456)
        
        dataset1 = SyntheticDataset(config1)
        dataset2 = SyntheticDataset(config2)
        
        assert not np.array_equal(dataset1.data, dataset2.data)

class TestMemoryMonitor:
    """Tests for MemoryMonitor class."""

    def test_memory_monitor_creation(self):
        """Test that memory monitor can be created."""
        monitor = MemoryMonitor(threshold_mb=6000)
        assert monitor.threshold_mb == 6000

    def test_memory_monitor_warning(self, caplog):
        """Test that warning is logged when memory exceeds threshold."""
        # Set a very low threshold to trigger warning
        monitor = MemoryMonitor(threshold_mb=1)
        
        with caplog.at_level('WARNING'):
            monitor.check_memory()
            # Should log a warning since we're above 1MB
            assert any('Memory usage' in record.message for record in caplog.records)

    def test_memory_monitor_no_warning(self, caplog):
        """Test that no warning when memory is below threshold."""
        # Set a very high threshold
        monitor = MemoryMonitor(threshold_mb=100000)
        
        with caplog.at_level('WARNING'):
            monitor.check_memory()
            # Should not log a warning
            assert not any('Memory usage' in record.message for record in caplog.records)

class TestSimulationOrchestrator:
    """Tests for SimulationOrchestrator class."""

    def test_orchestrator_creation(self):
        """Test that orchestrator can be created."""
        from utils.simulation import SimulationOrchestrator
        orchestrator = SimulationOrchestrator()
        assert orchestrator is not None

    def test_parameter_sweep_generation(self):
        """Test that parameter sweep generates expected combinations."""
        from utils.simulation import SimulationOrchestrator
        orchestrator = SimulationOrchestrator()
        
        n_values = [50, 100]
        p_values = [100, 200]
        rho_values = [0.3, 0.7]
        
        params = orchestrator.generate_parameter_sweep(n_values, p_values, rho_values, n_seeds=2)
        
        # Expected: 2 * 2 * 2 * 2 = 16 combinations
        assert len(params) == 16

        # Check that all combinations are present
        n_set = set(p['n'] for p in params)
        p_set = set(p['p'] for p in params)
        rho_set = set(p['rho'] for p in params)
        
        assert n_set == set(n_values)
        assert p_set == set(p_values)
        assert rho_set == set(rho_values)
