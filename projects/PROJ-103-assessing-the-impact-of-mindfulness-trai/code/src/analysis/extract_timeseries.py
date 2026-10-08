"""
Time series extraction from MNI152 normalized BOLD images.

Extracts mean time series from DMN ROI masks for subjects that passed
motion filtering (T015).
"""
import os
import logging
import numpy as np
import nibabel as nib
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple, Union
from dataclasses import dataclass

from src.config.env import get_data_dir
from src.utils.seeding import set_seed

logger = logging.getLogger(__name__)


@dataclass
class TimeSeriesResult:
    """Container for extracted time series data."""
    subject_id: str
    time_series: np.ndarray
    roi_names: List[str]
    n_timepoints: int
    n_rois: int


class TimeSeriesExtractionError(Exception):
    """Custom exception for time series extraction failures."""
    pass


def load_roi_masks(atlas_dir: Path) -> Dict[str, np.ndarray]:
    """
    Load ROI mask files from the atlas directory.

    Args:
        atlas_dir: Path to directory containing ROI mask NIfTI files.

    Returns:
        Dictionary mapping ROI name to 3D mask array.

    Raises:
        TimeSeriesExtractionError: If no masks are found or loading fails.
    """
    if not atlas_dir.exists():
        raise TimeSeriesExtractionError(f"Atlas directory not found: {atlas_dir}")

    mask_files = list(atlas_dir.glob("*.nii.gz"))
    if not mask_files:
        raise TimeSeriesExtractionError(f"No ROI mask files found in {atlas_dir}")

    masks = {}
    for mask_file in mask_files:
        roi_name = mask_file.stem
        try:
            img = nib.load(str(mask_file))
            mask_data = img.get_fdata()
            if mask_data.ndim != 3:
                logger.warning(f"Skipping {roi_name}: expected 3D mask, got {mask_data.ndim}D")
                continue
            masks[roi_name] = mask_data
            logger.info(f"Loaded ROI mask: {roi_name} (shape: {mask_data.shape})")
        except Exception as e:
            raise TimeSeriesExtractionError(f"Failed to load mask {mask_file}: {e}")

    if not masks:
        raise TimeSeriesExtractionError("No valid ROI masks could be loaded")

    return masks


def load_bold_image(bold_path: Path) -> Tuple[np.ndarray, Tuple[int, int, int, int]]:
    """
    Load a 4D BOLD image and return data and shape.

    Args:
        bold_path: Path to the BOLD NIfTI file.

    Returns:
        Tuple of (4D data array, shape tuple).

    Raises:
        TimeSeriesExtractionError: If loading fails or dimensions are incorrect.
    """
    try:
        img = nib.load(str(bold_path))
        data = img.get_fdata()
        if data.ndim != 4:
            raise TimeSeriesExtractionError(
                f"Expected 4D BOLD image, got {data.ndim}D: {bold_path}"
            )
        return data, img.shape
    except Exception as e:
        raise TimeSeriesExtractionError(f"Failed to load BOLD image {bold_path}: {e}")


def extract_mean_timeseries(
    bold_data: np.ndarray,
    roi_mask: np.ndarray,
    roi_name: str
) -> np.ndarray:
    """
    Extract mean time series from a single ROI mask.

    Args:
        bold_data: 4D BOLD data (x, y, z, t).
        roi_mask: 3D binary mask for the ROI.
        roi_name: Name of the ROI (for logging).

    Returns:
        1D array of mean time series values.

    Raises:
        TimeSeriesExtractionError: If mask and image dimensions mismatch.
    """
    if bold_data.shape[:3] != roi_mask.shape:
        raise TimeSeriesExtractionError(
            f"Dimension mismatch for {roi_name}: "
            f"BOLD shape {bold_data.shape[:3]} vs mask shape {roi_mask.shape}"
        )

    # Create boolean mask
    mask_bool = roi_mask > 0.5

    # Check if mask has any voxels
    if not np.any(mask_bool):
        logger.warning(f"ROI {roi_name} mask is empty; returning zeros")
        return np.zeros(bold_data.shape[3])

    # Extract voxels within ROI
    roi_voxels = bold_data[mask_bool, :]

    # Compute mean across voxels for each timepoint
    mean_ts = np.mean(roi_voxels, axis=0)

    logger.debug(f"Extracted {len(mean_ts)} timepoints from {roi_name} "
                 f"using {np.sum(mask_bool)} voxels")

    return mean_ts


