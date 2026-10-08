"""
Motion parameter extraction from fMRIPrep output.

Extracts rigid-body motion parameters (translations and rotations) from
fMRIPrep confounds TSV files and aggregates them into a single CSV file.

Output format: CSV with columns:
- subject_id
- translation_x, translation_y, translation_z
- rotation_x, rotation_y, rotation_z

The script reads from data/processed/<dataset_id>/sub-<id>/func/
and writes to data/processed/motion_parameters.csv
"""

import os
import csv
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional

import pandas as pd
from src.config.env import get_data_dir

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class MotionExtractionError(Exception):
    """Custom exception for motion extraction failures."""
    pass


def find_fmriprep_confounds(
    data_dir: Optional[Path] = None,
    dataset_id: Optional[str] = None
) -> List[Path]:
    """
    Find all fMRIPrep confounds TSV files in the processed data directory.

    Args:
        data_dir: Base data directory. If None, uses get_data_dir().
        dataset_id: Optional specific dataset ID to filter by.

    Returns:
        List of paths to confounds TSV files.

    Raises:
        MotionExtractionError: If no confounds files are found.
    """
    if data_dir is None:
        data_dir = Path(get_data_dir())

    processed_dir = data_dir / "processed"

    if not processed_dir.exists():
        raise MotionExtractionError(
            f"Processed data directory not found: {processed_dir}"
        )

    # Search for confounds files matching fMRIPrep naming convention
    # Pattern: sub-<label>/func/*confounds*.tsv
    confounds_files = []

    for tsv_path in processed_dir.rglob("sub-*/func/*confounds*.tsv"):
        # Filter to only the main motion confounds file (typically
        # *confounds_regressors.tsv or *confounds_timeseries.tsv)
        filename = tsv_path.name
        if "confounds" in filename and not "confounds_bold" in filename:
            # Prefer the most standard fMRIPrep output
            if "regressors" in filename or "timeseries" in filename:
                confounds_files.append(tsv_path)

    if not confounds_files:
        raise MotionExtractionError(
            f"No fMRIPrep confounds files found in {processed_dir}. "
            "Ensure fMRIPrep has been run and output exists."
        )

    logger.info(f"Found {len(confounds_files)} confounds files")
    return confounds_files


def extract_subject_id_from_path(file_path: Path) -> str:
    """
    Extract subject ID from a file path.

    Args:
        file_path: Path to the confounds file.

    Returns:
        Subject ID string (e.g., 'sub-001').
    """
    # Look for sub-<label> in the path
    parts = file_path.parts
    for part in parts:
        if part.startswith("sub-"):
            return part

    # Fallback: extract from filename
    stem = file_path.stem
    if stem.startswith("sub-"):
        return stem.split("_")[0]

    raise MotionExtractionError(
        f"Could not extract subject ID from path: {file_path}"
    )


def extract_motion_parameters(confounds_path: Path) -> Dict[str, Any]:
    """
    Extract motion parameters from a single fMRIPrep confounds file.

    fMRIPrep typically outputs:
    - trans_x, trans_y, trans_z (translations in mm)
    - rot_x, rot_y, rot_z (rotations in radians)

    Args:
        confounds_path: Path to the confounds TSV file.

    Returns:
        Dictionary with subject_id and motion parameters.
        If multiple volumes exist, returns the mean motion per parameter.

    Raises:
        MotionExtractionError: If required columns are missing.
    """
    try:
        df = pd.read_csv(confounds_path, sep='\t', low_memory=False)
    except Exception as e:
        raise MotionExtractionError(
            f"Failed to read confounds file {confounds_path}: {e}"
        )

    subject_id = extract_subject_id_from_path(confounds_path)

    # Map fMRIPrep column names to our standard names
    # fMRIPrep uses: trans_x, trans_y, trans_z, rot_x, rot_y, rot_z
    required_cols = {
        'translation_x': ['trans_x'],
        'translation_y': ['trans_y'],
        'translation_z': ['trans_z'],
        'rotation_x': ['rot_x'],
        'rotation_y': ['rot_y'],
        'rotation_z': ['rot_z'],
    }

    extracted_values = {}

    for target_name, possible_names in required_cols.items():
        found_col = None
        for name in possible_names:
            if name in df.columns:
                found_col = name
                break

        if found_col is None:
            raise MotionExtractionError(
                f"Could not find motion column for {target_name} in {confounds_path}. "
                f"Looked for: {possible_names}. Available columns: {list(df.columns)[:20]}..."
            )

        # Calculate mean absolute motion across all volumes
        # This gives a single summary value per parameter per subject
        values = df[found_col].dropna()
        if len(values) == 0:
            logger.warning(f"No valid values for {target_name} in {subject_id}")
            extracted_values[target_name] = 0.0
        else:
            # Use mean absolute displacement for robustness
            extracted_values[target_name] = float(values.abs().mean())

    extracted_values['subject_id'] = subject_id

    return extracted_values


