import os
import sys
import json
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple

import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split

# Import existing project utilities and config
from src.config import get_project_root, ensure_directories
from src.utils import setup_logging, calculate_checksum

# Configure logger for this module
logger = logging.getLogger(__name__)

def load_processed_data(tumor_type: str, data_dir: Path) -> pd.DataFrame:
    """
    Load the preprocessed data for a specific tumor type.
    Expects a file named '{tumor_type}_processed.csv' in the data_dir.
    """
    file_path = data_dir / f"{tumor_type}_processed.csv"
    if not file_path.exists():
        raise FileNotFoundError(f"Processed data file not found for {tumor_type}: {file_path}")
    
    logger.info(f"Loading processed data for {tumor_type} from {file_path}")
    df = pd.read_csv(file_path)
    
    # Validate required columns exist
    required_cols = ['response']
    # Gene columns are assumed to be all columns except metadata/response
    if not all(col in df.columns for col in required_cols):
        raise ValueError(f"Missing required columns in {file_path}. Found: {df.columns.tolist()}")
    
    return df

def save_processed_data(df: pd.DataFrame, output_path: Path) -> None:
    """
    Save the dataframe to a CSV file.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False)
    logger.info(f"Saved data to {output_path}")

def split_data_stratified(
    df: pd.DataFrame, 
    response_col: str = 'response', 
    test_size: float = 0.3, 
    random_state: int = 42
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Split the dataframe into discovery and training sets using stratified sampling.
    
    Args:
        df: Input dataframe containing gene expression and response labels.
        response_col: Name of the column containing the response labels.
        test_size: Proportion of the dataset to include in the training set (since we need a discovery set for feature selection first).
                   Here, we treat 'test' as the 'training_set' for the model, and 'train' as the 'discovery_set'.
                   Wait, standard split: train (discovery) / test (training for model).
                   Let's map: discovery_set = train_split, training_set = test_split.
                   We need a specific split ratio. Usually 70/30 or 80/20.
                   Task says: discovery_set (for gene selection), training_set (for model fitting).
                   We will use 70% for discovery, 30% for training to ensure sufficient data for model fitting.
        random_state: Random seed for reproducibility.
    
    Returns:
        Tuple of (discovery_set, training_set) DataFrames.
    """
    # Ensure response column is not a string object if it has numeric labels, but stratify works on categories
    # Check class balance
    class_counts = df[response_col].value_counts()
    logger.info(f"Class distribution in {df.shape[0]} samples: {class_counts.to_dict()}")
    
    # Check for minimum class size to allow stratification
    min_class_count = class_counts.min()
    if min_class_count < 2:
        logger.warning(f"Class imbalance detected (min count {min_class_count}). Stratification might fail. Attempting split.")
    
    try:
        # We want discovery_set (larger) and training_set (smaller)
        # Let's do 70% discovery, 30% training
        # sklearn train_test_split: train is first arg, test is second
        # We want discovery = train, training = test
        discovery_set, training_set = train_test_split(
            df, 
            test_size=test_size, 
            stratify=df[response_col], 
            random_state=random_state
        )
    except ValueError as e:
        # Fallback if stratification fails due to small sample size
        if "The least populated class in y has only 1 member" in str(e):
            logger.warning(f"Stratification failed due to small class size. Falling back to non-stratified split.")
            discovery_set, training_set = train_test_split(
                df, 
                test_size=test_size, 
                random_state=random_state
            )
        else:
            raise e

    logger.info(f"Split complete. Discovery set: {discovery_set.shape[0]} samples, Training set: {training_set.shape[0]} samples.")
    
    # Verify class distribution in splits
    logger.info(f"Discovery set distribution: {discovery_set[response_col].value_counts().to_dict()}")
    logger.info(f"Training set distribution: {training_set[response_col].value_counts().to_dict()}")
    
    return discovery_set, training_set

def process_tumor_type(tumor_type: str, data_dir: Path, output_dir: Path) -> Dict[str, Any]:
    """
    Process a single tumor type: load, split, and save discovery/training sets.
    
    Args:
        tumor_type: The identifier for the tumor type (e.g., 'BRCA').
        data_dir: Directory containing the preprocessed input files.
        output_dir: Directory to save the split files.
    
    Returns:
        Dictionary with split statistics and output paths.
    """
    logger.info(f"Processing tumor type: {tumor_type}")
    
    # Load data
    df = load_processed_data(tumor_type, data_dir)
    
    # Split data
    discovery_set, training_set = split_data_stratified(df)
    
    # Define output paths
    discovery_path = output_dir / f"{tumor_type}_discovery_set.csv"
    training_path = output_dir / f"{tumor_type}_training_set.csv"
    
    # Save data
    save_processed_data(discovery_set, discovery_path)
    save_processed_data(training_set, training_path)
    
    # Calculate checksums
    discovery_checksum = calculate_checksum(discovery_path)
    training_checksum = calculate_checksum(training_path)
    
    result = {
        "tumor_type": tumor_type,
        "total_samples": len(df),
        "discovery_samples": len(discovery_set),
        "training_samples": len(training_set),
        "discovery_path": str(discovery_path),
        "training_path": str(training_path),
        "discovery_checksum": discovery_checksum,
        "training_checksum": training_checksum
    }
    
    logger.info(f"Finished processing {tumor_type}. Discovery: {result['discovery_samples']}, Training: {result['training_samples']}")
    return result

def main():
    """
    Main entry point for the preprocessing splitting stage.
    Iterates over available tumor types and splits their data.
    """
    setup_logging()
    project_root = get_project_root()
    data_dir = project_root / "data" / "processed"
    output_dir = project_root / "data" / "processed"
    
    ensure_directories([output_dir])
    
    # Determine which tumor types to process
    # We look for files matching '*_processed.csv' in the data_dir
    if not data_dir.exists():
        logger.error(f"Data directory {data_dir} does not exist. Run data acquisition first.")
        sys.exit(1)
    
    processed_files = list(data_dir.glob("*_processed.csv"))
    if not processed_files:
        logger.warning(f"No processed data files found in {data_dir}.")
        sys.exit(0)
    
    tumor_types = [f.stem.replace("_processed", "") for f in processed_files]
    logger.info(f"Found {len(tumor_types)} tumor types to process: {tumor_types}")
    
    results = []
    for tumor_type in tumor_types:
        try:
            result = process_tumor_type(tumor_type, data_dir, output_dir)
            results.append(result)
        except Exception as e:
            logger.error(f"Failed to process tumor type {tumor_type}: {e}", exc_info=True)
            # Continue processing other types, but mark failure
            results.append({
                "tumor_type": tumor_type,
                "status": "failed",
                "error": str(e)
            })
    
    # Save summary of splitting operations
    summary_path = output_dir / "split_summary.json"
    with open(summary_path, 'w') as f:
        json.dump(results, f, indent=2)
    logger.info(f"Split summary saved to {summary_path}")
    
    # Check if any critical failures occurred
    failed_types = [r["tumor_type"] for r in results if r.get("status") == "failed"]
    if failed_types:
        logger.warning(f"Failed to process tumor types: {failed_types}")
        # Depending on strictness, we might exit here. For now, we log and continue.

if __name__ == "__main__":
    main()