"""
Spatial metrics analysis module for computing autocorrelation and fitting decay models.
"""
import numpy as np
from scipy import ndimage
from scipy.optimize import curve_fit
from scipy.stats import pearsonr
import logging
from typing import Tuple, Dict, Any, Optional, Union

logger = logging.getLogger(__name__)

def gaussian_decay(x: np.ndarray, amplitude: float, sigma: float, offset: float) -> np.ndarray:
    """
    Gaussian decay model: A * exp(-x^2 / (2 * sigma^2)) + offset
    
    Args:
        x: Distance array
        amplitude: Initial amplitude
        sigma: Decay width (correlation length)
        offset: Asymptotic offset
        
    Returns:
        Predicted values
    """
    return amplitude * np.exp(-(x**2) / (2 * sigma**2)) + offset

def exponential_decay(x: np.ndarray, amplitude: float, tau: float, offset: float) -> np.ndarray:
    """
    Exponential decay model: A * exp(-x / tau) + offset
    
    Args:
        x: Distance array
        amplitude: Initial amplitude
        tau: Decay constant (correlation length)
        offset: Asymptotic offset
        
    Returns:
        Predicted values
    """
    return amplitude * np.exp(-x / tau) + offset

def compute_autocorrelation(data: np.ndarray) -> np.ndarray:
    """
    Compute the 2D autocorrelation of the input data.
    
    Args:
        data: 2D numpy array representing a spatial map
        
    Returns:
        2D autocorrelation array
    """
    if data.ndim != 2:
        raise ValueError("Input data must be a 2D array")
    
    # Normalize data
    data_normalized = data - np.mean(data)
    
    # Compute autocorrelation using FFT
    fft_shape = (2 * data.shape[0] - 1, 2 * data.shape[1] - 1)
    autocorr = np.fft.irfft2(np.fft.rfft2(data_normalized) * np.conj(np.fft.rfft2(data_normalized)), s=fft_shape)
    
    # Shift zero-frequency component to center
    autocorr = np.fft.fftshift(autocorr)
    
    # Normalize by the number of elements
    autocorr = autocorr / (data.shape[0] * data.shape[1])
    
    # Extract the central region to match original size
    center_y, center_x = autocorr.shape[0] // 2, autocorr.shape[1] // 2
    y_start = center_y - data.shape[0] // 2
    y_end = y_start + data.shape[0]
    x_start = center_x - data.shape[1] // 2
    x_end = x_start + data.shape[1]
    
    return autocorr[y_start:y_end, x_start:x_end]

def fit_decay_model(
    distances: np.ndarray, 
    autocorr_values: np.ndarray, 
    model_type: str = 'gaussian'
) -> Dict[str, float]:
    """
    Fit a decay model to the autocorrelation values.
    
    Args:
        distances: Array of distances from the center
        autocorr_values: Autocorrelation values at those distances
        model_type: Type of decay model ('gaussian' or 'exponential')
        
    Returns:
        Dictionary containing fitted parameters, including 'sigma' or 'tau'
    """
    # Filter out non-positive distances or invalid values
    valid_mask = (distances >= 0) & np.isfinite(autocorr_values)
    if not np.any(valid_mask):
        raise ValueError("No valid data points for fitting")
        
    x_data = distances[valid_mask]
    y_data = autocorr_values[valid_mask]
    
    # Ensure y_data is normalized to 1 at x=0 if possible
    if len(x_data) > 0 and x_data[0] == 0:
        y_data = y_data / y_data[0]
    
    # Define model function
    if model_type == 'gaussian':
        model_func = gaussian_decay
        # Initial guesses: amplitude=1, sigma=10, offset=0
        p0 = [1.0, 10.0, 0.0]
        # Bounds: amplitude > 0, sigma > 0, offset can be negative
        bounds = ([0, 0, -1], [2, 100, 1])
    elif model_type == 'exponential':
        model_func = exponential_decay
        p0 = [1.0, 10.0, 0.0]
        bounds = ([0, 0, -1], [2, 100, 1])
    else:
        raise ValueError(f"Unknown model_type: {model_type}")
    
    try:
        # Perform curve fitting
        popt, _ = curve_fit(model_func, x_data, y_data, p0=p0, bounds=bounds, maxfev=5000)
        
        if model_type == 'gaussian':
            return {
                'amplitude': popt[0],
                'sigma': popt[1],
                'offset': popt[2],
                'model_type': 'gaussian'
            }
        else:
            return {
                'amplitude': popt[0],
                'tau': popt[1],
                'offset': popt[2],
                'model_type': 'exponential'
            }
            
    except RuntimeError as e:
        logger.warning(f"Curve fitting failed: {e}. Attempting with different initial guesses.")
        # Try with different initial guesses
        p0_alt = [1.0, 5.0, 0.0]
        try:
            popt, _ = curve_fit(model_func, x_data, y_data, p0=p0_alt, bounds=bounds, maxfev=5000)
            if model_type == 'gaussian':
                return {'amplitude': popt[0], 'sigma': popt[1], 'offset': popt[2], 'model_type': 'gaussian'}
            else:
                return {'amplitude': popt[0], 'tau': popt[1], 'offset': popt[2], 'model_type': 'exponential'}
        except RuntimeError as e2:
            raise RuntimeError(f"Curve fitting failed even with alternative guesses: {e2}")