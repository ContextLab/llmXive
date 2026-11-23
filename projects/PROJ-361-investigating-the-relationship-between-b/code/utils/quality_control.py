"""
Motion quality control utilities for fMRI preprocessing.

This module calculates Mean Framewise Displacement (FD) for all subjects
derived from fMRIPrep outputs and excludes subjects exceeding the threshold
(0.5mm).
"""

import os
import re
from pathlib import Path
from typing import List, Dict, Tuple, Optional
import numpy as np
import pandas as pd

from utils.config import get_raw_data_dir, get_processed_data_dir
from utils.logging_utils import get_logger, log_preprocessing_step

logger = get_logger(__name__)

# Threshold defined in Spec Constraints
MEAN_FD_THRESHOLD = 0.5

def parse_fmriprep_confounds(confounds_file: Path) -> pd.DataFrame:
    """
    Load fMRIPrep confounds TSV and extract Framewise Displacement (FD).

    Args:
        confounds_file: Path to the *_confounds.tsv file from fMRIPrep.

    Returns:
        DataFrame containing the 'framewise_displacement' column.
    """
    if not confounds_file.exists():
        raise FileNotFoundError(f"Confounds file not found: {confounds_file}")

    try:
        df = pd.read_csv(confounds_file, sep='\t')
    except Exception as e:
        raise PreprocessingError(f"Failed to parse confounds file {confounds_file}: {e}")

    if 'framewise_displacement' not in df.columns:
        raise ValueError(f"Column 'framewise_displacement' missing in {confounds_file}. "
                         f"Available columns: {list(df.columns)}")

    return df[['framewise_displacement']]

def calculate_mean_fd(confounds_file: Path) -> float:
    """
    Calculate the mean Framewise Displacement for a single subject.

    Args:
        confounds_file: Path to the confounds TSV.

    Returns:
        Mean FD value (float).
    """
    df = parse_fmriprep_confounds(confounds_file)
    fd_values = df['framewise_displacement'].dropna()

    if len(fd_values) == 0:
        raise ValueError("No valid FD values found in confounds file.")

    return float(fd_values.mean())

def get_subject_confounds_paths(raw_data_dir: Path) -> List[Tuple[str, Path]]:
    """
    Scan the raw data directory for fMRIPrep confounds files.

    Expects structure: data/raw/{subject_id}/func/sub-{id}_desc-preproc_confounds.tsv
    (or similar standard fMRIPrep output paths).

    Returns:
        List of tuples (subject_id, path_to_confounds).
    """
    confounds_files = []
    pattern = re.compile(r"sub-([a-zA-Z0-9]+)")

    # Recursively search for confounds files
    for tsv_file in raw_data_dir.rglob("*_confounds.tsv"):
        match = pattern.search(tsv_file.name)
        if match:
            subject_id = match.group(1)
            confounds_files.append((subject_id, tsv_file))

    logger.info(f"Found {len(confounds_files)} confounds files for {len(set([s for s, _ in confounds_files]))} subjects.")
    return confounds_files

class PreprocessingError(Exception):
    """Custom exception for preprocessing failures."""
    pass

def run_quality_control(raw_data_dir: Optional[Path] = None, output_dir: Optional[Path] = None) -> Dict[str, any]:
    """
    Main entry point for motion quality control.

    1. Scans for all subjects in data/raw.
    2. Calculates Mean FD for each.
    3. Records values.
    4. Excludes subjects with Mean FD > 0.5mm.
    5. Saves results to a CSV in data/processed.

    Args:
        raw_data_dir: Optional override for raw data path.
        output_dir: Optional override for output path.

    Returns:
        Dictionary containing 'included_subjects', 'excluded_subjects', and 'metrics'.
    """
    if raw_data_dir is None:
        raw_data_dir = get_raw_data_dir()
    if output_dir is None:
        output_dir = get_processed_data_dir()

    os.makedirs(output_dir, exist_ok=True)

    log_preprocessing_step("Starting Motion Quality Control (T015)")
    logger.info(f"Scanning {raw_data_dir} for fMRIPrep confounds files.")

    confounds_paths = get_subject_confounds_paths(raw_data_dir)

    if not confounds_paths:
        raise RuntimeError("No confounds files found. Ensure fMRIPrep has run (T013) and data is in data/raw/.")

    results = []
    included = []
    excluded = []

    for subject_id, conf_path in confounds_paths:
        try:
            mean_fd = calculate_mean_fd(conf_path)
            is_excluded = mean_fd > MEAN_FD_THRESHOLD

            results.append({
                "subject_id": subject_id,
                "mean_fd_mm": mean_fd,
                "excluded": is_excluded,
                "reason": "Motion > 0.5mm" if is_excluded else None
            })

            if is_excluded:
                excluded.append(subject_id)
                logger.warning(f"Subject {subject_id} EXCLUDED: Mean FD = {mean_fd:.4f}mm (Threshold: {MEAN_FD_THRESHOLD}mm)")
            else:
                included.append(subject_id)
                logger.info(f"Subject {subject_id} INCLUDED: Mean FD = {mean_fd:.4f}mm")

        except Exception as e:
            logger.error(f"Failed to process subject {subject_id}: {e}")
            # Treat failure as exclusion to be safe, or strictly fail the pipeline?
            # Per "fail loudly", we log error but continue to other subjects to report all failures.
            results.append({
                "subject_id": subject_id,
                "mean_fd_mm": None,
                "excluded": True,
                "reason": f"Processing error: {str(e)}"
            })
            excluded.append(subject_id)

    # Save detailed report
    report_path = output_dir / "qc_motion_report.csv"
    df_results = pd.DataFrame(results)
    df_results.to_csv(report_path, index=False)
    logger.info(f"Saved QC report to {report_path}")

    # Save exclusion list (text file for easy piping to next steps)
    exclusion_path = output_dir / "excluded_subjects.txt"
    with open(exclusion_path, 'w') as f:
        for sub in excluded:
            f.write(f"{sub}\n")
    logger.info(f"Saved exclusion list to {exclusion_path}")

    log_preprocessing_step(
        "Motion QC Complete",
        details=f"Included: {len(included)}, Excluded: {len(excluded)}"
    )

    return {
        "included_subjects": included,
        "excluded_subjects": excluded,
        "metrics": results,
        "report_path": str(report_path),
        "exclusion_list_path": str(exclusion_path)
    }

def main():
    """CLI entry point."""
    import argparse
    parser = argparse.ArgumentParser(description="Run Motion Quality Control on fMRIPrep outputs.")
    parser.add_argument("--raw-dir", type=str, default=None, help="Override raw data directory")
    parser.add_argument("--output-dir", type=str, default=None, help="Override output directory")
    args = parser.parse_args()

    raw_dir = Path(args.raw_dir) if args.raw_dir else None
    out_dir = Path(args.output_dir) if args.output_dir else None

    run_quality_control(raw_data_dir=raw_dir, output_dir=out_dir)

if __name__ == "__main__":
    main()