def extract_all_motion_parameters(
    confounds_files: Optional[List[Path]] = None,
    data_dir: Optional[Path] = None,
    dataset_id: Optional[str] = None
) -> pd.DataFrame:
    """
    Extract motion parameters from all fMRIPrep confounds files.

    Args:
        confounds_files: Optional list of confounds files to process.
        data_dir: Base data directory.
        dataset_id: Optional dataset ID filter.

    Returns:
        DataFrame with motion parameters for all subjects.

    Raises:
        MotionExtractionError: If extraction fails for any file.
    """
    if confounds_files is None:
        confounds_files = find_fmriprep_confounds(data_dir, dataset_id)

    results = []
    errors = []

    for confounds_path in confounds_files:
        try:
            motion_data = extract_motion_parameters(confounds_path)
            results.append(motion_data)
        except MotionExtractionError as e:
            logger.error(f"Error processing {confounds_path}: {e}")
            errors.append({"file": str(confounds_path), "error": str(e)})
        except Exception as e:
            logger.error(f"Unexpected error processing {confounds_path}: {e}")
            errors.append({"file": str(confounds_path), "error": str(e)})

    if errors:
        logger.warning(f"Failed to process {len(errors)} files")
        for err in errors:
            logger.warning(f"  {err['file']}: {err['error']}")

    if not results:
        raise MotionExtractionError(
            "No motion parameters were successfully extracted from any confounds file."
        )

    df = pd.DataFrame(results)

    # Ensure consistent column order
    columns = ['subject_id', 'translation_x', 'translation_y', 'translation_z',
               'rotation_x', 'rotation_y', 'rotation_z']
    df = df[columns]

    logger.info(f"Successfully extracted motion for {len(df)} subjects")
    return df


def write_motion_csv(df: pd.DataFrame, output_path: Path) -> None:
    """
    Write motion parameters to a CSV file.

    Args:
        df: DataFrame with motion parameters.
        output_path: Path to output CSV file.
    """
    # Ensure parent directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    df.to_csv(output_path, index=False)
    logger.info(f"Wrote motion parameters to {output_path}")


def run_motion_extraction(
    output_path: Optional[Path] = None,
    data_dir: Optional[Path] = None,
    dataset_id: Optional[str] = None
) -> Path:
    """
    Main entry point for motion parameter extraction.

    Finds all fMRIPrep confounds files, extracts motion parameters,
    and writes the results to a CSV file.

    Args:
        output_path: Optional output path. If None, uses data/processed/motion_parameters.csv.
        data_dir: Base data directory.
        dataset_id: Optional dataset ID filter.

    Returns:
        Path to the output CSV file.
    """
    if output_path is None:
        if data_dir is None:
            data_dir = Path(get_data_dir())
        output_path = data_dir / "processed" / "motion_parameters.csv"

    logger.info(f"Starting motion extraction, output: {output_path}")

    confounds_files = find_fmriprep_confounds(data_dir, dataset_id)
    motion_df = extract_all_motion_parameters(confounds_files, data_dir, dataset_id)
    write_motion_csv(motion_df, output_path)

    return output_path


def main() -> None:
    """CLI entry point for motion extraction."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Extract motion parameters from fMRIPrep output"
    )
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="Output CSV path (default: data/processed/motion_parameters.csv)"
    )
    parser.add_argument(
        "--data-dir",
        type=str,
        default=None,
        help="Base data directory (default: from env)"
    )
    parser.add_argument(
        "--dataset",
        type=str,
        default=None,
        help="Optional dataset ID to filter"
    )

    args = parser.parse_args()

    output_path = Path(args.output) if args.output else None
    data_dir = Path(args.data_dir) if args.data_dir else None

    try:
        result_path = run_motion_extraction(
            output_path=output_path,
            data_dir=data_dir,
            dataset_id=args.dataset
        )
        print(f"Motion extraction complete. Output: {result_path}")
    except MotionExtractionError as e:
        logger.error(f"Motion extraction failed: {e}")
        raise SystemExit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise


if __name__ == "__main__":
    main()
