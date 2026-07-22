"""
EEG-specific helper functions for filtering, channel rejection, and ICA.
"""
import numpy as np
import mne
from typing import List, Tuple, Optional, Dict

def bandpass_filter(raw: mne.io.BaseRaw, l_freq: float = 1.0, h_freq: float = 40.0) -> mne.io.BaseRaw:
    """
    Apply band-pass filter to EEG data.
    
    Args:
        raw: Raw EEG data object
        l_freq: Low cutoff frequency (Hz)
        h_freq: High cutoff frequency (Hz)
        
    Returns:
        Filtered raw object (copy)
    """
    raw_filtered = raw.copy()
    raw_filtered.filter(l_freq=l_freq, h_freq=h_freq, method='fir', 
                       fir_design='firwin', verbose=False)
    return raw_filtered

def notch_filter(raw: mne.io.BaseRaw, freqs: List[float] = [50, 60]) -> mne.io.BaseRaw:
    """
    Apply notch filter to remove line noise.
    
    Args:
        raw: Raw EEG data object
        freqs: List of frequencies to notch (Hz)
        
    Returns:
        Notched raw object (copy)
    """
    raw_notched = raw.copy()
    for freq in freqs:
        raw_notched.notch_filter(freqs=[freq], verbose=False)
    return raw_notched

def reject_channels_by_variance(raw: mne.io.BaseRaw, threshold_sd: float = 3.0) -> Tuple[List[str], List[str]]:
    """
    Reject channels with variance exceeding threshold standard deviations.
    
    Args:
        raw: Raw EEG data object
        threshold_sd: Number of standard deviations above mean to reject
        
    Returns:
        Tuple of (rejected_channels, kept_channels)
    """
    data = raw.get_data()
    variances = np.var(data, axis=1)
    mean_var = np.mean(variances)
    std_var = np.std(variances)
    
    if std_var == 0:
        return [], raw.ch_names
    
    threshold = mean_var + threshold_sd * std_var
    rejected = []
    kept = []
    
    for i, ch_name in enumerate(raw.ch_names):
        if variances[i] > threshold:
            rejected.append(ch_name)
        else:
            kept.append(ch_name)
    
    if rejected:
        raw.info['bads'] = rejected
    
    return rejected, kept

def apply_ica(raw: mne.io.BaseRaw, rejected_channels: List[str] = None) -> Tuple[mne.io.BaseRaw, int]:
    """
    Apply ICA to remove ocular and muscle artifacts.
    
    Args:
        raw: Preprocessed raw EEG data object
        rejected_channels: List of channels already marked as bad
        
    Returns:
        Tuple of (raw_with_ica_applied, n_components_removed)
    """
    # Create copy to avoid modifying original
    raw_ica = raw.copy()
    
    # Exclude bad channels
    if rejected_channels:
        raw_ica.info['bads'] = list(set(raw_ica.info['bads'] + rejected_channels))
    
    # Fit ICA
    n_components = min(0.99, len(raw_ica.ch_names) - len(raw_ica.info['bads']))
    ica = mne.preprocessing.ICA(n_components=n_components, random_state=42, verbose=False)
    ica.fit(raw_ica)
    
    # Find EOG/ECG components
    eog_indices, eog_scores = ica.find_bads_eog(raw_ica)
    ecg_indices, ecg_scores = ica.find_bads_ecg(raw_ica)
    
    # Combine components to exclude
    components_to_exclude = list(set(eog_indices + ecg_indices))
    n_removed = len(components_to_exclude)
    
    if components_to_exclude:
        ica.exclude = components_to_exclude
        ica.apply(raw_ica)
    
    return raw_ica, n_removed
