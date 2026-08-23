"""
Data validation module for fMRI and behavioral data.
Implements strict integrity checks, sample size validation, and variable fallback logic.
"""
import os
import json
import logging
from pathlib import Path
from typing import Optional, Dict, Any, List, Tuple
import pandas as pd
import numpy as np

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class DataValidationError(Exception):
    """Custom exception for data validation failures."""
    def __init__(self, message: str, code: str = "ERR_DATA_MISSING"):
        super().__init__(message)
        self.code = code
        self.message = message

def check_participants_file(dataset_dir: Path) -> Path:
    """
    Verify that participants.tsv exists in the dataset directory.
    
    Args:
        dataset_dir: Path to the BIDS dataset root.
        
    Returns:
        Path to the participants.tsv file.
        
    Raises:
        FileNotFoundError: If participants.tsv is missing.
    """
    participants_path = dataset_dir / "participants.tsv"
    if not participants_path.exists():
        raise FileNotFoundError(
            f"CRITICAL: participants.tsv not found at {participants_path}. "
            "Dataset may be incomplete or not in BIDS format."
        )
    return participants_path

def validate_sample_size(df: pd.DataFrame, min_n: int = 85) -> bool:
    """
    Validate that the sample size meets the minimum power requirement.
    
    Args:
        df: DataFrame containing subject data.
        min_n: Minimum required sample size (default 85 per Plan override).
        
    Returns:
        True if sample size is sufficient.
        
    Raises:
        DataValidationError: If N < min_n.
    """
    n = len(df)
    if n < min_n:
        raise DataValidationError(
            f"ERR_UNDERPOWERED: Sample size N={n} is below the required minimum of {min_n}. "
            f"The study is underpowered. Please ensure the dataset contains at least {min_n} subjects.",
            code="ERR_UNDERPOWERED"
        )
    logger.info(f"Sample size validation passed: N={n} >= {min_n}")
    return True

def get_behavioral_variable(df: pd.DataFrame, primary_var: str = 'musical_genre', 
                            fallback_var: str = 'STOMP-R') -> Tuple[str, bool]:
    """
    Attempt to locate the primary behavioral variable, with fallback to a proxy.
    
    This implements the 'Fail Loudly' mechanism for missing data while preserving
    the fallback logic for variable substitution.
    
    Args:
        df: DataFrame containing subject data (participants.tsv).
        primary_var: The primary variable name to check (e.g., 'musical_genre').
        fallback_var: The fallback variable name to check if primary is missing (e.g., 'STOMP-R').
        
    Returns:
        A tuple (variable_name, used_fallback).
        
    Raises:
        DataValidationError: If neither variable is found.
    """
    columns = df.columns.tolist()
    
    # Check primary variable
    if primary_var in columns:
        logger.info(f"Found primary behavioral variable: '{primary_var}'")
        return primary_var, False
    
    # Log warning for missing primary
    logger.warning(f"Primary behavioral variable '{primary_var}' not found. "
                   f"Attempting fallback to '{fallback_var}'...")
    
    # Check fallback variable
    if fallback_var in columns:
        logger.warning(f"Fallback variable '{fallback_var}' found. Using '{fallback_var}' as proxy.")
        return fallback_var, True
    
    # Both missing - Fail Loudly
    raise DataValidationError(
        f"ERR_DATA_MISSING: Neither '{primary_var}' nor '{fallback_var}' found in participants.tsv. "
        f"Available columns: {columns}. The pipeline cannot proceed without a valid behavioral measure.",
        code="ERR_DATA_MISSING"
    )

def exclude_subjects_by_missing_data(confounds_df: pd.DataFrame, threshold: float = 0.1) -> List[str]:
    """
    Flag subjects with excessive missing data in confounds.
    
    Args:
        confounds_df: DataFrame of confound regressors.
        threshold: Fraction of missing values allowed (default 0.1).
        
    Returns:
        List of subject IDs to exclude.
    """
    excluded = []
    # Assuming index or a column 'participant_id' exists
    subjects = confounds_df.index if isinstance(confounds_df.index, pd.Index) else confounds_df['participant_id']
    
    for subj in subjects:
        if isinstance(confounds_df.index, pd.Index):
            row = confounds_df.loc[subj]
        else:
            row = confounds_df[confounds_df['participant_id'] == subj].iloc[0]
        
        missing_ratio = row.isna().mean()
        if missing_ratio > threshold:
            excluded.append(subj)
            logger.warning(f"Excluding subject {subj}: {missing_ratio:.2%} missing confound data.")
    
    return excluded

