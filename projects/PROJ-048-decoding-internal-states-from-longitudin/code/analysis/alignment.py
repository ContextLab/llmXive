import logging
import numpy as np
import json
from pathlib import Path
from typing import Dict, Any, Tuple, List, Optional

from utils.logger import get_logger, log_stage_start, log_stage_end, log_memory_usage
from config import get_config_value

logger = get_logger(__name__)


class AlignmentError(Exception):
    """Custom exception for alignment-related errors."""
    pass


def align_timestamps(
    imaging_ts: np.ndarray,
    behavior_ts: np.ndarray,
    method: str = "nearest"
) -> np.ndarray:
    """
    Align behavior timestamps to the nearest imaging timestamp.

    Args:
        imaging_ts: 1D array of imaging frame timestamps (seconds).
        behavior_ts: 1D array of behavior event timestamps (seconds).
        method: Alignment method (currently only 'nearest' supported).

    Returns:
        Array of aligned indices corresponding to imaging frames.
    """
    if len(imaging_ts) == 0:
        raise AlignmentError("Imaging timestamps array is empty.")
    if len(behavior_ts) == 0:
        raise AlignmentError("Behavior timestamps array is empty.")

    if method != "nearest":
        raise AlignmentError(f"Alignment method '{method}' not implemented.")

    # Find the index of the nearest imaging frame for each behavior timestamp
    # broadcasting for efficiency
    diff = np.abs(imaging_ts[:, np.newaxis] - behavior_ts[np.newaxis, :])
    aligned_indices = np.argmin(diff, axis=0)

    return aligned_indices


def calculate_alignment_error(
    original_indices: np.ndarray,
    reconstructed_indices: np.ndarray,
    frame_rate: float = 30.0
) -> Dict[str, Any]:
    """
    Calculate the alignment error metric and validate against the threshold.

    Args:
        original_indices: Ground truth indices of behavior events in imaging frames.
        reconstructed_indices: Indices predicted by the alignment algorithm.
        frame_rate: Sampling rate of the imaging data in Hz (frames per second).

    Returns:
        Dictionary containing error metrics and validation status.
    """
    if len(original_indices) != len(reconstructed_indices):
        raise AlignmentError(
            f"Index length mismatch: original={len(original_indices)}, "
            f"reconstructed={len(reconstructed_indices)}"
        )

    # Calculate frame difference
    frame_diff = np.abs(original_indices.astype(float) - reconstructed_indices.astype(float))

    # Calculate statistics
    max_error_frames = int(np.max(frame_diff))
    mean_error_frames = float(np.mean(frame_diff))
    median_error_frames = float(np.median(frame_diff))

    # Convert to time (seconds)
    max_error_seconds = max_error_frames / frame_rate
    mean_error_seconds = mean_error_frames / frame_rate
    median_error_seconds = median_error_frames / frame_rate

    # SC-005 Threshold: <= 1 frame
    threshold_frames = 1
    is_valid = max_error_frames <= threshold_frames

    result = {
        "max_error_frames": max_error_frames,
        "mean_error_frames": mean_error_frames,
        "median_error_frames": median_error_frames,
        "max_error_seconds": max_error_seconds,
        "mean_error_seconds": mean_error_seconds,
        "median_error_seconds": median_error_seconds,
        "threshold_frames": threshold_frames,
        "frame_rate_hz": frame_rate,
        "is_valid": is_valid,
        "status": "PASS" if is_valid else "FAIL"
    }

    if not is_valid:
        error_msg = (
            f"Alignment error validation FAILED (SC-005). "
            f"Max error: {max_error_frames} frames (limit: {threshold_frames}). "
            f"Mean error: {mean_error_frames:.2f} frames."
        )
        logger.error(error_msg)
        raise AlignmentError(error_msg)

    logger.info(f"Alignment error validation PASSED (SC-005). Max error: {max_error_frames} frames.")
    return result


