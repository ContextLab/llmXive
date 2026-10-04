"""
Preprocessing module for the pupil dilation pipeline.
Handles blink interpolation, low-pass filtering, and data validation.
"""
import os
import sys
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple
import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).parent.parent))

from preprocessing.filter import process_pupil_data, apply_filter_to_dataset, write_quality_report
from preprocessing.load_data import load_raw_data_from_dataset, normalize_columns
from config import load_config

logger = logging.getLogger(__name__)

def load_raw_data(data_dir: Path) -> List[pd.DataFrame]:
    """Load raw data files from directory."""
    files = list(data_dir.glob("*.csv"))
    dfs = []
    for f in files:
        dfs.append(pd.read_csv(f))
    return dfs

def validate_data_columns(df: pd.DataFrame) -> bool:
    """Validate that DataFrame has required columns."""
    required = ['timestamp', 'x', 'y', 'pupil_diameter']
    return all(col in df.columns for col in required)

def preprocess_single_subject(df: pd.DataFrame, config: Dict[str, Any]) -> pd.DataFrame:
    """
    Preprocess a single subject's data.
    
    Args:
        df: Input DataFrame
        config: Configuration dictionary
        
    Returns:
        Preprocessed DataFrame
    """
    # Apply blink interpolation and filtering
    processed = process_pupil_data(df, config)
    
    # Log exclusions
    write_quality_report(processed, config)
    
    return processed

def run_preprocessing_pipeline(config: Dict[str, Any]):
    """
    Run the full preprocessing pipeline.
    
    Args:
        config: Configuration dictionary
    """
    processed_data_dir = Path(config['paths']['processed_data'])
    processed_data_dir.mkdir(parents=True, exist_ok=True)
    
    # Load processed data from loading stage
    input_files = list(processed_data_dir.glob("*_normalized.csv"))
    
    if not input_files:
        logger.warning("No normalized files found. Creating empty processed file.")
        # Create minimal structure
        empty_df = pd.DataFrame(columns=['timestamp', 'x', 'y', 'pupil_diameter', 'subject_id', 'trial_id'])
        empty_df.to_csv(processed_data_dir / 'preprocessed_data.csv', index=False)
        return
    
    all_processed = []
    for input_file in input_files:
        logger.info(f"Preprocessing {input_file}")
        df = pd.read_csv(input_file)
        processed = preprocess_single_subject(df, config)
        
        # Add subject ID based on filename
        subject_id = input_file.stem.replace('_normalized', '')
        processed['subject_id'] = subject_id
        
        all_processed.append(processed)
    
    # Combine all subjects
    combined = pd.concat(all_processed, ignore_index=True)
    output_path = processed_data_dir / 'preprocessed_data.csv'
    combined.to_csv(output_path, index=False)
    
    logger.info(f"Preprocessing complete. Output: {output_path}")

def main():
    """Main entry point for preprocessing."""
    parser = argparse.ArgumentParser(description="Preprocess eye-tracking data")
    parser.add_argument("--config", type=str, default="code/config.yaml")
    args = parser.parse_args()
    
    config = load_config(Path(args.config))
    run_preprocessing_pipeline(config)

if __name__ == "__main__":
    main()