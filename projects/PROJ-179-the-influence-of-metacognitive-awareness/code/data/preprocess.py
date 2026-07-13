"""
T012: Implement data/preprocess.py to extract trial-wise source labels and responses.

This script extracts trial-wise source labels and responses from the VALID dataset
identified by T004 and downloaded by T005. It produces data/derived/trial_data.csv.

Prerequisites: T006 must have passed (validating that confidence_rating and source_label exist).
"""
import os
import sys
import json
import logging
import pandas as pd
from pathlib import Path
from typing import Optional, Dict, Any

# Project root is the parent of the 'code' directory
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
DERIVED_DIR = DATA_DIR / "derived"

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

# Expected input file paths (from T005/T006)
INPUT_FILE_PATTERNS = [
    "ds003386_behavioral.csv",
    "downloaded/ds003386_behavioral.csv",
    "behavioral_data.csv"
]

# Required columns for preprocessing
REQUIRED_COLUMNS = [
    'participant_id',
    'trial_id',
    'stimulus_modality',
    'source_label',
    'participant_response',
    'confidence_rating'
]

def setup_directories() -> Path:
    """Ensure output directory exists."""
    DERIVED_DIR.mkdir(parents=True, exist_ok=True)
    logger.info(f"Output directory ready: {DERIVED_DIR}")
    return DERIVED_DIR

def load_and_clean_data() -> Optional[pd.DataFrame]:
    """
    Locate and load the valid dataset produced by T005.
    
    Returns:
        DataFrame with raw behavioral data, or None if not found.
    """
    input_path = None
    for pattern in INPUT_FILE_PATTERNS:
        candidate = DATA_DIR / pattern
        if candidate.exists():
            input_path = candidate
            break
    
    if not input_path:
        logger.error("No input CSV found in data/ directory. Run T005 first.")
        return None
    
    logger.info(f"Loading dataset from: {input_path}")
    try:
        df = pd.read_csv(input_path)
        logger.info(f"Loaded {len(df)} rows from {input_path.name}")
        return df
    except Exception as e:
        logger.error(f"Failed to read CSV: {e}")
        return None

def validate_required_columns(df: pd.DataFrame) -> bool:
    """
    Ensure the dataset contains all required columns.
    
    Args:
        df: Input DataFrame.
        
    Returns:
        True if all columns present, False otherwise.
    """
    missing = [col for col in REQUIRED_COLUMNS if col not in df.columns]
    if missing:
        logger.error(f"Missing required columns: {missing}")
        return False
    return True

def extract_trial_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Extract and normalize trial-wise data.
    
    Performs:
    - Column selection (only required fields)
    - Type normalization
    - Removal of rows with missing critical values
    
    Args:
        df: Raw DataFrame.
        
    Returns:
        Cleaned DataFrame with trial-level metrics.
    """
    logger.info("Extracting trial-level data...")
    
    # Select only required columns
    out_df = df[REQUIRED_COLUMNS].copy()
    
    # Ensure correct dtypes
    out_df['participant_id'] = out_df['participant_id'].astype(str)
    out_df['trial_id'] = out_df['trial_id'].astype(int)
    out_df['stimulus_modality'] = out_df['stimulus_modality'].astype(str)
    out_df['source_label'] = out_df['source_label'].astype(str)
    out_df['participant_response'] = out_df['participant_response'].astype(int)
    out_df['confidence_rating'] = out_df['confidence_rating'].astype(float)
    
    # Drop rows with any missing values in critical fields
    initial_count = len(out_df)
    out_df = out_df.dropna(subset=REQUIRED_COLUMNS)
    dropped_count = initial_count - len(out_df)
    
    if dropped_count > 0:
        logger.warning(f"Dropped {dropped_count} rows with missing values.")
    
    logger.info(f"Extracted {len(out_df)} valid trials.")
    return out_df

def write_output(df: pd.DataFrame, output_path: Path) -> bool:
    """
    Write the processed DataFrame to CSV.
    
    Args:
        df: Processed DataFrame.
        output_path: Target file path.
        
    Returns:
        True if successful, False otherwise.
    """
    try:
        df.to_csv(output_path, index=False)
        logger.info(f"Successfully wrote output to: {output_path}")
        return True
    except Exception as e:
        logger.error(f"Failed to write output file: {e}")
        return False

def main() -> int:
    """
    Main entry point for T012.
    
    Returns:
        0 on success, 1 on failure.
    """
    logger.info("Starting data preprocessing (T012)...")
    
    # 1. Setup directories
    setup_directories()
    
    # 2. Load data
    raw_df = load_and_clean_data()
    if raw_df is None:
        logger.error("Data loading failed. Aborting.")
        return 1
    
    # 3. Validate columns
    if not validate_required_columns(raw_df):
        logger.error("Required columns missing. Aborting.")
        return 1
    
    # 4. Extract trial data
    trial_df = extract_trial_data(raw_df)
    if trial_df.empty:
        logger.error("No valid trials extracted. Aborting.")
        return 1
    
    # 5. Write output
    output_path = DERIVED_DIR / "trial_data.csv"
    if not write_output(trial_df, output_path):
        logger.error("Output writing failed. Aborting.")
        return 1
    
    logger.info("Preprocessing completed successfully.")
    return 0

if __name__ == "__main__":
    sys.exit(main())