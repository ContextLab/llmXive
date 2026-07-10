"""
Unit tests for code/config.py configuration loading module.
"""

import os
import tempfile
from pathlib import Path

import pytest
import yaml

from code.config import (
    ConfigError,
    _get_config_path,
    get_frequency_bins,
    get_inertia,
    get_material_properties,
    get_mass,
    get_roughness_proxy,
    load_config,
    validate_config,
)


class TestConfigLoading:
    """Tests for basic configuration loading functionality."""

    @pytest.fixture
    def valid_config_file(self, tmp_path):
        """Create a temporary valid config file."""
        config_data = {
            "materials": {
                "test_material": {
                    "mass": 1.0,
                    "inertia": 0.5,
                    "roughness_proxy": 0.1,
                }
            },
            "frequency_bins": [
                {"label": "low", "min_hz": 0.0, "max_hz": 10.0},
                {"label": "high", "min_hz": 10.0, "max_hz": 100.0},
            ],
        }
        config_file = tmp_path / "config.yaml"
        with open(config_file, "w") as f:
            yaml.dump(config_data, f)
        return config_file

    def test_load_config_valid(self, valid_config_file, monkeypatch):
        """Test loading a valid configuration file."""
        # Monkeypatch the config path resolution
        monkeypatch.setattr("code.config._get_config_path", lambda: valid_config_file)

        config = load_config()

        assert "materials" in config
        assert "frequency_bins" in config
        assert "test_material" in config["materials"]

    def test_load_config_empty_file(self, tmp_path, monkeypatch):
        """Test loading an empty config file raises error."""
        config_file = tmp_path / "empty.yaml"
        config_file.touch()

        monkeypatch.setattr("code.config._get_config_path", lambda: config_file)

        with pytest.raises(ConfigError, match="empty"):
            load_config()

    def test_load_config_invalid_yaml(self, tmp_path, monkeypatch):
        """Test loading invalid YAML raises error."""
        config_file = tmp_path / "invalid.yaml"
        config_file.write_text("invalid: yaml: content: [unclosed")

        monkeypatch.setattr("code.config._get_config_path", lambda: config_file)

        with pytest.raises(ConfigError, match="parse YAML"):
            load_config()


class TestMaterialProperties:
    """Tests for material property retrieval."""

    @pytest.fixture
    def config_with_materials(self, tmp_path, monkeypatch):
        """Create config with multiple materials."""
        config_data = {
            "materials": {
                "steel": {
                    "mass": 5.0,
                    "inertia": 2.5,
                    "roughness_proxy": 0.05,
                },
                "polymer": {
                    "mass": 2.0,
                    "inertia": 1.0,
                    "roughness_proxy": 0.25,
                },
            },
            "frequency_bins": [
                {"label": "low", "min_hz": 0.0, "max_hz": 10.0},
            ],
        }
        config_file = tmp_path / "config.yaml"
        with open(config_file, "w") as f:
            yaml.dump(config_data, f)

        monkeypatch.setattr("code.config._get_config_path", lambda: config_file)
        return config_data

    def test_get_all_materials(self, config_with_materials):
        """Test retrieving all materials."""
        materials = get_material_properties()

        assert "steel" in materials
        assert "polymer" in materials
        assert materials["steel"]["mass"] == 5.0

    def test_get_specific_material(self, config_with_materials):
        """Test retrieving a specific material."""
        steel = get_material_properties("steel")

        assert steel["mass"] == 5.0
        assert steel["inertia"] == 2.5
        assert steel["roughness_proxy"] == 0.05

    def test_get_nonexistent_material(self, config_with_materials):
        """Test retrieving a non-existent material raises error."""
        with pytest.raises(ConfigError, match="not found"):
            get_material_properties("aluminum")

    def test_get_mass(self, config_with_materials):
        """Test retrieving mass for a material."""
        mass = get_mass("polymer")
        assert mass == 2.0

    def test_get_inertia(self, config_with_materials):
        """Test retrieving inertia for a material."""
        inertia = get_inertia("steel")
        assert inertia == 2.5

    def test_get_roughness_proxy(self, config_with_materials):
        """Test retrieving roughness proxy for a material."""
        roughness = get_roughness_proxy("polymer")
        assert roughness == 0.25


