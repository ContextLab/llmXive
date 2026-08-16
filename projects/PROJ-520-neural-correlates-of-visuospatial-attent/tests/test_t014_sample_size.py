import pytest
import numpy as np
import mne
from pathlib import Path
import tempfile
import os

# Import the function to test
# We need to simulate the environment where this is imported from preprocessing
# Since we can't easily run the full pipeline in a unit test without data,
# we will mock the Epochs object or create a minimal one.

# Note: In a real CI environment, we would need to ensure mne is installed.
# For this test, we assume the function is accessible.

def create_mock_epochs(n_conditions=2, n_epochs_per_cond=60, n_times=100, n_channels=5):
    """Create a minimal MNE Epochs object for testing."""
    # Create dummy data
    info = mne.create_info(ch_names=[f'EEG {i:03d}' for i in range(n_channels)], 
                           sfreq=100.0, ch_types='eeg')
    data = np.random.randn(n_conditions * n_epochs_per_cond, n_channels, n_times)
    
    # Create events array
    events = np.zeros((n_conditions * n_epochs_per_cond, 3), dtype=int)
    events[:, 0] = np.arange(n_conditions * n_epochs_per_cond) * 100  # sample indices
    events[:, 2] = np.repeat([1, 2], n_epochs_per_cond)  # event codes
    
    event_id = {'active': 1, 'passive': 2}
    
    epochs = mne.EpochsArray(data, info, events, tmin=0.0, event_id=event_id)
    return epochs

def test_validate_sample_size_pass():
    """Test that validation passes when epochs >= 100 per condition."""
    epochs = create_mock_epochs(n_conditions=2, n_epochs_per_cond=110)
    
    from preprocessing import validate_sample_size
    
    result = validate_sample_size(epochs, min_threshold=50, warning_threshold=100)
    
    assert result["passed"] is True
    assert result["underpowered"] is False
    assert result["counts"]["active"] == 110
    assert result["counts"]["passive"] == 110
    assert result["min_count"] == 110

def test_validate_sample_size_underpowered():
    """Test that validation flags underpowered when 50 <= epochs < 100."""
    epochs = create_mock_epochs(n_conditions=2, n_epochs_per_cond=75)
    
    from preprocessing import validate_sample_size
    
    result = validate_sample_size(epochs, min_threshold=50, warning_threshold=100)
    
    assert result["passed"] is True
    assert result["underpowered"] is True
    assert result["counts"]["active"] == 75
    assert result["min_count"] == 75
    assert "Underpowered" in result["message"]

def test_validate_sample_size_fail():
    """Test that validation fails when epochs < 50."""
    epochs = create_mock_epochs(n_conditions=2, n_epochs_per_cond=40)
    
    from preprocessing import validate_sample_size
    
    with pytest.raises(ValueError, match="CRITICAL: Insufficient epochs"):
        validate_sample_size(epochs, min_threshold=50, warning_threshold=100)

def test_validate_sample_size_uneven_conditions():
    """Test validation when conditions have different counts."""
    # Create custom epochs with uneven counts
    info = mne.create_info(ch_names=['EEG 001'], sfreq=100.0, ch_types='eeg')
    # 60 active, 40 passive
    data = np.random.randn(100, 1, 100)
    events = np.zeros((100, 3), dtype=int)
    events[:60, 2] = 1
    events[60:, 2] = 2
    events[:, 0] = np.arange(100) * 100
    
    event_id = {'active': 1, 'passive': 2}
    epochs = mne.EpochsArray(data, info, events, tmin=0.0, event_id=event_id)
    
    from preprocessing import validate_sample_size
    
    # Should fail because passive has 40 < 50
    with pytest.raises(ValueError):
        validate_sample_size(epochs, min_threshold=50, warning_threshold=100)

def test_validate_sample_size_none_epochs():
    """Test that validation raises error if epochs is None."""
    from preprocessing import validate_sample_size
    
    with pytest.raises(ValueError, match="Epochs object is None"):
        validate_sample_size(None)
