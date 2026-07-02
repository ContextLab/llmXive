"""
Unit tests for the configuration loader module.
"""
import os
import sys
import yaml
import tempfile
from pathlib import Path
import pytest

# Add code directory to path for imports
code_dir = Path(__file__).parent.parent.parent / "code"
sys.path.insert(0, str(code_dir))

from config_loader import (
    load_preprocess_config,
    get_filter_bands,
    get_ica_settings,
    get_pseudocount,
    validate_config,
    _apply_defaults
)


class TestLoadPreprocessConfig:
    """Tests for load_preprocess_config function."""

    def test_load_from_default_path(self, tmp_path):
        """Test loading config from default path when file exists."""
        # Create a temporary config file
        processed_dir = tmp_path / "data" / "processed"
        processed_dir.mkdir(parents=True)
        
        config_content = {
            "filter_bands": {"low_cutoff": 1.0, "high_cutoff": 40.0},
            "ica_settings": {"n_components": 15},
            "pseudocount": 0.25
        }
        
        config_file = processed_dir / "preprocess.yaml"
        with open(config_file, 'w') as f:
            yaml.dump(config_content, f)
        
        # Mock get_project_root to return tmp_path
        import config_loader
        original_get_project_root = config_loader.get_project_root
        config_loader.get_project_root = lambda: tmp_path
        
        try:
            config = load_preprocess_config()
            assert config["filter_bands"]["low_cutoff"] == 1.0
            assert config["filter_bands"]["high_cutoff"] == 40.0
            assert config["ica_settings"]["n_components"] == 15
            assert config["pseudocount"] == 0.25
        finally:
            config_loader.get_project_root = original_get_project_root

    def test_load_from_custom_path(self, tmp_path):
        """Test loading config from a custom path."""
        config_content = {
            "filter_bands": {"low_cutoff": 0.5, "high_cutoff": 45.0},
            "pseudocount": 0.5
        }
        
        custom_config = tmp_path / "custom_config.yaml"
        with open(custom_config, 'w') as f:
            yaml.dump(config_content, f)
        
        config = load_preprocess_config(str(custom_config))
        assert config["filter_bands"]["low_cutoff"] == 0.5
        assert config["pseudocount"] == 0.5

    def test_missing_config_file_raises_error(self, tmp_path):
        """Test that missing config file raises FileNotFoundError."""
        import config_loader
        original_get_project_root = config_loader.get_project_root
        config_loader.get_project_root = lambda: tmp_path / "nonexistent"
        
        try:
            with pytest.raises(FileNotFoundError):
                load_preprocess_config()
        finally:
            config_loader.get_project_root = original_get_project_root

    def test_empty_config_uses_defaults(self, tmp_path):
        """Test that empty config file uses all default values."""
        processed_dir = tmp_path / "data" / "processed"
        processed_dir.mkdir(parents=True)
        
        config_file = processed_dir / "preprocess.yaml"
        with open(config_file, 'w') as f:
            f.write("")  # Empty file
        
        import config_loader
        original_get_project_root = config_loader.get_project_root
        config_loader.get_project_root = lambda: tmp_path
        
        try:
            config = load_preprocess_config()
            assert config["filter_bands"]["low_cutoff"] == 0.5
            assert config["ica_settings"]["n_components"] == 20
            assert config["pseudocount"] == 0.5
        finally:
            config_loader.get_project_root = original_get_project_root


class TestGetFilterBands:
    """Tests for get_filter_bands function."""

    def test_extract_filter_bands(self, tmp_path):
        """Test extraction of filter band parameters."""
        config = {
            "filter_bands": {
                "low_cutoff": 1.0,
                "high_cutoff": 40.0,
                "notch_freq": 50.0
            }
        }
        
        bands = get_filter_bands(config)
        assert bands["low_cutoff"] == 1.0
        assert bands["high_cutoff"] == 40.0
        assert bands["notch_freq"] == 50.0


class TestGetICASettings:
    """Tests for get_ica_settings function."""

    def test_extract_ica_settings(self, tmp_path):
        """Test extraction of ICA settings."""
        config = {
            "ica_settings": {
                "n_components": 25,
                "algorithm": "infomax",
                "random_state": 123,
                "max_iter": 1000
            }
        }
        
        ica = get_ica_settings(config)
        assert ica["n_components"] == 25
        assert ica["algorithm"] == "infomax"
        assert ica["random_state"] == 123
        assert ica["max_iter"] == 1000


class TestGetPseudocount:
    """Tests for get_pseudocount function."""

    def test_extract_pseudocount(self, tmp_path):
        """Test extraction of pseudocount value."""
        config = {"pseudocount": 0.75}
        assert get_pseudocount(config) == 0.75


class TestValidateConfig:
    """Tests for validate_config function."""

    def test_valid_config(self, tmp_path):
        """Test validation of a valid configuration."""
        config = {
            "filter_bands": {
                "low_cutoff": 0.5,
                "high_cutoff": 45.0,
                "notch_freq": 60.0
            },
            "ica_settings": {
                "n_components": 20,
                "max_iter": 500
            },
            "pseudocount": 0.5
        }
        
        errors = validate_config(config)
        assert len(errors) == 0

    def test_invalid_low_cutoff(self, tmp_path):
        """Test validation catches negative low_cutoff."""
        config = {
            "filter_bands": {
                "low_cutoff": -1.0,
                "high_cutoff": 45.0
            }
        }
        
        errors = validate_config(config)
        assert len(errors) > 0
        assert any("low_cutoff" in e for e in errors)

    def test_invalid_high_low_order(self, tmp_path):
        """Test validation catches high_cutoff <= low_cutoff."""
        config = {
            "filter_bands": {
                "low_cutoff": 50.0,
                "high_cutoff": 45.0
            }
        }
        
        errors = validate_config(config)
        assert len(errors) > 0
        assert any("high_cutoff" in e and "low_cutoff" in e for e in errors)

    def test_invalid_n_components(self, tmp_path):
        """Test validation catches non-positive n_components."""
        config = {
            "ica_settings": {
                "n_components": 0
            }
        }
        
        errors = validate_config(config)
        assert len(errors) > 0
        assert any("n_components" in e for e in errors)


class TestApplyDefaults:
    """Tests for _apply_defaults function."""

    def test_defaults_filled_for_missing_keys(self, tmp_path):
        """Test that missing keys get default values."""
        config = {}
        result = _apply_defaults(config)
        
        assert "filter_bands" in result
        assert "ica_settings" in result
        assert "pseudocount" in result
        assert result["pseudocount"] == 0.5
        assert result["ica_settings"]["n_components"] == 20

    def test_user_values_preserved(self, tmp_path):
        """Test that user-provided values override defaults."""
        config = {
            "pseudocount": 1.0,
            "ica_settings": {"n_components": 10}
        }
        result = _apply_defaults(config)
        
        assert result["pseudocount"] == 1.0
        assert result["ica_settings"]["n_components"] == 10
        assert result["ica_settings"]["algorithm"] == "fastica"  # default preserved