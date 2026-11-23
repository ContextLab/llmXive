"""
Unit tests for code/config.py
Verifies configuration loading and mode selection.
"""
import pytest
from pathlib import Path
import sys

# Ensure imports work from tests/
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import RunMode, Config

def test_run_mode_enum():
    """Test that RunMode enum has expected values."""
    assert RunMode.REAL == "REAL"
    assert RunMode.SYNTHETIC == "SYNTHETIC"
    assert RunMode.MIXED == "MIXED"

def test_config_default_paths():
    """Test that Config initializes with correct default paths."""
    config = Config()
    
    # Check that paths are Path objects
    assert isinstance(config.data_dir, Path)
    assert isinstance(config.raw_dir, Path)
    assert isinstance(config.processed_dir, Path)
    
    # Check that paths are under the expected root (assumed to be 'data')
    assert config.data_dir.name == "data"
    assert config.raw_dir.name == "raw"
    assert config.processed_dir.name == "processed"

def test_config_mode_selection():
    """Test that Config can be initialized with a specific mode."""
    config = Config(mode=RunMode.SYNTHETIC)
    assert config.mode == RunMode.SYNTHETIC

def test_config_output_paths():
    """Test that output paths are correctly constructed."""
    config = Config()
    audit_log = config.audit_log_path
    
    assert audit_log.name == "audit_log.json"
    assert audit_log.parent.name == "data"
