"""
Data Splitting Module for Battery Electrolyte Decomposition Project.

This module implements the splitting logic for the processed feature matrix
into Train, Validation, and Held-Out sets as required by Task T018.

It reads the validated feature matrix from the previous pipeline steps,
performs a stratified split (if possible, otherwise random), and saves
the resulting datasets to the `data/processed/` directory.
"""
import os
import sys
import logging
from pathlib import Path
from typing import Tuple, Optional

import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split

# Add project root to path to allow imports from sibling modules
# This assumes the script is run as `python code/data/split_data.py`
# or the CWD is the project root.
PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

from data.ingestion import run_ingestion_pipeline
from data.descriptors import run_descriptor_pipeline
from data.target_calc import calculate_decomposition_energy_from_yaml
from data.validation import run_validation_pipeline
from utils.logging_config import get_logger
from config import get_data_dir, get_output_dir

# Configure logging
logger = get_logger("split_data")

def load_processed_features(filepath: Path) -> pd.DataFrame:
    """
    Loads the processed feature matrix from disk.
    
    Args:
        filepath: Path to the CSV file containing features.
        
    Returns:
        DataFrame with features and targets.
        
    Raises:
        FileNotFoundError: If the file does not exist.
    """
    if not filepath.exists():
        raise FileNotFoundError(f"Processed features file not found at {filepath}. "
                                "Please ensure T017 (validation) has run and produced this file.")
    
    df = pd.read_csv(filepath)
    logger.info(f"Loaded {len(df)} rows from {filepath}")
    return df

