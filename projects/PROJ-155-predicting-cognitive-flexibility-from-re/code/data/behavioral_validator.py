import os
import logging
import pandas as pd
from typing import List, Optional, Tuple, Dict, Any
from code.data.paths import get_processed_path, ensure_dir
from code.utils.logging import log_exclusion, get_exclusion_log_path

logger = logging.getLogger(__name__)

def load_behavioral_scores(behavioral_csv_path: str) -> pd.DataFrame:
    """
    Load behavioral scores from a CSV file.
    
    Args:
        behavioral_csv_path: Path to the behavioral CSV file.
        
    Returns:
        DataFrame with behavioral scores.
    """
    if not os.path.exists(behavioral_csv_path):
        raise FileNotFoundError(f"Behavioral CSV not found at {behavioral_csv_path}")
    
    df = pd.read_csv(behavioral_csv_path)
    logger.info(f"Loaded {len(df)} rows from {behavioral_csv_path}")
    return df

def identify_missing_scores(merged_df: pd.DataFrame, score_column: str = "Flexibility_Score") -> List[str]:
    """
    Identify subjects with missing behavioral scores.
    
    Args:
        merged_df: Merged DataFrame with neuroimaging and behavioral data.
        score_column: Name of the column containing the flexibility score.
        
    Returns:
        List of Subject_IDs with missing scores.
    """
    missing_mask = merged_df[score_column].isna()
    missing_subjects = merged_df.loc[missing_mask, "Subject_ID"].tolist()
    logger.info(f"Identified {len(missing_subjects)} subjects with missing {score_column}")
    return missing_subjects

def log_missing_score_exclusions(missing_subjects: List[str], exclusion_log_path: Optional[str] = None) -> None:
    """
    Log excluded subjects due to missing behavioral scores to the exclusion log CSV.
    
    This function appends a row for each missing subject to the exclusion log with:
    - Subject_ID: The ID of the excluded subject
    - Exclusion_Reason: "Missing_Behavioral_Score"
    - Mean_FD: Empty/NaN (since this is not a motion exclusion)
    
    Args:
        missing_subjects: List of Subject_IDs to exclude.
        exclusion_log_path: Path to the exclusion log CSV. If None, uses default path.
    """
    if not missing_subjects:
        logger.info("No missing subjects to log.")
        return
    
    if exclusion_log_path is None:
        exclusion_log_path = get_exclusion_log_path()
    
    ensure_dir(exclusion_log_path)
    
    # Create exclusion records
    exclusion_records = []
    for sub_id in missing_subjects:
        exclusion_records.append({
            "Subject_ID": sub_id,
            "Exclusion_Reason": "Missing_Behavioral_Score",
            "Mean_FD": ""  # Empty for non-motion exclusions
        })
    
    new_df = pd.DataFrame(exclusion_records)
    
    # Load existing log if it exists
    if os.path.exists(exclusion_log_path):
        existing_df = pd.read_csv(exclusion_log_path)
        combined_df = pd.concat([existing_df, new_df], ignore_index=True)
    else:
        combined_df = new_df
    
    # Write back to CSV
    combined_df.to_csv(exclusion_log_path, index=False)
    logger.info(f"Logged {len(missing_subjects)} missing score exclusions to {exclusion_log_path}")

def filter_missing_scores(merged_df: pd.DataFrame, score_column: str = "Flexibility_Score") -> Tuple[pd.DataFrame, List[str]]:
    """
    Filter out subjects with missing behavioral scores.
    
    Args:
        merged_df: Merged DataFrame.
        score_column: Name of the column containing the flexibility score.
        
    Returns:
        Tuple of (filtered DataFrame, list of excluded Subject_IDs).
    """
    missing_subjects = identify_missing_scores(merged_df, score_column)
    if missing_subjects:
        filtered_df = merged_df.dropna(subset=[score_column])
        logger.info(f"Dropped {len(missing_subjects)} subjects due to missing scores.")
        return filtered_df, missing_subjects
    return merged_df, []

def run_behavioral_validation_pipeline(merged_df: pd.DataFrame, 
                                       behavioral_csv_path: str,
                                       score_column: str = "Flexibility_Score") -> pd.DataFrame:
    """
    Run the full behavioral validation pipeline:
    1. Load behavioral scores (if needed, though merged_df should already have them)
    2. Identify missing scores
    3. Log exclusions to exclusion_log.csv
    4. Filter out missing subjects
    
    Args:
        merged_df: Merged DataFrame with neuroimaging and behavioral data.
        behavioral_csv_path: Path to original behavioral CSV (for reference).
        score_column: Name of the flexibility score column.
        
    Returns:
        Filtered DataFrame with only subjects having valid behavioral scores.
    """
    logger.info("Starting behavioral validation pipeline...")
    
    # Identify and log missing scores
    missing_subjects = identify_missing_scores(merged_df, score_column)
    if missing_subjects:
        log_missing_score_exclusions(missing_subjects)
    
    # Filter the DataFrame
    filtered_df, _ = filter_missing_scores(merged_df, score_column)
    
    logger.info(f"Behavioral validation complete. {len(filtered_df)} subjects remaining.")
    return filtered_df