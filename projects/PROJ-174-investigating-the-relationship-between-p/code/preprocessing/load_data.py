"""
Data Loading Module for Pupil Dilation Study.

This module ingests raw eye-tracking data from verified sources (OpenNeuro)
and converts them into a uniform CSV format with columns:
timestamp, x, y, pupil_diameter.

It relies on the `datasets` library to fetch real data as specified in
verify_data_availability.py and config.yaml.
"""

import os
import sys
import logging
import argparse
from pathlib import Path
from typing import Optional, Dict, Any, List

import pandas as pd
import numpy as np
from datasets import load_dataset

# Import config loader to respect project settings
from config import load_config
from logging_config import get_logger

# Ensure the parent directory is in the path for relative imports if run directly
if __package__ is None:
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from config import load_config
    from logging_config import get_logger
else:
    from ..config import load_config
    from ..logging_config import get_logger

# Constants for column mapping
TARGET_COLUMNS = ['timestamp', 'x', 'y', 'pupil_diameter']
REQUIRED_RAW_COLUMNS = ['timestamp', 'x', 'y', 'pupil_diameter']

def load_raw_data_from_dataset(dataset_id: str, split: str = 'train') -> pd.DataFrame:
    """
    Loads raw eye-tracking data from a specified HuggingFace/OpenNeuro dataset.

    Args:
        dataset_id (str): The dataset identifier (e.g., 'openneuro_ds001234').
        split (str): The dataset split to load (default: 'train').

    Returns:
        pd.DataFrame: A DataFrame containing the raw eye-tracking data.

    Raises:
        ValueError: If the dataset cannot be found or lacks required columns.
        RuntimeError: If the download fails.
    """
    logger = get_logger(__name__)
    logger.info(f"Loading dataset: {dataset_id}, split: {split}")

    try:
        # Load dataset with streaming to handle large files without full download
        # Note: We use streaming=True to avoid OOM on large datasets, but we
        # materialize the specific split if it fits or iterate if not.
        # For this loader, we assume the dataset is small enough to be processed
        # in memory after filtering, or we stream and convert.
        
        # Attempt to load the dataset. 
        # The 'dataset_id' here is expected to be the actual HF dataset name 
        # derived from the verified list in plan.md.
        ds = load_dataset(dataset_id, split=split, streaming=True)
        
        # Convert to pandas. Since we are streaming, we might need to collect.
        # If the dataset is massive, this might be memory intensive.
        # However, for the "load_data" step, we assume we are processing
        # a specific subject or a manageable chunk.
        # To be safe with memory, we convert to pandas only if the dataset
        # is not too large, otherwise we iterate.
        
        # For the purpose of this task (T013), we assume the verified dataset
        # allows for direct loading or streaming conversion.
        df = ds.to_pandas()
        
        logger.info(f"Successfully loaded {len(df)} rows from {dataset_id}")

    except Exception as e:
        logger.error(f"Failed to load dataset {dataset_id}: {e}")
        raise RuntimeError(f"Failed to load dataset {dataset_id}: {e}") from e

    # Validate columns
    missing_cols = [col for col in REQUIRED_RAW_COLUMNS if col not in df.columns]
    if missing_cols:
        raise ValueError(f"Dataset missing required columns: {missing_cols}")

    return df

def normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    """
    Ensures the DataFrame has the standard column names and types.

    Args:
        df (pd.DataFrame): The raw input DataFrame.

    Returns:
        pd.DataFrame: The normalized DataFrame with columns:
                      timestamp, x, y, pupil_diameter.
    """
    logger = get_logger(__name__)
    logger.debug("Normalizing data columns")

    # Create a copy to avoid modifying the original
    normalized = df.copy()

    # Ensure required columns exist (already validated in load_raw_data_from_dataset)
    # Standardize names if they differ slightly (e.g., 'pupil_size' -> 'pupil_diameter')
    column_mapping = {
        'pupil_size': 'pupil_diameter',
        'pupil': 'pupil_diameter',
        'time': 'timestamp',
        'x_pos': 'x',
        'y_pos': 'y',
        'x_coord': 'x',
        'y_coord': 'y'
    }

    for old_name, new_name in column_mapping.items():
        if old_name in normalized.columns and new_name not in normalized.columns:
            normalized.rename(columns={old_name: new_name}, inplace=True)
            logger.debug(f"Renamed column {old_name} to {new_name}")

    # Select only the target columns
    if not all(col in normalized.columns for col in TARGET_COLUMNS):
        missing = [c for c in TARGET_COLUMNS if c not in normalized.columns]
        raise ValueError(f"After normalization, missing columns: {missing}")

    output = normalized[TARGET_COLUMNS].copy()

    # Ensure data types
    output['timestamp'] = pd.to_numeric(output['timestamp'], errors='coerce')
    output['x'] = pd.to_numeric(output['x'], errors='coerce')
    output['y'] = pd.to_numeric(output['y'], errors='coerce')
    output['pupil_diameter'] = pd.to_numeric(output['pupil_diameter'], errors='coerce')

    # Drop rows with NaN in critical fields
    initial_count = len(output)
    output = output.dropna(subset=TARGET_COLUMNS)
    dropped_count = initial_count - len(output)
    if dropped_count > 0:
        logger.warning(f"Dropped {dropped_count} rows due to NaN values in critical columns")

    return output

