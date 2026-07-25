"""
Spectral analysis functions for the Binding Problem project.

Provides FFT, Welch PSD, and SNR calculation utilities.
"""
import numpy as np
from scipy.signal import welch, windows
from typing import Tuple, Union, Optional


def compute_fft(signal: np.ndarray, fs: float = 1.0) -> Tuple[np.ndarray, np.ndarray]:
    """
    Compute the Fast Fourier Transform of a signal.
    
    Args:
        signal: 1D numpy array of time-series data.
        fs: Sampling frequency (in arbitrary units, typically "samples per sequence").
    
    Returns:
        Tuple of (frequencies, magnitudes).
        frequencies: Array of frequency bins.
        magnitudes: Absolute value of the FFT coefficients.
    """
    n = len(signal)
    # Apply Hanning window to reduce spectral leakage
    window = windows.hann(n)
    windowed_signal = signal * window
    
    # Compute FFT
    fft_result = np.fft.rfft(windowed_signal)
    frequencies = np.fft.rfftfreq(n, d=1.0/fs)
    magnitudes = np.abs(fft_result)
    
    return frequencies, magnitudes


def compute_welch_psd(
    signal: np.ndarray,
    fs: float = 1.0,
    nperseg: Optional[int] = None,
    noverlap: Optional[int] = None,
    nfft: Optional[int] = None
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Compute the Power Spectral Density using Welch's method.
    
    Args:
        signal: 1D numpy array of time-series data.
        fs: Sampling frequency.
        nperseg: Length of each segment. If None, defaults to min(256, len(signal)).
        noverlap: Number of points to overlap between segments. Defaults to 50% of nperseg.
        nfft: Length of the FFT. If None, defaults to nperseg (or zero-padded to 512 if seq_len < 512 per spec).
    
    Returns:
        Tuple of (frequencies, psd).
        frequencies: Array of frequency bins.
        psd: Power Spectral Density values.
    """
    seq_len = len(signal)
    
    # Determine segment length
    if nperseg is None:
        nperseg = min(256, seq_len)
        
    # Determine overlap
    if noverlap is None:
        noverlap = nperseg // 2
        
    # Determine FFT length
    if nfft is None:
        # Per spec T047: zero-pad to 512 if seq_len < 512
        if seq_len < 512:
            nfft = 512
        else:
            nfft = nperseg
    
    f, pxx = welch(
        signal,
        fs=fs,
        window='hann',
        nperseg=nperseg,
        noverlap=noverlap,
        nfft=nfft,
        scaling='density'
    )
    
    return f, pxx


def normalize_psd_to_unit_area(psd: np.ndarray, freqs: np.ndarray) -> np.ndarray:
    """
    Normalize a PSD array to have unit area (integral = 1).
    
    This is used for comparing spectral shapes independent of total power.
    
    Args:
        psd: Power Spectral Density values.
        freqs: Corresponding frequency bins.
    
    Returns:
        Normalized PSD array.
    """
    # Compute the integral using trapezoidal rule
    total_area = np.trapz(psd, freqs)
    
    if total_area <= 0:
        # Avoid division by zero or negative area
        return psd
        
    return psd / total_area


def calculate_snr(
    psd: np.ndarray,
    freqs: np.ndarray,
    target_band: Tuple[float, float],
    noise_band: Tuple[float, float]
) -> float:
    """
    Calculate Signal-to-Noise Ratio (SNR) in decibels (dB).
    
    The SNR is computed as the ratio of the average power in the target band
    to the average power in the noise band.
    
    Args:
        psd: Power Spectral Density values.
        freqs: Corresponding frequency bins.
        target_band: Tuple (f_low, f_high) defining the signal band.
        noise_band: Tuple (f_low, f_high) defining the noise band.
    
    Returns:
        SNR in dB.
    """
    # Mask for target band
    target_mask = (freqs >= target_band[0]) & (freqs <= target_band[1])
    target_power = np.mean(psd[target_mask]) if np.any(target_mask) else 0.0
    
    # Mask for noise band
    noise_mask = (freqs >= noise_band[0]) & (freqs <= noise_band[1])
    noise_power = np.mean(psd[noise_mask]) if np.any(noise_mask) else 0.0
    
    if noise_power <= 0:
        # Avoid log of zero or negative
        return float('inf') if target_power > 0 else 0.0
    
    snr_db = 10 * np.log10(target_power / noise_power)
    return snr_db
