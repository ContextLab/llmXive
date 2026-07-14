"""
Unit tests for the configuration management module.

These tests verify that the configuration system correctly loads defaults,
overrides from environment variables, and provides proper accessor functions.
"""

import os
import pytest
from utils.config import (
    Config,
    DatasetConfig,
    PreprocessingConfig,
    CentralityConfig,
    RegressionConfig,
    OutputPaths,
    get_config,
    reset_config,
    get_dataset_config,
    get_preprocessing_config,
    get_centrality_config,
    get_regression_config,
    get_output_paths,
    get_fd_threshold,
    get_min_retention_rate,
    get_power_threshold_n,
    get_vif_threshold,
    get_permutation_shuffles,
    get_permutation_seed,
    get_cv_folds,
    get_fixed_region_indices,
    get_regional_analysis_flag,
    get_global_model_pvalue_threshold,
)


class TestConfigDataClasses:
    """Tests for configuration data classes."""

    def test_dataset_config_defaults(self):
        """Test default values for DatasetConfig."""
        config = DatasetConfig()
        assert config.openneuro_dataset_id == "ds000030"
        assert config.openneuro_base_url.startswith("https://")
        assert config.download_dir == "data/raw/openneuro_ds000030"
        assert config.expected_subject_count == 100
        assert config.min_retention_rate == 0.80
        assert config.power_threshold_n == 85

    def test_preprocessing_config_defaults(self):
        """Test default values for PreprocessingConfig."""
        config = PreprocessingConfig()
        assert config.fmriprep_version == "20.2.7"
        assert config.memory_limit_gb == 8
        assert config.float32_conversion is True
        assert config.batch_size == 10
        assert config.fd_threshold == 0.5
        assert config.global_signal_regression is False
        assert config.bandpass_filter == (0.01, 0.1)
        assert config.motion_regression_params == 24

    def test_centrality_config_defaults(self):
        """Test default values for CentralityConfig."""
        config = CentralityConfig()
        assert config.atlas_name == "AAL3"
        assert config.atlas_nodes == 90
        assert config.fixed_region_indices == tuple(range(1, 11))
        assert "degree" in config.centrality_metrics
        assert "betweenness" in config.centrality_metrics
        assert "eigenvector" in config.centrality_metrics
        assert config.vif_threshold == 5.0
        assert config.regional_analysis_flag is False
        assert config.global_model_pvalue_threshold == 0.05

    def test_regression_config_defaults(self):
        """Test default values for RegressionConfig."""
        config = RegressionConfig()
        assert config.model_type == "linear"
        assert config.non_linearity_check is True
        assert config.polynomial_degree == 2
        assert config.gam_smoothness == 3
        assert config.permutation_shuffles == 1000
        assert config.permutation_seed == 42
        assert config.cv_folds == 5
        assert config.fdr_correction_method == "benjamini_hochberg"

    def test_output_paths_defaults(self):
        """Test default values for OutputPaths."""
        config = OutputPaths()
        assert config.processed_dir == "data/processed"
        assert config.connectivity_dir == "data/processed/connectivity"
        assert config.centrality_dir == "data/processed/centrality"
        assert config.behavioral_dir == "data/processed/behavioral"
        assert config.regression_dir == "data/processed/regression"
        assert config.validation_dir == "data/processed/validation"
        assert config.figures_dir == "figures"

    def test_master_config_defaults(self):
        """Test that master Config contains all sub-configs."""
        config = Config()
        assert isinstance(config.dataset, DatasetConfig)
        assert isinstance(config.preprocessing, PreprocessingConfig)
        assert isinstance(config.centrality, CentralityConfig)
        assert isinstance(config.regression, RegressionConfig)
        assert isinstance(config.output, OutputPaths)

    def test_to_dict_serialization(self):
        """Test that config can be converted to dictionary."""
        config = Config()
        config_dict = config.to_dict()
        assert "dataset" in config_dict
        assert "preprocessing" in config_dict
        assert "centrality" in config_dict
        assert "regression" in config_dict
        assert "output" in config_dict
        assert config_dict["dataset"]["openneuro_dataset_id"] == "ds000030"

    def test_save_to_file(self, tmp_path):
        """Test saving config to JSON file."""
        config = Config()
        filepath = tmp_path / "config_test.json"
        config.save_to_file(str(filepath))
        assert filepath.exists()
        assert filepath.stat().st_size > 0


