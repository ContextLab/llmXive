import os
import sys
import logging
import argparse
from pathlib import Path
from typing import Optional, Dict, Any, List
import pandas as pd
import numpy as np
from datasets import load_dataset

from config import load_config

# Ensure logging is configured before use
try:
    from logging_config import get_logger
    logger = get_logger("load_data")
except ImportError:
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger("load_data")

def load_raw_data_from_dataset(dataset_id: str, split: str = "train") -> pd.DataFrame:
    """
    Ingest raw data from a verified OpenNeuro dataset using the HuggingFace datasets library.
    This function handles the streaming/download of the real dataset to ensure no synthetic data is used.
    
    Args:
        dataset_id: The OpenNeuro dataset ID (e.g., 'ds00XXXX').
        split: The dataset split to load (default: 'train').
    
    Returns:
        A pandas DataFrame containing the raw eye-tracking data.
    
    Raises:
        RuntimeError: If the dataset cannot be found or loaded.
    """
    logger.info(f"Attempting to load raw dataset: {dataset_id}, split: {split}")
    
    try:
        # Load dataset using streaming to handle large files efficiently
        # This fetches REAL data from the HuggingFace hub
        ds = load_dataset(dataset_id, split=split, streaming=True)
        
        # Convert the first few chunks to a DataFrame to verify structure
        # We assume the dataset contains a key 'data' or similar with eye-tracking columns
        # If the structure is unknown, we attempt to find the first available table
        table_name = None
        for key in ds:
            table_name = key
            break

        if table_name is None:
            raise RuntimeError(f"Dataset {dataset_id} has no available tables.")

        # Load the specific table
        df = ds[table_name].to_pandas()
        
        if df.empty:
            raise RuntimeError(f"Dataset {dataset_id} table '{table_name}' is empty.")

        logger.info(f"Successfully loaded {len(df)} rows from {dataset_id}")
        return df

    except Exception as e:
        logger.error(f"Failed to load dataset {dataset_id}: {str(e)}")
        raise RuntimeError(f"Failed to load verified dataset {dataset_id}. Pipeline cannot proceed without real data.") from e

def normalize_columns(df: pd.DataFrame, config: Dict[str, Any]) -> pd.DataFrame:
    """
    Normalize column names to the uniform schema required by the pipeline.
    
    Expected output columns: timestamp, x, y, pupil_diameter
    
    Args:
        df: The raw DataFrame.
        config: Configuration dictionary containing column mappings.
    
    Returns:
        A DataFrame with normalized columns.
    """
    logger.info("Normalizing data columns...")
    
    # Define standard mapping based on common OpenNeuro formats (e.g., ASL, EyeLink)
    # The config can override these if specific datasets use different naming
    col_map = config.get('column_mapping', {
        'time': ['timestamp', 'time', 't', 'trial_time'],
        'x': ['x', 'x_coord', 'eye_x', 'position_x'],
        'y': ['y', 'y_coord', 'eye_y', 'position_y'],
        'pupil': ['pupil_diameter', 'pupil', 'pupil_size', 'diam', 'pupil_mm']
    })
    
    def find_column(df, candidates):
        for cand in candidates:
            if cand in df.columns:
                return cand
        return None

    # Map columns
    mapped = {}
    for standard_name, candidates in col_map.items():
        found = find_column(df, candidates)
        if found:
            mapped[standard_name] = found
        else:
            # Try to find a case-insensitive match
            for col in df.columns:
                if col.lower() in [c.lower() for c in candidates]:
                    mapped[standard_name] = col
                    break

    if len(mapped) < 4:
        missing = set(mapped.keys()) ^ {'timestamp', 'x', 'y', 'pupil_diameter'}
        raise ValueError(f"Cannot find columns for: {missing}. Available columns: {list(df.columns)}")
    
    # Rename
    rename_map = {mapped[k]: k for k in mapped}
    df_normalized = df.rename(columns=rename_map)
    
    # Ensure types
    df_normalized['timestamp'] = pd.to_numeric(df_normalized['timestamp'], errors='coerce')
    df_normalized['x'] = pd.to_numeric(df_normalized['x'], errors='coerce')
    df_normalized['y'] = pd.to_numeric(df_normalized['y'], errors='coerce')
    df_normalized['pupil_diameter'] = pd.to_numeric(df_normalized['pupil_diameter'], errors='coerce')
    
    # Drop rows with missing critical data
    df_normalized = df_normalized.dropna(subset=['timestamp', 'pupil_diameter'])
    
    logger.info(f"Normalized columns: {list(df_normalized.columns)}")
    return df_normalized

def save_to_csv(df: pd.DataFrame, output_path: Path):
    """
    Save the normalized DataFrame to a CSV file.
    
    Args:
        df: The DataFrame to save.
        output_path: The path to the output file.
    """
    if not output_path.parent.exists():
        logger.info(f"Creating directory: {output_path.parent}")
        output_path.parent.mkdir(parents=True, exist_ok=True)
    
    logger.info(f"Saving processed data to: {output_path}")
    df.to_csv(output_path, index=False)
    logger.info(f"Saved {len(df)} rows to {output_path}")

def process_single_file(dataset_id: str, output_path: Path, config: Dict[str, Any]):
    """
    Process a single dataset: load, normalize, and save.
    
    Args:
        dataset_id: The OpenNeuro dataset ID.
        output_path: Path to the output CSV.
        config: Configuration dictionary.
    """
    logger.info(f"Processing dataset: {dataset_id}")
    
    # Load real data
    raw_df = load_raw_data_from_dataset(dataset_id)
    
    # Normalize
    norm_df = normalize_columns(raw_df, config)
    
    # Save
    save_to_csv(norm_df, output_path)
    
    logger.info(f"Successfully processed {dataset_id} -> {output_path}")

def run_loading_pipeline(config_path: Optional[str] = None):
    """
    Main pipeline entry point for data loading.
    
    Reads config.yaml to determine which datasets to load and where to save them.
    
    Args:
        config_path: Path to the configuration file. Defaults to 'code/config.yaml'.
    """
    if config_path is None:
        config_path = Path(__file__).parent.parent / "config.yaml"
    
    config_path = Path(config_path)
    
    if not config_path.exists():
        raise FileNotFoundError(f"Configuration file not found at {config_path}")
    
    config = load_config(config_path)
    
    # Get list of datasets to process from config
    datasets_to_process = config.get('datasets', [])
    output_dir = Path(config.get('paths', {}).get('processed', 'data/processed'))
    
    if not datasets_to_process:
        logger.warning("No datasets configured in config.yaml. Nothing to process.")
        return

    logger.info(f"Starting loading pipeline for {len(datasets_to_process)} datasets...")
    
    for ds_config in datasets_to_process:
        dataset_id = ds_config.get('id')
        if not dataset_id:
            logger.warning("Skipping entry without 'id' in config.")
            continue

        output_filename = ds_config.get('output_filename', f"{dataset_id}_processed.csv")
        output_path = output_dir / output_filename

        try:
            process_single_file(dataset_id, output_path, config)
        except Exception as e:
            logger.error(f"Failed to process dataset {dataset_id}: {e}")
            # Fail loudly as per constraints - do not continue with partial data if critical
            raise

def main():
    """Command line entry point."""
    parser = argparse.ArgumentParser(description="Load and normalize raw eye-tracking data.")
    parser.add_argument('--config', type=str, default=None, help='Path to config.yaml')
    args = parser.parse_args()
    
    run_loading_pipeline(args.config)

if __name__ == "__main__":
    main()
