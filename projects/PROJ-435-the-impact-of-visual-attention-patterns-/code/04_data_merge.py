import os
import sys
import logging
import json
from pathlib import Path
from typing import Dict, Any, List, Optional

import pandas as pd
import numpy as np

# Import logging setup from utils
try:
    from utils.logging_init import setup_global_logger, get_project_root
except ImportError:
    # Fallback if run as script without utils path setup
    def get_project_root():
        return Path(__file__).resolve().parent.parent
    
    def setup_global_logger():
        logging.basicConfig(level=logging.INFO)
        return logging.getLogger(__name__)

class DataMissingError(Exception):
    """Raised when required data columns or files are missing."""
    pass

def setup_logger(name: str = "data_merge") -> logging.Logger:
    """Configure and return the logger for this module."""
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    return logger

def load_gaze_data(path: Path, logger: logging.Logger) -> pd.DataFrame:
    """
    Load preprocessed gaze data.
    Expected columns: participant_id, headline_id, fixation_duration, roi_type
    """
    logger.info(f"Loading gaze data from {path}")
    if not path.exists():
        raise FileNotFoundError(f"Gaze data file not found: {path}")
    
    df = pd.read_csv(path)
    required_cols = ['participant_id', 'headline_id', 'fixation_duration', 'roi_type']
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        raise DataMissingError(f"Gaze data missing columns: {missing}")
    
    logger.info(f"Gaze data loaded: {len(df)} rows")
    return df

def load_empirical_outcomes(path: Path, logger: logging.Logger) -> pd.DataFrame:
    """
    Load empirical outcomes data.
    Expected columns: participant_id, headline_id, belief_rating, headline_text
    """
    logger.info(f"Loading empirical outcomes from {path}")
    if not path.exists():
        raise FileNotFoundError(f"Empirical outcomes file not found: {path}")
    
    df = pd.read_csv(path)
    required_cols = ['participant_id', 'headline_id', 'belief_rating', 'headline_text']
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        raise DataMissingError(f"Empirical outcomes missing columns: {missing}")
    
    logger.info(f"Empirical outcomes loaded: {len(df)} rows")
    return df

def load_valence_scores(path: Path, logger: logging.Logger) -> pd.DataFrame:
    """
    Load valence scores data.
    Expected columns: headline_id, valence_score
    """
    logger.info(f"Loading valence scores from {path}")
    if not path.exists():
        raise FileNotFoundError(f"Valence scores file not found: {path}")
    
    df = pd.read_csv(path)
    required_cols = ['headline_id', 'valence_score']
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        raise DataMissingError(f"Valence scores missing columns: {missing}")
    
    logger.info(f"Valence scores loaded: {len(df)} rows")
    return df

def load_crt_scores(path: Path, logger: logging.Logger) -> pd.DataFrame:
    """
    Load CRT scores.
    Note: The raw data or empirical outcomes might contain this.
    If not in empirical outcomes, we check if it exists in the raw data or a separate file.
    For this task, we assume it might be in the raw data or needs to be merged from a specific source.
    However, the task description for T023 does not explicitly list a CRT input file separate from the others,
    but the regression task T024 requires it.
    Looking at T004b (Empirical Outcomes), it extracts belief_rating and headline_text.
    If CRT is not in the empirical outcomes, we must find it.
    Let's assume for T023 we only merge the three specified streams.
    If CRT is needed for the merge (e.g. as a control), it should be in one of the inputs.
    The task description says: "Input Schemas: ... empirical_outcomes.csv (participant_id, headline_id, belief_rating, headline_text)".
    It does NOT list cognitive_reflection_score in the empirical outcomes schema in T023 description.
    However, T024 requires it.
    Let's check T005 (Data Loading) or T004b logic. T004b extracts from raw.
    If the raw data has it, T004b should have included it?
    The task T023 description says: "Immediately apply outlier capping to cognitive_reflection_score within this script".
    This implies the score IS present in the merged data.
    Therefore, we must ensure it is loaded.
    Since T004b output schema in T023 description is explicit and does NOT include CRT,
    we must look for CRT elsewhere or assume T004b was supposed to include it but the schema description in T023 was partial.
    OR, CRT is in the raw data and we need to load it separately.
    Let's assume the raw data (data/raw/eye_tracking_raw.parquet) contains 'cognitive_reflection_score' and we need to join it.
    But T023 says "Merge Gaze, Empirical, Valence".
    Let's re-read T023: "Input Schemas: ... empirical_outcomes.csv ... (participant_id, headline_id, belief_rating, headline_text)".
    If CRT is not there, and we need it, we must load it from the raw data or a separate participant-level file.
    Given the constraints, I will assume the 'empirical_outcomes.csv' should have contained it or we load it from raw.
    However, to be safe and strictly follow T023's input list, I will check if 'cognitive_reflection_score' is in the empirical outcomes.
    If not, I will attempt to load it from the raw data if available, or raise an error if the task requires it but it's missing.
    Actually, looking at T004b description: "extract the belief_rating and headline_text columns". It doesn't mention CRT.
    But T024 requires CRT.
    Let's assume the raw data has 'cognitive_reflection_score' per participant.
    I will add a step to load CRT from the raw data if it's not in the empirical outcomes.
    But T023 description doesn't list raw data as input.
    Let's assume the schema for empirical_outcomes in T023 is incomplete and it actually contains CRT, OR
    we load it from a separate file if it exists.
    Given the ambiguity, I will implement a robust check:
    1. Try to get CRT from empirical_outcomes.
    2. If not present, try to load from raw data (if path exists) and merge by participant_id.
    3. If still not found, raise DataMissingError.
    """
    # This function is not explicitly requested in T023's input list, but the logic requires CRT.
    # I will handle CRT loading within the merge logic to be safe.
    pass

