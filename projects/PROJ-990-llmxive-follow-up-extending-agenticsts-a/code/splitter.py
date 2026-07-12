"""
Splitter module for stratified data splitting of trajectories.

This module performs a stratified split of trajectory data into training
and hold-out sets based on the utility scores derived from the ablation study.
"""
import os
import json
import logging
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, Any, Optional, Tuple

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import from existing project modules
from config import load_config_from_file, ensure_directories

def load_processed_data(
    utility_labels_path: str,
    parser_metrics_path: str
) -> pd.DataFrame:
    """
    Load and merge utility labels with parser metrics.

    Args:
        utility_labels_path: Path to utility_labels.csv
        parser_metrics_path: Path to parsed trajectory metrics

    Returns:
        Merged DataFrame containing both utility scores and trajectory metrics
    """
    logger.info(f"Loading utility labels from {utility_labels_path}")
    utility_df = pd.read_csv(utility_labels_path)
    
    logger.info(f"Loading parser metrics from {parser_metrics_path}")
    metrics_df = pd.read_csv(parser_metrics_path)

    # Merge on trajectory_id and turn_id
    merged_df = pd.merge(
        utility_df,
        metrics_df,
        on=['trajectory_id', 'turn_id'],
        how='inner'
    )

    logger.info(f"Merged dataset shape: {merged_df.shape}")
    logger.info(f"Columns: {merged_df.columns.tolist()}")
    
    return merged_df

