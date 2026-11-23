"""
Unit tests for experiment grid configuration.
"""

import pytest
import json
import os
from pathlib import Path
import tempfile

from experiments.grid_config import GridConfig, ExperimentConfig, create_default_grid


class TestExperimentConfig:
    """Tests for the ExperimentConfig dataclass."""

    def test_create_config(self):
        """Test basic instantiation of ExperimentConfig."""
        cfg = ExperimentConfig(alpha=0.5, horizon=3, experiment_id="test_001")
        assert cfg.alpha == 0.5
        assert cfg.horizon == 3
        assert cfg.experiment_id == "test_001"
        assert cfg.seed == 42  # Default seed

    def test_to_dict(self):
        """Test conversion to dictionary."""
        cfg = ExperimentConfig(
            alpha=0.7, horizon=4, experiment_id="test_002", seed=123
        )
        d = cfg.to_dict()
        assert d["alpha"] == 0.7
        assert d["horizon"] == 4
        assert d["experiment_id"] == "test_002"
        assert d["seed"] == 123

    def test_to_json_roundtrip(self):
        """Test JSON serialization and deserialization."""
        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = os.path.join(tmpdir, "config.json")
            cfg = ExperimentConfig(alpha=0.9, horizon=5, experiment_id="test_003")
            cfg.to_json(filepath)

            assert os.path.exists(filepath)
            with open(filepath, 'r') as f:
                data = json.load(f)
            
            assert data["alpha"] == 0.9
            assert data["horizon"] == 5
            assert data["experiment_id"] == "test_003"


class TestGridConfig:
    """Tests for the GridConfig class."""

    def test_default_grid_initialization(self):
        """Test that default grid has expected values."""
        grid = GridConfig()
        assert grid.alphas == [0.1, 0.3, 0.5, 0.7, 0.9]
        assert grid.horizons == [1, 2, 3, 4, 5]
        assert grid.base_seed == 42

    def test_custom_grid_initialization(self):
        """Test grid with custom parameters."""
        grid = GridConfig(
            alphas=[0.2, 0.8],
            horizons=[2, 4],
            base_seed=99
        )
        assert grid.alphas == [0.2, 0.8]
        assert grid.horizons == [2, 4]
        assert grid.base_seed == 99

    def test_generate_grid_count(self):
        """Test that grid generates correct number of configurations."""
        grid = GridConfig(alphas=[0.1, 0.5], horizons=[1, 2, 3])
        configs = list(grid.generate_grid())
        assert len(configs) == 2 * 3  # 6 combinations

    def test_generate_grid_uniqueness(self):
        """Test that all generated configurations are unique."""
        grid = GridConfig(alphas=[0.1, 0.5], horizons=[1, 2])
        configs = list(grid.generate_grid())
        ids = [c.experiment_id for c in configs]
        assert len(ids) == len(set(ids))  # All IDs are unique

    def test_generate_grid_seeds_differ(self):
        """Test that each configuration gets a unique seed."""
        grid = GridConfig(alphas=[0.1, 0.5], horizons=[1, 2], base_seed=100)
        configs = list(grid.generate_grid())
        seeds = [c.seed for c in configs]
        assert len(seeds) == len(set(seeds))  # All seeds are unique

    def test_get_grid_summary(self):
        """Test grid summary generation."""
        grid = GridConfig(alphas=[0.1, 0.5], horizons=[1, 2])
        summary = grid.get_grid_summary()
        assert summary["total_experiments"] == 4
        assert summary["alpha_values"] == [0.1, 0.5]
        assert summary["horizon_values"] == [1, 2]

    def test_save_config_summary(self):
        """Test saving grid summary to file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = os.path.join(tmpdir, "summary.json")
            grid = GridConfig(alphas=[0.1], horizons=[1])
            grid.save_config_summary(filepath)
            
            assert os.path.exists(filepath)
            with open(filepath, 'r') as f:
                data = json.load(f)
            assert data["total_experiments"] == 1

    def test_empty_alphas_raises(self):
        """Test that empty alpha list raises ValueError."""
        with pytest.raises(ValueError):
            GridConfig(alphas=[], horizons=[1])

    def test_empty_horizons_raises(self):
        """Test that empty horizon list raises ValueError."""
        with pytest.raises(ValueError):
            GridConfig(alphas=[0.1], horizons=[])


class TestCreateDefaultGrid:
    """Tests for the factory function."""

    def test_returns_grid_config(self):
        """Test that factory returns a GridConfig instance."""
        grid = create_default_grid()
        assert isinstance(grid, GridConfig)

    def test_default_values(self):
        """Test that factory uses default values."""
        grid = create_default_grid()
        assert grid.alphas == [0.1, 0.3, 0.5, 0.7, 0.9]
        assert grid.horizons == [1, 2, 3, 4, 5]