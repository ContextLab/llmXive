"""
Unit tests for EEG preprocessing functions.

This module contains tests for the preprocessing pipeline, specifically
focusing on ICA artifact removal functionality as per task T010.
"""

import pytest
import numpy as np
import mne
from mne.preprocessing import ICA

# Import the preprocessing module if it exists, otherwise we'll test ICA directly
# Since T013 (implementation) is not yet done, we test the ICA logic directly
# using the MNE API surface which is available via requirements.txt (T002)

def test_ica_artifact_removal():
    """
    Test that ICA initialization and fitting works correctly on dummy EEG data.
    
    This test verifies:
    1. ICA.n_components_ is greater than 0 after fitting
    2. ICA.fit() completes without error on a dummy MNE Epochs object
    
    Corresponds to task T010: Write unit test test_ica_artifact_removal
    """
    # Create dummy EEG data
    # 64 channels, 1000 time points, 10 epochs
    n_channels = 64
    n_times = 1000
    n_epochs = 10
    sfreq = 250.0  # Hz
    
    # Create random data with realistic structure
    data = np.random.randn(n_epochs, n_channels, n_times)
    
    # Create info structure
    info = mne.create_info(
        ch_names=[f'EEG {i:03d}' for i in range(n_channels)],
        sfreq=sfreq,
        ch_types='eeg'
    )
    
    # Create epochs object
    events = np.array([[i * 1000, 0, 1] for i in range(n_epochs)])
    epochs = mne.EpochsArray(
        data, 
        info, 
        events=events,
        tmin=0.0,
        event_id={'dummy': 1}
    )
    
    # Initialize ICA with reasonable parameters
    # Using FastICA for faster testing
    ica = ICA(n_components=10, method='fastica', random_state=42, max_iter=100)
    
    # Fit ICA on the dummy data - this should complete without error
    try:
        ica.fit(epochs)
    except Exception as e:
        pytest.fail(f"ICA.fit() raised an unexpected exception: {e}")
    
    # Verify that n_components_ is set and greater than 0
    assert ica.n_components_ > 0, \
        f"ICA.n_components_ should be > 0, but got {ica.n_components_}"
    
    # Additional sanity checks
    assert hasattr(ica, 'pca_components_'), "ICA should have pca_components_ attribute"
    assert hasattr(ica, 'mixing_matrix_'), "ICA should have mixing_matrix_ attribute"
    
    # Verify the number of components matches what we requested
    assert ica.n_components_ == 10, \
        f"Expected 10 components, but got {ica.n_components_}"
    
    # Test that we can apply the ICA (even if we don't actually remove artifacts yet)
    # This ensures the fitted ICA is usable
    ica.apply(epochs.copy())

if __name__ == '__main__':
    # Run the test when executed directly
    test_ica_artifact_removal()
    print("Test test_ica_artifact_removal passed successfully!")