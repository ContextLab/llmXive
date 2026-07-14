"""
Preprocessing module for behavioral metacognition data.

Extracts trial-wise source labels and responses from the validated dataset.
Produces `data/derived/trial_data.csv` with required columns.
"""
import os
import sys
import json
import logging
import pandas as pd
from pathlib import Path

# Add project root to path for imports if running as script
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from config.env_config import load_config, setup_logging

logger = logging.getLogger(__name__)

def setup_directories():
    """Ensure output directories exist."""
    base_dir = Path(__file__).resolve().parent.parent
    derived_dir = base_dir / "data" / "derived"
    derived_dir.mkdir(parents=True, exist_ok=True)
    logger.info(f"Output directory ready: {derived_dir}")
    return derived_dir

def load_and_clean_data(input_path: Path) -> pd.DataFrame:
    """
    Load the validated dataset and perform basic cleaning.
    
    Args:
        input_path: Path to the input CSV file.
        
    Returns:
        Cleaned DataFrame.
        
    Raises:
        FileNotFoundError: If input file does not exist.
        ValueError: If required columns are missing.
    """
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    logger.info(f"Loading dataset from {input_path}")
    df = pd.read_csv(input_path)
    
    # Basic cleaning: drop rows with missing critical fields
    required_cols = ['confidence_rating', 'source_label', 'participant_response', 'stimulus_modality']
    # Handle potential missing columns gracefully - log warning if missing
    missing_cols = [c for c in required_cols if c not in df.columns]
    if missing_cols:
        # Try to map common aliases if available
        alias_map = {
            'confidence_rating': ['confidence', 'conf_rating', 'confidence_score'],
            'source_label': ['source', 'source_type', 'signal_source'],
            'participant_response': ['response', 'participant_response', 'answer'],
            'stimulus_modality': ['modality', 'stimulus_type', 'mode']
        }
        for col in missing_cols:
            for alias in alias_map.get(col, []):
                if alias in df.columns:
                    df[col] = df[alias]
                    logger.info(f"Mapped alias '{alias}' to '{col}'")
                    break
            else:
                logger.warning(f"Required column '{col}' not found and no alias mapped.")
        
        # Re-check after alias mapping
        missing_cols = [c for c in required_cols if c not in df.columns]
        if missing_cols:
            raise ValueError(f"Required columns missing after alias mapping: {missing_cols}")
    
    # Drop rows with NaN in critical columns
    initial_count = len(df)
    df = df.dropna(subset=required_cols)
    dropped_count = initial_count - len(df)
    if dropped_count > 0:
        logger.warning(f"Dropped {dropped_count} rows with missing critical values.")
    
    return df

def validate_required_columns(df: pd.DataFrame) -> bool:
    """
    Validate that all required columns exist in the DataFrame.
    
    Args:
        df: Input DataFrame.
        
    Returns:
        True if all required columns are present.
        
    Raises:
        ValueError: If required columns are missing.
    """
    required_cols = [
        'participant_id', 'trial_id', 'stimulus_modality', 
        'source_label', 'participant_response', 'confidence_rating'
    ]
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns: {missing}")
    return True

def extract_trial_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Extract and format trial-wise data.
    
    Ensures all required columns are present and properly typed.
    
    Args:
        df: Input DataFrame with raw trial data.
        
    Returns:
        Processed DataFrame with standardized columns.
    """
    # Ensure required columns exist (alias mapping handled in load_and_clean_data)
    # Add participant_id and trial_id if missing
    if 'participant_id' not in df.columns:
        if 'participant' in df.columns:
            df['participant_id'] = df['participant']
        else:
            # Generate synthetic participant IDs if none exist
            df['participant_id'] = 'P001'
    
    if 'trial_id' not in df.columns:
        if 'trial' in df.columns:
            df['trial_id'] = df['trial']
        else:
            # Generate sequential trial IDs
            df['trial_id'] = range(1, len(df) + 1)
    
    # Standardize column names if aliases were used
    standard_cols = {
        'confidence': 'confidence_rating',
        'conf_rating': 'confidence_rating',
        'source': 'source_label',
        'source_type': 'source_label',
        'response': 'participant_response',
        'modality': 'stimulus_modality',
        'stimulus_type': 'stimulus_modality'
    }
    
    for old, new in standard_cols.items():
        if old in df.columns and new not in df.columns:
            df[new] = df[old]
    
    # Select and order columns
    output_cols = [
        'participant_id', 'trial_id', 'stimulus_modality', 
        'source_label', 'participant_response', 'confidence_rating'
    ]
    
    # Only include columns that exist
    available_cols = [c for c in output_cols if c in df.columns]
    result = df[available_cols].copy()
    
    # Ensure correct data types
    result['participant_id'] = result['participant_id'].astype(str)
    result['trial_id'] = result['trial_id'].astype(int)
    result['confidence_rating'] = pd.to_numeric(result['confidence_rating'], errors='coerce')
    
    # Drop rows where confidence_rating conversion failed
    result = result.dropna(subset=['confidence_rating'])
    
    return result

def write_output(df: pd.DataFrame, output_path: Path):
    """
    Write the processed DataFrame to CSV.
    
    Args:
        df: Processed DataFrame.
        output_path: Path to write the output CSV.
    """
    df.to_csv(output_path, index=False)
    logger.info(f"Written {len(df)} trials to {output_path}")

def main():
    """Main entry point for preprocessing task."""
    # Setup logging
    setup_logging(level=logging.INFO)
    
    try:
        # Setup directories
        derived_dir = setup_directories()
        
        # Find input file
        base_dir = Path(__file__).resolve().parent.parent
        data_dir = base_dir / "data"
        
        possible_inputs = [
            data_dir / "behavioral_data.csv",
            data_dir / "downloaded" / "behavioral_data.csv",
            data_dir / "ds003386_behavioral.csv",
            data_dir / "downloaded" / "ds003386_behavioral.csv"
        ]
        
        input_path = None
        for p in possible_inputs:
            if p.exists():
                input_path = p
                break
        
        if not input_path:
            logger.error("No input CSV found in data/ directory. Run T005 first.")
            sys.exit(1)
        
        logger.info(f"Found input file: {input_path}")
        
        # Load and clean data
        df = load_and_clean_data(input_path)
        
        # Validate columns
        validate_required_columns(df)
        
        # Extract trial data
        trial_df = extract_trial_data(df)
        
        # Write output
        output_path = derived_dir / "trial_data.csv"
        write_output(trial_df, output_path)
        
        logger.info("Preprocessing completed successfully.")
        sys.exit(0)
        
    except Exception as e:
        logger.error(f"Preprocessing failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()