"""
Fractal dimension computation using box-counting algorithm on vorticity iso-surfaces.

Implements the box-counting method to estimate the fractal dimension (D_f) of
vorticity iso-surfaces derived from turbulent flow data.
"""

import numpy as np
from typing import Dict, Any, Optional, Tuple, List
from pathlib import Path
import logging

from config import get_config, validate_config
from utils.logging import get_logger


def _count_boxes(binary_volume: np.ndarray, box_size: int) -> int:
    """
    Count the number of boxes of a given size that intersect the iso-surface.
    
    Args:
        binary_volume: 3D boolean array where True indicates the iso-surface is present.
        box_size: Size of the cubic box in grid units.
        
    Returns:
        Number of boxes that contain at least one surface point.
    """
    if box_size <= 0:
        raise ValueError("box_size must be positive")
        
    shape = binary_volume.shape
    # Calculate number of boxes along each dimension
    n_boxes_x = shape[0] // box_size
    n_boxes_y = shape[1] // box_size
    n_boxes_z = shape[2] // box_size
    
    count = 0
    
    # Iterate through all possible box positions
    for i in range(n_boxes_x):
        for j in range(n_boxes_y):
            for k in range(n_boxes_z):
                # Extract the current box
                box = binary_volume[
                    i*box_size:(i+1)*box_size,
                    j*box_size:(j+1)*box_size,
                    k*box_size:(k+1)*box_size
                ]
                # If any point in the box is part of the surface, count it
                if np.any(box):
                    count += 1
                    
    return count


def _compute_iso_surface(
    vorticity_field: np.ndarray,
    threshold: float,
    method: str = "absolute"
) -> np.ndarray:
    """
    Compute a binary iso-surface mask from the vorticity field.
    
    Args:
        vorticity_field: 3D array of vorticity magnitudes.
        threshold: Threshold value for iso-surface extraction.
        method: "absolute" or "normalized" (relative to RMS).
        
    Returns:
        Boolean 3D array where True indicates the iso-surface.
    """
    if method == "normalized":
        rms = np.sqrt(np.mean(vorticity_field**2))
        if rms == 0:
            raise ValueError("RMS of vorticity field is zero; cannot normalize.")
        effective_threshold = threshold * rms
    else:
        effective_threshold = threshold
        
    # Create binary mask: points above threshold are part of the structure
    return vorticity_field > effective_threshold


def compute_fractal_dimension(
    vorticity_field: np.ndarray,
    threshold: float,
    threshold_method: str = "normalized",
    min_box_size: int = 4,
    max_box_size: Optional[int] = None,
    logger: Optional[logging.Logger] = None
) -> Dict[str, Any]:
    """
    Compute the fractal dimension (D_f) of a vorticity iso-surface using box-counting.
    
    Args:
        vorticity_field: 3D numpy array of vorticity magnitudes.
        threshold: Threshold value (absolute or relative to RMS).
        threshold_method: "absolute" or "normalized".
        min_box_size: Minimum box size for counting.
        max_box_size: Maximum box size (defaults to 1/4 of grid size).
        logger: Logger instance for progress updates.
        
    Returns:
        Dictionary containing:
            - D_f: Estimated fractal dimension.
            - R_squared: R-squared value of the linear fit.
            - box_sizes: List of box sizes used.
            - counts: List of box counts for each size.
            - threshold_used: The effective threshold value applied.
            - status: "success", "rejected_no_surface", or "rejected_space_filling".
            - message: Optional explanation for rejection.
    """
    if logger is None:
        logger = logging.getLogger(__name__)
        
    # Validate input
    if vorticity_field.ndim != 3:
        raise ValueError("vorticity_field must be a 3D array")
        
    grid_size = vorticity_field.shape[0]
    if vorticity_field.shape[1] != grid_size or vorticity_field.shape[2] != grid_size:
        raise ValueError("vorticity_field must be a cubic grid")
        
    if max_box_size is None:
        max_box_size = grid_size // 4
        
    # Compute iso-surface
    try:
        iso_surface = _compute_iso_surface(
            vorticity_field, threshold, threshold_method
        )
    except ValueError as e:
        return {
            "D_f": None,
            "R_squared": None,
            "box_sizes": [],
            "counts": [],
            "threshold_used": None,
            "status": "rejected_no_surface",
            "message": str(e)
        }
    
    # Check for edge cases
    num_surface_points = np.sum(iso_surface)
    if num_surface_points == 0:
        return {
            "D_f": None,
            "R_squared": None,
            "box_sizes": [],
            "counts": [],
            "threshold_used": threshold,
            "status": "rejected_no_surface",
            "message": "Threshold yielded no surface points."
        }
        
    if num_surface_points == vorticity_field.size:
        return {
            "D_f": None,
            "R_squared": None,
            "box_sizes": [],
            "counts": [],
            "threshold_used": threshold,
            "status": "rejected_space_filling",
            "message": "Threshold yielded a space-filling result (all points included)."
        }
    
    # Generate box sizes (powers of 2 for efficient counting)
    box_sizes = []
    current_size = min_box_size
    while current_size <= max_box_size:
        box_sizes.append(current_size)
        current_size *= 2
        
    # Count boxes for each size
    counts = []
    for box_size in box_sizes:
        count = _count_boxes(iso_surface, box_size)
        counts.append(count)
        if logger:
            logger.debug(f"Box size {box_size}: {count} boxes")
    
    if len(counts) < 2:
        return {
            "D_f": None,
            "R_squared": None,
            "box_sizes": box_sizes,
            "counts": counts,
            "threshold_used": threshold,
            "status": "rejected_insufficient_data",
            "message": "Insufficient box sizes for linear regression."
        }
    
    # Perform linear regression: log(N) = -D_f * log(r) + C
    log_sizes = np.log(np.array(box_sizes))
    log_counts = np.log(np.array(counts))
    
    # Fit line using least squares
    A = np.vstack([log_sizes, np.ones(len(log_sizes))]).T
    slope, intercept = np.linalg.lstsq(A, log_counts, rcond=None)[0]
    
    D_f = -slope
    R_squared = 1 - np.sum((log_counts - (slope * log_sizes + intercept))**2) / np.sum((log_counts - np.mean(log_counts))**2)
    
    # Validate D_f range
    if not (2.0 <= D_f <= 3.0):
        logger.warning(f"Computed D_f = {D_f:.4f} is outside expected range [2.0, 3.0]")
    
    return {
        "D_f": D_f,
        "R_squared": R_squared,
        "box_sizes": box_sizes,
        "counts": counts,
        "threshold_used": threshold,
        "status": "success",
        "message": None
    }


