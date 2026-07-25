import numpy as np
from typing import Union, Tuple
from src.analysis.spectral import normalize_psd_to_unit_area

def spectral_density_correlation(
    psd_model: Union[np.ndarray, list],
    psd_meg: Union[np.ndarray, list],
    normalize: bool = True
) -> float:
    """
    Calculate the Spectral Density Correlation (SDC) between two Power Spectral Densities.

    SDC is defined as the Pearson correlation coefficient between the normalized
    PSDs of the model activations and the reference MEG data. This serves as a
    secondary metric to PLV for methodological rigor regarding discrete/continuous
    time comparison.

    Args:
        psd_model: 1D array of Power Spectral Density values from model activations.
        psd_meg: 1D array of Power Spectral Density values from MEG reference.
        normalize: If True, normalize both PSDs to unit area before correlation.
                   Defaults to True as per task requirements.

    Returns:
        float: Pearson correlation coefficient between -1.0 and 1.0.

    Raises:
        ValueError: If input arrays have different lengths or are not 1D.
        TypeError: If inputs cannot be converted to numpy arrays.
    """
    psd_model = np.asarray(psd_model, dtype=float)
    psd_meg = np.asarray(psd_meg, dtype=float)

    if psd_model.ndim != 1 or psd_meg.ndim != 1:
        raise ValueError("Both PSD inputs must be 1-dimensional arrays.")
    
    if psd_model.shape[0] != psd_meg.shape[0]:
        raise ValueError(
            f"PSD arrays must have the same length. "
            f"Got model: {psd_model.shape[0]}, MEG: {psd_meg.shape[0]}"
        )

    if normalize:
        psd_model = normalize_psd_to_unit_area(psd_model)
        psd_meg = normalize_psd_to_unit_area(psd_meg)

    # Calculate Pearson correlation
    correlation_matrix = np.corrcoef(psd_model, psd_meg)
    
    # np.corrcoef returns a 2x2 matrix: [[var(x), cov(x,y)], [cov(y,x), var(y)]]
    # We want the off-diagonal element
    if np.isnan(correlation_matrix[0, 1]):
        # Handle cases where variance is zero (e.g., constant signal)
        return 0.0
    
    return float(correlation_matrix[0, 1])

def compute_sdc_batch(
    psd_models: np.ndarray,
    psd_meg_reference: np.ndarray,
    axis: int = 1
) -> np.ndarray:
    """
    Compute SDC for a batch of model PSDs against a single MEG reference.

    Args:
        psd_models: 2D array of shape (batch_size, freq_bins) containing
                    model PSDs.
        psd_meg_reference: 1D array of shape (freq_bins,) containing
                           the reference MEG PSD.
        axis: Axis along which the frequency bins are aligned. Defaults to 1.

    Returns:
        np.ndarray: 1D array of shape (batch_size,) containing SDC values.
    """
    if psd_models.ndim != 2:
        raise ValueError(f"psd_models must be 2D, got {psd_models.ndim}D")
    
    if psd_meg_reference.ndim != 1:
        raise ValueError(f"psd_meg_reference must be 1D, got {psd_meg_reference.ndim}D")

    if axis != 1:
        # Move frequency axis to the end for easier broadcasting if needed
        # But for standard (batch, freq), axis=1 is expected
        psd_models = np.moveaxis(psd_models, axis, -1)
        psd_meg_reference = np.moveaxis(psd_meg_reference, axis, -1)

    batch_size = psd_models.shape[0]
    sdc_values = np.zeros(batch_size, dtype=float)

    for i in range(batch_size):
        sdc_values[i] = spectral_density_correlation(
            psd_models[i], 
            psd_meg_reference
        )

    return sdc_values
