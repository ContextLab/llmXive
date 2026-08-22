"""
Behavioral data validation and exclusion handling.

This module handles the loading, validation, and exclusion of subjects
based on missing behavioral scores (specifically the NIH Toolbox 
Dimensional Change Card Sort scores).
"""
import os
import logging
import pandas as pd
from typing import List, Optional, Tuple, Dict, Any

from code.data.paths import get_processed_path, ensure_dir
from code.utils.logging import log_exclusion, get_exclusion_log_path

logger = logging.getLogger(__name__)

# Column names for the exclusion log
EXCLUSION_LOG_COLUMNS = ['Subject_ID', 'Exclusion_Reason', 'Mean_FD']

def load_behavioral_scores(behavioral_csv_path: str) -> pd.DataFrame:
    """
    Load behavioral scores from a CSV file.
    
    Args:
        behavioral_csv_path: Path to the behavioral CSV file.
        
    Returns:
        DataFrame containing behavioral scores with at least 'Subject_ID' 
        and 'Flexibility_Score' columns.
        
    Raises:
        FileNotFoundError: If the behavioral CSV file does not exist.
        ValueError: If required columns are missing.
    """
    if not os.path.exists(behavioral_csv_path):
        raise FileNotFoundError(f"Behavioral CSV not found at {behavioral_csv_path}")
    
    df = pd.read_csv(behavioral_csv_path)
    
    # Validate required columns
    required_cols = ['Subject_ID', 'Flexibility_Score']
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        raise ValueError(f"Behavioral CSV missing required columns: {missing_cols}")
    
    logger.info(f"Loaded {len(df)} behavioral records from {behavioral_csv_path}")
    return df

def identify_missing_scores(neuro_df: pd.DataFrame, behavioral_df: pd.DataFrame) -> List[str]:
    """
    Identify subjects present in neuro data but missing behavioral scores.
    
    Args:
        neuro_df: DataFrame with neuroimaging data (must have 'Subject_ID').
        behavioral_df: DataFrame with behavioral data (must have 'Subject_ID').
        
    Returns:
        List of Subject_IDs that are in neuro_df but missing from behavioral_df
        or have NaN Flexibility_Score.
    """
    neuro_subjects = set(neuro_df['Subject_ID'].astype(str).unique())
    behavioral_subjects = set(behavioral_df['Subject_ID'].astype(str).unique())
    
    # Find subjects in neuro but not in behavioral
    missing_subjects = neuro_subjects - behavioral_subjects
    
    # Also check for subjects with NaN scores in behavioral
    if 'Flexibility_Score' in behavioral_df.columns:
        null_score_subjects = set(
            behavioral_df[behavioral_df['Flexibility_Score'].isna()]['Subject_ID'].astype(str)
        )
        missing_subjects.update(null_score_subjects)
    
    logger.info(f"Identified {len(missing_subjects)} subjects with missing behavioral scores")
    return list(missing_subjects)

def log_missing_score_exclusions(missing_subject_ids: List[str], mean_fd_values: Optional[Dict[str, float]] = None) -> None:
    """
    Log exclusions due to missing behavioral scores to the exclusion log CSV.
    
    This function appends rows to the exclusion log with:
    - Subject_ID: The ID of the excluded subject
    - Exclusion_Reason: "Missing_Behavioral_Score"
    - Mean_FD: The Mean FD value if available, otherwise empty/NaN
    
    Args:
        missing_subject_ids: List of Subject_IDs to exclude.
        mean_fd_values: Optional dict mapping Subject_ID to Mean_FD value.
    """
    if not missing_subject_ids:
        logger.info("No subjects to log for missing behavioral scores")
        return
    
    exclusion_log_path = get_exclusion_log_path()
    ensure_dir(exclusion_log_path)
    
    # Prepare data for new rows
    new_rows = []
    for subject_id in missing_subject_ids:
        fd_val = mean_fd_values.get(subject_id) if mean_fd_values else None
        new_rows.append({
            'Subject_ID': subject_id,
            'Exclusion_Reason': 'Missing_Behavioral_Score',
            'Mean_FD': fd_val
        })
    
    new_df = pd.DataFrame(new_rows, columns=EXCLUSION_LOG_COLUMNS)
    
    # Append to existing log if it exists, otherwise create new
    if os.path.exists(exclusion_log_path):
        existing_df = pd.read_csv(exclusion_log_path)
        # Ensure consistent column order
        existing_df = existing_df.reindex(columns=EXCLUSION_LOG_COLUMNS)
        combined_df = pd.concat([existing_df, new_df], ignore_index=True)
    else:
        combined_df = new_df
    
    combined_df.to_csv(exclusion_log_path, index=False)
    logger.info(f"Logged {len(new_rows)} missing behavioral score exclusions to {exclusion_log_path}")
    
    # Log individual exclusions
    for row in new_rows.itertuples():
        log_exclusion(row.Subject_ID, row.Exclusion_Reason, row.Mean_FD)

def filter_missing_scores(df: pd.DataFrame, missing_subject_ids: List[str]) -> pd.DataFrame:
    """
    Filter a DataFrame to remove subjects with missing behavioral scores.
    
    Args:
        df: Input DataFrame with 'Subject_ID' column.
        missing_subject_ids: List of Subject_IDs to exclude.
        
    Returns:
        Filtered DataFrame with missing subjects removed.
    """
    if not missing_subject_ids:
        return df
    
    missing_set = set(missing_subject_ids)
    filtered_df = df[~df['Subject_ID'].astype(str).isin(missing_set)].reset_index(drop=True)
    
    logger.info(f"Filtered {len(missing_subject_ids)} subjects with missing scores. "
               f"Remaining: {len(filtered_df)} subjects")
    return filtered_df

def run_behavioral_validation_pipeline(neuro_df: pd.DataFrame, behavioral_df: pd.DataFrame, 
                                     mean_fd_dict: Optional[Dict[str, float]] = None) -> Tuple[pd.DataFrame, List[str]]:
    """
    Run the full behavioral validation pipeline:
    1. Identify subjects with missing behavioral scores
    2. Log them to the exclusion log
    3. Filter them from the neuro data
    
    Args:
        neuro_df: DataFrame with neuroimaging data.
        behavioral_df: DataFrame with behavioral data.
        mean_fd_dict: Optional dict mapping Subject_ID to Mean_FD for logging.
        
    Returns:
        Tuple of (filtered_neuro_df, list_of_excluded_subject_ids)
    """
    logger.info("Starting behavioral validation pipeline")
    
    # Identify missing
    missing_ids = identify_missing_scores(neuro_df, behavioral_df)
    
    if missing_ids:
        # Log exclusions
        log_missing_score_exclusions(missing_ids, mean_fd_dict)
        
        # Filter
        filtered_df = filter_missing_scores(neuro_df, missing_ids)
    else:
        filtered_df = neuro_df
        logger.info("No subjects missing behavioral scores")
    
    logger.info("Behavioral validation pipeline complete")
    return filtered_df, missing_ids