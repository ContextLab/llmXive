"""
Spectral Density Correlation (SDC) calculation.

SDC measures the Pearson correlation between normalized Power Spectral Densities (PSDs).
It serves as a complementary/secondary metric to Phase Locking Value (PLV) for
methodological rigor in comparing discrete model activations with continuous MEG signals.
"""

import numpy as np
from typing import Union, Tuple

from src.analysis.spectral import normalize_psd_to_unit_area


def spectral_density_correlation(
    psd_model: Union[np.ndarray, list],
    psd_meg: Union[np.ndarray, list]
) -> float:
    """
    Calculate the Spectral Density Correlation (SDC) between two PSDs.

    This function computes the Pearson correlation coefficient between the
    normalized power spectral densities of a model activation and a reference
    MEG signal.

    Args:
        psd_model: 1D array or list of power spectral density values from the model.
        psd_meg: 1D array or list of power spectral density values from MEG data.

    Returns:
        float: The Pearson correlation coefficient (SDC) between -1.0 and 1.0.

    Raises:
        ValueError: If input arrays have different lengths or are empty.
        TypeError: If inputs cannot be converted to numpy arrays.
    """
    # Convert inputs to numpy arrays
    try:
        psd_model_arr = np.asarray(psd_model, dtype=np.float64)
        psd_meg_arr = np.asarray(psd_meg, dtype=np.float64)
    except (ValueError, TypeError) as e:
        raise TypeError(f"Inputs must be convertible to numpy arrays: {e}")

    # Validate dimensions
    if psd_model_arr.ndim != 1:
        raise ValueError(f"psd_model must be 1D, got {psd_model_arr.ndim}D")
    if psd_meg_arr.ndim != 1:
        raise ValueError(f"psd_meg must be 1D, got {psd_meg_arr.ndim}D")

    if len(psd_model_arr) != len(psd_meg_arr):
        raise ValueError(
            f"Input lengths must match: model={len(psd_model_arr)}, meg={len(psd_meg_arr)}"
        )

    if len(psd_model_arr) == 0:
        raise ValueError("Input arrays cannot be empty")

    # Normalize both PSDs to unit area (L1 normalization)
    # This ensures the correlation is based on spectral shape, not magnitude
    psd_model_norm = normalize_psd_to_unit_area(psd_model_arr)
    psd_meg_norm = normalize_psd_to_unit_area(psd_meg_arr)

    # Calculate Pearson correlation coefficient
    # np.corrcoef returns a 2x2 matrix; we want the off-diagonal element
    correlation_matrix = np.corrcoef(psd_model_norm, psd_meg_norm)
    sdc_value = correlation_matrix[0, 1]

    # Handle potential NaN (e.g., if one signal is constant after normalization)
    if np.isnan(sdc_value):
        # If both signals are identical constants after normalization, correlation is undefined
        # In this edge case, we return 1.0 if they are perfectly aligned (both constant)
        # or 0.0 if they differ. However, normalization to unit area on constant signals
        # results in uniform distributions, so correlation should be 1.0 if identical.
        # To be safe, we check if the arrays are identical.
        if np.array_equal(psd_model_norm, psd_meg_norm):
            return 1.0
        return 0.0

    return float(sdc_value)


def compute_sdc_batch(
    psd_model_batch: np.ndarray,
    psd_meg_batch: np.ndarray
) -> np.ndarray:
    """
    Compute SDC for a batch of PSD pairs.

    Args:
        psd_model_batch: 2D array of shape (n_samples, n_freq_bins) for model PSDs.
        psd_meg_batch: 2D array of shape (n_samples, n_freq_bins) for MEG PSDs.

    Returns:
        1D array of shape (n_samples,) containing SDC values for each pair.

    Raises:
        ValueError: If batch dimensions do not match or are invalid.
    """
    if psd_model_batch.ndim != 2 or psd_meg_batch.ndim != 2:
        raise ValueError("Batch inputs must be 2D arrays")

    if psd_model_batch.shape[0] != psd_meg_batch.shape[0]:
        raise ValueError(
            f"Batch size mismatch: model={psd_model_batch.shape[0]}, meg={psd_meg_batch.shape[0]}"
        )

    if psd_model_batch.shape[1] != psd_meg_batch.shape[1]:
        raise ValueError(
            f"Frequency bin mismatch: model={psd_model_batch.shape[1]}, meg={psd_meg_batch.shape[1]}"
        )

    n_samples = psd_model_batch.shape[0]
    sdc_values = np.empty(n_samples, dtype=np.float64)

    for i in range(n_samples):
        sdc_values[i] = spectral_density_correlation(
            psd_model_batch[i],
            psd_meg_batch[i]
        )

    return sdc_values