class TestFrequencyBins:
    """Tests for frequency bin retrieval."""

    @pytest.fixture
    def config_with_bins(self, tmp_path, monkeypatch):
        """Create config with frequency bins."""
        config_data = {
            "materials": {
                "test": {
                    "mass": 1.0,
                    "inertia": 0.5,
                    "roughness_proxy": 0.1,
                }
            },
            "frequency_bins": [
                {"label": "low", "min_hz": 0.0, "max_hz": 10.0},
                {"label": "mid", "min_hz": 10.0, "max_hz": 100.0},
                {"label": "high", "min_hz": 100.0, "max_hz": 1000.0},
            ],
        }
        config_file = tmp_path / "config.yaml"
        with open(config_file, "w") as f:
            yaml.dump(config_data, f)

        monkeypatch.setattr("code.config._get_config_path", lambda: config_file)
        return config_data

    def test_get_frequency_bins(self, config_with_bins):
        """Test retrieving frequency bins."""
        bins = get_frequency_bins()

        assert len(bins) == 3
        assert bins[0]["label"] == "low"
        assert bins[0]["min_hz"] == 0.0
        assert bins[0]["max_hz"] == 10.0
        assert bins[2]["label"] == "high"

    def test_invalid_bin_range(self, tmp_path, monkeypatch):
        """Test that invalid bin ranges raise error during validation."""
        config_data = {
            "materials": {
                "test": {
                    "mass": 1.0,
                    "inertia": 0.5,
                    "roughness_proxy": 0.1,
                }
            },
            "frequency_bins": [
                {"label": "invalid", "min_hz": 100.0, "max_hz": 10.0},
            ],
        }
        config_file = tmp_path / "config.yaml"
        with open(config_file, "w") as f:
            yaml.dump(config_data, f)

        monkeypatch.setattr("code.config._get_config_path", lambda: config_file)

        with pytest.raises(ConfigError, match="invalid range"):
            validate_config()


class TestValidation:
    """Tests for configuration validation."""

    def test_validate_missing_materials(self, tmp_path, monkeypatch):
        """Test validation fails when materials section is missing."""
        config_data = {
            "frequency_bins": [
                {"label": "low", "min_hz": 0.0, "max_hz": 10.0},
            ],
        }
        config_file = tmp_path / "config.yaml"
        with open(config_file, "w") as f:
            yaml.dump(config_data, f)

        monkeypatch.setattr("code.config._get_config_path", lambda: config_file)

        with pytest.raises(ConfigError, match="missing.*materials"):
            validate_config()

    def test_validate_missing_frequency_bins(self, tmp_path, monkeypatch):
        """Test validation fails when frequency_bins section is missing."""
        config_data = {
            "materials": {
                "test": {
                    "mass": 1.0,
                    "inertia": 0.5,
                    "roughness_proxy": 0.1,
                }
            },
        }
        config_file = tmp_path / "config.yaml"
        with open(config_file, "w") as f:
            yaml.dump(config_data, f)

        monkeypatch.setattr("code.config._get_config_path", lambda: config_file)

        with pytest.raises(ConfigError, match="missing.*frequency_bins"):
            validate_config()

    def test_validate_missing_property(self, tmp_path, monkeypatch):
        """Test validation fails when material property is missing."""
        config_data = {
            "materials": {
                "incomplete": {
                    "mass": 1.0,
                    "inertia": 0.5,
                    # missing roughness_proxy
                }
            },
            "frequency_bins": [
                {"label": "low", "min_hz": 0.0, "max_hz": 10.0},
            ],
        }
        config_file = tmp_path / "config.yaml"
        with open(config_file, "w") as f:
            yaml.dump(config_data, f)

        monkeypatch.setattr("code.config._get_config_path", lambda: config_file)

        with pytest.raises(ConfigError, match="missing.*properties"):
            validate_config()

    def test_validate_success(self, tmp_path, monkeypatch):
        """Test validation succeeds with valid config."""
        config_data = {
            "materials": {
                "test": {
                    "mass": 1.0,
                    "inertia": 0.5,
                    "roughness_proxy": 0.1,
                }
            },
            "frequency_bins": [
                {"label": "low", "min_hz": 0.0, "max_hz": 10.0},
            ],
        }
        config_file = tmp_path / "config.yaml"
        with open(config_file, "w") as f:
            yaml.dump(config_data, f)

        monkeypatch.setattr("code.config._get_config_path", lambda: config_file)

        assert validate_config() is True
