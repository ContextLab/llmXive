"""
Extract Empirical Outcome (Task T004b)

Loads the raw eye-tracking dataset, extracts belief ratings and headline text,
handles common column aliases, and writes the derived empirical outcomes CSV.
"""

import os
import sys
import logging
import hashlib
import json
from pathlib import Path
from typing import List, Optional, Tuple

import pandas as pd

# Import shared utilities from the project structure
from utils.logging_init import setup_global_logger
from utils.config_loader import load_config

# Custom exception for data missing scenarios
class DataMissingError(Exception):
    """Raised when required data or columns are missing."""
    pass

def get_project_root() -> Path:
    """Returns the project root directory (parent of 'code')."""
    return Path(__file__).resolve().parent.parent

def load_raw_data(raw_path: Path) -> pd.DataFrame:
    """
    Loads the raw eye-tracking dataset from a Parquet file.

    Args:
        raw_path: Path to the raw parquet file.

    Returns:
        Loaded DataFrame.

    Raises:
        DataMissingError: If the file does not exist or cannot be read.
    """
    if not raw_path.exists():
        raise DataMissingError(f"Raw data file not found: {raw_path}")
    
    try:
        df = pd.read_parquet(raw_path)
        return df
    except Exception as e:
        raise DataMissingError(f"Failed to read raw data from {raw_path}: {e}")

def verify_schema(df: pd.DataFrame, logger: logging.Logger) -> Tuple[str, bool]:
    """
    Verifies that the dataframe contains the required columns for empirical outcome extraction.
    Handles common aliases for 'belief_rating' and 'headline_text'.

    Args:
        df: The raw dataframe.
        logger: Logger instance.

    Returns:
        Tuple of (canonical_belief_col, canonical_headline_col) if valid, else raises DataMissingError.
    """
    required_cols = set(df.columns)
    
    # Define aliases for belief_rating
    belief_aliases = ['belief_rating', 'belief', 'rating', 'self_reported_belief']
    belief_col = None
    for alias in belief_aliases:
        if alias in required_cols:
            belief_col = alias
            if alias != 'belief_rating':
                logger.warning(f"Column '{alias}' found. Mapping to 'belief_rating'.")
            break
    
    if not belief_col:
        raise DataMissingError(
            f"Missing required column for belief. Searched for: {belief_aliases}. "
            f"Available columns: {list(df.columns)}"
        )

    # Define aliases for headline_text
    headline_aliases = ['headline_text', 'headline', 'text', 'stimulus_text']
    headline_col = None
    for alias in headline_aliases:
        if alias in required_cols:
            headline_col = alias
            if alias != 'headline_text':
                logger.warning(f"Column '{alias}' found. Mapping to 'headline_text'.")
            break
    
    if not headline_col:
        raise DataMissingError(
            f"Missing required column for headline text. Searched for: {headline_aliases}. "
            f"Available columns: {list(df.columns)}"
        )

    # Check for participant_id and headline_id
    if 'participant_id' not in required_cols:
        raise DataMissingError("Missing required column 'participant_id'")
    if 'headline_id' not in required_cols:
        raise DataMissingError("Missing required column 'headline_id'")

    return belief_col, headline_col

def extract_outcomes(
    df: pd.DataFrame, 
    belief_col: str, 
    headline_col: str, 
    logger: logging.Logger
) -> pd.DataFrame:
    """
    Extracts the required columns and renames them to the canonical schema.

    Args:
        df: Raw dataframe.
        belief_col: Canonical name for the belief column.
        headline_col: Canonical name for the headline column.
        logger: Logger instance.

    Returns:
        DataFrame with columns: participant_id, headline_id, belief_rating, headline_text.
    """
    outcome_df = df[['participant_id', 'headline_id', belief_col, headline_col]].copy()
    outcome_df.rename(columns={
        belief_col: 'belief_rating',
        headline_col: 'headline_text'
    }, inplace=True)

    # Ensure types
    outcome_df['belief_rating'] = pd.to_numeric(outcome_df['belief_rating'], errors='coerce')
    
    logger.info(f"Extracted {len(outcome_df)} rows for empirical outcomes.")
    return outcome_df

def main():
    """Main entry point for the empirical outcome extraction task."""
    project_root = get_project_root()
    
    # Setup logging
    logger = setup_global_logger("empirical_outcome_extractor")
    logger.info("Starting empirical outcome extraction (Task T004b).")

    # Load configuration
    try:
        config = load_config(project_root / "code" / "config.yaml")
        random_seed = config.get("random_seed", 42)
        logger.info(f"Random seed set to: {random_seed}")
    except Exception as e:
        logger.warning(f"Could not load config.yaml: {e}. Proceeding with defaults.")

    # Define paths
    raw_data_path = project_root / "data" / "raw" / "eye_tracking_raw.parquet"
    output_dir = project_root / "data" / "derived"
    output_path = output_dir / "empirical_outcomes.csv"

    # Ensure output directory exists
    output_dir.mkdir(parents=True, exist_ok=True)

    try:
        # Load data
        logger.info(f"Loading raw data from {raw_data_path}...")
        df = load_raw_data(raw_data_path)

        # Verify schema
        logger.info("Verifying dataset schema...")
        belief_col, headline_col = verify_schema(df, logger)

        # Extract outcomes
        logger.info("Extracting outcomes...")
        outcome_df = extract_outcomes(df, belief_col, headline_col, logger)

        # Write output
        logger.info(f"Writing empirical outcomes to {output_path}...")
        outcome_df.to_csv(output_path, index=False)
        
        # Log success
        logger.info(f"Task T004b completed successfully. Output: {output_path}")
        print(f"Success: {output_path}")

    except DataMissingError as e:
        logger.error(f"Data validation failed: {e}")
        print(f"Error: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error during extraction: {e}", exc_info=True)
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