def extract_subject_timeseries(
    subject_id: str,
    bold_path: Path,
    roi_masks: Dict[str, np.ndarray],
    roi_order: Optional[List[str]] = None
) -> TimeSeriesResult:
    """
    Extract time series for a single subject across all ROIs.

    Args:
        subject_id: Subject identifier.
        bold_path: Path to subject's preprocessed BOLD image.
        roi_masks: Dictionary of ROI name -> mask array.
        roi_order: Optional list to enforce specific ROI ordering in output.

    Returns:
        TimeSeriesResult object with extracted data.

    Raises:
        TimeSeriesExtractionError: If extraction fails for any ROI.
    """
    if not bold_path.exists():
        raise TimeSeriesExtractionError(f"BOLD file not found: {bold_path}")

    # Load BOLD image
    bold_data, shape = load_bold_image(bold_path)
    n_timepoints = shape[3]
    logger.info(f"Processing subject {subject_id}: {n_timepoints} timepoints")

    # Determine ROI order
    if roi_order is None:
        roi_order = sorted(roi_masks.keys())
    else:
        # Validate all ROIs are present
        missing = set(roi_order) - set(roi_masks.keys())
        if missing:
            raise TimeSeriesExtractionError(
                f"ROI order contains unknown ROIs: {missing}"
            )

    # Extract time series for each ROI
    time_series_list = []
    for roi_name in roi_order:
        try:
            ts = extract_mean_timeseries(bold_data, roi_masks[roi_name], roi_name)
            time_series_list.append(ts)
        except Exception as e:
            raise TimeSeriesExtractionError(
                f"Failed to extract time series for {roi_name}: {e}"
            )

    # Stack into 2D array (n_rois, n_timepoints)
    time_series_array = np.vstack(time_series_list)

    return TimeSeriesResult(
        subject_id=subject_id,
        time_series=time_series_array,
        roi_names=roi_order,
        n_timepoints=n_timepoints,
        n_rois=len(roi_order)
    )


