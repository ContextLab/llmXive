import os
import tempfile
import yaml
import pytest
from pathlib import Path

# Add parent directory to path to allow imports from code/
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from config_loader import (
    load_preprocess_config,
    get_filter_bands,
    get_ica_settings,
    get_pseudocount,
    validate_config,
    DEFAULT_CONFIG
)

class TestConfigLoader:
    def test_load_default_config(self):
        """Test that loading a non-existent file returns defaults."""
        config = load_preprocess_config("/nonexistent/path.yaml")
        
        assert config["filter_bands"]["low_cut"] == 0.5
        assert config["filter_bands"]["high_cut"] == 45.0
        assert config["ica_settings"]["n_components"] == 20
        assert config["pseudocount"] == 0.5

    def test_load_custom_config(self):
        """Test loading a custom configuration file."""
        custom_config = {
            "filter_bands": {
                "low_cut": 1.0,
                "high_cut": 40.0,
                "order": 2
            },
            "pseudocount": 1.0
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(custom_config, f)
            temp_path = f.name
        
        try:
            config = load_preprocess_config(temp_path)
            
            # Custom values should be present
            assert config["filter_bands"]["low_cut"] == 1.0
            assert config["filter_bands"]["high_cut"] == 40.0
            assert config["pseudocount"] == 1.0
            
            # Default values should be merged in
            assert config["ica_settings"]["n_components"] == 20
        finally:
            os.unlink(temp_path)

    def test_get_filter_bands(self):
        """Test extraction of filter band settings."""
        config = load_preprocess_config()
        fb = get_filter_bands(config)
        
        assert "low_cut" in fb
        assert "high_cut" in fb
        assert "order" in fb
        assert isinstance(fb["low_cut"], float)

    def test_get_ica_settings(self):
        """Test extraction of ICA settings."""
        config = load_preprocess_config()
        ica = get_ica_settings(config)
        
        assert "n_components" in ica
        assert "method" in ica
        assert "random_state" in ica
        assert ica["method"] in ["fastica", "infomax", "picard"]

    def test_get_pseudocount(self):
        """Test extraction of pseudocount."""
        config = load_preprocess_config()
        pc = get_pseudocount(config)
        
        assert isinstance(pc, float)
        assert pc >= 0

    def test_validate_config_valid(self):
        """Test validation of a valid configuration."""
        config = {
            "filter_bands": {"low_cut": 0.5, "high_cut": 45.0, "order": 4},
            "ica_settings": {"n_components": 20, "method": "fastica"},
            "pseudocount": 0.5
        }
        
        errors = validate_config(config)
        assert len(errors) == 0

    def test_validate_config_invalid_filter_bands(self):
        """Test validation catches invalid filter bands."""
        config = {
            "filter_bands": {"low_cut": 50.0, "high_cut": 40.0, "order": 4},
            "ica_settings": {"n_components": 20, "method": "fastica"},
            "pseudocount": 0.5
        }
        
        errors = validate_config(config)
        assert any("low_cut" in e for e in errors)

    def test_validate_config_invalid_ica(self):
        """Test validation catches invalid ICA settings."""
        config = {
            "filter_bands": {"low_cut": 0.5, "high_cut": 45.0, "order": 4},
            "ica_settings": {"n_components": 0, "method": "invalid_method"},
            "pseudocount": 0.5
        }
        
        errors = validate_config(config)
        assert any("n_components" in e or "method" in e for e in errors)

    def test_validate_config_invalid_pseudocount(self):
        """Test validation catches negative pseudocount."""
        config = {
            "filter_bands": {"low_cut": 0.5, "high_cut": 45.0, "order": 4},
            "ica_settings": {"n_components": 20, "method": "fastica"},
            "pseudocount": -1.0
        }
        
        errors = validate_config(config)
        assert any("pseudocount" in e for e in errors)
