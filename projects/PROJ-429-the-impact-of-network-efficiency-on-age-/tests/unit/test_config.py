"""
Unit tests for code/config.py
"""
import pytest
from pathlib import Path
import sys
import os

# Add parent directory to path to allow imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.config import (
    PROJECT_ROOT,
    RAW_DATA_DIR,
    PROCESSED_DATA_DIR,
    QUALITY_DIR,
    RESULTS_DIR,
    FIGURES_DIR,
    STATE_DIR,
    CONFIG_DIR,
    EPOCH_LENGTH_SEC,
    BANDPASS_MIN_FREQ,
    BANDPASS_MAX_FREQ,
    SNR_THRESHOLD_DB,
    ARTIFACT_REJECTION_THRESHOLD,
    NETWORK_DENSITY_THRESHOLDS,
    COGNITIVE_INSTRUMENT_REGISTRY_PATH,
    ensure_dirs,
    get_config_summary
)

def test_epoch_length_is_10():
    """Verify T014 design decision: epoch length is 10 seconds."""
    assert EPOCH_LENGTH_SEC == 10, "Epoch length must be 10 seconds per ratified design decision"

def test_bandpass_range():
    """Verify bandpass filter range."""
    assert BANDPASS_MIN_FREQ == 1.0
    assert BANDPASS_MAX_FREQ == 40.0

def test_snr_threshold():
    """Verify SNR threshold is 10dB."""
    assert SNR_THRESHOLD_DB == 10.0

def test_artifact_rejection_threshold():
    """Verify artifact rejection threshold is 0.5 (50%)."""
    assert ARTIFACT_REJECTION_THRESHOLD == 0.5

def test_network_density_thresholds():
    """Verify sensitivity analysis thresholds exist."""
    assert len(NETWORK_DENSITY_THRESHOLDS) == 3
    assert 0.1 in NETWORK_DENSITY_THRESHOLDS
    assert 0.3 in NETWORK_DENSITY_THRESHOLDS
    assert 0.5 in NETWORK_DENSITY_THRESHOLDS

def test_cognitive_registry_path():
    """Verify cognitive instrument registry path is set correctly."""
    expected = PROJECT_ROOT / 'data' / 'config' / 'cognitive_instrument_registry.yaml'
    assert COGNITIVE_INSTRUMENT_REGISTRY_PATH == expected

def test_ensure_dirs_creates_directories(tmp_path, monkeypatch):
    """Test that ensure_dirs creates required directories."""
    # Mock PROJECT_ROOT to a temporary directory for testing
    mock_root = tmp_path
    monkeypatch.setattr('code.config.PROJECT_ROOT', mock_root)
    
    # Re-import to pick up the new root (simulating fresh state)
    # In real usage, this would be called once at startup
    dirs = ensure_dirs()
    
    for d in dirs:
        assert d.exists(), f"Directory {d} should have been created"

def test_get_config_summary():
    """Test that get_config_summary returns expected keys."""
    summary = get_config_summary()
    
    expected_keys = [
        'epoch_length_sec',
        'bandpass_min_freq',
        'bandpass_max_freq',
        'snr_threshold_db',
        'artifact_rejection_threshold',
        'network_density_thresholds',
        'cognitive_instrument_registry'
    ]
    
    for key in expected_keys:
        assert key in summary, f"Config summary missing key: {key}"
    
    assert summary['epoch_length_sec'] == 10