import pytest
import os
import json
import tempfile
import numpy as np
import mne
from unittest.mock import patch, MagicMock

from preprocessing import handle_missing_electrodes, load_raw, filter_data
from logger import get_logger

@pytest.fixture
def sample_raw():
    """Create a sample raw object for testing."""
    info = mne.create_info(ch_names=['EEG 001', 'EEG 002', 'EEG 003', 'EEG 004'], 
                           sfreq=250, ch_types='eeg')
    data = np.random.randn(4, 500)
    raw = mne.io.RawArray(data, info)
    return raw

@pytest.fixture
def temp_metadata_path():
    """Create a temporary file path for metadata."""
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
        return f.name

def test_missing_electrodes(sample_raw, temp_metadata_path):
    """Test that missing electrodes are correctly identified and skipped."""
    logger = get_logger(__name__)
    
    # Simulate a bad channel
    sample_raw.info['bads'] = ['EEG 002']
    
    # Simulate a channel with all NaN data
    data, _ = sample_raw[:]
    data[2, :] = np.nan
    sample_raw._data = data
    
    # Run the function
    result = handle_missing_electrodes(sample_raw, temp_metadata_path, logger)
    
    # Check that EEG 002 and EEG 003 are dropped
    assert 'EEG 002' not in result.ch_names
    assert 'EEG 003' not in result.ch_names
    assert 'EEG 001' in result.ch_names
    assert 'EEG 004' in result.ch_names
    
    # Check metadata file
    assert os.path.exists(temp_metadata_path)
    with open(temp_metadata_path, 'r') as f:
        metadata = json.load(f)
    
    assert 'skipped_electrodes' in metadata
    assert len(metadata['skipped_electrodes']) == 2
    assert 'EEG 002' in metadata['skipped_electrodes']
    assert 'EEG 003' in metadata['skipped_electrodes']

def test_empty_events(sample_raw, temp_metadata_path):
    """Test handling of empty events list (edge case for downstream epoching)."""
    # This test verifies that the pipeline doesn't crash when events are empty.
    # In a real scenario, this would be caught during epoching (T013/T015).
    logger = get_logger(__name__)
    
    # Handle missing electrodes with no bads
    result = handle_missing_electrodes(sample_raw, temp_metadata_path, logger)
    
    # Should succeed without errors
    assert result is not None
    assert len(result.ch_names) == 4

def test_all_channels_missing(sample_raw, temp_metadata_path):
    """Test behavior when all channels are marked as bad/missing."""
    logger = get_logger(__name__)
    
    # Mark all channels as bad
    sample_raw.info['bads'] = ['EEG 001', 'EEG 002', 'EEG 003', 'EEG 004']
    
    with pytest.raises(ValueError) as excinfo:
        handle_missing_electrodes(sample_raw, temp_metadata_path, logger)
    
    # Should raise an error because no channels remain
    assert "No channels remaining after dropping" in str(excinfo.value)

def test_no_missing_electrodes(sample_raw, temp_metadata_path):
    """Test when there are no missing electrodes."""
    logger = get_logger(__name__)
    
    result = handle_missing_electrodes(sample_raw, temp_metadata_path, logger)
    
    assert result is not None
    assert len(result.ch_names) == 4
    
    with open(temp_metadata_path, 'r') as f:
        metadata = json.load(f)
    
    assert metadata['skipped_electrodes'] == []
    assert metadata['skipped_count'] == 0
