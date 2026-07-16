import os
import yaml
import pytest

def test_config_exists_and_loads():
    """Verify config.yaml exists and is valid YAML."""
    config_path = os.path.join("code", "config.yaml")
    assert os.path.exists(config_path), f"Config file not found at {config_path}"
    
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    
    assert config is not None
    assert "qc" in config
    assert "paths" in config

def test_motion_threshold_is_correct():
    """Verify motion threshold matches FR-002 (3.0mm)."""
    config_path = os.path.join("code", "config.yaml")
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    
    threshold = config["qc"]["motion_threshold_mm"]
    assert threshold == 3.0, f"Motion threshold must be 3.0mm per FR-002, got {threshold}"

def test_required_paths_exist_in_config():
    """Verify all required path keys are present."""
    config_path = os.path.join("code", "config.yaml")
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    
    required_paths = ["data_raw", "data_processed", "data_results", "figures"]
    for path_key in required_paths:
        assert path_key in config["paths"], f"Missing path key: {path_key}"

def test_min_subjects_threshold():
    """Verify minimum subject count requirement (FR-009)."""
    config_path = os.path.join("code", "config.yaml")
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    
    assert config["qc"]["min_subjects_required"] == 10

def test_atlas_configuration():
    """Verify atlas settings are present."""
    config_path = os.path.join("code", "config.yaml")
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    
    assert "atlas" in config
    assert "name" in config["atlas"]
    assert "rois" in config["atlas"]