def find_preprocessed_bold_files(
    processed_dir: Path,
    motion_filter_csv: Optional[Path] = None
) -> List[Tuple[str, Path]]:
    """
    Find preprocessed BOLD files for subjects that passed motion filtering.

    Args:
        processed_dir: Path to processed data directory.
        motion_filter_csv: Optional path to exclusion CSV from T015.
                         If provided, only include subjects not in exclusion list.

    Returns:
        List of (subject_id, bold_path) tuples.

    Raises:
        TimeSeriesExtractionError: If no valid BOLD files are found.
    """
    # Load excluded subjects if filter CSV provided
    excluded_subjects = set()
    if motion_filter_csv and motion_filter_csv.exists():
        import csv
        with open(motion_filter_csv, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if 'subject_id' in row:
                    excluded_subjects.add(row['subject_id'].strip())
        logger.info(f"Loaded {len(excluded_subjects)} excluded subjects from {motion_filter_csv}")

    # Find BOLD files
    # Expected pattern: sub-<id>/func/sub-<id>_task-rest_space-MNI152NLin2009cAsym_desc-preproc_bold.nii.gz
    bold_files = []
    for subject_dir in sorted(processed_dir.glob("sub-*")):
        subject_id = subject_dir.name.split("_")[0] if "_" in subject_dir.name else subject_dir.name
        
        # Skip if excluded
        if subject_id in excluded_subjects:
            logger.debug(f"Skipping excluded subject: {subject_id}")
            continue

        # Look for preprocessed BOLD
        func_dir = subject_dir / "func"
        if func_dir.exists():
            # Try common preprocessed naming patterns
            patterns = [
                f"*space-MNI152*desc-preproc_bold.nii.gz",
                f"*desc-preproc_bold.nii.gz",
                f"*space-MNI152*bold.nii.gz",
            ]
            for pattern in patterns:
                matches = list(func_dir.glob(pattern))
                if matches:
                    bold_files.append((subject_id, matches[0]))
                    break

    if not bold_files:
        raise TimeSeriesExtractionError(
            f"No preprocessed BOLD files found in {processed_dir} "
            f"(after filtering {len(excluded_subjects)} excluded subjects)"
        )

    logger.info(f"Found {len(bold_files)} valid BOLD files for time series extraction")
    return bold_files


def extract_all_timeseries(
    atlas_dir: Path,
    processed_dir: Path,
    motion_filter_csv: Optional[Path] = None,
    output_dir: Optional[Path] = None,
    roi_order: Optional[List[str]] = None
) -> List[TimeSeriesResult]:
    """
    Main entry point: extract time series for all valid subjects.

    Args:
        atlas_dir: Path to directory containing ROI mask files.
        processed_dir: Path to preprocessed BOLD data directory.
        motion_filter_csv: Optional path to motion filter exclusion CSV.
        output_dir: Optional directory to save .npz output files.
        roi_order: Optional list to enforce specific ROI ordering.

    Returns:
        List of TimeSeriesResult objects for each subject.

    Raises:
        TimeSeriesExtractionError: If extraction fails.
    """
    # Load ROI masks
    roi_masks = load_roi_masks(atlas_dir)
    roi_names = list(roi_masks.keys())
    if roi_order is None:
        roi_order = sorted(roi_names)

    logger.info(f"Using {len(roi_masks)} ROIs: {roi_order}")

    # Find valid BOLD files
    bold_files = find_preprocessed_bold_files(processed_dir, motion_filter_csv)

    # Extract time series for each subject
    results = []
    for subject_id, bold_path in bold_files:
        try:
            result = extract_subject_timeseries(
                subject_id, bold_path, roi_masks, roi_order
            )
            results.append(result)

            # Save to output if requested
            if output_dir:
                output_dir.mkdir(parents=True, exist_ok=True)
                output_path = output_dir / f"timeseries_{subject_id}.npz"
                np.savez(
                    str(output_path),
                    time_series=result.time_series,
                    roi_names=np.array(result.roi_names),
                    subject_id=subject_id
                )
                logger.info(f"Saved time series to {output_path}")

        except TimeSeriesExtractionError as e:
            logger.error(f"Failed to extract timeseries for {subject_id}: {e}")
            raise

    logger.info(f"Successfully extracted time series for {len(results)} subjects")
    return results


def run_timeseries_extraction(
    atlas_dir: Optional[Path] = None,
    processed_dir: Optional[Path] = None,
    motion_filter_csv: Optional[Path] = None,
    output_dir: Optional[Path] = None
) -> List[TimeSeriesResult]:
    """
    Run time series extraction with configuration from environment.

    Args:
        atlas_dir: Path to atlas (defaults to data/processed/atlas).
        processed_dir: Path to processed data (defaults to data/processed).
        motion_filter_csv: Path to motion filter CSV (defaults to data/processed/excluded_subjects.csv).
        output_dir: Path to output directory (defaults to data/processed/timeseries).

    Returns:
        List of TimeSeriesResult objects.
    """
    data_root = Path(get_data_dir())

    if atlas_dir is None:
        atlas_dir = data_root / "processed" / "atlas"
    if processed_dir is None:
        processed_dir = data_root / "processed"
    if motion_filter_csv is None:
        motion_filter_csv = data_root / "processed" / "excluded_subjects.csv"
    if output_dir is None:
        output_dir = data_root / "processed" / "timeseries"

    # Ensure output directory exists
    output_dir.mkdir(parents=True, exist_ok=True)

    # Set seed for reproducibility
    set_seed()

    logger.info("Starting time series extraction...")
    logger.info(f"Atlas directory: {atlas_dir}")
    logger.info(f"Processed directory: {processed_dir}")
    logger.info(f"Motion filter CSV: {motion_filter_csv}")
    logger.info(f"Output directory: {output_dir}")

    results = extract_all_timeseries(
        atlas_dir=atlas_dir,
        processed_dir=processed_dir,
        motion_filter_csv=motion_filter_csv,
        output_dir=output_dir
    )

    # Save summary metadata
    summary_path = output_dir / "timeseries_metadata.json"
    import json
    summary = {
        "n_subjects": len(results),
        "roi_names": results[0].roi_names if results else [],
        "subjects": [
            {
                "subject_id": r.subject_id,
                "n_timepoints": r.n_timepoints,
                "n_rois": r.n_rois
            }
            for r in results
        ]
    }
    with open(summary_path, 'w') as f:
        json.dump(summary, f, indent=2)
    logger.info(f"Saved metadata to {summary_path}")

    return results


def main():
    """Command-line entry point."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Extract mean time series from DMN ROIs for preprocessed BOLD images."
    )
    parser.add_argument(
        "--atlas-dir", type=str, default=None,
        help="Path to ROI mask directory (default: data/processed/atlas)"
    )
    parser.add_argument(
        "--processed-dir", type=str, default=None,
        help="Path to preprocessed BOLD directory (default: data/processed)"
    )
    parser.add_argument(
        "--motion-filter-csv", type=str, default=None,
        help="Path to motion filter exclusion CSV (default: data/processed/excluded_subjects.csv)"
    )
    parser.add_argument(
        "--output-dir", type=str, default=None,
        help="Path to output directory (default: data/processed/timeseries)"
    )
    parser.add_argument(
        "--verbose", action="store_true",
        help="Enable verbose logging"
    )

    args = parser.parse_args()

    # Configure logging
    log_level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    # Parse paths
    atlas_dir = Path(args.atlas_dir) if args.atlas_dir else None
    processed_dir = Path(args.processed_dir) if args.processed_dir else None
    motion_filter_csv = Path(args.motion_filter_csv) if args.motion_filter_csv else None
    output_dir = Path(args.output_dir) if args.output_dir else None

    try:
        results = run_timeseries_extraction(
            atlas_dir=atlas_dir,
            processed_dir=processed_dir,
            motion_filter_csv=motion_filter_csv,
            output_dir=output_dir
        )
        logger.info(f"Extraction complete. Processed {len(results)} subjects.")
    except TimeSeriesExtractionError as e:
        logger.error(f"Time series extraction failed: {e}")
        raise


if __name__ == "__main__":
    main()
