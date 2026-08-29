"""
code/utils/eeg_helpers.py
EEG preprocessing utilities for T005 and T010.
"""
import numpy as np
import mne

def apply_bandpass(raw: mne.io.Raw, l_freq: float, h_freq: float) -> mne.io.Raw:
    """
    Apply band-pass filter to raw data.
    """
    # Use mne.filter.filter_data or raw.filter
    # mne.raw.filter is preferred for in-place or copy
    return raw.filter(l_freq=l_freq, h_freq=h_freq, method='iir', phase='forward')

def apply_notch(raw: mne.io.Raw, freqs: list) -> mne.io.Raw:
    """
    Apply notch filter to raw data.
    """
    # mne.preprocessing.notch_filter is robust
    # Or raw.notch_filter
    return raw.notch_filter(freqs=freqs, method='iir')

def reject_channels_by_variance(raw: mne.io.Raw, threshold_std: float = 3.0) -> tuple:
    """
    Reject channels with variance > threshold_std * session_mean_variance.
    Returns (list of rejected channel names, ratio of rejected channels).
    """
    # Get data matrix: channels x time
    data = raw.get_data()
    
    # Calculate variance per channel
    variances = np.var(data, axis=1)
    
    # Calculate mean variance across channels
    mean_var = np.mean(variances)
    std_var = np.std(variances)
    
    # Threshold: mean + threshold_std * std
    # Note: The task says "variance > 3 SD from the session mean".
    # Interpretation: |variance - mean_variance| > 3 * std_dev_of_variances
    # Or simply variance > mean + 3*std (one-sided). Usually outliers are high variance.
    threshold = mean_var + (threshold_std * std_var)
    
    rejected = []
    for i, ch_name in enumerate(raw.ch_names):
        if variances[i] > threshold:
            rejected.append(ch_name)
    
    raw.drop_channels(rejected)
    return rejected, len(rejected) / len(raw.ch_names) if raw.ch_names else 0.0
