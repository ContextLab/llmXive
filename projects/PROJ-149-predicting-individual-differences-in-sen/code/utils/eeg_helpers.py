"""
EEG Helper Utilities for Preprocessing Pipeline.

This module provides core signal processing functions for EEG data:
- Band-pass filtering (Butterworth)
- Notch filtering (for line noise)
- Channel rejection based on variance thresholds
- ICA-based artifact removal
"""
import numpy as np
import mne
from typing import List, Tuple, Optional, Dict

def bandpass_filter(
    raw: mne.io.Raw,
    l_freq: float,
    h_freq: float,
    filter_length: str = 'auto',
    l_trans_bandwidth: float = 'auto',
    h_trans_bandwidth: float = 'auto',
    n_jobs: int = 1,
    copy: bool = True
) -> mne.io.Raw:
    """
    Apply a band-pass filter to the raw EEG data.

    Parameters
    ----------
    raw : mne.io.Raw
        The raw EEG data object.
    l_freq : float
        The lower cutoff frequency in Hz.
    h_freq : float
        The upper cutoff frequency in Hz.
    filter_length : str, optional
        The length of the filter kernel. Default is 'auto'.
    l_trans_bandwidth : float or str, optional
        The transition bandwidth for the low cutoff. Default is 'auto'.
    h_trans_bandwidth : float or str, optional
        The transition bandwidth for the high cutoff. Default is 'auto'.
    n_jobs : int, optional
        Number of jobs to run in parallel. Default is 1.
    copy : bool, optional
        If True, return a copy of the data. Default is True.

    Returns
    -------
    mne.io.Raw
        The filtered raw EEG data object.
    """
    if copy:
        raw = raw.copy()

    raw.filter(
        l_freq=l_freq,
        h_freq=h_freq,
        filter_length=filter_length,
        l_trans_bandwidth=l_trans_bandwidth,
        h_trans_bandwidth=h_trans_bandwidth,
        n_jobs=n_jobs,
        method='fft',  # Using FFT method for efficiency on continuous data
        verbose=False
    )
    return raw


def notch_filter(
    raw: mne.io.Raw,
    freqs: List[float],
    q: float = 30.0,
    method: str = 'savgol',
    copy: bool = True
) -> mne.io.Raw:
    """
    Apply a notch filter to remove line noise.

    Parameters
    ----------
    raw : mne.io.Raw
        The raw EEG data object.
    freqs : list of float
        The frequencies to notch out (e.g., [50, 100] or [60, 120]).
    q : float, optional
        Quality factor for the notch filter. Default is 30.0.
    method : str, optional
        The method to use for filtering. Options are 'savgol' or 'iir'. Default is 'savgol'.
    copy : bool, optional
        If True, return a copy of the data. Default is True.

    Returns
    -------
    mne.io.Raw
        The notched raw EEG data object.
    """
    if copy:
        raw = raw.copy()

    raw.notch_filter(
        freqs=freqs,
        q=q,
        method=method,
        verbose=False
    )
    return raw


