"""
Unit tests for code/config.py
"""
import pytest
from pathlib import Path
from code.config import RunMode, Config

def test_run_mode_enum():
    """Verify RunMode enum values."""
    assert RunMode.REAL.value == "real"
    assert RunMode.SYNTHETIC.value == "synthetic"
    assert RunMode.AUDIT.value == "audit"

def test_config_defaults():
    """Test default configuration initialization."""
    config = Config()
    assert config.mode == RunMode.REAL
    assert config.data_dir == Path("data")
    assert config.raw_dir == config.data_dir / "raw"
    assert config.processed_dir == config.data_dir / "processed"
    assert config.contracts_dir == config.data_dir / "contracts"

def test_config_paths_exist():
    """Test that config paths are resolved correctly."""
    config = Config(data_dir=Path("/tmp/test_data"))
    assert str(config.raw_dir) == "/tmp/test_data/raw"
