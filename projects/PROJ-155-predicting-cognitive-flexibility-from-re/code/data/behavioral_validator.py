"""
Module to handle validation of behavioral scores and logging exclusions.
Implements T017: Error handling for missing behavioral scores.
"""
import os
import logging
import pandas as pd
from typing import List, Optional, Tuple, Dict, Any

from code.data.paths import get_processed_path, ensure_dir
from code.utils.logging import log_exclusion, get_exclusion_log_path

logger = logging.getLogger(__name__)

def load_behavioral_scores(behavioral_data_path: str) -> pd.DataFrame:
    """
    Load behavioral data from a CSV file.
    
    Args:
        behavioral_data_path: Path to the behavioral CSV file.
        
    Returns:
        DataFrame containing behavioral scores.
    """
    if not os.path.exists(behavioral_data_path):
        raise FileNotFoundError(f"Behavioral data file not found: {behavioral_data_path}")
    
    df = pd.read_csv(behavioral_data_path)
    logger.info(f"Loaded behavioral data from {behavioral_data_path}: {len(df)} rows")
    return df

def identify_missing_scores(merged_df: pd.DataFrame, score_column: str = 'Flexibility_Score') -> List[str]:
    """
    Identify subjects with missing behavioral scores.
    
    Args:
        merged_df: DataFrame containing merged neuro and behavioral data.
        score_column: Name of the column containing the flexibility score.
        
    Returns:
        List of Subject_IDs with missing scores.
    """
    missing_mask = merged_df[score_column].isna() | (merged_df[score_column] == '')
    missing_subjects = merged_df.loc[missing_mask, 'Subject_ID'].tolist()
    logger.info(f"Identified {len(missing_subjects)} subjects with missing behavioral scores")
    return missing_subjects

def log_missing_score_exclusions(missing_subjects: List[str], exclusion_log_path: Optional[str] = None) -> None:
    """
    Log exclusions for missing behavioral scores to the exclusion log.
    
    Args:
        missing_subjects: List of Subject_IDs to exclude.
        exclusion_log_path: Optional path to the exclusion log file. 
                            If None, uses the default path from utils.logging.
    """
    if not missing_subjects:
        logger.info("No missing behavioral scores to log.")
        return

    if exclusion_log_path is None:
        exclusion_log_path = get_exclusion_log_path()
    
    ensure_dir(os.path.dirname(exclusion_log_path))

    # Check if file exists to determine if we need headers
    file_exists = os.path.exists(exclusion_log_path)
    
    with open(exclusion_log_path, 'a', newline='') as f:
        writer = csv.writer(f)
        
        if not file_exists:
            # Write header
            writer.writerow(['Subject_ID', 'Exclusion_Reason', 'Mean_FD'])
        
        for subject_id in missing_subjects:
            # Mean_FD is N/A for behavioral exclusions, but column must exist
            writer.writerow([subject_id, 'Missing_Behavioral_Score', 'N/A'])
    
    logger.info(f"Logged {len(missing_subjects)} exclusions for missing behavioral scores to {exclusion_log_path}")

def filter_missing_scores(merged_df: pd.DataFrame, score_column: str = 'Flexibility_Score', 
                          exclusion_log_path: Optional[str] = None) -> pd.DataFrame:
    """
    Filter out subjects with missing behavioral scores and log the exclusions.
    
    This function implements the core logic for T017:
    1. Identifies subjects with missing scores
    2. Logs them to exclusion_log.csv with reason "Missing_Behavioral_Score"
    3. Returns the filtered DataFrame
    
    Args:
        merged_df: DataFrame containing merged neuro and behavioral data.
        score_column: Name of the column containing the flexibility score.
        exclusion_log_path: Optional path to the exclusion log file.
        
    Returns:
        Filtered DataFrame with subjects having valid behavioral scores.
    """
    initial_count = len(merged_df)
    missing_subjects = identify_missing_scores(merged_df, score_column)
    
    if missing_subjects:
        log_missing_score_exclusions(missing_subjects, exclusion_log_path)
        filtered_df = merged_df.drop(merged_df[merged_df['Subject_ID'].isin(missing_subjects)].index)
        logger.info(f"Dropped {len(missing_subjects)} subjects due to missing behavioral scores.")
        logger.info(f"Remaining subjects: {len(filtered_df)}")
        return filtered_df
    else:
        logger.info("All subjects have valid behavioral scores.")
        return merged_df

def run_behavioral_validation_pipeline(merged_df: pd.DataFrame, 
                                       score_column: str = 'Flexibility_Score',
                                       exclusion_log_path: Optional[str] = None) -> pd.DataFrame:
    """
    Run the complete behavioral validation pipeline.
    
    Args:
        merged_df: Input merged DataFrame.
        score_column: Column name for flexibility score.
        exclusion_log_path: Optional custom path for exclusion log.
        
    Returns:
        Filtered DataFrame ready for downstream analysis.
    """
    logger.info("Starting behavioral validation pipeline...")
    filtered_df = filter_missing_scores(merged_df, score_column, exclusion_log_path)
    logger.info("Behavioral validation pipeline completed.")
    return filtered_df
