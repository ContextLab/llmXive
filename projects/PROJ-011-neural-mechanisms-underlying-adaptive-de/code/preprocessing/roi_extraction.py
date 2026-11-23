"""
ROI Extraction utilities for preprocessing.

Provides functions to load ROI mask NIfTI files and extract mean BOLD
time‑series from a 4‑D functional image for each mask.

The public API matches the expectations of the integration test
``tests/integration/test_roi_extraction.py``:
  - ``load_roi_masks(mask_paths)`` – returns a mapping of mask name to
    binary mask array.
  - ``extract_roi_timeseries(func_path, mask_paths)`` – returns a mapping
    of mask name to a 1‑D NumPy array containing the mean signal across
    all voxels in the mask for each time point.

The implementation is lightweight, uses only ``nibabel`` and ``numpy``,
and logs useful information via the project's logger.
"""

import logging
from pathlib import Path
from typing import Dict, List, Union

import nibabel as nib
import numpy as np

from utils.logger import get_logger

logger = get_logger(__name__)

def _ensure_path(p: Union[str, Path]) -> Path:
    """Coerce ``p`` to a ``Path`` and ensure it exists."""
    path = Path(p)
    if not path.is_file():
        raise FileNotFoundError(f"File not found: {path}")
    return path

def load_roi_masks(mask_paths: List[Union[str, Path]]) -> Dict[str, np.ndarray]:
    """
    Load ROI mask NIfTI files.

    Parameters
    ----------
    mask_paths : List[Union[str, Path]]
        List of file paths pointing to mask NIfTI images.

    Returns
    -------
    Dict[str, np.ndarray]
        Mapping from a human‑readable mask name (derived from the file stem)
        to a 3‑D NumPy array containing the mask data (typically binary).

    Raises
    ------
    FileNotFoundError
        If any of the supplied mask files does not exist.
    """
    masks: Dict[str, np.ndarray] = {}
    for mp in mask_paths:
        mask_path = _ensure_path(mp)
        try:
            img = nib.load(str(mask_path))
            data = img.get_fdata()
            # Ensure binary mask (0/1) – any non‑zero is treated as 1
            mask_array = (data > 0).astype(np.uint8)
            mask_name = mask_path.stem  # e.g. "dlPFC_mask"
            masks[mask_name] = mask_array
            logger.debug(f"Loaded mask '{mask_name}' with shape {mask_array.shape}")
        except Exception as e:
            logger.error(f"Failed to load mask {mask_path}: {e}")
            raise
    return masks

def extract_roi_timeseries(
    func_path: Union[str, Path],
    mask_paths: List[Union[str, Path]]
) -> Dict[str, np.ndarray]:
    """
    Extract mean BOLD time‑series for each ROI mask.

    Parameters
    ----------
    func_path : Union[str, Path]
        Path to the 4‑D functional NIfTI image (X, Y, Z, Time).
    mask_paths : List[Union[str, Path]]
        List of mask file paths. The same list accepted by
        ``load_roi_masks``; each mask is applied independently.

    Returns
    -------
    Dict[str, np.ndarray]
        Mapping from mask name to a 1‑D NumPy array of length equal to the
        number of time points in the functional image. Each entry contains
        the mean signal across all voxels belonging to that mask.

    Raises
    ------
    FileNotFoundError
        If the functional image or any mask file is missing.
    ValueError
        If a mask's spatial dimensions do not match the functional image.
    """
    func_path = _ensure_path(func_path)

    # Load functional data
    try:
        func_img = nib.load(str(func_path))
        func_data = func_img.get_fdata()
    except Exception as e:
        logger.error(f"Failed to load functional image {func_path}: {e}")
        raise

    if func_data.ndim != 4:
        raise ValueError(
            f"Functional image must be 4‑D (X,Y,Z,Time); got shape {func_data.shape}"
        )

    # Shape components
    vol_shape = func_data.shape[:3]  # (X, Y, Z)
    n_timepoints = func_data.shape[3]

    # Load masks (reuse the loader to get binary arrays)
    masks = load_roi_masks(mask_paths)

    roi_timeseries: Dict[str, np.ndarray] = {}

    for mask_name, mask_arr in masks.items():
        if mask_arr.shape != vol_shape:
            raise ValueError(
                f"Mask '{mask_name}' shape {mask_arr.shape} does not match "
                f"functional volume shape {vol_shape}"
            )
        # Apply mask: flatten spatial dimensions, keep time dimension
        # mask_arr is (X,Y,Z); func_data is (X,Y,Z,T)
        # Selecting voxels where mask == 1 gives an array (N_voxels, T)
        masked_voxels = func_data[mask_arr > 0]  # shape (N_voxels, T)
        if masked_voxels.size == 0:
            logger.warning(f"Mask '{mask_name}' contains no voxels > 0; returning zeros.")
            mean_ts = np.zeros(n_timepoints, dtype=np.float32)
        else:
            # Compute mean across voxels for each time point
            mean_ts = masked_voxels.mean(axis=0).astype(np.float32)  # shape (T,)
        roi_timeseries[mask_name] = mean_ts
        logger.debug(
            f"Extracted time‑series for mask '{mask_name}': "
            f"{mean_ts.shape[0]} time points."
        )

    return roi_timeseries

# The module's public interface
__all__ = ["load_roi_masks", "extract_roi_timeseries"]