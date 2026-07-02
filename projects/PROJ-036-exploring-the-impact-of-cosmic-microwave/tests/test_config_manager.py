"""
Tests for the configuration manager module.

These tests verify that configuration files are loaded correctly
and that the combined configuration is formed as expected.
"""
import pytest
import os
import tempfile
import shutil
from pathlib import Path
import yaml
import sys

# Add the project root to the path so we can import from code/
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root / "code"))

from utils.config_manager import (
    load_yaml_config,
    load_lambdacdm_config,
    load_anomaly_config,
    get_combined_config,
    ensure_config_exists,
    CONFIG_DIR
)


class TestConfigLoading:
    """Tests for basic configuration loading functionality."""

    def test_load_yaml_config_valid_file(self, tmp_path):
        """Test loading a valid YAML file."""
        config_data = {
            "key1": "value1",
            "key2": 42,
            "nested": {
                "inner_key": "inner_value"
            }
        }
        
        config_file = tmp_path / "test_config.yaml"
        with open(config_file, 'w') as f:
            yaml.dump(config_data, f)
        
        loaded = load_yaml_config(config_file)
        assert loaded == config_data
        assert loaded["key1"] == "value1"
        assert loaded["key2"] == 42
        assert loaded["nested"]["inner_key"] == "inner_value"

    def test_load_yaml_config_missing_file(self, tmp_path):
        """Test that loading a missing file raises FileNotFoundError."""
        missing_file = tmp_path / "nonexistent.yaml"
        
        with pytest.raises(FileNotFoundError):
            load_yaml_config(missing_file)

    def test_load_yaml_config_invalid_yaml(self, tmp_path):
        """Test that loading invalid YAML raises an error."""
        config_file = tmp_path / "invalid.yaml"
        with open(config_file, 'w') as f:
            f.write("invalid: yaml: content: [unclosed")
        
        with pytest.raises(yaml.YAMLError):
            load_yaml_config(config_file)

    def test_load_lambdacdm_config(self):
        """Test loading the Lambda-CDM configuration."""
        # This assumes the config files exist in the project
        config = load_lambdacdm_config()
        
        assert "cosmology" in config
        assert "h" in config["cosmology"]
        assert "omega_m" in config["cosmology"]
        assert "omega_b" in config["cosmology"]
        
        # Check some expected values
        assert 0.6 < config["cosmology"]["h"] < 0.8
        assert 0.2 < config["cosmology"]["omega_m"] < 0.4

    def test_load_anomaly_config(self):
        """Test loading the anomaly configuration."""
        config = load_anomaly_config()
        
        assert "anomaly_type" in config
        assert "cold_spot" in config
        assert "phase_injection" in config
        
        # Check Cold Spot parameters
        cold_spot = config["cold_spot"]
        assert "galactic_l" in cold_spot
        assert "galactic_b" in cold_spot
        assert 180 < cold_spot["galactic_l"] < 230
        assert -60 < cold_spot["galactic_b"] < -50


class TestConfigIntegration:
    """Tests for configuration integration and combination."""

    def test_get_combined_config(self):
        """Test that combined config contains keys from both sources."""
        combined = get_combined_config()
        
        # Should have Lambda-CDM keys
        assert "cosmology" in combined
        assert "h" in combined["cosmology"]
        
        # Should have anomaly keys
        assert "anomaly_type" in combined
        assert "cold_spot" in combined
        
        # Anomaly config should override Lambda-CDM for overlapping keys
        # (if any exist)
        assert "simulation" in combined

    def test_combined_config_simulation_params(self):
        """Test that simulation parameters are correctly merged."""
        combined = get_combined_config()
        
        assert "simulation" in combined
        assert "box_size" in combined["simulation"]
        assert "n_particles" in combined["simulation"]
        
        # Check that box size is consistent
        assert combined["simulation"]["box_size"] == 250

    def test_ensure_config_exists(self):
        """Test that the configuration existence check works."""
        # This should return True if the project is set up correctly
        result = ensure_config_exists()
        assert result is True

    def test_config_structure_integrity(self):
        """Test that the combined config has the expected structure."""
        combined = get_combined_config()
        
        # Check top-level keys
        expected_keys = ["cosmology", "simulation", "anomaly_type", "cold_spot", "phase_injection"]
        for key in expected_keys:
            assert key in combined, f"Missing expected key: {key}"
        
        # Check nested structure
        assert isinstance(combined["cosmology"], dict)
        assert isinstance(combined["cold_spot"], dict)
        assert isinstance(combined["phase_injection"], dict)

    def test_config_values_ranges(self):
        """Test that configuration values are within expected physical ranges."""
        combined = get_combined_config()
        
        cosmology = combined["cosmology"]
        
        # Hubble parameter
        assert 0.5 < cosmology["h"] < 0.9
        
        # Density parameters should sum to ~1
        omega_sum = cosmology["omega_m"] + cosmology["omega_lambda"]
        assert 0.9 < omega_sum < 1.1
        
        # Spectral index
        assert 0.9 < cosmology["n_s"] < 1.0
        
        # Cold Spot location
        cold_spot = combined["cold_spot"]
        assert 0 <= cold_spot["galactic_l"] <= 360
        assert -90 <= cold_spot["galactic_b"] <= 90

if __name__ == "__main__":
    pytest.main([__file__, "-v"])