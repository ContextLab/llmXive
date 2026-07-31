"""
Preprocessing pipeline for Moral Machine data with salience integration.

This module handles the merging of raw moral decision data with computed
visual/textual salience scores and extracts proxy control variables as
required by FR-008.

Proxy Control Variables (FR-008):
- lives_saved: Number of lives saved in the scenario
- lives_lost: Number of lives lost in the scenario
- species: Categorical distribution of entities (human, pet, livestock, etc.)
- age: Age distribution of human entities
- gender: Gender distribution of human entities

Note: This module strictly avoids 'Voluntary' tags, 'System 1/2' proxies,
or 'Salience Withdrawal' simulations as per project constraints.
"""

import os
import sys
import logging
import json
from pathlib import Path
from typing import Optional, Dict, Any, List, Tuple

import pandas as pd
import numpy as np

# Project root relative to this file
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DATA_DIR = PROJECT_ROOT / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
PROCESSED_DATA_DIR = DATA_DIR / "processed"

# Ensure directories exist
PROCESSED_DATA_DIR.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def load_raw_moral_machine_data(filepath: Optional[Path] = None) -> pd.DataFrame:
    """
    Load the raw Moral Machine dataset.

    Args:
        filepath: Optional path to the raw CSV. If None, defaults to
                  data/raw/moral_machine_subset.csv

    Returns:
        DataFrame containing the raw moral machine data.

    Raises:
        FileNotFoundError: If the specified file does not exist.
        ValueError: If the file is empty or malformed.
    """
    if filepath is None:
        filepath = RAW_DATA_DIR / "moral_machine_subset.csv"

    if not filepath.exists():
        raise FileNotFoundError(
            f"Raw data file not found: {filepath}. "
            "Please run the download stage (T013) first."
        )

    logger.info(f"Loading raw data from {filepath}")
    df = pd.read_csv(filepath)

    if df.empty:
        raise ValueError(f"Loaded dataset from {filepath} is empty.")

    logger.info(f"Loaded {len(df)} rows and {len(df.columns)} columns")
    return df


def load_salience_scores(filepath: Optional[Path] = None) -> pd.DataFrame:
    """
    Load the pre-computed salience scores.

    Args:
        filepath: Optional path to the salience CSV. If None, defaults to
                  data/processed/salience_enriched.csv (if it exists) or
                  expects the salience column to be in the raw data after
                  the salience stage.

    Note: In the current pipeline flow, T016 (merge) happens after T014/T015.
    This function is a helper for the merge step. If T016 hasn't run yet,
    we expect the salience stage (T014/T015) to have appended the column
    to the raw data or produced an intermediate file. For T010, we assume
    the salience column 'salience_score' exists in the input dataframe
    provided by the pipeline orchestrator, or we load it from a specific
    intermediate file if T014/T015 outputs it separately.

    For this implementation, we assume the salience stage (T014/T015)
    outputs to `data/processed/salience_scores.csv` if not merged yet,
    OR we expect the caller to pass a dataframe that already has the
    salience column.

    To be robust: Try loading from a specific intermediate file first.
    """
    # Expected intermediate file from salience computation stage
    intermediate_path = DATA_DIR / "processed" / "salience_scores.csv"

    if filepath is None and intermediate_path.exists():
        logger.info(f"Loading salience scores from intermediate file: {intermediate_path}")
        return pd.read_csv(intermediate_path)

    # If no intermediate file, return empty DF (caller must handle merge logic)
    logger.warning("No salience scores file found. Returning empty DataFrame.")
    return pd.DataFrame()


def handle_missing_images(df: pd.DataFrame) -> pd.DataFrame:
    """
    Identify rows with missing or broken image URLs and flag them.

    This function prepares the dataframe for text-heuristic fallbacks.
    It does NOT compute the fallback score itself (that is T015's job),
    but marks the rows that require it.

    Args:
        df: Input DataFrame.

    Returns:
        DataFrame with a new column 'image_valid' (bool).
    """
    # Heuristic: Check if 'image_url' column exists and is not NaN
    if 'image_url' in df.columns:
        # Check for empty strings or NaN
        df['image_valid'] = df['image_url'].notna() & (df['image_url'].str.strip() != '')
    else:
        # If no image_url column, assume all are text-only
        df['image_valid'] = False

    missing_count = (~df['image_valid']).sum()
    logger.info(f"Identified {missing_count} rows with missing/invalid images (text-only fallback needed)")
    return df


