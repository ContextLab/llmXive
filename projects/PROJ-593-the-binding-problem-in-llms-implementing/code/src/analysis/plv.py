"""
Phase Locking Value (PLV) calculation module.

PLV is the primary metric for measuring phase synchrony between two signals,
as mandated by FR-003. It is calculated as the magnitude of the mean of the
phase differences across time points.

This module provides functions to calculate PLV between two signals,
between pairs of signals in a batch, and a wrapper for the main calculation
logic.
"""
import numpy as np
from typing import Union, Tuple, Optional
from scipy.signal import hilbert

def _get_instantaneous_phases(signal: np.ndarray, fs: Optional[float] = None) -> np.ndarray:
    """
    Extract instantaneous phase from a signal using the Hilbert transform.

    Args:
        signal: 1D or 2D (channels x time) array.
        fs: Sampling frequency (unused for normalized phase, but kept for interface consistency).

    Returns:
        Instantaneous phase array of same shape as input.
    """
    if signal.ndim == 1:
        analytic_signal = hilbert(signal)
    elif signal.ndim == 2:
        # Apply hilbert transform along the last axis (time)
        analytic_signal = hilbert(signal, axis=-1)
    else:
        raise ValueError("Input signal must be 1D or 2D.")

    phases = np.angle(analytic_signal)
    return phases

def compute_plv(
    signal1: np.ndarray,
    signal2: np.ndarray,
    fs: Optional[float] = None
) -> float:
    """
    Calculate the Phase Locking Value (PLV) between two signals.

    PLV = |mean(exp(1j * (phase1 - phase2)))|

    Args:
        signal1: First signal (1D array of shape [time]).
        signal2: Second signal (1D array of shape [time]).
        fs: Sampling frequency (optional, for interface consistency).

    Returns:
        PLV value between 0 and 1.
    """
    if signal1.shape != signal2.shape:
        raise ValueError(f"Signal shapes must match: {signal1.shape} vs {signal2.shape}")
    
    if signal1.ndim != 1:
        raise ValueError("compute_plv expects 1D signals. Use compute_plv_batch for 2D.")

    phase1 = _get_instantaneous_phases(signal1, fs)
    phase2 = _get_instantaneous_phases(signal2, fs)

    phase_diff = phase1 - phase2
    plv = np.abs(np.mean(np.exp(1j * phase_diff)))

    return float(plv)

def compute_plv_batch(
    signals1: np.ndarray,
    signals2: np.ndarray,
    fs: Optional[float] = None
) -> np.ndarray:
    """
    Calculate PLV for multiple pairs of signals (batched).

    Args:
        signals1: 2D array of shape [n_signals, time].
        signals2: 2D array of shape [n_signals, time].
        fs: Sampling frequency (optional).

    Returns:
        1D array of PLV values of shape [n_signals].
    """
    if signals1.shape != signals2.shape:
        raise ValueError(f"Signal batch shapes must match: {signals1.shape} vs {signals2.shape}")
    
    if signals1.ndim != 2:
        raise ValueError("compute_plv_batch expects 2D signals [n, time].")

    n_signals = signals1.shape[0]
    plv_values = np.zeros(n_signals)

    phase1 = _get_instantaneous_phases(signals1, fs)
    phase2 = _get_instantaneous_phases(signals2, fs)

    phase_diff = phase1 - phase2
    mean_complex = np.mean(np.exp(1j * phase_diff), axis=-1)
    plv_values = np.abs(mean_complex)

    return plv_values

def plv_calc(
    signal1: np.ndarray,
    signal2: np.ndarray,
    fs: Optional[float] = None
) -> float:
    """
    Wrapper function for PLV calculation, providing a clear API entry point.
    This is the primary function to be used by external modules (e.g., main.py, US2).

    Args:
        signal1: First signal (1D array).
        signal2: Second signal (1D array).
        fs: Sampling frequency (optional).

    Returns:
        PLV value (float).
    """
    return compute_plv(signal1, signal2, fs)
