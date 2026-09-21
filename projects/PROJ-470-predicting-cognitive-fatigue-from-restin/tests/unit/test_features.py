"""Tests for feature extraction module (T016)."""
import os
import pytest
import pandas as pd
import numpy as np
from unittest.mock import patch, MagicMock

# Import the module
from code.features import (
    calculate_lempel_ziv_complexity,
    calculate_permutation_entropy,
    process_eeg_segments,
    main
)

def test_lzc_basic():
    """Test that LZC returns a value within expected range."""
    # Create a random signal
    signal = np.random.randn(1000)
    lzc = calculate_lempel_ziv_complexity(signal)
    # LZC should be between 0 and 1 (normalized)
    assert 0.0 <= lzc <= 1.0, f"LZC {lzc} out of range [0, 1]"

def test_pe_basic():
    """Test that PE returns a value within expected range."""
    signal = np.random.randn(1000)
    pe = calculate_permutation_entropy(signal, order=3, delay=1)
    # PE should be between 0 and 1 (normalized)
    assert 0.0 <= pe <= 1.0, f"PE {pe} out of range [0, 1]"

def test_pe_order_3():
    """Test PE with order=3 (6 permutations)."""
    # A constant signal should have PE=0
    signal = np.ones(100)
    pe = calculate_permutation_entropy(signal, order=3, delay=1)
    assert pe == 0.0, "Constant signal should have PE=0"

    # A random signal should have PE > 0
    signal = np.random.randn(1000)
    pe = calculate_permutation_entropy(signal, order=3, delay=1)
    assert pe > 0.0, "Random signal should have PE > 0"

def test_process_eeg_segments_structure():
    """Test that process_eeg_segments returns a DataFrame with correct columns."""
    # Mock MNE raw object
    mock_raw = MagicMock()
    mock_raw.ch_names = ['Fz', 'Cz', 'Pz']
    mock_raw.info = {
        'sfreq': 250.0,
        'subject_info': {'his_id': 'sub-001'}
    }
    # Create dummy data: 3 channels, 30000 samples (120s)
    mock_data = np.random.randn(3, 30000)
    mock_raw.get_data.return_value = (mock_data, None)

    config = {}
    mock_logger = MagicMock()

    df = process_eeg_segments(mock_raw, config, mock_logger)

    assert isinstance(df, pd.DataFrame)
    expected_cols = ['participant_id', 'channel', 'segment_id', 'lzc_value', 'pe_value']
    assert list(df.columns) == expected_cols, f"Columns mismatch: {list(df.columns)}"
    assert len(df) == 3, "Should have 3 rows (one per channel)"

def test_main_integration():
    """Test that main() writes the output file."""
    # This is a bit tricky because it requires a real file.
    # We will mock the file existence and the mne loading.
    with patch('os.path.exists', return_value=True):
        with patch('mne.io.read_raw_fif') as mock_read:
            # Mock raw object
            mock_raw = MagicMock()
            mock_raw.ch_names = ['Fz']
            mock_raw.info = {'sfreq': 250.0, 'subject_info': {'his_id': 'sub-001'}}
            mock_raw.get_data.return_value = (np.random.randn(1, 30000), None)
            mock_read.return_value = mock_raw

            with patch('code.features.save_metrics_to_csv') as mock_save:
                main()
                mock_save.assert_called_once()
                # Check the path passed to save_metrics_to_csv
                call_args = mock_save.call_args
                df = call_args[0][0]
                path = call_args[0][1]
                assert path == "data/analysis/complexity_metrics.csv"
                assert 'lzc_value' in df.columns
                assert 'pe_value' in df.columns
