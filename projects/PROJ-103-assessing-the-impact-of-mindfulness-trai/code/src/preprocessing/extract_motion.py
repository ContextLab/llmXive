"""
Motion parameter extraction from fMRIPrep output.

Extracts 6 rigid-body motion parameters (3 translations, 3 rotations)
from fMRIPrep confounds TSV files and outputs a CSV summary.
"""

import os
import csv
import pandas as pd
from pathlib import Path
from typing import List, Dict, Any, Optional
from src.config.env import get_data_dir


class MotionExtractionError(Exception):
    """Custom exception for motion parameter extraction failures."""
    pass


def find_fmriprep_confounds(data_root: Path) -> List[Path]:
    """
    Locate fMRIPrep confounds TSV files in the processed data directory.

    Searches for files matching the pattern:
    sub-*/func/*desc-confounds_timeseries.tsv

    Args:
        data_root: Root directory of the dataset (should contain 'processed' subdirectory)

    Returns:
        List of paths to confounds TSV files
    """
    processed_dir = data_root / "processed"
    if not processed_dir.exists():
        raise MotionExtractionError(f"Processed directory not found: {processed_dir}")

    confounds_files = list(processed_dir.glob("**/desc-confounds_timeseries.tsv"))

    if not confounds_files:
        raise MotionExtractionError(
            f"No fMRIPrep confounds files found in {processed_dir}. "
            "Ensure fMRIPrep has been run and output is in data/processed/."
        )

    return confounds_files


def extract_subject_id_from_path(file_path: Path) -> str:
    """
    Extract subject ID from a file path.

    Expected path pattern: .../sub-<subject_id>/func/...

    Args:
        file_path: Path to the confounds file

    Returns:
        Subject ID string (e.g., '01', 'sub-001')
    """
    parts = file_path.parts
    for i, part in enumerate(parts):
        if part.startswith("sub-"):
            return part
    # Fallback to directory name
    return file_path.parent.name


def extract_motion_parameters(confounds_path: Path) -> Dict[str, Any]:
    """
    Extract 6 rigid-body motion parameters from a single confounds file.

    fMRIPrep provides 6 motion parameters in the confounds file:
    - trans_x, trans_y, trans_z (translations in mm)
    - rot_x, rot_y, rot_z (rotations in radians)

    This function computes the mean absolute displacement for each parameter
    across all time points.

    Args:
        confounds_path: Path to the confounds TSV file

    Returns:
        Dictionary with subject_id and 6 motion parameter means
    """
    try:
        df = pd.read_csv(confounds_path, sep='\t')
    except Exception as e:
        raise MotionExtractionError(
            f"Failed to read confounds file {confounds_path}: {e}"
        )

    # Define expected motion parameter columns
    motion_cols = {
        'translation_x': 'trans_x',
        'translation_y': 'trans_y',
        'translation_z': 'trans_z',
        'rotation_x': 'rot_x',
        'rotation_y': 'rot_y',
        'rotation_z': 'rot_z'
    }

    # Verify all required columns exist
    missing_cols = []
    for output_name, fmriprep_name in motion_cols.items():
        if fmriprep_name not in df.columns:
            missing_cols.append(fmriprep_name)

    if missing_cols:
        raise MotionExtractionError(
            f"Missing motion parameter columns in {confounds_path}: {missing_cols}. "
            f"Available columns: {list(df.columns)}"
        )

    subject_id = extract_subject_id_from_path(confounds_path)

    result = {'subject_id': subject_id}

    for output_name, fmriprep_name in motion_cols.items():
        # Compute mean absolute displacement
        values = df[fmriprep_name].dropna()
        if len(values) == 0:
            result[output_name] = 0.0
        else:
            result[output_name] = float(values.abs().mean())

    return result


def extract_all_motion_parameters(confounds_files: List[Path]) -> List[Dict[str, Any]]:
    """
    Extract motion parameters from all confounds files.

    Args:
        confounds_files: List of paths to confounds TSV files

    Returns:
        List of dictionaries, one per subject, containing motion parameters
    """
    all_results = []

    for confounds_path in confounds_files:
        try:
            result = extract_motion_parameters(confounds_path)
            all_results.append(result)
        except MotionExtractionError as e:
            # Log warning but continue processing other subjects
            print(f"Warning: {e}")
            continue

    return all_results


def write_motion_csv(results: List[Dict[str, Any]], output_path: Path) -> None:
    """
    Write motion parameters to a CSV file.

    Args:
        results: List of dictionaries with motion parameters
        output_path: Path to the output CSV file
    """
    if not results:
        raise MotionExtractionError("No results to write - motion extraction failed for all subjects")

    # Define column order
    fieldnames = [
        'subject_id',
        'translation_x', 'translation_y', 'translation_z',
        'rotation_x', 'rotation_y', 'rotation_z'
    ]

    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w', newline='') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)


def run_motion_extraction(data_root: Optional[Path] = None, output_path: Optional[Path] = None) -> Path:
    """
    Main function to extract motion parameters from fMRIPrep output.

    Args:
        data_root: Root directory of the dataset (defaults to data/ from env config)
        output_path: Path for the output CSV (defaults to data/processed/motion_parameters.csv)

    Returns:
        Path to the generated CSV file
    """
    if data_root is None:
        data_root = Path(get_data_dir())

    data_root = Path(data_root)

    if output_path is None:
        output_path = data_root / "processed" / "motion_parameters.csv"

    print(f"Searching for fMRIPrep confounds files in {data_root}...")
    confounds_files = find_fmriprep_confounds(data_root)
    print(f"Found {len(confounds_files)} confounds files.")

    print("Extracting motion parameters...")
    results = extract_all_motion_parameters(confounds_files)
    print(f"Successfully extracted parameters for {len(results)} subjects.")

    print(f"Writing results to {output_path}...")
    write_motion_csv(results, output_path)
    print("Done.")

    return output_path


def main():
    """Entry point for command-line execution."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Extract motion parameters from fMRIPrep output"
    )
    parser.add_argument(
        "--data-root",
        type=str,
        default=None,
        help="Root directory of the dataset (default: from environment)"
    )
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="Output CSV path (default: data/processed/motion_parameters.csv)"
    )

    args = parser.parse_args()

    data_root = Path(args.data_root) if args.data_root else None
    output_path = Path(args.output) if args.output else None

    try:
        result_path = run_motion_extraction(data_root, output_path)
        print(f"Motion parameters written to: {result_path}")
    except MotionExtractionError as e:
        print(f"Error: {e}")
        exit(1)


if __name__ == "__main__":
    main()
