import os
import sys
import json
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple

import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split

from src.config import get_project_root, ensure_directories

logger = logging.getLogger(__name__)

# Constants for split ratio and random seed
DISCOVERY_RATIO: float = 0.6  # 60% for discovery (gene selection)
TRAINING_RATIO: float = 0.4   # 40% for training (model fitting)
RANDOM_SEED: int = 42         # Fixed seed for reproducibility
STRATA_COLUMN: str = 'response_label' # Column used for stratification

def load_processed_data(file_path: Path) -> pd.DataFrame:
    """
    Load a processed data file (CSV or Parquet).
    
    Args:
        file_path: Path to the data file.
        
    Returns:
        DataFrame containing the data.
        
    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If the file format is unsupported.
    """
    if not file_path.exists():
        raise FileNotFoundError(f"Data file not found: {file_path}")
        
    suffix = file_path.suffix.lower()
    if suffix == '.csv':
        return pd.read_csv(file_path)
    elif suffix in ['.parquet', '.pq']:
        return pd.read_parquet(file_path)
    else:
        raise ValueError(f"Unsupported file format: {suffix}. Use .csv or .parquet.")

def save_processed_data(df: pd.DataFrame, file_path: Path) -> None:
    """
    Save a DataFrame to a CSV or Parquet file.
    
    Args:
        df: DataFrame to save.
        file_path: Destination path.
    """
    ensure_directories([file_path.parent])
    suffix = file_path.suffix.lower()
    if suffix == '.csv':
        df.to_csv(file_path, index=False)
    elif suffix in ['.parquet', '.pq']:
        df.to_parquet(file_path, index=False)
    else:
        # Default to CSV if extension is missing or unknown
        df.to_csv(file_path.with_suffix('.csv'), index=False)

