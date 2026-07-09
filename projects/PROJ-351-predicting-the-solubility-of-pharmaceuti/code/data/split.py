"""
Split cleaned graph data into train/validation/test sets using stratified sampling
based on quantile binning of the logS target variable.
"""
import os
import sys
import json
import logging
from pathlib import Path
from typing import Dict, List, Any, Tuple

import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split

# Configure logging for this module
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import seed utilities from config
try:
    from code.config.seeds import get_seed, set_seed, ensure_seeded
except ImportError:
    # Fallback for direct execution if path not set up
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
    from config.seeds import get_seed, set_seed, ensure_seeded


def load_cleaned_data(input_path: str) -> pd.DataFrame:
    """
    Load the preprocessed graph data containing SMILES and logS values.
    
    Args:
        input_path: Path to the cleaned CSV file (e.g., data/processed/cleaned_graphs.csv)
        
    Returns:
        DataFrame with molecule data
        
    Raises:
        FileNotFoundError: If input file does not exist
        ValueError: If required columns are missing
    """
    logger.info(f"Loading cleaned data from {input_path}")
    df = pd.read_csv(input_path)
    
    required_cols = ['smiles', 'logS']
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing required columns: {missing_cols}")
        
    logger.info(f"Loaded {len(df)} molecules. Columns: {list(df.columns)}")
    return df


