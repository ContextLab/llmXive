"""
Unit tests for code/utils/config.py
"""
import os
import tempfile
from pathlib import Path

import pytest
import numpy as np

# Import from the project
from code.utils.config import Config, get_config, set_seed, reset_config, load_config_from_yaml

@pytest.fixture(autouse=True)
def reset_config_env():
    """Ensure config is reset before and after each test."""
    reset_config()
    # Clear env vars that might interfere
    if "CONFIG_PATH" in os.environ:
        del os.environ["CONFIG_PATH"]
    if "SEED" in os.environ:
        del os.environ["SEED"]
    if "PROJECT_ROOT" in os.environ:
        del os.environ["PROJECT_ROOT"]
    if "DATA_DIR" in os.environ:
        del os.environ["DATA_DIR"]
    yield
    reset_config()

def test_config_defaults():
    """Test that default config values are loaded when no file/env is provided."""
    cfg = get_config()
    assert cfg.seed == 42
    assert cfg.device == "cpu"
    assert cfg.n_cores == 1
    assert cfg.motion_threshold_mm == 3.0
    assert cfg.convergence_rate_threshold == 0.90

def test_config_from_env():
    """Test loading config from environment variables."""
    os.environ["SEED"] = "123"
    os.environ["MOTION_THRESHOLD_MM"] = "2.5"
    os.environ["PROJECT_ROOT"] = "/tmp/test_proj"
    os.environ["DATA_DIR"] = "/tmp/test_data"
    
    cfg = get_config()
    assert cfg.seed == 123
    assert cfg.motion_threshold_mm == 2.5
    assert str(cfg.project_root) == "/tmp/test_proj"
    assert str(cfg.data_dir) == "/tmp/test_data"

def test_config_from_yaml(tmp_path):
    """Test loading config from a YAML file."""
    yaml_content = """
    seed: 999
    device: "cuda"
    n_cores: 4
    motion_threshold_mm: 1.5
    """
    yaml_file = tmp_path / "test_config.yaml"
    yaml_file.write_text(yaml_content)
    
    os.environ["CONFIG_PATH"] = str(yaml_file)
    cfg = get_config()
    
    assert cfg.seed == 999
    assert cfg.device == "cuda"
    assert cfg.n_cores == 4
    assert cfg.motion_threshold_mm == 1.5

def test_set_seed():
    """Test that set_seed affects numpy and random state."""
    set_seed(42)
    val1 = np.random.rand()
    
    set_seed(42)
    val2 = np.random.rand()
    
    assert val1 == val2

def test_config_paths():
    """Test that derived paths are correctly constructed."""
    cfg = get_config()
    assert (cfg.data_dir / "raw") == cfg.data_raw
    assert (cfg.data_dir / "processed") == cfg.data_processed
    assert cfg.state_dir == cfg.project_root / "state"

def test_load_config_from_yaml_missing():
    """Test error handling for missing YAML file."""
    with pytest.raises(FileNotFoundError):
        load_config_from_yaml("/nonexistent/path/config.yaml")