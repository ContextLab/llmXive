"""
Tests for T017: Saving preprocessed epochs.
Verifies that the pipeline produces a valid .fif file with correct structure.
"""
import os
import json
import tempfile
from pathlib import Path
import pytest
import numpy as np
import mne

# Mock the dependencies to avoid full data download in unit tests
# We will test the *save* logic by creating a mock epochs object
# and ensuring the function that saves it works correctly.

from preprocessing import validate_sample_size, update_metadata_with_validation

@pytest.fixture
def mock_epochs():
    """Create a mock MNE Epochs object for testing."""
    # Create dummy data: 100 epochs, 64 channels, 200 time points
    n_epochs = 100
    n_channels = 64
    n_times = 200
    sfreq = 100.0
    
    data = np.random.randn(n_epochs, n_channels, n_times)
    info = mne.create_info(n_channels, sfreq, ch_types='eeg')
    
    # Create events
    events = np.array([
        [i * 100, 0, 1] if i % 2 == 0 else [i * 100, 0, 2] 
        for i in range(n_epochs)
    ])
    
    event_id = {'active': 1, 'passive': 2}
    
    epochs = mne.EpochsArray(
        data, 
        info, 
        events=events, 
        event_id=event_id,
        tmin=-1.0
    )
    epochs.metadata = mne.epochs.make_metadata(
        row_events=['stimulus'], 
        key_events=[], 
        time_events=['time'],
        sfreq=sfreq,
        n_rows=n_epochs
    )
    # Add a dummy 'condition' column to metadata for T014 test
    epochs.metadata['condition'] = ['active' if e[2] == 1 else 'passive' for e in events]
    
    return epochs

def test_validate_sample_size_pass(mock_epochs):
    """Test that validation passes when epochs >= 100."""
    is_valid, status, counts = validate_sample_size(mock_epochs, 'condition')
    assert is_valid is True
    assert status == "PASS"
    assert counts['active'] == 50
    assert counts['passive'] == 50

def test_validate_sample_size_warning(mock_epochs):
    """Test that validation warns when epochs < 100 but >= 50."""
    # Slice to 80 epochs (40 per condition)
    sliced_epochs = mock_epochs[:80]
    is_valid, status, counts = validate_sample_size(sliced_epochs, 'condition')
    assert is_valid is True
    assert status == "WARNING"
    assert counts['active'] == 40
    assert counts['passive'] == 40

def test_validate_sample_size_fail(mock_epochs):
    """Test that validation fails when epochs < 50."""
    # Slice to 40 epochs (20 per condition)
    sliced_epochs = mock_epochs[:40]
    with pytest.raises(ValueError, match="CRITICAL: Sample size too low"):
        validate_sample_size(sliced_epochs, 'condition')

def test_update_metadata_with_validation(tmp_path, mock_epochs):
    """Test that metadata file is updated correctly."""
    metadata_path = tmp_path / "metadata.json"
    
    # Create initial empty metadata
    metadata_path.write_text("{}")
    
    counts = {'active': 50, 'passive': 50}
    status = "PASS"
    
    update_metadata_with_validation(metadata_path, counts, status)
    
    with open(metadata_path, 'r') as f:
        data = json.load(f)
    
    assert 'validation' in data
    assert data['validation']['sample_size_check']['status'] == "PASS"
    assert data['validation']['sample_size_check']['counts'] == counts
    assert data['validation']['sample_size_check']['min_required'] == 50

def test_save_epochs_fif(tmp_path, mock_epochs):
    """Test that epochs can be saved to .fif format."""
    output_path = tmp_path / "test_epochs.fif"
    mock_epochs.save(output_path, overwrite=True)
    
    assert output_path.exists()
    assert output_path.suffix == '.fif'
    
    # Verify we can load it back
    loaded_epochs = mne.read_epochs(output_path)
    assert len(loaded_epochs) == len(mock_epochs)
    assert loaded_epochs.info['nchan'] == mock_epochs.info['nchan']
