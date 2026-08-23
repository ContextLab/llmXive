"""
Data validation module for fMRI datasets.
Refactored for modularity: separates file checks, sample size validation, and behavioral variable extraction.
"""
import os
import json
import logging
from pathlib import Path
from typing import Optional, Dict, Any, List, Tuple
import pandas as pd

from config import get_data_path
from utils.io import load_json, ensure_dir

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class DataValidationError(Exception):
    """Custom exception for data validation errors."""
    def __init__(self, message: str, code: str = "ERR_DATA_VALIDATION"):
        self.code = code
        super().__init__(message)

def check_participants_file(data_dir: Path) -> Path:
    """
    Check if participants.tsv exists in the dataset directory.
    
    Args:
        data_dir: Path to the dataset directory
        
    Returns:
        Path to the participants.tsv file
        
    Raises:
        DataValidationError: If participants.tsv is missing
    """
    participants_path = data_dir / "participants.tsv"
    
    if not participants_path.exists():
        raise DataValidationError(
            f"participants.tsv not found in {data_dir}",
            code="ERR_FILE_MISSING"
        )
    
    logger.info(f"Found participants.tsv at {participants_path}")
    return participants_path

def validate_sample_size(participants_df: pd.DataFrame, min_n: int = 85) -> int:
    """
    Validate that the sample size meets the power requirement (N >= 85).
    
    Args:
        participants_df: DataFrame loaded from participants.tsv
        min_n: Minimum required sample size (default 85 per Plan)
        
    Returns:
        Number of subjects in the dataset
        
    Raises:
        DataValidationError: If sample size is insufficient
    """
    n_subjects = len(participants_df)
    
    if n_subjects < min_n:
        logger.error(f"Sample size N={n_subjects} is underpowered. Required: N>={min_n}")
        raise DataValidationError(
            f"Underpowered dataset: N={n_subjects} < {min_n}",
            code="ERR_UNDERPOWERED"
        )
    
    logger.info(f"Sample size validation passed: N={n_subjects} >= {min_n}")
    return n_subjects

def get_behavioral_variable(participants_df: pd.DataFrame, 
                            primary_var: str = "musical_genre", 
                            fallback_var: str = "STOMP-R") -> str:
    """
    Get the behavioral variable name, attempting fallback if primary is missing.
    
    Args:
        participants_df: DataFrame loaded from participants.tsv
        primary_var: Primary behavioral variable name
        fallback_var: Fallback variable name if primary is missing
        
    Returns:
        Name of the behavioral variable to use
        
    Raises:
        DataValidationError: If both primary and fallback variables are missing
    """
    columns = participants_df.columns.tolist()
    
    if primary_var in columns:
        logger.info(f"Using primary behavioral variable: {primary_var}")
        return primary_var
    
    logger.warning(f"Primary variable '{primary_var}' not found. Checking for fallback: {fallback_var}")
    
    if fallback_var in columns:
        logger.warning(f"Fallback variable '{fallback_var}' found. Using it instead.")
        return fallback_var
    
    # Both missing
    missing_fields = [primary_var, fallback_var]
    raise DataValidationError(
        f"Behavioral variables missing: {', '.join(missing_fields)}. "
        f"Found columns: {columns}",
        code="ERR_DATA_MISSING"
    )

def exclude_subjects_by_missing_data(confounds_df: pd.DataFrame, 
                                     threshold: float = 0.1) -> List[str]:
    """
    Flag subjects with >threshold % corrupted fMRI volumes.
    
    Args:
        confounds_df: DataFrame of confounds (one row per volume, with subject_id column)
        threshold: Fraction of corrupted volumes to trigger exclusion
        
    Returns:
        List of subject IDs to exclude
    """
    if 'subject_id' not in confounds_df.columns:
        logger.warning("confounds_df missing 'subject_id' column. Skipping exclusion by missing data.")
        return []
    
    # Group by subject and calculate corruption rate
    # Assuming 'corrupted' or similar flag exists, or we check for NaN in key columns
    # For now, we check for NaN in framewise_displacement as a proxy for corruption
    if 'framewise_displacement' not in confounds_df.columns:
        logger.warning("framewise_displacement not found in confounds. Skipping corruption check.")
        return []
    
    subject_stats = confounds_df.groupby('subject_id')['framewise_displacement'].agg(['count', 'sum', 'mean'])
    # Simple heuristic: if mean FD is extremely high or count is very low (missing data)
    # A more robust check would look for specific corruption flags
    
    excluded = []
    for subj_id, stats in subject_stats.iterrows():
        # Check for excessive missing data (count of valid rows vs total expected)
        # This is a simplified check; real implementation would depend on BIDS confounds structure
        if pd.isna(stats['mean']) or stats['count'] == 0:
            excluded.append(subj_id)
    
    if excluded:
        logger.info(f"Excluding {len(excluded)} subjects due to missing data issues.")
    
    return excluded

