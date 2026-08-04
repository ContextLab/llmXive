"""
Unit tests for configuration management.

Tests cover:
- Default configuration values
- Environment variable overrides
- Configuration validation
- Helper functions for accessing config values
"""
import os
import pytest
from pathlib import Path
from unittest.mock import patch

# Import config module
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from config import (
    Config,
    load_config_from_env,
    validate_config,
    get_config,
    reset_config,
    get_dataset_url,
    get_output_path,
    get_frequency_band,
    get_entropy_params,
    get_data_quality_thresholds,
    get_preprocessing_params,
    get_resource_limits,
    get_vif_threshold,
    get_fdr_method,
    is_power_analysis_deferred,
    get_wcst_variable_name,
    get_min_age,
    get_dataset_ids
)


class TestConfigDataClass:
    """Tests for the Config dataclass."""
    
    def test_default_values(self):
        """Test that default values are set correctly."""
        config = Config()
        
        assert config.openneuro_base_url == "https://api.openneuro.org"
        assert config.dataset_ids == ["ds003104"]
        assert config.wcst_variable == "wcst_perseverative_errors"
        assert config.min_age == 50
        assert config.snr_threshold_db == 5.0
        assert config.artifact_threshold_percent == 20.0
        assert config.min_eeg_duration_sec == 60.0
        assert config.max_corrupted_percent == 20.0
        assert config.entropy_method == "both"
        assert config.sample_entropy_m == 2
        assert config.sample_entropy_r == 0.2
        assert config.approximate_entropy_m == 2
        assert config.approximate_entropy_r == 0.2
        assert config.bandpass_low_hz == 1.0
        assert config.bandpass_high_hz == 45.0
        assert config.notch_freqs == [50.0, 60.0]
        assert config.epoch_duration_sec == 2.0
        assert config.vif_threshold == 5.0
        assert config.fdr_method == "benjamini_hochberg"
        assert config.power_analysis_deferred is True
        
        # Check frequency bands
        assert "delta" in config.frequency_bands
        assert "theta" in config.frequency_bands
        assert "alpha" in config.frequency_bands
        assert "beta" in config.frequency_bands
        assert "gamma" in config.frequency_bands
        assert config.frequency_bands["delta"] == [0.5, 4.0]
        assert config.frequency_bands["gamma"] == [30.0, 45.0]
        
        # Check resource limits
        assert config.resource_limits["max_ram_gb"] == 7.0
        assert config.resource_limits["max_disk_gb"] == 14.0
    
    def test_custom_values(self):
        """Test creating config with custom values."""
        config = Config(
            dataset_ids=["ds001", "ds002"],
            snr_threshold_db=10.0,
            min_age=60,
            entropy_method="sample"
        )
        
        assert config.dataset_ids == ["ds001", "ds002"]
        assert config.snr_threshold_db == 10.0
        assert config.min_age == 60
        assert config.entropy_method == "sample"


