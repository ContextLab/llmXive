import os
import yaml
import tempfile
from pathlib import Path
import pytest

# Import the module under test
from config_loader import (
    load_preprocess_config,
    save_preprocess_config,
    get_filter_bands,
    get_ica_settings,
    get_pseudocount,
    get_alpha_band,
    get_epoch_config,
    get_matching_config,
    validate_config,
    DEFAULT_CONFIG
)
from config import get_project_root

class TestConfigLoader:
    """Tests for the configuration loader functionality."""

    def test_load_creates_default_config(self, tmp_path):
        """Test that loading a non-existent config creates it with defaults."""
        # Create a temp directory structure
        artifacts_dir = tmp_path / "artifacts"
        artifacts_dir.mkdir()
        config_path = artifacts_dir / "preprocess.yaml"

        # Mock get_project_root to use our temp dir
        import config_loader
        original_get_root = config_loader.get_project_root
        config_loader.get_project_root = lambda: tmp_path

        try:
            # Load config (should create file)
            config = load_preprocess_config()
            
            # Verify file was created
            assert config_path.exists(), "Config file should be created"
            
            # Verify defaults are present
            assert "filter_bands" in config
            assert "ica_settings" in config
            assert "pseudocount" in config
            assert config["pseudocount"] == 0.5
            
            # Verify specific default values
            assert config["filter_bands"]["low_pass"] == 45.0
            assert config["ica_settings"]["n_components"] == 20
        finally:
            config_loader.get_project_root = original_get_root

    def test_load_existing_config(self, tmp_path):
        """Test loading an existing config file."""
        artifacts_dir = tmp_path / "artifacts"
        artifacts_dir.mkdir()
        config_path = artifacts_dir / "preprocess.yaml"

        # Create a custom config
        custom_config = {
            "filter_bands": {"low_pass": 40.0, "high_pass": 2.0, "notch": 60.0},
            "ica_settings": {"n_components": 15, "method": "fastica"},
            "pseudocount": 1.0,
            "alpha_band": {"low": 8.0, "high": 12.0},
            "epoch_config": {"tmin": -0.1, "tmax": 0.5},
            "matching_config": {"strata_min_size": 10}
        }

        with open(config_path, 'w') as f:
            yaml.dump(custom_config, f)

        # Mock get_project_root
        import config_loader
        original_get_root = config_loader.get_project_root
        config_loader.get_project_root = lambda: tmp_path

        try:
            config = load_preprocess_config()
            
            # Verify custom values are loaded
            assert config["filter_bands"]["low_pass"] == 40.0
            assert config["pseudocount"] == 1.0
            assert config["ica_settings"]["n_components"] == 15
        finally:
            config_loader.get_project_root = original_get_root

    def test_save_preprocess_config(self, tmp_path):
        """Test saving a configuration to file."""
        artifacts_dir = tmp_path / "artifacts"
        artifacts_dir.mkdir()
        config_path = artifacts_dir / "preprocess.yaml"

        test_config = {
            "filter_bands": {"low_pass": 30.0, "high_pass": 1.5, "notch": 50.0},
            "ica_settings": {"n_components": 25, "method": "picard"},
            "pseudocount": 0.25
        }

        save_preprocess_config(test_config, config_path)
        
        assert config_path.exists()
        
        with open(config_path, 'r') as f:
            loaded = yaml.safe_load(f)
        
        assert loaded["filter_bands"]["low_pass"] == 30.0
        assert loaded["ica_settings"]["n_components"] == 25

    def test_getters(self, tmp_path):
        """Test the specific getter functions."""
        artifacts_dir = tmp_path / "artifacts"
        artifacts_dir.mkdir()
        config_path = artifacts_dir / "preprocess.yaml"

        # Create a full config
        full_config = DEFAULT_CONFIG.copy()
        full_config["filter_bands"]["low_pass"] = 100.0
        full_config["pseudocount"] = 2.0
        full_config["alpha_band"]["low"] = 9.0

        with open(config_path, 'w') as f:
            yaml.dump(full_config, f)

        import config_loader
        original_get_root = config_loader.get_project_root
        config_loader.get_project_root = lambda: tmp_path

        try:
            config = load_preprocess_config()
            
            assert get_filter_bands(config)["low_pass"] == 100.0
            assert get_pseudocount(config) == 2.0
            assert get_alpha_band(config)["low"] == 9.0
            assert get_ica_settings(config)["n_components"] == 20
            assert "tmin" in get_epoch_config(config)
            assert "strata_min_size" in get_matching_config(config)
        finally:
            config_loader.get_project_root = original_get_root

    def test_validate_config_success(self):
        """Test validation of a valid config."""
        assert validate_config(DEFAULT_CONFIG) is True

    def test_validate_config_missing_key(self):
        """Test validation fails with missing required key."""
        invalid_config = DEFAULT_CONFIG.copy()
        del invalid_config["filter_bands"]
        
        assert validate_config(invalid_config) is False

    def test_validate_config_missing_nested_key(self):
        """Test validation fails with missing nested key."""
        invalid_config = DEFAULT_CONFIG.copy()
        invalid_config["filter_bands"] = {"low_pass": 40.0}  # Missing high_pass, notch
        
        assert validate_config(invalid_config) is False
