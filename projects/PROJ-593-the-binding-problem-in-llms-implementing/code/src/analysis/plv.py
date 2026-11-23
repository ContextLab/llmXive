"""
Phase Locking Value (PLV) calculation module.

This module implements the PLV metric as mandated by FR-003.
PLV measures the consistency of phase differences between two signals across
trials or time windows, serving as the primary metric for neural alignment.

Note: Frequency in this context is defined as "cycles per sequence length",
not physical Hz, as per project constraints.
"""
import numpy as np
from typing import Union, Tuple, Optional, List
from scipy.signal import hilbert

def compute_plv(signal1: np.ndarray, signal2: np.ndarray) -> float:
    """
    Compute the Phase Locking Value between two 1D signals.
    
    The PLV is defined as the magnitude of the mean of the phase differences
    between two signals across time points.
    
    PLV = | (1/N) * sum(exp(i * (phase1[t] - phase2[t]))) |
    
    Parameters
    ----------
    signal1 : np.ndarray
        First 1D signal (shape: (N,))
    signal2 : np.ndarray
        Second 1D signal (shape: (N,))
        
    Returns
    -------
    float
        PLV value in range [0, 1], where 1 indicates perfect phase locking.
        
    Raises
    ------
    ValueError
        If input arrays are not 1D or have different lengths.
    """
    signal1 = np.asarray(signal1)
    signal2 = np.asarray(signal2)
    
    if signal1.ndim != 1 or signal2.ndim != 1:
        raise ValueError("Both inputs must be 1D arrays")
    if len(signal1) != len(signal2):
        raise ValueError(f"Input signals must have the same length. Got {len(signal1)} and {len(signal2)}")
    
    # Compute analytic signals using Hilbert transform to get instantaneous phase
    analytic1 = hilbert(signal1)
    analytic2 = hilbert(signal2)
    
    # Extract instantaneous phases
    phase1 = np.angle(analytic1)
    phase2 = np.angle(analytic2)
    
    # Compute phase difference
    phase_diff = phase1 - phase2
    
    # Compute PLV: magnitude of the mean of complex exponentials of phase differences
    plv = np.abs(np.mean(np.exp(1j * phase_diff)))
    
    return float(plv)

def compute_plv_batch(
    signals1: np.ndarray,
    signals2: np.ndarray,
    axis: int = -1
) -> np.ndarray:
    """
    Compute PLV for batches of signals.
    
    Parameters
    ----------
    signals1 : np.ndarray
        Batch of first signals. Shape: (batch_size, ..., signal_length)
    signals2 : np.ndarray
        Batch of second signals. Shape: (batch_size, ..., signal_length)
    axis : int
        Axis along which the signal dimension lies. Default is -1 (last axis).
        
    Returns
    -------
    np.ndarray
        Array of PLV values with shape matching the broadcasted batch dimensions.
        
    Raises
    ------
    ValueError
        If input arrays have incompatible shapes or if axis is out of bounds.
    """
    signals1 = np.asarray(signals1)
    signals2 = np.asarray(signals2)
    
    if signals1.shape != signals2.shape:
        raise ValueError(f"Input batches must have the same shape. Got {signals1.shape} and {signals2.shape}")
    
    # Normalize axis
    if axis < 0:
        axis = signals1.ndim + axis
    if axis < 0 or axis >= signals1.ndim:
        raise ValueError(f"Axis {axis} is out of bounds for arrays with {signals1.ndim} dimensions")
    
    # Compute analytic signals along the specified axis
    # hilbert operates on the last axis by default, so we need to transpose if necessary
    if axis != -1:
        # Move the signal axis to the end
        perm = list(range(signals1.ndim))
        perm.remove(axis)
        perm.append(axis)
        signals1 = np.transpose(signals1, perm)
        signals2 = np.transpose(signals2, perm)
    
    # Compute analytic signals
    analytic1 = hilbert(signals1, axis=-1)
    analytic2 = hilbert(signals2, axis=-1)
    
    # Extract phases
    phase1 = np.angle(analytic1)
    phase2 = np.angle(analytic2)
    
    # Compute phase difference
    phase_diff = phase1 - phase2
    
    # Compute PLV: magnitude of the mean along the signal axis
    plv = np.abs(np.mean(np.exp(1j * phase_diff), axis=-1))
    
    # If we transposed, the result has the signal axis at the end. 
    # We need to move it back to the original position (but it's removed now).
    # Actually, the result shape is (batch_size, ...), so no need to transpose back
    # unless we want to match input shape exactly (which would have a singleton dimension).
    # We return the result as is, with the signal dimension reduced.
    
    return plv

def plv_calc(
    activation1: np.ndarray,
    activation2: np.ndarray,
    normalize: bool = True
) -> float:
    """
    Calculate PLV between two activation time series, with optional normalization.
    
    This is the primary entry point for PLV calculation in the analysis pipeline.
    It wraps compute_plv with additional preprocessing options.
    
    Parameters
    ----------
    activation1 : np.ndarray
        First activation time series (1D array).
    activation2 : np.ndarray
        Second activation time series (1D array).
    normalize : bool, optional
        If True, normalize each signal to zero mean and unit variance before
        computing PLV. Default is True.
        
    Returns
    -------
    float
        Phase Locking Value between the two activation series.
        
    Notes
    -----
    - This function is the primary metric per the project specification.
    - SDC (Spectral Density Correlation) is a complementary/secondary metric.
    - Frequency is defined as "cycles per sequence length", not physical Hz.
    """
    activation1 = np.asarray(activation1, dtype=np.float64)
    activation2 = np.asarray(activation2, dtype=np.float64)
    
    if activation1.ndim != 1 or activation2.ndim != 1:
        raise ValueError("Both activations must be 1D arrays")
    
    if normalize:
        # Normalize to zero mean and unit variance
        activation1 = (activation1 - np.mean(activation1)) / (np.std(activation1) + 1e-10)
        activation2 = (activation2 - np.mean(activation2)) / (np.std(activation2) + 1e-10)
    
    return compute_plv(activation1, activation2)
