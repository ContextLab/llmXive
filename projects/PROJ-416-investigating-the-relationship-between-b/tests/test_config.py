"""
Unit tests for code/config.py
"""
import os
import pytest
from pathlib import Path
from code.config import Config

def test_config_initialization_with_env():
    """Test Config initialization with environment variables."""
    # Set a temporary environment variable for testing
    os.environ["OPENNEURO_ID"] = "ds000001"
    os.environ["RANDOM_SEED"] = "123"
    
    config = Config()
    
    assert config.openneuro_id == "ds000001"
    assert config.seed == 123
    assert config.project_root.exists()
    
    # Cleanup
    del os.environ["OPENNEURO_ID"]
    del os.environ["RANDOM_SEED"]

def test_config_missing_openneuro_id():
    """Test Config raises error when OPENNEURO_ID is missing."""
    # Ensure the env var is not set
    if "OPENNEURO_ID" in os.environ:
        del os.environ["OPENNEURO_ID"]
    
    with pytest.raises(ValueError, match="OPENNEURO_ID is not set"):
        Config()

def test_config_directories_created():
    """Test that Config creates necessary directories."""
    os.environ["OPENNEURO_ID"] = "ds_test"
    config = Config()
    
    assert config.data_root.exists()
    assert (config.data_root / "raw").exists()
    assert (config.data_root / "processed").exists()
    assert (config.data_root / "metrics").exists()
    assert (config.data_root / "metrics" / "matrices").exists()
    assert config.reports_root.exists()
    assert config.logs_root.exists()
    
    del os.environ["OPENNEURO_ID"]

def test_config_motion_thresholds():
    """Test that motion thresholds are set correctly."""
    os.environ["OPENNEURO_ID"] = "ds_test"
    config = Config()
    
    assert config.motion_threshold_translation_mm == 3.0
    assert config.motion_threshold_rotation_deg == 3.0
    
    del os.environ["OPENNEURO_ID"]

def test_config_statistical_defaults():
    """Test that statistical configuration defaults are correct."""
    os.environ["OPENNEURO_ID"] = "ds_test"
    config = Config()
    
    assert config.alpha == 0.05
    assert config.fdr_method == "fdr_bh"
    assert config.vif_threshold == 5.0
    assert config.ridge_lambda == 1.0
    assert config.min_effect_size_f2 == 0.15
    assert config.target_power == 0.8
    
    del os.environ["OPENNEURO_ID"]