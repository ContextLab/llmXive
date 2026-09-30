"""
Motion parameter extraction from fMRIPrep output.

Extracts 6 rigid-body motion parameters (3 translations, 3 rotations)
from fMRIPrep confounds TSV files and writes them to a CSV summary.
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


def find_fmriprep_confounds(processed_dir: Path) -> List[Path]:
    """
    Find all fMRIPrep confounds TSV files in the processed directory.

    fMRIPrep typically outputs confounds in:
    <processed_dir>/sub-<label>/func/sub-<label>_task-<label>_desc-confounds_timeseries.tsv

    Args:
        processed_dir: Path to the processed data directory (data/processed/)

    Returns:
        List of paths to confounds TSV files

    Raises:
        MotionExtractionError: If no confounds files are found
    """
    confounds_files = list(processed_dir.glob("**/sub-*/func/*desc-confounds_timeseries.tsv"))

    if not confounds_files:
        # Also check for alternative naming patterns
        confounds_files = list(processed_dir.glob("**/sub-*/func/*_confounds.tsv"))

    if not confounds_files:
        raise MotionExtractionError(
            f"No fMRIPrep confounds files found in {processed_dir}. "
            "Ensure fMRIPrep has completed preprocessing and output files exist."
        )

    logger.info(f"Found {len(confounds_files)} confounds files")
    return confounds_files


def extract_subject_id_from_path(confounds_path: Path) -> str:
    """
    Extract subject ID from a confounds file path.

    Args:
        confounds_path: Path to the confounds TSV file

    Returns:
        Subject ID string (e.g., 'sub-01')
    """
    # Path typically looks like: .../sub-01/func/sub-01_task-rest_desc-confounds_timeseries.tsv
    parts = confounds_path.parts
    for i, part in enumerate(parts):
        if part.startswith("sub-"):
            return part
    # Fallback: extract from filename
    filename = confounds_path.stem
    # Handle patterns like sub-01_task-rest_desc-confounds_timeseries
    if "_" in filename:
        return filename.split("_")[0]
    return filename


def extract_motion_parameters(confounds_path: Path) -> Optional[Dict[str, Any]]:
    """
    Extract 6 rigid-body motion parameters from a single confounds file.

    fMRIPrep outputs motion parameters in columns:
    - trans_x, trans_y, trans_z (translations in mm)
    - rot_x, rot_y, rot_z (rotations in radians)

    Args:
        confounds_path: Path to the confounds TSV file

    Returns:
        Dictionary with subject_id and motion parameters (max values across time)
        or None if extraction fails
    """
    try:
        df = pd.read_csv(confounds_path, sep='\t')

        # Required motion parameter columns from fMRIPrep
        motion_columns = {
            'translation_x': 'trans_x',
            'translation_y': 'trans_y',
            'translation_z': 'trans_z',
            'rotation_x': 'rot_x',
            'rotation_y': 'rot_y',
            'rotation_z': 'rot_z'
        }

        # Check if all required columns exist
        missing_cols = [col for col, fmriprep_col in motion_columns.items()
                      if fmriprep_col not in df.columns]

        if missing_cols:
            logger.warning(
                f"Missing motion columns in {confounds_path}: {missing_cols}. "
                f"Available columns: {list(df.columns)}"
            )
            return None

        # Extract max absolute values for each motion parameter
        # This gives a summary of the maximum motion for this subject
        motion_data = {}
        for output_col, input_col in motion_columns.items():
            values = df[input_col].abs()
            motion_data[output_col] = float(values.max())

        subject_id = extract_subject_id_from_path(confounds_path)
        motion_data['subject_id'] = subject_id

        logger.info(f"Extracted motion parameters for {subject_id}")
        return motion_data

    except Exception as e:
        logger.error(f"Failed to extract motion from {confounds_path}: {e}")
        return None


def extract_all_motion_parameters(confounds_files: List[Path]) -> List[Dict[str, Any]]:
    """
    Extract motion parameters from all confounds files.

    Args:
        confounds_files: List of paths to confounds TSV files

    Returns:
        List of dictionaries, each containing subject_id and motion parameters
    """
    results = []
    for confounds_path in confounds_files:
        motion_data = extract_motion_parameters(confounds_path)
        if motion_data is not None:
            results.append(motion_data)

    if not results:
        raise MotionExtractionError(
            "No motion parameters could be extracted from any confounds files. "
            "Check that fMRIPrep output contains the required motion parameter columns."
        )

    logger.info(f"Successfully extracted motion from {len(results)} subjects")
    return results


def write_motion_csv(motion_data: List[Dict[str, Any]], output_path: Path) -> None:
    """
    Write motion parameters to a CSV file.

    Output format: CSV with columns: subject_id, translation_x/y/z, rotation_x/y/z

    Args:
        motion_data: List of dictionaries with motion parameters
        output_path: Path to output CSV file
    """
    if not motion_data:
        raise MotionExtractionError("Cannot write empty motion data to CSV")

    # Define column order
    columns = ['subject_id', 'translation_x', 'translation_y', 'translation_z',
               'rotation_x', 'rotation_y', 'rotation_z']

    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Write CSV
    with open(output_path, 'w', newline='') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=columns)
        writer.writeheader()

        for row in motion_data:
            # Ensure all columns are present (fill with 0 if missing)
            complete_row = {col: row.get(col, 0.0) for col in columns}
            writer.writerow(complete_row)

    logger.info(f"Wrote motion parameters to {output_path}")


def run_motion_extraction(
    processed_dir: Optional[Path] = None,
    output_path: Optional[Path] = None
) -> Path:
    """
    Main function to run motion parameter extraction.

    Args:
        processed_dir: Path to processed data directory (defaults to data/processed/)
        output_path: Path for output CSV (defaults to data/results/motion_parameters.csv)

    Returns:
        Path to the output CSV file
    """
    # Get data directory from environment
    data_dir = Path(get_data_dir())

    if processed_dir is None:
        processed_dir = data_dir / "processed"

    if output_path is None:
        output_path = data_dir / "results" / "motion_parameters.csv"

    logger.info(f"Starting motion extraction from {processed_dir}")

    # Find confounds files
    confounds_files = find_fmriprep_confounds(processed_dir)

    # Extract motion parameters
    motion_data = extract_all_motion_parameters(confounds_files)

    # Write output CSV
    write_motion_csv(motion_data, output_path)

    logger.info("Motion extraction completed successfully")
    return output_path


def main() -> None:
    """Entry point for command-line execution."""
    import argparse
    from src.utils.logging import setup_logging

    # Setup logging
    setup_logging()

    parser = argparse.ArgumentParser(
        description="Extract motion parameters from fMRIPrep output"
    )
    parser.add_argument(
        "--processed-dir",
        type=Path,
        default=None,
        help="Path to processed data directory (default: data/processed/)"
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Path for output CSV (default: data/results/motion_parameters.csv)"
    )

    args = parser.parse_args()

    try:
        output_path = run_motion_extraction(
            processed_dir=args.processed_dir,
            output_path=args.output
        )
        print(f"Motion parameters written to: {output_path}")
    except MotionExtractionError as e:
        logger.error(f"Motion extraction failed: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error during motion extraction: {e}")
        raise