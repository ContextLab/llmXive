"""
Unit tests for configuration loading and validation.
Ensures config.yaml is readable and contains required keys.
"""
import pytest
import yaml
import os
from pathlib import Path

# Helper to load config from the project root
def load_config():
    config_path = Path(__file__).parent.parent.parent / "config.yaml"
    if not config_path.exists():
        pytest.fail("config.yaml not found in project root")
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)

def test_config_exists():
    """Test that config.yaml exists."""
    config_path = Path(__file__).parent.parent.parent / "config.yaml"
    assert config_path.exists(), "config.yaml must exist"

def test_config_loads():
    """Test that config.yaml is valid YAML."""
    config = load_config()
    assert isinstance(config, dict), "Config must be a dictionary"

def test_required_sections_exist():
    """Test that all required top-level sections exist."""
    config = load_config()
    required_sections = ["project", "paths", "qc", "atlases", "data_sources"]
    for section in required_sections:
        assert section in config, f"Missing required section: {section}"

def test_motion_threshold_value():
    """Test that motion threshold is set to 3.0mm per FR-002."""
    config = load_config()
    threshold = config["qc"]["motion_threshold_mm"]
    assert threshold == 3.0, f"Motion threshold must be 3.0, got {threshold}"

def test_min_subjects_required():
    """Test that min subjects required is set (FR-009)."""
    config = load_config()
    min_subjects = config["qc"]["min_subjects_required"]
    assert min_subjects == 10, f"Min subjects must be 10, got {min_subjects}"

def test_data_paths_exist():
    """Test that data paths are defined."""
    config = load_config()
    paths = config["paths"]["data"]
    assert "raw" in paths
    assert "processed" in paths
    assert "results" in paths
    assert "figures" in paths

def test_atlas_configuration():
    """Test that atlas configuration is present."""
    config = load_config()
    atlases = config["atlases"]
    assert "functional_rois" in atlases
    rois = atlases["functional_rois"]
    roi_names = [r["name"] for r in rois]
    assert "PCC" in roi_names
    assert "mPFC" in roi_names
    assert "Angular" in roi_names

def test_data_source_openneuro():
    """Test OpenNeuro dataset configuration."""
    config = load_config()
    source = config["data_sources"]["openneuro"]
    assert source["dataset_id"] == "ds000030"
    assert "events_required" in source