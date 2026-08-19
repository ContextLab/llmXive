import os
import sys
import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Tuple

import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split

from src.config import get_project_root
from src.utils import setup_logging, ensure_path_exists

# Configure logging
logger = setup_logging("preprocessing")

def load_batch_corrected_data(tumor_type: str, project_root: Path) -> pd.DataFrame:
    """
    Load the batch-corrected data for a specific tumor type.
    Expects the file to be named {tumor_type}_batch_corrected.csv in data/processed/
    
    Args:
        tumor_type: The tumor type identifier (e.g., 'BRCA', 'LUAD')
        project_root: The root path of the project
        
    Returns:
        DataFrame with batch-corrected expression data and metadata
        
    Raises:
        FileNotFoundError: If the input file does not exist
    """
    input_path = project_root / "data" / "processed" / f"{tumor_type}_batch_corrected.csv"
    
    if not input_path.exists():
        raise FileNotFoundError(
            f"Batch-corrected data file not found: {input_path}. "
            "Ensure T016 (Batch Correction) has completed successfully."
        )
    
    logger.info(f"Loading batch-corrected data for {tumor_type} from {input_path}")
    df = pd.read_csv(input_path)
    
    # Validate required columns
    required_cols = ['sample_id', 'response_label']
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        raise ValueError(
            f"Missing required columns in {input_path}: {missing_cols}. "
            "Expected 'sample_id' and 'response_label'."
        )
    
    return df

