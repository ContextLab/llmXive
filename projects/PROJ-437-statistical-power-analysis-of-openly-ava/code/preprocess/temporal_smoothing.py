"""
Temporal smoothing module for 1D ROI time-series data.

This module implements temporal smoothing kernels (equivalent to 4mm, 8mm spatial
smoothing in terms of degrees of freedom/frequency attenuation) applied to
pre-extracted ROI time-series.

Required by FR-002 (adapted): Distinct from spatial smoothing.
"""

import argparse
import json
import logging
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any, Union

import numpy as np
import pandas as pd

# Import seed manager for reproducibility
from utils.seed_manager import set_global_seed

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def apply_temporal_smoothing(
    timeseries: np.ndarray,
    kernel_size: int,
    axis: int = -1
) -> np.ndarray:
    """
    Apply a Gaussian temporal smoothing kernel to a 1D or 2D time-series.

    This function applies a moving average with Gaussian weights to smooth
    temporal fluctuations in the data. The kernel_size parameter controls
    the width of the smoothing window (in time points).

    Args:
        timeseries: Input time-series data. Can be 1D (single ROI) or 2D (multiple ROIs).
        kernel_size: Width of the smoothing kernel in time points.
            - 4mm equivalent: ~3-5 time points (depending on TR)
            - 8mm equivalent: ~5-9 time points (depending on TR)
        axis: Axis along which to apply smoothing. Default is last axis (-1).

    Returns:
        Smoothed time-series with same shape as input.

    Raises:
        ValueError: If kernel_size is less than 1 or if input is empty.
    """
    if kernel_size < 1:
        raise ValueError(f"Kernel size must be >= 1, got {kernel_size}")

    if timeseries.size == 0:
        raise ValueError("Input time-series is empty")

    # Normalize axis to be positive
    if axis < 0:
        axis = timeseries.ndim + axis

    if axis < 0 or axis >= timeseries.ndim:
        raise ValueError(f"Axis {axis} out of bounds for array with {timeseries.ndim} dimensions")

    # Create Gaussian kernel
    # Standard deviation is typically kernel_size / 6 for good coverage
    sigma = kernel_size / 6.0
    if sigma < 0.5:
        sigma = 0.5  # Minimum sigma to avoid numerical issues

    x = np.arange(-kernel_size // 2, kernel_size // 2 + 1)
    kernel = np.exp(-0.5 * (x / sigma) ** 2)
    kernel = kernel / kernel.sum()  # Normalize to sum to 1

    # Apply smoothing using convolution
    # Use 'same' mode to preserve input shape
    if timeseries.ndim == 1:
        smoothed = np.convolve(timeseries, kernel, mode='same')
    else:
        # For 2D arrays, apply along specified axis
        # Transpose to put smoothing axis first, then apply 1D convolution
        # We'll use a loop for simplicity and clarity
        smoothed = np.zeros_like(timeseries)
        if axis == 0:
            for i in range(timeseries.shape[1]):
                smoothed[:, i] = np.convolve(timeseries[:, i], kernel, mode='same')
        elif axis == 1:
            for i in range(timeseries.shape[0]):
                smoothed[i, :] = np.convolve(timeseries[i, :], kernel, mode='same')
        else:
            # For higher dimensions, flatten other axes
            # This is a simplified approach that handles the common 1D/2D cases
            logger.warning(f"Axis {axis} for {timeseries.ndim}D array not fully optimized, using fallback")
            # Fallback: reshape to 2D with smoothing axis last
            original_shape = timeseries.shape
            timeseries_flat = timeseries.reshape(-1, timeseries.shape[axis])
            kernel_axis = 1
            smoothed_flat = np.zeros_like(timeseries_flat)
            for i in range(smoothed_flat.shape[0]):
                smoothed_flat[i, :] = np.convolve(timeseries_flat[i, :], kernel, mode='same')
            smoothed = smoothed_flat.reshape(original_shape)

    return smoothed


def load_roi_timeseries(file_path: Path) -> Dict[str, np.ndarray]:
    """
    Load ROI time-series from a CSV or JSON file.

    Expected formats:
    - CSV: columns are ROI names, rows are time points
    - JSON: {"roi_name": [time_points], ...}

    Args:
        file_path: Path to the input file.

    Returns:
        Dictionary mapping ROI names to 1D numpy arrays.

    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If the file format is unsupported or parsing fails.
    """
    if not file_path.exists():
        raise FileNotFoundError(f"ROI time-series file not found: {file_path}")

    suffix = file_path.suffix.lower()

    if suffix == '.csv':
        df = pd.read_csv(file_path)
        # Assume first column is time or index, rest are ROIs
        # If first column is not numeric, treat it as index
        if pd.api.types.is_numeric_dtype(df.iloc[:, 0]):
            roi_data = df.iloc[:, 1:].to_dict('list')
        else:
            roi_data = df.to_dict('list')

        # Convert to numpy arrays
        return {k: np.array(v, dtype=float) for k, v in roi_data.items()}

    elif suffix == '.json':
        with open(file_path, 'r') as f:
            data = json.load(f)

        if not isinstance(data, dict):
            raise ValueError(f"JSON file must contain a dictionary of ROI data, got {type(data)}")

        return {k: np.array(v, dtype=float) for k, v in data.items()}

    else:
        raise ValueError(f"Unsupported file format: {suffix}. Use .csv or .json")


def save_smoothed_timeseries(
    smoothed_data: Dict[str, np.ndarray],
    output_path: Path
) -> None:
    """
    Save smoothed time-series to a CSV file.

    Args:
        smoothed_data: Dictionary mapping ROI names to 1D numpy arrays.
        output_path: Path to the output CSV file.
    """
    # Convert to DataFrame
    df = pd.DataFrame(smoothed_data)
    df.to_csv(output_path, index=False)
    logger.info(f"Saved smoothed time-series to {output_path}")


def process_single_roi_file(
    input_path: Path,
    output_path: Path,
    kernel_size: int
) -> Dict[str, Any]:
    """
    Process a single ROI time-series file with temporal smoothing.

    Args:
        input_path: Path to input ROI time-series file.
        output_path: Path to save smoothed time-series.
        kernel_size: Smoothing kernel size in time points.

    Returns:
        Dictionary with processing metadata.
    """
    logger.info(f"Processing {input_path} with kernel size {kernel_size}")

    # Load data
    roi_data = load_roi_timeseries(input_path)
    logger.info(f"Loaded {len(roi_data)} ROIs")

    # Apply smoothing
    smoothed_data = {}
    for roi_name, timeseries in roi_data.items():
        smoothed_timeseries = apply_temporal_smoothing(timeseries, kernel_size)
        smoothed_data[roi_name] = smoothed_timeseries

    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Save results
    save_smoothed_timeseries(smoothed_data, output_path)

    # Calculate summary statistics
    stats = {
        'input_file': str(input_path),
        'output_file': str(output_path),
        'kernel_size': kernel_size,
        'num_rois': len(roi_data),
        'num_timepoints': len(next(iter(roi_data.values()))),
        'success': True
    }

    return stats


def main(args: Optional[List[str]] = None) -> int:
    """
    Main entry point for temporal smoothing CLI.

    Args:
        args: Command line arguments. If None, uses sys.argv[1:].

    Returns:
        Exit code (0 for success, 1 for failure).
    """
    parser = argparse.ArgumentParser(
        description='Apply temporal smoothing to ROI time-series data.'
    )
    parser.add_argument(
        '--input', '-i',
        type=Path,
        required=True,
        help='Path to input ROI time-series file (CSV or JSON)'
    )
    parser.add_argument(
        '--output', '-o',
        type=Path,
        required=True,
        help='Path to output smoothed time-series file (CSV)'
    )
    parser.add_argument(
        '--kernel', '-k',
        type=int,
        default=5,
        help='Smoothing kernel size in time points (default: 5, approx 4mm equivalent)'
    )
    parser.add_argument(
        '--seed', '-s',
        type=int,
        default=42,
        help='Random seed for reproducibility (default: 42)'
    )

    parsed_args = parser.parse_args(args)

    # Set global seed for reproducibility
    set_global_seed(parsed_args.seed)

    try:
        # Process the file
        stats = process_single_roi_file(
            parsed_args.input,
            parsed_args.output,
            parsed_args.kernel
        )

        # Log summary
        logger.info(f"Processing complete: {stats}")

        # Save metadata
        metadata_path = parsed_args.output.with_suffix('.json')
        with open(metadata_path, 'w') as f:
            json.dump(stats, f, indent=2)

        return 0

    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        return 1
    except ValueError as e:
        logger.error(f"Value error: {e}")
        return 1
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        return 1


if __name__ == '__main__':
    sys.exit(main())