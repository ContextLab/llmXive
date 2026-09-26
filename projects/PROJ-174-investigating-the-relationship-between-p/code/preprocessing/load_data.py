import os
import sys
import logging
import argparse
from pathlib import Path
from typing import Optional, Dict, Any, List
import pandas as pd
import numpy as np

# Import config loader from project root
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from config import load_config
from logging_config import get_logger

# Constants for output
UNIFIED_OUTPUT_PATH = "data/processed/unified_eye_tracking.csv"

def load_raw_data_from_dataset(source_path: str) -> pd.DataFrame:
    """
    Ingest raw files from verified eye-tracking sources.
    Handles common formats (CSV, TSV) and normalizes column names.
    
    Args:
        source_path: Path to the raw data file or directory of files.
        
    Returns:
        DataFrame with raw data.
        
    Raises:
        FileNotFoundError: If source path does not exist.
        ValueError: If no valid data files are found.
    """
    source = Path(source_path)
    if not source.exists():
        raise FileNotFoundError(f"Source path not found: {source}")
    
    dataframes = []
    
    if source.is_file():
        files = [source]
    elif source.is_dir():
        # Look for common data extensions
        files = list(source.glob("*.csv")) + list(source.glob("*.tsv")) + list(source.glob("*.txt"))
    else:
        raise ValueError(f"Invalid source path type: {source}")
    
    if not files:
        raise ValueError(f"No valid data files found in {source}")
    
    logger = get_logger()
    
    for file_path in files:
        try:
            if file_path.suffix.lower() in ['.csv']:
                df = pd.read_csv(file_path)
            elif file_path.suffix.lower() in ['.tsv', '.txt']:
                df = pd.read_csv(file_path, sep='\t')
            else:
                logger.warning(f"Skipping unsupported file format: {file_path}")
                continue
            
            # Basic validation
            if df.empty:
                logger.warning(f"File {file_path} is empty, skipping.")
                continue
                
            dataframes.append(df)
        except Exception as e:
            logger.error(f"Error reading {file_path}: {e}")
            continue
    
    if not dataframes:
        raise ValueError("No valid data could be loaded from the source.")
        
    return pd.concat(dataframes, ignore_index=True)

def normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    """
    Normalize column names to the standard schema:
    timestamp, x, y, pupil_diameter
    
    Args:
        df: Raw DataFrame.
        
    Returns:
        Normalized DataFrame.
        
    Raises:
        ValueError: If required columns are missing after normalization.
    """
    logger = get_logger()
    df = df.copy()
    df.columns = df.columns.str.lower().str.strip()
    
    # Mapping strategies for common column names
    mappings = {
        'timestamp': ['timestamp', 'time', 'time_ms', 'time_sec', 't', 'sample_time'],
        'x': ['x', 'x_pos', 'x_coordinate', 'horizontal', 'x_eye'],
        'y': ['y', 'y_pos', 'y_coordinate', 'vertical', 'y_eye'],
        'pupil_diameter': ['pupil_diameter', 'pupil', 'pupil_size', 'pupil_mm', 'diam', 'pupil_dia']
    }
    
    normalized_map = {}
    
    for std_name, candidates in mappings.items():
        found = False
        for candidate in candidates:
            if candidate in df.columns:
                normalized_map[std_name] = candidate
                found = True
                logger.debug(f"Mapped '{candidate}' to '{std_name}'")
                break
        
        if not found:
            # Try fuzzy match (contains)
            for col in df.columns:
                if any(cand in col for cand in candidates):
                    normalized_map[std_name] = col
                    logger.debug(f"Fuzzy matched '{col}' to '{std_name}'")
                    found = True
                    break
        
        if not found:
            logger.error(f"Could not find column for standard '{std_name}'")
            raise ValueError(f"Missing required column mapping for '{std_name}'. "
                           f"Found columns: {list(df.columns)}")
    
    # Rename columns
    rename_dict = {v: k for k, v in normalized_map.items()}
    df = df.rename(columns=rename_dict)
    
    # Ensure numeric types
    numeric_cols = ['timestamp', 'x', 'y', 'pupil_diameter']
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
    
    return df[['timestamp', 'x', 'y', 'pupil_diameter']]

def save_to_csv(df: pd.DataFrame, output_path: str) -> None:
    """
    Save the unified DataFrame to CSV.
    
    Args:
        df: Processed DataFrame.
        output_path: Destination path.
    """
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False)
    logging.getLogger(__name__).info(f"Saved unified data to {output_path}")

def process_single_file(input_path: str, output_path: str) -> None:
    """
    Process a single input file and save the unified output.
    
    Args:
        input_path: Path to raw input.
        output_path: Path for unified output.
    """
    logger = get_logger()
    logger.info(f"Processing {input_path} -> {output_path}")
    
    raw_df = load_raw_data_from_dataset(input_path)
    logger.info(f"Loaded {len(raw_df)} rows from {input_path}")
    
    normalized_df = normalize_columns(raw_df)
    logger.info(f"Normalized to standard schema ({len(normalized_df)} rows)")
    
    save_to_csv(normalized_df, output_path)

def run_loading_pipeline(config: Dict[str, Any] = None) -> None:
    """
    Main pipeline entry point for data loading.
    Reads configuration, finds raw data, and produces unified CSV.
    
    Args:
        config: Optional config dict. If None, loads from code/config.yaml.
    """
    logger = get_logger()
    logger.info("Starting data loading pipeline")
    
    if config is None:
        config = load_config()
    
    # Determine input source
    paths_cfg = config.get('paths', {})
    raw_data_path = paths_cfg.get('raw_data', 'data/raw')
    
    # Determine output path
    output_path = paths_cfg.get('unified_data', UNIFIED_OUTPUT_PATH)
    
    logger.info(f"Input source: {raw_data_path}")
    logger.info(f"Output target: {output_path}")
    
    if not Path(raw_data_path).exists():
        raise FileNotFoundError(f"Raw data directory not found: {raw_data_path}. "
                              "Please run verify_data_availability.py first.")
    
    process_single_file(raw_data_path, output_path)
    
    logger.info("Data loading pipeline completed successfully")

def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(description="Load and unify raw eye-tracking data.")
    parser.add_argument('--config', type=str, default='code/config.yaml',
                      help='Path to configuration file')
    parser.add_argument('--input', type=str, default=None,
                      help='Override input path')
    parser.add_argument('--output', type=str, default=None,
                      help='Override output path')
    
    args = parser.parse_args()
    
    # Load config
    config = load_config(args.config)
    
    # Override paths if provided
    if args.input:
        if 'paths' not in config:
            config['paths'] = {}
        config['paths']['raw_data'] = args.input
    if args.output:
        if 'paths' not in config:
            config['paths'] = {}
        config['paths']['unified_data'] = args.output
    
    run_loading_pipeline(config)

if __name__ == "__main__":
    main()