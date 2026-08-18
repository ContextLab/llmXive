import os
import json
import logging
from pathlib import Path
from typing import Optional, Dict, Any, List, Tuple
import pandas as pd
import numpy as np

from utils.io import load_json, save_json, ensure_dir
from config import get_data_path, get_processed_path

logger = logging.getLogger(__name__)

class DataValidationError(Exception):
    """Custom exception for data validation failures."""
    def __init__(self, message: str, code: str):
        super().__init__(message)
        self.code = code

def exclude_subjects_by_missing_data(
    participants_df: pd.DataFrame,
    missing_threshold: float = 0.10
) -> List[str]:
    """
    Identify subjects with >10% missing behavioral data.
    
    Args:
        participants_df: DataFrame from participants.tsv
        missing_threshold: Fraction of missing values allowed (default 0.10)
        
    Returns:
        List of subject IDs to exclude
    """
    # Identify numeric/behavioral columns (excluding subject ID and non-numeric metadata)
    numeric_cols = participants_df.select_dtypes(include=[np.number]).columns.tolist()
    
    if not numeric_cols:
        logger.warning("No numeric behavioral columns found in participants.tsv")
        return []
    
    # Calculate missing percentage per subject
    missing_counts = participants_df[numeric_cols].isnull().sum(axis=1)
    total_cols = len(numeric_cols)
    missing_pct = missing_counts / total_cols
    
    # Filter subjects exceeding threshold
    exclude_ids = participants_df.loc[missing_pct > missing_threshold, 'subject_id'].tolist()
    
    if exclude_ids:
        logger.warning(f"Found {len(exclude_ids)} subjects with >{missing_threshold*100}% missing behavioral data")
        for sub_id in exclude_ids:
            pct = missing_pct[participants_df['subject_id'] == sub_id].values[0]
            logger.debug(f"Subject {sub_id} has {pct*100:.1f}% missing data")
    
    return exclude_ids

def check_data_integrity(
    participants_df: pd.DataFrame,
    min_sample_size: int = 85
) -> Tuple[bool, str]:
    """
    Perform comprehensive data integrity checks.
    
    1. Check sample size N >= 85.
    2. Verify 'musical_genre' or 'STOMP-R' exists.
    
    Args:
        participants_df: DataFrame from participants.tsv
        min_sample_size: Minimum required subjects
        
    Returns:
        Tuple of (is_valid, message)
    """
    n_subjects = len(participants_df)
    if n_subjects < min_sample_size:
        msg = f"Sample size {n_subjects} is below minimum {min_sample_size}. ERR_UNDERPOWERED"
        logger.error(msg)
        return False, msg
    
    # Check for required behavioral variables
    cols = participants_df.columns.tolist()
    has_genre = 'musical_genre' in cols
    has_stomp = 'STOMP-R' in cols or 'stomp_r' in cols
    
    if not has_genre and not has_stomp:
        missing = "musical_genre" if 'musical_genre' not in cols else "STOMP-R"
        msg = f"Required behavioral variable missing: {missing}. ERR_DATA_MISSING"
        logger.error(msg)
        return False, msg
    
    return True, "Data integrity check passed."

def exclude_subjects_by_motion(
    confounds_dir: Path,
    fd_threshold: float = 0.5,
    motion_fraction_threshold: float = 0.10
) -> List[str]:
    """
    Flag/exclude subjects with excessive head motion.
    
    Criteria: Exclude if >10% of timepoints have FD > 0.5mm.
    
    Args:
        confounds_dir: Path to directory containing confounds TSV files
        fd_threshold: Framewise displacement threshold in mm (default 0.5)
        motion_fraction_threshold: Max allowed fraction of high-motion timepoints (default 0.10)
        
    Returns:
        List of subject IDs to exclude
    """
    exclude_ids = []
    
    if not confounds_dir.exists():
        logger.error(f"Confounds directory not found: {confounds_dir}")
        return exclude_ids
    
    # Iterate over confounds files (assuming fMRIPrep naming: sub-<id>_desc-confounds_timeseries.tsv)
    confounds_files = list(confounds_dir.glob("*desc-confounds_timeseries.tsv"))
    
    if not confounds_files:
        logger.warning("No confounds files found in directory. Check fMRIPrep output paths.")
        return exclude_ids
    
    logger.info(f"Checking motion for {len(confounds_files)} subjects...")
    
    for fpath in confounds_files:
        # Extract subject ID from filename (e.g., sub-01_desc-confounds_timeseries.tsv -> 01)
        stem = fpath.stem
        # Handle potential sub- prefix
        if stem.startswith("sub-"):
            sub_id = stem.split("_")[0].replace("sub-", "")
        else:
            sub_id = stem.split("_")[0]
        
        try:
            df = pd.read_csv(fpath, sep='\t', low_memory=False)
            
            # Identify FD column (common names: 'framewise_displacement', 'FD')
            fd_col = None
            candidates = ['framewise_displacement', 'FD', 'FramewiseDisplacement']
            for cand in candidates:
                if cand in df.columns:
                    fd_col = cand
                    break
            
            if fd_col is None:
                logger.warning(f"FD column not found in {fpath.name}. Skipping motion check.")
                continue
            
            # Check for NaNs in FD column
            if df[fd_col].isnull().any():
                # fMRIPrep often has NaN for first timepoint; drop them for calculation
                valid_fd = df[fd_col].dropna()
            else:
                valid_fd = df[fd_col]
            
            if len(valid_fd) == 0:
                logger.warning(f"No valid FD values for {sub_id}. Skipping.")
                continue
            
            # Calculate fraction of timepoints exceeding threshold
            high_motion_mask = valid_fd > fd_threshold
            high_motion_fraction = high_motion_mask.sum() / len(valid_fd)
            
            if high_motion_fraction > motion_fraction_threshold:
                exclude_ids.append(sub_id)
                pct = high_motion_fraction * 100
                logger.warning(
                    f"Subject {sub_id} excluded: {pct:.1f}% of timepoints have FD > {fd_threshold}mm"
                )
            
        except Exception as e:
            logger.error(f"Error processing confounds for {sub_id}: {e}")
            continue
    
    if exclude_ids:
        logger.info(f"Total subjects excluded due to motion: {len(exclude_ids)}")
    else:
        logger.info("No subjects excluded due to excessive head motion.")
        
    return exclude_ids

def main():
    """CLI entry point for motion exclusion."""
    logging.basicConfig(level=logging.INFO)
    
    # Load config or use defaults
    confounds_path = get_processed_path("confounds")
    
    if not confounds_path.exists():
        print(f"Error: Confounds directory not found at {confounds_path}")
        print("Please run preprocessing (T014) first.")
        return 1
    
    excluded = exclude_subjects_by_motion(confounds_path)
    
    # Save report
    report = {
        "excluded_subjects": excluded,
        "count": len(excluded),
        "threshold_mm": 0.5,
        "fraction_threshold": 0.10
    }
    
    report_path = get_data_path("processed", "motion_exclusion_report.json")
    ensure_dir(report_path)
    save_json(report_path, report)
    
    print(f"Motion exclusion complete. Excluded {len(excluded)} subjects.")
    print(f"Report saved to {report_path}")
    
    return 0

if __name__ == "__main__":
    exit(main())
