import os
import sys
import json
import logging
import pandas as pd
from pathlib import Path

# Add project root to path for imports if running as script
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from config.env_config import load_config, setup_logging

def setup_directories():
    """Ensure output directories exist."""
    base_dir = Path("projects/PROJ-179-the-influence-of-metacognitive-awareness")
    derived_dir = base_dir / "data" / "derived"
    derived_dir.mkdir(parents=True, exist_ok=True)
    return derived_dir

def load_and_clean_data(derived_dir):
    """
    Load the validated dataset from the expected location.
    T006 ensures the file exists at data/behavioral_data.csv relative to project root.
    """
    # The download script (T005) places the file here after validation (T006)
    input_file = derived_dir.parent / "behavioral_data.csv"
    
    if not input_file.exists():
        # Fallback check for common locations if not in derived parent
        fallback_paths = [
            derived_dir.parent / "downloaded" / "behavioral_data.csv",
            derived_dir.parent / "ds003386_behavioral.csv",
            derived_dir.parent / "sample_behavioral_data.csv",
            derived_dir.parent / "downloaded" / "ds003386_behavioral.csv",
            derived_dir.parent / "downloaded" / "sample_behavioral_data.csv",
        ]
        found = False
        for p in fallback_paths:
            if p.exists():
                input_file = p
                found = True
                break
        
        if not found:
            raise FileNotFoundError(
                "No valid input dataset found. Ensure T005 (download) and T006 (validation) "
                "have completed successfully and placed the file in data/."
            )

    logging.info(f"Loading dataset from: {input_file}")
    df = pd.read_csv(input_file)
    
    # Basic cleaning: drop rows with missing critical fields
    required_cols = ['participant_id', 'trial_id', 'confidence_rating', 'source_label', 'participant_response']
    # Check for modality if available, otherwise infer or leave as is
    if 'stimulus_modality' not in df.columns:
        # If missing, we might need to infer or handle, but spec says extract it.
        # Assuming the dataset from T004/T005 has it or we add a placeholder if strictly needed.
        # However, T006 validates required fields. Let's assume it exists or is derived.
        # For robustness, if missing, we create a default 'unknown' or check if it's in source_label.
        # Given the spec, we expect it. If not, we raise or handle.
        # Let's assume standard behavioral datasets have this or we map it.
        # For now, if missing, we'll raise a clear error as per data contract.
        raise ValueError("Required column 'stimulus_modality' missing from dataset.")
    
    # Ensure required columns exist
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        raise ValueError(f"Required columns missing: {missing}")

    # Clean data types
    df['participant_id'] = df['participant_id'].astype(str)
    df['trial_id'] = df['trial_id'].astype(str)
    df['confidence_rating'] = pd.to_numeric(df['confidence_rating'], errors='coerce')
    df['participant_response'] = df['participant_response'].astype(str).str.strip()
    df['source_label'] = df['source_label'].astype(str).str.strip()
    df['stimulus_modality'] = df['stimulus_modality'].astype(str).str.strip()

    # Drop rows with NaN in critical fields
    df = df.dropna(subset=required_cols + ['stimulus_modality'])
    
    logging.info(f"Loaded {len(df)} valid trials.")
    return df

def validate_required_columns(df):
    """Ensure the dataframe has the necessary columns for downstream analysis."""
    required = ['participant_id', 'trial_id', 'stimulus_modality', 'source_label', 'participant_response', 'confidence_rating']
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns in preprocessed data: {missing}")
    return True

def extract_trial_data(df):
    """
    Extract and format trial-wise data.
    Ensures data types are consistent for downstream statistical analysis.
    """
    # Select and order columns
    output_cols = [
        'participant_id', 
        'trial_id', 
        'stimulus_modality', 
        'source_label', 
        'participant_response', 
        'confidence_rating'
    ]
    
    # Filter to only these columns and ensure order
    trial_data = df[output_cols].copy()
    
    # Validate again after selection
    validate_required_columns(trial_data)
    
    return trial_data

def write_output(trial_data, derived_dir):
    """Write the preprocessed trial data to CSV."""
    output_path = derived_dir / "trial_data.csv"
    trial_data.to_csv(output_path, index=False)
    logging.info(f"Wrote preprocessed trial data to {output_path}")
    return output_path

def main():
    """Main entry point for T012: Preprocess data."""
    # Setup logging
    config = load_config()
    logger = setup_logging(config.get("logging", {}).get("level", "INFO"))
    
    logger.info("Starting data preprocessing (T012)...")
    
    try:
        # Setup directories
        derived_dir = setup_directories()
        
        # Load and clean data
        df = load_and_clean_data(derived_dir)
        
        # Extract trial data
        trial_data = extract_trial_data(df)
        
        # Write output
        output_path = write_output(trial_data, derived_dir)
        
        logger.info("Preprocessing completed successfully.")
        return 0
        
    except FileNotFoundError as e:
        logger.error(str(e))
        return 1
    except ValueError as e:
        logger.error(str(e))
        return 1
    except Exception as e:
        logger.error(f"Unexpected error during preprocessing: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())