"""
EEG preprocessing helper functions.

Provides utilities for:
- Band-pass filtering
- Notch filtering
- Channel variance rejection
- ICA cleaning
"""
import numpy as np
import mne
from typing import List, Tuple, Optional, Dict

def bandpass_filter(
    raw: mne.io.Raw,
    l_freq: float,
    h_freq: float,
    fir_design: str = "firwin",
    verbose: bool = False,
) -> mne.io.Raw:
    """
    Apply band-pass filter to EEG data.

    Args:
        raw: Raw EEG data
        l_freq: Low frequency cutoff (Hz)
        h_freq: High frequency cutoff (Hz)
        fir_design: FIR filter design method
        verbose: Whether to print verbose output

    Returns:
        Filtered raw data
    """
    raw_filtered = raw.copy()
    raw_filtered.filter(
        l_freq=l_freq,
        h_freq=h_freq,
        fir_design=fir_design,
        verbose="WARNING" if not verbose else None,
    )
    return raw_filtered

def notch_filter(
    raw: mne.io.Raw,
    freqs: List[float],
    verbose: bool = False,
) -> mne.io.Raw:
    """
    Apply notch filter to remove line noise.

    Args:
        raw: Raw EEG data
        freqs: List of frequencies to notch (e.g., [50.0] or [60.0])
        verbose: Whether to print verbose output

    Returns:
        Notch-filtered raw data
    """
    raw_notched = raw.copy()
    raw_notched.notch_filter(
        freqs=freqs,
        verbose="WARNING" if not verbose else None,
    )
    return raw_notched

def reject_channels_by_variance(
    raw: mne.io.Raw,
    threshold: float = 3.0,
    verbose: bool = False,
) -> Tuple[List[str], mne.io.Raw]:
    """
    Reject channels with variance > threshold * SD.

    Args:
        raw: Raw EEG data
        threshold: Number of standard deviations for rejection
        verbose: Whether to print verbose output

    Returns:
        Tuple of (list of rejected channel names, cleaned raw data)
    """
    # Get data matrix (channels x time)
    data = raw.get_data()
    # Calculate variance per channel
    variances = np.var(data, axis=1)
    mean_var = np.mean(variances)
    std_var = np.std(variances)

    if std_var == 0:
        return [], raw

    # Find channels with variance > threshold * SD
    rejected_indices = np.where(variances > mean_var + threshold * std_var)[0]
    rejected_channels = [raw.ch_names[i] for i in rejected_indices]

    if rejected_channels and verbose:
        print(f"Rejecting {len(rejected_channels)} channels due to high variance:")
        print(f"  {rejected_channels}")

    if rejected_channels:
        raw_cleaned = raw.copy().drop_channels(rejected_channels)
    else:
        raw_cleaned = raw

    return rejected_channels, raw_cleaned

def apply_ica(
    raw: mne.io.Raw,
    n_components: float = 0.95,
    random_state: int = 42,
    max_iter: int = 800,
    verbose: bool = False,
) -> Tuple[mne.io.Raw, int]:
    """
    Apply ICA to remove ocular and muscle artifacts.

    Args:
        raw: Raw EEG data (after filtering and channel rejection)
        n_components: Number of components to keep (or fraction of variance)
        random_state: Random seed for reproducibility
        max_iter: Maximum iterations for ICA
        verbose: Whether to print verbose output

    Returns:
        Tuple of (cleaned raw data, number of components removed)
    """
    # Create ICA object
    ica = mne.preprocessing.ICA(
        n_components=n_components,
        random_state=random_state,
        max_iter=max_iter,
        method="fastica",
    )

    # Fit ICA
    ica.fit(raw)

    # Find components to exclude (EOG, ECG artifacts)
    # Use automated detection
    eog_indices, eog_scores = ica.find_bads_eog(raw)
    ecg_indices, ecg_scores = ica.find_bads_ecg(raw)

    # Combine indices
    exclude_indices = list(set(eog_indices + ecg_indices))

    if verbose:
        print(f"ICA found {len(ica)} components")
        print(f"EOG components: {eog_indices} (scores: {eog_scores})")
        print(f"ECG components: {ecg_indices} (scores: {ecg_scores})")
        print(f"Excluding {len(exclude_indices)} components: {exclude_indices}")

    # Apply ICA to remove artifacts
    ica.apply(raw, exclude=exclude_indices)

    return raw, len(exclude_indices)
