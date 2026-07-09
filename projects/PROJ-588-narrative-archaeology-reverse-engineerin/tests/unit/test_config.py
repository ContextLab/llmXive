"""
Unit tests for code/config.py
"""
import os
import sys
import pytest
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import code.config as config

class TestConfigSeeds:
    """Test random seed initialization and constants."""

    def test_random_seed_constant(self):
        """Verify RANDOM_SEED is an integer."""
        assert isinstance(config.RANDOM_SEED, int)
        assert config.RANDOM_SEED == 42

    def test_numpy_seed_constant(self):
        """Verify NUMPY_SEED is an integer."""
        assert isinstance(config.NUMPY_SEED, int)
        assert config.NUMPY_SEED == 42

    def test_torch_seed_constant(self):
        """Verify TORCH_SEED is an integer."""
        assert isinstance(config.TORCH_SEED, int)
        assert config.TORCH_SEED == 42

    def test_sklearn_seed_constant(self):
        """Verify SKLEARN_SEED is an integer."""
        assert isinstance(config.SKLEARN_SEED, int)
        assert config.SKLEARN_SEED == 42

class TestExecutionConstraints:
    """Test execution constraint settings."""

    def test_force_cpu_only(self):
        """Verify CPU-only constraint is enabled."""
        assert config.FORCE_CPU_ONLY is True

    def test_max_memory_gb(self):
        """Verify max memory constraint is set."""
        assert config.MAX_MEMORY_GB == 7.0

    def test_thread_count(self):
        """Verify thread count matches fMRIPrep constraints."""
        assert config.THREAD_COUNT == 2

    def test_cuda_visible_devices_env(self):
        """Verify CUDA_VISIBLE_DEVICES is set to empty string if torch is available."""
        # This is a side effect of the import in config.py
        # We check the environment variable was set
        assert os.environ.get("CUDA_VISIBLE_DEVICES") == ""

class TestProjectPaths:
    """Test path definitions."""

    def test_project_root_exists(self):
        """Verify PROJECT_ROOT is a valid Path object."""
        assert isinstance(config.PROJECT_ROOT, Path)
        assert config.PROJECT_ROOT.exists()

    def test_data_dir_exists(self):
        """Verify DATA_DIR is a valid Path object."""
        assert isinstance(config.DATA_DIR, Path)
        assert config.DATA_DIR.exists()

    def test_figures_dir_exists(self):
        """Verify FIGURES_DIR is a valid Path object."""
        assert isinstance(config.FIGURES_DIR, Path)
        assert config.FIGURES_DIR.exists()

    def test_logs_dir_exists(self):
        """Verify LOGS_DIR is a valid Path object."""
        assert isinstance(config.LOGS_DIR, Path)
        assert config.LOGS_DIR.exists()

    def test_raw_dir_exists(self):
        """Verify RAW_DIR is a valid Path object."""
        assert isinstance(config.RAW_DIR, Path)
        assert config.RAW_DIR.exists()

    def test_processed_dir_exists(self):
        """Verify PROCESSED_DIR is a valid Path object."""
        assert isinstance(config.PROCESSED_DIR, Path)
        assert config.PROCESSED_DIR.exists()

class TestDatasetConfiguration:
    """Test dataset and fMRIPrep configuration."""

    def test_openneuro_dataset_id(self):
        """Verify OpenNeuro dataset ID is correct."""
        assert config.OPENNEURO_DATASET_ID == "ds000234"

    def test_ci_subject_subset(self):
        """Verify CI subject subset is a list."""
        assert isinstance(config.CI_SUBJECT_SUBSET, list)
        assert len(config.CI_SUBJECT_SUBSET) > 0

    def test_fmriprep_flags(self):
        """Verify fMRIPrep flags are correctly configured."""
        assert isinstance(config.FMRIPREP_FLAGS, list)
        assert "--output-spaces" in config.FMRIPREP_FLAGS
        assert "MNI" in config.FMRIPREP_FLAGS
        assert "--fs-no-reconall" in config.FMRIPREP_FLAGS
        # Check thread count matches config
        assert str(config.THREAD_COUNT) in config.FMRIPREP_FLAGS

class TestAnalysisParameters:
    """Test analysis parameter constants."""

    def test_hrf_model(self):
        """Verify HRF model is set."""
        assert config.HRF_MODEL == "glover"

    def test_tr(self):
        """Verify TR value is set."""
        assert config.TR == 2.0

    def test_motion_threshold_mm(self):
        """Verify motion threshold is set."""
        assert config.MOTION_THRESHOLD_MM == 3.0

    def test_permutation_iterations(self):
        """Verify permutation iterations are set."""
        assert config.PERMUTATION_ITERATIONS == 1000

    def test_fdr_q_threshold(self):
        """Verify FDR q threshold is set."""
        assert config.FDR_Q_THRESHOLD == 0.05

    def test_classifier_type(self):
        """Verify classifier type is set."""
        assert config.CLASSIFIER_TYPE == "ridge"

    def test_n_folds(self):
        """Verify number of folds is set."""
        assert config.N_FOLDS == 5

    def test_min_samples_per_class(self):
        """Verify min samples per class is set."""
        assert config.MIN_SAMPLES_PER_CLASS == 5

    def test_distance_metric(self):
        """Verify distance metric is set."""
        assert config.DISTANCE_METRIC == "correlation"

class TestLoggingConfiguration:
    """Test logging configuration."""

    def test_log_level(self):
        """Verify log level is set."""
        assert config.LOG_LEVEL == "INFO"

    def test_log_format(self):
        """Verify log format is set."""
        assert isinstance(config.LOG_FORMAT, str)
        assert "%(asctime)s" in config.LOG_FORMAT

    def test_error_log_file(self):
        """Verify error log file path is set."""
        assert isinstance(config.ERROR_LOG_FILE, Path)
        assert config.ERROR_LOG_FILE.suffix == ".log"

class TestExternalDependencies:
    """Test external dependency flags."""

    def test_use_bert_features(self):
        """Verify BERT features flag is set."""
        assert config.USE_BERT_FEATURES is True

    def test_bert_model_name(self):
        """Verify BERT model name is set."""
        assert config.BERT_MODEL_NAME == "bert-base-uncased"

class TestValidateEnvironment:
    """Test the validate_environment function."""

    def test_validate_environment_returns_dict(self):
        """Verify validate_environment returns a dictionary."""
        result = config.validate_environment()
        assert isinstance(result, dict)

    def test_validate_environment_has_valid_key(self):
        """Verify validate_environment has 'valid' key."""
        result = config.validate_environment()
        assert "valid" in result
        assert isinstance(result["valid"], bool)

    def test_validate_environment_has_warnings_key(self):
        """Verify validate_environment has 'warnings' key."""
        result = config.validate_environment()
        assert "warnings" in result
        assert isinstance(result["warnings"], list)

    def test_validate_environment_has_config_key(self):
        """Verify validate_environment has 'config' key."""
        result = config.validate_environment()
        assert "config" in result
        assert isinstance(result["config"], dict)

    def test_validate_environment_config_seeds(self):
        """Verify validate_environment config contains seed info."""
        result = config.validate_environment()
        config_dict = result["config"]
        assert "random_seed" in config_dict
        assert config_dict["random_seed"] == 42
        assert "force_cpu_only" in config_dict
        assert config_dict["force_cpu_only"] is True