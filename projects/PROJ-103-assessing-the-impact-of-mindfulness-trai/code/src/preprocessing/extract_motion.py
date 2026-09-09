"""
Motion parameter extraction from fMRIPrep output.

Extracts 6 rigid-body motion parameters (3 translations, 3 rotations)
from fMRIPrep confounds files and writes them to a CSV summary.
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
    """Custom exception for motion extraction failures."""
    pass


def find_fmriprep_confounds(
    processed_dir: Optional[Path] = None
) -> List[Path]:
    """
    Locate all fMRIPrep confounds TSV files in the processed directory.

    fMRIPrep typically outputs files named:
    sub-<label>_task-<label>_desc-confounds_timeseries.tsv

    Args:
        processed_dir: Path to the processed data directory.
                       If None, uses data/processed/ from config.

    Returns:
        List of Path objects pointing to confounds TSV files.

    Raises:
        MotionExtractionError: If the processed directory does not exist.
    """
    if processed_dir is None:
        data_root = get_data_dir()
        processed_dir = data_root / "processed"

    if not processed_dir.exists():
        raise MotionExtractionError(
            f"Processed directory does not exist: {processed_dir}"
        )

    # Search recursively for confounds files
    pattern = "*desc-confounds_timeseries.tsv"
    confounds_files = list(processed_dir.rglob(pattern))

    if not confounds_files:
        logger.warning(
            f"No confounds files found matching '{pattern}' in {processed_dir}"
        )

    return confounds_files


def extract_subject_id_from_path(file_path: Path) -> str:
    """
    Extract the subject ID from a fMRIPrep file path.

    Expected format: .../sub-<label>/...
    Returns the <label> part.

    Args:
        file_path: Path to the fMRIPrep output file.

    Returns:
        Subject ID string.
    """
    # Look for 'sub-' pattern in the path parts
    for part in file_path.parts:
        if part.startswith("sub-"):
            return part.replace("sub-", "")
    
    # Fallback: use the directory name if pattern not found
    logger.warning(
        f"Could not extract subject ID from path: {file_path}. Using directory name."
    )
    return file_path.parent.name


def extract_motion_parameters(confounds_path: Path) -> Optional[Dict[str, float]]:
    """
    Extract the 6 rigid-body motion parameters from a single confounds file.

    fMRIPrep provides:
    - trans_x, trans_y, trans_z (translation in mm)
    - rot_x, rot_y, rot_z (rotation in radians)

    We compute the mean absolute displacement across all volumes for each parameter.

    Args:
        confounds_path: Path to the confounds TSV file.

    Returns:
        Dictionary with keys:
            subject_id, translation_x, translation_y, translation_z,
            rotation_x, rotation_y, rotation_z
        Values are the mean absolute values of the motion parameters.
        Returns None if extraction fails.
    """
    try:
        # Load the confounds file
        df = pd.read_csv(confounds_path, sep='\t', low_memory=False)
        
        required_columns = [
            'trans_x', 'trans_y', 'trans_z',
            'rot_x', 'rot_y', 'rot_z'
        ]
        
        # Check if all required columns exist
        missing = [col for col in required_columns if col not in df.columns]
        if missing:
            logger.warning(
                f"Missing columns in {confounds_path}: {missing}. "
                "Skipping this file."
            )
            return None

        # Extract subject ID
        subject_id = extract_subject_id_from_path(confounds_path)

        # Calculate mean absolute motion for each parameter
        # (absolute value to capture total displacement regardless of direction)
        motion_data = {
            'subject_id': subject_id,
            'translation_x': float(df['trans_x'].abs().mean()),
            'translation_y': float(df['trans_y'].abs().mean()),
            'translation_z': float(df['trans_z'].abs().mean()),
            'rotation_x': float(df['rot_x'].abs().mean()),
            'rotation_y': float(df['rot_y'].abs().mean()),
            'rotation_z': float(df['rot_z'].abs().mean()),
        }

        return motion_data

    except Exception as e:
        logger.error(
            f"Failed to extract motion parameters from {confounds_path}: {e}"
        )
        return None


def extract_all_motion_parameters(
    confounds_files: Optional[List[Path]] = None
) -> List[Dict[str, Any]]:
    """
    Extract motion parameters from all fMRIPrep confounds files.

    Args:
        confounds_files: List of confounds file paths.
                         If None, searches the default processed directory.

    Returns:
        List of dictionaries containing motion parameters for each subject.
    """
    if confounds_files is None:
        confounds_files = find_fmriprep_confounds()

    results = []
    for confounds_path in confounds_files:
        motion_data = extract_motion_parameters(confounds_path)
        if motion_data is not None:
            results.append(motion_data)
            logger.info(
                f"Extracted motion parameters for subject: {motion_data['subject_id']}"
            )

    logger.info(f"Successfully extracted motion for {len(results)} subjects.")
    return results


def write_motion_csv(
    motion_data: List[Dict[str, Any]],
    output_path: Optional[Path] = None
) -> Path:
    """
    Write motion parameters to a CSV file.

    Output format:
    - Columns: subject_id, translation_x, translation_y, translation_z,
               rotation_x, rotation_y, rotation_z
    - One row per subject

    Args:
        motion_data: List of motion parameter dictionaries.
        output_path: Path for the output CSV.
                     If None, uses data/results/motion_parameters.csv

    Returns:
        Path to the written CSV file.

    Raises:
        MotionExtractionError: If no data to write or write fails.
    """
    if not motion_data:
        raise MotionExtractionError(
            "No motion data provided to write. Cannot create CSV."
        )

    if output_path is None:
        data_root = get_data_dir()
        output_path = data_root / "results" / "motion_parameters.csv"
    
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        df = pd.DataFrame(motion_data)
        
        # Ensure column order
        expected_cols = [
            'subject_id', 'translation_x', 'translation_y', 'translation_z',
            'rotation_x', 'rotation_y', 'rotation_z'
        ]
        # Only include columns that exist in the data
        cols_to_write = [c for c in expected_cols if c in df.columns]
        df = df[cols_to_write]

        df.to_csv(output_path, index=False)
        logger.info(f"Motion parameters written to {output_path}")
        return output_path

    except Exception as e:
        raise MotionExtractionError(
            f"Failed to write motion CSV to {output_path}: {e}"
        )


def run_motion_extraction(
    processed_dir: Optional[Path] = None,
    output_path: Optional[Path] = None
) -> Path:
    """
    Main entry point for running the motion extraction pipeline.

    1. Finds all fMRIPrep confounds files in the processed directory.
    2. Extracts 6 rigid-body motion parameters for each subject.
    3. Writes results to a CSV file.

    Args:
        processed_dir: Path to the processed data directory.
        output_path: Path for the output CSV file.

    Returns:
        Path to the generated CSV file.
    """
    logger.info("Starting motion parameter extraction...")
    
    confounds_files = find_fmriprep_confounds(processed_dir)
    
    if not confounds_files:
        raise MotionExtractionError(
            "No fMRIPrep confounds files found. "
            "Ensure preprocessing has been run and processed_dir is correct."
        )

    motion_data = extract_all_motion_parameters(confounds_files)
    
    if not motion_data:
        raise MotionExtractionError(
            "No motion data could be extracted from the found confounds files."
        )

    output_csv = write_motion_csv(motion_data, output_path)
    
    logger.info("Motion parameter extraction completed successfully.")
    return output_csv


def main():
    """CLI entry point for motion extraction."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    try:
        output_file = run_motion_extraction()
        print(f"Motion parameters extracted to: {output_file}")
    except MotionExtractionError as e:
        logger.error(f"Motion extraction failed: {e}")
        raise SystemExit(1)
    except Exception as e:
        logger.exception(f"Unexpected error during motion extraction: {e}")
        raise SystemExit(1)


if __name__ == "__main__":
    main()
