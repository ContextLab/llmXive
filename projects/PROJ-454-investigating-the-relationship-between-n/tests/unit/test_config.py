"""
Unit tests for configuration management (T009).

Tests verify that:
- Configuration loads from environment variables
- Defaults are used when environment variables are missing
- Type parsing works correctly (int, float, list, bool)
- Helper methods return correct grouped parameters
- Validation catches invalid configurations
"""

import os
import pytest
from pathlib import Path
import sys

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from config import Config, CONFIG_DEFAULTS, validate_config, load_config_from_env


class TestConfigLoading:
    """Test configuration loading from environment and defaults."""
    
    def test_defaults_exist(self):
        """Test that all expected default keys are present."""
        expected_keys = [
            "OPENNEURO_DATASET_IDS",
            "SNR_MIN_THRESHOLD_DB",
            "VIF_COLLINEARITY_THRESHOLD",
            "RAM_LIMIT_GB",
            "DISK_LIMIT_GB",
            "ENTROPY_SAMPLE_M",
            "ENTROPY_SAMPLE_R_RATIO",
            "EEG_BANDPASS_LOW",
            "EEG_BANDPASS_HIGH",
            "FDR_ALPHA",
        ]
        
        for key in expected_keys:
            assert key in CONFIG_DEFAULTS, f"Missing default for {key}"
    
    def test_config_loads_from_defaults(self):
        """Test that Config loads defaults when no env vars are set."""
        # Clear any existing env vars for these keys
        for key in ["SNR_MIN_THRESHOLD_DB", "RAM_LIMIT_GB"]:
            if key in os.environ:
                del os.environ[key]
        
        config = Config(CONFIG_DEFAULTS)
        
        assert config.get("SNR_MIN_THRESHOLD_DB") == 5.0
        assert config.get("RAM_LIMIT_GB") == 7.0
    
    def test_config_overrides_with_env_vars(self, monkeypatch):
        """Test that environment variables override defaults."""
        monkeypatch.setenv("SNR_MIN_THRESHOLD_DB", "10.5")
        monkeypatch.setenv("RAM_LIMIT_GB", "8.0")
        
        config = Config(CONFIG_DEFAULTS)
        
        assert config.get("SNR_MIN_THRESHOLD_DB") == 10.5
        assert config.get("RAM_LIMIT_GB") == 8.0
    
    def test_config_caches_values(self, monkeypatch):
        """Test that config caches values after first load."""
        monkeypatch.setenv("TEST_CACHE_KEY", "first_value")
        
        config = Config({"TEST_CACHE_KEY": "default"})
        
        # First call
        val1 = config.get("TEST_CACHE_KEY")
        assert val1 == "first_value"
        
        # Change env var
        monkeypatch.setenv("TEST_CACHE_KEY", "second_value")
        
        # Second call should return cached value, not new env value
        val2 = config.get("TEST_CACHE_KEY")
        assert val2 == "first_value"


class TestTypeParsing:
    """Test parsing of different value types from environment strings."""
    
    def test_int_parsing(self, monkeypatch):
        """Test integer parsing from environment."""
        monkeypatch.setenv("TEST_INT", "42")
        config = Config({"TEST_INT": 10})
        assert config.get("TEST_INT") == 42
    
    def test_float_parsing(self, monkeypatch):
        """Test float parsing from environment."""
        monkeypatch.setenv("TEST_FLOAT", "3.14159")
        config = Config({"TEST_FLOAT": 1.0})
        assert abs(config.get("TEST_FLOAT") - 3.14159) < 0.0001
    
    def test_bool_parsing_true(self, monkeypatch):
        """Test boolean parsing for true values."""
        for val in ["true", "True", "1", "yes", "on"]:
            monkeypatch.setenv("TEST_BOOL", val)
            config = Config({"TEST_BOOL": False})
            assert config.get("TEST_BOOL") is True
    
    def test_bool_parsing_false(self, monkeypatch):
        """Test boolean parsing for false values."""
        for val in ["false", "False", "0", "no", "off"]:
            monkeypatch.setenv("TEST_BOOL", val)
            config = Config({"TEST_BOOL": True})
            assert config.get("TEST_BOOL") is False
    
    def test_list_parsing(self, monkeypatch):
        """Test list parsing from comma-separated string."""
        monkeypatch.setenv("TEST_LIST", "a, b, c, d")
        config = Config({"TEST_LIST": ["x", "y"]})
        result = config.get("TEST_LIST")
        assert result == ["a", "b", "c", "d"]


