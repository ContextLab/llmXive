"""
Task T012b: Extract and convert behavioral scores from raw parquet files.

This script reads the downloaded dataset parquet files from data/raw/,
verifies the existence of the required WCST variable ('wcst_perseverative_errors'),
filters for participants aged >= 50, and extracts behavioral scores to
data/processed/behavioral_scores.csv.

If the required variable is missing, it halts with 'DATASET_VARIABLE_MISMATCH'.
"""

import os
import sys
import logging
import pandas as pd
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.logging_config import get_logger, setup_data_flow_logger

# Constants
REQUIRED_COLUMNS = ['participant_id', 'age', 'wcst_perseverative_errors']
AGE_THRESHOLD = 50
MIN_REQUIRED_COLS = 3  # At least ID, Age, and the WCST variable

def setup_logger():
    """Initialize logger for this script."""
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    return logger

def load_raw_parquet_files(raw_dir: Path) -> pd.DataFrame:
    """
    Load all parquet files from the raw directory into a single DataFrame.
    Assumes T012 has already populated this directory.
    """
    parquet_files = list(raw_dir.glob("*.parquet"))
    
    if not parquet_files:
        raise FileNotFoundError(f"No parquet files found in {raw_dir}. "
                                "Ensure T012 (download_data.py) has run successfully.")

    logger = logging.getLogger(__name__)
    logger.info(f"Found {len(parquet_files)} parquet files in {raw_dir}")

    dfs = []
    for file_path in parquet_files:
        logger.info(f"Loading {file_path.name}...")
        try:
            df = pd.read_parquet(file_path)
            dfs.append(df)
        except Exception as e:
            logger.error(f"Failed to load {file_path}: {e}")
            raise

    if not dfs:
        raise ValueError("No data loaded from parquet files.")

    combined_df = pd.concat(dfs, ignore_index=True)
    logger.info(f"Total rows loaded: {len(combined_df)}")
    return combined_df

def verify_variable_fit(df: pd.DataFrame) -> None:
    """
    Verify that the dataset contains the required WCST column.
    Halts execution if missing (DATASET_VARIABLE_MISMATCH).
    """
    logger = logging.getLogger(__name__)
    
    # Check for the specific variable required by the study design
    if 'wcst_perseverative_errors' not in df.columns:
        available_cols = list(df.columns)
        error_msg = (
            "DATASET_VARIABLE_MISMATCH: Required column 'wcst_perseverative_errors' "
            f"not found in dataset. Available columns: {available_cols}. "
            "Task T012 variable-fit check failed or dataset structure changed."
        )
        logger.critical(error_msg)
        raise RuntimeError(error_msg)

    logger.info("Variable fit verification passed: 'wcst_perseverative_errors' exists.")

def extract_behavioral_scores(df: pd.DataFrame) -> pd.DataFrame:
    """
    Filter for age >= 50 and select required behavioral columns.
    """
    logger = logging.getLogger(__name__)
    
    # Ensure we have an ID column. If 'participant_id' doesn't exist, 
    # try to infer from index or common alternatives.
    if 'participant_id' not in df.columns:
        # Common alternative in OpenNeuro derived data
        if 'sub_id' in df.columns:
            df = df.rename(columns={'sub_id': 'participant_id'})
        elif 'subject_id' in df.columns:
            df = df.rename(columns={'subject_id': 'participant_id'})
        elif df.index.name == 'subject':
            df = df.reset_index()
            df = df.rename(columns={'subject': 'participant_id'})
        else:
            # Fallback: create a synthetic ID if none exists (unlikely for parquet)
            logger.warning("No participant ID column found. Creating synthetic index-based IDs.")
            df['participant_id'] = [f"sub-{i:03d}" for i in range(len(df))]

    # Verify essential columns exist now
    missing_cols = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing_cols:
        # This is a secondary check; the primary check was for WCST
        if 'wcst_perseverative_errors' in missing_cols:
            # This should have been caught by verify_variable_fit
            pass
        else:
            # Age is critical for filtering
            if 'age' not in df.columns:
                logger.warning("Age column not found. Attempting to find alternatives...")
                # Common alternatives
                alt_cols = [c for c in df.columns if 'age' in c.lower()]
                if alt_cols:
                    df = df.rename(columns={alt_cols[0]: 'age'})
                    logger.info(f"Renamed {alt_cols[0]} to 'age'")
                else:
                    raise ValueError("Cannot proceed: 'age' column missing and no alternative found.")
    
    # Filter for Age >= 50
    initial_count = len(df)
    df_filtered = df[df['age'] >= AGE_THRESHOLD].copy()
    excluded_count = initial_count - len(df_filtered)
    
    logger.info(f"Filtered for age >= {AGE_THRESHOLD}: {len(df_filtered)} participants "
                f"(excluded {excluded_count})")

    # Select only the required columns
    # Ensure 'participant_id' is the first column
    output_cols = ['participant_id', 'age', 'wcst_perseverative_errors']
    # Add any other columns that might be useful but are not strictly required?
    # The task says "Extract and convert behavioral scores", implying a focused output.
    # We stick to the schema implied by the regression task (T020a).
    
    # Clean up data types
    df_filtered['age'] = pd.to_numeric(df_filtered['age'], errors='coerce')
    df_filtered['wcst_perseverative_errors'] = pd.to_numeric(
        df_filtered['wcst_perseverative_errors'], errors='coerce'
    )
    
    # Drop rows where critical metrics are NaN
    initial_clean = len(df_filtered)
    df_filtered = df_filtered.dropna(subset=['age', 'wcst_perseverative_errors'])
    dropped_nans = initial_clean - len(df_filtered)
    if dropped_nans > 0:
        logger.warning(f"Dropped {dropped_nans} rows due to NaN in critical behavioral columns.")

    return df_filtered[output_cols]

def main():
    logger = setup_logger()
    logger.info("Starting T012b: Extract Behavioral Scores")

    # Define paths relative to project root
    # Assuming code/ is at project root level or parent of this script
    project_root = Path(__file__).parent.parent
    raw_dir = project_root / "data" / "raw"
    processed_dir = project_root / "data" / "processed"
    output_file = processed_dir / "behavioral_scores.csv"

    # Ensure output directory exists
    processed_dir.mkdir(parents=True, exist_ok=True)

    try:
        # 1. Load data
        df = load_raw_parquet_files(raw_dir)

        # 2. Verify variable fit (Critical Check)
        verify_variable_fit(df)

        # 3. Extract and filter
        df_scores = extract_behavioral_scores(df)

        # 4. Save output
        df_scores.to_csv(output_file, index=False)
        logger.info(f"Successfully saved behavioral scores to {output_file}")
        logger.info(f"Output shape: {df_scores.shape}")
        logger.info(df_scores.head())

    except RuntimeError as e:
        if "DATASET_VARIABLE_MISMATCH" in str(e):
            logger.critical(f"Task T012b failed due to data mismatch: {e}")
            # Re-raise to ensure the pipeline knows this task failed
            raise
        else:
            logger.error(f"Unexpected error: {e}")
            raise
    except Exception as e:
        logger.error(f"Task T012b failed with unexpected error: {e}")
        raise

if __name__ == "__main__":
    main()