def split_data(
    df: pd.DataFrame,
    target_col: str = "decomp_energy",
    stratify_col: Optional[str] = "potential_v",
    train_size: float = 0.7,
    val_size: float = 0.15,
    test_size: float = 0.15,
    random_state: int = 42
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Splits the dataframe into Train, Validation, and Held-Out (Test) sets.
    
    The split respects the `stratify_col` (potential) if provided to ensure
    distribution consistency across splits.
    
    Args:
        df: The full processed dataframe.
        target_col: Name of the target column.
        stratify_col: Column to use for stratification (e.g., potential_v).
        train_size: Fraction of data for training.
        val_size: Fraction of data for validation.
        test_size: Fraction of data for held-out set.
        random_state: Random seed for reproducibility.
        
    Returns:
        Tuple of (train_df, val_df, test_df).
    """
    # Validate sizes
    total = train_size + val_size + test_size
    if not np.isclose(total, 1.0):
        logger.warning(f"Split sizes sum to {total}, not 1.0. Adjusting test_size.")
        test_size = 1.0 - train_size - val_size

    # Separate features and target for splitting logic if needed,
    # but we will split the whole DF to keep metadata (molecule_id, etc.) together.
    
    # Determine stratification
    stratify = None
    if stratify_col and stratify_col in df.columns:
        stratify = df[stratify_col]
        logger.info(f"Stratifying split by '{stratify_col}'")
    else:
        logger.warning(f"Stratification column '{stratify_col}' not found. Performing random split.")

    # First split: Train vs (Val + Test)
    # We keep the target column in the DF for now, splitting the whole DF.
    train_df, temp_df = train_test_split(
        df,
        train_size=train_size,
        random_state=random_state,
        stratify=stratify if stratify is not None else None
    )
    
    # Adjust stratify for the second split
    if stratify is not None:
        # Recalculate stratify for the remaining data based on the original column
        stratify_temp = temp_df[stratify_col]
    else:
        stratify_temp = None

    # Second split: Val vs Test from the remaining data
    # val_size needs to be relative to the remaining data (1 - train_size)
    val_ratio = val_size / (1 - train_size)
    
    val_df, test_df = train_test_split(
        temp_df,
        train_size=val_ratio,
        random_state=random_state,
        stratify=stratify_temp
    )
    
    logger.info(f"Split complete: Train={len(train_df)}, Val={len(val_df)}, Test={len(test_df)}")
    return train_df, val_df, test_df

def save_splits(
    train_df: pd.DataFrame,
    val_df: pd.DataFrame,
    test_df: pd.DataFrame,
    output_dir: Path
) -> None:
    """
    Saves the split dataframes to CSV files.
    
    Per T018 requirements:
    - `data/processed/electrolyte_features.csv`: Contains Train + Validation (processed feature matrix)
    - `data/processed/electrolyte_heldout.csv`: Contains the Held-Out set (Test)
    
    Args:
        train_df: Training set.
        val_df: Validation set.
        test_df: Held-out set.
        output_dir: Directory to save the files.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Combine Train and Validation for the "processed feature matrix" file
    # as per standard ML pipeline where validation is used during training/tuning.
    # The task specifically asks to save "processed feature matrix" and "held-out set".
    combined_train_val = pd.concat([train_df, val_df], ignore_index=True)
    
    features_path = output_dir / "electrolyte_features.csv"
    heldout_path = output_dir / "electrolyte_heldout.csv"
    
    combined_train_val.to_csv(features_path, index=False)
    test_df.to_csv(heldout_path, index=False)
    
    logger.info(f"Saved combined Train/Val to {features_path}")
    logger.info(f"Saved Held-Out set to {heldout_path}")

def run_split_pipeline(input_path: Optional[Path] = None) -> None:
    """
    Orchestrates the data splitting pipeline.
    
    1. Loads the validated feature matrix (from T017).
    2. Performs the split.
    3. Saves the outputs.
    
    Args:
        input_path: Optional path to the input CSV. Defaults to the expected location
                    after T017 runs.
    """
    # Default paths
    data_dir = get_data_dir()
    processed_dir = data_dir / "processed"
    
    if input_path is None:
        # T017 typically outputs to a standard location or we assume the user
        # has run the previous steps. We look for the most likely output.
        # However, T017 in the spec says "Add validation logic...". 
        # We assume the output of the validation pipeline is the input here.
        # If T017 doesn't explicitly write a file, we might need to run the 
        # upstream pipeline to generate the features.
        # Given the task description: "Split data... and save ... to data/processed/electrolyte_features.csv"
        # We assume the input is the result of the ingestion+descriptors+target+validation flow.
        # For this script to be runnable standalone, we assume the input file 
        # 'electrolyte_features_raw.csv' or similar exists, OR we run the pipeline up to validation.
        # To be safe and robust, we check for a standard input.
        # If the previous task (T017) didn't write a specific file, we might need to 
        # re-run the descriptor/target calculation.
        # Let's assume the input is 'data/processed/electrolyte_features_validated.csv' if T017 wrote it,
        # or we run the pipeline.
        # Since T017 description is "Add validation logic to ensure feature matrix has no missing values",
        # it likely modifies the dataframe in place or writes a cleaned version.
        # We will assume the input is the output of the descriptor/target pipeline.
        
        # Let's try to find the most recent processed file or run the pipeline if missing.
        # For simplicity in this task, we expect the input to be the result of T016/T017.
        # If that file doesn't exist, we attempt to run the upstream pipeline.
        input_path = processed_dir / "electrolyte_features.csv"
        
        if not input_path.exists():
            logger.warning(f"Input file {input_path} not found. Attempting to run upstream pipeline...")
            # Run upstream pipeline to generate features if missing
            # This is a fallback to ensure the script is runnable
            try:
                logger.info("Running ingestion pipeline...")
                raw_df = run_ingestion_pipeline()
                logger.info("Running descriptor pipeline...")
                desc_df = run_descriptor_pipeline(raw_df)
                logger.info("Calculating targets...")
                # This step depends on T016 logic
                # We assume T016 logic is encapsulated or we replicate the call
                # Since T016 is 'completed', we assume the function exists in target_calc
                # We need to pass the dataframe to the target calculation
                # Assuming T016 produced a file or function. 
                # If T016 produced a file, we load it. If not, we call the function.
                # The task T016 says "Implement logic... to calculate E_decomp".
                # Let's assume it writes to 'data/processed/electrolyte_with_targets.csv'
                # or we just call the function here.
                
                # To be safe, we check if T016 output exists
                target_input = processed_dir / "electrolyte_with_targets.csv"
                if target_input.exists():
                    df_with_targets = pd.read_csv(target_input)
                else:
                    # Fallback: run the calculation if the file doesn't exist
                    # This implies we need to know the exact function signature of T016
                    # Since we can't see T016's exact output file name, we assume 
                    # the pipeline flow generates the features.
                    # We will assume the input to T018 is the result of T017.
                    # If T017 didn't write a file, we are stuck.
                    # Let's assume T017 writes 'electrolyte_features.csv' to processed.
                    # If it doesn't exist, we raise an error.
                    raise FileNotFoundError("Upstream pipeline output not found. Please run T016 and T017 first.")
                
                input_path = target_input
            except Exception as e:
                logger.error(f"Failed to run upstream pipeline: {e}")
                raise

    # Load data
    df = load_processed_features(input_path)
    
    # Perform split
    train_df, val_df, test_df = split_data(df)
    
    # Save splits
    save_splits(train_df, val_df, test_df, processed_dir)
    
    logger.info("Data splitting pipeline completed successfully.")

if __name__ == "__main__":
    # Entry point for execution
    run_split_pipeline()
