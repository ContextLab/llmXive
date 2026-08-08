"""
Module: code/04_data_merge.py
Task: T023 [US2] Data Merge and Outlier Capping
Description: Merges Gaze, Empirical, and Valence streams, validates schemas, and applies outlier capping.
"""
import os
import sys
import logging
import json
from pathlib import Path
from typing import Dict, Any, List

import pandas as pd
import numpy as np

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def get_project_root() -> Path:
    """Returns the project root directory (parent of 'code')."""
    return Path(__file__).resolve().parent.parent

class DataMissingError(Exception):
    """Custom exception for missing data columns."""
    pass

def load_gaze_data() -> pd.DataFrame:
    """
    Loads the preprocessed gaze data from T018.
    Input: data/derived/preprocessed_gaze.csv
    """
    project_root = get_project_root()
    path = project_root / "data" / "derived" / "preprocessed_gaze.csv"
    
    if not path.exists():
        raise FileNotFoundError(f"Gaze data file not found at {path}. Ensure T018 has run.")
    
    logger.info(f"Loading gaze data from {path}")
    df = pd.read_csv(path)
    return df

def load_empirical_outcomes() -> pd.DataFrame:
    """
    Loads the empirical outcomes (belief ratings) from T004b.
    Input: data/derived/empirical_outcomes.csv
    """
    project_root = get_project_root()
    path = project_root / "data" / "derived" / "empirical_outcomes.csv"
    
    if not path.exists():
        raise FileNotFoundError(f"Empirical outcomes file not found at {path}. Ensure T004b has run.")
    
    logger.info(f"Loading empirical outcomes from {path}")
    df = pd.read_csv(path)
    return df

def load_valence_scores() -> pd.DataFrame:
    """
    Loads the valence scores from T021.
    Input: data/derived/valence_scores.csv
    """
    project_root = get_project_root()
    path = project_root / "data" / "derived" / "valence_scores.csv"
    
    if not path.exists():
        raise FileNotFoundError(f"Valence scores file not found at {path}. Ensure T021 has run.")
    
    logger.info(f"Loading valence scores from {path}")
    df = pd.read_csv(path)
    return df

def load_crt_scores(empirical_df: pd.DataFrame) -> pd.DataFrame:
    """
    Extracts or loads Cognitive Reflection Test (CRT) scores.
    Depending on the source data structure, CRT might be in the empirical outcomes
    or a separate participant file. We assume it is present in the empirical
    outcomes or derived from participant data available in the merged stream.
    For this task, we assume 'cognitive_reflection_score' is available in the
    empirical stream or needs to be joined.
    
    Based on T007 (models), we expect a Participant entity.
    If the empirical outcomes do not have CRT, we look for a participant mapping.
    However, T004b output is described as 'participant_id', 'headline_id', 'belief_rating'.
    We assume the raw data or a derived participant file exists, OR the CRT score
    is repeated in the empirical outcomes.
    
    Let's check if 'cognitive_reflection_score' is in empirical_df.
    If not, we try to load a participant file if it exists (T007 might have generated one).
    """
    if 'cognitive_reflection_score' in empirical_df.columns:
        logger.info("CRT score found in empirical outcomes.")
        return empirical_df
    
    # Fallback: Try to load participant data if it exists
    project_root = get_project_root()
    participant_path = project_root / "data" / "derived" / "participant_scores.csv"
    
    if participant_path.exists():
        logger.info("CRT score not in empirical outcomes, loading from participant_scores.csv")
        p_df = pd.read_csv(participant_path)
        # Merge if necessary, but for now we return empirical_df and let the merge logic handle it
        # Actually, we need to attach it to the empirical_df before the main merge?
        # The task says "Merge the Gaze stream, Empirical stream, and Valence stream".
        # If CRT is in a separate file, we should merge it into empirical_df first.
        if 'participant_id' in p_df.columns and 'cognitive_reflection_score' in p_df.columns:
            empirical_df = empirical_df.merge(
                p_df[['participant_id', 'cognitive_reflection_score']], 
                on='participant_id', 
                how='left'
            )
            logger.info(f"Merged CRT scores from {participant_path}")
            return empirical_df
    
    # If still missing, we might need to raise an error or assume a default?
    # The spec says "crt" is continuous and part of the model.
    # If it's missing, the regression will fail.
    # Let's assume for now that the raw data had it and T004b extracted it.
    # If not, we raise a warning but proceed, hoping it's in the gaze data?
    # Gaze data (T018) has participant_id.
    # Let's check if it's in the gaze data.
    logger.warning("CRT score not found in expected locations. Checking gaze data...")
    return None # Will be handled in merge or raise error later

