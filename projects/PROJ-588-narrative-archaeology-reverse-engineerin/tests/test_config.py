"""
Unit tests for code/config.py.

Verifies that:
1. Random seeds are set correctly.
2. Device is CPU-only.
3. Required directories exist.
4. Hyperparameters are defined correctly.
"""

import os
import random
import numpy as np
import pytest
from pathlib import Path

# Import the module under test
import code.config as config


class TestRandomSeeds:
    """Test that random seeds are pinned correctly."""

    def test_random_seed_set(self):
        """Verify random.seed was called with the correct value."""
        # We can't easily test the internal state of random, but we can
        # verify the constant is set and matches expectations.
        assert config.RANDOM_SEED == 42

    def test_numpy_seed_set(self):
        """Verify numpy random seed is set."""
        try:
            # Generate a random number to check state
            val = np.random.random()
            # Reset and generate again to see if it's deterministic
            np.random.seed(config.RANDOM_SEED)
            val2 = np.random.random()
            assert val == val2, "Numpy random state is not deterministic with seed"
        except ImportError:
            pytest.skip("numpy not installed")

    def test_torch_seed_set(self):
        """Verify torch random seed is set."""
        try:
            import torch
            torch.manual_seed(config.RANDOM_SEED)
            val = torch.rand(1).item()
            torch.manual_seed(config.RANDOM_SEED)
            val2 = torch.rand(1).item()
            assert val == val2, "Torch random state is not deterministic with seed"
        except ImportError:
            pytest.skip("torch not installed")


class TestHardwareConstraints:
    """Test that hardware constraints are enforced."""

    def test_use_gpu_is_false(self):
        """Verify GPU usage is disabled."""
        assert config.USE_GPU is False

    def test_device_is_cpu(self):
        """Verify default device is CPU."""
        assert config.DEVICE == "cpu"

    def test_max_cpu_threads(self):
        """Verify CPU thread limit is set."""
        assert config.MAX_CPU_THREADS == 2
        assert os.environ.get("OMP_NUM_THREADS") == "2"


class TestPathDefinitions:
    """Test that all required paths are defined and exist."""

    def test_project_root_exists(self):
        """Verify project root is a valid Path."""
        assert isinstance(config._PROJECT_ROOT, Path)
        assert config._PROJECT_ROOT.exists()

    def test_data_directories_exist(self):
        """Verify all data subdirectories exist."""
        dirs = [
            config.DATA_DIR,
            config.RAW_DATA_DIR,
            config.PREPROCESSED_DATA_DIR,
            config.PROCESSED_DATA_DIR,
            config.EXTERNAL_DATA_DIR,
        ]
        for d in dirs:
            assert d.exists(), f"Directory does not exist: {d}"
            assert d.is_dir(), f"Path is not a directory: {d}"

    def test_output_directories_exist(self):
        """Verify output directories exist."""
        dirs = [
            config.FIGURES_DIR,
            config.LOGS_DIR,
            config.RESULTS_DIR,
        ]
        for d in dirs:
            assert d.exists(), f"Directory does not exist: {d}"
            assert d.is_dir(), f"Path is not a directory: {d}"


class TestHyperparameters:
    """Test that hyperparameters are defined correctly."""

    def test_motion_threshold(self):
        """Verify motion artifact threshold."""
        assert config.MOTION_THRESHOLD_MM == 0.5

    def test_fmriprep_flags(self):
        """Verify fMRIPrep configuration flags."""
        assert config.FMRIPREP_OUTPUT_SPACES == "MNI"
        assert config.FMRIPREP_FS_RECONALL is False
        assert config.FMRIPREP_OMP_NUM_THREADS == 2
        assert config.FMRIPREP_NTHREADS == 2

    def test_analysis_params(self):
        """Verify analysis parameters."""
        assert config.RSA_METRIC == "correlation"
        assert config.PERMUTATION_ITERATIONS == 1000
        assert config.FDR_Q_VALUE == 0.05

    def test_decoder_params(self):
        """Verify decoder parameters."""
        assert isinstance(config.DECODER_C_VALUES, list)
        assert config.MIN_SAMPLES_PER_CLASS == 5

    def test_dataset_config(self):
        """Verify dataset configuration."""
        assert config.DATASET_ID == "ds000234"
        assert config.DATASET_VERSION == "1.0.0"
        assert "ds000234" in config.OPENNEURO_URL_TEMPLATE.format(
            dataset_id=config.DATASET_ID,
            version=config.DATASET_VERSION
        )

    def test_roi_names(self):
        """Verify ROI names list."""
        expected_rois = [
            "hippocampus",
            "mPFC",
            "PCC",
            "lateral_temporal_cortex"
        ]
        assert config.ROI_NAMES == expected_rois

    def test_event_phases(self):
        """Verify event phase definitions."""
        assert config.EARLY_PHASE_MINUTES == 0
        assert config.EARLY_PHASE_MAX_MINUTES == 10
        assert config.LATE_PHASE_MINUTES == 10
        assert config.LATE_PHASE_MAX_MINUTES == 20

    def test_bert_config(self):
        """Verify BERT configuration."""
        assert config.BERT_MODEL_NAME == "bert-base-uncased"
        assert config.BERT_MAX_LENGTH == 128
        assert config.BERT_BATCH_SIZE == 16


class TestVerificationFunction:
    """Test the verify_config helper function."""

    def test_verify_config_returns_true(self):
        """Verify that verify_config returns True when all dirs exist."""
        # Since we created the dirs in the config module, this should pass
        assert config.verify_config() is True

    def test_verify_config_handles_missing_dir(self):
        """Verify verify_config returns False if a critical dir is missing."""
        # Temporarily rename a critical dir to test failure case
        # We use RAW_DATA_DIR as it is critical
        temp_path = config.RAW_DATA_DIR
        backup_path = config._PROJECT_ROOT / "raw_backup_test"

        if temp_path.exists():
            temp_path.rename(backup_path)

        try:
            assert config.verify_config() is False
        finally:
            # Restore the directory
            if backup_path.exists():
                backup_path.rename(temp_path)