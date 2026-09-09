"""
Motion exclusion filter for fMRI preprocessing pipeline.

Filters subjects based on motion parameters extracted from fMRIPrep output.
Exclusion criteria: >3mm translation or >3° rotation.
"""
import os
import csv
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import pandas as pd

from src.config.env import get_data_dir

logger = logging.getLogger(__name__)

# Exclusion thresholds per task specification
MAX_TRANSLATION_MM = 3.0
MAX_ROTATION_DEG = 3.0

class MotionFilterError(Exception):
    """Custom exception for motion filtering errors."""
    pass

def load_motion_data(motion_csv_path: Path) -> pd.DataFrame:
    """
    Load motion parameters from a CSV file.

    Args:
        motion_csv_path: Path to the motion parameters CSV file.

    Returns:
        DataFrame with motion parameters.

    Raises:
        MotionFilterError: If the file cannot be loaded or is missing required columns.
    """
    if not motion_csv_path.exists():
        raise MotionFilterError(f"Motion CSV file not found: {motion_csv_path}")

    try:
        df = pd.read_csv(motion_csv_path)
    except Exception as e:
        raise MotionFilterError(f"Failed to read motion CSV: {e}")

    required_columns = ['subject_id', 'translation_x', 'translation_y', 'translation_z',
                        'rotation_x', 'rotation_y', 'rotation_z']
    missing_cols = [col for col in required_columns if col not in df.columns]
    if missing_cols:
        raise MotionFilterError(f"Missing required columns in motion CSV: {missing_cols}")

    return df

def calculate_max_displacement(row: pd.Series) -> Tuple[float, float]:
    """
    Calculate total displacement for a subject row.

    Args:
        row: A row from the motion DataFrame.

    Returns:
        Tuple of (max_translation_mm, max_rotation_deg).
    """
    translations = [row['translation_x'], row['translation_y'], row['translation_z']]
    rotations = [row['rotation_x'], row['rotation_y'], row['rotation_z']]

    max_trans = max(abs(t) for t in translations)
    max_rot = max(abs(r) for r in rotations)

    return max_trans, max_rot

def filter_subjects(df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame, List[Dict[str, Any]]]:
    """
    Filter subjects based on motion thresholds.

    Args:
        df: DataFrame with motion parameters.

    Returns:
        Tuple of (included_subjects, excluded_subjects, exclusion_details).
    """
    included_rows = []
    excluded_rows = []
    exclusion_details = []

    for _, row in df.iterrows():
        max_trans, max_rot = calculate_max_displacement(row)
        subject_id = row['subject_id']

        excluded = False
        reason = []

        if max_trans > MAX_TRANSLATION_MM:
            excluded = True
            reason.append(f"Max translation {max_trans:.2f}mm > {MAX_TRANSLATION_MM}mm")

        if max_rot > MAX_ROTATION_DEG:
            excluded = True
            reason.append(f"Max rotation {max_rot:.2f}deg > {MAX_ROTATION_DEG}deg")

        if excluded:
            excluded_rows.append(row)
            exclusion_details.append({
                'subject_id': subject_id,
                'max_translation_mm': max_trans,
                'max_rotation_deg': max_rot,
                'reason': "; ".join(reason)
            })
        else:
            included_rows.append(row)

    included_df = pd.DataFrame(included_rows) if included_rows else pd.DataFrame(columns=df.columns)
    excluded_df = pd.DataFrame(excluded_rows) if excluded_rows else pd.DataFrame(columns=df.columns)

    return included_df, excluded_df, exclusion_details

def write_exclusion_report(exclusion_details: List[Dict[str, Any]], output_path: Path) -> None:
    """
    Write a JSON report of excluded subjects.

    Args:
        exclusion_details: List of dictionaries with exclusion info.
        output_path: Path to write the JSON report.
    """
    import json

    output_path.parent.mkdir(parents=True, exist_ok=True)

    report = {
        "exclusion_thresholds": {
            "max_translation_mm": MAX_TRANSLATION_MM,
            "max_rotation_deg": MAX_ROTATION_DEG
        },
        "total_excluded": len(exclusion_details),
        "excluded_subjects": exclusion_details
    }

    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2)

    logger.info(f"Exclusion report written to {output_path}")

def run_motion_filter(input_csv: Path, output_csv: Path, report_path: Optional[Path] = None) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Main function to run the motion filter pipeline.

    Args:
        input_csv: Path to the input motion parameters CSV.
        output_csv: Path to write the filtered (included) subjects CSV.
        report_path: Optional path to write the exclusion report.

    Returns:
        Tuple of (included_df, excluded_df).
    """
    logger.info(f"Loading motion data from {input_csv}")
    df = load_motion_data(input_csv)

    logger.info(f"Filtering subjects (threshold: >{MAX_TRANSLATION_MM}mm or >{MAX_ROTATION_DEG}deg)")
    included_df, excluded_df, exclusion_details = filter_subjects(df)

    logger.info(f"Writing included subjects to {output_csv}")
    output_csv.parent.mkdir(parents=True, exist_ok=True)
    included_df.to_csv(output_csv, index=False)

    if report_path:
        logger.info(f"Writing exclusion report to {report_path}")
        write_exclusion_report(exclusion_details, report_path)
    else:
        logger.warning("No report path provided. Exclusion details not saved.")

    logger.info(f"Motion filtering complete. Included: {len(included_df)}, Excluded: {len(excluded_df)}")

    return included_df, excluded_df

def main() -> None:
    """
    Entry point for the motion filter script.
    """
    import argparse

    parser = argparse.ArgumentParser(description="Filter subjects based on motion parameters.")
    parser.add_argument("--input", type=str, required=True, help="Path to input motion CSV")
    parser.add_argument("--output", type=str, required=True, help="Path to output filtered CSV")
    parser.add_argument("--report", type=str, default=None, help="Path to exclusion report JSON")
    args = parser.parse_args()

    input_path = Path(args.input)
    output_path = Path(args.output)
    report_path = Path(args.report) if args.report else None

    run_motion_filter(input_path, output_path, report_path)

if __name__ == "__main__":
    main()