class TestHelperMethods:
    """Test grouped parameter helper methods."""
    
    def test_get_dataset_ids(self):
        """Test get_dataset_ids returns list of IDs."""
        config = Config(CONFIG_DEFAULTS)
        ids = config.get_dataset_ids()
        assert isinstance(ids, list)
        assert len(ids) > 0
        assert "ds003104" in ids
    
    def test_get_entropy_params(self):
        """Test get_entropy_params returns correct dict."""
        config = Config(CONFIG_DEFAULTS)
        params = config.get_entropy_params()
        
        assert "sample_m" in params
        assert "sample_r_ratio" in params
        assert "approximate_m" in params
        assert "approximate_r_ratio" in params
        assert params["sample_m"] == 2
        assert params["sample_r_ratio"] == 0.2
    
    def test_get_eeg_params(self):
        """Test get_eeg_params returns correct dict."""
        config = Config(CONFIG_DEFAULTS)
        params = config.get_eeg_params()
        
        assert "bandpass_low" in params
        assert "bandpass_high" in params
        assert "notch_freqs" in params
        assert "epoch_duration" in params
        assert params["bandpass_low"] == 1.0
        assert params["bandpass_high"] == 45.0
    
    def test_get_thresholds(self):
        """Test get_thresholds returns correct dict."""
        config = Config(CONFIG_DEFAULTS)
        thresholds = config.get_thresholds()
        
        assert "snr_min_db" in thresholds
        assert "vif_threshold" in thresholds
        assert "fdr_alpha" in thresholds
        assert thresholds["snr_min_db"] == 5.0
        assert thresholds["vif_threshold"] == 5.0


class TestValidation:
    """Test configuration validation."""
    
    def test_validate_config_passes_with_defaults(self):
        """Test validation passes with valid defaults."""
        # Clear any potentially invalid env vars
        for key in ["SNR_MIN_THRESHOLD_DB", "VIF_COLLINEARITY_THRESHOLD"]:
            if key in os.environ:
                del os.environ[key]
        
        # This should not raise
        assert validate_config() is True
    
    def test_validate_config_fails_negative_snr(self, monkeypatch):
        """Test validation fails with negative SNR threshold."""
        monkeypatch.setenv("SNR_MIN_THRESHOLD_DB", "-5.0")
        
        with pytest.raises(ValueError, match="SNR threshold must be positive"):
            validate_config()
    
    def test_validate_config_fails_negative_vif(self, monkeypatch):
        """Test validation fails with negative VIF threshold."""
        monkeypatch.setenv("VIF_COLLINEARITY_THRESHOLD", "-1.0")
        
        with pytest.raises(ValueError, match="VIF threshold must be positive"):
            validate_config()
    
    def test_validate_config_fails_missing_critical(self, monkeypatch):
        """Test validation fails when critical key is missing."""
        # Temporarily remove from defaults
        original = CONFIG_DEFAULTS.pop("SNR_MIN_THRESHOLD_DB", None)
        try:
            with pytest.raises(ValueError, match="Critical config missing"):
                validate_config()
        finally:
            # Restore
            if original is not None:
                CONFIG_DEFAULTS["SNR_MIN_THRESHOLD_DB"] = original


class TestLoadConfigFromEnv:
    """Test loading full configuration."""
    
    def test_load_all_config(self):
        """Test that load_config_from_env returns all keys."""
        config_dict = load_config_from_env()
        
        assert isinstance(config_dict, dict)
        assert len(config_dict) == len(CONFIG_DEFAULTS)
        
        # Check a few keys
        assert "SNR_MIN_THRESHOLD_DB" in config_dict
        assert "RAM_LIMIT_GB" in config_dict
        assert config_dict["SNR_MIN_THRESHOLD_DB"] == 5.0