class TestConfigEnvLoading:
    """Tests for environment variable loading."""

    def setup_method(self):
        """Reset config before each test."""
        reset_config()
        # Clean up test env vars
        test_vars = [
            "OPENNEURO_DATASET_ID",
            "FD_THRESHOLD",
            "VIF_THRESHOLD",
            "REGIONAL_ANALYSIS_FLAG",
            "PERMUTATION_SHUFFLES",
        ]
        for var in test_vars:
            if var in os.environ:
                del os.environ[var]

    def teardown_method(self):
        """Clean up after tests."""
        reset_config()
        test_vars = [
            "OPENNEURO_DATASET_ID",
            "FD_THRESHOLD",
            "VIF_THRESHOLD",
            "REGIONAL_ANALYSIS_FLAG",
            "PERMUTATION_SHUFFLES",
        ]
        for var in test_vars:
            if var in os.environ:
                del os.environ[var]

    def test_load_dataset_id_from_env(self):
        """Test loading dataset ID from environment."""
        os.environ["OPENNEURO_DATASET_ID"] = "ds_test_123"
        config = Config.load_from_env()
        assert config.dataset.openneuro_dataset_id == "ds_test_123"

    def test_load_fd_threshold_from_env(self):
        """Test loading FD threshold from environment."""
        os.environ["FD_THRESHOLD"] = "0.75"
        config = Config.load_from_env()
        assert config.preprocessing.fd_threshold == 0.75

    def test_load_vif_threshold_from_env(self):
        """Test loading VIF threshold from environment."""
        os.environ["VIF_THRESHOLD"] = "3.5"
        config = Config.load_from_env()
        assert config.centrality.vif_threshold == 3.5

    def test_load_regional_analysis_flag_from_env(self):
        """Test loading regional analysis flag from environment."""
        os.environ["REGIONAL_ANALYSIS_FLAG"] = "true"
        config = Config.load_from_env()
        assert config.centrality.regional_analysis_flag is True

        os.environ["REGIONAL_ANALYSIS_FLAG"] = "false"
        config = Config.load_from_env()
        assert config.centrality.regional_analysis_flag is False

    def test_load_permutation_shuffles_from_env(self):
        """Test loading permutation shuffles from environment."""
        os.environ["PERMUTATION_SHUFFLES"] = "5000"
        config = Config.load_from_env()
        assert config.regression.permutation_shuffles == 5000

    def test_get_config_singleton(self):
        """Test that get_config returns singleton instance."""
        reset_config()
        config1 = get_config()
        config2 = get_config()
        assert config1 is config2

    def test_get_config_overrides(self):
        """Test that environment overrides are applied via get_config."""
        os.environ["FD_THRESHOLD"] = "0.99"
        reset_config()
        config = get_config()
        assert config.preprocessing.fd_threshold == 0.99

    def test_reset_config(self):
        """Test that reset_config clears the singleton."""
        get_config()
        reset_config()
        assert get_config() is not get_config()  # New instance

    def test_get_fd_threshold_accessor(self):
        """Test the fd_threshold accessor function."""
        os.environ["FD_THRESHOLD"] = "0.88"
        reset_config()
        assert get_fd_threshold() == 0.88

    def test_get_vif_threshold_accessor(self):
        """Test the vif_threshold accessor function."""
        os.environ["VIF_THRESHOLD"] = "4.2"
        reset_config()
        assert get_vif_threshold() == 4.2

    def test_get_permutation_shuffles_accessor(self):
        """Test the permutation_shuffles accessor function."""
        os.environ["PERMUTATION_SHUFFLES"] = "2000"
        reset_config()
        assert get_permutation_shuffles() == 2000

    def test_get_permutation_seed_accessor(self):
        """Test the permutation_seed accessor function."""
        os.environ["PERMUTATION_SEED"] = "12345"
        reset_config()
        assert get_permutation_seed() == 12345

    def test_get_cv_folds_accessor(self):
        """Test the cv_folds accessor function."""
        os.environ["CV_FOLDS"] = "10"
        reset_config()
        assert get_cv_folds() == 10

    def test_get_fixed_region_indices_accessor(self):
        """Test the fixed_region_indices accessor function."""
        os.environ["FIXED_REGION_INDICES"] = "1,2,3,4,5"
        reset_config()
        assert get_fixed_region_indices() == (1, 2, 3, 4, 5)

    def test_get_regional_analysis_flag_accessor(self):
        """Test the regional_analysis_flag accessor function."""
        os.environ["REGIONAL_ANALYSIS_FLAG"] = "true"
        reset_config()
        assert get_regional_analysis_flag() is True

    def test_get_global_model_pvalue_threshold_accessor(self):
        """Test the global_model_pvalue_threshold accessor function."""
        os.environ["GLOBAL_MODEL_PVALUE_THRESHOLD"] = "0.01"
        reset_config()
        assert get_global_model_pvalue_threshold() == 0.01


class TestConfigIntegration:
    """Integration tests for configuration module."""

    def test_complete_config_workflow(self):
        """Test a complete configuration workflow with multiple overrides."""
        reset_config()
        os.environ["OPENNEURO_DATASET_ID"] = "ds_custom"
        os.environ["FD_THRESHOLD"] = "0.6"
        os.environ["VIF_THRESHOLD"] = "4.0"
        os.environ["PERMUTATION_SHUFFLES"] = "1500"
        os.environ["REGIONAL_ANALYSIS_FLAG"] = "true"

        config = Config.load_from_env()

        assert config.dataset.openneuro_dataset_id == "ds_custom"
        assert config.preprocessing.fd_threshold == 0.6
        assert config.centrality.vif_threshold == 4.0
        assert config.regression.permutation_shuffles == 1500
        assert config.centrality.regional_analysis_flag is True

        # Verify defaults remain for non-overridden values
        assert config.preprocessing.float32_conversion is True
        assert config.regression.model_type == "linear"
        assert config.output.figures_dir == "figures"