def create_stratified_splits(
    df: pd.DataFrame,
    test_size: float = 0.2,
    val_size: float = 0.1,
    n_bins: int = 10,
    random_state: int = 42
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Perform stratified train/validation/test split using quantile binning on logS.
    
    This ensures that the distribution of solubility values (logS) is preserved
    across all splits, which is critical for regression tasks where the target
    distribution might be skewed.
    
    Args:
        df: Input DataFrame with 'smiles' and 'logS' columns
        test_size: Fraction of data for test set
        val_size: Fraction of data for validation set
        n_bins: Number of quantile bins for stratification
        random_state: Random seed for reproducibility
        
    Returns:
        Tuple of (train_df, val_df, test_df)
    """
    logger.info(f"Creating stratified splits: test={test_size}, val={val_size}, bins={n_bins}")
    
    # Set seed for reproducibility
    set_seed(random_state)
    
    # Filter out any remaining NaN logS values (should be none, but safety first)
    df_clean = df.dropna(subset=['logS'])
    
    if len(df_clean) == 0:
        raise ValueError("No valid data remaining after dropping NaN logS values")
    
    # Create quantile bins for stratification
    # We use 'qcut' to create bins with approximately equal number of samples
    df_copy = df_clean.copy()
    df_copy['logS_bin'] = pd.qcut(df_copy['logS'], q=n_bins, duplicates='drop')
    
    # First split: separate test set from train+val
    train_val_df, test_df = train_test_split(
        df_copy,
        test_size=test_size,
        stratify=df_copy['logS_bin'],
        random_state=random_state
    )
    
    # Calculate relative validation size for the remaining data
    # If test_size=0.2 and val_size=0.1, then val should be 0.1/0.8 of the remaining
    remaining_size = 1.0 - test_size
    val_ratio_relative = val_size / remaining_size
    
    # Second split: separate validation set from training set
    train_df, val_df = train_test_split(
        train_val_df,
        test_size=val_ratio_relative,
        stratify=train_val_df['logS_bin'],
        random_state=random_state
    )
    
    # Drop the temporary bin column
    train_df = train_df.drop(columns=['logS_bin'])
    val_df = val_df.drop(columns=['logS_bin'])
    test_df = test_df.drop(columns=['logS_bin'])
    
    logger.info(f"Split complete:")
    logger.info(f"  Train: {len(train_df)} ({len(train_df)/len(df):.1%})")
    logger.info(f"  Val:   {len(val_df)} ({len(val_df)/len(df):.1%})")
    logger.info(f"  Test:  {len(test_df)} ({len(test_df)/len(df):.1%})")
    
    # Log logS statistics for each split
    for split_name, split_df in [('Train', train_df), ('Val', val_df), ('Test', test_df)]:
        logS_mean = split_df['logS'].mean()
        logS_std = split_df['logS'].std()
        logS_min = split_df['logS'].min()
        logS_max = split_df['logS'].max()
        logger.info(f"  {split_name} logS stats: mean={logS_mean:.3f}, std={logS_std:.3f}, "
                    f"range=[{logS_min:.3f}, {logS_max:.3f}]")
    
    return train_df, val_df, test_df


def save_split_indices(
    train_df: pd.DataFrame,
    val_df: pd.DataFrame,
    test_df: pd.DataFrame,
    output_dir: str,
    smiles_col: str = 'smiles'
) -> Dict[str, str]:
    """
    Save the split indices and data to JSON and CSV files.
    
    We save:
    1. Full dataframes as CSV for each split
    2. Indices (SMILES strings) as JSON lists for easy loading in training
    
    Args:
        train_df: Training set DataFrame
        val_df: Validation set DataFrame
        test_df: Test set DataFrame
        output_dir: Directory to save output files
        smiles_col: Column name containing SMILES strings
        
    Returns:
        Dictionary mapping split names to output file paths
    """
    logger.info(f"Saving split indices to {output_dir}")
    
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    files_saved = {}
    
    # Save CSV files with full data
    csv_files = {
        'train': 'train.csv',
        'val': 'val.csv',
        'test': 'test.csv'
    }
    
    for split_name, filename in csv_files.items():
        df = {'train': train_df, 'val': val_df, 'test': test_df}[split_name]
        csv_path = output_path / filename
        df.to_csv(csv_path, index=False)
        files_saved[split_name] = str(csv_path)
        logger.info(f"Saved {split_name} CSV: {csv_path} ({len(df)} rows)")
    
    # Save JSON files with just the SMILES indices
    json_files = {
        'train': 'train_indices.json',
        'val': 'val_indices.json',
        'test': 'test_indices.json'
    }
    
    for split_name, filename in json_files.items():
        df = {'train': train_df, 'val': val_df, 'test': test_df}[split_name]
        indices = df[smiles_col].tolist()
        json_path = output_path / filename
        with open(json_path, 'w') as f:
            json.dump(indices, f, indent=2)
        files_saved[split_name] = str(json_path)
        logger.info(f"Saved {split_name} indices: {json_path} ({len(indices)} items)")
    
    # Save metadata about the split
    metadata = {
        'split_ratios': {
            'train': len(train_df) / (len(train_df) + len(val_df) + len(test_df)),
            'val': len(val_df) / (len(train_df) + len(val_df) + len(test_df)),
            'test': len(test_df) / (len(train_df) + len(val_df) + len(test_df))
        },
        'counts': {
            'train': len(train_df),
            'val': len(val_df),
            'test': len(test_df),
            'total': len(train_df) + len(val_df) + len(test_df)
        },
        'logS_stats': {
            'train': {
                'mean': float(train_df['logS'].mean()),
                'std': float(train_df['logS'].std()),
                'min': float(train_df['logS'].min()),
                'max': float(train_df['logS'].max())
            },
            'val': {
                'mean': float(val_df['logS'].mean()),
                'std': float(val_df['logS'].std()),
                'min': float(val_df['logS'].min()),
                'max': float(val_df['logS'].max())
            },
            'test': {
                'mean': float(test_df['logS'].mean()),
                'std': float(test_df['logS'].std()),
                'min': float(test_df['logS'].min()),
                'max': float(test_df['logS'].max())
            }
        }
    }
    
    metadata_path = output_path / 'split_metadata.json'
    with open(metadata_path, 'w') as f:
        json.dump(metadata, f, indent=2)
    logger.info(f"Saved split metadata: {metadata_path}")
    
    return files_saved


def main():
    """
    Main entry point for the split script.
    
    Reads cleaned data from data/processed/cleaned_graphs.csv,
    performs stratified split, and saves results to data/processed/.
    """
    logger.info("Starting data split process")
    
    # Define paths
    project_root = Path(__file__).resolve().parents[2]
    input_path = project_root / "data" / "processed" / "cleaned_graphs.csv"
    output_dir = project_root / "data" / "processed"
    
    # Ensure input file exists
    if not input_path.exists():
        logger.error(f"Input file not found: {input_path}")
        logger.error("Please run code/data/preprocess.py first to generate cleaned data.")
        sys.exit(1)
    
    try:
        # Load cleaned data
        df = load_cleaned_data(str(input_path))
        
        # Perform stratified split
        train_df, val_df, test_df = create_stratified_splits(
            df,
            test_size=0.2,
            val_size=0.1,
            n_bins=10,
            random_state=get_seed()  # Use global seed configuration
        )
        
        # Save split indices
        saved_files = save_split_indices(
            train_df,
            val_df,
            test_df,
            str(output_dir)
        )
        
        logger.info("Split process completed successfully!")
        logger.info(f"Output files: {saved_files}")
        
    except Exception as e:
        logger.error(f"Error during split process: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()