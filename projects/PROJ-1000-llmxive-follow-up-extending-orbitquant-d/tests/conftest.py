"""
Pytest configuration and fixtures.
"""
import pytest
import torch
from pathlib import Path
from config import Config

@pytest.fixture
def config():
    """Provide a default configuration for tests."""
    return Config()

@pytest.fixture
def temp_data_dir(tmp_path):
    """Provide a temporary data directory for tests."""
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    return data_dir

@pytest.fixture
def cpu_device():
    """Force tests to run on CPU."""
    return "cpu"

@pytest.fixture
def dummy_tensor():
    """Provide a dummy tensor for tests."""
    return torch.randn(2, 3, 4)
