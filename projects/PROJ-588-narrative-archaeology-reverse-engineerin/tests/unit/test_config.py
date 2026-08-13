"""
Unit tests for configuration module.
"""
import pytest
from pathlib import Path
import numpy as np
import code.config as config

def test_random_seed_is_set():
    """Test that the random seed is properly set."""
    assert config.RANDOM_SEED == 42
    # Verify numpy random is reproducible
    np.random.seed(config.RANDOM_SEED)
    val1 = np.random.rand()
    np.random.seed(config.RANDOM_SEED)
    val2 = np.random.rand()
    assert val1 == val2

def test_project_root_exists():
    """Test that project root is a valid Path."""
    assert isinstance(config.PROJECT_ROOT, Path)
    assert config.PROJECT_ROOT.exists()

def test_data_directories_exist():
    """Test that data directories are created."""
    assert config.DATA_DIR.exists()
    assert config.RAW_DATA_DIR.exists()
    assert config.PROCESSED_DATA_DIR.exists()
    assert config.SEGMENTED_DATA_DIR.exists()
    assert config.FIGURES_DIR.exists()

def test_fmriprep_flags():
    """Test that fMRIPrep flags are correctly configured."""
    flags = config.FMRIPREP_FLAGS
    assert "--output-spaces" in flags
    assert "MNI" in flags
    assert "--fs-no-reconall" in flags
    assert "--omp-num-threads" in flags
    assert "2" in flags
    assert "--nthreads" in flags
    assert "2" in flags

def test_motion_threshold():
    """Test motion artifact threshold."""
    assert config.MOTION_THRESHOLD_MM > 0
    assert config.MOTION_THRESHOLD_MM < 10.0

def test_analysis_parameters():
    """Test analysis parameters are valid."""
    assert config.N_PERMUTATIONS > 0
    assert 0 < config.FDR_Q < 1.0
    assert config.N_FOLDS > 1

def test_cpu_only_constraint():
    """Test that CPU-only is enforced."""
    assert config.FORCE_CPU is True

def test_max_memory():
    """Test memory limit is reasonable."""
    assert 1.0 <= config.MAX_MEMORY_GB <= 16.0

def test_openneuro_dataset():
    """Test OpenNeuro dataset configuration."""
    assert config.OPENNEURO_DATASET_ID.startswith("ds")
    assert config.OPENNEURO_VERSION is not None

def test_rois_defined():
    """Test that ROIs are defined."""
    assert len(config.ROIS) > 0
    assert "hippocampus" in config.ROIS
    assert "mPFC" in config.ROIS
    assert "PCC" in config.ROIS
    assert "lateral_temporal_cortex" in config.ROIS

def test_decoder_config():
    """Test decoder configuration."""
    assert config.MIN_SAMPLES_PER_CLASS > 0
    assert config.AGGREGATED_LABEL is not None