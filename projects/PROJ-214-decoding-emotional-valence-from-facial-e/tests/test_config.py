"""
Unit tests for code/config.py
"""

import pytest
from pathlib import Path
import sys
import os

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from code.config import (
    PROJECT_ROOT,
    DIR_DATA_RAW,
    DIR_DATA_PROCESSED,
    DIR_DATA_MODELS,
    DIR_FIGURES,
    RANDOM_SEED,
    SAMPLE_RATE,
    EMG_CHANNELS_OF_INTEREST,
    FEATURES_TO_EXTRACT,
    RF_N_ESTIMATORS,
    get_feature_dimension,
    get_window_samples,
    get_baseline_samples
)

def test_project_root_exists():
    """Verify PROJECT_ROOT is a valid Path."""
    assert isinstance(PROJECT_ROOT, Path)
    assert PROJECT_ROOT.exists()

def test_directories_exist():
    """Verify all required directories are created."""
    for d in [DIR_DATA_RAW, DIR_DATA_PROCESSED, DIR_DATA_MODELS, DIR_FIGURES]:
        assert d.exists()
        assert d.is_dir()

def test_random_seed():
    """Verify random seed is an integer."""
    assert isinstance(RANDOM_SEED, int)
    assert RANDOM_SEED >= 0

def test_sample_rate():
    """Verify sample rate matches DEAP standard (512 Hz)."""
    assert SAMPLE_RATE == 512

def test_emg_channels():
    """Verify EMG channels of interest are defined."""
    assert len(EMG_CHANNELS_OF_INTEREST) == 3
    assert "EMG_Corrugator" in EMG_CHANNELS_OF_INTEREST
    assert "EMG_Zygomaticus" in EMG_CHANNELS_OF_INTEREST
    assert "EMG_Orbicularis" in EMG_CHANNELS_OF_INTEREST

def test_features_list():
    """Verify feature list is defined."""
    assert len(FEATURES_TO_EXTRACT) == 4
    assert "RMS" in FEATURES_TO_EXTRACT
    assert "ZCR" in FEATURES_TO_EXTRACT
    assert "WAMP" in FEATURES_TO_EXTRACT
    assert "MAV" in FEATURES_TO_EXTRACT

def test_rf_n_estimators():
    """Verify Random Forest hyperparameter."""
    assert RF_N_ESTIMATORS == 100

def test_feature_dimension_calculation():
    """Verify feature dimension calculation: 3 muscles * 4 features."""
    expected = 3 * 4
    assert get_feature_dimension() == expected

def test_window_samples_calculation():
    """Verify window samples: 1.0s * 512Hz = 512."""
    expected = 512
    assert get_window_samples() == expected

def test_baseline_samples_calculation():
    """Verify baseline samples: 2.0s * 512Hz = 1024."""
    expected = 1024
    assert get_baseline_samples() == expected