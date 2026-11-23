"""
Unit tests for code/config.py

Verifies:
- Random seeds are set correctly
- CPU-only constraints are enforced
- Path definitions are valid Path objects
- Analysis parameters are of correct types
"""

import os
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import code.config as config


def test_random_seed_exists():
    """Test that RANDOM_SEED is defined and is an integer."""
    assert hasattr(config, "RANDOM_SEED")
    assert isinstance(config.RANDOM_SEED, int)
    assert config.RANDOM_SEED == 42


def test_pythonhashseed_set():
    """Test that PYTHONHASHSEED environment variable is set."""
    assert "PYTHONHASHSEED" in os.environ
    assert os.environ["PYTHONHASHSEED"] == str(config.RANDOM_SEED)


def test_cpu_only_constraints():
    """Test that CPU-only constraints are enforced."""
    assert config.USE_CUDA is False
    assert config.N_CPUS == 2
    assert os.environ.get("CUDA_VISIBLE_DEVICES") == ""


def test_path_definitions():
    """Test that all path definitions are valid Path objects."""
    assert isinstance(config.ROOT_DIR, Path)
    assert isinstance(config.CODE_DIR, Path)
    assert isinstance(config.DATA_DIR, Path)
    assert isinstance(config.TESTS_DIR, Path)
    assert isinstance(config.SPECS_DIR, Path)
    assert isinstance(config.FIGURES_DIR, Path)
    assert isinstance(config.LOGS_DIR, Path)

    # Verify paths are absolute
    assert config.ROOT_DIR.is_absolute()
    assert config.CODE_DIR.is_absolute()


def test_analysis_parameters():
    """Test that analysis parameters are of correct types and values."""
    assert isinstance(config.MOTION_THRESHOLD_MM, float)
    assert config.MOTION_THRESHOLD_MM == 3.0

    assert isinstance(config.HRF_FWHM, float)
    assert config.HRF_FWHM == 6.0

    assert isinstance(config.RSA_METRIC, str)
    assert config.RSA_METRIC in ["correlation", "euclidean"]

    assert isinstance(config.DECODER_C, float)
    assert config.DECODER_C == 1.0

    assert isinstance(config.PERMUTATION_ITERATIONS, int)
    assert config.PERMUTATION_ITERATIONS == 1000

    assert isinstance(config.FDR_ALPHA, float)
    assert config.FDR_ALPHA == 0.05


def test_dataset_id():
    """Test that DATASET_ID is defined correctly."""
    assert hasattr(config, "DATASET_ID")
    assert config.DATASET_ID == "ds000234"


def test_log_configuration():
    """Test that logging configuration is defined."""
    assert isinstance(config.LOG_LEVEL, str)
    assert isinstance(config.LOG_FILE, Path)
    assert isinstance(config.ERROR_LOG_FILE, Path)


def test_data_paths():
    """Test that data path variables are defined."""
    assert isinstance(config.RAW_DATA_DIR, Path)
    assert isinstance(config.PREPROCESSED_DATA_DIR, Path)
    assert isinstance(config.EVENT_ANNOTATIONS_FILE, Path)
    assert isinstance(config.ROI_MASKS_DIR, Path)


def test_helper_functions():
    """Test that helper functions exist and return Path objects."""
    assert callable(config.get_data_path)
    assert callable(config.get_output_path)
    assert callable(config.get_figure_path)

    test_file = "test.txt"
    data_path = config.get_data_path(test_file)
    output_path = config.get_output_path(test_file)
    figure_path = config.get_figure_path(test_file)

    assert isinstance(data_path, Path)
    assert isinstance(output_path, Path)
    assert isinstance(figure_path, Path)

    assert data_path.name == test_file
    assert output_path.name == test_file
    assert figure_path.name == test_file