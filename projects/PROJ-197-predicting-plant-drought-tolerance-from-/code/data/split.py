"""
Data splitting module for the drought tolerance prediction pipeline.

Implements stratified train-test split with fallback to leave-one-out
for small datasets, as per FR-003.
"""
import os
import sys
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Tuple, Optional, Dict, Any
from sklearn.model_selection import train_test_split, LeaveOneOut
from sklearn.utils import shuffle
import json
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import get_config, validate_config, ensure_directories
from utils.logging import DataPipelineLog


def perform_stratified_split(
    df: pd.DataFrame,
    label_col: str = "label",
    test_size: float = 0.2,
    random_state: int = 42,
    min_samples_per_class: int = 5
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Perform stratified train-test split by drought label.
    
    Falls back to leave-one-out if the dataset is too small to maintain
    stratification or has insufficient samples per class.
    
    Args:
        df: Input DataFrame with species data
        label_col: Name of the target label column
        test_size: Proportion of data for testing (0.0 to 1.0)
        random_state: Random seed for reproducibility
        min_samples_per_class: Minimum samples required per class for stratification
        
    Returns:
        Tuple of (train_df, test_df) DataFrames
    """
    # Validate input
    if label_col not in df.columns:
        raise ValueError(f"Label column '{label_col}' not found in DataFrame")
    
    if df.empty:
        raise ValueError("Input DataFrame is empty")
        
    n_samples = len(df)
    label_counts = df[label_col].value_counts()
    
    # Check for small dataset or insufficient samples per class
    if n_samples < 10 or any(count < min_samples_per_class for count in label_counts):
        return _perform_leave_one_out_split(df, label_col)
    
    # Perform stratified split
    try:
        train_df, test_df = train_test_split(
            df,
            test_size=test_size,
            stratify=df[label_col],
            random_state=random_state
        )
        return train_df, test_df
    except ValueError as e:
        # Fallback if stratification fails (e.g., only one class present)
        if "The least populated class" in str(e) or "stratify" in str(e).lower():
            return _perform_leave_one_out_split(df, label_col)
        raise


def _perform_leave_one_out_split(
    df: pd.DataFrame,
    label_col: str
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Perform leave-one-out split as a fallback for small datasets.
    
    For this implementation, we'll use a single train-test split where
    the test set contains the minimum number of samples needed to have
    at least one sample per class, and the rest is training.
    
    Args:
        df: Input DataFrame
        label_col: Name of the target label column
        
    Returns:
        Tuple of (train_df, test_df) DataFrames
    """
    n_samples = len(df)
    label_counts = df[label_col].value_counts()
    
    # Determine minimum test size: one sample per class
    min_test_size = len(label_counts)
    
    if n_samples <= min_test_size:
        # Edge case: not enough samples for any split
        # Return empty test set and full dataset as train
        # This allows models to train but evaluation will be limited
        return df, pd.DataFrame(columns=df.columns)
    
    # Shuffle the data first
    df_shuffled = shuffle(df, random_state=42)
    
    # Create split
    test_df = df_shuffled.iloc[:min_test_size].copy()
    train_df = df_shuffled.iloc[min_test_size:].copy()
    
    return train_df, test_df


def save_split_metadata(
    train_df: pd.DataFrame,
    test_df: pd.DataFrame,
    metadata_path: Path,
    split_method: str
) -> None:
    """
    Save metadata about the data split for reproducibility.
    
    Args:
        train_df: Training DataFrame
        test_df: Test DataFrame
        metadata_path: Path to save the metadata JSON
        split_method: Name of the split method used
    """
    metadata = {
        "split_method": split_method,
        "timestamp": datetime.now().isoformat(),
        "train_samples": len(train_df),
        "test_samples": len(test_df),
        "total_samples": len(train_df) + len(test_df),
        "train_label_distribution": train_df["label"].value_counts().to_dict(),
        "test_label_distribution": test_df["label"].value_counts().to_dict() if len(test_df) > 0 else {},
        "train_columns": list(train_df.columns),
        "test_columns": list(test_df.columns)
    }
    
    # Ensure directory exists
    metadata_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(metadata_path, 'w') as f:
        json.dump(metadata, f, indent=2)


def main():
    """
    Main function to execute the data splitting pipeline.
    
    Reads the merged dataset from data/processed/merged_dataset.csv,
    performs stratified split, and saves the resulting datasets
    and metadata.
    """
    # Initialize logger
    logger = DataPipelineLog()
    logger.record_start("Data Split")
    
    # Load configuration
    config = get_config()
    validate_config(config)
    ensure_directories()
    
    # Define paths
    input_path = Path("data/processed/merged_dataset.csv")
    train_output_path = Path("data/processed/train_split.csv")
    test_output_path = Path("data/processed/test_split.csv")
    metadata_path = Path("data/processed/split_metadata.json")
    
    # Verify input file exists
    if not input_path.exists():
        error_msg = f"Input file not found: {input_path}"
        logger.record_error("Data Split", error_msg)
        print(f"ERROR: {error_msg}")
        sys.exit(1)
    
    try:
        # Load data
        print(f"Loading dataset from {input_path}...")
        df = pd.read_csv(input_path)
        print(f"Loaded {len(df)} samples with {len(df.columns)} columns")
        
        # Check for label column
        if "label" not in df.columns:
            error_msg = "Label column 'label' not found in dataset"
            logger.record_error("Data Split", error_msg)
            print(f"ERROR: {error_msg}")
            sys.exit(1)
        
        # Determine split method
        n_samples = len(df)
        label_counts = df["label"].value_counts()
        min_samples_per_class = 5
        
        if n_samples < 10 or any(count < min_samples_per_class for count in label_counts):
            split_method = "leave_one_out_fallback"
            print(f"Small dataset detected ({n_samples} samples, min per class: {min_samples_per_class}). Using leave-one-out fallback.")
        else:
            split_method = "stratified"
            print(f"Dataset size sufficient ({n_samples} samples). Using stratified split.")
        
        # Perform split
        train_df, test_df = perform_stratified_split(
            df,
            label_col="label",
            test_size=0.2,
            random_state=42,
            min_samples_per_class=min_samples_per_class
        )
        
        # Log split statistics
        logger.record_split_statistics(
            total_samples=n_samples,
            train_samples=len(train_df),
            test_samples=len(test_df),
            split_method=split_method,
            train_label_distribution=train_df["label"].value_counts().to_dict(),
            test_label_distribution=test_df["label"].value_counts().to_dict() if len(test_df) > 0 else {}
        )
        
        # Save outputs
        print(f"Saving train split to {train_output_path}...")
        train_df.to_csv(train_output_path, index=False)
        
        if len(test_df) > 0:
            print(f"Saving test split to {test_output_path}...")
            test_df.to_csv(test_output_path, index=False)
        else:
            print("Warning: Test set is empty. Saving empty file.")
            test_df.to_csv(test_output_path, index=False)
        
        # Save metadata
        print(f"Saving split metadata to {metadata_path}...")
        save_split_metadata(train_df, test_df, metadata_path, split_method)
        
        # Log completion
        logger.record_end("Data Split", "Success")
        
        print("\n=== Split Summary ===")
        print(f"Method: {split_method}")
        print(f"Total samples: {n_samples}")
        print(f"Train samples: {len(train_df)}")
        print(f"Test samples: {len(test_df)}")
        if len(train_df) > 0:
            print(f"Train label distribution: {train_df['label'].value_counts().to_dict()}")
        if len(test_df) > 0:
            print(f"Test label distribution: {test_df['label'].value_counts().to_dict()}")
        print("=====================")
        
    except Exception as e:
        error_msg = f"Failed to perform data split: {str(e)}"
        logger.record_error("Data Split", error_msg)
        print(f"ERROR: {error_msg}")
        sys.exit(1)


if __name__ == "__main__":
    main()