def exclude_subjects_by_motion(confounds_df: pd.DataFrame, fd_threshold: float = 0.5) -> List[str]:
    """
    Flag subjects with excessive head motion (FD > threshold).
    
    Args:
        confounds_df: DataFrame of confound regressors (must contain 'framewise_displacement').
        fd_threshold: Maximum allowed mean FD (default 0.5mm).
        
    Returns:
        List of subject IDs to exclude.
    """
    excluded = []
    if 'framewise_displacement' not in confounds_df.columns:
        logger.warning("framewise_displacement column not found in confounds. Skipping motion check.")
        return excluded
    
    # Calculate mean FD per subject if multiple rows per subject, otherwise check mean
    if 'participant_id' in confounds_df.columns:
        mean_fd = confounds_df.groupby('participant_id')['framewise_displacement'].mean()
        for subj, fd in mean_fd.items():
            if fd > fd_threshold:
                excluded.append(subj)
                logger.warning(f"Excluding subject {subj}: Mean FD={fd:.3f}mm > {fd_threshold}mm.")
    else:
        # Assume single row per subject or aggregate
        mean_fd = confounds_df['framewise_displacement'].mean()
        if mean_fd > fd_threshold:
            logger.warning(f"Overall mean FD={mean_fd:.3f}mm > {fd_threshold}mm. Consider excluding all subjects.")
            # In a real scenario, we'd list specific subjects, but here we assume aggregate or index-based
            if isinstance(confounds_df.index, pd.Index):
                excluded.extend(confounds_df.index.tolist())
    
    return excluded

def check_data_integrity(dataset_dir: str, min_n: int = 85) -> List[str]:
    """
    Perform comprehensive data integrity checks.
    
    1. Verify participants.tsv exists.
    2. Validate sample size N >= min_n.
    3. Locate behavioral variable (primary or fallback).
    4. (Placeholder for confounds checks if files available).
    
    Args:
        dataset_dir: Path to the BIDS dataset root.
        min_n: Minimum sample size requirement.
        
    Returns:
        List of valid subject IDs (if confounds are available, otherwise empty list).
        
    Raises:
        DataValidationError: If any critical check fails.
    """
    dataset_path = Path(dataset_dir)
    valid_subjects = []
    
    # 1. File Existence Check
    participants_path = check_participants_file(dataset_path)
    df = pd.read_csv(participants_path, sep='\t')
    
    # 2. Power Check
    validate_sample_size(df, min_n)
    
    # 3. Variable Validation (Primary + Fallback)
    var_name, used_fallback = get_behavioral_variable(df, primary_var='musical_genre', fallback_var='STOMP-R')
    if used_fallback:
        logger.info(f"Proceeding with proxy variable: {var_name}")
    
    # 4. & 5. Confounds checks (if confounds files exist)
    # Note: This step assumes confounds files are available in the dataset structure.
    # In a real pipeline, we would iterate over subject directories to load confounds.
    # For this validation task, we return the list of subjects from participants.tsv
    # assuming they pass initial checks, pending specific confounds file validation.
    if 'participant_id' in df.columns:
        valid_subjects = df['participant_id'].tolist()
    elif 'subject_id' in df.columns:
        valid_subjects = df['subject_id'].tolist()
    else:
        # Fallback to index if no explicit ID column
        valid_subjects = [str(i) for i in range(len(df))]
    
    logger.info(f"Data integrity check passed for {len(valid_subjects)} subjects.")
    return valid_subjects

def main():
    """
    CLI entry point for data validation.
    Usage: python -m code.data.validate --dataset /path/to/ds000030
    """
    import argparse
    
    parser = argparse.ArgumentParser(description="Validate fMRI dataset integrity.")
    parser.add_argument("--dataset", type=str, required=True, help="Path to BIDS dataset")
    parser.add_argument("--min-n", type=int, default=85, help="Minimum sample size")
    
    args = parser.parse_args()
    
    try:
        valid_subjects = check_data_integrity(args.dataset, min_n=args.min_n)
        print(f"Validation successful. {len(valid_subjects)} subjects are valid.")
        # In a real pipeline, we might write this to a state file or return it
        return valid_subjects
    except DataValidationError as e:
        logger.error(f"Validation failed: {e.message} (Code: {e.code})")
        raise
    except FileNotFoundError as e:
        logger.error(f"File error: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise

if __name__ == "__main__":
    main()