import pytest
import numpy as np
import mne
from code.preprocessing import apply_average_rereference, apply_bandpass_filter, run_ica_artifact_removal

@pytest.fixture
def sample_eeg_raw():
    """Create a sample MNE Raw object for testing."""
    # Create sample EEG data
    n_channels = 32
    n_times = 1000
    sfreq = 250.0
    
    # Generate random EEG-like data
    data = np.random.randn(n_channels, n_times)
    
    # Create channel names and types
    ch_names = [f'EEG {i:03d}' for i in range(1, n_channels + 1)]
    ch_types = ['eeg'] * n_channels
    
    # Create info structure
    info = mne.create_info(ch_names, sfreq, ch_types)
    
    # Create Raw object
    raw = mne.io.RawArray(data, info)
    return raw

def test_apply_average_rereference(sample_eeg_raw):
    """Test that average rereference is applied correctly."""
    # Apply average rereference
    rereferenced = apply_average_rereference(sample_eeg_raw)
    
    # Check that the object is still a Raw instance
    assert isinstance(rereferenced, mne.io.Raw)
    
    # Check that the data shape is preserved
    assert rereferenced.get_data().shape == sample_eeg_raw.get_data().shape
    
    # Check that the reference is set to average
    # In MNE, after set_eeg_reference('average'), the reference channel should be 'average'
    # This is a basic check - more thorough validation would involve checking the actual data
    assert rereferenced.info['custom_ref_applied'] == True

def test_apply_bandpass_filter(sample_eeg_raw):
    """Test that bandpass filter is applied correctly."""
    # Apply bandpass filter
    filtered = apply_bandpass_filter(sample_eeg_raw, low_freq=1.0, high_freq=40.0)
    
    # Check that the object is still a Raw instance
    assert isinstance(filtered, mne.io.Raw)
    
    # Check that the data shape is preserved
    assert filtered.get_data().shape == sample_eeg_raw.get_data().shape

def test_run_ica_artifact_removal(sample_eeg_raw):
    """Test that ICA artifact removal works correctly."""
    # Run ICA artifact removal
    cleaned = run_ica_artifact_removal(sample_eeg_raw, method='adjust')
    
    # Check that the object is still a Raw instance
    assert isinstance(cleaned, mne.io.Raw)
    
    # Check that the data shape is preserved
    assert cleaned.get_data().shape == sample_eeg_raw.get_data().shape

def test_apply_average_rereference_invalid_input():
    """Test that invalid input raises appropriate error."""
    with pytest.raises(TypeError):
        apply_average_rereference("not a Raw object")