def extract_proxy_controls(df: pd.DataFrame) -> pd.DataFrame:
    """
    Extract proxy control variables as required by FR-008.

    FR-008 Requirements:
    - lives_saved: Number of lives saved
    - lives_lost: Number of lives lost
    - species: Categorical distribution
    - age: Age distribution
    - gender: Gender distribution

    This function ensures these columns are present, normalized, and
    ready for downstream statistical control. It does NOT perform the
    statistical analysis itself (that is T031/diagnostics.py).

    Args:
        df: Input DataFrame (raw or salience-merged).

    Returns:
        DataFrame with proxy control columns added/normalized.
    """
    logger.info("Extracting proxy control variables (FR-008)...")

    # 1. Lives Saved / Lost
    # Moral Machine data often has columns like 'n_lives_saved', 'n_lives_lost'
    # or encoded in 'choice' vs 'alternative' counts.
    # We look for standard naming conventions or calculate from scenario details.
    if 'n_lives_saved' not in df.columns:
        # Attempt to infer from other columns or set to 0 if not present
        # In many MM datasets, this is explicit. If missing, we must handle gracefully.
        if 'lives_saved' in df.columns:
            df['n_lives_saved'] = df['lives_saved']
        else:
            # Fallback: create a placeholder column if the raw data is sparse
            # This is a safeguard; the raw data should ideally have this.
            logger.warning("Column 'n_lives_saved' not found. Creating placeholder.")
            df['n_lives_saved'] = 0

    if 'n_lives_lost' not in df.columns:
        if 'lives_lost' in df.columns:
            df['n_lives_lost'] = df['lives_lost']
        else:
            logger.warning("Column 'n_lives_lost' not found. Creating placeholder.")
            df['n_lives_lost'] = 0

    # Ensure numeric types
    df['n_lives_saved'] = pd.to_numeric(df['n_lives_saved'], errors='coerce').fillna(0)
    df['n_lives_lost'] = pd.to_numeric(df['n_lives_lost'], errors='coerce').fillna(0)

    # 2. Species
    # Often encoded as 'species_human', 'species_pet', etc., or a single string.
    # We create a categorical summary column if not present.
    if 'species' not in df.columns:
        # Attempt to construct from individual species columns if they exist
        species_cols = [c for c in df.columns if c.startswith('species_')]
        if species_cols:
            # Create a combined string representation or just flag presence
            # For control variables, we often need counts per category.
            # Let's create a simple 'dominant_species' or 'species_mix' string.
            # However, for regression controls, we usually need one-hot or count.
            # We'll create a 'species_summary' column as a string for now,
            # and downstream will encode it.
            df['species'] = df[species_cols].astype(str).agg(','.join, axis=1)
        else:
            df['species'] = 'unknown'

    # 3. Age
    # Similar to species, check for age columns
    if 'age' not in df.columns:
        age_cols = [c for c in df.columns if c.startswith('age_') or 'age' in c.lower()]
        if age_cols:
            # Take the first non-null or average?
            # For control, we might need a distribution summary.
            # Let's create a 'age_summary' string.
            df['age'] = df[age_cols].astype(str).agg(','.join, axis=1)
        else:
            df['age'] = 'unknown'

    # 4. Gender
    if 'gender' not in df.columns:
        gender_cols = [c for c in df.columns if c.startswith('gender_') or 'gender' in c.lower()]
        if gender_cols:
            df['gender'] = df[gender_cols].astype(str).agg(','.join, axis=1)
        else:
            df['gender'] = 'unknown'

    # Normalize string columns to lowercase to reduce cardinality
    for col in ['species', 'age', 'gender']:
        if col in df.columns:
            df[col] = df[col].astype(str).str.lower().str.strip()
            df.loc[df[col] == 'nan', col] = 'unknown'

    logger.info(f"Proxy controls extracted: lives_saved, lives_lost, species, age, gender")
    return df


