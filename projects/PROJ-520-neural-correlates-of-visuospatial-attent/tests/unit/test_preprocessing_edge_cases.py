import pytest
import os
import json
import numpy as np
import mne
from pathlib import Path

from preprocessing import handle_missing_electrodes, EpochingError
from config import get_paths

@pytest.fixture
def temp_metadata_path(tmp_path):
    """Create a temporary metadata file path."""
    path = tmp_path / "metadata.json"
    # Initialize with empty schema
    with open(path, 'w') as f:
        json.dump({'skipped_electrodes': [], 'assumptions': {}, 'data_source_url': None, 'fetch_method': None}, f)
    return str(path)

@pytest.fixture
def raw_with_bad_channels(tmp_path):
    """Create a mock MNE Raw object with some bad channels."""
    # Create mock info
    info = mne.create_info(ch_names=['EEG 001', 'EEG 002', 'EEG 003', 'EEG 004'], 
                           sfreq=1000, ch_types='eeg')
    
    # Create data: 4 channels, 1000 samples
    # Channel 0: Good data
    # Channel 1: All NaN
    # Channel 2: Constant (dead)
    # Channel 3: 60% NaN
    data = np.random.randn(4, 1000)
    data[1, :] = np.nan
    data[2, :] = 0.0
    data[3, :400] = np.nan
    
    raw = mne.io.RawArray(data, info)
    return raw

def test_missing_electrodes_all_nan(temp_metadata_path, raw_with_bad_channels):
    """Test that electrodes with all NaN are skipped."""
    skipped = handle_missing_electrodes(raw_with_bad_channels, temp_metadata_path)
    
    # Check that the all-NaN channel is skipped
    assert 'EEG 002' in skipped
    
    # Check metadata update
    with open(temp_metadata_path, 'r') as f:
        metadata = json.load(f)
    assert 'EEG 002' in metadata['skipped_electrodes']

def test_missing_electrodes_dead_channel(temp_metadata_path, raw_with_bad_channels):
    """Test that dead channels (zero variance) are skipped."""
    skipped = handle_missing_electrodes(raw_with_bad_channels, temp_metadata_path)
    
    # Check that the dead channel is skipped
    assert 'EEG 003' in skipped
    
    # Check metadata update
    with open(temp_metadata_path, 'r') as f:
        metadata = json.load(f)
    assert 'EEG 003' in metadata['skipped_electrodes']

def test_missing_electrodes_high_nan_ratio(temp_metadata_path, raw_with_bad_channels):
    """Test that channels with >50% NaN are skipped."""
    skipped = handle_missing_electrodes(raw_with_bad_channels, temp_metadata_path)
    
    # Check that the high-NaN channel is skipped
    assert 'EEG 004' in skipped
    
    # Check metadata update
    with open(temp_metadata_path, 'r') as f:
        metadata = json.load(f)
    assert 'EEG 004' in metadata['skipped_electrodes']

def test_missing_electrodes_good_channel_kept(temp_metadata_path, raw_with_bad_channels):
    """Test that good channels are not skipped."""
    skipped = handle_missing_electrodes(raw_with_bad_channels, temp_metadata_path)
    
    # Check that the good channel is NOT skipped
    assert 'EEG 001' not in skipped
    
    # Check raw channels after dropping
    assert 'EEG 001' in raw_with_bad_channels.info['ch_names']

def test_missing_electrodes_metadata_persistence(temp_metadata_path, raw_with_bad_channels):
    """Test that metadata is correctly updated and persisted."""
    # Run twice to ensure accumulation
    handle_missing_electrodes(raw_with_bad_channels, temp_metadata_path)
    handle_missing_electrodes(raw_with_bad_channels, temp_metadata_path)
    
    with open(temp_metadata_path, 'r') as f:
        metadata = json.load(f)
    
    # Should not have duplicates
    assert len(metadata['skipped_electrodes']) == len(set(metadata['skipped_electrodes']))
    assert len(metadata['skipped_electrodes']) >= 3  # At least the 3 bad channels
