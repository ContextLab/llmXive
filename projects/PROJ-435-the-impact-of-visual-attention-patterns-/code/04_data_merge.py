import os
import sys
import logging
import json
from pathlib import Path
from typing import Dict, Any, List
import pandas as pd
import numpy as np

# Add project root to path for imports if running as script
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from utils.environment_manager import load_config, get_paths, setup_reproducibility

# Configure logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

class DataMissingError(Exception):
    """Raised when required data columns are missing."""
    pass

def load_gaze_data(gaze_path: Path) -> pd.DataFrame:
    """
    Load preprocessed gaze data.
    Validates required columns: participant_id, headline_id, fixation_duration, roi_type.
    """
    if not gaze_path.exists():
        raise FileNotFoundError(f"Gaze data file not found: {gaze_path}")
    
    df = pd.read_csv(gaze_path)
    required_cols = ['participant_id', 'headline_id', 'fixation_duration', 'roi_type']
    missing_cols = [col for col in required_cols if col not in df.columns]
    
    if missing_cols:
        raise DataMissingError(f"Missing required columns in gaze data: {missing_cols}")
    
    logger.info(f"Loaded gaze data: {len(df)} rows, columns: {list(df.columns)}")
    return df

def load_empirical_outcomes(empirical_path: Path) -> pd.DataFrame:
    """
    Load empirical outcomes data.
    Expected columns: participant_id, headline_id, belief_rating, headline_text.
    """
    if not empirical_path.exists():
        raise FileNotFoundError(f"Empirical outcomes file not found: {empirical_path}")
    
    df = pd.read_csv(empirical_path)
    required_cols = ['participant_id', 'headline_id', 'belief_rating', 'headline_text']
    missing_cols = [col for col in required_cols if col not in df.columns]
    
    if missing_cols:
        raise DataMissingError(f"Missing required columns in empirical outcomes: {missing_cols}")
    
    logger.info(f"Loaded empirical outcomes: {len(df)} rows")
    return df

def load_valence_scores(valence_path: Path) -> pd.DataFrame:
    """
    Load valence scores data.
    Expected columns: headline_id, valence_score (or similar, verified at merge).
    """
    if not valence_path.exists():
        raise FileNotFoundError(f"Valence scores file not found: {valence_path}")
    
    df = pd.read_csv(valence_path)
    required_cols = ['headline_id', 'valence_score']
    missing_cols = [col for col in required_cols if col not in df.columns]
    
    if missing_cols:
        # Fallback check if column name differs slightly, though spec says valence_score
        if 'headline_id' not in df.columns:
            raise DataMissingError(f"Missing required column 'headline_id' in valence scores")
        # Assume the second column is the score if named differently
        score_col = [c for c in df.columns if c != 'headline_id'][0]
        df = df.rename(columns={score_col: 'valence_score'})
        logger.warning(f"Renamed column '{score_col}' to 'valence_score' in valence data")
    
    logger.info(f"Loaded valence scores: {len(df)} rows")
    return df

def load_crt_scores(empirical_path: Path) -> pd.DataFrame:
    """
    Extract CRT scores from the empirical outcomes file.
    The empirical outcomes file is expected to have 'cognitive_reflection_score' or similar.
    If not present, we might need to load from a separate source, but spec implies it's in the outcome stream.
    Checking standard spec columns: participant_id, headline_id, belief_rating, headline_text.
    Wait, T004b output is `participant_id`, `headline_id`, `belief_rating`, `headline_text`.
    Where is CRT?
    Looking at T024 model formula: `belief_rating ~ fixation_duration * valence * crt ...`
    And T023 description: "Immediately apply outlier capping to `cognitive_reflection_score`".
    This implies `cognitive_reflection_score` MUST be in the merged dataset.
    It is likely part of the participant-level data.
    Let's check T007 (Participant model): `crt_score`.
    If T004b didn't include it, we need to find it.
    However, T004b description says: "Output `data/derived/empirical_outcomes.csv` containing `participant_id`, `headline_id`, `belief_rating`, and `headline_text`."
    It does NOT explicitly mention CRT.
    But T023 says: "Immediately apply outlier capping to `cognitive_reflection_score`".
    This implies the data MUST be present.
    Assumption: The raw data or T004b logic includes `cognitive_reflection_score` per participant,
    or it is in `empirical_outcomes.csv` despite the brief description.
    If not, we must look for it.
    Given the strict requirement, I will check if it exists in the empirical outcomes.
    If not, I will assume it's a participant-level attribute that needs to be joined.
    However, without a separate participant file path provided in T023, I must rely on the inputs.
    Let's assume `cognitive_reflection_score` is present in `empirical_outcomes.csv` or `preprocessed_gaze.csv`
    (as a participant attribute).
    If missing, we raise an error as per "Schema Validation".
    """
    # Re-loading empirical outcomes to check for CRT
    df = pd.read_csv(empirical_path)
    if 'cognitive_reflection_score' not in df.columns:
        # Try to find if it's named differently
        possible_names = ['crt_score', 'crt', 'cognitive_reflection']
        found = None
        for name in possible_names:
            if name in df.columns:
                found = name
                break
        
        if found:
            df = df.rename(columns={found: 'cognitive_reflection_score'})
            logger.warning(f"Renamed column '{found}' to 'cognitive_reflection_score'")
        else:
            # If still not found, we must check if we have a separate participant file or if it's missing
            # The task description for T004b did NOT list it, but T023 REQUIRES it.
            # This is a dependency gap. However, the task says "Verify ... If missing, raise DataMissingError".
            raise DataMissingError("Missing required column 'cognitive_reflection_score' in empirical outcomes. "
                                 "This column is required for the merge and outlier capping as per T023.")
    
    return df

