import os
import json
import logging
from pathlib import Path
from typing import Optional, Dict, Any, List, Tuple
import pandas as pd
from utils.io import load_parquet, load_json, ensure_dir
from config import get_processed_path, get_derived_path

logger = logging.getLogger(__name__)

class DataValidationError(Exception):
    """Custom exception for data validation failures."""
    def __init__(self, message: str, code: str = "ERR_DATA_MISSING"):
        super().__init__(message)
        self.code = code
        self.message = message

def exclude_subjects_by_motion(
    subjects: List[str],
    confounds_dir: Optional[Path] = None,
    threshold_mm: float = 0.5
) -> Tuple[List[str], Dict[str, float], Dict[str, str]]:
    """
    Flag/exclude subjects with excessive head motion (Mean FD > threshold_mm).
    
    Args:
        subjects: List of subject IDs to check.
        confounds_dir: Directory containing confounds TSV files. Defaults to 
                       processed space confounds directory.
        threshold_mm: Maximum allowed mean Framewise Displacement (mm).
    
    Returns:
        Tuple containing:
            - List of valid subject IDs (passed motion check)
            - Dict mapping subject_id -> mean FD
            - Dict mapping subject_id -> exclusion reason (if excluded)
    
    Raises:
        DataValidationError: If no valid subjects remain after filtering.
    """
    if confounds_dir is None:
        confounds_dir = get_processed_path() / "confounds"
    
    if not confounds_dir.exists():
        logger.warning(f"Confounds directory not found at {confounds_dir}. "
                     "Skipping motion check. All subjects retained.")
        return subjects, {s: 0.0 for s in subjects}, {}

    valid_subjects = []
    motion_stats = {}
    exclusions = {}

    for sub_id in subjects:
        # Expected filename pattern: sub-<id>_desc-confounds_timeseries.tsv
        confound_file = confounds_dir / f"sub-{sub_id}_desc-confounds_timeseries.tsv"
        
        if not confound_file.exists():
            logger.warning(f"Confounds file missing for {sub_id}: {confound_file}. "
                         "Excluding subject.")
            exclusions[sub_id] = "missing_confounds"
            continue

        try:
            df = pd.read_csv(confound_file, sep='\t')
            
            # Check if 'framewise_displacement' column exists
            if 'framewise_displacement' not in df.columns:
                # Try common aliases
                fd_col = None
                candidates = ['framewise_displacement', 'fd', 'FramewiseDisplacement']
                for cand in candidates:
                    if cand in df.columns:
                        fd_col = cand
                        break
                
                if fd_col is None:
                    logger.warning(f"FD column not found in {confound_file}. "
                                 "Excluding subject.")
                    exclusions[sub_id] = "missing_fd_column"
                    continue
            else:
                fd_col = 'framewise_displacement'

            # Calculate mean FD, handling NaNs
            fd_values = df[fd_col].dropna()
            if len(fd_values) == 0:
                logger.warning(f"All FD values are NaN for {sub_id}. "
                             "Excluding subject.")
                exclusions[sub_id] = "all_fd_nan"
                continue

            mean_fd = fd_values.mean()
            motion_stats[sub_id] = mean_fd

            if mean_fd > threshold_mm:
                exclusions[sub_id] = f"high_motion: mean_fd={mean_fd:.3f}mm > {threshold_mm}mm"
                logger.info(f"Excluding subject {sub_id} due to high motion: "
                          f"mean FD = {mean_fd:.3f}mm")
            else:
                valid_subjects.append(sub_id)

        except Exception as e:
            logger.error(f"Error processing confounds for {sub_id}: {e}")
            exclusions[sub_id] = f"read_error: {str(e)}"
            continue

    if len(valid_subjects) == 0:
        raise DataValidationError(
            "No subjects passed the motion exclusion threshold. "
            f"Threshold was {threshold_mm}mm mean FD.",
            code="ERR_UNDERPOWERED"
        )

    logger.info(f"Motion exclusion complete: {len(exclusions)} excluded, "
              f"{len(valid_subjects)} retained.")
    
    return valid_subjects, motion_stats, exclusions

def main():
    """
    CLI entry point for motion exclusion validation.
    Reads subject list from data/derived/subject_list.json (if exists)
    or data/raw/participants.tsv, applies motion filter, and saves results.
    """
    logging.basicConfig(level=logging.INFO)
    
    # Try to load subject list from derived data first
    subject_list_path = get_derived_path() / "subject_list.json"
    if subject_list_path.exists():
        with open(subject_list_path, 'r') as f:
            subjects = json.load(f)
    else:
        # Fallback: read from raw participants file
        raw_dir = get_processed_path().parent / "raw"
        participants_file = raw_dir / "participants.tsv"
        if not participants_file.exists():
            # Try common raw location
            participants_file = Path("data/raw/participants.tsv")
        
        if participants_file.exists():
            df = pd.read_csv(participants_file, sep='\t')
            subjects = df['participant_id'].tolist()
        else:
            logger.error("No subject list found. Cannot run motion exclusion.")
            return

    logger.info(f"Loaded {len(subjects)} subjects for motion check.")
    
    valid_subjects, stats, exclusions = exclude_subjects_by_motion(subjects)
    
    # Save results
    output_dir = get_derived_path()
    ensure_dir(output_dir)
    
    stats_path = output_dir / "motion_statistics.json"
    with open(stats_path, 'w') as f:
        json.dump({
            "valid_subjects": valid_subjects,
            "motion_stats": stats,
            "exclusions": exclusions
        }, f, indent=2)
    
    logger.info(f"Motion report saved to {stats_path}")
    logger.info(f"Valid subjects: {len(valid_subjects)}")

if __name__ == "__main__":
    main()