def batch_fractal_analysis(
    vorticity_field: np.ndarray,
    thresholds: List[float],
    threshold_method: str = "normalized",
    logger: Optional[logging.Logger] = None
) -> List[Dict[str, Any]]:
    """
    Run box-counting analysis across multiple thresholds.
    
    Args:
        vorticity_field: 3D numpy array of vorticity magnitudes.
        thresholds: List of threshold values to test.
        threshold_method: "absolute" or "normalized".
        logger: Logger instance.
        
    Returns:
        List of result dictionaries, one per threshold.
    """
    results = []
    for thresh in thresholds:
        if logger:
            logger.info(f"Computing D_f for threshold {thresh}")
        result = compute_fractal_dimension(
            vorticity_field,
            thresh,
            threshold_method,
            logger=logger
        )
        result["threshold_input"] = thresh
        results.append(result)
    return results


def main():
    """
    CLI entry point for standalone fractal analysis.
    Expects a preprocessed vorticity field file (HDF5) and config.
    """
    import argparse
    import json
    import h5py
    
    parser = argparse.ArgumentParser(description="Compute fractal dimension from vorticity field")
    parser.add_argument("--input", type=str, required=True, help="Path to input HDF5 file")
    parser.add_argument("--output", type=str, required=True, help="Path to output JSON file")
    parser.add_argument("--thresholds", type=float, nargs="+", default=[2.0, 3.0, 4.0], 
                        help="Threshold multipliers for RMS (default: 2.0 3.0 4.0)")
    parser.add_argument("--method", type=str, default="normalized", 
                        choices=["absolute", "normalized"], help="Threshold method")
    
    args = parser.parse_args()
    
    logger = get_logger("fractal_analysis")
    logger.info(f"Loading vorticity field from {args.input}")
    
    # Load data
    with h5py.File(args.input, "r") as f:
        if "vorticity" in f:
            vorticity = f["vorticity"][:]
        elif "vorticity_magnitude" in f:
            vorticity = f["vorticity_magnitude"][:]
        else:
            raise KeyError("Input file must contain 'vorticity' or 'vorticity_magnitude' dataset")
    
    logger.info(f"Running box-counting analysis with thresholds: {args.thresholds}")
    results = batch_fractal_analysis(
        vorticity,
        args.thresholds,
        args.method,
        logger=logger
    )
    
    # Save results
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, "w") as f:
        json.dump(results, f, indent=2)
        
    logger.info(f"Results saved to {args.output}")
    
    # Print summary
    successful = [r for r in results if r["status"] == "success"]
    if successful:
        avg_d_f = np.mean([r["D_f"] for r in successful])
        logger.info(f"Average D_f across {len(successful)} thresholds: {avg_d_f:.4f}")
    else:
        logger.warning("No successful D_f computations found.")

if __name__ == "__main__":
    main()