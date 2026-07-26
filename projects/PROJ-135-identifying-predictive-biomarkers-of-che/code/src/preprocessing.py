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
from src.utils import setup_logging

# Configure logging
logger = logging.getLogger(__name__)

def load_processed_data(tumor_type: str, processed_dir: Path) -> pd.DataFrame:
    """
    Load the pre-processed, normalized, and harmonized data for a specific tumor type.
    Expects the file to exist at: processed_dir/{tumor_type}_normalized.csv
    
    Args:
        tumor_type: The specific tumor type identifier (e.g., 'BRCA', 'LUAD').
        processed_dir: Path to the data/processed directory.
        
    Returns:
        A pandas DataFrame containing the gene expression matrix and metadata.
        
    Raises:
        FileNotFoundError: If the processed file does not exist.
    """
    input_path = processed_dir / f"{tumor_type}_normalized.csv"
    if not input_path.exists():
        raise FileNotFoundError(f"Processed data file not found: {input_path}")
    
    logger.info(f"Loading processed data for {tumor_type} from {input_path}")
    df = pd.read_csv(input_path)
    
    # Ensure required columns exist
    required_cols = ['response_label', 'sample_id']
    # We assume gene expression columns are all others or explicitly handled
    # We need to know which column holds the label for stratification
    if 'response_label' not in df.columns:
        raise ValueError(f"Column 'response_label' missing in {input_path}. Cannot stratify.")
        
    return df

