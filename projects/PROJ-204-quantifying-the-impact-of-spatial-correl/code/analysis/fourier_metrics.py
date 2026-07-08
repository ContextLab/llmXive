import numpy as np
from numpy.fft import fft2, fftshift
from typing import Tuple, Dict, Any, Optional
import logging

__all__ = [
    "compute_fourier_transform",
    "compute_power_spectrum",
    "get_frequency_grid",
    "compute_low_frequency_spectral_power",
    "compute_spatial_frequency_metrics",
]

def compute_fourier_transform(image: np.ndarray) -> np.ndarray:
    """
    Compute the 2‑D Fourier transform of an image.

    Parameters
    ----------
    image: np.ndarray
        2‑D array representing the image.

    Returns
    -------
    np.ndarray
        Shifted Fourier transform (complex values).
    """
    logging.debug("Computing Fourier transform")
    return fftshift(fft2(image))

def compute_power_spectrum(ft: np.ndarray) -> np.ndarray:
    """
    Compute the power spectrum from a Fourier transform.

    Parameters
    ----------
    ft: np.ndarray
        Fourier transform (complex).

    Returns
    -------
    np.ndarray
        Power spectrum (real, non‑negative).
    """
    logging.debug("Computing power spectrum")
    return np.abs(ft) ** 2

def get_frequency_grid(shape: Tuple[int, int]) -> Tuple[np.ndarray, np.ndarray]:
    """
    Generate the frequency grid for a given image shape.

    Parameters
    ----------
    shape: Tuple[int, int]
        (height, width) of the image.

    Returns
    -------
    Tuple[np.ndarray, np.ndarray]
        Meshgrid arrays (fx, fy) with frequency coordinates.
    """
    h, w = shape
    fy = np.fft.fftfreq(h)
    fx = np.fft.fftfreq(w)
    return np.meshgrid(fx, fy)

def compute_low_frequency_spectral_power(
    power_spectrum: np.ndarray,
    freq_grid: Tuple[np.ndarray, np.ndarray],
    cutoff: float = 0.1,
) -> float:
    """
    Integrate spectral power over low‑frequency components.

    Parameters
    ----------
    power_spectrum: np.ndarray
        Power spectrum of the image.
    freq_grid: Tuple[np.ndarray, np.ndarray]
        Frequency meshgrid (fx, fy).
    cutoff: float, optional
        Normalised frequency cutoff (default 0.1).

    Returns
    -------
    float
        Integrated low‑frequency power.
    """
    fx, fy = freq_grid
    radius = np.sqrt(fx ** 2 + fy ** 2)
    mask = radius <= cutoff
    low_freq_power = power_spectrum[mask].sum()
    total_power = power_spectrum.sum()
    logging.debug(
        "Low‑frequency power: %f, total power: %f", low_freq_power, total_power
    )
    return low_freq_power / total_power if total_power != 0 else 0.0

def compute_spatial_frequency_metrics(image: np.ndarray, cutoff: float = 0.1) -> Dict[str, Any]:
    """
    Compute a dictionary of spatial frequency metrics for an image.

    The metrics include the full power spectrum, low‑frequency power
    fraction, and the raw Fourier transform.

    Parameters
    ----------
    image: np.ndarray
        Input 2‑D image.
    cutoff: float, optional
        Frequency cutoff for low‑frequency integration.

    Returns
    -------
    Dict[str, Any]
        Dictionary with keys ``'ft'``, ``'power_spectrum'``,
        ``'low_freq_fraction'``.
    """
    ft = compute_fourier_transform(image)
    power = compute_power_spectrum(ft)
    freq_grid = get_frequency_grid(image.shape)
    low_frac = compute_low_frequency_spectral_power(power, freq_grid, cutoff)
    return {
        "ft": ft,
        "power_spectrum": power,
        "low_freq_fraction": low_frac,
    }
