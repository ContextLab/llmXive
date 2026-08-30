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
