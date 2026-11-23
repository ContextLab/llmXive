"""Unit tests for training configuration."""
import pytest
import os
from unittest.mock import patch
from model.train_config import TrainingConfig, load_config_from_args


class MockArgs:
    """Mock argparse namespace for testing."""
    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)


def test_default_config():
    """Test that default values are set correctly."""
    config = TrainingConfig()
    assert config.hidden_dim == 64
    assert config.num_layers == 3
    assert config.epochs == 100
    assert config.batch_size == 32
    assert config.learning_rate == 0.001
    assert config.early_stopping_patience == 10
    assert config.cpu_only is True
    assert config.max_memory_gb == 7.0


def test_config_to_dict():
    """Test conversion to dictionary."""
    config = TrainingConfig(epochs=50, batch_size=16)
    config_dict = config.to_dict()
    assert isinstance(config_dict, dict)
    assert config_dict["epochs"] == 50
    assert config_dict["batch_size"] == 16
    assert "disclaimer" in config_dict


def test_load_config_from_args():
    """Test loading config from arguments."""
    args = MockArgs(
        epochs=200,
        patience=5,
        batch_size=64,
        lr=0.01,
        data_path="data/test.parquet",
        split_path="data/split.json"
    )
    config = load_config_from_args(args)
    assert config.epochs == 200
    assert config.early_stopping_patience == 5
    assert config.batch_size == 64
    assert config.learning_rate == 0.01
    assert config.data_path == "data/test.parquet"
    assert config.split_path == "data/split.json"


def test_load_config_from_args_missing():
    """Test that missing args don't crash and use defaults."""
    args = MockArgs(epochs=50)
    config = load_config_from_args(args)
    assert config.epochs == 50
    assert config.early_stopping_patience == 10  # default
    assert config.batch_size == 32  # default


@patch.dict(os.environ, {"TRAIN_EPOCHS": "150", "TRAIN_LR": "0.0005"})
def test_env_overrides_post_init():
    """Test that environment variables override defaults in __post_init__."""
    config = TrainingConfig()
    assert config.epochs == 150
    assert config.learning_rate == 0.0005


@patch.dict(os.environ, {"CUDA_VISIBLE_DEVICES": "0"})
def test_cpu_only_forces_cuda_disabled():
    """Test that cpu_only=True clears CUDA_VISIBLE_DEVICES."""
    # Note: In __post_init__, if cpu_only is True, it sets CUDA_VISIBLE_DEVICES to ""
    # This test verifies the logic path exists
    config = TrainingConfig(cpu_only=True)
    assert os.environ.get("CUDA_VISIBLE_DEVICES") == ""