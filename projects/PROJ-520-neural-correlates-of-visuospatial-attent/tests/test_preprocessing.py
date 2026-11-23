"""
Tests for preprocessing module, specifically T016 (missing electrodes).
"""
import os
import json
import tempfile
from pathlib import Path
import numpy as np
import pytest

# Mock MNE if not available in test environment, but assume it's installed
try:
    import mne
    HAS_MNE = True
except ImportError:
    HAS_MNE = False
    pytest.skip("MNE not installed", allow_module_level=True)

from preprocessing import handle_missing_electrodes, preprocess_pipeline
from config import get_paths

@pytest.fixture
def mock_epochs_with_bad():
    """Create a mock MNE Epochs object with a known bad channel."""
    if not HAS_MNE:
        return None
        
    # Create dummy data: 10 epochs, 5 channels, 100 time points
    n_epochs, n_channels, n_times = 10, 5, 100
    data = np.random.randn(n_epochs, n_channels, n_times)
    
    # Make channel index 2 (3rd channel) all NaN
    data[:, 2, :] = np.nan
    
    # Create info
    info = mne.create_info(ch_names=['A1', 'A2', 'A3', 'A4', 'A5'], 
                           sfreq=100, ch_types='eeg')
    
    # Create epochs
    epochs = mne.EpochsArray(data, info)
    
    return epochs

@pytest.fixture
def temp_metadata(tmp_path):
    """Create a temporary metadata file."""
    metadata = {
        "pipeline_version": "1.0.0",
        "task_id": "T015",
        "assumptions": {"event_source": "standard_markers"},
        "validation_results": {}
    }
    path = tmp_path / "metadata.json"
    with open(path, 'w') as f:
        json.dump(metadata, f)
    return path

def test_handle_missing_electrodes_skips_nan(mock_epochs_with_bad, temp_metadata):
    """Test that T016 correctly identifies and skips NaN electrodes."""
    if not HAS_MNE:
        return
        
    epochs = mock_epochs_with_bad
    initial_channels = epochs.ch_names.copy()
    
    # Run the function
    cleaned_epochs, skipped = handle_missing_electrodes(epochs, temp_metadata)
    
    # Verify the bad channel was skipped
    assert 'A3' in skipped, "A3 should be in skipped list"
    assert 'A3' not in cleaned_epochs.ch_names, "A3 should be dropped from epochs"
    assert len(cleaned_epochs.ch_names) == len(initial_channels) - 1, "Channel count should decrease by 1"
    
    # Verify metadata was updated
    with open(temp_metadata, 'r') as f:
        meta = json.load(f)
    assert 'skipped_electrodes' in meta, "metadata should contain skipped_electrodes key"
    assert 'A3' in meta['skipped_electrodes'], "A3 should be in metadata skipped list"

def test_handle_missing_electrodes_no_missing(mock_epochs_with_bad, temp_metadata):
    """Test that T016 handles the case where no electrodes are missing."""
    if not HAS_MNE:
        return
        
    epochs = mock_epochs_with_bad
    # Remove NaN from the bad channel to simulate good data
    epochs._data[:, 2, :] = np.random.randn(10, 100)
    
    cleaned_epochs, skipped = handle_missing_electrodes(epochs, temp_metadata)
    
    assert len(skipped) == 0, "No electrodes should be skipped"
    assert len(cleaned_epochs.ch_names) == len(epochs.ch_names), "Channel count should remain same"
    
    with open(temp_metadata, 'r') as f:
        meta = json.load(f)
    # Should either not have the key or have an empty list if it was there
    skipped_list = meta.get('skipped_electrodes', [])
    assert len(skipped_list) == 0 or 'A3' not in skipped_list, "A3 should not be in skipped list"