def stratified_split(
    df: pd.DataFrame,
    stratify_column: str = 'utility_score',
    test_size: float = 0.2,
    random_state: int = 42
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Perform stratified split of the dataset.

    Args:
        df: Input DataFrame
        stratify_column: Column to use for stratification
        test_size: Proportion of data to include in hold-out set
        random_state: Random seed for reproducibility

    Returns:
        Tuple of (train_df, holdout_df)
    """
    # Ensure stratify column exists
    if stratify_column not in df.columns:
        raise ValueError(f"Stratify column '{stratify_column}' not found in DataFrame")

    # For continuous utility_score, we bin it for stratification
    if df[stratify_column].dtype in ['float64', 'float32']:
        logger.info(f"Binning continuous {stratify_column} for stratification")
        # Create bins based on percentiles to ensure balanced stratification
        n_bins = 5
        df = df.copy()
        df['_stratify_bins'] = pd.qcut(
            df[stratify_column], 
            q=n_bins, 
            labels=False, 
            duplicates='drop'
        )
        stratify_col = '_stratify_bins'
    else:
        stratify_col = stratify_column

    # Perform stratified split
    train_df, holdout_df = train_test_split(
        df,
        test_size=test_size,
        stratify=df[stratify_col],
        random_state=random_state
    )

    # Drop the temporary bin column if it was created
    if '_stratify_bins' in train_df.columns:
        train_df = train_df.drop(columns=['_stratify_bins'])
    if '_stratify_bins' in holdout_df.columns:
        holdout_df = holdout_df.drop(columns=['_stratify_bins'])

    logger.info(f"Train set size: {len(train_df)}")
    logger.info(f"Hold-out set size: {len(holdout_df)}")
    
    return train_df, holdout_df

def train_test_split(
    df: pd.DataFrame,
    test_size: float,
    stratify: pd.Series,
    random_state: int
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Custom stratified train-test split implementation without sklearn dependency.
    
    Args:
        df: Input DataFrame
        test_size: Proportion for test set
        stratify: Series to stratify by
        random_state: Random seed

    Returns:
        Tuple of (train_df, test_df)
    """
    np.random.seed(random_state)
    
    train_indices = []
    test_indices = []
    
    # Group by stratify column
    unique_strata = stratify.unique()
    
    for stratum in unique_strata:
        stratum_mask = stratify == stratum
        stratum_indices = df.index[stratum_mask].tolist()
        
        # Shuffle indices
        np.random.shuffle(stratum_indices)
        
        # Calculate split point
        n_stratum = len(stratum_indices)
        n_test = int(n_stratum * test_size)
        
        # Split
        test_indices.extend(stratum_indices[:n_test])
        train_indices.extend(stratum_indices[n_test:])
    
    train_df = df.loc[train_indices].reset_index(drop=True)
    test_df = df.loc[test_indices].reset_index(drop=True)
    
    return train_df, test_df

def save_split_data(
    train_df: pd.DataFrame,
    holdout_df: pd.DataFrame,
    output_dir: str
) -> None:
    """
    Save split datasets to CSV files.

    Args:
        train_df: Training DataFrame
        holdout_df: Hold-out DataFrame
        output_dir: Directory to save files
    """
    train_path = Path(output_dir) / 'train_set.csv'
    holdout_path = Path(output_dir) / 'holdout_set.csv'

    logger.info(f"Saving train set to {train_path}")
    train_df.to_csv(train_path, index=False)
    
    logger.info(f"Saving hold-out set to {holdout_path}")
    holdout_df.to_csv(holdout_path, index=False)

    # Log distribution statistics
    logger.info(f"Train set statistics:")
    logger.info(f"  Shape: {train_df.shape}")
    if 'utility_score' in train_df.columns:
        logger.info(f"  Utility score mean: {train_df['utility_score'].mean():.4f}")
        logger.info(f"  Utility score std: {train_df['utility_score'].std():.4f}")
    
    logger.info(f"Hold-out set statistics:")
    logger.info(f"  Shape: {holdout_df.shape}")
    if 'utility_score' in holdout_df.columns:
        logger.info(f"  Utility score mean: {holdout_df['utility_score'].mean():.4f}")
        logger.info(f"  Utility score std: {holdout_df['utility_score'].std():.4f}")

def validate_split(
    train_df: pd.DataFrame,
    holdout_df: pd.DataFrame,
    stratify_column: str = 'utility_score'
) -> Dict[str, Any]:
    """
    Validate that the split is appropriate.

    Args:
        train_df: Training DataFrame
        holdout_df: Hold-out DataFrame
        stratify_column: Column used for stratification

    Returns:
        Validation report dictionary
    """
    report = {
        'train_size': len(train_df),
        'holdout_size': len(holdout_df),
        'total_size': len(train_df) + len(holdout_df),
        'train_ratio': len(train_df) / (len(train_df) + len(holdout_df)),
        'holdout_ratio': len(holdout_df) / (len(train_df) + len(holdout_df))
    }

    if stratify_column in train_df.columns:
        train_stats = train_df[stratify_column].describe()
        holdout_stats = holdout_df[stratify_column].describe()
        
        report['train_mean'] = float(train_stats['mean'])
        report['train_std'] = float(train_stats['std'])
        report['holdout_mean'] = float(holdout_stats['mean'])
        report['holdout_std'] = float(holdout_stats['std'])
        
        # Check if means are similar (within 10%)
        if report['train_mean'] != 0:
            diff_pct = abs(report['train_mean'] - report['holdout_mean']) / abs(report['train_mean'])
            report['mean_diff_pct'] = diff_pct
            report['distribution_match'] = diff_pct < 0.1
        else:
            report['mean_diff_pct'] = 0.0
            report['distribution_match'] = True

    return report

def main():
    """
    Main entry point for the splitter module.
    
    Reads utility labels and parser metrics, performs stratified split,
    and saves train and hold-out sets.
    """
    # Load configuration
    config = load_config_from_file()
    
    # Ensure output directories exist
    ensure_directories(config)
    
    # Define paths
    utility_labels_path = config.get('paths', {}).get('utility_labels', 'data/processed/utility_labels.csv')
    parser_metrics_path = config.get('paths', {}).get('parser_metrics', 'data/processed/parser_metrics.csv')
    output_dir = config.get('paths', {}).get('processed', 'data/processed')
    
    # Check if input files exist
    if not os.path.exists(utility_labels_path):
        raise FileNotFoundError(f"Utility labels file not found: {utility_labels_path}")
    if not os.path.exists(parser_metrics_path):
        raise FileNotFoundError(f"Parser metrics file not found: {parser_metrics_path}")
    
    # Load and merge data
    merged_df = load_processed_data(utility_labels_path, parser_metrics_path)
    
    if merged_df.empty:
        raise ValueError("Merged dataset is empty. Check input files and merge keys.")
    
    # Perform stratified split
    logger.info("Performing stratified split...")
    train_df, holdout_df = stratified_split(
        merged_df,
        stratify_column='utility_score',
        test_size=0.2,
        random_state=config.get('hyperparameters', {}).get('random_state', 42)
    )
    
    # Validate split
    validation_report = validate_split(train_df, holdout_df)
    logger.info(f"Split validation: {json.dumps(validation_report, indent=2)}")
    
    # Save split data
    save_split_data(train_df, holdout_df, output_dir)
    
    # Save validation report
    report_path = Path(output_dir) / 'split_validation_report.json'
    with open(report_path, 'w') as f:
        json.dump(validation_report, f, indent=2)
    
    logger.info(f"Split complete. Validation report saved to {report_path}")
    logger.info(f"Train set: {len(train_df)} samples")
    logger.info(f"Hold-out set: {len(holdout_df)} samples")

if __name__ == '__main__':
    main()