def validate_schema(dfs: Dict[str, pd.DataFrame], logger: logging.Logger) -> None:
    """Validate that all DataFrames have required columns."""
    required = {
        'gaze': ['participant_id', 'headline_id', 'fixation_duration', 'roi_type'],
        'empirical': ['participant_id', 'headline_id', 'belief_rating', 'headline_text'],
        'valence': ['headline_id', 'valence_score']
    }
    for name, df in dfs.items():
        req_cols = required.get(name, [])
        missing = [c for c in req_cols if c not in df.columns]
        if missing:
            raise DataMissingError(f"{name} data missing required columns: {missing}")
    logger.info("All input schemas validated.")

def merge_datasets(gaze_df: pd.DataFrame, empirical_df: pd.DataFrame, valence_df: pd.DataFrame, logger: logging.Logger) -> pd.DataFrame:
    """
    Merge the three datasets on participant_id and headline_id.
    """
    # Merge Gaze and Empirical
    logger.info("Merging Gaze and Empirical datasets...")
    merged = pd.merge(
        gaze_df,
        empirical_df,
        on=['participant_id', 'headline_id'],
        how='inner'
    )
    logger.info(f"Intermediate merge result: {len(merged)} rows")

    # Merge with Valence
    logger.info("Merging with Valence scores...")
    merged = pd.merge(
        merged,
        valence_df,
        on='headline_id',
        how='left' # Valence is headline-level, might be missing if headline not in valence file
    )

    # Handle CRT Score
    # If CRT is not in empirical, we try to load from raw or assume it's missing (which will break T024)
    # T023 Logic: "Immediately apply outlier capping to cognitive_reflection_score"
    # This implies it MUST exist.
    if 'cognitive_reflection_score' not in merged.columns:
        # Try to load from raw data if available
        raw_path = get_project_root() / 'data' / 'raw' / 'eye_tracking_raw.parquet'
        if raw_path.exists():
            logger.info("CRT score not in empirical outcomes. Attempting to load from raw data...")
            try:
                raw_df = pd.read_parquet(raw_path)
                # Assume raw data has participant_id and cognitive_reflection_score
                if 'participant_id' in raw_df.columns and 'cognitive_reflection_score' in raw_df.columns:
                    # Aggregate by participant_id if multiple rows exist per participant
                    crt_map = raw_df.groupby('participant_id')['cognitive_reflection_score'].first().to_dict()
                    merged['cognitive_reflection_score'] = merged['participant_id'].map(crt_map)
                    logger.info("CRT score loaded from raw data.")
                else:
                    raise DataMissingError("Raw data does not contain required CRT columns.")
            except Exception as e:
                raise DataMissingError(f"Failed to load CRT from raw data: {e}")
        else:
            raise DataMissingError("cognitive_reflection_score missing from empirical outcomes and raw data not found.")

    logger.info(f"Merged dataset shape: {merged.shape}")
    return merged

def apply_outlier_capping(df: pd.DataFrame, logger: logging.Logger) -> pd.DataFrame:
    """
    Apply outlier capping to cognitive_reflection_score at 1st and 99th percentiles.
    """
    col = 'cognitive_reflection_score'
    if col not in df.columns:
        logger.warning(f"Column {col} not found, skipping outlier capping.")
        return df

    logger.info(f"Applying outlier capping to {col} at 1st and 99th percentiles.")
    lower = df[col].quantile(0.01)
    upper = df[col].quantile(0.99)
    
    original_mean = df[col].mean()
    df[col] = df[col].clip(lower=lower, upper=upper)
    new_mean = df[col].mean()
    
    logger.info(f"Capping range: [{lower:.4f}, {upper:.4f}]. Mean changed from {original_mean:.4f} to {new_mean:.4f}")
    return df

def main():
    logger = setup_logger()
    root = get_project_root()
    
    # Define paths
    gaze_path = root / 'data' / 'derived' / 'preprocessed_gaze.csv'
    empirical_path = root / 'data' / 'derived' / 'empirical_outcomes.csv'
    valence_path = root / 'data' / 'derived' / 'valence_scores.csv'
    output_path = root / 'data' / 'derived' / 'merged_dataset_full.csv'
    
    logger.info("Starting Data Merge (T023)...")
    
    try:
        # Load Data
        gaze_df = load_gaze_data(gaze_path, logger)
        empirical_df = load_empirical_outcomes(empirical_path, logger)
        valence_df = load_valence_scores(valence_path, logger)
        
        # Validate Schemas
        validate_datasets = {
            'gaze': gaze_df,
            'empirical': empirical_df,
            'valence': valence_df
        }
        validate_schema(validate_datasets, logger)
        
        # Merge
        merged_df = merge_datasets(gaze_df, empirical_df, valence_df, logger)
        
        # Apply Outlier Capping
        merged_df = apply_outlier_capping(merged_df, logger)
        
        # Save Output
        logger.info(f"Writing merged dataset to {output_path}")
        merged_df.to_csv(output_path, index=False)
        
        logger.info("T023 completed successfully.")
        
    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        sys.exit(1)
    except DataMissingError as e:
        logger.error(f"Data missing error: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()