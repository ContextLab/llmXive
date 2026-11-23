import mne
import numpy as np

def bandpass_filter(raw, l_freq, h_freq):
    """
    Apply a bandpass filter to the raw data.
    """
    # Use MNE's built-in filter
    # Note: MNE filters are applied in-place on the copy
    raw_filtered = raw.copy()
    raw_filtered.filter(l_freq=l_freq, h_freq=h_freq, method='fir', fir_design='firwin')
    return raw_filtered

def notch_filter(raw, freq):
    """
    Apply a notch filter to remove line noise.
    """
    raw_filtered = raw.copy()
    raw_filtered.notch_filter(freqs=freq, method='fir', fir_design='firwin')
    return raw_filtered

def reject_high_variance_channels(raw, threshold_sd=3.0):
    """
    Reject channels with variance > threshold_sd * std of channel variances.
    Returns a list of rejected channel names.
    """
    raw.load_data()
    data = raw.get_data()
    channel_names = raw.ch_names

    channel_variances = np.var(data, axis=1)
    mean_var = np.mean(channel_variances)
    std_var = np.std(channel_variances)

    rejected_mask = channel_variances > (mean_var + threshold_sd * std_var)
    rejected_channels = [ch for ch, rej in zip(channel_names, rejected_mask) if rej]

    return rejected_channels

def reject_channels_by_variance(raw, threshold_sd=3.0):
    """
    Reject channels whose variance exceeds ``threshold_sd`` standard deviations
    above the mean variance across channels.

    Returns
    -------
    rejected_channels : list[str]
        Names of channels that are marked as bad.
    rejection_ratio : float
        Fraction of total channels that were rejected (0‑1).
    """
    raw.load_data()
    data = raw.get_data()
    channel_names = raw.ch_names

    channel_variances = np.var(data, axis=1)
    mean_var = np.mean(channel_variances)
    std_var = np.std(channel_variances)

    rejected_mask = channel_variances > (mean_var + threshold_sd * std_var)
    rejected_channels = [ch for ch, rej in zip(channel_names, rejected_mask) if rej]
    rejection_ratio = len(rejected_channels) / len(channel_names) if channel_names else 0.0

    return rejected_channels, rejection_ratio

def apply_ica(raw, n_components=None):
    """
    Perform ICA cleaning on the raw EEG data.

    Parameters
    ----------
    raw : mne.io.Raw
        The raw EEG object to be cleaned.
    n_components : int | None
        Number of ICA components to compute. If ``None`` MNE will choose a
        suitable number based on the data dimensionality.

    Returns
    -------
    cleaned_raw : mne.io.Raw
        The ICA‑cleaned raw data.
    info : dict
        Dictionary with metadata about the ICA step (currently only
        ``n_components`` is stored).
    """
    # Work on a copy to avoid mutating the original object outside this function
    cleaned_raw = raw.copy()

    # Initialise ICA
    ica = mne.preprocessing.ICA(
        n_components=n_components,
        random_state=42,
        max_iter='auto',
        method='fastica'
    )
    # Fit ICA on the copy
    ica.fit(cleaned_raw)

    # Apply the ICA solution (removes the identified artifact components)
    ica.apply(cleaned_raw)

    info = {
        'n_components': n_components if n_components is not None else ica.n_components_
    }
    return cleaned_raw, info