class TestLoadConfigFromEnv:
    """Tests for loading configuration from environment variables."""
    
    def test_no_env_vars_uses_defaults(self):
        """Test that defaults are used when no env vars are set."""
        # Clear any existing LLMXIVE_ env vars
        env_copy = os.environ.copy()
        for key in list(env_copy.keys()):
            if key.startswith("LLMXIVE_"):
                del env_copy[key]
        
        with patch.dict(os.environ, env_copy, clear=True):
            config = load_config_from_env(Config())
            assert config.dataset_ids == ["ds003104"]
            assert config.snr_threshold_db == 5.0
    
    def test_env_var_overrides(self):
        """Test that environment variables override defaults."""
        env_vars = {
            "LLMXIVE_OPENNEURO_URL": "https://custom.openneuro.org",
            "LLMXIVE_DATASET_IDS": "ds001,ds002,ds003",
            "LLMXIVE_WCST_VARIABLE": "custom_wcst_var",
            "LLMXIVE_MIN_AGE": "65",
            "LLMXIVE_SNR_THRESHOLD_DB": "8.5",
            "LLMXIVE_ARTIFACT_THRESHOLD_PERCENT": "15.0",
            "LLMXIVE_MIN_EEG_DURATION_SEC": "90.0",
            "LLMXIVE_MAX_CORRUPTED_PERCENT": "10.0",
            "LLMXIVE_ENTROPY_METHOD": "sample",
            "LLMXIVE_SAMPLE_ENTROPY_M": "3",
            "LLMXIVE_SAMPLE_ENTROPY_R": "0.25",
            "LLMXIVE_APPROXIMATE_ENTROPY_M": "3",
            "LLMXIVE_APPROXIMATE_ENTROPY_R": "0.25",
            "LLMXIVE_BANDPASS_LOW_HZ": "0.5",
            "LLMXIVE_BANDPASS_HIGH_HZ": "50.0",
            "LLMXIVE_NOTCH_FREQS": "50.0,60.0,100.0",
            "LLMXIVE_EPOCH_DURATION_SEC": "1.5",
            "LLMXIVE_VIF_THRESHOLD": "10.0",
            "LLMXIVE_FDR_METHOD": "benjamini_yekutieli"
        }
        
        with patch.dict(os.environ, env_vars):
            config = load_config_from_env(Config())
            
            assert config.openneuro_base_url == "https://custom.openneuro.org"
            assert config.dataset_ids == ["ds001", "ds002", "ds003"]
            assert config.wcst_variable == "custom_wcst_var"
            assert config.min_age == 65
            assert config.snr_threshold_db == 8.5
            assert config.artifact_threshold_percent == 15.0
            assert config.min_eeg_duration_sec == 90.0
            assert config.max_corrupted_percent == 10.0
            assert config.entropy_method == "sample"
            assert config.sample_entropy_m == 3
            assert config.sample_entropy_r == 0.25
            assert config.approximate_entropy_m == 3
            assert config.approximate_entropy_r == 0.25
            assert config.bandpass_low_hz == 0.5
            assert config.bandpass_high_hz == 50.0
            assert config.notch_freqs == [50.0, 60.0, 100.0]
            assert config.epoch_duration_sec == 1.5
            assert config.vif_threshold == 10.0
            assert config.fdr_method == "benjamini_yekutieli"


class TestValidateConfig:
    """Tests for configuration validation."""
    
    def test_valid_config(self):
        """Test that a valid config passes validation."""
        config = Config()
        assert validate_config(config) is True
    
    def test_invalid_dataset_id_format(self):
        """Test validation fails for invalid dataset ID format."""
        config = Config(dataset_ids=["invalid_id"])
        with pytest.raises(ValueError, match="Invalid dataset ID format"):
            validate_config(config)
    
    def test_empty_dataset_ids(self):
        """Test validation fails for empty dataset IDs."""
        config = Config(dataset_ids=[])
        with pytest.raises(ValueError, match="At least one dataset ID must be specified"):
            validate_config(config)
    
    def test_negative_snr_threshold(self):
        """Test validation fails for negative SNR threshold."""
        config = Config(snr_threshold_db=-1.0)
        with pytest.raises(ValueError, match="SNR threshold must be non-negative"):
            validate_config(config)
    
    def test_invalid_artifact_threshold(self):
        """Test validation fails for artifact threshold outside 0-100."""
        config = Config(artifact_threshold_percent=150.0)
        with pytest.raises(ValueError, match="Artifact threshold must be between 0 and 100"):
            validate_config(config)
    
    def test_zero_min_eeg_duration(self):
        """Test validation fails for zero or negative EEG duration."""
        config = Config(min_eeg_duration_sec=0.0)
        with pytest.raises(ValueError, match="Minimum EEG duration must be positive"):
            validate_config(config)
    
    def test_invalid_sample_entropy_m(self):
        """Test validation fails for non-positive sample entropy m."""
        config = Config(sample_entropy_m=0)
        with pytest.raises(ValueError, match="Sample entropy m must be positive"):
            validate_config(config)
    
    def test_invalid_sample_entropy_r(self):
        """Test validation fails for non-positive sample entropy r."""
        config = Config(sample_entropy_r=-0.1)
        with pytest.raises(ValueError, match="Sample entropy r must be positive"):
            validate_config(config)
    
    def test_invalid_frequency_band(self):
        """Test validation fails for invalid frequency band (low >= high)."""
        config = Config()
        config.frequency_bands["test"] = [10.0, 5.0]
        with pytest.raises(ValueError, match="Invalid frequency band test"):
            validate_config(config)
    
    def test_invalid_bandpass(self):
        """Test validation fails for invalid bandpass parameters."""
        config = Config(bandpass_low_hz=50.0, bandpass_high_hz=45.0)
        with pytest.raises(ValueError, match="Bandpass high"):
            validate_config(config)
    
    def test_invalid_fdr_method(self):
        """Test validation fails for invalid FDR method."""
        config = Config(fdr_method="invalid_method")
        with pytest.raises(ValueError, match="Invalid FDR method"):
            validate_config(config)