def merge_datasets(gaze_df: pd.DataFrame, empirical_df: pd.DataFrame, valence_df: pd.DataFrame) -> pd.DataFrame:
    """
    Merge the three data streams on participant_id and headline_id.
    """
    # First, merge gaze and empirical
    # Ensure dtypes match for join keys
    gaze_df = gaze_df.copy()
    empirical_df = empirical_df.copy()
    
    # Convert join keys to string to avoid type mismatches
    for key in ['participant_id', 'headline_id']:
        gaze_df[key] = gaze_df[key].astype(str)
        empirical_df[key] = empirical_df[key].astype(str)
    
    merged = pd.merge(gaze_df, empirical_df, on=['participant_id', 'headline_id'], how='inner')
    logger.info(f"After Gaze+Empirical merge: {len(merged)} rows")
    
    # Merge with valence
    valence_df = valence_df.copy()
    valence_df['headline_id'] = valence_df['headline_id'].astype(str)
    
    merged = pd.merge(merged, valence_df, on='headline_id', how='left')
    logger.info(f"After Valence merge: {len(merged)} rows")
    
    # Check for missing valence scores
    if merged['valence_score'].isna().any():
        logger.warning(f"{merged['valence_score'].isna().sum()} rows have missing valence scores")
    
    return merged

def apply_outlier_capping(df: pd.DataFrame, column: str = 'cognitive_reflection_score') -> pd.DataFrame:
    """
    Apply outlier capping to the specified column at 1st and 99th percentiles.
    """
    if column not in df.columns:
        raise DataMissingError(f"Column '{column}' not found for outlier capping")
    
    lower = df[column].quantile(0.01)
    upper = df[column].quantile(0.99)
    
    original_mean = df[column].mean()
    original_std = df[column].std()
    
    df[column] = df[column].clip(lower=lower, upper=upper)
    
    new_mean = df[column].mean()
    new_std = df[column].std()
    
    logger.info(f"Capped {column}: 1st%={lower:.4f}, 99th%={upper:.4f}")
    logger.info(f"Mean changed from {original_mean:.4f} to {new_mean:.4f}")
    logger.info(f"Std changed from {original_std:.4f} to {new_std:.4f}")
    
    return df

def main():
    """
    Main execution for T023: Data Merge.
    """
    config = load_config()
    paths = get_paths()
    
    # Define input paths
    gaze_path = paths['derived'] / 'preprocessed_gaze.csv'
    empirical_path = paths['derived'] / 'empirical_outcomes.csv'
    valence_path = paths['derived'] / 'valence_scores.csv'
    
    # Define output path
    output_path = paths['derived'] / 'merged_dataset.csv'
    
    logger.info(f"Starting data merge task T023")
    logger.info(f"Input Gaze: {gaze_path}")
    logger.info(f"Input Empirical: {empirical_path}")
    logger.info(f"Input Valence: {valence_path}")
    logger.info(f"Output: {output_path}")
    
    try:
        # 1. Load Data
        logger.info("Loading Gaze data...")
        gaze_df = load_gaze_data(gaze_path)
        
        logger.info("Loading Empirical outcomes...")
        # We need CRT scores, so we load and verify presence
        empirical_df = load_crt_scores(empirical_path)
        # Ensure belief_rating and headline_text are also present (from T004b)
        if 'belief_rating' not in empirical_df.columns or 'headline_text' not in empirical_df.columns:
             raise DataMissingError("Empirical outcomes missing 'belief_rating' or 'headline_text'")
        
        logger.info("Loading Valence scores...")
        valence_df = load_valence_scores(valence_path)
        
        # 2. Merge Datasets
        logger.info("Merging datasets...")
        merged_df = merge_datasets(gaze_df, empirical_df, valence_df)
        
        # 3. Apply Outlier Capping
        logger.info("Applying outlier capping to cognitive_reflection_score...")
        merged_df = apply_outlier_capping(merged_df, 'cognitive_reflection_score')
        
        # 4. Save Output
        output_path.parent.mkdir(parents=True, exist_ok=True)
        merged_df.to_csv(output_path, index=False)
        
        logger.info(f"Successfully wrote merged dataset to {output_path}")
        logger.info(f"Final shape: {merged_df.shape}")
        logger.info(f"Columns: {list(merged_df.columns)}")
        
    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        sys.exit(1)
    except DataMissingError as e:
        logger.error(f"Data schema error: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error during merge: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()