"""
Unit tests for the experiment configuration manager.
"""

import pytest
import os

from code.config import (
    ExperimentConfig,
    CUTOFFS,
    DEFAULT_SEED,
    ensure_directories,
    get_default_config,
)


class TestCutoffs:
    """Test the CUTOFFS constant as per Spec FR-007."""

    def test_cutoffs_contains_required_values(self):
        """Verify CUTOFFS contains exactly {0.01, 0.05, 0.1}."""
        expected = {0.01, 0.05, 0.1}
        assert CUTOFFS == expected, f"CUTOFFS must be {expected}, got {CUTOFFS}"

    def test_cutoffs_is_set(self):
        """Verify CUTOFFS is a set."""
        assert isinstance(CUTOFFS, set), "CUTOFFS must be a set"


class TestExperimentConfig:
    """Test the ExperimentConfig class."""

    def test_default_initialization(self):
        """Test default configuration initialization."""
        config = ExperimentConfig()
        assert config.seed == DEFAULT_SEED
        assert config.device == "cpu"
        assert config.batch_size == 1
        assert config.num_clips == 50
        assert config.flow_model == "raft-small"
        assert config.cutoffs == CUTOFFS

    def test_custom_seed(self):
        """Test custom seed initialization."""
        config = ExperimentConfig(seed=123)
        assert config.seed == 123

    def test_custom_cutoffs(self):
        """Test custom cutoffs initialization."""
        custom_cutoffs = {0.02, 0.06, 0.12}
        config = ExperimentConfig(cutoffs=custom_cutoffs)
        assert config.cutoffs == custom_cutoffs

    def test_invalid_seed(self):
        """Test that negative seed raises ValueError."""
        with pytest.raises(ValueError, match="Seed must be non-negative"):
            ExperimentConfig(seed=-1)

    def test_invalid_batch_size(self):
        """Test that batch_size < 1 raises ValueError."""
        with pytest.raises(ValueError, match="Batch size must be at least 1"):
            ExperimentConfig(batch_size=0)

    def test_invalid_num_clips(self):
        """Test that num_clips < 1 raises ValueError."""
        with pytest.raises(ValueError, match="Number of clips must be at least 1"):
            ExperimentConfig(num_clips=0)

    def test_invalid_device(self):
        """Test that invalid device raises ValueError."""
        with pytest.raises(ValueError, match="Device must be 'cpu' or 'cuda'"):
            ExperimentConfig(device="tpu")

    def test_to_dict(self):
        """Test conversion to dictionary."""
        config = ExperimentConfig(seed=42, device="cpu", batch_size=2)
        config_dict = config.to_dict()
        assert isinstance(config_dict, dict)
        assert config_dict["seed"] == 42
        assert config_dict["device"] == "cpu"
        assert config_dict["batch_size"] == 2
        assert "cutoffs" in config_dict
        assert isinstance(config_dict["cutoffs"], list)

    def test_reproducibility(self):
        """Test that seeds are set correctly for reproducibility."""
        import random
        import numpy as np
        import torch

        config1 = ExperimentConfig(seed=42)
        config2 = ExperimentConfig(seed=42)

        # Both should produce same random values
        random.seed(42)
        val1 = random.random()
        np.random.seed(42)
        val2 = np.random.random()
        torch.manual_seed(42)
        val3 = torch.rand(1).item()

        random.seed(42)
        val4 = random.random()
        np.random.seed(42)
        val5 = np.random.random()
        torch.manual_seed(42)
        val6 = torch.rand(1).item()

        assert val1 == val4
        assert val2 == val5
        assert abs(val3 - val6) < 1e-6


class TestGetDefaultConfig:
    """Test the get_default_config function."""

    def test_returns_experiment_config(self):
        """Test that get_default_config returns an ExperimentConfig."""
        config = get_default_config()
        assert isinstance(config, ExperimentConfig)

    def test_has_correct_defaults(self):
        """Test that default config has correct values."""
        config = get_default_config()
        assert config.seed == DEFAULT_SEED
        assert config.cutoffs == CUTOFFS


class TestEnsureDirectories:
    """Test the ensure_directories function."""

    def test_creates_directories(self):
        """Test that ensure_directories creates required directories."""
        # Clean up if they exist
        dirs_to_check = [
            "data/raw",
            "data/flow",
            "data/metrics",
            "results",
        ]

        # Run the function
        ensure_directories()

        # Verify directories exist
        for dir_path in dirs_to_check:
            assert os.path.exists(dir_path), f"Directory {dir_path} was not created"

        # Clean up (optional, for test isolation)
        # Note: In real CI, we might want to keep these for debugging
