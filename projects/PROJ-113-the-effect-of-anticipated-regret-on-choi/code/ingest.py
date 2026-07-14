"""
Data ingestion utilities for the Anticipated Regret project.
Handles loading from HuggingFace, applying deferral flags, and generating processed datasets.
"""
import hashlib
import json
import os
import requests
import logging
from pathlib import Path
from typing import Dict, Any, Optional, Tuple

import pandas as pd
from datasets import load_dataset

from config import get_project_root, get_path, ensure_paths_exist, get_dataset_url, get_config
from features import add_regret_and_loss_metrics, add_perceived_risk_covariate

# Configure logging
logger = logging.getLogger(__name__)

def get_project_root() -> Path:
    """Return the project root directory."""
    return Path(__file__).resolve().parent.parent

def load_and_checksum(url: str, output_path: Optional[Path] = None) -> Tuple[str, Path]:
    """
    Download a file from URL, compute its SHA256 checksum, and save it.
    Returns the checksum and the path to the saved file.
    """
    logger.info(f"Downloading and checksumming: {url}")
    if output_path is None:
        output_path = get_path("data/raw/downloaded_file.bin")
    
    ensure_paths_exist([output_path])
    
    response = requests.get(url, stream=True)
    response.raise_for_status()
    
    sha256_hash = hashlib.sha256()
    with open(output_path, "wb") as f:
        for chunk in response.iter_content(chunk_size=8192):
            sha256_hash.update(chunk)
            f.write(chunk)
    
    checksum = sha256_hash.hexdigest()
    
    checksums_path = get_path("data/raw/checksums.json")
    ensure_paths_exist([checksums_path])
    
    checksums = {}
    if checksums_path.exists():
        with open(checksums_path, "r") as f:
            checksums = json.load(f)
    
    checksums[url] = {
        "checksum": checksum,
        "path": str(output_path)
    }
    
    with open(checksums_path, "w") as f:
        json.dump(checksums, f, indent=2)
    
    logger.info(f"Checksum for {url}: {checksum}")
    return checksum, output_path

def load_huggingface_dataset(dataset_name: str, split: str = "train") -> pd.DataFrame:
    """
    Load a dataset from HuggingFace and convert to pandas DataFrame.
    
    Args:
        dataset_name: Name of the dataset on HuggingFace (e.g., 'zhehuderek/textual_decisionmaking_data')
        split: Dataset split to load (default: 'train')
        
    Returns:
        pandas DataFrame containing the dataset
    """
    logger.info(f"Loading HuggingFace dataset: {dataset_name} (split: {split})")
    
    try:
        dataset = load_dataset(dataset_name, split=split)
        df = dataset.to_pandas()
        logger.info(f"Loaded {len(df)} rows from {dataset_name}")
        return df
    except Exception as e:
        logger.error(f"Failed to load dataset {dataset_name}: {e}")
        raise

def apply_deferral_flags(df: pd.DataFrame, timeout_col: str = "timeout", action_col: str = "action") -> pd.DataFrame:
    """
    Apply deferral flags based on timeout without action.
    
    Args:
        df: Input DataFrame
        timeout_col: Name of the column indicating timeout (boolean or numeric)
        action_col: Name of the column indicating action taken
        
    Returns:
        DataFrame with 'deferral' column added (1 if deferred, 0 otherwise)
    """
    logger.info("Applying deferral flags")
    
    # Create deferral flag: 1 if timeout occurred without action, 0 otherwise
    # Assuming timeout is True/1 and action is None/empty for deferral
    if timeout_col in df.columns and action_col in df.columns:
        # If timeout is True and action is missing/empty, mark as deferral
        df['deferral'] = ((df[timeout_col] == True) | (df[timeout_col] == 1)) & (
            (df[action_col].isna()) | (df[action_col] == '') | (df[action_col].isnull())
        ).astype(int)
    else:
        # Fallback: if no timeout column, assume no deferrals
        logger.warning(f"Columns {timeout_col} or {action_col} not found. Setting all deferral=0")
        df['deferral'] = 0
    
    return df

def generate_regret_proxy_dataset(
    dataset_name: str = "zhehuderek/textual_decisionmaking_data",
    output_file: str = "data/processed/regret_proxy_v1.csv"
) -> None:
    """
    Main pipeline to load data, apply deferral flags, calculate regret proxy,
    and save the processed dataset.
    
    Args:
        dataset_name: HuggingFace dataset name
        output_file: Path to output CSV file
    """
    logger.info(f"Starting regret proxy generation pipeline for {dataset_name}")
    
    # Load raw data
    df = load_huggingface_dataset(dataset_name)
    
    # Apply deferral flags
    df = apply_deferral_flags(df)
    
    # Add regret and loss metrics (includes regret_proxy calculation)
    # This function is defined in features.py and handles the Min-Max Regret calculation
    df = add_regret_and_loss_metrics(df)
    
    # Add perceived risk covariate (handles missing data by calculating price_variance)
    df = add_perceived_risk_covariate(df)
    
    # Select required columns for output
    required_columns = ['regret_proxy', 'deferral']
    # Ensure all required columns exist
    for col in required_columns:
        if col not in df.columns:
            logger.error(f"Required column '{col}' not found in processed data")
            raise ValueError(f"Missing required column: {col}")
    
    output_df = df[required_columns].copy()
    
    # Ensure output directory exists
    output_path = get_path(output_file)
    ensure_paths_exist([output_path])
    
    # Save to CSV
    output_df.to_csv(output_path, index=False)
    logger.info(f"Saved processed dataset to {output_path} with {len(output_df)} rows")
    
    # Log summary statistics
    logger.info(f"Deferral rate: {output_df['deferral'].mean():.2%}")
    logger.info(f"Regret proxy range: [{output_df['regret_proxy'].min():.4f}, {output_df['regret_proxy'].max():.4f}]")

def main():
    """Main entry point for the ingestion script."""
    # Setup logging
    from utils.logging import setup_logging
    setup_logging()
    
    # Get configuration
    config = get_config()
    dataset_name = config.get('primary_dataset', 'zhehuderek/textual_decisionmaking_data')
    output_file = config.get('output_regret_proxy_file', 'data/processed/regret_proxy_v1.csv')
    
    try:
        generate_regret_proxy_dataset(dataset_name, output_file)
        logger.info("Pipeline completed successfully")
    except Exception as e:
        logger.error(f"Pipeline failed: {e}")
        raise

if __name__ == "__main__":
    main()
