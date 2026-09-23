"""
Temporal smoothing module for 1D ROI time-series.

Applies Gaussian temporal smoothing kernels (FWHM) to preprocessed ROI time-series data.
Implements temporal smoothing as a CPU-tractable equivalent to spatial smoothing,
mapping spatial kernel sizes to temporal durations (TR=2s).

Mapping:
  - 4mm spatial -> 4s temporal (2 TRs)
  - 8mm spatial -> 8s temporal (4 TRs)
"""

import argparse
import json
import logging
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any, Union

import numpy as np
from scipy.signal import convolve

# Import from local project modules
from utils.seed_manager import set_global_seed
from utils.timer import log_split

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
DEFAULT_TR = 2.0  # Repetition time in seconds
DEFAULT_KERNEL_SIZES = [4, 8]  # Temporal kernel sizes in seconds


def _gaussian_kernel_1d(fwhm: float, tr: float = DEFAULT_TR) -> np.ndarray:
    """
    Generate a 1D Gaussian kernel with specified Full Width at Half Maximum (FWHM).

    Args:
        fwhm: Full width at half maximum in seconds.
        tr: Repetition time in seconds.

    Returns:
        1D numpy array representing the Gaussian kernel.
    """
    # Convert FWHM to standard deviation: sigma = FWHM / (2 * sqrt(2 * ln(2)))
    sigma = fwhm / (2 * np.sqrt(2 * np.log(2)))

    # Determine kernel size (odd number of samples)
    # Kernel width should be at least 3 * sigma on each side
    kernel_width_samples = int(np.ceil(6 * sigma / tr))
    if kernel_width_samples % 2 == 0:
        kernel_width_samples += 1

    # Generate kernel
    x = np.arange(-kernel_width_samples // 2, kernel_width_samples // 2 + 1) * tr
    kernel = np.exp(-0.5 * (x / sigma) ** 2)

    # Normalize to sum to 1
    kernel = kernel / np.sum(kernel)

    return kernel


def apply_temporal_smoothing(
    timeseries: np.ndarray,
    kernel_size_seconds: float,
    tr: float = DEFAULT_TR,
    boundary_mode: str = 'reflect'
) -> np.ndarray:
    """
    Apply temporal smoothing to a 1D time-series using a Gaussian kernel.

    Args:
        timeseries: 1D numpy array of time-series values.
        kernel_size_seconds: Size of the temporal smoothing kernel in seconds.
        tr: Repetition time in seconds.
        boundary_mode: Boundary handling mode for convolution ('reflect', 'constant', etc.).

    Returns:
        Smoothed 1D numpy array.
    """
    if timeseries.ndim != 1:
        raise ValueError(f"Expected 1D time-series, got {timeseries.ndim}D array")

    if len(timeseries) == 0:
        return timeseries.copy()

    # Generate Gaussian kernel
    kernel = _gaussian_kernel_1d(kernel_size_seconds, tr)

    # Apply convolution with boundary handling
    # 'reflect' mode reflects the array at the boundary
    if boundary_mode == 'reflect':
        # Manual reflect padding for better control
        pad_size = len(kernel) // 2
        if pad_size > 0:
            padded = np.pad(
                timeseries,
                pad_width=pad_size,
                mode='reflect'
            )
            smoothed = convolve(padded, kernel, mode='valid')
        else:
            smoothed = timeseries.copy()
    else:
        # Use scipy's built-in modes for other cases
        smoothed = convolve(
            timeseries,
            kernel,
            mode='same',
            method='direct'
        )

    return smoothed


def load_roi_timeseries(roi_file_path: Path) -> Tuple[np.ndarray, Dict[str, Any]]:
    """
    Load ROI time-series data from a JSON file.

    Expected format:
    {
        "roi_name": "string",
        "subject_id": "string",
        "paradigm_id": "string",
        "timeseries": [float, float, ...],
        "tr": float,
        "metadata": {...}
    }

    Args:
        roi_file_path: Path to the JSON file containing ROI data.

    Returns:
        Tuple of (timeseries array, metadata dict).
    """
    if not roi_file_path.exists():
        raise FileNotFoundError(f"ROI file not found: {roi_file_path}")

    with open(roi_file_path, 'r') as f:
        data = json.load(f)

    if 'timeseries' not in data:
        raise ValueError(f"Missing 'timeseries' key in {roi_file_path}")

    timeseries = np.array(data['timeseries'], dtype=np.float64)

    # Extract metadata
    metadata = {
        'roi_name': data.get('roi_name', 'unknown'),
        'subject_id': data.get('subject_id', 'unknown'),
        'paradigm_id': data.get('paradigm_id', 'unknown'),
        'tr': data.get('tr', DEFAULT_TR),
        'original_length': len(timeseries)
    }

    return timeseries, metadata


def save_smoothed_timeseries(
    timeseries: np.ndarray,
    metadata: Dict[str, Any],
    output_path: Path,
    kernel_size_seconds: float
) -> None:
    """
    Save smoothed time-series data to a JSON file.

    Args:
        timeseries: Smoothed time-series array.
        metadata: Original metadata dict.
        output_path: Path to save the JSON file.
        kernel_size_seconds: Size of the applied smoothing kernel.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)

    output_data = {
        'roi_name': metadata['roi_name'],
        'subject_id': metadata['subject_id'],
        'paradigm_id': metadata['paradigm_id'],
        'timeseries': timeseries.tolist(),
        'tr': metadata['tr'],
        'kernel_size_seconds': kernel_size_seconds,
        'original_length': metadata['original_length'],
        'smoothed_length': len(timeseries),
        'processing_timestamp': str(np.datetime64('now')),
        'metadata': metadata.get('metadata', {})
    }

    with open(output_path, 'w') as f:
        json.dump(output_data, f, indent=2)

    logger.info(f"Saved smoothed timeseries to {output_path}")


def process_single_roi_file(
    input_path: Path,
    output_dir: Path,
    kernel_size_seconds: float,
    tr: float = DEFAULT_TR
) -> Dict[str, Any]:
    """
    Process a single ROI file: load, smooth, and save.

    Args:
        input_path: Path to input ROI JSON file.
        output_dir: Directory to save output files.
        kernel_size_seconds: Size of the temporal smoothing kernel.
        tr: Repetition time.

    Returns:
        Dictionary with processing results.
    """
    try:
        # Load data
        timeseries, metadata = load_roi_timeseries(input_path)

        # Apply smoothing
        smoothed_timeseries = apply_temporal_smoothing(
            timeseries,
            kernel_size_seconds,
            tr=tr,
            boundary_mode='reflect'
        )

        # Generate output filename
        output_filename = input_path.stem + f"_smoothed_{int(kernel_size_seconds)}s.json"
        output_path = output_dir / output_filename

        # Save results
        save_smoothed_timeseries(
            smoothed_timeseries,
            metadata,
            output_path,
            kernel_size_seconds
        )

        return {
            'success': True,
            'input_file': str(input_path),
            'output_file': str(output_path),
            'roi_name': metadata['roi_name'],
            'subject_id': metadata['subject_id'],
            'kernel_size_seconds': kernel_size_seconds,
            'original_length': metadata['original_length'],
            'smoothed_length': len(smoothed_timeseries)
        }

    except Exception as e:
        logger.error(f"Failed to process {input_path}: {str(e)}")
        return {
            'success': False,
            'input_file': str(input_path),
            'error': str(e)
        }


def main() -> int:
    """
    Main entry point for temporal smoothing pipeline.

    Processes all ROI files in the input directory with specified kernel sizes.
    Outputs smoothed files to the designated output directory.
    """
    parser = argparse.ArgumentParser(
        description='Apply temporal smoothing to ROI time-series data'
    )
    parser.add_argument(
        '--input-dir',
        type=str,
        required=True,
        help='Directory containing ROI JSON files'
    )
    parser.add_argument(
        '--output-dir',
        type=str,
        required=True,
        help='Directory to save smoothed ROI files'
    )
    parser.add_argument(
        '--kernels',
        type=str,
        default='4,8',
        help='Comma-separated list of kernel sizes in seconds (default: 4,8)'
    )
    parser.add_argument(
        '--tr',
        type=float,
        default=DEFAULT_TR,
        help=f'Repetition time in seconds (default: {DEFAULT_TR})'
    )
    parser.add_argument(
        '--seed',
        type=int,
        default=42,
        help='Random seed for reproducibility'
    )
    parser.add_argument(
        '--log-file',
        type=str,
        default=None,
        help='Path to save processing log'
    )

    args = parser.parse_args()

    # Set global seed
    set_global_seed(args.seed)

    # Parse kernel sizes
    kernel_sizes = [float(k.strip()) for k in args.kernels.split(',')]
    logger.info(f"Applying temporal smoothing with kernel sizes: {kernel_sizes}s")
    logger.info(f"Using TR = {args.tr}s")

    input_dir = Path(args.input_dir)
    output_dir = Path(args.output_dir)

    if not input_dir.exists():
        logger.error(f"Input directory does not exist: {input_dir}")
        return 1

    output_dir.mkdir(parents=True, exist_ok=True)

    # Find all ROI JSON files
    roi_files = list(input_dir.glob("*.json"))
    if not roi_files:
        logger.warning(f"No JSON files found in {input_dir}")
        return 0

    logger.info(f"Found {len(roi_files)} ROI files to process")

    # Process results
    all_results = []
    processing_log = {
        'timestamp': str(np.datetime64('now')),
        'input_dir': str(input_dir),
        'output_dir': str(output_dir),
        'kernel_sizes': kernel_sizes,
        'tr': args.tr,
        'seed': args.seed,
        'files_processed': 0,
        'files_failed': 0,
        'results': []
    }

    for kernel_size in kernel_sizes:
        log_split(f"Processing kernel {kernel_size}s")

        for roi_file in roi_files:
            result = process_single_roi_file(
                roi_file,
                output_dir,
                kernel_size,
                args.tr
            )
            all_results.append(result)
            processing_log['results'].append(result)

            if result['success']:
                processing_log['files_processed'] += 1
            else:
                processing_log['files_failed'] += 1

    # Save processing log
    log_path = Path(args.log_file) if args.log_file else output_dir / 'temporal_smoothing_log.json'
    with open(log_path, 'w') as f:
        json.dump(processing_log, f, indent=2)

    logger.info(f"Processing complete. Log saved to {log_path}")
    logger.info(f"Successful: {processing_log['files_processed']}, Failed: {processing_log['files_failed']}")

    return 0 if processing_log['files_failed'] == 0 else 1


if __name__ == '__main__':
    sys.exit(main())