def split_data_stratified(
    df: pd.DataFrame,
    strata_column: str = STRATA_COLUMN,
    discovery_ratio: float = DISCOVERY_RATIO,
    random_state: int = RANDOM_SEED
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Split data into discovery and training sets with stratification.
    
    This function ensures that the class distribution of the target variable
    (response_label) is maintained in both splits.
    
    Args:
        df: Input DataFrame containing gene expression and response labels.
        strata_column: Name of the column to use for stratification.
        discovery_ratio: Proportion of samples to include in the discovery set.
        random_state: Random seed for reproducibility.
        
    Returns:
        Tuple of (discovery_set, training_set) DataFrames.
        
    Raises:
        ValueError: If the stratification column is missing or has insufficient classes.
    """
    if strata_column not in df.columns:
        raise ValueError(f"Stratification column '{strata_column}' not found in data.")
    
    # Check for minimum class representation
    class_counts = df[strata_column].value_counts()
    if any(class_counts < 2):
        logger.warning(
            "Some classes have fewer than 2 samples. "
            "Stratified split might fail or produce empty sets for those classes."
        )
    
    # Perform stratified split
    try:
        discovery_set, training_set = train_test_split(
            df,
            test_size=(1 - discovery_ratio),
            stratify=df[strata_column],
            random_state=random_state
        )
        logger.info(
            f"Split completed: Discovery={len(discovery_set)}, "
            f"Training={len(training_set)} (Ratio: {len(discovery_set)/len(df):.2%})"
        )
    except ValueError as e:
        # Fallback if stratification fails due to small class sizes
        logger.warning(f"Stratified split failed: {e}. Attempting non-stratified split.")
        discovery_set, training_set = train_test_split(
            df,
            test_size=(1 - discovery_ratio),
            random_state=random_state
        )
        logger.info(
            f"Fallback split completed: Discovery={len(discovery_set)}, "
            f"Training={len(training_set)}"
        )
        
    return discovery_set, training_set

def save_split_data(
    discovery_set: pd.DataFrame,
    training_set: pd.DataFrame,
    tumor_type: str,
    output_dir: Path
) -> Dict[str, str]:
    """
    Save discovery and training sets to disk.
    
    Args:
        discovery_set: Discovery set DataFrame.
        training_set: Training set DataFrame.
        tumor_type: Name of the tumor type (used for filenames).
        output_dir: Directory to save files.
        
    Returns:
        Dictionary mapping set names to file paths.
    """
    # Ensure output directory exists
    ensure_directories([output_dir])
    
    # Define file paths
    discovery_path = output_dir / f"{tumor_type}_discovery_set.csv"
    training_path = output_dir / f"{tumor_type}_training_set.csv"
    
    # Save files
    save_processed_data(discovery_set, discovery_path)
    save_processed_data(training_set, training_path)
    
    logger.info(f"Saved discovery set to: {discovery_path}")
    logger.info(f"Saved training set to: {training_path}")
    
    return {
        "discovery": str(discovery_path),
        "training": str(training_path)
    }

def process_tumor_type_split(
    tumor_type: str,
    input_file: Path,
    output_dir: Path,
    strata_column: str = STRATA_COLUMN,
    discovery_ratio: float = DISCOVERY_RATIO
) -> Dict[str, Any]:
    """
    Process a single tumor type: load, split, and save data.
    
    Args:
        tumor_type: Name of the tumor type.
        input_file: Path to the preprocessed data file.
        output_dir: Directory to save split files.
        strata_column: Column to use for stratification.
        discovery_ratio: Proportion for discovery set.
        
    Returns:
        Dictionary containing split results and file paths.
    """
    logger.info(f"Processing split for tumor type: {tumor_type}")
    
    # Load data
    df = load_processed_data(input_file)
    logger.info(f"Loaded {len(df)} samples for {tumor_type}")
    
    # Split data
    discovery_set, training_set = split_data_stratified(
        df,
        strata_column=strata_column,
        discovery_ratio=discovery_ratio
    )
    
    # Save splits
    file_paths = save_split_data(
        discovery_set,
        training_set,
        tumor_type,
        output_dir
    )
    
    # Return summary
    return {
        "tumor_type": tumor_type,
        "total_samples": len(df),
        "discovery_samples": len(discovery_set),
        "training_samples": len(training_set),
        "discovery_path": file_paths["discovery"],
        "training_path": file_paths["training"],
        "class_distribution": {
            "discovery": discovery_set[strata_column].value_counts().to_dict(),
            "training": training_set[strata_column].value_counts().to_dict()
        }
    }

def main():
    """
    Main entry point for the data splitting stage.
    
    This function orchestrates the splitting of preprocessed data for all
    tumor types into discovery and training sets.
    """
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    project_root = get_project_root()
    processed_dir = project_root / "data" / "processed"
    output_dir = project_root / "data" / "processed" # Save in same directory
    
    # Ensure output directory exists
    ensure_directories([output_dir])
    
    # Find all input files matching the pattern (excluding already split files)
    # We look for files that do NOT end in _discovery_set or _training_set
    input_files = []
    for f in processed_dir.iterdir():
        if f.is_file() and f.suffix.lower() in ['.csv', '.parquet']:
            name = f.stem
            if not name.endswith('_discovery_set') and not name.endswith('_training_set'):
                # Extract tumor type from filename (assuming format: tumor_type_processed.csv)
                # If the file is just 'data.csv' or similar, we might need a mapping
                # For now, assume the stem is the tumor type or part of it
                input_files.append(f)
    
    if not input_files:
        logger.warning("No input files found in data/processed/. Skipping split.")
        return
    
    logger.info(f"Found {len(input_files)} input files to process.")
    
    results = []
    for input_file in input_files:
        # Infer tumor type from filename
        # Expected pattern: {tumor_type}_processed.csv or similar
        # If the file is named generically, we might need a config mapping
        # For this implementation, we strip common suffixes to get the type
        stem = input_file.stem
        if stem.endswith('_processed'):
            tumor_type = stem[:-10] # Remove '_processed'
        else:
            tumor_type = stem
            
        try:
            result = process_tumor_type_split(
                tumor_type=tumor_type,
                input_file=input_file,
                output_dir=output_dir
            )
            results.append(result)
        except Exception as e:
            logger.error(f"Failed to process {input_file}: {e}", exc_info=True)
            results.append({
                "tumor_type": tumor_type,
                "status": "failed",
                "error": str(e)
            })
    
    # Log summary
    logger.info(f"Splitting complete. Processed {len(results)} tumor types.")
    for res in results:
        if res.get("status") != "failed":
            logger.info(
                f"{res['tumor_type']}: {res['discovery_samples']} discovery, "
                f"{res['training_samples']} training"
            )
        else:
            logger.error(f"{res['tumor_type']}: FAILED - {res.get('error')}")

if __name__ == "__main__":
    main()