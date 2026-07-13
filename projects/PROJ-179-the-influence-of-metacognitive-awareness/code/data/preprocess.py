"""
Preprocessing module for the Metacognitive Awareness project (T012).
Extracts trial-wise source labels and responses from the validated dataset.
"""
import os
import sys
import json
import logging
import pandas as pd
from pathlib import Path

# Project root relative to this file (code/data/preprocess.py -> project root)
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DATA_DIR = PROJECT_ROOT / "data"
DERIVED_DIR = DATA_DIR / "derived"

# Expected input file names (from T005/T006 validation)
INPUT_FILE_NAMES = [
    "behavioral_data.csv",
    "downloaded/behavioral_data.csv",
    "ds003386_behavioral.csv",
    "downloaded/ds003386_behavioral.csv"
]

# Required columns for preprocessing
REQUIRED_COLUMNS = [
    "participant_id",
    "trial_id",
    "stimulus_modality",
    "source_label",
    "participant_response",
    "confidence_rating"
]

def setup_directories():
    """Ensure output directories exist."""
    DERIVED_DIR.mkdir(parents=True, exist_ok=True)
    logging.info(f"Output directory ready: {DERIVED_DIR}")

def load_and_clean_data():
    """
    Locate and load the validated dataset.
    Returns a cleaned DataFrame.
    """
    input_path = None
    for name in INPUT_FILE_NAMES:
        candidate = DATA_DIR / name
        if candidate.exists():
            input_path = candidate
            break

    if not input_path:
        logging.error("No input CSV found in data/ directory. Run T005 first.")
        raise FileNotFoundError("No validated dataset found. Ensure T005 completed successfully.")

    logging.info(f"Loading dataset from: {input_path}")
    try:
        df = pd.read_csv(input_path)
    except Exception as e:
        logging.error(f"Failed to load CSV: {e}")
        raise

    # Basic cleaning: drop rows with any missing required fields
    df = df.dropna(subset=REQUIRED_COLUMNS)
    
    # Ensure correct dtypes
    if 'confidence_rating' in df.columns:
        df['confidence_rating'] = pd.to_numeric(df['confidence_rating'], errors='coerce')
    
    logging.info(f"Loaded {len(df)} rows. Cleaned to {len(df)} rows after dropping NaNs.")
    return df

def validate_required_columns(df):
    """Ensure all required columns are present."""
    missing = [col for col in REQUIRED_COLUMNS if col not in df.columns]
    if missing:
        msg = f"Missing required columns: {missing}"
        logging.error(msg)
        raise ValueError(msg)
    return True

def extract_trial_data(df):
    """
    Extract and format trial-wise data.
    Ensures the schema matches the specification:
    participant_id, trial_id, stimulus_modality, source_label, participant_response, confidence_rating
    """
    # Select only the required columns to ensure schema consistency
    output_df = df[REQUIRED_COLUMNS].copy()
    
    # Ensure trial_id is unique per participant if needed, but usually it's global
    # If the dataset has nested IDs, we might need to flatten, assuming flat here.
    
    logging.info(f"Extracted {len(output_df)} trials with required schema.")
    return output_df

def write_output(df):
    """
    Write the processed DataFrame to the output CSV.
    """
    output_path = DERIVED_DIR / "trial_data.csv"
    try:
        df.to_csv(output_path, index=False)
        logging.info(f"Successfully wrote output to: {output_path}")
    except Exception as e:
        logging.error(f"Failed to write output: {e}")
        raise

def main():
    """Main entry point for T012."""
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    logging.info("Starting data preprocessing (T012)...")

    try:
        setup_directories()
        df = load_and_clean_data()
        validate_required_columns(df)
        processed_df = extract_trial_data(df)
        write_output(processed_df)
        
        logging.info("Preprocessing completed successfully.")
        return 0
    except Exception as e:
        logging.error(f"Preprocessing failed: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