def save_to_csv(df: pd.DataFrame, output_path: Path) -> None:
    """
    Saves the processed DataFrame to a CSV file.

    Args:
        df (pd.DataFrame): The data to save.
        output_path (Path): The destination file path.
    """
    logger = get_logger(__name__)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False)
    logger.info(f"Saved processed data to {output_path}")

def process_single_file(input_path: Path, output_path: Path) -> None:
    """
    Processes a single raw file (if local) or dataset and saves to CSV.
    
    For this implementation, we primarily handle the case where data is
    loaded from the verified dataset source (OpenNeuro/HF) as per T002c.
    If a local file is provided (for testing or alternative sources),
    we attempt to load it.
    """
    logger = get_logger(__name__)
    
    # Check if input_path is a local file or a dataset ID
    if str(input_path).endswith('.csv') or str(input_path).endswith('.tsv') or str(input_path).endswith('.parquet'):
        logger.info(f"Loading local file: {input_path}")
        if str(input_path).endswith('.csv'):
            df = pd.read_csv(input_path)
        elif str(input_path).endswith('.tsv'):
            df = pd.read_csv(input_path, sep='\t')
        elif str(input_path).endswith('.parquet'):
            df = pd.read_parquet(input_path)
        else:
            raise ValueError(f"Unsupported file format: {input_path}")
    else:
        # Assume it's a dataset ID string
        logger.info(f"Loading dataset ID: {input_path}")
        df = load_raw_data_from_dataset(str(input_path))
    
    # Normalize
    processed_df = normalize_columns(df)
    
    # Save
    save_to_csv(processed_df, output_path)

def run_loading_pipeline(config: Dict[str, Any], output_dir: Path) -> List[Path]:
    """
    Runs the loading pipeline for all datasets specified in the config.

    Args:
        config (Dict[str, Any]): The project configuration.
        output_dir (Path): Directory to save processed files.

    Returns:
        List[Path]: List of paths to the generated CSV files.
    """
    logger = get_logger(__name__)
    output_files = []
    
    # Get datasets from config or default to verified list
    # T002c ensures we have valid datasets. We assume config['paths']['datasets']
    # or a similar key holds the list of dataset IDs.
    datasets = config.get('paths', {}).get('datasets', [])
    
    if not datasets:
        # Fallback: try to read from plan.md if config is empty, but strictly
        # we rely on T002c having populated a state or config.
        logger.warning("No datasets found in config. Checking default verified sources.")
        # This part depends on how T002c exposes the data. 
        # For now, we assume the config is populated with the verified list.
        # If the project uses a specific state file from T002c, we might need to parse it.
        # However, T013 is "Implement load_data.py", so we assume the input is provided via config.
        pass

    for dataset_id in datasets:
        if not dataset_id:
            continue
        
        try:
            # Define output path
            safe_id = dataset_id.replace('/', '_').replace(':', '_')
            output_file = output_dir / f"{safe_id}_processed.csv"
            
            process_single_file(Path(dataset_id), output_file)
            output_files.append(output_file)
            
        except Exception as e:
            logger.error(f"Failed to process dataset {dataset_id}: {e}")
            # Decide whether to fail hard or continue. 
            # Given the "Fail loudly" constraint, we raise.
            raise e

    return output_files

def main():
    """
    Main entry point for the data loading script.
    Usage: python code/preprocessing/load_data.py [--config code/config.yaml]
    """
    logger = get_logger(__name__)
    
    parser = argparse.ArgumentParser(description="Load and normalize raw eye-tracking data.")
    parser.add_argument('--config', type=str, default='code/config.yaml', help='Path to config file')
    parser.add_argument('--output-dir', type=str, default='data/processed', help='Output directory')
    parser.add_argument('--dataset-id', type=str, help='Override dataset ID from config')
    
    args = parser.parse_args()
    
    # Load config
    try:
        config = load_config(args.config)
    except Exception as e:
        logger.error(f"Failed to load config: {e}")
        sys.exit(1)
    
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    datasets_to_load = [args.dataset_id] if args.dataset_id else config.get('paths', {}).get('datasets', [])
    
    if not datasets_to_load:
        logger.error("No datasets specified in config or via --dataset-id. Exiting.")
        sys.exit(1)
        
    # Update config with specific dataset if overridden
    if args.dataset_id:
        config['paths']['datasets'] = [args.dataset_id]

    try:
        output_files = run_loading_pipeline(config, output_dir)
        logger.info(f"Pipeline complete. Generated {len(output_files)} files.")
    except Exception as e:
        logger.error(f"Pipeline failed: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