def reject_channels_by_variance(
    raw: mne.io.Raw,
    threshold: float = 3.0,
    channel_names: Optional[List[str]] = None
) -> Tuple[mne.io.Raw, List[str], Dict[str, float]]:
    """
    Reject channels that have variance exceeding a threshold (in standard deviations).

    Parameters
    ----------
    raw : mne.io.Raw
        The raw EEG data object.
    threshold : float, optional
        The number of standard deviations above the mean variance to reject. Default is 3.0.
    channel_names : list of str, optional
        Specific channel names to evaluate. If None, all EEG channels are evaluated.

    Returns
    -------
    tuple
        A tuple containing:
        - mne.io.Raw: The raw data with rejected channels dropped.
        - list of str: The names of the rejected channels.
        - dict: A mapping of channel names to their calculated variance (for logging).
    """
    # Ensure we are working with a copy to avoid modifying the original if not intended
    # Note: This function drops channels, so it returns a new object
    data = raw.get_data()
    sfreq = raw.info['sfreq']
    ch_names = raw.ch_names

    if channel_names is None:
        # Filter for EEG channels only if mixed montage exists
        eeg_indices = mne.pick_types(raw.info, eeg=True)
        channel_names_to_check = [ch_names[i] for i in eeg_indices]
        data_subset = data[eeg_indices, :]
    else:
        channel_names_to_check = channel_names
        # Pick indices corresponding to provided names
        indices = [ch_names.index(name) for name in channel_names_to_check]
        data_subset = data[indices, :]

    # Calculate variance for each channel
    variances = np.var(data_subset, axis=1)
    mean_var = np.mean(variances)
    std_var = np.std(variances)

    if std_var == 0:
        # If no variance in variance (unlikely), reject none
        rejected = []
    else:
        # Identify channels exceeding threshold
        # We use the global mean and std of the variances
        z_scores = (variances - mean_var) / std_var
        bad_indices = np.where(z_scores > threshold)[0]
        rejected = [channel_names_to_check[i] for i in bad_indices]

    # Drop the bad channels
    if rejected:
        raw_dropped = raw.copy().drop_channels(rejected)
    else:
        raw_dropped = raw.copy()

    # Create a dict of variances for logging purposes (only for checked channels)
    var_log = {
        name: float(variances[i])
        for i, name in enumerate(channel_names_to_check)
    }

    return raw_dropped, rejected, var_log


def apply_ica(
    raw: mne.io.Raw,
    method: str = 'fastica',
    n_components: Optional[float] = None,
    max_iter: int = 200,
    random_state: int = 42,
    ecg_epochs: Optional[mne.Epochs] = None,
    eog_epochs: Optional[mne.Epochs] = None
) -> Tuple[mne.preprocessing.ICA, List[int]]:
    """
    Apply Independent Component Analysis (ICA) to identify and remove artifacts.

    This function fits ICA to the data and returns the ICA object and a list
    of component indices to exclude (typically identified via EOG/ECG correlation).
    Note: This function does NOT automatically exclude components; it prepares
    the ICA object and returns the indices of components that correlate with
    EOG/ECG if epochs are provided.

    Parameters
    ----------
    raw : mne.io.Raw
        The raw EEG data object (should be filtered and cleaned before ICA).
    method : str, optional
        The ICA algorithm to use. Options: 'fastica', 'infomax'. Default is 'fastica'.
    n_components : float or int, optional
        Number of components to keep. If float, it's a fraction of channels. Default is None (all).
    max_iter : int, optional
        Maximum number of iterations for ICA. Default is 200.
    random_state : int, optional
        Random seed for reproducibility. Default is 42.
    ecg_epochs : mne.Epochs, optional
        ECG epochs for identifying cardiac artifacts.
    eog_epochs : mne.Epochs, optional
        EOG epochs for identifying ocular artifacts.

    Returns
    -------
    tuple
        A tuple containing:
        - mne.preprocessing.ICA: The fitted ICA object.
        - list of int: Indices of components identified as artifacts (if EOG/ECG epochs provided).
    """
    ica = mne.preprocessing.ICA(
        method=method,
        n_components=n_components,
        max_iter=max_iter,
        random_state=random_state,
        verbose=False
    )

    # Fit ICA on the raw data
    ica.fit(raw)

    excluded_components = []

    if eog_epochs is not None:
        # Find EOG-related components
        eog_indices, eog_scores = ica.find_bads_eog(eog_epochs)
        excluded_components.extend(eog_indices)

    if ecg_epochs is not None:
        # Find ECG-related components
        ecg_indices, ecg_scores = ica.find_bads_ecg(ecg_epochs)
        excluded_components.extend(ecg_indices)

    # Remove duplicates and sort
    excluded_components = sorted(list(set(excluded_components)))

    return ica, excluded_components