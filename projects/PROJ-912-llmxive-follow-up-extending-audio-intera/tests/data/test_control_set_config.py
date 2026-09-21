"""
Tests for control_set_config module.
"""
import os
import yaml
import tempfile
from pathlib import Path
import pytest

# Ensure code directory is in path if running from tests
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from data.control_set_config import get_control_classes, generate_control_config, CONTROL_CLASS_MAPPING

def test_get_control_classes_returns_list():
    """Test that get_control_classes returns a list of integers."""
    classes = get_control_classes()
    assert isinstance(classes, list)
    assert all(isinstance(c, int) for c in classes)
    assert len(classes) > 0

def test_control_classes_count():
    """Test that we have the expected number of control classes."""
    classes = get_control_classes()
    # We defined 10 classes in the mapping
    assert len(classes) == 10

def test_generate_control_config_creates_file():
    """Test that generate_control_config creates the YAML file."""
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / "test_config.yaml"
        config = generate_control_config(str(output_path))
        
        assert output_path.exists()
        assert config is not None
        assert "control_classes" in config
        assert "criteria" in config

def test_generate_control_config_content():
    """Test the content of the generated config."""
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / "test_config.yaml"
        config = generate_control_config(str(output_path))
        
        # Check criteria description mentions override
        assert "Plan.md" in config["criteria"]["source"]
        assert "Override" in config["criteria"]["source"]
        
        # Check classes match mapping values
        expected_classes = list(CONTROL_CLASS_MAPPING.values())
        assert sorted(config["control_classes"]) == sorted(expected_classes)
        
        # Check class names match mapping keys
        expected_names = list(CONTROL_CLASS_MAPPING.keys())
        assert sorted(config["class_names"]) == sorted(expected_names)

def test_file_is_valid_yaml():
    """Test that the generated file is valid YAML."""
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / "test_config.yaml"
        generate_control_config(str(output_path))
        
        # Should not raise an exception
        with open(output_path, 'r', encoding='utf-8') as f:
            loaded = yaml.safe_load(f)
        
        assert loaded is not None
        assert "control_classes" in loaded