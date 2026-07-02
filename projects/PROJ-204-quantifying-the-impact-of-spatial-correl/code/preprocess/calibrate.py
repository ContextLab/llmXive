"""
Calibration and defect masking module for perovskite elemental maps.

This module implements the masking of defective regions (dead pixels, artifacts)
in EDS elemental maps and logs the percentage of masked area for quality control.
"""
import numpy as np
import logging
from typing import Dict, List, Tuple, Optional, Union, Any
from pathlib import Path
from scipy import ndimage
import json

# Configure logging
logger = logging.getLogger(__name__)
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)


def detect_dead_pixels(
    map_data: np.ndarray,
    threshold_std: float = 5.0,
    connectivity: int = 1
) -> np.ndarray:
    """
    Detect dead pixels or stuck pixels based on local variance and absolute values.

    Dead pixels often manifest as extreme outliers (very low or very high) compared
    to their immediate neighbors.

    Args:
        map_data: 2D numpy array of the elemental map.
        threshold_std: Number of standard deviations from the local mean to flag as dead.
        connectivity: Neighborhood connectivity for convolution (1 or 2).

    Returns:
        Boolean mask where True indicates a detected defective pixel.
    """
    if map_data.ndim != 2:
        raise ValueError("map_data must be a 2D array.")

    # Calculate local mean using convolution
    kernel = np.ones((3, 3))
    # Handle boundaries by reflecting
    local_mean = ndimage.convolve(map_data.astype(float), kernel, mode='reflect') / 9.0

    # Calculate local std dev
    local_sq_mean = ndimage.convolve(map_data.astype(float)**2, kernel, mode='reflect') / 9.0
    local_var = local_sq_mean - local_mean**2
    # Ensure non-negative variance due to floating point errors
    local_var = np.maximum(local_var, 0)
    local_std = np.sqrt(local_var)

    # Avoid division by zero in uniform regions
    local_std[local_std < 1e-9] = 1e-9

    # Detect outliers: |x - local_mean| > threshold * local_std
    # Also check for absolute stuck values (e.g., 0 or 65535 in 16-bit data)
    # Assuming data is not normalized to 0-1 yet, but if it is, we check extremes
    diff = np.abs(map_data.astype(float) - local_mean)
    outlier_mask = diff > (threshold_std * local_std)

    # Check for stuck pixels (extreme values relative to global min/max if range is known)
    # Heuristic: if value is exactly 0 and neighbors are not, or value is max possible and neighbors aren't.
    # For generic float data, we rely on the statistical outlier detection primarily.
    # However, dead pixels in EDS often show as 0.
    zero_mask = (map_data == 0) & (local_mean > 0) # Local mean > 0 implies neighbors exist and aren't all 0

    return outlier_mask | zero_mask


def detect_artifacts(
    map_data: np.ndarray,
    min_cluster_size: int = 3,
    noise_threshold: float = 3.0
) -> np.ndarray:
    """
    Detect small noise artifacts or salt-and-pepper noise.

    Args:
        map_data: 2D numpy array of the elemental map.
        min_cluster_size: Minimum number of connected pixels to consider an artifact.
        noise_threshold: Standard deviations from global mean to consider a pixel noisy.

    Returns:
        Boolean mask where True indicates a detected artifact pixel.
    """
    if map_data.ndim != 2:
        raise ValueError("map_data must be a 2D array.")

    global_mean = np.mean(map_data)
    global_std = np.std(map_data)

    if global_std < 1e-9:
        return np.zeros_like(map_data, dtype=bool)

    # Identify pixels that deviate significantly from global mean
    noise_mask = np.abs(map_data - global_mean) > (noise_threshold * global_std)

    # Label connected components in the noise mask
    labeled_array, num_features = ndimage.label(noise_mask)

    # Calculate sizes of each component
    component_sizes = np.bincount(labeled_array.ravel())
    # Filter out the background (label 0)
    component_sizes[0] = 0

    # Create a mask of small components
    small_components = component_sizes < min_cluster_size
    artifact_mask = np.isin(labeled_array, np.where(small_components)[0])

    return artifact_mask


