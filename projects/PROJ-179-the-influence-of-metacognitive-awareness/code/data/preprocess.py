import os
import sys
import logging
import json
from pathlib import Path
import pandas as pd

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

def setup_directories():
    """Ensure output directories exist."""
    project_root = Path(__file__).resolve().parent.parent.parent
    derived_dir = project_root / "data" / "derived"
    derived_dir.mkdir(parents=True, exist_ok=True)
    logger.info(f"Ensured output directory exists: {derived_dir}")
    return derived_dir

def find_input_file():
    """Find the valid input dataset from raw directory or fallback locations."""
    project_root = Path(__file__).resolve().parent.parent.parent
    raw_dir = project_root / "code" / "data" / "raw"
    
    # Check standard raw directory first
    if raw_dir.exists():
        csv_files = list(raw_dir.glob("*.csv"))
        if csv_files:
            logger.info(f"Found input file: {csv_files[0]}")
            return csv_files[0]
    
    # Check data/raw directory (alternative location)
    alt_raw_dir = project_root / "data" / "raw"
    if alt_raw_dir.exists():
        csv_files = list(alt_raw_dir.glob("*.csv"))
        if csv_files:
            logger.info(f"Found input file in alt location: {csv_files[0]}")
            return csv_files[0]
    
    # Check for downloaded dataset in data/ directory
    data_dir = project_root / "data"
    if data_dir.exists():
        csv_files = list(data_dir.glob("*.csv"))
        if csv_files:
            logger.info(f"Found input file in data dir: {csv_files[0]}")
            return csv_files[0]
    
    logger.error("No CSV files found in raw data directory.")
    return None

def load_and_clean_data(input_path):
    """Load CSV and perform basic cleaning."""
    try:
        df = pd.read_csv(input_path)
        logger.info(f"Loaded {len(df)} rows from {input_path}")
        
        # Basic cleaning: drop rows with missing critical fields
        critical_cols = ['confidence_rating', 'source_label']
        for col in critical_cols:
            if col in df.columns:
                df = df.dropna(subset=[col])
        
        # Ensure required columns exist
        required_cols = [
            'participant_id', 'trial_id', 'stimulus_modality', 
            'source_label', 'participant_response', 'confidence_rating'
        ]
        
        # Normalize column names (lowercase, strip spaces)
        df.columns = df.columns.str.lower().str.strip()
        
        # Map common variations to standard names
        column_mapping = {
            'subject_id': 'participant_id',
            'subject': 'participant_id',
            'p_id': 'participant_id',
            'trial_number': 'trial_id',
            'trial': 'trial_id',
            'modality': 'stimulus_modality',
            'stimulus_type': 'stimulus_modality',
            'source': 'source_label',
            'source_type': 'source_label',
            'response': 'participant_response',
            'answer': 'participant_response',
            'confidence': 'confidence_rating',
            'conf': 'confidence_rating',
            'conf_rating': 'confidence_rating'
        }
        
        df = df.rename(columns=column_mapping)
        
        # Fill missing participant_id if needed
        if 'participant_id' not in df.columns:
            logger.warning("participant_id column missing, generating synthetic IDs")
            df['participant_id'] = [f"P{i:03d}" for i in range(len(df))]
        
        # Ensure trial_id exists
        if 'trial_id' not in df.columns:
            df['trial_id'] = range(len(df))
        
        # Ensure numeric types
        if 'confidence_rating' in df.columns:
            df['confidence_rating'] = pd.to_numeric(df['confidence_rating'], errors='coerce')
        
        return df
        
    except Exception as e:
        logger.error(f"Error loading data: {e}")
        raise

def validate_required_columns(df):
    """Validate that all required columns are present."""
    required = ['participant_id', 'trial_id', 'source_label', 'participant_response', 'confidence_rating']
    missing = [col for col in required if col not in df.columns]
    
    if missing:
        logger.error(f"Missing required columns: {missing}")
        raise ValueError(f"Required columns missing: {missing}")
    
    logger.info("All required columns present")
    return True

def extract_trial_data(df):
    """Extract and format trial-wise data."""
    # Select and order columns as required
    output_cols = [
        'participant_id', 
        'trial_id', 
        'stimulus_modality', 
        'source_label', 
        'participant_response', 
        'confidence_rating'
    ]
    
    # Filter to only existing columns (handle optional stimulus_modality)
    existing_cols = [col for col in output_cols if col in df.columns]
    
    # Add stimulus_modality if missing, default to 'visual'
    if 'stimulus_modality' not in df.columns:
        logger.warning("stimulus_modality not found, defaulting to 'visual'")
        df['stimulus_modality'] = 'visual'
    
    # Ensure all required columns exist
    for col in output_cols:
        if col not in df.columns:
            if col == 'stimulus_modality':
                df[col] = 'visual'
            else:
                raise ValueError(f"Column {col} missing after processing")
    
    # Select and order columns
    trial_data = df[output_cols].copy()
    
    # Ensure trial_id is integer
    trial_data['trial_id'] = trial_data['trial_id'].astype(int)
    
    # Ensure participant_id is string
    trial_data['participant_id'] = trial_data['participant_id'].astype(str)
    
    # Convert source_label and participant_response to string if numeric
    for col in ['source_label', 'participant_response']:
        if trial_data[col].dtype in ['int64', 'float64']:
            trial_data[col] = trial_data[col].astype(str)
    
    logger.info(f"Extracted {len(trial_data)} trial records")
    return trial_data

def write_output(trial_data, output_dir):
    """Write trial data to CSV file."""
    output_path = output_dir / "trial_data.csv"
    trial_data.to_csv(output_path, index=False)
    logger.info(f"Wrote trial data to {output_path}")
    
    # Also write modality-specific subsets if modality column exists
    if 'stimulus_modality' in trial_data.columns:
        for modality in trial_data['stimulus_modality'].unique():
            modality_df = trial_data[trial_data['stimulus_modality'] == modality].copy()
            modality_output = output_dir / f"{modality}_trials.csv"
            modality_df.to_csv(modality_output, index=False)
            logger.info(f"Wrote {modality} trials to {modality_output}")
    
    return output_path

def main():
    """Main entry point for preprocessing task."""
    logger.info("Starting data preprocessing (T012)...")
    
    try:
        # Setup directories
        output_dir = setup_directories()
        
        # Find input file
        input_file = find_input_file()
        if input_file is None:
            logger.error("No valid input dataset found. Ensure T005 (download) and T006 (validation) have completed successfully.")
            sys.exit(1)
        
        # Load and clean data
        df = load_and_clean_data(input_file)
        
        # Validate required columns
        validate_required_columns(df)
        
        # Extract trial data
        trial_data = extract_trial_data(df)
        
        # Write output
        output_path = write_output(trial_data, output_dir)
        
        logger.info("Preprocessing completed successfully.")
        sys.exit(0)
        
    except Exception as e:
        logger.error(f"Preprocessing failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()