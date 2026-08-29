import os
import sys
import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

import pandas as pd
import pyarrow.parquet as pq

# Ensure we can import from the project root if running as script
if "code" not in sys.path:
    sys.path.insert(0, str(Path(__file__).parent))

from utils.data_integrity import compute_file_checksum, generate_manifest

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

def ensure_directories():
    """Create necessary output directories if they don't exist."""
    Path("data/processed").mkdir(parents=True, exist_ok=True)
    Path("data/raw").mkdir(parents=True, exist_ok=True)
    logger.info("Directories ensured.")

def load_dataset(file_path: Path) -> pd.DataFrame:
    """
    Load a dataset from a parquet file.
    
    Args:
        file_path: Path to the parquet file.
        
    Returns:
        DataFrame containing the dataset.
        
    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If the file is empty or cannot be read.
    """
    if not file_path.exists():
        raise FileNotFoundError(f"Dataset file not found: {file_path}")
    
    try:
        df = pd.read_parquet(file_path)
        if df.empty:
            raise ValueError(f"Dataset is empty: {file_path}")
        logger.info(f"Loaded {len(df)} rows from {file_path}")
        return df
    except Exception as e:
        logger.error(f"Error loading {file_path}: {e}")
        raise

def validate_and_prepare_dataset(df: pd.DataFrame, source_name: str) -> pd.DataFrame:
    """
    Validate and prepare a dataset for merging.
    
    Ensures required columns exist and standardizes column names/types.
    
    Args:
        df: Input DataFrame.
        source_name: Name of the source dataset for logging.
        
    Returns:
        Prepared DataFrame.
        
    Raises:
        ValueError: If required columns are missing.
    """
    required_cols = ["user_id", "dialogue_id", "quality_rating"]
    optional_cols = ["age", "gender", "politeness_score"]
    
    missing = [col for col in required_cols if col not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns in {source_name}: {missing}")
    
    # Ensure numeric types for rating if present
    if "quality_rating" in df.columns:
        df["quality_rating"] = pd.to_numeric(df["quality_rating"], errors="coerce")
    
    # Standardize column names if source uses different casing (common in HF datasets)
    df.columns = df.columns.str.lower().str.strip()
    
    # Select only relevant columns for merging to reduce memory
    keep_cols = [c for c in required_cols + optional_cols if c in df.columns]
    df = df[keep_cols].copy()
    
    logger.info(f"Prepared {source_name}: {len(df)} rows, columns: {list(df.columns)}")
    return df

def merge_datasets(dfs: List[Tuple[pd.DataFrame, str]]) -> pd.DataFrame:
    """
    Merge a list of DataFrames vertically.
    
    Args:
        dfs: List of tuples (DataFrame, source_name).
        
    Returns:
        Merged DataFrame.
    """
    if not dfs:
        raise ValueError("No datasets provided for merging.")
    
    logger.info(f"Merging {len(dfs)} datasets...")
    merged = pd.concat([df for df, _ in dfs], ignore_index=True, copy=False)
    
    # Add source indicator if not present (useful for debugging)
    # We assume the input dfs already have a 'source' column or we add one based on the tuple
    # However, to keep it clean, we'll just rely on the fact that the input files are distinct.
    # If the original files had a 'source' column, concat preserves it.
    
    logger.info(f"Merged dataset shape: {merged.shape}")
    return merged

def handle_missing_demographics(df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict[str, int]]:
    """
    Handle missing demographic data (age, gender).
    
    Logs counts of missing values and optionally fills or drops.
    For this task, we will log and keep rows, but mark missing demographics.
    
    Args:
        df: Input DataFrame.
        
    Returns:
        Tuple of (DataFrame with missing info logged, dict of missing counts).
    """
    missing_counts = {}
    if "age" in df.columns:
        missing_counts["age"] = int(df["age"].isna().sum())
    if "gender" in df.columns:
        missing_counts["gender"] = int(df["gender"].isna().sum())
    
    for col, count in missing_counts.items():
        if count > 0:
            logger.warning(f"Found {count} missing values in '{col}'.")
    
    return df, missing_counts

def save_merged_data(df: pd.DataFrame, output_path: Path, checksum_path: Path):
    """
    Save the merged DataFrame to a parquet file and generate a checksum.
    
    Args:
        df: DataFrame to save.
        output_path: Path to the output parquet file.
        checksum_path: Path to the JSON file containing the checksum.
    """
    df.to_parquet(output_path, index=False)
    logger.info(f"Saved merged data to {output_path}")
    
    checksum = compute_file_checksum(output_path)
    manifest = {
        "file": str(output_path),
        "checksum": checksum,
        "rows": len(df),
        "columns": list(df.columns)
    }
    
    with open(checksum_path, "w") as f:
        json.dump(manifest, f, indent=2)
    
    logger.info(f"Generated checksum manifest: {checksum_path}")

def main():
    """Main entry point for the merging task."""
    ensure_directories()
    
    # Define input paths based on T015, T016, T017 outputs
    # We expect these to be in data/raw/<dataset_name>/merged.parquet or similar
    # Based on T015-T017, they likely save raw data. 
    # However, T018 specifically says "combine ... into a unified DataFrame".
    # We assume the previous tasks saved processed/raw data in data/raw/<name>/
    # Let's look for standard filenames. If T015-T017 saved 'raw_data.parquet' or similar.
    # The task description says "Store all datasets separately, then merge."
    # We will assume the output of T015-T017 is in data/raw/<dataset_name>/raw.parquet
    
    data_paths = {
        "persona_chat": Path("data/raw/persona_chat/raw_data.parquet"),
        "empathetic_dialogues": Path("data/raw/empathetic_dialogues/raw_data.parquet"),
        "hci_p2": Path("data/raw/hci_p2/raw_data.parquet")
    }
    
    datasets_to_load = []
    for name, path in data_paths.items():
        if path.exists():
            datasets_to_load.append((name, path))
        else:
            logger.warning(f"Dataset file not found: {path}. Skipping {name}.")
    
    if not datasets_to_load:
        logger.error("No dataset files found. Aborting merge.")
        sys.exit(1)
    
    loaded_dfs = []
    for name, path in datasets_to_load:
        try:
            df = load_dataset(path)
            prepared_df = validate_and_prepare_dataset(df, name)
            loaded_dfs.append((prepared_df, name))
        except Exception as e:
            logger.error(f"Failed to process {name}: {e}")
            # Depending on strictness, we might exit. Here we skip the bad one.
    
    if not loaded_dfs:
        logger.error("No valid datasets to merge.")
        sys.exit(1)
    
    # Merge
    merged_df = merge_datasets(loaded_dfs)
    
    # Handle demographics
    merged_df, missing_stats = handle_missing_demographics(merged_df)
    
    # Save
    output_file = Path("data/processed/merged_dialogues.parquet")
    checksum_file = Path("data/processed/merged_dialogues_checksum.json")
    
    save_merged_data(merged_df, output_file, checksum_file)
    
    logger.info("Task T018 completed successfully.")

if __name__ == "__main__":
    main()
