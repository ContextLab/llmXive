import os
import json
import logging
from pathlib import Path
from typing import Optional, Dict, Any, List, Tuple
import pandas as pd
import numpy as np

from utils.io import load_parquet, load_json, save_parquet, save_json

logger = logging.getLogger(__name__)

class DataValidationError(Exception):
    """Custom exception for data validation failures."""
    def __init__(self, message: str, code: str):
        super().__init__(message)
        self.code = code

def validate_dataset_id(dataset_id: str) -> bool:
    """Validate dataset ID against a verified list."""
    verified_ids = {"ds000030", "ds000208"}
    if dataset_id not in verified_ids:
        raise DataValidationError(
            f"Dataset ID {dataset_id} is not in the verified list.",
            code="ERR_INVALID_DATASET"
        )
    return True

def check_sample_size(n: int, min_n: int = 85) -> bool:
    """Check if sample size meets the hard gate requirement."""
    if n < min_n:
        raise DataValidationError(
            f"Sample size N={n} is below the hard gate threshold of {min_n}.",
            code="ERR_UNDERPOWERED"
        )
    return True

def check_behavioral_variables(participants_df: pd.DataFrame) -> List[str]:
    """Check for required behavioral variables, with fallback logic."""
    required_vars = ["musical_genre"]
    fallback_vars = ["STOMP-R"]
    
    missing = []
    for var in required_vars:
        if var not in participants_df.columns:
            missing.append(var)
    
    if missing:
        # Try fallback
        fallback_found = False
        for fb in fallback_vars:
            if fb in participants_df.columns:
                logger.info(f"Primary variable missing, using fallback: {fb}")
                fallback_found = True
                break
        
        if not fallback_found:
            raise DataValidationError(
                f"Required behavioral variables missing: {missing}. Fallbacks also missing.",
                code="ERR_DATA_MISSING"
            )
    
    return missing

def check_data_integrity(dataset_id: str, raw_dir: str) -> Dict[str, Any]:
    """Comprehensive data integrity check."""
    validate_dataset_id(dataset_id)
    
    participants_path = Path(raw_dir) / "participants.tsv"
    if not participants_path.exists():
        raise DataValidationError(
            "participants.tsv not found in dataset.",
            code="ERR_DATA_MISSING"
        )
    
    participants_df = pd.read_csv(participants_path, sep='\t')
    check_sample_size(len(participants_df))
    check_behavioral_variables(participants_df)
    
    return {"status": "ok", "n_subjects": len(participants_df)}

def exclude_subjects_by_missing_data(participants_df: pd.DataFrame, threshold: float = 0.1) -> Tuple[pd.DataFrame, List[str]]:
    """Exclude subjects with > threshold missing behavioral data."""
    # Identify columns that are behavioral (not 'participant_id')
    behavioral_cols = [c for c in participants_df.columns if c != 'participant_id' and c != 'subject_id']
    
    if not behavioral_cols:
        logger.warning("No behavioral columns found to check for missing data.")
        return participants_df, []
    
    # Calculate missing percentage per row
    missing_pct = participants_df[behavioral_cols].isna().mean(axis=1)
    
    excluded_mask = missing_pct > threshold
    excluded_ids = participants_df[excluded_mask]['participant_id'].tolist()
    
    if excluded_ids:
        logger.info(f"Excluding {len(excluded_ids)} subjects due to >{threshold*100}% missing behavioral data.")
    
    return participants_df[~excluded_mask], excluded_ids

