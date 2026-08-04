import os
import sys
import logging
import traceback
import gc
import json
import math
from pathlib import Path
from typing import List, Dict, Any, Optional

import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error

# Local imports matching API surface
from utils.logging_config import setup_logging, get_logger
from utils.seed import set_seed
from config import get_config

# Configure logging
logger = get_logger(__name__)

class DataInsufficientError(Exception):
    """Raised when dataset size is insufficient for requested subset sizes."""
    pass

def load_master_dataset(features_path: str) -> pd.DataFrame:
    """
    Load the master dataset containing materials and their descriptors.
    
    Args:
        features_path: Path to the Parquet or CSV file containing features.
        
    Returns:
        DataFrame with material properties and descriptors.
        
    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If the file format is unsupported.
    """
    path = Path(features_path)
    if not path.exists():
        raise FileNotFoundError(f"Feature file not found: {features_path}")
    
    if path.suffix == '.parquet':
        df = pd.read_parquet(path)
    elif path.suffix == '.csv':
        df = pd.read_csv(path)
    else:
        raise ValueError(f"Unsupported file format: {path.suffix}. Use .parquet or .csv")
    
    logger.info(f"Loaded dataset with {len(df)} rows and {len(df.columns)} columns")
    return df

def get_feature_columns(df: pd.DataFrame, exclude_cols: List[str] = None) -> List[str]:
    """
    Identify feature columns for training.
    
    Args:
        df: Input DataFrame.
        exclude_cols: Columns to exclude from features (e.g., target, ID).
        
    Returns:
        List of feature column names.
    """
    if exclude_cols is None:
        exclude_cols = ['property_name', 'material_id', 'target']
    
    feature_cols = [col for col in df.columns if col not in exclude_cols]
    logger.info(f"Identified {len(feature_cols)} feature columns")
    return feature_cols

def train_single_model(X_train, y_train, X_test, y_test, seed: int = 42) -> Dict[str, Any]:
    """
    Train a single Random Forest model and return metrics.
    
    Args:
        X_train: Training features.
        y_train: Training targets.
        X_test: Test features.
        y_test: Test targets.
        seed: Random seed for reproducibility.
        
    Returns:
        Dictionary containing RMSE and R2 score.
    """
    set_seed(seed)
    
    model = RandomForestRegressor(
        n_estimators=100,
        max_depth=10,
        min_samples_split=2,
        min_samples_leaf=1,
        random_state=seed,
        n_jobs=-1
    )
    
    model.fit(X_train, y_train)
    y_pred = model.predict(X_test)
    
    rmse = np.sqrt(mean_squared_error(y_test, y_pred))
    
    # Calculate R2 score
    ss_res = np.sum((y_test - y_pred) ** 2)
    ss_tot = np.sum((y_test - np.mean(y_test)) ** 2)
    r2 = 1 - (ss_res / ss_tot) if ss_tot != 0 else 0.0
    
    return {
        'rmse': float(rmse),
        'r2': float(r2),
        'n_train': len(y_train),
        'n_test': len(y_test)
    }

