"""
Motion parameter extraction from fMRIPrep output.

Extracts rigid-body motion parameters (translation and rotation) from
fMRIPrep confounds TSV files and outputs a consolidated CSV.
"""
import os
import csv
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional

import pandas as pd

from src.config.env import get_data_dir

logger = logging.getLogger(__name__)


class MotionExtractionError(Exception):
    """Raised when motion parameter extraction fails."""
    pass


def find_fmriprep_confounds(
    processed_dir: Path,
    dataset_id: str
) -> List[Path]:
    """
    Find all fMRIPrep confounds TSV files for a given dataset.

    Args:
        processed_dir: Path to the processed data directory.
        dataset_id: The OpenNeuro dataset ID.

    Returns:
        List of paths to confounds TSV files.

    Raises:
        MotionExtractionError: If no confounds files are found.
    """
    # fMRIPrep output structure: sub-<label>/func/sub-<label>_task-<label>_desc-confounds_timeseries.tsv
    search_pattern = processed_dir / dataset_id / "sub-*" / "func" / "*_desc-confounds_timeseries.tsv"
    confounds_files = list(processed_dir.glob(str(search_pattern)))

    if not confounds_files:
        # Fallback: try a broader search in case structure varies slightly
        search_pattern_alt = processed_dir / dataset_id / "**" / "*_desc-confounds_timeseries.tsv"
        confounds_files = list(processed_dir.glob(str(search_pattern_alt)))

    if not confounds_files:
        raise MotionExtractionError(
            f"No fMRIPrep confounds files found in {processed_dir / dataset_id}. "
            "Ensure fMRIPrep has been run successfully."
        )

    return sorted(confounds_files)


def extract_subject_id_from_path(file_path: Path) -> str:
    """
    Extract subject ID from an fMRIPrep file path.

    Args:
        file_path: Path to the confounds file.

    Returns:
        Subject ID string (e.g., 'sub-01').
    """
    # Typical path: .../sub-01/func/...
    # We look for the 'sub-XX' directory component
    for part in file_path.parts:
        if part.startswith("sub-") and len(part) == 6: # sub-XX
            return part
    # Fallback: extract from filename if directory structure is flat
    filename = file_path.name
    if filename.startswith("sub-"):
        parts = filename.split("_")
        if parts:
            return parts[0]
    raise MotionExtractionError(f"Could not extract subject ID from {file_path}")


def extract_motion_parameters(confounds_path: Path) -> Optional[pd.DataFrame]:
    """
    Extract motion parameters from a single fMRIPrep confounds file.

    fMRIPrep typically provides:
    - trans_x, trans_y, trans_z (translation in mm)
    - rot_x, rot_y, rot_z (rotation in radians)

    Args:
        confounds_path: Path to the confounds TSV file.

    Returns:
        DataFrame with subject_id and motion parameters, or None if columns missing.
    """
    try:
        df = pd.read_csv(confounds_path, sep="\t")
    except Exception as e:
        logger.error(f"Failed to read confounds file {confounds_path}: {e}")
        return None

    # Define expected columns for rigid body motion
    trans_cols = ["trans_x", "trans_y", "trans_z"]
    rot_cols = ["rot_x", "rot_y", "rot_z"]

    # Check if columns exist (case-insensitive check for robustness)
    available_cols = set(df.columns.str.lower())
    needed_trans = {c.lower() for c in trans_cols}
    needed_rot = {c.lower() for c in rot_cols}

    if not needed_trans.issubset(available_cols) or not needed_rot.issubset(available_cols):
        logger.warning(
            f"Missing motion columns in {confounds_path}. "
            f"Found: {list(df.columns)}. Expected translations: {trans_cols}, rotations: {rot_cols}"
        )
        return None

    # Normalize column names to lowercase for consistency
    df.columns = df.columns.str.lower()

    # Select and rename columns
    motion_data = df[trans_cols + rot_cols].copy()
    motion_data.columns = ["translation_x", "translation_y", "translation_z",
                           "rotation_x", "rotation_y", "rotation_z"]

    subject_id = extract_subject_id_from_path(confounds_path)
    motion_data["subject_id"] = subject_id

    # Reorder to put subject_id first
    cols = ["subject_id"] + [c for c in motion_data.columns if c != "subject_id"]
    return motion_data[cols]


def extract_all_motion_parameters(
    processed_dir: Path,
    dataset_id: str
) -> pd.DataFrame:
    """
    Extract motion parameters from all subjects in a dataset.

    Args:
        processed_dir: Path to the processed data directory.
        dataset_id: The OpenNeuro dataset ID.

    Returns:
        Consolidated DataFrame with motion parameters for all subjects.
    """
    confounds_files = find_fmriprep_confounds(processed_dir, dataset_id)
    logger.info(f"Found {len(confounds_files)} confounds files for dataset {dataset_id}")

    all_data = []
    for file_path in confounds_files:
        try:
            motion_df = extract_motion_parameters(file_path)
            if motion_df is not None:
                all_data.append(motion_df)
        except Exception as e:
            logger.error(f"Error processing {file_path}: {e}")
            continue

    if not all_data:
        raise MotionExtractionError(
            "No motion data extracted from any confounds files. "
            "Check that fMRIPrep output contains valid motion parameters."
        )

    return pd.concat(all_data, ignore_index=True)


def write_motion_csv(dataframe: pd.DataFrame, output_path: Path) -> None:
    """
    Write motion parameters to a CSV file.

    Args:
        dataframe: DataFrame with motion parameters.
        output_path: Path to the output CSV file.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    dataframe.to_csv(output_path, index=False)
    logger.info(f"Wrote motion data to {output_path} ({len(dataframe)} rows)")


def run_motion_extraction(
    dataset_id: str,
    output_filename: str = "motion_parameters.csv"
) -> Path:
    """
    Main entry point for motion parameter extraction.

    Reads fMRIPrep confounds for the specified dataset and writes a
    consolidated CSV file.

    Args:
        dataset_id: The OpenNeuro dataset ID to process.
        output_filename: Name of the output CSV file.

    Returns:
        Path to the generated CSV file.
    """
    data_dir = Path(get_data_dir())
    processed_dir = data_dir / "processed"
    output_dir = data_dir / "results"

    logger.info(f"Starting motion extraction for dataset {dataset_id}")

    try:
        motion_df = extract_all_motion_parameters(processed_dir, dataset_id)
    except MotionExtractionError as e:
        logger.error(str(e))
        raise

    output_path = output_dir / output_filename
    write_motion_csv(motion_df, output_path)

    return output_path


def main() -> None:
    """
    Command-line entry point.

    Expects dataset_id as a command-line argument or falls back to a default
    if not provided (for testing purposes only).
    """
    import sys

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    if len(sys.argv) > 1:
        dataset_id = sys.argv[1]
    else:
        # Default for local testing if no arg provided
        # In production, this should be provided or fail
        dataset_id = "ds000001"
        logger.warning(f"No dataset ID provided. Using default: {dataset_id}")

    try:
        run_motion_extraction(dataset_id)
    except MotionExtractionError as e:
        logger.error(f"Motion extraction failed: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
