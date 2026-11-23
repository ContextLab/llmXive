"""
Temporal Smoothing Module for fMRI ROI Time-Series.

This module implements temporal smoothing kernels on 1D ROI time-series data.
It serves as a CPU-tractable substitute for the spatial smoothing typically
performed in fMRIPrep, adapted for the temporal dimension as required by
FR-002 (adapted).

Algorithm: Gaussian kernel with Full Width at Half Maximum (FWHM).
Sigma calculation: sigma = FWHM / (2 * sqrt(2 * ln(2)))
Boundary handling: 'reflect' mode.

Mapping:
  - 4mm spatial [deferred] -> 4s temporal (TR=2s, kernel_size=2 samples)
  - 8mm spatial [deferred] -> 8s temporal (TR=2s, kernel_size=4 samples)
"""

import argparse
import json
import logging
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any, Union

import numpy as np
from scipy.ndimage import gaussian_filter1d

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

# Constants
DEFAULT_TR = 2.0  # Default repetition time in seconds
DEFAULT_KERNEL_FWHM = 4.0  # Default FWHM in seconds (maps to 4s temporal)
DEFAULT_MODE = 'temporal'

def compute_sigma(fwhm_seconds: float, tr_seconds: float = DEFAULT_TR) -> float:
    """
    Calculate the standard deviation (sigma) for a Gaussian kernel given FWHM.

    Formula: sigma = FWHM / (2 * sqrt(2 * ln(2)))
    The result is in seconds, which must be converted to samples based on TR.

    Args:
        fwhm_seconds: Full Width at Half Maximum in seconds.
        tr_seconds: Repetition time in seconds.

    Returns:
        Sigma in units of samples.
    """
    if fwhm_seconds <= 0:
        raise ValueError("FWHM must be positive.")
    if tr_seconds <= 0:
        raise ValueError("TR must be positive.")

    # Sigma in seconds
    sigma_seconds = fwhm_seconds / (2 * np.sqrt(2 * np.log(2)))
    # Convert to samples
    sigma_samples = sigma_seconds / tr_seconds
    return sigma_samples


def apply_temporal_smoothing(
    time_series: np.ndarray,
    kernel_fwhm_seconds: float,
    tr_seconds: float = DEFAULT_TR,
    mode: str = 'temporal',
    reflect_threshold: Optional[float] = None
) -> np.ndarray:
    """
    Apply temporal smoothing to a 1D ROI time-series using a Gaussian kernel.

    This is a CPU-tractable substitute for fMRIPrep's spatial smoothing,
    adapted for the temporal dimension.

    Args:
        time_series: 1D numpy array of ROI time-series data.
        kernel_fwhm_seconds: Full Width at Half Maximum of the Gaussian kernel in seconds.
        tr_seconds: Repetition time in seconds.
        mode: Smoothing mode. Only 'temporal' is supported here as per task requirements.
              The 'spatial' mode is deferred to spatial_smoothing.py.
        reflect_threshold: Threshold for reflect mode boundary handling (passed to scipy).

    Returns:
        Smoothed 1D numpy array.

    Raises:
        ValueError: If mode is not 'temporal' or inputs are invalid.
        TypeError: If time_series is not a numpy array.
    """
    if mode != 'temporal':
        raise ValueError(
            f"Invalid mode '{mode}'. This function only supports 'temporal' mode. "
            "For spatial smoothing, use code/preprocess/spatial_smoothing.py."
        )

    if not isinstance(time_series, np.ndarray):
        raise TypeError("time_series must be a numpy array.")

    if time_series.ndim != 1:
        raise ValueError(f"time_series must be 1D, got {time_series.ndim}D.")

    if kernel_fwhm_seconds <= 0:
        raise ValueError("kernel_fwhm_seconds must be positive.")

    # Calculate sigma in samples
    sigma_samples = compute_sigma(kernel_fwhm_seconds, tr_seconds)

    logger.debug(
        f"Applying temporal smoothing: FWHM={kernel_fwhm_seconds}s, "
        f"TR={tr_seconds}s, Sigma={sigma_samples:.2f} samples"
    )

    # Apply Gaussian smoothing with reflect boundary handling
    # scipy's gaussian_filter1d handles the kernel size calculation internally based on sigma
    smoothed_data = gaussian_filter1d(
        time_series,
        sigma=sigma_samples,
        mode='reflect',
        truncate=4.0,  # Standard truncation for Gaussian filters
        reflect_threshold=reflect_threshold
    )

    return smoothed_data


