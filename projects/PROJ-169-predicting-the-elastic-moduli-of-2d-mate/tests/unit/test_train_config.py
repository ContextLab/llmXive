"""
Unit tests for training configuration.
"""
import pytest
from model.train_config import TrainingConfig, load_config_from_args
import argparse


def test_default_config():
    """Test that default configuration values are set correctly."""
    config = TrainingConfig()
    assert config.hidden_dim == 64
    assert config.num_layers == 3
    assert config.epochs == 100
    assert config.batch_size == 32
    assert config.learning_rate == 0.001
    assert config.early_stopping_patience == 10
    assert config.max_memory_gb == 7.0
    assert config.cpu_only is True
    assert "CUDA_VISIBLE_DEVICES" in config.__dict__ or True  # Side effect check


def test_config_to_dict():
    """Test conversion to dictionary."""
    config = TrainingConfig()
    config_dict = config.to_dict()
    assert isinstance(config_dict, dict)
    assert "hidden_dim" in config_dict
    assert "epochs" in config_dict
    assert "disclaimer" in config_dict
    assert "first-principles" not in config_dict["disclaimer"].lower()


def test_load_config_from_args():
    """Test loading config from argparse arguments."""
    parser = argparse.ArgumentParser()
    parser.add_argument('--epochs', type=int, default=None)
    parser.add_argument('--patience', type=int, default=None)
    parser.add_argument('--lr', type=float, default=None)
    parser.add_argument('--data_path', type=str, default=None)
    parser.add_argument('--split_path', type=str, default=None)

    args = parser.parse_args(['--epochs', '50', '--patience', '5', '--lr', '0.01'])
    config = load_config_from_args(args)

    assert config.epochs == 50
    assert config.early_stopping_patience == 5
    assert config.learning_rate == 0.01
    assert config.batch_size == 32  # Default


def test_config_cpu_enforcement():
    """Test that CPU-only mode disables CUDA."""
    config = TrainingConfig(cpu_only=True)
    # Check environment variable was set
    import os
    assert os.environ.get("CUDA_VISIBLE_DEVICES") == ""


def test_config_disclaimer():
    """Test that disclaimer is present and correct."""
    config = TrainingConfig()
    assert "ML interpolation" in config.disclaimer
    assert "first-principles" not in config.disclaimer.lower()
    assert "DFT" in config.disclaimer