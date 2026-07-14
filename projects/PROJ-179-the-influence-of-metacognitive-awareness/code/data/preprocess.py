"""
T012: Implement data/preprocess.py to extract trial-wise source labels and responses.

This script loads the validated behavioral dataset (from T005/T006) and extracts
trial-level data into data/derived/trial_data.csv.

It also filters and saves modality-specific subsets (visual/auditory) required by T026/T027.
"""
import json
import logging
import os
import sys
import pandas as pd
from pathlib import Path
from typing import Optional, List, Dict, Any

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Project root (relative to where script is run)
BASE_DIR = Path(__file__).resolve().parent.parent.parent
DATA_DIR = BASE_DIR / "data"
DERIVED_DIR = DATA_DIR / "derived"
DOWNLOAD_DIR = DATA_DIR / "downloaded"

# Required columns in input dataset
REQUIRED_COLUMNS = [
    'participant_id', 'trial_id', 'stimulus_modality', 
    'source_label', 'participant_response', 'confidence_rating'
]

def setup_directories() -> None:
    """Create output directories if they don't exist."""
    DERIVED_DIR.mkdir(parents=True, exist_ok=True)
    logger.info(f"Ensured output directory exists: {DERIVED_DIR}")

def find_input_file() -> Optional[Path]:
    """
    Locate the validated dataset file produced by T005/T006.
    Searches common filenames in data/ and data/downloaded/.
    """
    candidates = [
        DATA_DIR / "behavioral_data.csv",
        DATA_DIR / "sample_behavioral_data.csv",
        DATA_DIR / "ds003386_behavioral.csv",
        DOWNLOAD_DIR / "behavioral_data.csv",
        DOWNLOAD_DIR / "sample_behavioral_data.csv",
        DOWNLOAD_DIR / "ds003386_behavioral.csv",
    ]
    
    for candidate in candidates:
        if candidate.exists():
            logger.info(f"Found input dataset at: {candidate}")
            return candidate
    
    logger.error("No valid input dataset found. Ensure T005 (download) and T006 (validation) have completed successfully.")
    return None

def load_and_clean_data(input_path: Path) -> pd.DataFrame:
    """
    Load the CSV dataset and perform basic cleaning.
    
    - Handles missing values by dropping rows with critical missing fields.
    - Ensures numeric columns are properly typed.
    """
    logger.info(f"Loading dataset from: {input_path}")
    try:
        df = pd.read_csv(input_path)
    except Exception as e:
        logger.error(f"Failed to load dataset: {e}")
        sys.exit(1)

    # Basic cleaning
    initial_count = len(df)
    
    # Drop rows with missing critical fields
    critical_cols = ['participant_id', 'trial_id', 'source_label', 'participant_response', 'confidence_rating']
    df = df.dropna(subset=critical_cols)
    
    # Ensure numeric columns are numeric
    numeric_cols = ['confidence_rating', 'participant_response']
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
    
    # Drop rows where conversion failed
    df = df.dropna(subset=numeric_cols)
    
    final_count = len(df)
    logger.info(f"Loaded {initial_count} rows, kept {final_count} after cleaning.")
    
    return df

def validate_required_columns(df: pd.DataFrame) -> bool:
    """
    Validate that the dataframe contains all required columns.
    """
    missing = [col for col in REQUIRED_COLUMNS if col not in df.columns]
    if missing:
        logger.error(f"Missing required columns: {missing}")
        return False
    return True

def extract_trial_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Extract and format trial-wise data.
    
    Ensures the output schema matches exactly what downstream tasks expect:
    - participant_id
    - trial_id
    - stimulus_modality
    - source_label
    - participant_response
    - confidence_rating
    """
    logger.info("Extracting trial-wise data...")
    
    # Select only the required columns in the correct order
    output_df = df[REQUIRED_COLUMNS].copy()
    
    # Ensure trial_id is string or int consistently (keep as is if already valid)
    # Ensure stimulus_modality is normalized (lowercase, strip whitespace)
    if 'stimulus_modality' in output_df.columns:
        output_df['stimulus_modality'] = output_df['stimulus_modality'].astype(str).str.strip().str.lower()
    
    # Ensure source_label is normalized
    if 'source_label' in output_df.columns:
        output_df['source_label'] = output_df['source_label'].astype(str).str.strip()
    
    # Ensure participant_response is numeric (0/1 for accuracy)
    if 'participant_response' in output_df.columns:
        output_df['participant_response'] = pd.to_numeric(output_df['participant_response'], errors='coerce')
    
    # Ensure confidence_rating is numeric
    if 'confidence_rating' in output_df.columns:
        output_df['confidence_rating'] = pd.to_numeric(output_df['confidence_rating'], errors='coerce')
    
    # Drop any remaining rows with NaN in critical fields
    output_df = output_df.dropna(subset=REQUIRED_COLUMNS)
    
    logger.info(f"Extracted {len(output_df)} valid trials.")
    return output_df

def write_output(df: pd.DataFrame) -> Dict[str, Path]:
    """
    Write the processed trial data and modality-specific subsets to disk.
    
    Outputs:
    - data/derived/trial_data.csv (full dataset)
    - data/derived/visual_trials.csv (subset)
    - data/derived/auditory_trials.csv (subset)
    """
    output_files = {}
    
    # 1. Write full trial data
    full_path = DERIVED_DIR / "trial_data.csv"
    df.to_csv(full_path, index=False)
    output_files['full'] = full_path
    logger.info(f"Written full trial data to: {full_path}")
    
    # 2. Write visual subset
    if 'stimulus_modality' in df.columns:
        visual_df = df[df['stimulus_modality'].str.lower() == 'visual']
        visual_path = DERIVED_DIR / "visual_trials.csv"
        visual_df.to_csv(visual_path, index=False)
        output_files['visual'] = visual_path
        logger.info(f"Written visual trials to: {visual_path} ({len(visual_df)} rows)")
        
        auditory_df = df[df['stimulus_modality'].str.lower() == 'auditory']
        auditory_path = DERIVED_DIR / "auditory_trials.csv"
        auditory_df.to_csv(auditory_path, index=False)
        output_files['auditory'] = auditory_path
        logger.info(f"Written auditory trials to: {auditory_path} ({len(auditory_df)} rows)")
    else:
        logger.warning("stimulus_modality column not found; skipping modality subsets.")
    
    return output_files

def main():
    """Main entry point for T012 preprocessing."""
    logger.info("Starting data preprocessing (T012)...")
    
    # Step 1: Setup directories
    setup_directories()
    
    # Step 2: Find input file
    input_file = find_input_file()
    if input_file is None:
        sys.exit(1)
    
    # Step 3: Load and clean data
    df = load_and_clean_data(input_file)
    
    # Step 4: Validate columns
    if not validate_required_columns(df):
        logger.error("Validation failed: missing required columns.")
        sys.exit(1)
    
    # Step 5: Extract trial data
    trial_df = extract_trial_data(df)
    
    # Step 6: Write outputs
    output_files = write_output(trial_df)
    
    logger.info("Preprocessing completed successfully.")
    logger.info(f"Output files: {list(output_files.values())}")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())