def load_roi_timeseries(roi_file_path: Path) -> Tuple[np.ndarray, Dict[str, Any]]:
    """
    Load ROI time-series data from a JSON file.

    Expected JSON structure:
    {
        "roi_name": "string",
        "time_series": [float, float, ...],
        "metadata": { ... }
    }

    Args:
        roi_file_path: Path to the JSON file containing ROI data.

    Returns:
        Tuple of (time_series_array, metadata_dict).

    Raises:
        FileNotFoundError: If the file does not exist.
        json.JSONDecodeError: If the file is not valid JSON.
        KeyError: If required fields are missing.
    """
    if not roi_file_path.exists():
        raise FileNotFoundError(f"ROI file not found: {roi_file_path}")

    with open(roi_file_path, 'r') as f:
        data = json.load(f)

    if 'time_series' not in data:
        raise KeyError(f"Missing 'time_series' key in {roi_file_path}")

    time_series = np.array(data['time_series'], dtype=np.float64)
    metadata = data.get('metadata', {})
    metadata['roi_name'] = data.get('roi_name', 'unknown')

    return time_series, metadata


def save_smoothed_timeseries(
    smoothed_data: np.ndarray,
    original_metadata: Dict[str, Any],
    output_path: Path,
  kernel_fwhm_seconds: float,
    tr_seconds: float,
    mode: str
) -> None:
    """
    Save smoothed time-series data to a JSON file.

    Args:
        smoothed_data: 1D numpy array of smoothed data.
        original_metadata: Metadata from the original data.
        output_path: Path to save the output JSON file.
        kernel_fwhm_seconds: The FWHM used for smoothing.
        tr_seconds: The TR used for smoothing.
        mode: The mode used for smoothing.
    """
    output_data = {
        "roi_name": original_metadata.get('roi_name', 'unknown'),
        "time_series": smoothed_data.tolist(),
        "metadata": {
            **original_metadata,
            "smoothing_applied": True,
            "smoothing_type": "temporal_gaussian",
            "kernel_fwhm_seconds": kernel_fwhm_seconds,
            "tr_seconds": tr_seconds,
            "mode": mode,
            "original_length": len(smoothed_data),
            "processing_timestamp": str(datetime.now())
        }
    }

    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w') as f:
        json.dump(output_data, f, indent=2)

    logger.info(f"Saved smoothed data to {output_path}")


def process_single_roi_file(
    input_path: Path,
    output_dir: Path,
    kernel_fwhm_seconds: float,
    tr_seconds: float = DEFAULT_TR,
    mode: str = 'temporal'
) -> Dict[str, Any]:
    """
    Process a single ROI file: load, smooth, and save.

    Args:
        input_path: Path to the input ROI JSON file.
        output_dir: Directory to save the smoothed output.
        kernel_fwhm_seconds: FWHM for the smoothing kernel.
        tr_seconds: Repetition time.
        mode: Smoothing mode.

    Returns:
        Dictionary with processing status and output path.
    """
    try:
        logger.info(f"Processing {input_path.name}...")

        # Load data
        time_series, metadata = load_roi_timeseries(input_path)

        # Apply smoothing
        smoothed_series = apply_temporal_smoothing(
            time_series,
            kernel_fwhm_seconds,
            tr_seconds,
            mode
        )

        # Prepare output path
        output_filename = input_path.stem + f"_smoothed_{kernel_fwhm_seconds}s.json"
        output_path = output_dir / output_filename

        # Save data
        save_smoothed_timeseries(
            smoothed_series,
            metadata,
            output_path,
            kernel_fwhm_seconds,
            tr_seconds,
            mode
        )

        return {
            "status": "success",
            "input_file": str(input_path),
            "output_file": str(output_path),
            "roi_name": metadata.get('roi_name', 'unknown'),
            "original_length": len(time_series),
            "smoothed_length": len(smoothed_series)
        }

    except Exception as e:
        logger.error(f"Failed to process {input_path}: {e}", exc_info=True)
        return {
            "status": "failed",
            "input_file": str(input_path),
            "error": str(e)
        }