def exclude_subjects_by_motion(confounds_path: str, fd_threshold: float = 0.5) -> Tuple[pd.DataFrame, List[str]]:
    """
    Load confounds data (Parquet or JSON) and exclude subjects with mean FD > threshold.
    
    Args:
        confounds_path: Path to the confounds file (e.g., sub-01_desc-confounds_timeseries.tsv)
        fd_threshold: Maximum allowed mean Framewise Displacement (default 0.5mm)
    
    Returns:
        Tuple of (valid_subjects_df, excluded_subject_ids)
    """
    if not os.path.exists(confounds_path):
        logger.warning(f"Confounds file not found: {confounds_path}. Skipping motion exclusion for this file.")
        return pd.DataFrame(), []
    
    try:
        # Try loading as TSV first (standard fMRIPrep output)
        confounds_df = pd.read_csv(confounds_path, sep='\t')
    except Exception:
        try:
            # Try loading as Parquet
            confounds_df = load_parquet(confounds_path)
        except Exception:
            try:
                # Try loading as JSON (rare, but possible)
                with open(confounds_path, 'r') as f:
                    confounds_df = pd.DataFrame([json.load(f)])
            except Exception:
                raise DataValidationError(f"Could not parse confounds file: {confounds_path}", "ERR_DATA_CORRUPT")
    
    if 'framewise_displacement' not in confounds_df.columns:
        logger.warning("framewise_displacement column not found in confounds. Skipping motion check.")
        return pd.DataFrame(), []
    
    # Calculate mean FD for this subject (based on this file)
    mean_fd = confounds_df['framewise_displacement'].mean()
    
    # Extract subject ID from filename if not in dataframe
    # Expected filename format: sub-<label>_desc-confounds_timeseries.tsv
    subject_id = Path(confounds_path).stem.split('_')[0].replace('sub-', '')
    
    if mean_fd > fd_threshold:
        logger.info(f"Subject {subject_id} excluded: Mean FD = {mean_fd:.3f}mm > {fd_threshold}mm")
        return pd.DataFrame({'subject_id': [subject_id], 'mean_fd': [mean_fd]}), [subject_id]
    
    return pd.DataFrame({'subject_id': [subject_id], 'mean_fd': [mean_fd]}), []

def main():
    """
    CLI entry point for running motion exclusion checks on a dataset.
    Expects a path to a directory containing confounds files.
    """
    import argparse
    
    parser = argparse.ArgumentParser(description="Exclude subjects based on head motion (FD).")
    parser.add_argument("--confounds-dir", type=str, required=True, help="Directory containing confounds files")
    parser.add_argument("--output", type=str, default="data/derived/motion_exclusion_report.json", help="Output JSON path")
    parser.add_argument("--threshold", type=float, default=0.5, help="FD threshold (default: 0.5mm)")
    
    args = parser.parse_args()
    
    confounds_dir = Path(args.confounds_dir)
    if not confounds_dir.exists():
        logger.error(f"Directory not found: {confounds_dir}")
        return
    
    excluded_subjects = []
    all_stats = []
    
    # Find all confounds files (pattern: *desc-confounds*)
    confounds_files = list(confounds_dir.glob("*desc-confounds*"))
    if not confounds_files:
        # Fallback to generic tsv/parquet if pattern doesn't match
        confounds_files = list(confounds_dir.glob("*.tsv")) + list(confounds_dir.glob("*.parquet"))
    
    logger.info(f"Found {len(confounds_files)} confounds files.")
    
    for conf_file in confounds_files:
        valid_df, excluded_ids = exclude_subjects_by_motion(str(conf_file), args.threshold)
        all_stats.append(valid_df)
        excluded_subjects.extend(excluded_ids)
    
    # Combine stats
    if all_stats:
        combined_stats = pd.concat(all_stats, ignore_index=True)
    else:
        combined_stats = pd.DataFrame(columns=['subject_id', 'mean_fd'])
    
    report = {
        "threshold_mm": args.threshold,
        "total_subjects_processed": len(combined_stats),
        "excluded_count": len(excluded_subjects),
        "excluded_subjects": excluded_subjects,
        "statistics": combined_stats.to_dict(orient='records')
    }
    
    # Save report
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    save_json(report, str(output_path))
    logger.info(f"Motion exclusion report saved to {output_path}")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()