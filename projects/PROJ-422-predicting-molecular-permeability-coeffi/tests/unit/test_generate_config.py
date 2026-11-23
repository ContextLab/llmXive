"""
Unit tests for the generate_config.py script.
"""
import pytest
import yaml
import os
import sys
from pathlib import Path
import tempfile
import shutil

# Add the project root to the path to allow imports
project_root = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from code.generate_config import generate_config

class TestGenerateConfig:
    def test_config_generation_creates_file(self, tmp_path):
        """Test that the config file is created."""
        config_path = tmp_path / "config.yaml"
        generate_config(config_path)
        assert config_path.exists(), "config.yaml was not created"

    def test_config_structure(self, tmp_path):
        """Test that the config file contains expected keys."""
        config_path = tmp_path / "config.yaml"
        generate_config(config_path)
        
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
        
        # Check top-level keys
        assert "pipeline" in config
        assert "data" in config
        assert "thresholds" in config
        assert "modeling" in config
        assert "evaluation" in config
        assert "logging" in config

    def test_threshold_values(self, tmp_path):
        """Test that threshold values are set correctly."""
        config_path = tmp_path / "config.yaml"
        generate_config(config_path)
        
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
        
        thresholds = config["thresholds"]
        assert thresholds["bias_threshold"] == 0.85
        assert thresholds["retention_threshold"] == 0.95
        assert thresholds["stratification_diff_threshold"] == 0.05

    def test_proxy_target_columns(self, tmp_path):
        """Test that proxy target columns are set correctly."""
        config_path = tmp_path / "config.yaml"
        generate_config(config_path)
        
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
        
        modeling = config["modeling"]
        assert modeling["proxy_target_columns"] == ["logP", "calculated_logP"]

    def test_staged_mode_default(self, tmp_path):
        """Test that staged_mode defaults to False."""
        config_path = tmp_path / "config.yaml"
        generate_config(config_path)
        
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
        
        modeling = config["modeling"]
        assert modeling["staged_mode"] is False

    def test_yaml_valid_syntax(self, tmp_path):
        """Test that the generated file is valid YAML."""
        config_path = tmp_path / "config.yaml"
        generate_config(config_path)
        
        # This will raise an exception if the YAML is invalid
        with open(config_path, 'r') as f:
            yaml.safe_load(f)
        
        # If we get here, the YAML is valid
        assert True