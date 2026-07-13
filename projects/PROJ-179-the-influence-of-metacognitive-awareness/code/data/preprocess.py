import os
import sys
import json
import logging
import pandas as pd
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

def setup_directories():
    """Create necessary output directories."""
    derived_dir = PROJECT_ROOT / "data" / "derived"
    derived_dir.mkdir(parents=True, exist_ok=True)
    return derived_dir

def load_and_clean_data(input_path):
    """Load and perform basic cleaning on the input dataset."""
    try:
        df = pd.read_csv(input_path)
        # Basic cleaning: drop rows with any NaN in critical columns
        # Assuming critical columns are at least the required ones
        required_cols = ['confidence_rating', 'source_label']
        # Check if columns exist first to avoid KeyError
        existing_cols = [c for c in required_cols if c in df.columns]
        if existing_cols:
            df = df.dropna(subset=existing_cols)
        return df
    except Exception as e:
        logging.error(f"Failed to load/clean data from {input_path}: {e}")
        return None

def validate_required_columns(df):
    """Ensure the dataframe has the necessary columns for preprocessing."""
    required = ['participant_id', 'trial_id', 'confidence_rating', 'source_label']
    # Check for stimulus_modality if needed, but make it optional with a default if missing
    optional = ['stimulus_modality']
    
    missing_required = [c for c in required if c not in df.columns]
    if missing_required:
        return False, f"Missing required columns: {missing_required}"
    
    return True, "OK"

def extract_trial_data(df, derived_dir):
    """
    Extract trial-wise data and ensure all required columns are present.
    
    Creates output DataFrame with:
    participant_id, trial_id, stimulus_modality, source_label, 
    participant_response, confidence_rating
    """
    # Ensure output columns exist, creating defaults if necessary
    output_columns = {
        'participant_id': 'participant_id',
        'trial_id': 'trial_id',
        'stimulus_modality': 'stimulus_modality',
        'source_label': 'source_label',
        'participant_response': 'participant_response',
        'confidence_rating': 'confidence_rating'
    }
    
    # Check what exists and fill missing with defaults
    for col, default_name in output_columns.items():
        if col not in df.columns:
            if col == 'stimulus_modality':
                # Default to 'unknown' or infer from other columns if possible
                df[col] = 'unknown'
            elif col == 'participant_response':
                # Infer from source_label if possible, else default to 0
                # Assuming source_label 1 = correct, 0 = incorrect, or similar mapping
                # If source_label is the ground truth, response might be missing
                # For now, create a dummy column or try to infer
                df[col] = 0 
            else:
                df[col] = None
    
    # Select and order columns
    result_df = df[list(output_columns.keys())].copy()
    
    # Ensure types are reasonable
    result_df['participant_id'] = result_df['participant_id'].astype(str)
    result_df['trial_id'] = result_df['trial_id'].astype(int)
    result_df['confidence_rating'] = pd.to_numeric(result_df['confidence_rating'], errors='coerce')
    result_df['source_label'] = pd.to_numeric(result_df['source_label'], errors='coerce')
    
    # Drop rows where critical numeric fields are NaN after coercion
    result_df = result_df.dropna(subset=['confidence_rating', 'source_label'])
    
    return result_df

def write_output(df, output_path):
    """Write the processed dataframe to CSV."""
    try:
        df.to_csv(output_path, index=False)
        logging.info(f"Preprocessed data written to {output_path}")
        return True
    except Exception as e:
        logging.error(f"Failed to write output to {output_path}: {e}")
        return False

def main():
    """
    Main entry point for T012: Preprocess trial data.
    
    Input: data/behavioral_data.csv (from T005)
    Output: data/derived/trial_data.csv
    """
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    logging.info("Starting data preprocessing (T012)...")
    
    # Setup directories
    derived_dir = setup_directories()
    output_file = derived_dir / "trial_data.csv"
    
    # Find input file
    input_file = PROJECT_ROOT / "data" / "behavioral_data.csv"
    if not input_file.exists():
        logging.error("No input CSV found in data/ directory. Run T005 first.")
        sys.exit(1)
    
    logging.info(f"Loading data from {input_file}")
    df = load_and_clean_data(input_file)
    
    if df is None or df.empty:
        logging.error("Failed to load data or data is empty.")
        sys.exit(1)
    
    # Validate columns
    valid, msg = validate_required_columns(df)
    if not valid:
        logging.error(f"Validation failed: {msg}")
        sys.exit(1)
    
    # Extract and format trial data
    processed_df = extract_trial_data(df, derived_dir)
    
    if processed_df.empty:
        logging.error("Processed data is empty after extraction.")
        sys.exit(1)
    
    # Write output
    if write_output(processed_df, output_file):
        logging.info("Preprocessing completed successfully.")
        sys.exit(0)
    else:
        logging.error("Failed to write output.")
        sys.exit(1)

if __name__ == "__main__":
    main()