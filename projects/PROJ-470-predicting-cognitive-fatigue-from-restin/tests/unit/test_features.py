"""
Unit tests for feature extraction module.
"""
import os
import sys
import pytest
import numpy as np
import pandas as pd
import mne
from unittest.mock import patch, MagicMock

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
from code.features import (
    calculate_lempel_ziv_complexity,
    calculate_permutation_entropy,
    process_eeg_segments,
    save_metrics_to_csv,
    main
)

def test_calculate_lempel_ziv_complexity():
    """Test LZC calculation with known inputs."""
    # Constant signal should have low complexity
    const_signal = np.ones(1000)
    lzc_const = calculate_lempel_ziv_complexity(const_signal)
    assert lzc_const < 0.1  # Very low complexity
    
    # Random signal should have higher complexity
    np.random.seed(42)
    rand_signal = np.random.rand(1000)
    lzc_rand = calculate_lempel_ziv_complexity(rand_signal)
    assert lzc_rand > 0.5  # Higher complexity
    
    # Check range
    assert 0 <= lzc_const <= 1
    assert 0 <= lzc_rand <= 1

def test_calculate_permutation_entropy():
    """Test PE calculation with known inputs."""
    # Constant signal should have low entropy
    const_signal = np.ones(1000)
    pe_const = calculate_permutation_entropy(const_signal)
    assert pe_const < 0.1  # Very low entropy
    
    # Random signal should have higher entropy
    np.random.seed(42)
    rand_signal = np.random.rand(1000)
    pe_rand = calculate_permutation_entropy(rand_signal)
    assert pe_rand > 0.5  # Higher entropy
    
    # Check range (normalized 0-1)
    assert 0 <= pe_const <= 1
    assert 0 <= pe_rand <= 1

def test_process_eeg_segments():
    """Test EEG segment processing."""
    # Create dummy EEG data
    n_channels = 5
    n_samples = 10000
    sfreq = 250
    info = mne.create_info(n_channels, sfreq, ch_types='eeg')
    data = np.random.rand(n_channels, n_samples)
    raw = mne.io.RawArray(data, info)
    
    config = {
        'filter_low': 1,
        'filter_high': 40
    }
    
    metrics = process_eeg_segments(raw, "sub-001", "seg-001", config, MagicMock())
    
    assert len(metrics) == n_channels
    for m in metrics:
        assert m['participant_id'] == "sub-001"
        assert m['segment_id'] == "seg-001"
        assert 'lzc_value' in m
        assert 'pe_value' in m
        assert 0 <= m['lzc_value'] <= 1
        assert 0 <= m['pe_value'] <= 1

def test_save_metrics_to_csv(tmp_path):
    """Test saving metrics to CSV."""
    metrics = [
        {'participant_id': 'sub-001', 'channel': 'Cz', 'segment_id': 'seg-001', 'lzc_value': 0.5, 'pe_value': 0.6},
        {'participant_id': 'sub-001', 'channel': 'Pz', 'segment_id': 'seg-001', 'lzc_value': 0.4, 'pe_value': 0.7}
    ]
    output_file = tmp_path / "test_metrics.csv"
    
    save_metrics_to_csv(metrics, str(output_file))
    
    assert output_file.exists()
    df = pd.read_csv(output_file)
    assert len(df) == 2
    assert list(df.columns) == ['participant_id', 'channel', 'segment_id', 'lzc_value', 'pe_value']
    assert 'pe_value' in df.columns

def test_save_empty_metrics_to_csv(tmp_path):
    """Test saving empty metrics to CSV."""
    metrics = []
    output_file = tmp_path / "test_empty_metrics.csv"
    
    save_metrics_to_csv(metrics, str(output_file))
    
    assert output_file.exists()
    df = pd.read_csv(output_file)
    assert len(df) == 0
    assert list(df.columns) == ['participant_id', 'channel', 'segment_id', 'lzc_value', 'pe_value']

@patch('code.features.mne.io.read_raw_fif')
@patch('code.features.process_eeg_segments')
@patch('code.features.save_metrics_to_csv')
def test_main(mock_save, mock_process, mock_read, tmp_path, monkeypatch):
    """Test main function."""
    # Setup mocks
    mock_raw = MagicMock()
    mock_raw.ch_names = ['Cz', 'Pz']
    mock_raw.info = {'sfreq': 250, 'nchan': 2}
    mock_read.return_value = mock_raw
    mock_process.return_value = [
        {'participant_id': 'sub-001', 'channel': 'Cz', 'segment_id': 'seg-001', 'lzc_value': 0.5, 'pe_value': 0.6},
        {'participant_id': 'sub-001', 'channel': 'Pz', 'segment_id': 'seg-001', 'lzc_value': 0.4, 'pe_value': 0.7}
    ]
    
    # Create dummy input file
    input_file = tmp_path / "cleaned_eeg.fif"
    input_file.touch()
    
    # Create output directory
    output_dir = tmp_path / "analysis"
    output_dir.mkdir()
    output_file = output_dir / "complexity_metrics.csv"
    
    # Patch paths
    monkeypatch.setattr('code.features.input_file', str(input_file))
    monkeypatch.setattr('code.features.output_file', str(output_file))
    
    # Run main
    with patch('code.features.load_config', return_value={'filter_low': 1, 'filter_high': 40}):
        main()
    
    # Verify
    mock_read.assert_called_once()
    mock_process.assert_called_once()
    mock_save.assert_called_once()
    assert output_file.exists()