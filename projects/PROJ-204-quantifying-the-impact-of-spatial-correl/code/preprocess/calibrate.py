"""
code/preprocess/calibrate.py
----------------------------
Handles the calibration and masking of elemental EDS maps.
Identifies defective pixels (zeros or NaNs) and computes the mask percentage.
"""
import numpy as np
from llmxive_toolkit import get_logger

log = get_logger(__name__)

def calibrate_and_log(image: np.ndarray):
    """
    Identify defective pixels in an EDS map and mask them.
    
    Parameters
    ----------
    image : np.ndarray
        The 2-D elemental map array.
        
    Returns
    -------
    Tuple[np.ndarray, Dict[str, float]]
        The masked image (defects replaced by NaN) and a dictionary containing
        the 'total_mask_fraction'.
    """
    # Defective pixels are those that are non-positive or NaN
    # In EDS, concentrations should be strictly positive.
    mask = (image <= 0) | np.isnan(image)
    
    # Create a masked version of the image
    masked_image = np.copy(image).astype(float)
    masked_image[mask] = np.nan
    
    # Calculate the fraction of pixels masked
    mask_fraction = np.mean(mask)
    
    stats = {
        "total_mask_fraction": float(mask_fraction)
    }
    
    log.debug(f"Masking complete. Fraction masked: {mask_fraction:.4f}")
    
    return masked_image, stats

def apply_mask_to_dataset(df, map_columns):
    """
    Helper to apply masking to a whole dataset if needed.
    (Not used directly by the ingestion pipeline but provided for completeness).
    """
    # This would be used in a separate preprocessing step.
    pass