def validate_schema(df: pd.DataFrame, required_cols: List[str], source_name: str) -> None:
    """
    Validates that a DataFrame contains required columns.
    Raises DataMissingError if any are missing.
    """
    missing = [col for col in required_cols if col not in df.columns]
    if missing:
        raise DataMissingError(
            f"Schema validation failed for {source_name}: "
            f"Missing columns: {missing}"
        )
    logger.info(f"Schema validation passed for {source_name}")

def merge_datasets(gaze_df: pd.DataFrame, empirical_df: pd.DataFrame, valence_df: pd.DataFrame) -> pd.DataFrame:
    """
    Merges the three streams on participant_id and headline_id.
    """
    logger.info("Merging datasets...")
    
    # 1. Merge Gaze and Empirical
    # Both should have participant_id and headline_id
    merged = gaze_df.merge(
        empirical_df, 
        on=['participant_id', 'headline_id'], 
        how='inner'
    )
    logger.info(f"Intermediate merge (Gaze + Empirical) shape: {merged.shape}")
    
    # 2. Merge with Valence
    # Valence should have headline_id (and possibly participant_id if calculated per trial)
    # Assuming valence is per headline_id based on T021 description
    merged = merged.merge(
        valence_df, 
        on='headline_id', 
        how='left' # Left join to keep all gaze/empirical pairs
    )
    logger.info(f"Final merge shape: {merged.shape}")
    
    return merged

def apply_outlier_capping(df: pd.DataFrame, column: str = 'cognitive_reflection_score') -> pd.DataFrame:
    """
    Applies outlier capping to the specified column at the 1st and 99th percentiles.
    Reference: Spec Edge Cases section.
    """
    if column not in df.columns:
        logger.warning(f"Column '{column}' not found in dataset. Skipping outlier capping.")
        return df
    
    logger.info(f"Applying outlier capping to '{column}' (1st and 99th percentiles).")
    
    lower_bound = df[column].quantile(0.01)
    upper_bound = df[column].quantile(0.99)
    
    logger.info(f"Capping range: [{lower_bound:.4f}, {upper_bound:.4f}]")
    
    df[column] = df[column].clip(lower=lower_bound, upper=upper_bound)
    
    return df

def main():
    """
    Main execution function for T023.
    """
    try:
        # 1. Load Data
        gaze_df = load_gaze_data()
        empirical_df = load_empirical_outcomes()
        valence_df = load_valence_scores()
        
        # 2. Validate Schemas
        # Gaze requirements
        validate_schema(gaze_df, ['participant_id', 'headline_id', 'fixation_duration', 'roi_type'], "Gaze Data")
        
        # Empirical requirements
        validate_schema(empirical_df, ['participant_id', 'headline_id', 'belief_rating'], "Empirical Data")
        
        # Valence requirements
        validate_schema(valence_df, ['headline_id', 'valence_score'], "Valence Data") # Assuming valence_score is the column
        
        # 3. Handle CRT Score
        # If not in empirical, try to attach from gaze or participant file
        if 'cognitive_reflection_score' not in empirical_df.columns:
            # Check if it's in gaze_df (sometimes participant metadata is repeated)
            if 'cognitive_reflection_score' in gaze_df.columns:
                logger.info("CRT score found in Gaze data, merging into Empirical...")
                # We need to merge this into empirical_df before the main merge
                # But empirical_df might have multiple rows per participant (one per headline)
                # So we group by participant_id in gaze_df to get unique CRT score?
                # Or assume it's constant per participant.
                crt_map = gaze_df[['participant_id', 'cognitive_reflection_score']].drop_duplicates()
                empirical_df = empirical_df.merge(crt_map, on='participant_id', how='left')
            else:
                logger.error("CRT score not found in Gaze or Empirical data. Cannot proceed with model.")
                raise DataMissingError("Missing 'cognitive_reflection_score' in input data.")
        
        # 4. Merge Datasets
        merged_df = merge_datasets(gaze_df, empirical_df, valence_df)
        
        # 5. Apply Outlier Capping
        merged_df = apply_outlier_capping(merged_df, 'cognitive_reflection_score')
        
        # 6. Save Output
        project_root = get_project_root()
        output_path = project_root / "data" / "derived" / "merged_dataset_full.csv"
        
        merged_df.to_csv(output_path, index=False)
        logger.info(f"Successfully wrote merged dataset to {output_path}")
        
        # Log summary
        logger.info(f"Final dataset shape: {merged_df.shape}")
        logger.info(f"Columns: {list(merged_df.columns)}")
        
    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        sys.exit(1)
    except DataMissingError as e:
        logger.error(f"Data Missing Error: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error during merge: {e}")
        raise

if __name__ == "__main__":
    main()