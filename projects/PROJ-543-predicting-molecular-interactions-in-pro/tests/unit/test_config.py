"""
Unit tests for configuration management module.
"""

import os
import pytest
import random
import numpy as np
import torch

from utils.config import (
    Hyperparameters,
    EnvironmentConfig,
    set_seed,
    get_config,
    load_config_from_env,
    initialize_environment,
    DEFAULT_SEED,
)


class TestHyperparameters:
    """Tests for Hyperparameters dataclass."""

    def test_default_values(self):
        """Test that default values are set correctly."""
        hp = Hyperparameters()
        
        assert hp.seed == DEFAULT_SEED
        assert hp.hidden_dim == 256
        assert hp.num_layers == 3
        assert hp.dropout == 0.1
        assert hp.learning_rate == 1e-3
        assert hp.batch_size == 32
        assert hp.resolution_threshold == 2.5
        assert hp.distance_cutoff == 5.0

    def test_to_dict(self):
        """Test conversion to dictionary."""
        hp = Hyperparameters(seed=123, hidden_dim=512)
        d = hp.to_dict()
        
        assert d["seed"] == 123
        assert d["hidden_dim"] == 512
        assert "device" in d
        assert "num_layers" in d

    def test_custom_values(self):
        """Test setting custom values."""
        hp = Hyperparameters(
            seed=999,
            hidden_dim=512,
            learning_rate=0.01,
            resolution_threshold=3.0,
        )
        
        assert hp.seed == 999
        assert hp.hidden_dim == 512
        assert hp.learning_rate == 0.01
        assert hp.resolution_threshold == 3.0


class TestEnvironmentConfig:
    """Tests for EnvironmentConfig dataclass."""

    def test_default_paths(self):
        """Test that default paths are generated."""
        env_config = EnvironmentConfig()
        
        assert "data" in env_config.data_raw_dir
        assert "raw" in env_config.data_raw_dir
        assert "processed" in env_config.data_processed_dir
        assert "results" in env_config.data_results_dir

    def test_env_var_override(self, tmp_path):
        """Test that environment variables override defaults."""
        # Set environment variable
        os.environ["PROJECT_ROOT"] = str(tmp_path)
        
        try:
            env_config = EnvironmentConfig()
            
            assert env_config.data_raw_dir == str(tmp_path / "data" / "raw")
            assert env_config.data_processed_dir == str(tmp_path / "data" / "processed")
        finally:
            # Clean up
            del os.environ["PROJECT_ROOT"]

    def test_directories_created(self, tmp_path):
        """Test that directories are created on initialization."""
        os.environ["PROJECT_ROOT"] = str(tmp_path)
        
        try:
            env_config = EnvironmentConfig()
            
            # Check that directories exist
            assert os.path.exists(env_config.data_raw_dir)
            assert os.path.exists(env_config.data_processed_dir)
            assert os.path.exists(env_config.data_results_dir)
        finally:
            del os.environ["PROJECT_ROOT"]

    def test_no_env_var_uses_project_root(self):
        """Test fallback to project_root when env var not set."""
        # Ensure env var is not set
        if "PROJECT_ROOT" in os.environ:
            del os.environ["PROJECT_ROOT"]
        
        env_config = EnvironmentConfig()
        
        # Should use project_root (defaults to parent of utils.config)
        assert os.path.isabs(env_config.project_root)
        assert os.path.exists(env_config.project_root)

class TestSetSeed:
    """Tests for seed setting functionality."""

    def test_seed_python(self):
        """Test that Python random seed is set."""
        set_seed(42)
        val1 = random.random()
        
        set_seed(42)
        val2 = random.random()
        
        assert val1 == val2

    def test_seed_numpy(self):
        """Test that NumPy seed is set."""
        set_seed(42)
        val1 = np.random.rand()
        
        set_seed(42)
        val2 = np.random.rand()
        
        assert val1 == val2

    def test_seed_torch(self):
        """Test that PyTorch seed is set."""
        set_seed(42)
        val1 = torch.rand(1).item()
        
        set_seed(42)
        val2 = torch.rand(1).item()
        
        assert val1 == val2


class TestGetConfig:
    """Tests for get_config function."""

    def test_returns_tuple(self):
        """Test that get_config returns a tuple."""
        result = get_config()
        
        assert isinstance(result, tuple)
        assert len(result) == 2

    def test_returns_correct_types(self):
        """Test that correct types are returned."""
        hp, env_config = get_config()
        
        assert isinstance(hp, Hyperparameters)
        assert isinstance(env_config, EnvironmentConfig)

class TestLoadConfigFromEnv:
    """Tests for load_config_from_env function."""

    def test_env_overrides(self):
        """Test that environment variables override defaults."""
        os.environ["SEED"] = "999"
        os.environ["HIDDEN_DIM"] = "512"
        os.environ["LEARNING_RATE"] = "0.01"
        
        try:
            hp, _ = load_config_from_env()
            
            assert hp.seed == 999
            assert hp.hidden_dim == 512
            assert hp.learning_rate == 0.01
        finally:
            del os.environ["SEED"]
            del os.environ["HIDDEN_DIM"]
            del os.environ["LEARNING_RATE"]

    def test_missing_env_uses_defaults(self):
        """Test that missing env vars use defaults."""
        # Remove any existing env vars
        for key in ["SEED", "HIDDEN_DIM", "LEARNING_RATE"]:
            if key in os.environ:
                del os.environ[key]
        
        hp, _ = load_config_from_env()
        
        assert hp.seed == DEFAULT_SEED

class TestInitializeEnvironment:
    """Tests for initialize_environment function."""

    def test_sets_seed(self):
        """Test that initialize_environment sets the seed."""
        hp = initialize_environment(seed=42)
        
        assert hp.seed == 42

    def test_reproducibility(self):
        """Test that same seed produces same results."""
        hp1 = initialize_environment(seed=123)
        val1 = random.random()
        
        hp2 = initialize_environment(seed=123)
        val2 = random.random()
        
        assert val1 == val2

    def test_default_seed_from_config(self):
        """Test that default seed is used when not specified."""
        os.environ["SEED"] = "999"
        
        try:
            hp = initialize_environment()
            assert hp.seed == 999
        finally:
            del os.environ["SEED"]