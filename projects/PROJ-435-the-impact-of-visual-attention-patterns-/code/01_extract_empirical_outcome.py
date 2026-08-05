import os
import sys
import logging
import hashlib
import json
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

import pandas as pd

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Column aliases for belief_rating mapping
BELIEF_RATING_ALIASES = [
    'belief_rating',
    'rating',
    'response',
    'belief_score',
    'trust_score',
    'credibility_rating',
    'credibility_score'
]

REQUIRED_COLUMNS = ['participant_id', 'headline_id', 'belief_rating', 'headline_text']


class DataMissingError(Exception):
    """Raised when required data columns are missing and cannot be mapped."""
    pass


def get_project_root() -> Path:
    """Determine the project root directory."""
    current = Path(__file__).resolve()
    # Assume structure: code/01_extract_empirical_outcome.py -> project root is parent of code/
    return current.parent.parent


def load_raw_data(input_path: Path) -> pd.DataFrame:
    """
    Load the raw eye-tracking dataset from a Parquet file.

    Args:
        input_path: Path to the raw parquet file.

    Returns:
        DataFrame containing the raw data.

    Raises:
        FileNotFoundError: If the input file does not exist.
        ValueError: If the file format is unsupported or data cannot be read.
    """
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")

    logger.info(f"Loading raw data from {input_path}")
    try:
        df = pd.read_parquet(input_path)
        logger.info(f"Loaded {len(df)} rows with columns: {list(df.columns)}")
        return df
    except Exception as e:
        raise ValueError(f"Failed to read parquet file: {e}") from e


def verify_schema(df: pd.DataFrame) -> Tuple[bool, str]:
    """
    Verify that the dataframe contains the necessary columns for outcome extraction.
    Attempts to map common aliases to 'belief_rating' if the exact name is missing.

    Args:
        df: The input dataframe.

    Returns:
        Tuple of (success: bool, message: str)
    """
    required_static = ['participant_id', 'headline_id', 'headline_text']
    available_cols = set(df.columns)

    # Check static requirements
    missing_static = [col for col in required_static if col not in available_cols]
    if missing_static:
        return False, f"Missing required static columns: {missing_static}"

    # Check for belief_rating or its aliases
    found_rating_col = None
    for alias in BELIEF_RATING_ALIASES:
        if alias in available_cols:
            found_rating_col = alias
            break

    if found_rating_col is None:
        available_str = ", ".join(sorted(available_cols))
        raise DataMissingError(
            f"Could not find 'belief_rating' or any of its aliases {BELIEF_RATING_ALIASES}. "
            f"Available columns: {available_str}"
        )

    if found_rating_col != 'belief_rating':
        logger.warning(f"Mapping column '{found_rating_col}' to 'belief_rating'")
        df['belief_rating'] = df[found_rating_col]

    return True, "Schema verified successfully"


def extract_outcomes(df: pd.DataFrame) -> pd.DataFrame:
    """
    Extract the specific columns required for empirical outcomes.

    Args:
        df: The validated dataframe.

    Returns:
        DataFrame with columns: participant_id, headline_id, belief_rating, headline_text
    """
    outcome_df = df[REQUIRED_COLUMNS].copy()

    # Ensure correct data types if possible
    if 'belief_rating' in outcome_df.columns:
        # Try to convert to numeric, coercing errors to NaN (which we might drop later if needed)
        outcome_df['belief_rating'] = pd.to_numeric(outcome_df['belief_rating'], errors='coerce')

    logger.info(f"Extracted outcomes shape: {outcome_df.shape}")
    return outcome_df


def main():
    """Main entry point for the empirical outcome extraction script."""
    project_root = get_project_root()
    input_path = project_root / "data" / "raw" / "eye_tracking_raw.parquet"
    output_path = project_root / "data" / "derived" / "empirical_outcomes.csv"

    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    logger.info(f"Starting empirical outcome extraction. Input: {input_path}")

    try:
        # 1. Load raw data
        df = load_raw_data(input_path)

        # 2. Verify schema and map aliases
        # This may raise DataMissingError if no mapping is found
        success, msg = verify_schema(df)
        if not success:
            raise DataMissingError(msg)

        # 3. Extract outcomes
        outcome_df = extract_outcomes(df)

        # 4. Drop any rows where belief_rating became NaN during conversion (if applicable)
        initial_count = len(outcome_df)
        outcome_df = outcome_df.dropna(subset=['belief_rating'])
        dropped_count = initial_count - len(outcome_df)
        if dropped_count > 0:
            logger.warning(f"Dropped {dropped_count} rows due to missing/invalid belief_rating")

        # 5. Save to CSV
        outcome_df.to_csv(output_path, index=False)
        logger.info(f"Successfully wrote {len(outcome_df)} rows to {output_path}")

    except DataMissingError as e:
        logger.error(f"Data schema error: {e}")
        raise
    except FileNotFoundError as e:
        logger.error(f"File not found error: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error during extraction: {e}")
        raise


if __name__ == "__main__":
    main()
