import pytest
import numpy as np
import mne
from pathlib import Path
import json
import tempfile
import os

# Import the function under test
from preprocessing import handle_missing_electrodes, update_metadata_with_validation

@pytest.fixture
def sample_raw():
    """Create a sample raw object with specific channels."""
    # Create info structure
    info = mne.create_info(ch_names=['F3', 'Fz', 'F4', 'P3', 'Pz', 'P4', 'EOG', 'ECG'],
                           sfreq=1000, ch_types=['eeg']*6 + ['eog', 'ecg'])
    # Create dummy data
    data = np.random.randn(len(info['ch_names']), 10000)
    raw = mne.io.RawArray(data, info)
    return raw

def test_handle_missing_electrodes_all_present(sample_raw):
    """Test when all required electrodes are present."""
    required = ['F3', 'Fz', 'F4', 'P3', 'Pz', 'P4']
    raw_out, skipped = handle_missing_electrodes(sample_raw, required)
    
    assert len(skipped) == 0
    assert all(ch in raw_out.ch_names for ch in required)
    # EOG and ECG should be dropped if we only keep EEG or if they are not in required
    # The function logic keeps only channels in 'required' if provided
    # So EOG/ECG should be dropped
    assert 'EOG' not in raw_out.ch_names
    assert 'ECG' not in raw_out.ch_names

def test_handle_missing_electrodes_some_missing(sample_raw):
    """Test when some required electrodes are missing."""
    # Modify raw to remove P4
    raw_missing = sample_raw.copy()
    raw_missing.drop_channels(['P4'])
    
    required = ['F3', 'Fz', 'F4', 'P3', 'Pz', 'P4']
    raw_out, skipped = handle_missing_electrodes(raw_missing, required)
    
    assert 'P4' in skipped
    assert 'P4' not in raw_out.ch_names
    assert all(ch in raw_out.ch_names for ch in ['F3', 'Fz', 'F4', 'P3', 'Pz'])

def test_handle_missing_electrodes_no_required_list(sample_raw):
    """Test when no required list is provided (keeps all EEG)."""
    raw_out, skipped = handle_missing_electrodes(sample_raw, required_ch_names=None)
    
    # Should keep all EEG channels
    expected_eeg = ['F3', 'Fz', 'F4', 'P3', 'Pz', 'P4']
    assert all(ch in raw_out.ch_names for ch in expected_eeg)
    # EOG/ECG might be dropped if logic filters by type, or kept if not.
    # Based on implementation: keeps channels where type is 'eeg'
    assert 'EOG' not in raw_out.ch_names
    assert 'ECG' not in raw_out.ch_names

def test_update_metadata_with_validation(tmp_path):
    """Test metadata update with skipped electrodes."""
    metadata_file = tmp_path / "metadata.json"
    skipped = ['P4', 'Pz']
    
    # Create initial file if needed
    update_metadata_with_validation(str(metadata_file), skipped)
    
    with open(metadata_file, 'r') as f:
        data = json.load(f)
    
    assert 'skipped_electrodes' in data
    assert 'P4' in data['skipped_electrodes']
    assert 'Pz' in data['skipped_electrodes']
    
    # Test appending
    update_metadata_with_validation(str(metadata_file), ['F3'])
    with open(metadata_file, 'r') as f:
        data = json.load(f)
    assert 'F3' in data['skipped_electrodes']
    assert len(data['skipped_electrodes']) == 3