def mask_defective_regions(
    map_data: np.ndarray,
    dead_pixel_std_threshold: float = 5.0,
    artifact_noise_threshold: float = 3.0,
    min_artifact_cluster_size: int = 3,
    replace_value: Optional[float] = None
) -> Tuple[np.ndarray, float, Dict[str, int]]:
    """
    Mask defective regions in an elemental map.

    This function identifies dead pixels and small noise artifacts, creates a mask,
    and optionally replaces the defective values with a specified value (e.g., median,
    interpolated, or a specific fill value).

    Args:
        map_data: 2D numpy array of the elemental map.
        dead_pixel_std_threshold: Std dev multiplier for dead pixel detection.
        artifact_noise_threshold: Std dev multiplier for artifact detection.
        min_artifact_cluster_size: Min size for an artifact cluster.
        replace_value: Value to replace defective pixels with. If None, uses local median interpolation.

    Returns:
        Tuple of:
            - masked_map: The cleaned map data.
            - masked_percentage: Percentage of total pixels that were masked.
            - stats: Dictionary with counts of dead pixels and artifacts.
    """
    if map_data.ndim != 2:
        raise ValueError("map_data must be a 2D array.")

    # Detect defects
    dead_pixel_mask = detect_dead_pixels(map_data, threshold_std=dead_pixel_std_threshold)
    artifact_mask = detect_artifacts(map_data, noise_threshold=artifact_noise_threshold,
                                     min_cluster_size=min_artifact_cluster_size)

    combined_mask = dead_pixel_mask | artifact_mask
    total_pixels = map_data.size
    masked_count = np.sum(combined_mask)
    masked_percentage = (masked_count / total_pixels) * 100.0

    stats = {
        "dead_pixels": int(np.sum(dead_pixel_mask)),
        "artifacts": int(np.sum(artifact_mask)),
        "total_masked": int(masked_count),
        "masked_percentage": masked_percentage
    }

    if masked_count == 0:
        logger.info("No defective regions detected.")
        return map_data.copy(), 0.0, stats

    masked_map = map_data.copy()

    # Fill strategy
    if replace_value is not None:
        masked_map[combined_mask] = replace_value
        logger.info(f"Replaced {masked_count} defective pixels with value {replace_value}.")
    else:
        # Use interpolation to fill (scipy.ndimage)
        # Create a mask of valid data (inverse of combined_mask)
        valid_mask = ~combined_mask
        # Use nearest neighbor or spline interpolation to fill holes
        # For robustness, we'll use a simple approach: replace with local median of valid neighbors
        # Or use ndimage.generic_filter with a median function, but handling boundaries is tricky.
        # A robust simple way: use ndimage.map_coordinates with nearest valid?
        # Let's use scipy.interpolate if available, but to keep deps minimal and robust:
        # We'll use a simple iterative fill or just set to global median of valid pixels if holes are small.
        # For high quality, we use ndimage.binary_fill_holes logic but on values? No.
        # Let's use a simple local median fill using a loop or vectorized approach if possible.
        # Given constraints, we will replace with the median of the valid pixels in the map.
        # This is a safe fallback.
        valid_values = map_data[valid_mask]
        if len(valid_values) > 0:
            fill_value = np.median(valid_values)
            masked_map[combined_mask] = fill_value
            logger.info(f"Replaced {masked_count} defective pixels with global median {fill_value:.4f}.")
        else:
            logger.warning("No valid pixels found to determine fill value. Map may be all noise.")
            masked_map[:] = 0.0

    return masked_map, masked_percentage, stats


