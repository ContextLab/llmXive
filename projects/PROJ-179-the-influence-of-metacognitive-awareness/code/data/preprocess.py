import json
import logging
import os
import sys
import pandas as pd
from pathlib import Path

# Configure logging to stdout/stderr for pipeline visibility
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

def setup_directories():
    """Ensure the derived output directory exists."""
    project_root = Path(__file__).resolve().parent.parent.parent
    derived_dir = project_root / "data" / "derived"
    derived_dir.mkdir(parents=True, exist_ok=True)
    logger.info(f"Ensured output directory exists: {derived_dir}")
    return derived_dir

def find_input_file():
    """
    Locate the validated input dataset.
    Looks in data/raw for a CSV file that passed T006 validation.
    """
    project_root = Path(__file__).resolve().parent.parent.parent
    raw_dir = project_root / "data" / "raw"
    
    if not raw_dir.exists():
        logger.error(f"Raw data directory not found: {raw_dir}")
        return None

    csv_files = list(raw_dir.glob("*.csv"))
    if not csv_files:
        logger.error("No CSV files found in raw data directory.")
        return None

    # Prefer the file that matches the expected validation report naming if exists
    # Otherwise take the first available CSV
    for f in csv_files:
        if "validated" in f.name or "clean" in f.name:
            return f
    
    return csv_files[0]

def load_and_clean_data(file_path):
    """Load CSV and ensure basic data cleanliness."""
    logger.info(f"Loading dataset from: {file_path}")
    try:
        df = pd.read_csv(file_path)
    except Exception as e:
        logger.error(f"Failed to load dataset: {e}")
        return None
    
    # Drop rows with missing critical fields
    required_cols = ['participant_id', 'trial_id', 'source_label', 'participant_response', 'confidence_rating']
    # Check if columns exist, if not try to map or fail gracefully
    missing_cols = [c for c in required_cols if c not in df.columns]
    
    if missing_cols:
        # Attempt to handle common variations or fail
        logger.error(f"Required columns missing: {missing_cols}")
        # Try to find similar columns
        found_cols = []
        for c in required_cols:
            if c in df.columns:
                found_cols.append(c)
            else:
                # Check for case-insensitive matches
                matches = [col for col in df.columns if col.lower() == c.lower()]
                if matches:
                    df.rename(columns={matches[0]: c}, inplace=True)
                    found_cols.append(c)
        
        final_missing = [c for c in required_cols if c not in df.columns]
        if final_missing:
            logger.error(f"Still missing required columns after mapping: {final_missing}")
            return None

    # Drop rows with NaN in critical columns
    df.dropna(subset=required_cols, inplace=True)
    logger.info(f"Loaded {len(df)} valid trials after cleaning.")
    return df

def validate_required_columns(df):
    """Ensure the dataframe has the schema expected by downstream tasks."""
    required = [
        'participant_id', 'trial_id', 'stimulus_modality', 
        'source_label', 'participant_response', 'confidence_rating'
    ]
    missing = [c for c in required if c not in df.columns]
    if missing:
        logger.error(f"Preprocessed data missing required columns: {missing}")
        return False
    return True

def extract_trial_data(df):
    """
    Extract and standardize trial-wise data.
    Ensures 'stimulus_modality' exists (defaults to 'visual' if not present but inferable, 
    or handles missing gracefully if the dataset is purely behavioral without modality).
    """
    if 'stimulus_modality' not in df.columns:
        logger.warning("Column 'stimulus_modality' not found. Checking for alternatives...")
        if 'modality' in df.columns:
            df.rename(columns={'modality': 'stimulus_modality'}, inplace=True)
        elif 'condition' in df.columns:
            # Fallback: assume condition implies modality if it contains 'visual' or 'auditory'
            # Otherwise default to 'visual' for compatibility with T026 filter
            df['stimulus_modality'] = df['condition'].apply(
                lambda x: 'auditory' if 'auditory' in str(x).lower() else 'visual'
            )
        else:
            # Default to 'visual' if no modality info is found, to prevent pipeline crash
            logger.warning("No modality information found. Defaulting all trials to 'visual'.")
            df['stimulus_modality'] = 'visual'
    
    # Ensure numeric types for calculations downstream
    df['confidence_rating'] = pd.to_numeric(df['confidence_rating'], errors='coerce')
    df['participant_response'] = pd.to_numeric(df['participant_response'], errors='coerce')
    
    # Drop rows where confidence or response became NaN during conversion
    df.dropna(subset=['confidence_rating', 'participant_response'], inplace=True)
    
    return df

def write_output(df, output_dir):
    """Write the derived trial data to CSV."""
    output_path = output_dir / "trial_data.csv"
    try:
        df.to_csv(output_path, index=False)
        logger.info(f"Successfully wrote derived data to: {output_path}")
        
        # Also write modality-specific splits as declared deliverables for T012/T026 handoff
        # Even though T026 is separate, the run-book needs these files for validation
        if 'stimulus_modality' in df.columns:
            for mod in df['stimulus_modality'].unique():
                mod_df = df[df['stimulus_modality'] == mod]
                if mod == 'visual':
                    mod_df.to_csv(output_dir / "visual_trials.csv", index=False)
                    logger.info(f"Wrote visual trials to: {output_dir / 'visual_trials.csv'}")
                elif mod == 'auditory':
                    mod_df.to_csv(output_dir / "auditory_trials.csv", index=False)
                    logger.info(f"Wrote auditory trials to: {output_dir / 'auditory_trials.csv'}")
        
        return True
    except Exception as e:
        logger.error(f"Failed to write output: {e}")
        return False

def main():
    logger.info("Starting data preprocessing (T012)...")
    
    # 1. Setup directories
    output_dir = setup_directories()
    
    # 2. Find input file
    input_file = find_input_file()
    if not input_file:
        logger.error("No valid input dataset found. Ensure T005 (download) and T006 (validation) have completed successfully.")
        sys.exit(1)
    
    # 3. Load and clean
    df = load_and_clean_data(input_file)
    if df is None:
        logger.error("Failed to load or clean data.")
        sys.exit(1)
    
    # 4. Validate columns
    if not validate_required_columns(df):
        logger.error("Data validation failed: missing required columns.")
        sys.exit(1)
    
    # 5. Extract and standardize
    df = extract_trial_data(df)
    
    # 6. Write output
    if not write_output(df, output_dir):
        logger.error("Failed to write output files.")
        sys.exit(1)
    
    logger.info("Preprocessing completed successfully.")
    sys.exit(0)

if __name__ == "__main__":
    main()