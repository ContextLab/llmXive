"""
Unit tests for the ICA detection and removal functionality added in T004.
"""
import pytest
import mne
import numpy as np
from pathlib import Path
import sys

# Ensure the code directory is on the import path
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'code'))

from preprocess import detect_ica_components, remove_ica_components

@pytest.fixture
def synthetic_raw():
    """
    Create a synthetic Raw object that contains a clear blink‑like component
    on the frontal channels (Fz, FCz). This allows us to test that the
    detection logic correctly identifies and removes the component.
    """
    sfreq = 250
    n_times = sfreq * 10  # 10 s of data
    ch_names = ['Fz', 'FCz', 'Cz', 'Pz']
    info = mne.create_info(ch_names=ch_names, sfreq=sfreq, ch_types='eeg')
    # Random EEG background
    data = np.random.randn(len(ch_names), n_times) * 1e-6

    # Simulate a blink artifact: a large positive deflection on frontal channels
    blink = np.zeros(n_times)
    blink[2000:2100] = 5e-5  # 100 ms blink around 8 s
    data[0, :] += blink  # Fz
    data[1, :] += blink  # FCz

    raw = mne.io.RawArray(data, info)
    return raw

def test_detect_ica_components_identifies_blink(synthetic_raw):
    """
    The synthetic data contains a strong frontal deflection; the ICA
    detection should return at least one component index.
    """
    components = detect_ica_components(synthetic_raw, threshold=0.5)
    assert isinstance(components, list), "Returned value should be a list"
    assert len(components) > 0, "Should detect at least one component for the simulated blink"

def test_remove_ica_components_cleans_raw(synthetic_raw):
    """
    After removal, the variance of the frontal channels should be reduced.
    """
    # Detect components first
    components = detect_ica_components(synthetic_raw, threshold=0.5)
    raw_clean = remove_ica_components(synthetic_raw.copy(), components)

    # Compute variance before and after on frontal channels
    pre_var = synthetic_raw.get_data(picks=['Fz', 'FCz']).var()
    post_var = raw_clean.get_data(picks=['Fz', 'FCz']).var()
    # Expect variance reduction
    assert np.all(post_var < pre_var), "Variance should decrease after ICA removal"
    
    # Ensure that the cleaned raw still contains the same channel set
    assert raw_clean.ch_names == synthetic_raw.ch_names

if __name__ == "__main__":
    pytest.main([__file__, "-v"])