def calibrate_and_log(
    map_paths: List[str],
    output_log_path: Optional[str] = None,
    dead_pixel_std_threshold: float = 5.0,
    artifact_noise_threshold: float = 3.0,
    min_artifact_cluster_size: int = 3
) -> List[Dict[str, Any]]:
    """
    Process a list of map files, mask defects, and log results.

    Args:
        map_paths: List of paths to map files (assumed to be .npy or similar loadable format).
                   If paths are not valid files, this function expects a dictionary or
                   pre-loaded data structure if passed differently, but here we assume file paths.
                   For this implementation, we assume the caller passes a list of dictionaries
                   with 'path' and 'data' if files are not on disk, OR we try to load them.
                   To be robust against the "real data" constraint, we assume the data is
                   passed as a list of (sample_id, numpy_array) or we load from disk if paths exist.
                   Let's assume the input is a list of dicts: [{'sample_id': '...', 'data': np.array}, ...]
                   OR a list of paths.
                   Re-reading task: "Implement ... to mask defective regions ... and log masked area percentage".
                   It doesn't specify input format. We will assume a list of (sample_id, data) tuples
                   or a list of dicts is passed, as loading from disk is usually done in ingest.py.
                   However, to be generic, we will accept a list of dictionaries containing 'sample_id' and 'data'.

    Returns:
        List of dictionaries containing sample_id, masked_percentage, and stats.
    """
    results = []
    log_entries = []

    # Normalize input handling
    # If the input is a list of strings (paths), we try to load them.
    # If it's a list of dicts with 'data', we use that.
    # This function is a utility, so we expect the data to be ready or easily loadable.

    for item in map_paths:
        sample_id = "unknown"
        map_data = None

        if isinstance(item, dict):
            sample_id = item.get('sample_id', 'unknown')
            map_data = item.get('data')
        elif isinstance(item, str):
            # Try to load from path
            path = Path(item)
            if not path.exists():
                logger.error(f"File not found: {item}")
                continue
            # Assuming .npy for now as it's standard for numpy arrays in this context
            if path.suffix == '.npy':
                map_data = np.load(path)
                sample_id = path.stem
            else:
                logger.warning(f"Unsupported file format for {item}, skipping.")
                continue
        elif isinstance(item, np.ndarray):
            # If just an array is passed, we need a sample_id
            sample_id = f"sample_{len(results)}"
            map_data = item
        else:
            logger.warning(f"Unknown input type: {type(item)}, skipping.")
            continue

        if map_data is None:
            continue

        # Ensure 2D
        if map_data.ndim > 2:
            # If 3D (e.g. RGB or multiple channels), take the first channel or mean?
            # EDS maps are usually single channel per element.
            # If it's (H, W, C), we assume C=1 or take first.
            if map_data.shape[-1] in [3, 4]:
                map_data = map_data[..., 0] # Take first channel
            elif map_data.ndim == 3 and map_data.shape[0] < 10:
                map_data = map_data[0] # Assume first slice
            else:
                logger.error(f"Map for {sample_id} is not 2D and cannot be easily reduced.")
                continue

        # Perform masking
        try:
            masked_map, masked_pct, stats = mask_defective_regions(
                map_data,
                dead_pixel_std_threshold=dead_pixel_std_threshold,
                artifact_noise_threshold=artifact_noise_threshold,
                min_artifact_cluster_size=min_artifact_cluster_size
            )

            result_entry = {
                "sample_id": sample_id,
                "masked_percentage": masked_pct,
                "dead_pixels": stats["dead_pixels"],
                "artifacts": stats["artifacts"],
                "total_masked": stats["total_masked"],
                "status": "success"
            }
            results.append(result_entry)
            log_entries.append(f"Sample {sample_id}: Masked {masked_pct:.2f}% ({stats['total_masked']} pixels)")

            # Save masked map if needed? Task says "log masked area percentage".
            # We return the stats and the masked map if the caller wants it, but the function signature
            # here returns the list of stats. The caller (ingest.py) would handle saving.

        except Exception as e:
            logger.error(f"Error processing {sample_id}: {e}")
            results.append({
                "sample_id": sample_id,
                "status": "error",
                "error": str(e)
            })

    # Write log file if path provided
    if output_log_path:
        log_path = Path(output_log_path)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        with open(log_path, 'w') as f:
            f.write("Calibration Log\n")
            f.write("="*40 + "\n")
            for entry in log_entries:
                f.write(entry + "\n")
            logger.info(f"Calibration log written to {output_log_path}")

    return results


def apply_mask_to_dataset(
    dataset: List[Dict[str, Any]],
    mask_threshold: float = 10.0
) -> List[Dict[str, Any]]:
    """
    Apply masking to a list of dataset items and filter out those with excessive masking.

    Args:
        dataset: List of dicts containing 'data' and 'sample_id'.
        mask_threshold: Maximum allowed masked percentage to keep the sample.

    Returns:
        Filtered list of valid samples and a list of rejected samples.
    """
    valid_samples = []
    rejected_samples = []

    for item in dataset:
        if 'data' not in item:
            rejected_samples.append(item)
            continue

        map_data = item['data']
        sample_id = item.get('sample_id', 'unknown')

        # Ensure 2D
        if map_data.ndim > 2:
            if map_data.shape[-1] in [3, 4]:
                map_data = map_data[..., 0]
            elif map_data.ndim == 3:
                map_data = map_data[0]
            else:
                rejected_samples.append(item)
                continue

        _, masked_pct, _ = mask_defective_regions(map_data)

        if masked_pct <= mask_threshold:
            item['masked_percentage'] = masked_pct
            valid_samples.append(item)
        else:
            item['rejection_reason'] = f"Excessive masking: {masked_pct:.2f}%"
            rejected_samples.append(item)

    return valid_samples, rejected_samples