def exclude_subjects_by_motion(confounds_df: pd.DataFrame, 
                               fd_threshold: float = 0.5) -> List[str]:
    """
    Flag subjects with excessive head motion (>fd_threshold mm FD).
    
    Args:
        confounds_df: DataFrame of confounds
        fd_threshold: Maximum allowed mean Framewise Displacement
        
    Returns:
        List of subject IDs to exclude
    """
    if 'subject_id' not in confounds_df.columns or 'framewise_displacement' not in confounds_df.columns:
        logger.warning("Required columns for motion check missing. Skipping motion exclusion.")
        return []
    
    # Calculate mean FD per subject
    mean_fd = confounds_df.groupby('subject_id')['framewise_displacement'].mean()
    
    excluded = mean_fd[mean_fd > fd_threshold].index.tolist()
    
    if excluded:
        logger.warning(f"Excluding {len(excluded)} subjects due to excessive motion (mean FD > {fd_threshold}mm).")
        logger.warning(f"Excluded subjects: {excluded[:5]}...") # Log first 5
    
    return excluded

def check_data_integrity(data_dir: Path, 
                         min_n: int = 85,
                         primary_var: str = "musical_genre",
                         fallback_var: str = "STOMP-R") -> List[str]:
    """
    Perform comprehensive data integrity checks.
    
    Args:
        data_dir: Path to the dataset directory
        min_n: Minimum required sample size
        primary_var: Primary behavioral variable name
        fallback_var: Fallback variable name
        
    Returns:
        List of valid subject IDs
        
    Raises:
        DataValidationError: If critical checks fail
    """
    logger.info(f"Starting data integrity check for {data_dir}")
    
    # 1. File Existence Check
    participants_path = check_participants_file(data_dir)
    
    # 2. Load and Validate Sample Size
    participants_df = pd.read_csv(participants_path, sep='\t')
    n_subjects = validate_sample_size(participants_df, min_n)
    
    # 3. Variable Validation
    behavioral_var = get_behavioral_variable(participants_df, primary_var, fallback_var)
    
    # 4. Check for confounds if available (for motion/corruption checks)
    # This is optional and depends on preprocessing status
    confounds_path = data_dir / "derivatives" / "fmriprep"
    if confounds_path.exists():
        # Try to load confounds if they exist (simplified logic)
        # In a real pipeline, we'd scan for *_confounds.tsv files
        logger.info("Derivatives found. Skipping deep confounds check here (handled in preprocess step).")
    
    # Return valid subjects (all, since we passed the hard gates)
    valid_subjects = participants_df['participant_id'].tolist()
    
    logger.info(f"Data integrity check passed. {len(valid_subjects)} valid subjects.")
    return valid_subjects

def main():
    """CLI entry point for data validation."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Validate fMRI dataset integrity")
    parser.add_argument("--dataset", type=str, required=True, help="Dataset directory path")
    parser.add_argument("--min-n", type=int, default=85, help="Minimum sample size")
    parser.add_argument("--primary-var", type=str, default="musical_genre", help="Primary behavioral variable")
    parser.add_argument("--fallback-var", type=str, default="STOMP-R", help="Fallback behavioral variable")
    
    args = parser.parse_args()
    
    data_dir = Path(args.dataset)
    
    if not data_dir.exists():
        print(f"ERROR: Directory {data_dir} does not exist.")
        return 1
    
    try:
        valid_subjects = check_data_integrity(
            data_dir, 
            min_n=args.min_n,
            primary_var=args.primary_var,
            fallback_var=args.fallback_var
        )
        print(f"SUCCESS: Validation passed. {len(valid_subjects)} subjects valid.")
        return 0
    except DataValidationError as e:
        print(f"VALIDATION ERROR [{e.code}]: {e}")
        return 1
    except Exception as e:
        print(f"UNEXPECTED ERROR: {e}")
        return 2

if __name__ == "__main__":
    exit(main())