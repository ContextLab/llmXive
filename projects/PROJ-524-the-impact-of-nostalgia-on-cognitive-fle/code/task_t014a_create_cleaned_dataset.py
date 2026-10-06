"""
T014a: Generate Cleaned Dataset

Reads the cleaned dataset (with MMSE filtering applied if available),
selects the required columns, and writes the final cleaned dataset.

Depends on: T012c, T012e
"""
import os
import json
import logging
import pandas as pd
from pathlib import Path
from typing import Optional, Dict, Any

# Import config helpers from the project's config module
try:
    from config import get_config, get_config_value
except ImportError:
    # Fallback if running as script directly without package import
    import sys
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from config import get_config, get_config_value

from utils import setup_logging, log_info, log_warning, log_error, get_timestamp

# Configure logging
logger = setup_logging("task_t014a")

def get_config_paths() -> Dict[str, Path]:
    """Retrieve configured paths for input and output files."""
    config = get_config()
    paths = config.get('paths', {})
    
    processed_dir = Path(paths.get('processed', 'data/processed'))
    
    return {
        'input_file': processed_dir / 'cleaned_dataset.csv',
        'output_file': processed_dir / 'final_cleaned_dataset.csv',
        'exclusion_log_file': processed_dir / 'exclusion_log.json',
        'mmse_flag_file': processed_dir / 'mmse_flag.json'
    }

def load_exclusion_log(file_path: Path) -> Optional[Dict[str, Any]]:
    """Load the exclusion log to check for simulation mode or errors."""
    if not file_path.exists():
        log_warning(f"Exclusion log not found at {file_path}. Proceeding without it.")
        return None
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        log_error(f"Failed to load exclusion log: {e}")
        return None

def load_mmse_flag(file_path: Path) -> bool:
    """Load the MMSE flag to determine if MMSE filtering was applied."""
    if not file_path.exists():
        log_warning(f"MMSE flag not found at {file_path}. Assuming MMSE filtering was not applied.")
        return False
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return data.get('has_mmse', False)
    except (json.JSONDecodeError, IOError) as e:
        log_error(f"Failed to load MMSE flag: {e}")
        return False

def load_intermediate_dataset(file_path: Path) -> pd.DataFrame:
    """Load the intermediate cleaned dataset."""
    if not file_path.exists():
        raise FileNotFoundError(f"Input dataset not found at {file_path}")
    
    try:
        df = pd.read_csv(file_path)
        log_info(f"Loaded dataset with {len(df)} rows from {file_path}")
        return df
    except Exception as e:
        log_error(f"Failed to load dataset: {e}")
        raise

def create_cleaned_dataset(df: pd.DataFrame) -> pd.DataFrame:
    """
    Select required columns for the final cleaned dataset.
    
    Required columns: participant_id, stimulus_type, perseverative_errors, 
    categories_completed, age
    """
    required_columns = [
        'participant_id', 
        'stimulus_type', 
        'perseverative_errors', 
        'categories_completed', 
        'age'
    ]
    
    # Check for missing columns
    missing_cols = [col for col in required_columns if col not in df.columns]
    if missing_cols:
        log_error(f"Missing required columns in dataset: {missing_cols}")
        raise ValueError(f"Missing required columns: {missing_cols}")
    
    # Select and order columns
    final_df = df[required_columns].copy()
    
    log_info(f"Selected {len(required_columns)} columns for final dataset")
    return final_df

def save_cleaned_dataset(df: pd.DataFrame, file_path: Path) -> None:
    """Save the final cleaned dataset to CSV."""
    try:
        # Ensure parent directory exists
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        df.to_csv(file_path, index=False)
        log_info(f"Saved final cleaned dataset to {file_path} with {len(df)} rows")
    except Exception as e:
        log_error(f"Failed to save cleaned dataset: {e}")
        raise

def main() -> int:
    """Main entry point for T014a."""
    log_info(f"Starting T014a: Generate Cleaned Dataset at {get_timestamp()}")
    
    try:
        # Get paths
        paths = get_config_paths()
        input_file = paths['input_file']
        output_file = paths['output_file']
        exclusion_log_file = paths['exclusion_log_file']
        mmse_flag_file = paths['mmse_flag_file']
        
        # Load metadata for logging
        exclusion_log = load_exclusion_log(exclusion_log_file)
        has_mmse = load_mmse_flag(mmse_flag_file)
        
        if exclusion_log:
            log_info(f"Exclusion log loaded. Simulation mode: {exclusion_log.get('SIMULATION_FALLBACK', False)}")
        
        log_info(f"MMSE filtering applied: {has_mmse}")
        
        # Load intermediate dataset
        df = load_intermediate_dataset(input_file)
        
        # Create final cleaned dataset
        final_df = create_cleaned_dataset(df)
        
        # Save output
        save_cleaned_dataset(final_df, output_file)
        
        log_info(f"T014a completed successfully. Output: {output_file}")
        return 0
        
    except FileNotFoundError as e:
        log_error(f"Data not found: {e}")
        return 1
    except ValueError as e:
        log_error(f"Data validation error: {e}")
        return 1
    except Exception as e:
        log_error(f"Unexpected error in T014a: {e}")
        return 1

if __name__ == "__main__":
    exit(main())