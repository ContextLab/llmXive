"""
Fourier-based spatial metrics for perovskite solar cell analysis.
Computes 2D FFTs, power spectra, and low-frequency spectral power integration.
"""
import numpy as np
from numpy.fft import fft2, fftshift
from typing import Tuple, Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

def compute_fourier_transform(image: np.ndarray) -> np.ndarray:
    """
    Compute the 2D Fourier Transform of an image and shift zero-frequency to center.
    
    Args:
        image: 2D numpy array representing the spatial map.
        
    Returns:
        Shifted 2D Fourier transform coefficients.
    """
    if image.ndim != 2:
        raise ValueError(f"Input image must be 2D, got shape {image.shape}")
    
    # Compute 2D FFT and shift zero frequency to center
    fft_result = fft2(image)
    shifted_fft = fftshift(fft_result)
    return shifted_fft

def compute_power_spectrum(fft_result: np.ndarray) -> np.ndarray:
    """
    Compute the power spectrum (magnitude squared) from FFT result.
    
    Args:
        fft_result: Shifted 2D Fourier transform coefficients.
        
    Returns:
        Power spectrum array (real, non-negative).
    """
    if fft_result.ndim != 2:
        raise ValueError(f"FFT result must be 2D, got shape {fft_result.shape}")
    
    power_spectrum = np.abs(fft_result) ** 2
    return power_spectrum

def get_frequency_grid(shape: Tuple[int, int]) -> Tuple[np.ndarray, np.ndarray]:
    """
    Generate 2D frequency grid coordinates corresponding to the FFT output.
    
    Args:
        shape: Tuple (Ny, Nx) representing image dimensions.
        
    Returns:
        Tuple of (fx, fy) frequency grids in cycles/pixel.
    """
    Ny, Nx = shape
    
    # Frequency bins in cycles per pixel
    # For even N, frequencies are [-N/2, ..., N/2-1] / N
    # For odd N, frequencies are [-(N-1)/2, ..., (N-1)/2] / N
    fy = np.fft.fftfreq(Ny)
    fx = np.fft.fftfreq(Nx)
    
    # Shift to match fftshift output
    fy = np.fft.fftshift(fy)
    fx = np.fft.fftshift(fx)
    
    # Create meshgrid
    FY, FX = np.meshgrid(fy, fx, indexing='ij')
    
    return FX, FY

def compute_low_frequency_spectral_power(
    power_spectrum: np.ndarray,
    fx: np.ndarray,
    fy: np.ndarray,
    cutoff_freq: float = 0.1
) -> float:
    """
    Integrate spectral power in the low-frequency region (|f| < cutoff_freq).
    
    Args:
        power_spectrum: 2D power spectrum array.
        fx: X-frequency grid (cycles/pixel).
        fy: Y-frequency grid (cycles/pixel).
        cutoff_freq: Frequency cutoff in cycles/pixel (default 0.1).
        
    Returns:
        Total integrated power in the low-frequency band.
    """
    if power_spectrum.shape != fx.shape or power_spectrum.shape != fy.shape:
        raise ValueError("Shape mismatch between power_spectrum and frequency grids")
    
    # Compute radial frequency
    freq_radial = np.sqrt(fx**2 + fy**2)
    
    # Mask for low frequencies (excluding DC component at (0,0) for robustness,
    # though the task implies including it if it's low freq. We'll include DC.)
    low_freq_mask = freq_radial <= cutoff_freq
    
    # Integrate power in the low-frequency region
    low_freq_power = np.sum(power_spectrum[low_freq_mask])
    
    logger.debug(
        f"Low-frequency integration: cutoff={cutoff_freq}, "
        f"pixels_in_band={np.sum(low_freq_mask)}, total_power={low_freq_power}"
    )
    
    return float(low_freq_power)

def compute_spatial_frequency_metrics(
    image: np.ndarray,
    cutoff_freq: float = 0.1
) -> Dict[str, Any]:
    """
    Compute a suite of spatial frequency metrics for an image.
    
    Args:
        image: 2D spatial map.
        cutoff_freq: Frequency cutoff for low-frequency power integration.
        
    Returns:
        Dictionary containing:
            - total_power: Sum of entire power spectrum
            - low_freq_power: Integrated power below cutoff_freq
            - low_freq_ratio: Ratio of low_freq_power to total_power
            - peak_frequency: Frequency of maximum power (excluding DC)
    """
    # Compute FFT and Power Spectrum
    fft_result = compute_fourier_transform(image)
    power_spectrum = compute_power_spectrum(fft_result)
    fx, fy = get_frequency_grid(image.shape)
    
    # Total power
    total_power = np.sum(power_spectrum)
    
    # Low frequency power
    low_freq_power = compute_low_frequency_spectral_power(
        power_spectrum, fx, fy, cutoff_freq
    )
    
    # Ratio
    low_freq_ratio = low_freq_power / total_power if total_power > 0 else 0.0
    
    # Peak frequency (excluding DC at center)
    freq_radial = np.sqrt(fx**2 + fy**2)
    # Create mask to exclude DC (center pixel)
    center_y, center_x = image.shape[0] // 2, image.shape[1] // 2
    peak_mask = np.ones_like(power_spectrum, dtype=bool)
    peak_mask[center_y, center_x] = False
    
    peak_idx = np.unravel_index(
        np.argmax(power_spectrum[peak_mask]), power_spectrum.shape
    )
    peak_freq = np.sqrt(fx[peak_idx]**2 + fy[peak_idx]**2)
    
    return {
        "total_power": float(total_power),
        "low_freq_power": low_freq_power,
        "low_freq_ratio": float(low_freq_ratio),
        "peak_frequency": float(peak_freq)
    }
