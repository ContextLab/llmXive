"""
Data loading module for the pupil dilation pipeline.
Loads raw eye-tracking data from verified sources and normalizes to uniform format.
"""
import os
import sys
import logging
import argparse
from pathlib import Path
from typing import Optional, Dict, Any, List
import pandas as pd
import numpy as np

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import load_config

logger = logging.getLogger(__name__)

def load_raw_data_from_dataset(data_dir: Path, config: Dict[str, Any]) -> List[pd.DataFrame]:
    """
    Load raw data files from the dataset directory.
    
    Args:
        data_dir: Path to the raw data directory
        config: Configuration dictionary
        
    Returns:
        List of DataFrames, one per subject/file
    """
    data_files = list(data_dir.glob("*.csv"))
    
    if not data_files:
        raise FileNotFoundError(f"No CSV files found in {data_dir}")
    
    dfs = []
    for file_path in data_files:
        logger.info(f"Loading file: {file_path}")
        try:
            df = pd.read_csv(file_path)
            dfs.append(df)
        except Exception as e:
            logger.error(f"Failed to load {file_path}: {e}")
            raise
    
    return dfs

def normalize_columns(df: pd.DataFrame, config: Dict[str, Any]) -> pd.DataFrame:
    """
    Normalize column names to the standard schema.
    
    Args:
        df: Input DataFrame
        config: Configuration dictionary
        
    Returns:
        DataFrame with normalized columns
    """
    # Expected standard columns
    standard_cols = ['timestamp', 'x', 'y', 'pupil_diameter']
    
    # Try to map existing columns to standard names
    column_mapping = {
        'time': 'timestamp',
        't': 'timestamp',
        'time_ms': 'timestamp',
        'pupil': 'pupil_diameter',
        'pupil_size': 'pupil_diameter',
        'px': 'x',
        'x_pos': 'x',
        'py': 'y',
        'y_pos': 'y'
    }
    
    # Rename columns based on mapping
    rename_map = {}
    for old_name, new_name in column_mapping.items():
        if old_name in df.columns:
            rename_map[old_name] = new_name
    
    df = df.rename(columns=rename_map)
    
    # Ensure standard columns exist
    for col in standard_cols:
        if col not in df.columns:
            if col == 'pupil_diameter' and 'pupil' in df.columns:
                df[col] = df['pupil']
            elif col == 'timestamp' and 'time' in df.columns:
                df[col] = df['time']
            elif col == 'x' and 'px' in df.columns:
                df[col] = df['px']
            elif col == 'y' and 'py' in df.columns:
                df[col] = df['py']
            else:
                # Create placeholder if missing
                logger.warning(f"Column {col} not found, creating placeholder")
                df[col] = np.nan
    
    # Select and order columns
    df = df[standard_cols].copy()
    
    # Convert types
    df['timestamp'] = pd.to_numeric(df['timestamp'], errors='coerce')
    df['pupil_diameter'] = pd.to_numeric(df['pupil_diameter'], errors='coerce')
    df['x'] = pd.to_numeric(df['x'], errors='coerce')
    df['y'] = pd.to_numeric(df['y'], errors='coerce')
    
    return df

def save_to_csv(df: pd.DataFrame, output_path: Path):
    """
    Save DataFrame to CSV file.
    
    Args:
        df: DataFrame to save
        output_path: Path to output file
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False)
    logger.info(f"Saved {len(df)} rows to {output_path}")

def process_single_file(input_path: Path, output_dir: Path, config: Dict[str, Any]) -> Path:
    """
    Process a single input file: load, normalize, and save.
    
    Args:
        input_path: Path to input CSV file
        output_dir: Directory to save processed file
        config: Configuration dictionary
        
    Returns:
        Path to output file
    """
    # Load data
    df = pd.read_csv(input_path)
    
    # Normalize columns
    df_normalized = normalize_columns(df, config)
    
    # Generate output filename
    output_filename = input_path.stem + "_normalized.csv"
    output_path = output_dir / output_filename
    
    # Save
    save_to_csv(df_normalized, output_path)
    
    return output_path

def run_loading_pipeline(config: Dict[str, Any]):
    """
    Run the full data loading pipeline.
    
    Args:
        config: Configuration dictionary
    """
    raw_data_dir = Path(config['paths']['raw_data'])
    processed_data_dir = Path(config['paths']['processed_data'])
    
    if not raw_data_dir.exists():
        logger.error(f"Raw data directory not found: {raw_data_dir}")
        return
    
    # Load all raw files
    data_files = list(raw_data_dir.glob("*.csv"))
    
    if not data_files:
        # If no raw data, create a minimal features file for testing
        logger.warning("No raw CSV files found. Creating minimal processed data structure.")
        processed_data_dir.mkdir(parents=True, exist_ok=True)
        features_df = pd.DataFrame(columns=['subject_id', 'trial_id', 'search_time', 
                                            'fixation_count', 'target_salience', 'status'])
        features_df.to_csv(processed_data_dir / 'features.csv', index=False)
        return
    
    # Process each file
    for input_file in data_files:
        logger.info(f"Processing {input_file}")
        process_single_file(input_file, processed_data_dir, config)
    
    logger.info("Data loading pipeline completed")

def main():
    """Main entry point for data loading."""
    parser = argparse.ArgumentParser(description="Load and normalize raw eye-tracking data")
    parser.add_argument("--config", type=str, default="code/config.yaml", 
                      help="Path to configuration file")
    args = parser.parse_args()
    
    config = load_config(Path(args.config))
    run_loading_pipeline(config)

if __name__ == "__main__":
    main()