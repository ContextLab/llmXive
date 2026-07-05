"""
Unit tests for the configuration manager.
"""
import os
import tempfile
from pathlib import Path

import pytest

from src.config import Config, get_config


def test_config_defaults():
    """Test that default configuration values are set correctly."""
    cfg = Config()
    assert cfg.seed == 42
    assert cfg.device == "cpu"
    assert cfg.learning_rate == 1e-3
    assert cfg.batch_size == 32
    assert cfg.n_folds == 5


def test_config_paths_initialization():
    """Test that derived paths are correctly initialized."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        # Create a mock config with a specific root
        mock_root = Path(tmp_dir)
        cfg = Config(project_root=mock_root)
        
        expected_data = mock_root / "data" / "raw"
        expected_processed = mock_root / "data" / "processed"
        expected_results = mock_root / "results"
        expected_models = mock_root / "models"
        expected_contracts = mock_root / "contracts"
        expected_figures = mock_root / "figures"
        
        assert cfg.data_dir == expected_data
        assert cfg.processed_data_dir == expected_processed
        assert cfg.results_dir == expected_results
        assert cfg.models_dir == expected_models
        assert cfg.contracts_dir == expected_contracts
        assert cfg.figures_dir == expected_figures


def test_config_device_forces_cpu():
    """Test that device is forced to CPU."""
    cfg = Config()
    device = cfg.set_device()
    assert device.type == "cpu"
    assert os.environ.get("CUDA_VISIBLE_DEVICES") == "-1"


def test_config_seed_all():
    """Test that seed_all sets seeds for random, numpy, and torch."""
    cfg = Config(seed=12345)
    cfg.seed_all()
    # If we run again, it should be deterministic (basic check)
    import random
    import numpy as np
    import torch
    
    val1 = random.random()
    val2 = np.random.random()
    val3 = torch.rand(1).item()
    
    cfg.seed_all()
    
    assert random.random() == val1
    assert np.random.random() == val2
    assert torch.rand(1).item() == val3


def test_config_to_dict():
    """Test conversion to dictionary."""
    cfg = Config()
    d = cfg.to_dict()
    
    assert isinstance(d, dict)
    assert "seed" in d
    assert "learning_rate" in d
    # Paths should be strings in the dict
    assert isinstance(d["data_dir"], str)


def test_get_config_singleton():
    """Test that get_config returns the global instance."""
    cfg1 = get_config()
    cfg2 = get_config()
    assert cfg1 is cfg2