import numpy as np
from scipy.signal import welch, windows
from typing import Tuple, Union, Optional

def compute_fft(signal: np.ndarray, fs: float = 1.0) -> Tuple[np.ndarray, np.ndarray]:
    """
    Compute the Fast Fourier Transform (FFT) of a 1D signal.

    Parameters
    ----------
    signal : np.ndarray
        1D array of signal values.
    fs : float, optional
        Sampling frequency (in arbitrary units, typically 'cycles per sequence' in this project).

    Returns
    -------
    freqs : np.ndarray
        Array of frequencies corresponding to the FFT bins.
    fft_vals : np.ndarray
        Complex FFT values.
    """
    n = len(signal)
    # Use rfft for real signals to get positive frequencies only
    fft_vals = np.fft.rfft(signal)
    freqs = np.fft.rfftfreq(n, d=1.0/fs)
    return freqs, fft_vals

def compute_welch_psd(
    signal: np.ndarray,
    fs: float = 1.0,
    nperseg: Optional[int] = None,
    noverlap: Optional[int] = None,
    window: str = 'hann',
    nfft: Optional[int] = None
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Compute the Power Spectral Density (PSD) using Welch's method.

    Parameters
    ----------
    signal : np.ndarray
        1D array of signal values.
    fs : float, optional
        Sampling frequency.
    nperseg : int, optional
        Length of each segment. If None, defaults to min(256, len(signal)).
    noverlap : int, optional
        Number of points of overlap between segments. Defaults to nperseg // 2.
    window : str, optional
        Window function to use (e.g., 'hann', 'hamming').
    nfft : int, optional
        Number of FFT points. If None, defaults to nperseg. If signal is short,
        this task implies zero-padding to 512 if seq_len < 512 as per T047 context.

    Returns
    -------
    freqs : np.ndarray
        Array of frequencies.
    psd : np.ndarray
        Power Spectral Density values.
    """
    seq_len = len(signal)
    
    # Default segment length
    if nperseg is None:
        nperseg = min(256, seq_len)
    
    # Zero-padding logic: if sequence is shorter than 512, pad to 512 for FFT resolution
    # This aligns with T047 requirement: "zero-pad to 512 if seq_len < 512"
    effective_nfft = nfft
    if effective_nfft is None:
        effective_nfft = nperseg
    
    if seq_len < 512 and effective_nfft < 512:
        effective_nfft = 512

    # If nperseg is larger than signal, welch will fail or behave unexpectedly.
    # Ensure nperseg <= seq_len. If seq_len is very small, use seq_len.
    if nperseg > seq_len:
        nperseg = seq_len
    
    # Handle overlap
    if noverlap is None:
        noverlap = nperseg // 2

    # Compute Welch PSD
    freqs, psd = welch(
        signal,
        fs=fs,
        window=window,
        nperseg=nperseg,
        noverlap=noverlap,
        nfft=effective_nfft,
        scaling='density'
    )
    
    return freqs, psd

def normalize_psd_to_unit_area(psd: np.ndarray, freqs: np.ndarray) -> np.ndarray:
    """
    Normalize the PSD so that the sum of (PSD * freq_bin_width) equals 1.0.
    This effectively makes it a probability density function over frequency.

    Parameters
    ----------
    psd : np.ndarray
        Power Spectral Density values.
    freqs : np.ndarray
        Corresponding frequency values.

    Returns
    -------
    normalized_psd : np.ndarray
        Normalized PSD values.
    """
    if len(freqs) < 2:
        return psd / np.sum(psd) if np.sum(psd) > 0 else psd

    # Calculate frequency bin width (assuming uniform spacing)
    df = freqs[1] - freqs[0]
    
    # Calculate total power (area under the curve)
    total_power = np.sum(psd) * df
    
    if total_power <= 0:
        # Avoid division by zero
        return psd
    
    return psd / total_power

def calculate_snr(
    psd: np.ndarray,
    freqs: np.ndarray,
    target_band: Tuple[float, float],
    noise_band: Tuple[float, float]
) -> float:
    """
    Calculate the Signal-to-Noise Ratio (SNR) in decibels (dB).
    
    The signal power is the mean power in the target band.
    The noise power is the mean power in the noise (adjacent) band.
    
    SNR (dB) = 10 * log10(P_signal / P_noise)

    Parameters
    ----------
    psd : np.ndarray
        Power Spectral Density values (preferably normalized or raw, consistent).
    freqs : np.ndarray
        Corresponding frequency values.
    target_band : tuple (f_min, f_max)
        Frequency range defining the signal of interest (e.g., (38, 42) for 40Hz).
    noise_band : tuple (f_min, f_max)
        Frequency range defining the background noise.

    Returns
    -------
    snr_db : float
        SNR in decibels. Returns -inf if noise power is 0 or negative.
    """
    # Identify indices for target band
    target_mask = (freqs >= target_band[0]) & (freqs <= target_band[1])
    if not np.any(target_mask):
        raise ValueError(f"No frequencies found in target band {target_band}")
    
    target_psd = psd[target_mask]
    signal_power = np.mean(target_psd)

    # Identify indices for noise band
    noise_mask = (freqs >= noise_band[0]) & (freqs <= noise_band[1])
    if not np.any(noise_mask):
        raise ValueError(f"No frequencies found in noise band {noise_band}")
    
    noise_psd = psd[noise_mask]
    noise_power = np.mean(noise_psd)

    if noise_power <= 0:
        return float('inf') if signal_power > 0 else float('-inf')

    snr_db = 10 * np.log10(signal_power / noise_power)
    return snr_db
