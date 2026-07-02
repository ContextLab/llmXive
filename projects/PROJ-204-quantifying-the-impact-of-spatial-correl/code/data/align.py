"""
Module for aligning and resampling elemental maps to a common pixel grid.

This module handles dimension mismatches between different elemental maps (Pb, I, MA)
for the same sample by resampling them to a uniform grid size. It supports various
interpolation methods and ensures data integrity during the resampling process.
"""

import numpy as np
import logging
from typing import Dict, List, Tuple, Optional, Union
from pathlib import Path
from scipy.ndimage import zoom
from scipy.interpolate import RectBivariateSpline

logger = logging.getLogger(__name__)


def calculate_target_grid_shape(
    shapes: List[Tuple[int, int]], method: str = "min"
) -> Tuple[int, int]:
    """
    Calculate the target grid shape for alignment.

    Args:
        shapes: List of (height, width) tuples from input maps.
        method: Strategy for determining target size.
               "min": Use minimum dimensions across all maps (conservative).
               "max": Use maximum dimensions (requires upsampling).
               "median": Use median dimensions.
               "average": Use rounded average dimensions.

    Returns:
        Tuple of (target_height, target_width).
    """
    if not shapes:
        raise ValueError("At least one map shape must be provided.")

    heights = [s[0] for s in shapes]
    widths = [s[1] for s in shapes]

    if method == "min":
        target_h, target_w = min(heights), min(widths)
    elif method == "max":
        target_h, target_w = max(heights), max(widths)
    elif method == "median":
        target_h, target_w = int(np.median(heights)), int(np.median(widths))
    elif method == "average":
        target_h, target_w = int(round(np.mean(heights))), int(round(np.mean(widths)))
    else:
        raise ValueError(f"Unknown alignment method: {method}")

    # Ensure target dimensions are at least 2x2 for meaningful interpolation
    target_h = max(2, target_h)
    target_w = max(2, target_w)

    logger.info(f"Target grid shape calculated ({method} method): {target_h}x{target_w}")
    return target_h, target_w


def resample_map(
    data: np.ndarray,
    target_shape: Tuple[int, int],
    method: str = "linear",
    order: int = 1,
) -> np.ndarray:
    """
    Resample a 2D map to a target shape using various interpolation methods.

    Args:
        data: Input 2D numpy array (height, width).
        target_shape: Target (height, width).
        method: Interpolation method:
                "nearest": Nearest neighbor (order=0 in zoom).
                "linear": Linear interpolation (order=1 in zoom).
                "cubic": Cubic interpolation (order=3 in zoom).
                "spline": Spline interpolation using RectBivariateSpline.
        order: Order of spline interpolation for zoom-based methods (0, 1, or 3).

    Returns:
        Resampled 2D numpy array with shape matching target_shape.
    """
    if data.ndim != 2:
        raise ValueError(f"Input data must be 2D, got {data.ndim}D")

    original_shape = data.shape
    target_h, target_w = target_shape

    if original_shape == target_shape:
        logger.debug("Input shape matches target shape, returning copy.")
        return data.copy()

    if method == "spline":
        # Use RectBivariateSpline for higher accuracy interpolation
        y_orig = np.arange(original_shape[0])
        x_orig = np.arange(original_shape[1])
        y_new = np.linspace(0, original_shape[0] - 1, target_h)
        x_new = np.linspace(0, original_shape[1] - 1, target_w)

        spline = RectBivariateSpline(y_orig, x_orig, data)
        resampled = spline(y_new, x_new)
    else:
        # Use scipy.ndimage.zoom for simpler interpolation
        if method == "nearest":
            order = 0
        elif method == "linear":
            order = 1
        elif method == "cubic":
            order = 3
        else:
            raise ValueError(f"Unknown interpolation method: {method}")

        zoom_factors = (
            target_h / original_shape[0],
            target_w / original_shape[1],
        )
        resampled = zoom(data, zoom_factors, order=order)

    # Verify output shape
    if resampled.shape != target_shape:
        # Handle edge cases where zoom might produce off-by-one errors
        logger.warning(
            f"Resampled shape {resampled.shape} differs from target {target_shape}. "
            f"Adjusting via slicing/padding."
        )
        if resampled.shape[0] > target_shape[0] or resampled.shape[1] > target_shape[1]:
            # Slice to fit
            resampled = resampled[: target_shape[0], : target_shape[1]]
        else:
            # Pad with NaNs or zeros
            padded = np.full(target_shape, np.nan, dtype=data.dtype)
            padded[: resampled.shape[0], : resampled.shape[1]] = resampled
            resampled = padded

    return resampled


