"""
Preprocessing module for chemotherapeutic biomarker discovery.
Handles harmonization, normalization, batch correction, and data splitting.
"""
import os
import sys
import json
import logging
import tempfile
import time
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any

import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split

from src.config import get_project_root, ensure_directories
from src.utils import setup_logging, ensure_path_exists, update_state_artifact_hashes

# Configure logging
logger = logging.getLogger(__name__)

def load_processed_data(file_path: str) -> pd.DataFrame:
    """
    Load a processed data file (CSV/Parquet) into a DataFrame.
    
    Args:
        file_path: Path to the data file.
        
    Returns:
        DataFrame with expression data.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Input file not found: {file_path}")
    
    if file_path.endswith('.parquet'):
        return pd.read_parquet(file_path)
    else:
        return pd.read_csv(file_path, index_col=0)

def save_processed_data(df: pd.DataFrame, file_path: str) -> None:
    """
    Save a DataFrame to a CSV or Parquet file.
    
    Args:
        df: DataFrame to save.
        file_path: Output path.
    """
    ensure_path_exists(file_path)
    if file_path.endswith('.parquet'):
        df.to_parquet(file_path)
    else:
        df.to_csv(file_path)
    logger.info(f"Saved processed data to {file_path}")

def split_data_stratified(
    df: pd.DataFrame, 
    strata_column: str = 'response_label', 
    test_size: float = 0.3, 
    random_state: int = 42
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Split a DataFrame into discovery and training sets with stratification.
    
    This ensures the class distribution (response_label) is maintained in both sets.
    FR-013 Compliance: Strict separation of discovery (gene selection) and 
    training (model fitting) sets.
    
    Args:
        df: Input DataFrame containing expression data and metadata.
        strata_column: Name of the column to use for stratification (default: 'response_label').
        test_size: Proportion of data to include in the discovery set (default: 0.3).
        random_state: Random seed for reproducibility.
        
    Returns:
        Tuple of (discovery_set, training_set) DataFrames.
        
    Raises:
        ValueError: If stratification column is missing or has insufficient samples.
        RuntimeError: If stratification fails due to small class sizes.
    """
    if strata_column not in df.columns:
        raise ValueError(f"Stratification column '{strata_column}' not found in data.")
    
    # Check for minimum samples per class to allow stratified split
    class_counts = df[strata_column].value_counts()
    if (class_counts < 2).any():
        # If a class has only 1 sample, stratified split is impossible
        logger.warning("Insufficient samples in some classes for stratified split. "
                     "Attempting non-stratified split with warning.")
        # Fallback: if strict stratification fails, we must halt per FR-013 safety
        raise RuntimeError(
            f"Stratified split failed: one or more classes have < 2 samples. "
            f"Class counts: {class_counts.to_dict()}. "
            f"Cannot proceed without valid stratification to prevent bias."
        )

    try:
        discovery, training = train_test_split(
            df, 
            test_size=test_size, 
            stratify=df[strata_column], 
            random_state=random_state
        )
        logger.info(f"Stratified split successful. Discovery: {len(discovery)}, Training: {len(training)}")
        return discovery, training
    except ValueError as e:
        # This can happen if a class has only 1 sample despite the check above
        # (e.g., due to edge cases in split logic)
        raise RuntimeError(f"Stratified split failed: {str(e)}. "
                         f"Data may be too imbalanced or sparse for splitting.")

