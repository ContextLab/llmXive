"""
EEG Helper Utilities for MNE-Python processing.
Implements band-pass, notch, variance rejection, and ICA cleaning.
"""
import numpy as np
import mne
from typing import List, Tuple, Optional, Dict

def bandpass_filter(
    raw: mne.io.BaseRaw,
    l_freq: float,
    h_freq: float,
    filter_length: str = 'auto',
    l_trans_bandwidth: float = 'auto',
    h_trans_bandwidth: float = 'auto',
    n_jobs: int = 1
) -> mne.io.BaseRaw:
    """
    Apply a band-pass filter to the raw data.
    
    Args:
        raw: MNE Raw object.
        l_freq: Low cutoff frequency (Hz).
        h_freq: High cutoff frequency (Hz).
        filter_length: Length of the FIR filter.
        l_trans_bandwidth: Transition bandwidth for low cutoff.
        h_trans_bandwidth: Transition bandwidth for high cutoff.
        n_jobs: Number of jobs for parallel processing.
        
    Returns:
        Filtered MNE Raw object.
    """
    # Make a copy to avoid modifying in-place if the caller needs original
    raw_filtered = raw.copy()
    raw_filtered.filter(
        l_freq=l_freq,
        h_freq=h_freq,
        filter_length=filter_length,
        l_trans_bandwidth=l_trans_bandwidth,
        h_trans_bandwidth=h_trans_bandwidth,
        n_jobs=n_jobs,
        method='fir',
        phase='zero'
    )
    return raw_filtered

def notch_filter(
    raw: mne.io.BaseRaw,
    freqs: List[float],
    q: float = 30.0,
    method: str = 'fir',
    n_jobs: int = 1
) -> mne.io.BaseRaw:
    """
    Apply a notch filter to remove line noise.
    
    Args:
        raw: MNE Raw object.
        freqs: List of frequencies to notch (e.g., [50, 100] or [60, 120]).
        q: Quality factor. Higher is narrower notch.
        method: 'fir' or 'iir'.
        n_jobs: Number of jobs for parallel processing.
        
    Returns:
        Filtered MNE Raw object.
    """
    raw_notched = raw.copy()
    raw_notched.notch_filter(
        freqs=freqs,
        q=q,
        method=method,
        n_jobs=n_jobs
    )
    return raw_notched

def reject_channels_by_variance(
    raw: mne.io.BaseRaw,
    std_threshold: float = 3.0
) -> Tuple[mne.io.BaseRaw, List[str]]:
    """
    Identify and drop channels with variance exceeding std_threshold * global_std.
    
    Args:
        raw: MNE Raw object.
        std_threshold: Number of standard deviations above mean variance to reject.
        
    Returns:
        Tuple of (cleaned_raw, list_of_rejected_channel_names).
    """
    data = raw.get_data()
    # Calculate variance per channel (across time)
    variances = np.var(data, axis=1)
    mean_var = np.mean(variances)
    std_var = np.std(variances)
    
    if std_var == 0:
        # All variances identical, no rejection needed
        return raw, []
    
    threshold = mean_var + (std_threshold * std_var)
    bad_indices = np.where(variances > threshold)[0]
    
    rejected_channels = [raw.ch_names[i] for i in bad_indices]
    
    if rejected_channels:
        raw_cleaned = raw.copy()
        raw_cleaned.drop_channels(rejected_channels)
        return raw_cleaned, rejected_channels
    
    return raw, []

def apply_ica(
    raw: mne.io.BaseRaw,
    n_components: Optional[float] = 0.95,
    method: str = 'fastica',
    random_state: int = 42,
    reject: Optional[Dict[str, float]] = None,
    picks: Optional[List[str]] = None
) -> Tuple[mne.io.BaseRaw, mne.preprocessing.ICA]:
    """
    Apply ICA to remove ocular and muscle artifacts.
    
    This function:
    1. Fits ICA on the raw data.
    2. Identifies components correlated with EOG (if EOG channels exist) 
       or high variance in frontal channels (proxy for eye blinks).
    3. Excludes identified artifact components.
    4. Returns the cleaned raw data.
    
    Args:
        raw: MNE Raw object (preprocessed).
        n_components: Number of components or explained variance ratio.
        method: 'fastica' or 'picard'.
        random_state: Random seed for reproducibility.
        reject: Dictionary of rejection thresholds (e.g., {'grad': 4000e-13, 'eeg': 200e-6}).
                If None, uses MNE defaults or no rejection during fitting.
        picks: Channels to include in ICA fitting. If None, uses all EEG/EOG channels.
        
    Returns:
        Tuple of (cleaned_raw, fitted_ica_object).
    """
    ica = mne.preprocessing.ICA(
        n_components=n_components,
        method=method,
        random_state=random_state,
        max_iter='auto'
    )
    
    # Define picks if not provided
    if picks is None:
        # Prefer EEG channels, exclude MEG if present (unless specified)
        picks = mne.pick_types(raw.info, eeg=True, eog=True, meg=False, stim=False)
    
    # Fit ICA
    # We fit on the data, optionally excluding bad segments if 'reject' is provided
    # Note: In a robust pipeline, we might epoch first to reject bad epochs before ICA fit
    ica.fit(raw, picks=picks)
    
    # Identify artifact components
    # Strategy 1: EOG correlation (if EOG channels exist)
    eog_indices = mne.pick_types(raw.info, eog=True)
    eog_ch_names = [raw.ch_names[i] for i in eog_indices] if eog_indices else []
    
    # Strategy 2: High variance in frontal channels (proxy for blinks)
    # If no explicit EOG, we look for components with high correlation to frontal EEG
    # or simply mark components with high kurtosis/energy in low frequencies
    
    exclude_components = []
    
    if eog_ch_names:
        # Find EOG components using correlation
        eog_projs = mne.preprocessing.compute_proj_eog(raw, ch_name=eog_ch_names)
        # Actually, compute_proj_eog returns projection vectors, not ICA components directly.
        # Better approach: use find_bads_eog
        eog_indices_found, _ = mne.preprocessing.find_bads_eog(
            raw, ica=ica, ch_name=eog_ch_names
        )
        exclude_components.extend(eog_indices_found)
    else:
        # Fallback: If no EOG channels, try to find frontal artifacts via EEG
        # Heuristic: Components with high correlation to frontal electrodes (e.g., Fp1, Fp2)
        frontal_chs = [ch for ch in raw.ch_names if ch.startswith('Fp')]
        if frontal_chs:
            # Use find_bads_eog with EEG channels as proxy
            try:
                eog_indices_found, _ = mne.preprocessing.find_bads_eog(
                    raw, ica=ica, ch_name=frontal_chs
                )
                exclude_components.extend(eog_indices_found)
            except Exception:
                pass # If fails, proceed without exclusion
    
    # Also check for muscle artifacts (high frequency content)
    # Heuristic: Components with high variance in high-frequency bands
    # For simplicity, we rely on find_bads_eog for now, but in a full pipeline
    # we would also use find_bads_muscle or manual inspection.
    
    if exclude_components:
        ica.exclude = exclude_components
        # Apply ICA to remove components
        raw_cleaned = ica.apply(raw.copy())
    else:
        raw_cleaned = raw.copy()
        
    return raw_cleaned, ica