def main():
    """
    Command-line interface for temporal smoothing.

    Usage:
        python -m preprocess.temporal_smoothing --input data/derived/roi_data.json --output data/derived/smoothed_roi --fwhm 4.0 --tr 2.0
    """
    parser = argparse.ArgumentParser(
        description="Apply temporal smoothing to 1D ROI time-series data."
    )
    parser.add_argument(
        "--input", "-i",
        type=Path,
        required=True,
        help="Path to input ROI JSON file or directory containing ROI JSON files."
    )
    parser.add_argument(
        "--output", "-o",
        type=Path,
        required=True,
        help="Path to output directory for smoothed data."
    )
    parser.add_argument(
        "--fwhm",
        type=float,
        default=DEFAULT_KERNEL_FWHM,
        help=f"Full Width at Half Maximum in seconds (default: {DEFAULT_KERNEL_FWHM})"
    )
    parser.add_argument(
        "--tr",
        type=float,
        default=DEFAULT_TR,
        help=f"Repetition time in seconds (default: {DEFAULT_TR})"
    )
    parser.add_argument(
        "--mode",
        type=str,
        default=DEFAULT_MODE,
        choices=['temporal'],
        help="Smoothing mode. Currently only 'temporal' is supported."
    )

    args = parser.parse_args()

    # Validate mode
    if args.mode != 'temporal':
        logger.error(f"Mode '{args.mode}' is not supported. Use 'temporal'.")
        sys.exit(1)

    logger.info(f"Starting temporal smoothing pipeline.")
    logger.info(f"Configuration: FWHM={args.fwhm}s, TR={args.tr}s, Mode={args.mode}")

    results = []

    if args.input.is_file():
        # Process single file
        result = process_single_roi_file(
            args.input,
            args.output,
            args.fwhm,
            args.tr,
            args.mode
        )
        results.append(result)
    elif args.input.is_dir():
        # Process all JSON files in directory
        json_files = list(args.input.glob("*.json"))
        if not json_files:
            logger.warning(f"No JSON files found in {args.input}")
        else:
            logger.info(f"Found {len(json_files)} ROI files to process.")
            for json_file in json_files:
                result = process_single_roi_file(
                    json_file,
                    args.output,
                    args.fwhm,
                    args.tr,
                    args.mode
                )
                results.append(result)
    else:
        logger.error(f"Input path does not exist: {args.input}")
        sys.exit(1)

    # Summary
    successful = sum(1 for r in results if r["status"] == "success")
    failed = sum(1 for r in results if r["status"] == "failed")

    logger.info(f"Processing complete. Success: {successful}, Failed: {failed}")

    if failed > 0:
        sys.exit(1)

    # Save processing log
    log_path = args.output / "smoothing_log.json"
    with open(log_path, 'w') as f:
        json.dump({
            "configuration": {
                "fwhm_seconds": args.fwhm,
                "tr_seconds": args.tr,
                "mode": args.mode
            },
            "results": results
        }, f, indent=2)

    logger.info(f"Processing log saved to {log_path}")


if __name__ == "__main__":
    main()