def split_data_stratified(
    df: pd.DataFrame, 
    test_size: float = 0.3, 
    random_state: int = 42
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Split data into discovery and training sets with stratification.
    
    The discovery set is used for gene selection (DE analysis).
    The training set is used for model fitting.
    
    Stratification ensures the response_label distribution is maintained
    in both splits.
    
    Args:
        df: Input DataFrame with 'response_label' column
        test_size: Proportion of samples to include in the discovery set (default 0.3)
        random_state: Random seed for reproducibility
        
    Returns:
        Tuple of (discovery_set, training_set) DataFrames
    """
    if 'response_label' not in df.columns:
        raise ValueError("Input DataFrame must contain 'response_label' column for stratification.")
    
    # Check for class imbalance that might cause split issues
    value_counts = df['response_label'].value_counts()
    logger.info(f"Class distribution before split: {value_counts.to_dict()}")
    
    # Ensure minimum samples per class for stratification
    min_samples_per_class = value_counts.min()
    if min_samples_per_class < 2:
        logger.warning(
            f"Class with fewer than 2 samples found. "
            "Stratified split may fail. Falling back to random split if needed."
        )
    
    try:
        discovery_set, training_set = train_test_split(
            df,
            test_size=test_size,
            stratify=df['response_label'],
            random_state=random_state
        )
        logger.info("Stratified split successful.")
    except ValueError as e:
        if "The least populated class in y has only 1 member" in str(e):
            logger.warning(
                f"Stratified split failed due to single-member class: {e}. "
                "Attempting non-stratified split as fallback."
            )
            discovery_set, training_set = train_test_split(
                df,
                test_size=test_size,
                random_state=random_state
            )
        else:
            raise
    
    return discovery_set, training_set

def save_split_data(
    discovery_set: pd.DataFrame,
    training_set: pd.DataFrame,
    tumor_type: str,
    project_root: Path
) -> Tuple[Path, Path]:
    """
    Save the split datasets to CSV files.
    
    Args:
        discovery_set: DataFrame for the discovery set
        training_set: DataFrame for the training set
        tumor_type: The tumor type identifier
        project_root: The root path of the project
        
    Returns:
        Tuple of (discovery_path, training_path)
    """
    processed_dir = project_root / "data" / "processed"
    ensure_path_exists(processed_dir)
    
    discovery_path = processed_dir / f"{tumor_type}_discovery_set.csv"
    training_path = processed_dir / f"{tumor_type}_training_set.csv"
    
    discovery_set.to_csv(discovery_path, index=False)
    training_set.to_csv(training_path, index=False)
    
    logger.info(f"Saved discovery set ({len(discovery_set)} samples) to {discovery_path}")
    logger.info(f"Saved training set ({len(training_set)} samples) to {training_path}")
    
    return discovery_path, training_path

def process_tumor_type_split(
    tumor_type: str,
    project_root: Path,
    test_size: float = 0.3,
    random_state: int = 42
) -> Dict[str, Any]:
    """
    Process a single tumor type: load batch-corrected data, split, and save.
    
    Args:
        tumor_type: The tumor type identifier
        project_root: The root path of the project
        test_size: Proportion for discovery set
        random_state: Random seed
        
    Returns:
        Dictionary with split statistics
    """
    try:
        df = load_batch_corrected_data(tumor_type, project_root)
        discovery_set, training_set = split_data_stratified(
            df, test_size=test_size, random_state=random_state
        )
        discovery_path, training_path = save_split_data(
            discovery_set, training_set, tumor_type, project_root
        )
        
        return {
            "tumor_type": tumor_type,
            "status": "success",
            "total_samples": len(df),
            "discovery_samples": len(discovery_set),
            "training_samples": len(training_set),
            "discovery_path": str(discovery_path),
            "training_path": str(training_path),
            "discovery_class_dist": discovery_set['response_label'].value_counts().to_dict(),
            "training_class_dist": training_set['response_label'].value_counts().to_dict()
        }
    except FileNotFoundError as e:
        logger.error(f"Skipping {tumor_type}: {e}")
        return {
            "tumor_type": tumor_type,
            "status": "skipped",
            "reason": "input_file_not_found"
        }
    except Exception as e:
        logger.error(f"Error processing {tumor_type}: {e}")
        return {
            "tumor_type": tumor_type,
            "status": "failed",
            "reason": str(e)
        }

def get_tumor_types_from_batch_corrected(project_root: Path) -> List[str]:
    """
    Scan data/processed/ for batch-corrected files and extract tumor types.
    
    Returns:
        List of tumor type identifiers found
    """
    processed_dir = project_root / "data" / "processed"
    if not processed_dir.exists():
        logger.warning(f"Processed directory not found: {processed_dir}")
        return []
    
    tumor_types = []
    for f in processed_dir.glob("*_batch_corrected.csv"):
        # Extract tumor type from filename (e.g., "BRCA_batch_corrected.csv" -> "BRCA")
        tumor_type = f.stem.replace("_batch_corrected", "")
        tumor_types.append(tumor_type)
    
    logger.info(f"Found {len(tumor_types)} tumor types with batch-corrected data: {tumor_types}")
    return tumor_types

def main():
    """
    Main entry point for T020: Split data for each tumor type.
    
    This script:
    1. Scans for batch-corrected data files (output of T016)
    2. For each tumor type, splits data into discovery and training sets
    3. Saves distinct CSV files for each split
    4. Logs statistics about the splits
    """
    project_root = get_project_root()
    logger.info(f"Project root: {project_root}")
    
    # Get list of tumor types with batch-corrected data
    tumor_types = get_tumor_types_from_batch_corrected(project_root)
    
    if not tumor_types:
        logger.error(
            "No batch-corrected data files found. "
            "Ensure T016 (Batch Correction) has completed successfully."
        )
        sys.exit(1)
    
    results = []
    for tumor_type in tumor_types:
        result = process_tumor_type_split(
            tumor_type,
            project_root,
            test_size=0.3,
            random_state=42
        )
        results.append(result)
        logger.info(f"Result for {tumor_type}: {result['status']}")
    
    # Save overall split summary
    summary_path = project_root / "data" / "processed" / "split_summary.json"
    with open(summary_path, 'w') as f:
        json.dump(results, f, indent=2)
    logger.info(f"Saved split summary to {summary_path}")
    
    # Check for any failures
    failures = [r for r in results if r['status'] != 'success']
    if failures:
        logger.warning(f"Split completed with {len(failures)} failures/skips.")
        for f in failures:
            logger.warning(f"  - {f['tumor_type']}: {f.get('reason', 'unknown')}")
    else:
        logger.info("All tumor types split successfully.")

if __name__ == "__main__":
    main()