def generate_learning_curve_for_property(
    df: pd.DataFrame,
    property_name: str,
    target_col: str,
    feature_cols: List[str],
    subset_sizes: List[int] = [1000, 5000, 10000, 20000, 40000],
    seed: int = 42
) -> Optional[Dict[str, Any]]:
    """
    Generate a learning curve for a specific property.
    
    Args:
        df: Full dataset.
        property_name: Name of the property to analyze.
        target_col: Name of the target column.
        feature_cols: List of feature column names.
        subset_sizes: List of training subset sizes to evaluate.
        seed: Base random seed.
        
    Returns:
        Dictionary containing learning curve results or None if data is insufficient.
    """
    # Filter data for this property
    prop_data = df[df['property_name'] == property_name].copy()
    total_entries = len(prop_data)
    
    logger.info(f"Processing property '{property_name}' with {total_entries} entries")
    
    # Pre-check: Verify dataset size against maximum subset size
    max_subset = max(subset_sizes)
    if total_entries < max_subset:
        logger.warning(f"Property '{property_name}' has only {total_entries} entries, "
                     f"which is less than the required maximum subset size of {max_subset}. "
                     f"Skipping full curve generation.")
        
        # Update state/properties_status.json
        status_path = Path("state/properties_status.json")
        status_data = {}
        if status_path.exists():
            with open(status_path, 'r') as f:
                status_data = json.load(f)
        
        status_data[property_name] = {
            'total_entries': total_entries,
            'max_subset_size': total_entries,
            'status': 'skipped_insufficient_data',
            'reason': f'Only {total_entries} entries available, need {max_subset}'
        }
        
        with open(status_path, 'w') as f:
            json.dump(status_data, f, indent=2)
        
        return None
    
    # Prepare features and target
    if target_col not in prop_data.columns:
        logger.error(f"Target column '{target_col}' not found in property data")
        return None
        
    X = prop_data[feature_cols].values
    y = prop_data[target_col].values
    
    # Remove NaN values if any
    mask = ~np.isnan(X).any(axis=1) & ~np.isnan(y)
    X = X[mask]
    y = y[mask]
    
    if len(X) < max_subset:
        logger.warning(f"After cleaning, property '{property_name}' has {len(X)} entries, "
                     f"which is less than {max_subset}. Skipping.")
        return None
    
    results = []
    
    for size in subset_sizes:
        logger.info(f"Training on {size} samples for {property_name}")
        
        # Use stratified sampling if possible, otherwise random
        # For simplicity, we take the first 'size' samples after shuffling with seed
        indices = np.arange(len(X))
        np.random.seed(seed)
        np.random.shuffle(indices)
        
        train_indices = indices[:size]
        X_train = X[train_indices]
        y_train = y[train_indices]
        
        # Create a small test set (20% of the training size)
        test_size = max(100, int(size * 0.2))
        test_indices = indices[size:size + test_size]
        
        # Ensure we have enough data for test
        if len(test_indices) < test_size:
            test_indices = indices[:test_size]
            
        X_test = X[test_indices]
        y_test = y[test_indices]
        
        metrics = train_single_model(X_train, y_train, X_test, y_test, seed)
        
        results.append({
            'property_name': property_name,
            'subset_size': size,
            'rmse': metrics['rmse'],
            'r2': metrics['r2'],
            'n_train': metrics['n_train'],
            'n_test': metrics['n_test']
        })
    
    return {
        'property_name': property_name,
        'learning_curve': results,
        'total_available': len(X)
    }

def main():
    """Main entry point for learning curve generation."""
    # Parse arguments
    import argparse
    parser = argparse.ArgumentParser(description='Generate learning curves for material properties')
    parser.add_argument('--features', type=str, default='data/processed/magpie_features.parquet',
                      help='Path to features file')
    parser.add_argument('--output', type=str, default='data/processed/learning_curves.csv',
                      help='Output path for learning curve results')
    parser.add_argument('--target', type=str, default='target',
                      help='Name of target column')
    parser.add_argument('--seed', type=int, default=42,
                      help='Random seed')
    parser.add_argument('--subset-sizes', type=str, default='1000,5000,10000,20000,40000',
                      help='Comma-separated list of subset sizes')
    
    args = parser.parse_args()
    
    # Setup logging
    setup_logging()
    
    logger.info("Starting learning curve generation")
    
    try:
        # Load dataset
        df = load_master_dataset(args.features)
        
        # Get feature columns
        feature_cols = get_feature_columns(df, exclude_cols=['property_name', 'material_id', args.target])
        
        # Parse subset sizes
        subset_sizes = [int(x.strip()) for x in args.subset_sizes.split(',')]
        subset_sizes = sorted(subset_sizes)
        
        logger.info(f"Using subset sizes: {subset_sizes}")
        
        # Get unique properties
        properties = df['property_name'].unique()
        logger.info(f"Found {len(properties)} properties: {properties}")
        
        all_results = []
        
        for prop in properties:
            result = generate_learning_curve_for_property(
                df, prop, args.target, feature_cols, subset_sizes, args.seed
            )
            
            if result:
                all_results.extend(result['learning_curve'])
                logger.info(f"Completed learning curve for {prop}")
            else:
                logger.warning(f"Skipped {prop} due to insufficient data")
        
        if not all_results:
            logger.error("No learning curves were generated. Check data availability.")
            sys.exit(1)
        
        # Save results
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        results_df = pd.DataFrame(all_results)
        results_df.to_csv(output_path, index=False)
        
        logger.info(f"Saved learning curves to {output_path}")
        logger.info(f"Generated {len(all_results)} learning curve points across {len(properties)} properties")
        
    except Exception as e:
        logger.error(f"Error during learning curve generation: {e}")
        traceback.print_exc()
        sys.exit(1)
    finally:
        gc.collect()

if __name__ == '__main__':
    main()