def run_alignment(
    imaging_data_path: Path,
    behavior_data_path: Path,
    output_path: Path,
    frame_rate: Optional[float] = None
) -> Dict[str, Any]:
    """
    Main execution function to load data, align timestamps, and validate error.

    Args:
        imaging_data_path: Path to file containing imaging timestamps.
        behavior_data_path: Path to file containing behavior timestamps.
        output_path: Path to write the alignment report (JSON).
        frame_rate: Imaging frame rate. If None, attempts to read from config.

    Returns:
        Dictionary containing the alignment report.
    """
    log_stage_start(logger, "Alignment and Validation", {
        "imaging_path": str(imaging_data_path),
        "behavior_path": str(behavior_data_path)
    })

    # Load data
    # Assuming HDF5 or NumPy format as per project conventions
    try:
        if imaging_data_path.suffix == '.npy':
            imaging_ts = np.load(imaging_data_path)
        elif imaging_data_path.suffix == '.h5' or imaging_data_path.suffix == '.hdf5':
            import h5py
            with h5py.File(imaging_data_path, 'r') as f:
                imaging_ts = np.array(f['timestamps'])
        else:
            raise AlignmentError(f"Unsupported imaging data format: {imaging_data_path.suffix}")

        if behavior_data_path.suffix == '.npy':
            behavior_ts = np.load(behavior_data_path)
        elif behavior_data_path.suffix == '.h5' or behavior_data_path.suffix == '.hdf5':
            import h5py
            with h5py.File(behavior_data_path, 'r') as f:
                behavior_ts = np.array(f['timestamps'])
        else:
            raise AlignmentError(f"Unsupported behavior data format: {behavior_data_path.suffix}")

    except Exception as e:
        raise AlignmentError(f"Failed to load timestamp data: {e}")

    if frame_rate is None:
        # Try to get from config, default to 30Hz if not found
        frame_rate = get_config_value("FRAME_RATE", 30.0)

    logger.info(f"Loaded {len(imaging_ts)} imaging frames and {len(behavior_ts)} behavior events.")
    logger.info(f"Using frame rate: {frame_rate} Hz")

    # Perform alignment
    aligned_indices = align_timestamps(imaging_ts, behavior_ts)

    # For validation, we assume the 'original_indices' are the ground truth.
    # In a real scenario, these might be derived from a known ground truth file
    # or the behavior timestamps themselves mapped directly.
    # Here, we simulate the validation by checking the consistency of the alignment
    # against a hypothetical ground truth or by checking the max drift if
    # the behavior timestamps were re-sampled.
    #
    # To satisfy T027 strictly: We calculate the error against a 'reconstructed' set.
    # Since T026 produces the alignment, we treat the direct nearest-neighbor mapping
    # as the 'reconstructed' and compare it to a 'ground truth' if available.
    # If no ground truth is explicitly provided in the task context, we perform
    # a self-consistency check or assume the input indices are the ground truth
    # for the purpose of the error metric calculation (e.g., if behavior was
    # originally downsampled from imaging).
    #
    # However, the task asks to validate against a threshold.
    # We will assume `behavior_ts` was originally sampled at the imaging rate
    # or we have a ground truth mapping.
    #
    # Let's assume the 'original_indices' are the indices if we had sampled behavior
    # perfectly at the imaging rate. Since we don't have that here, we will
    # generate a synthetic ground truth for the sake of the script execution
    # IF the task implies a comparison between two alignment methods.
    #
    # Re-reading T027: "Calculate alignment error metric and validate against <= 1 frame threshold".
    # This implies we have a 'true' alignment and a 'predicted' alignment.
    # T026 produces the alignment.
    #
    # To make this runnable without external ground truth files not yet defined:
    # We will assume the 'behavior_ts' provided are the ground truth events.
    # We align them to imaging.
    # Then we reconstruct the timestamps from the indices and measure the error.
    # This measures the quantization error of the alignment.

    # Reconstruct timestamps from indices
    reconstructed_ts = imaging_ts[aligned_indices]

    # Calculate error in frames (difference between original behavior time and reconstructed time, converted to frames)
    # Original behavior time in frames = behavior_ts * frame_rate
    # Reconstructed behavior time in frames = aligned_indices
    # This is slightly different. The error is how many frames off we are from the true event.
    # True event frame = behavior_ts * frame_rate
    # Aligned frame = aligned_indices
    # Error = |True event frame - Aligned frame|

    true_event_frames = behavior_ts * frame_rate
    error_frames = np.abs(true_event_frames - aligned_indices)

    # Calculate metrics
    max_error_frames = int(np.max(error_frames))
    mean_error_frames = float(np.mean(error_frames))
    median_error_frames = float(np.median(error_frames))

    threshold_frames = 1
    is_valid = max_error_frames <= threshold_frames

    report = {
        "max_error_frames": max_error_frames,
        "mean_error_frames": mean_error_frames,
        "median_error_frames": median_error_frames,
        "threshold_frames": threshold_frames,
        "frame_rate_hz": frame_rate,
        "is_valid": is_valid,
        "status": "PASS" if is_valid else "FAIL",
        "num_events": len(behavior_ts)
    }

    if not is_valid:
        error_msg = (
            f"Alignment error validation FAILED (SC-005). "
            f"Max error: {max_error_frames} frames (limit: {threshold_frames}). "
            f"Mean error: {mean_error_frames:.2f} frames."
        )
        logger.error(error_msg)
        raise AlignmentError(error_msg)

    logger.info(f"Alignment error validation PASSED (SC-005). Max error: {max_error_frames} frames.")

    # Write report
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2)

    log_stage_end(logger, "Alignment and Validation", report)
    return report


def main():
    """Entry point for the alignment script."""
    import sys
    from config import get_config_value

    # Get paths from config or args
    # Defaulting to expected paths in the project structure
    base_dir = Path(__file__).resolve().parent.parent
    data_dir = base_dir / "data"
    results_dir = base_dir / "results"

    # Expecting preprocessed data or specific alignment inputs
    # For T027, we assume T026 has produced intermediate files or we run the alignment again
    # to validate.
    # We will look for standard output files from previous stages.
    imaging_ts_path = data_dir / "imaging_timestamps.npy"
    behavior_ts_path = data_dir / "behavior_timestamps.npy"
    output_report_path = results_dir / "alignment_validation_report.json"

    # Check if files exist, if not, try to find them or error out
    if not imaging_ts_path.exists():
        # Fallback or error
        logger.warning(f"Imaging timestamps not found at {imaging_ts_path}. "
                       "Attempting to use defaults or exit.")
        # In a real pipeline, this would be an error.
        # For the script to be runnable, we might need to generate minimal test data
        # or rely on the user providing it.
        # Given the constraint "Fail loudly", we raise an error if data is missing.
        raise FileNotFoundError(f"Required imaging timestamps file not found: {imaging_ts_path}")

    if not behavior_ts_path.exists():
        raise FileNotFoundError(f"Required behavior timestamps file not found: {behavior_ts_path}")

    try:
        run_alignment(imaging_ts_path, behavior_ts_path, output_report_path)
        print(f"Alignment validation complete. Report saved to {output_report_path}")
    except AlignmentError as e:
        print(f"Alignment validation failed: {e}")
        sys.exit(1)
    except Exception as e:
        logger.exception("Unexpected error during alignment validation")
        sys.exit(1)


if __name__ == "__main__":
    main()