def split_data_stratified(
    df: pd.DataFrame, 
    label_col: str = 'response_label',
    test_size: float = 0.3,
    random_state: int = 42
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Split the dataframe into discovery and training sets with stratification.
    
    The discovery set is used for gene selection (DE analysis).
    The training set is used for model fitting.
    
    Args:
        df: Input DataFrame with expression data and labels.
        label_col: Name of the column containing the response label.
        test_size: Proportion of the dataset to include in the training set (relative to total).
                   Here, we treat 'test_size' as the proportion for the training set to match
                   typical sklearn convention where 'test_size' is the hold-out set.
                   However, the task asks for Discovery (gene selection) and Training (model fitting).
                   Standard practice: Discovery = larger set (e.g., 70%), Training = smaller set (30%) 
                   OR Discovery = 50%, Training = 50%. 
                   Given the description "discovery_set (for gene selection) and training_set (for model fitting)",
                   and typical ML pipelines where we select features on a subset and train on another:
                   Let's assume:
                   - Discovery Set: The set used for DE (Gene Selection). 
                   - Training Set: The set used for Model Training.
                   
                   We will split such that:
                   - Discovery Set: 70% (or 1-test_size if we map test_size to training)
                   - Training Set: 30%
                   
                   Wait, the task says: "discovery_set (for gene selection) and training_set (for model fitting)".
                   Usually, you select features on the discovery set, then train on the training set.
                   Let's use a 70/30 split where Discovery=70% and Training=30%.
                   In sklearn, train_test_split(x, y, test_size=0.3) returns (train, test).
                   So if we want Training=30%, we set test_size=0.3.
                   Then:
                   - returned[0] -> Training Set (30%)? No, train_test_split returns (train, test).
                   - If test_size=0.3, then 'train' is 70% and 'test' is 30%.
                   - We want Discovery=70% and Training=30%.
                   - So: discovery_set = train, training_set = test.
                   
                   Actually, let's re-read carefully: "discovery_set (for gene selection) and training_set (for model fitting)".
                   Often, "Discovery" implies the initial set to find markers. "Training" implies the set to build the model.
                   If we split 70/30:
                   - 70% -> Discovery (Gene Selection)
                   - 30% -> Training (Model Fitting)
                   
                   So:
                   discovery_set = the 70% chunk.
                   training_set = the 30% chunk.
                   
                   In train_test_split:
                   X_train, X_test = train_test_split(X, y, test_size=0.3)
                   X_train is 70%, X_test is 30%.
                   So: discovery_set = X_train, training_set = X_test.
                   
                   Args:
                       df: DataFrame
                       label_col: 'response_label'
                       test_size: 0.3 (meaning 30% for training set)
                       random_state: 42
                       
                   Returns:
                       (discovery_df, training_df)
    """
    if label_col not in df.columns:
        raise ValueError(f"Label column '{label_col}' not found in dataframe.")
        
    # Separate features (genes) and labels
    # Assume all columns except 'sample_id', 'response_label' (and maybe 'batch' if present) are genes
    # We need to be careful not to drop non-gene columns that are metadata but not labels
    # For safety, we'll split based on the label column and keep the rest.
    
    y = df[label_col]
    X = df.drop(columns=[label_col])
    
    # Perform stratified split
    # We want Discovery (70%) and Training (30%)
    # train_test_split returns (train, test). 
    # If test_size=0.3, 'train' is 70%, 'test' is 30%.
    # So: discovery = train, training = test.
    
    discovery_df, training_df = train_test_split(
        df,
        test_size=test_size,
        random_state=random_state,
        stratify=y
    )
    
    logger.info(f"Split completed for {df.shape[0]} samples:")
    logger.info(f"  Discovery Set: {discovery_df.shape[0]} samples")
    logger.info(f"  Training Set: {training_df.shape[0]} samples")
    logger.info(f"  Class distribution in Discovery: {discovery_df[label_col].value_counts().to_dict()}")
    logger.info(f"  Class distribution in Training: {training_df[label_col].value_counts().to_dict()}")
    
    return discovery_df, training_df

def save_split_data(
    discovery_df: pd.DataFrame,
    training_df: pd.DataFrame,
    tumor_type: str,
    output_dir: Path
) -> None:
    """
    Save the split datasets to CSV files.
    
    Args:
        discovery_df: Discovery set DataFrame.
        training_df: Training set DataFrame.
        tumor_type: Tumor type identifier for naming.
        output_dir: Directory to save files.
    """
    ensure_directories([output_dir])
    
    discovery_path = output_dir / f"{tumor_type}_discovery_set.csv"
    training_path = output_dir / f"{tumor_type}_training_set.csv"
    
    discovery_df.to_csv(discovery_path, index=False)
    training_df.to_csv(training_path, index=False)
    
    logger.info(f"Saved discovery set to {discovery_path}")
    logger.info(f"Saved training set to {training_path}")

def process_tumor_type(
    tumor_type: str,
    processed_dir: Path,
    output_dir: Path,
    test_size: float = 0.3,
    random_state: int = 42
) -> Dict[str, Any]:
    """
    Main function to process a single tumor type: load, split, and save.
    
    Args:
        tumor_type: The tumor type identifier.
        processed_dir: Path to the directory containing normalized data.
        output_dir: Path to the directory to save split data.
        test_size: Proportion for the training set.
        random_state: Random seed for reproducibility.
        
    Returns:
        Dictionary with status and paths.
    """
    try:
        # 1. Load
        df = load_processed_data(tumor_type, processed_dir)
        
        # 2. Split
        discovery_df, training_df = split_data_stratified(
            df, 
            label_col='response_label',
            test_size=test_size,
            random_state=random_state
        )
        
        # 3. Save
        save_split_data(discovery_df, training_df, tumor_type, output_dir)
        
        return {
            "status": "success",
            "tumor_type": tumor_type,
            "discovery_path": str(output_dir / f"{tumor_type}_discovery_set.csv"),
            "training_path": str(output_dir / f"{tumor_type}_training_set.csv"),
            "discovery_count": len(discovery_df),
            "training_count": len(training_df)
        }
        
    except Exception as e:
        logger.error(f"Failed to process tumor type {tumor_type}: {e}")
        return {
            "status": "failed",
            "tumor_type": tumor_type,
            "error": str(e)
        }

def main():
    """
    Entry point for the splitting stage.
    Iterates over available tumor types in data/processed/ and splits them.
    """
    setup_logging()
    project_root = get_project_root()
    processed_dir = project_root / "data" / "processed"
    output_dir = processed_dir # Save back to processed as per task description
    
    if not processed_dir.exists():
        logger.error(f"Processed directory not found: {processed_dir}")
        sys.exit(1)
    
    # Identify tumor types by looking for files matching *_normalized.csv
    # Or we can read from a manifest if T012/T017 created one.
    # Assuming files exist from previous steps: {tumor_type}_normalized.csv
    tumor_files = list(processed_dir.glob("*_normalized.csv"))
    
    if not tumor_files:
        logger.warning("No normalized data files found. Skipping splitting.")
        # Create an empty summary or exit gracefully
        return
    
    results = []
    for file_path in tumor_files:
        tumor_type = file_path.stem.replace("_normalized", "")
        logger.info(f"Processing tumor type: {tumor_type}")
        result = process_tumor_type(tumor_type, processed_dir, output_dir)
        results.append(result)
    
    # Summary
    success_count = sum(1 for r in results if r["status"] == "success")
    logger.info(f"Splitting completed. Success: {success_count}/{len(results)}")
    
    if success_count == 0:
        sys.exit(1)

if __name__ == "__main__":
    main()