class TestGlobalConfig:
    """Tests for global configuration management."""
    
    def setup_method(self):
        """Reset config before each test."""
        reset_config()
    
    def teardown_method(self):
        """Reset config after each test."""
        reset_config()
    
    def test_get_config_loads_once(self):
        """Test that get_config loads configuration once."""
        config1 = get_config()
        config2 = get_config()
        assert config1 is config2
    
    def test_get_config_validates(self):
        """Test that get_config validates the configuration."""
        with patch.dict(os.environ, {"LLMXIVE_DATASET_IDS": ""}):
            with pytest.raises(ValueError):
                get_config()


class TestHelperFunctions:
    """Tests for helper functions that access configuration."""
    
    def setup_method(self):
        """Reset and set up config for tests."""
        reset_config()
        with patch.dict(os.environ, {
            "LLMXIVE_DATASET_IDS": "ds001,ds002",
            "LLMXIVE_OPENNEURO_URL": "https://test.openneuro.org"
        }):
            get_config()  # Load config
    
    def teardown_method(self):
        """Reset config after each test."""
        reset_config()
    
    def test_get_dataset_url(self):
        """Test URL construction for datasets."""
        url = get_dataset_url("ds001")
        assert url == "https://test.openneuro.org/datasets/ds001"
    
    def test_get_output_path(self):
        """Test output path construction."""
        path = get_output_path("processed", "test.csv")
        assert "data/processed" in str(path)
        assert path.name == "test.csv"
    
    def test_get_frequency_band(self):
        """Test frequency band retrieval."""
        delta = get_frequency_band("delta")
        assert delta == [0.5, 4.0]
        
        gamma = get_frequency_band("gamma")
        assert gamma == [30.0, 45.0]
    
    def test_get_frequency_band_invalid(self):
        """Test that invalid frequency band raises error."""
        with pytest.raises(ValueError, match="Unknown frequency band"):
            get_frequency_band("invalid_band")
    
    def test_get_entropy_params(self):
        """Test entropy parameters retrieval."""
        params = get_entropy_params()
        assert "method" in params
        assert "sample_entropy" in params
        assert "approximate_entropy" in params
        assert params["sample_entropy"]["m"] == 2
        assert params["sample_entropy"]["r"] == 0.2
    
    def test_get_data_quality_thresholds(self):
        """Test data quality thresholds retrieval."""
        thresholds = get_data_quality_thresholds()
        assert "snr_threshold_db" in thresholds
        assert "artifact_threshold_percent" in thresholds
        assert thresholds["snr_threshold_db"] == 5.0
    
    def test_get_preprocessing_params(self):
        """Test preprocessing parameters retrieval."""
        params = get_preprocessing_params()
        assert "bandpass_low_hz" in params
        assert "bandpass_high_hz" in params
        assert "notch_freqs" in params
        assert params["bandpass_low_hz"] == 1.0
    
    def test_get_resource_limits(self):
        """Test resource limits retrieval."""
        limits = get_resource_limits()
        assert "max_ram_gb" in limits
        assert "max_disk_gb" in limits
        assert limits["max_ram_gb"] == 7.0
    
    def test_get_vif_threshold(self):
        """Test VIF threshold retrieval."""
        threshold = get_vif_threshold()
        assert threshold == 5.0
    
    def test_get_fdr_method(self):
        """Test FDR method retrieval."""
        method = get_fdr_method()
        assert method == "benjamini_hochberg"
    
    def test_is_power_analysis_deferred(self):
        """Test power analysis deferred flag."""
        assert is_power_analysis_deferred() is True
    
    def test_get_wcst_variable_name(self):
        """Test WCST variable name retrieval."""
        name = get_wcst_variable_name()
        assert name == "wcst_perseverative_errors"
    
    def test_get_min_age(self):
        """Test minimum age retrieval."""
        age = get_min_age()
        assert age == 50
    
    def test_get_dataset_ids(self):
        """Test dataset IDs retrieval."""
        ids = get_dataset_ids()
        assert "ds001" in ids
        assert "ds002" in ids