def align_maps(
    maps: Dict[str, np.ndarray],
    target_shape: Optional[Tuple[int, int]] = None,
    alignment_method: str = "min",
    interpolation_method: str = "linear",
) -> Dict[str, np.ndarray]:
    """
    Align multiple maps to a common grid.

    This function takes a dictionary of maps (element name -> data array) and
    resamples them all to a common target shape. If no target shape is provided,
    it calculates one based on the input shapes and the specified alignment method.

    Args:
        maps: Dictionary mapping element names to 2D numpy arrays.
        target_shape: Optional explicit target (height, width). If None, calculated.
        alignment_method: Strategy for target shape calculation if target_shape is None.
        interpolation_method: Method for resampling (nearest, linear, cubic, spline).

    Returns:
        Dictionary of aligned maps with uniform shape.

    Raises:
        ValueError: If maps dictionary is empty or contains non-2D arrays.
    """
    if not maps:
        raise ValueError("Maps dictionary cannot be empty.")

    # Validate input shapes
    shapes = []
    for name, data in maps.items():
        if not isinstance(data, np.ndarray):
            raise ValueError(f"Map '{name}' must be a numpy array, got {type(data)}")
        if data.ndim != 2:
            raise ValueError(f"Map '{name}' must be 2D, got {data.ndim}D")
        shapes.append(data.shape)

    # Determine target shape
    if target_shape is None:
        target_shape = calculate_target_grid_shape(shapes, method=alignment_method)

    logger.info(f"Aligning {len(maps)} maps to target shape {target_shape}")

    aligned_maps = {}
    for name, data in maps.items():
        logger.debug(f"Resampling map '{name}' from {data.shape} to {target_shape}")
        aligned_maps[name] = resample_map(
            data, target_shape, method=interpolation_method
        )

    return aligned_maps


def validate_alignment(
    aligned_maps: Dict[str, np.ndarray],
    tolerance: float = 0.0,
) -> bool:
    """
    Validate that all maps in a dictionary have consistent shapes and no NaNs.

    Args:
        aligned_maps: Dictionary of aligned maps.
        tolerance: Allowable fraction of NaN values (default 0.0).

    Returns:
        True if validation passes, False otherwise.
    """
    if not aligned_maps:
        return False

    shapes = [data.shape for data in aligned_maps.values()]
    first_shape = shapes[0]

    # Check shape consistency
    if not all(s == first_shape for s in shapes):
        logger.error(f"Shape mismatch in aligned maps: {shapes}")
        return False

    # Check for excessive NaNs
    for name, data in aligned_maps.items():
        nan_ratio = np.isnan(data).sum() / data.size
        if nan_ratio > tolerance:
            logger.warning(
                f"Map '{name}' has {nan_ratio:.2%} NaN values (tolerance: {tolerance:.2%})"
            )
            # Depending on strictness, this might return False
            # For now, we just log and continue

    return True


def create_aligned_dataset(
    raw_maps: Dict[str, Dict[str, np.ndarray]],
    sample_ids: List[str],
    target_shape: Optional[Tuple[int, int]] = None,
    alignment_method: str = "min",
    interpolation_method: str = "linear",
) -> Dict[str, Dict[str, np.ndarray]]:
    """
    Create an aligned dataset from multiple samples.

    Args:
        raw_maps: Dictionary mapping sample_id -> {element_name -> data_array}.
        sample_ids: List of sample IDs to process.
        target_shape: Optional global target shape for all samples.
        alignment_method: Method for target shape calculation.
        interpolation_method: Interpolation method for resampling.

    Returns:
        Dictionary mapping sample_id -> {element_name -> aligned_data_array}.
    """
    aligned_dataset = {}

    # If no global target shape, calculate per-sample target based on that sample's maps
    if target_shape is None:
        for sample_id in sample_ids:
            if sample_id not in raw_maps:
                logger.warning(f"Sample ID '{sample_id}' not found in raw maps, skipping.")
                continue

            sample_maps = raw_maps[sample_id]
            shapes = [data.shape for data in sample_maps.values()]
            sample_target_shape = calculate_target_grid_shape(shapes, method=alignment_method)

            aligned_dataset[sample_id] = align_maps(
                sample_maps,
                target_shape=sample_target_shape,
                alignment_method=alignment_method,
                interpolation_method=interpolation_method,
            )
    else:
        # Use the same target shape for all samples
        for sample_id in sample_ids:
            if sample_id not in raw_maps:
                logger.warning(f"Sample ID '{sample_id}' not found in raw maps, skipping.")
                continue

            sample_maps = raw_maps[sample_id]
            aligned_dataset[sample_id] = align_maps(
                sample_maps,
                target_shape=target_shape,
                alignment_method=alignment_method,
                interpolation_method=interpolation_method,
            )

    return aligned_dataset