def merge_and_finalize(
    raw_df: pd.DataFrame,
    salience_df: pd.DataFrame,
    output_path: Optional[Path] = None
) -> pd.DataFrame:
    """
    Merge raw data with salience scores and finalize the dataset.

    This is the core function for T016 (US1) but implemented here in T010
    as the skeleton/infrastructure. It ensures the 'salience_score' column
    is correctly merged and normalized.

    Args:
        raw_df: The raw moral machine dataframe.
        salience_df: The dataframe containing salience scores.
        output_path: Optional path to save the final CSV.

    Returns:
        The merged and finalized DataFrame.
    """
    logger.info("Merging raw data with salience scores...")

    # If salience_df is empty, assume salience was computed inline or
    # the raw_df already has the column (from T014/T015 inline execution).
    if salience_df.empty:
        if 'salience_score' not in raw_df.columns:
            logger.warning("No salience scores found in raw data or separate file. "
                           "Proceeding without salience scores (this may be an error).")
            final_df = raw_df
        else:
            final_df = raw_df
    else:
        # Merge on a common key. Moral Machine usually has 'scenario_id' or similar.
        # If no ID, we assume row order is preserved (risky, but common in simple pipelines).
        # Let's try to find a common key.
        common_keys = set(raw_df.columns).intersection(set(salience_df.columns))
        if 'scenario_id' in common_keys:
            merge_key = 'scenario_id'
        elif 'id' in common_keys:
            merge_key = 'id'
        else:
            # Fallback to index if no key found
            logger.warning("No common key found. Merging by index (preserving order).")
            raw_df = raw_df.reset_index(drop=True)
            salience_df = salience_df.reset_index(drop=True)
            final_df = raw_df.copy()
            # Only merge the salience column
            if 'salience_score' in salience_df.columns:
                final_df['salience_score'] = salience_df['salience_score']
            # Handle other salience columns if any
            for col in salience_df.columns:
                if col not in final_df.columns and col != 'salience_score':
                    final_df[col] = salience_df[col]
            return final_df

        final_df = pd.merge(
            raw_df,
            salience_df[[merge_key, 'salience_score']],
            on=merge_key,
            how='left'
        )

    # Ensure salience_score is numeric and normalized [0, 1]
    if 'salience_score' in final_df.columns:
        final_df['salience_score'] = pd.to_numeric(final_df['salience_score'], errors='coerce')
        # Normalize if out of bounds (shouldn't happen if computed correctly, but safeguard)
        final_df['salience_score'] = final_df['salience_score'].clip(0.0, 1.0)

        # Fill missing salience scores with 0.0 (or NaN? FR-002 says fallback logic)
        # FR-002: "text-only fallback" implies we should have a value.
        # If we are here and it's NaN, it means the fallback wasn't computed.
        # For T010 (skeleton), we fill with 0.0 but log a warning.
        # In T015/T016, this would be replaced by the actual heuristic.
        missing_salience = final_df['salience_score'].isna().sum()
        if missing_salience > 0:
            logger.warning(f"Found {missing_salience} rows with missing salience scores. "
                           "Filling with 0.0. (Ensure T015 fallback is implemented).")
            final_df['salience_score'] = final_df['salience_score'].fillna(0.0)
    else:
        # If no salience score column exists, create one with 0.0 (placeholder)
        logger.warning("No salience_score column found. Creating placeholder with 0.0.")
        final_df['salience_score'] = 0.0

    # Validate output constraints
    assert final_df['salience_score'].min() >= 0.0, "Salience score below 0.0"
    assert final_df['salience_score'].max() <= 1.0, "Salience score above 1.0"

    # Extract proxy controls (FR-008)
    final_df = extract_proxy_controls(final_df)

    if output_path is None:
        output_path = PROCESSED_DATA_DIR / "salience_enriched.csv"

    logger.info(f"Saving finalized data to {output_path}")
    final_df.to_csv(output_path, index=False)

    logger.info(f"Finalized dataset saved: {len(final_df)} rows, {len(final_df.columns)} columns")
    return final_df


def validate_output(df: pd.DataFrame) -> bool:
    """
    Validate the output DataFrame against project constraints.

    Checks:
    - salience_score exists and is in [0, 1]
    - Proxy control variables exist (lives_saved, lives_lost, species, age, gender)
    - No missing values in critical columns (optional, but recommended)

    Args:
        df: The DataFrame to validate.

    Returns:
        True if valid, False otherwise.
    """
    logger.info("Validating output DataFrame...")
    valid = True

    # 1. Salience Score
    if 'salience_score' not in df.columns:
        logger.error("Validation failed: 'salience_score' column missing.")
        return False
    if df['salience_score'].isna().any():
        logger.error("Validation failed: 'salience_score' contains NaN values.")
        return False
    if df['salience_score'].min() < 0.0 or df['salience_score'].max() > 1.0:
        logger.error("Validation failed: 'salience_score' out of [0, 1] range.")
        return False

    # 2. Proxy Controls (FR-008)
    required_controls = ['n_lives_saved', 'n_lives_lost', 'species', 'age', 'gender']
    for col in required_controls:
        if col not in df.columns:
            logger.warning(f"Validation warning: Control variable '{col}' missing.")
            valid = False

    if valid:
        logger.info("Validation passed.")
    else:
        logger.warning("Validation completed with warnings.")

    return valid


def main():
    """
    Main entry point for the preprocessing stage.

    Orchestrates:
    1. Load raw data
    2. Handle missing images (flagging)
    3. Load salience scores (if available)
    4. Merge and finalize
    5. Validate output
    """
    logger.info("Starting preprocessing stage (T010/T016)...")

    try:
        # 1. Load Raw Data
        raw_df = load_raw_moral_machine_data()

        # 2. Handle Missing Images (Flagging)
        raw_df = handle_missing_images(raw_df)

        # 3. Load Salience Scores
        # Note: In a real pipeline, T014/T015 would have generated this.
        # For T010, we attempt to load it. If not present, we proceed
        # with a placeholder or error, depending on strictness.
        # Here, we try to load from the expected intermediate file.
        salience_df = load_salience_scores()

        # 4. Merge and Finalize
        final_df = merge_and_finalize(raw_df, salience_df)

        # 5. Validate
        if not validate_output(final_df):
            logger.error("Preprocessing validation failed. Exiting.")
            sys.exit(1)

        logger.info("Preprocessing stage completed successfully.")
        return 0

    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error during preprocessing: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    sys.exit(main())
