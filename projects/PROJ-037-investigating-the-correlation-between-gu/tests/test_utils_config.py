"""
Unit tests for the configuration utility.
"""
import pytest
from pathlib import Path
from unittest.mock import patch
import tempfile
import shutil

from code.utils.config import Config, get_config

@pytest.fixture
def temp_project_root():
    """Create a temporary directory to simulate project root."""
    temp_dir = tempfile.mkdtemp()
    yield Path(temp_dir)
    shutil.rmtree(temp_dir)

def test_config_initialization(temp_project_root):
    """Test that Config creates necessary directories."""
    config = Config(project_root=temp_project_root)

    assert config.project_root == temp_project_root
    assert config.data_root.exists()
    assert config.code_root.exists()
    assert config.logs_root.exists()

def test_get_path(temp_project_root):
    """Test path resolution."""
    config = Config(project_root=temp_project_root)
    resolved = config.get_path("data/processed/test.csv")

    assert resolved == temp_project_root / "data/processed/test.csv"

def test_to_dict(temp_project_root):
    """Test configuration export."""
    config = Config(project_root=temp_project_root)
    config_dict = config.to_dict()

    assert "project_root" in config_dict
    assert "data_root" in config_dict
    assert config_dict["project_root"] == str(temp_project_root)

def test_singleton_get_config():
    """Test that get_config returns the same instance."""
    # Reset global config for clean test
    import code.utils.config as config_module
    original_config = config_module._global_config
    config_module._global_config = None

    try:
        cfg1 = get_config()
        cfg2 = get_config()
        assert cfg1 is cfg2
    finally:
        config_module._global_config = original_config