def process_tumor_type_split(
    tumor_type: str, 
    input_path: str, 
    output_dir: str,
    strata_column: str = 'response_label',
    test_size: float = 0.3,
    random_state: int = 42
) -> Dict[str, Any]:
    """
    Process a single tumor type: load data, split it, and save outputs.
    
    Args:
        tumor_type: The tumor type identifier (e.g., 'BRCA', 'LUAD').
        input_path: Path to the batch-corrected data file for this tumor type.
        output_dir: Directory to save the split datasets.
        strata_column: Column name for stratification.
        test_size: Proportion for discovery set.
        random_state: Random seed.
        
    Returns:
        Dictionary with paths to the saved files and split statistics.
    """
    logger.info(f"Processing split for tumor type: {tumor_type}")
    
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Input file for {tumor_type} not found: {input_path}")
    
    # Load data
    df = load_processed_data(input_path)
    logger.info(f"Loaded {len(df)} samples for {tumor_type}")
    
    # Perform stratified split
    discovery_df, training_df = split_data_stratified(
        df, 
        strata_column=strata_column, 
        test_size=test_size, 
        random_state=random_state
    )
    
    # Ensure output directory exists
    ensure_path_exists(output_dir)
    
    # Define output paths
    discovery_path = os.path.join(output_dir, f"{tumor_type}_discovery_set.csv")
    training_path = os.path.join(output_dir, f"{tumor_type}_training_set.csv")
    
    # Save datasets
    save_processed_data(discovery_df, discovery_path)
    save_processed_data(training_df, training_path)
    
    # Calculate stats
    stats = {
        "tumor_type": tumor_type,
        "total_samples": len(df),
        "discovery_samples": len(discovery_df),
        "training_samples": len(training_df),
        "discovery_path": discovery_path,
        "training_path": training_path,
        "class_distribution_discovery": discovery_df[strata_column].value_counts().to_dict(),
        "class_distribution_training": training_df[strata_column].value_counts().to_dict()
    }
    
    logger.info(f"Split complete for {tumor_type}. Discovery: {len(discovery_df)}, Training: {len(training_df)}")
    return stats

def main():
    """
    Main entry point for the data splitting stage (T020).
    Reads batch-corrected data from data/processed/, splits by tumor type,
    and saves discovery/training sets.
    """
    setup_logging()
    project_root = get_project_root()
    input_dir = os.path.join(project_root, "data", "processed")
    output_dir = input_dir  # Save back to processed or a subfolder if preferred
    
    # Identify input files matching pattern: {tumor_type}_batch_corrected.csv
    # Assuming T016 produced files named like this or similar.
    # We need to find the batch-corrected files. 
    # Based on T016, the output is likely in data/processed/.
    # We will look for files that contain 'batch_corrected' or similar.
    # For robustness, we assume the input to this step is the output of T016.
    # Let's assume the files are named {tumor_type}_batch_corrected.csv
    
    input_files = [f for f in os.listdir(input_dir) if 'batch_corrected' in f and f.endswith('.csv')]
    
    if not input_files:
        # Fallback: if no explicit 'batch_corrected' files, try to find the most recent processed files
        # or all CSVs that look like tumor data (excluding 'discovery', 'training', 'de_results')
        all_csvs = [f for f in os.listdir(input_dir) if f.endswith('.csv')]
        input_files = [f for f in all_csvs if not any(kw in f for kw in ['discovery', 'training', 'de_results', 'meta'])]
        
        if not input_files:
            logger.error("No input files found for splitting. Expected files like {tumor_type}_batch_corrected.csv")
            sys.exit(1)
    
    logger.info(f"Found {len(input_files)} input files for splitting: {input_files}")
    
    results = []
    failed_types = []
    
    for filename in input_files:
        # Extract tumor type from filename
        # Expected format: {tumor_type}_batch_corrected.csv
        base_name = filename.replace('_batch_corrected.csv', '').replace('.csv', '')
        tumor_type = base_name
        
        input_path = os.path.join(input_dir, filename)
        
        try:
            stats = process_tumor_type_split(
                tumor_type=tumor_type,
                input_path=input_path,
                output_dir=output_dir,
                strata_column='response_label',
                test_size=0.3,
                random_state=42
            )
            results.append(stats)
        except Exception as e:
            logger.error(f"Failed to split data for {tumor_type}: {str(e)}")
            failed_types.append(tumor_type)
    
    if failed_types:
        logger.error(f"Splitting failed for tumor types: {failed_types}")
        sys.exit(1)
    
    # Save summary of splitting operation
    summary_path = os.path.join(project_root, "results", "split_summary.json")
    ensure_path_exists(summary_path)
    
    summary = {
        "stage": "T020_Data_Splitting",
        "total_tumor_types_processed": len(results),
        "successful_splits": len(results),
        "failed_splits": len(failed_types),
        "details": results
    }
    
    with open(summary_path, 'w') as f:
        json.dump(summary, f, indent=2)
    
    logger.info(f"Data splitting complete. Summary saved to {summary_path}")
    return 0

if __name__ == "__main__":
    sys.exit(main())
