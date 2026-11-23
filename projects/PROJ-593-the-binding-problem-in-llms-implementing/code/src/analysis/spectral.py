import numpy as np
from scipy.signal import welch, windows
from typing import Tuple, Union, Optional

def compute_fft(signal: np.ndarray, sample_rate: float = 1.0) -> Tuple[np.ndarray, np.ndarray]:
    """
    Compute the Fast Fourier Transform (FFT) of a 1D signal.
    
    Args:
        signal: 1D numpy array of time-series data.
        sample_rate: Sampling rate (in arbitrary units, e.g., tokens per sequence or Hz).
        
    Returns:
        Tuple of (frequencies, magnitudes) where frequencies are in cycles per unit time
        and magnitudes are the absolute values of the FFT.
    """
    if signal.ndim != 1:
        raise ValueError("Signal must be a 1D array.")
    
    n = len(signal)
    fft_result = np.fft.fft(signal)
    frequencies = np.fft.fftfreq(n, d=1.0/sample_rate)
    
    # Only return positive frequencies
    positive_mask = frequencies >= 0
    return frequencies[positive_mask], np.abs(fft_result[positive_mask])

def compute_welch_psd(signal: np.ndarray, 
                      fs: float = 1.0, 
                      nperseg: int = 256, 
                      noverlap: Optional[int] = None,
                      window: str = 'hann',
                      seq_len: Optional[int] = None) -> Tuple[np.ndarray, np.ndarray]:
    """
    Compute the Power Spectral Density (PSD) using Welch's method.
    
    Args:
        signal: 1D numpy array of time-series data.
        fs: Sampling frequency.
        nperseg: Length of each segment.
        noverlap: Number of points to overlap between segments. Defaults to nperseg // 2.
        window: Window function name or array (passed to scipy.signal.welch).
        seq_len: Optional total sequence length for zero-padding logic.
                If provided and len(signal) < seq_len, the signal is zero-padded to seq_len.
                
    Returns:
        Tuple of (frequencies, psd) where frequencies are in cycles per unit time.
    """
    if signal.ndim != 1:
        raise ValueError("Signal must be a 1D array.")
    
    current_signal = signal
    if seq_len is not None and len(signal) < seq_len:
        current_signal = np.zeros(seq_len)
        current_signal[:len(signal)] = signal
    
    if noverlap is None:
        noverlap = nperseg // 2
        
    frequencies, psd = welch(
        current_signal, 
        fs=fs, 
        window=window, 
        nperseg=nperseg, 
        noverlap=noverlap,
        scaling='density'
    )
    
    return frequencies, psd

def normalize_psd_to_unit_area(psd: np.ndarray, freqs: np.ndarray) -> np.ndarray:
    """
    Normalize a PSD array so that the area under the curve (integral) equals 1.
    This allows for comparison of spectral shapes independent of total power.
    
    Args:
        psd: 1D numpy array of power spectral density values.
        freqs: 1D numpy array of corresponding frequencies.
                
    Returns:
        Normalized PSD array.
    """
    if psd.ndim != 1 or freqs.ndim != 1:
        raise ValueError("PSD and frequencies must be 1D arrays.")
    if len(psd) != len(freqs):
        raise ValueError("PSD and frequencies must have the same length.")
        
    # Calculate the integral using the trapezoidal rule
    total_area = np.trapz(psd, freqs)
    
    if total_area == 0:
        # Avoid division by zero; return zeros if the signal has no power
        return np.zeros_like(psd)
        
    return psd / total_area

def calculate_snr(psd: np.ndarray, 
                  freqs: np.ndarray, 
                  target_band: Tuple[float, float], 
                  adjacent_band_width: float = 5.0) -> float:
    """
    Calculate the Signal-to-Noise Ratio (SNR) in decibels (dB) for a specific frequency band.
    The 'signal' is the average power in the target band. The 'noise' is the average power
    in the adjacent bands immediately flanking the target band.
    
    Args:
        psd: 1D numpy array of power spectral density values.
        freqs: 1D numpy array of corresponding frequencies.
        target_band: Tuple (f_low, f_high) defining the target frequency range.
        adjacent_band_width: Width of the adjacent bands on each side of the target band.
                
    Returns:
        SNR in dB. Returns -np.inf if noise power is zero or negative.
    """
    if psd.ndim != 1 or freqs.ndim != 1:
        raise ValueError("PSD and frequencies must be 1D arrays.")
    if len(psd) != len(freqs):
        raise ValueError("PSD and frequencies must have the same length.")
        
    f_low, f_high = target_band
    f_noise_low = f_low - adjacent_band_width
    f_noise_high = f_high + adjacent_band_width
    
    # Identify indices for the bands
    target_mask = (freqs >= f_low) & (freqs <= f_high)
    noise_mask = ((freqs >= f_noise_low) & (freqs < f_low)) | \
                 ((freqs > f_high) & (freqs <= f_noise_high))
    
    if not np.any(target_mask):
        raise ValueError(f"No frequencies found in target band {target_band}")
    if not np.any(noise_mask):
        raise ValueError(f"No frequencies found in adjacent noise bands [{f_noise_low}, {f_noise_high}]")
    
    signal_power = np.mean(psd[target_mask])
    noise_power = np.mean(psd[noise_mask])
    
    if noise_power <= 0:
        return np.inf
        
    snr_db = 10 * np.log10(signal_power / noise_power)
    return snr_db
