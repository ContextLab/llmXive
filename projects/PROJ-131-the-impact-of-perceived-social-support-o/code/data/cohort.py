import os
import logging
from pathlib import Path
from typing import Optional, Dict, Any, List
import pandas as pd
import numpy as np

from logger import get_logger

# Ensure imports align with the existing API surface provided in the prompt
# The prompt lists: load_preprocessed_data, compute_propensity_scores, perform_matching,
# apply_inverse_probability_weighting, derive_harassment_exposure, filter_invalid_scores,
# construct_synthetic_cohort, main.
# We must implement the logic for these functions to support the pipeline.
# Since T013c (preprocessing) produces the imputed data, we assume it is available
# or loadable from the intermediate steps. For this task, we focus on the final write.

# Import helper functions if they exist in sibling modules, or define them here if they are
# part of this module's responsibility based on the "extend" instruction.
# Given the prompt says "extend it on disk", we assume the skeleton exists but is incomplete.
# We will implement the missing logic for the functions listed in the API surface.

# Note: The prompt mentions `load_preprocessed_data`. This likely loads the output of T013.
# Since we don't have the exact content of T013's output file path, we assume a standard path
# or that the data is passed in. However, the task T014c specifically asks to "Write Intermediate".
# We will assume the data flow is: Preprocessing -> Cohort Derivation -> Write.

# Let's define the functions to match the API surface.

def load_preprocessed_data(data_dir: Optional[Path] = None) -> pd.DataFrame:
    """
    Loads the preprocessed data from the previous step (T013).
    Assumes the output of preprocessing is saved at a standard location.
    """
    if data_dir is None:
        data_dir = Path("data")
    
    # The previous step (T013) should have produced an imputed dataset.
    # We assume it's saved as 'imputed_data.csv' or similar in the data directory.
    # If not found, we might need to run preprocessing again or raise an error.
    # For this implementation, we try to load from a standard intermediate path.
    # If T013 output is not explicitly named, we assume 'data/results/preprocessed_data.csv'
    # or similar. Let's assume the pipeline passes data or it's in a known spot.
    # Since T013c is "Apply Scale Scoring", the output should be the scored data.
    
    input_path = data_dir / "results" / "preprocessed_data.csv"
    if not input_path.exists():
        # Fallback: try to load from ingestion if preprocessing hasn't saved yet (unlikely)
        # Or raise an error.
        raise FileNotFoundError(f"Preprocessed data not found at {input_path}. "
                                "Ensure T013 (preprocessing) has been run successfully.")
    
    logger = get_logger()
    logger.info(f"Loading preprocessed data from {input_path}")
    return pd.read_csv(input_path)

def derive_harassment_exposure(df: pd.DataFrame) -> pd.DataFrame:
    """
    Derives the binary harassment exposure flag.
    harassment_exposure = 1 if harassment_severity > 0, else 0.
    """
    logger = get_logger()
    logger.info("Deriving harassment exposure variable")
    
    if 'harassment_severity' not in df.columns:
        raise ValueError("Column 'harassment_severity' not found in data.")
    
    df = df.copy()
    df['harassment_exposure'] = (df['harassment_severity'] > 0).astype(int)
    logger.info(f"Harassment exposure derived. Exposed: {df['harassment_exposure'].sum()}, Unexposed: {(df['harassment_exposure'] == 0).sum()}")
    return df

def filter_invalid_scores(df: pd.DataFrame) -> pd.DataFrame:
    """
    Filters out rows with invalid scores (e.g., negative values, out-of-range sums).
    """
    logger = get_logger()
    initial_count = len(df)
    logger.info(f"Filtering invalid scores. Initial count: {initial_count}")
    
    # Define valid ranges based on typical scale scoring (CES-D 0-60, GAD-7 0-21, PCL-5 0-100)
    # We assume the columns 'depression', 'anxiety', 'ptsd' exist after scoring.
    valid_cols = ['depression', 'anxiety', 'ptsd']
    valid_cols = [c for c in valid_cols if c in df.columns]
    
    mask = pd.Series(True, index=df.index)
    
    for col in valid_cols:
        # Check for negative values
        if (df[col] < 0).any():
            invalid_mask = df[col] < 0
            mask &= ~invalid_mask
            logger.warning(f"Found {invalid_mask.sum()} negative values in {col}, filtering them out.")
        
        # Check for out-of-range values (simple heuristic: > max possible + small tolerance)
        # Assuming max values: CES-D 60, GAD-7 21, PCL-5 100.
        max_vals = {'depression': 60, 'anxiety': 21, 'ptsd': 100}
        if col in max_vals:
            max_val = max_vals[col]
            if (df[col] > max_val).any():
                invalid_mask = df[col] > max_val
                mask &= ~invalid_mask
                logger.warning(f"Found {(df[col] > max_val).sum()} values > {max_val} in {col}, filtering them out.")
    
    filtered_df = df[mask].reset_index(drop=True)
    dropped_count = initial_count - len(filtered_df)
    logger.info(f"Filtered {dropped_count} rows with invalid scores. Remaining: {len(filtered_df)}")
    
    return filtered_df

def construct_synthetic_cohort(data_dir: Optional[Path] = None) -> pd.DataFrame:
    """
    Constructs the analysis cohort by deriving variables and filtering.
    This function orchestrates the steps: load -> derive -> filter.
    """
    if data_dir is None:
        data_dir = Path("data")
    
    logger = get_logger()
    logger.info("Constructing analysis cohort")
    
    # Step 1: Load preprocessed data
    df = load_preprocessed_data(data_dir)
    
    # Step 2: Derive harassment exposure
    df = derive_harassment_exposure(df)
    
    # Step 3: Filter invalid scores
    df = filter_invalid_scores(df)
    
    # Ensure necessary columns are present for downstream tasks
    required_cols = ['harassment_exposure', 'harassment_severity', 'social_support', 
                     'depression', 'anxiety', 'ptsd', 'age', 'gender', 'education', 'income']
    missing_cols = [c for c in required_cols if c not in df.columns]
    if missing_cols:
        logger.warning(f"Missing columns in cohort: {missing_cols}. Proceeding with available columns.")
    
    return df

def compute_propensity_scores(df: pd.DataFrame) -> pd.DataFrame:
    """
    Placeholder for propensity score computation.
    Required by API surface, but logic may be deferred or minimal for this task.
    """
    # If not used in T014c, we can leave it as a stub that returns the df
    # or implement a simple logistic regression if needed.
    # For now, just return df as the function signature requires a return.
    # In a full implementation, this would fit a model.
    return df

def perform_matching(df: pd.DataFrame) -> pd.DataFrame:
    """
    Placeholder for matching logic.
    """
    return df

def apply_inverse_probability_weighting(df: pd.DataFrame) -> pd.DataFrame:
    """
    Placeholder for IPW logic.
    """
    return df

def main():
    """
    Main entry point for T014c: Write Intermediate Cohort.
    """
    logger = get_logger()
    logger.info("Starting T014c: Write Intermediate Cohort")
    
    try:
        # Construct the cohort
        cohort_df = construct_synthetic_cohort()
        
        # Define output path
        output_dir = Path("data") / "results"
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / "intermediate_cohort.csv"
        
        # Write to CSV
        cohort_df.to_csv(output_path, index=False)
        logger.info(f"Intermediate cohort written to {output_path}")
        logger.info(f"Shape of intermediate cohort: {cohort_df.shape}")
        
        return True
    except Exception as e:
        logger.error(f"Error in T014c: {e}")
        raise

if __name__ == "__main__":
    main()