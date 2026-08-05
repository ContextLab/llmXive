"""
Unit tests for the config_loader module.
"""

import os
import sys
import tempfile
import pytest
from pathlib import Path
import yaml

# Add parent directory to path to allow imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from utils.config_loader import (
    load_config,
    validate_ivt_config,
    get_validated_config,
    DEFAULT_IVT_DURATION_THRESHOLD_MS,
    CONFIG_PATH
)


class TestConfigLoader:
    """Tests for configuration loading and validation."""

    def test_load_config_valid_file(self, tmp_path):
        """Test loading a valid config file."""
        config_data = {
            'algorithms': {
                'ivt_duration_threshold': 150
            }
        }
        config_file = tmp_path / "config.yaml"
        with open(config_file, 'w') as f:
            yaml.dump(config_data, f)

        loaded = load_config(config_file)
        assert loaded == config_data

    def test_load_config_missing_file(self, tmp_path):
        """Test loading a non-existent config file raises error."""
        with pytest.raises(FileNotFoundError):
            load_config(tmp_path / "nonexistent.yaml")

    def test_validate_ivt_missing_threshold(self):
        """Test that missing threshold triggers default and warning."""
        config = {'algorithms': {}}
        validated, error = validate_ivt_config(config)
        
        assert error is None
        assert validated['algorithms']['ivt_duration_threshold'] == DEFAULT_IVT_DURATION_THRESHOLD_MS

    def test_validate_ivt_valid_threshold(self):
        """Test that valid threshold is accepted."""
        config = {'algorithms': {'ivt_duration_threshold': 200}}
        validated, error = validate_ivt_config(config)
        
        assert error is None
        assert validated['algorithms']['ivt_duration_threshold'] == 200

    def test_validate_ivt_non_integer_threshold(self):
        """Test that non-integer threshold raises error."""
        config = {'algorithms': {'ivt_duration_threshold': 100.5}}
        _, error = validate_ivt_config(config)
        
        assert error is not None
        assert "must be an integer" in error

    def test_validate_ivt_forbidden_velocity(self):
        """Test that velocity threshold raises error."""
        config = {
            'algorithms': {
                'ivt_duration_threshold': 100,
                'velocity_threshold': 30
            }
        }
        _, error = validate_ivt_config(config)
        
        assert error is not None
        assert "forbidden" in error.lower()
        assert "velocity" in error.lower()

    def test_validate_ivt_forbidden_dispersion(self):
        """Test that dispersion threshold raises error."""
        config = {
            'algorithms': {
                'ivt_duration_threshold': 100,
                'dispersion_threshold': 35
            }
        }
        _, error = validate_ivt_config(config)
        
        assert error is not None
        assert "forbidden" in error.lower()
        assert "dispersion" in error.lower()

    def test_validate_ivt_both_forbidden(self):
        """Test that both forbidden parameters raise error."""
        config = {
            'algorithms': {
                'ivt_duration_threshold': 100,
                'velocity_threshold': 30,
                'dispersion_threshold': 35
            }
        }
        _, error = validate_ivt_config(config)
        
        assert error is not None
        assert "velocity" in error.lower()
        assert "dispersion" in error.lower()

    def test_get_validated_config_success(self, tmp_path, monkeypatch):
        """Test successful validation flow."""
        config_data = {
            'algorithms': {'ivt_duration_threshold': 120}
        }
        config_file = tmp_path / "config.yaml"
        with open(config_file, 'w') as f:
            yaml.dump(config_data, f)
        
        # Monkeypatch CONFIG_PATH for testing
        monkeypatch.setattr('utils.config_loader.CONFIG_PATH', config_file)
        
        result = get_validated_config()
        assert result['algorithms']['ivt_duration_threshold'] == 120

    def test_get_validated_config_failure_forbidden(self, tmp_path, monkeypatch):
        """Test validation failure due to forbidden params."""
        config_data = {
            'algorithms': {
                'ivt_duration_threshold': 100,
                'velocity_threshold': 30
            }
        }
        config_file = tmp_path / "config.yaml"
        with open(config_file, 'w') as f:
            yaml.dump(config_data, f)
        
        monkeypatch.setattr('utils.config_loader.CONFIG_PATH', config_file)
        
        with pytest.raises(ValueError) as exc_info:
            get_validated_config()
        
        assert "forbidden" in str(exc_info.value).lower()