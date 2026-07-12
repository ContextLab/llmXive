"""
Unit tests for environment configuration management.

Tests verify that configuration loading, threshold retrieval,
and path resolution work correctly.
"""
import pytest
from pathlib import Path
import sys
import os

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from config.environment_config import (
    load_config,
    get_dataset_urls,
    get_snr_threshold,
    get_exclusion_thresholds,
    get_frequency_bands,
    get_filter_settings,
    get_vif_threshold,
    get_effect_size_threshold,
    get_path,
    validate_config,
    DEFAULT_CONFIG
)

class TestConfigLoading:
    """Test configuration loading functionality."""

    def test_load_config_returns_dict(self):
        """Config loading returns a dictionary."""
        config = load_config()
        assert isinstance(config, dict)
        assert len(config) > 0

    def test_config_has_required_sections(self):
        """Config contains all required top-level sections."""
        config = load_config()
        required_sections = ["datasets", "thresholds", "bands", "filters", "paths"]
        for section in required_sections:
            assert section in config, f"Missing section: {section}"

    def test_default_config_structure(self):
        """Default config has expected structure."""
        config = DEFAULT_CONFIG
        assert "datasets" in config
        assert "openneuro" in config["datasets"]
        assert "datasets" in config["datasets"]["openneuro"]
        assert len(config["datasets"]["openneuro"]["datasets"]) > 0

class TestDatasetConfiguration:
    """Test dataset URL and metadata retrieval."""

    def test_get_dataset_urls_returns_openneuro_data(self):
        """Dataset URLs are correctly retrieved."""
        urls = get_dataset_urls()
        assert "base_url" in urls
        assert "datasets" in urls
        assert urls["base_url"] == "https://api.openneuro.org"

    def test_ds003104_in_datasets(self):
        """Required dataset ds003104 is present."""
        urls = get_dataset_urls()
        dataset_ids = [ds["id"] for ds in urls["datasets"]]
        assert "ds003104" in dataset_ids

    def test_dataset_has_required_variables(self):
        """Dataset metadata includes required variables."""
        urls = get_dataset_urls()
        ds003104 = next(ds for ds in urls["datasets"] if ds["id"] == "ds003104")
        assert "required_variables" in ds003104
        assert "wcst_perseverative_errors" in ds003104["required_variables"]
        assert "age" in ds003104["required_variables"]

class TestThresholdConfiguration:
    """Test threshold value retrieval."""

    def test_snr_threshold_is_float(self):
        """SNR threshold is a float value."""
        snr = get_snr_threshold()
        assert isinstance(snr, float)
        assert snr > 0

    def test_snr_default_value(self):
        """SNR threshold has correct default value."""
        snr = get_snr_threshold()
        assert snr == 5.0

    def test_exclusion_thresholds_dict(self):
        """Exclusion thresholds return dictionary with expected keys."""
        thresholds = get_exclusion_thresholds()
        expected_keys = ["max_corrupted_pct", "min_valid_seconds", "snr_min_db"]
        for key in expected_keys:
            assert key in thresholds, f"Missing key: {key}"

    def test_vif_threshold(self):
        """VIF threshold is correctly retrieved."""
        vif = get_vif_threshold()
        assert isinstance(vif, float)
        assert vif == 5.0

    def test_effect_size_threshold(self):
        """Effect size threshold is correctly retrieved."""
        effect = get_effect_size_threshold()
        assert isinstance(effect, float)
        assert effect == 0.3

class TestFrequencyBands:
    """Test frequency band configuration."""

    def test_get_frequency_bands_returns_dict(self):
        """Frequency bands are returned as dictionary."""
        bands = get_frequency_bands()
        assert isinstance(bands, dict)
        assert len(bands) > 0

    def test_all_bands_present(self):
        """All expected frequency bands are present."""
        bands = get_frequency_bands()
        expected_bands = ["delta", "theta", "alpha", "beta", "gamma"]
        for band in expected_bands:
            assert band in bands, f"Missing band: {band}"

    def test_band_values_are_tuples(self):
        """Band values are (low, high) tuples."""
        bands = get_frequency_bands()
        for band, (low, high) in bands.items():
            assert isinstance(low, float)
            assert isinstance(high, float)
            assert low < high

class TestFilterSettings:
    """Test EEG filter configuration."""

    def test_get_filter_settings_returns_dict(self):
        """Filter settings are returned as dictionary."""
        filters = get_filter_settings()
        assert isinstance(filters, dict)
        assert "bandpass" in filters
        assert "notch" in filters

    def test_bandpass_range(self):
        """Bandpass filter has correct range."""
        filters = get_filter_settings()
        low, high = filters["bandpass"]
        assert low == 1.0
        assert high == 45.0

    def test_notch_frequencies(self):
        """Notch filter frequencies are correct."""
        filters = get_filter_settings()
        assert 50.0 in filters["notch"]
        assert 60.0 in filters["notch"]

class TestPathResolution:
    """Test project path resolution."""

    def test_get_path_returns_path_object(self):
        """Path resolution returns Path object."""
        path = get_path("raw_data")
        assert isinstance(path, Path)

    def test_paths_are_absolute(self):
        """Resolved paths are absolute."""
        for key in ["raw_data", "processed_data", "logs", "reports"]:
            path = get_path(key)
            assert path.is_absolute()

    def test_paths_under_project_root(self):
        """Resolved paths are under project root."""
        project_root = Path(__file__).parent.parent.parent / "code" / ".." / ".."
        for key in ["raw_data", "processed_data", "logs", "reports"]:
            path = get_path(key)
            assert str(project_root) in str(path)

class TestValidation:
    """Test configuration validation."""

    def test_validate_config_returns_bool(self):
        """Validation returns boolean."""
        result = validate_config()
        assert isinstance(result, bool)

    def test_default_config_valid(self):
        """Default configuration passes validation."""
        assert validate_config() is True

if __name__ == "__main__":
    pytest.main([__file__, "-v"])