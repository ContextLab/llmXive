"""
Train learning curves for material properties.

Generates 5 training subsets per property (sizes: 1000, 5000, 10000, 20000, 40000),
trains a Random Forest regressor for each subset using 1 random seed, and outputs
the results to a CSV file.

This implementation relies on the amendment ratified in T035 to deviate from
the Constitution's 10-subset/3-seed requirement.
"""

import os
import sys
import logging
import traceback
import gc
from pathlib import Path
from typing import List, Dict, Any, Optional

import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error
import joblib

# Project imports
from config import get_config, require_data_dir, require_state_dir
from utils.seed import set_seed
from utils.logging_config import setup_logging, get_logger
from models import LearningCurve

# Configure logging
logger = get_logger(__name__)

# Constants from task description
SUBSET_SIZES = [1000, 5000, 10000, 20000, 40000]
RANDOM_SEED = 42  # Fixed seed per task requirement
N_JOBS = -1  # Use all available cores

# Fixed hyperparameters for Random Forest
RF_PARAMS = {
    'n_estimators': 100,
    'max_depth': None,
    'min_samples_split': 2,
    'min_samples_leaf': 1,
    'random_state': RANDOM_SEED,
    'n_jobs': N_JOBS
}

def load_master_dataset(data_dir: Path) -> pd.DataFrame:
    """
    Load the consolidated master dataset from data/processed/materials_master.parquet.

    Args:
        data_dir: Path to the data directory.

    Returns:
        DataFrame with material properties and descriptors.

    Raises:
        FileNotFoundError: If the master dataset does not exist.
        ValueError: If the dataset is empty or missing required columns.
    """
    master_path = data_dir / "processed" / "materials_master.parquet"
    
    if not master_path.exists():
        raise FileNotFoundError(
            f"Master dataset not found at {master_path}. "
            "Run US1 (download_data, generate_descriptors, consolidate_data) first."
        )
    
    logger.info(f"Loading master dataset from {master_path}")
    df = pd.read_parquet(master_path)
    
    if df.empty:
        raise ValueError("Master dataset is empty.")
    
    # Validate required columns (property target and Magpie features)
    # Assuming the first non-property column is the target, and rest are features
    # This logic should match the output of generate_descriptors.py
    required_cols = ['property_name', 'value']
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing required columns in master dataset: {missing_cols}")
    
    logger.info(f"Loaded {len(df)} rows with columns: {list(df.columns)}")
    return df

def get_feature_columns(df: pd.DataFrame) -> List[str]:
    """
    Identify feature columns (Magpie descriptors) in the DataFrame.
    
    Assumes columns not named 'property_name', 'value', or 'material_id' are features.
    """
    exclude_cols = {'property_name', 'value', 'material_id', 'properties'}
    feature_cols = [col for col in df.columns if col not in exclude_cols]
    
    if not feature_cols:
        raise ValueError("No feature columns found in the dataset.")
    
    return feature_cols

def train_single_model(X_train: np.ndarray, y_train: np.ndarray, 
                       X_test: np.ndarray, y_test: np.ndarray,
                       params: Dict[str, Any]) -> Dict[str, Any]:
    """
    Train a single Random Forest model and return metrics.
    
    Args:
        X_train: Training features.
        y_train: Training targets.
        X_test: Test features.
        y_test: Test targets.
        params: Hyperparameters for the model.
    
    Returns:
        Dictionary with training metrics.
    """
    model = RandomForestRegressor(**params)
    model.fit(X_train, y_train)
    
    train_pred = model.predict(X_train)
    test_pred = model.predict(X_test)
    
    train_rmse = np.sqrt(mean_squared_error(y_train, train_pred))
    test_rmse = np.sqrt(mean_squared_error(y_test, test_pred))
    
    return {
        'train_rmse': train_rmse,
        'test_rmse': test_rmse,
        'model': model
    }

def generate_learning_curve_for_property(
    df_property: pd.DataFrame,
    property_name: str,
    feature_cols: List[str],
    subset_sizes: List[int],
    seed: int
) -> List[LearningCurve]:
    """
    Generate learning curve data for a single property.
    
    Args:
        df_property: DataFrame containing data for a single property.
        property_name: Name of the property.
        feature_cols: List of feature column names.
        subset_sizes: List of training subset sizes.
        seed: Random seed for reproducibility.
    
    Returns:
        List of LearningCurve objects.
    """
    results = []
    
    # Prepare data
    X = df_property[feature_cols].values
    y = df_property['value'].values
    n_samples = len(X)
    
    logger.info(f"Processing property '{property_name}' with {n_samples} samples")
    
    # Filter subset sizes that are feasible
    feasible_sizes = [s for s in subset_sizes if s < n_samples]
    if not feasible_sizes:
        logger.warning(f"No feasible subset sizes for property '{property_name}' "
                     f"(n={n_samples}, min_size={min(subset_sizes)})")
        return results
    
    # Set seed for this property's splits
    set_seed(seed)
    
    # Split into train/test once (80/20) to ensure consistent test set
    # The test set will be used to evaluate all subset sizes
    # We take 80% of data for training (to be subsampled) and 20% for testing
    X_train_full, X_test, y_train_full, y_test = train_test_split(
        X, y, test_size=0.2, random_state=seed
    )
    
    logger.info(f"  Train set: {len(X_train_full)}, Test set: {len(X_test)}")
    
    for size in feasible_sizes:
        logger.info(f"  Training subset size: {size}")
        
        # Subsample the training data
        if size >= len(X_train_full):
            # If requested size is larger than available, use all available
            X_sub = X_train_full
            y_sub = y_train_full
        else:
            # Randomly sample 'size' points from the full training set
            indices = np.random.choice(len(X_train_full), size=size, replace=False)
            X_sub = X_train_full[indices]
            y_sub = y_train_full[indices]
        
        # Train model
        metrics = train_single_model(X_sub, y_sub, X_test, y_test, RF_PARAMS)
        
        # Create LearningCurve object
        lc = LearningCurve(
            property_name=property_name,
            subset_size=size,
            train_rmse=metrics['train_rmse'],
            test_rmse=metrics['test_rmse'],
            seed=seed
        )
        results.append(lc)
        
        # Clean up model to free memory
        del metrics['model']
        gc.collect()
    
    return results

def main():
    """
    Main entry point for training learning curves.
    """
    try:
        # Setup
        config = get_config()
        data_dir = require_data_dir()
        state_dir = require_state_dir()
        
        setup_logging(
            log_dir=Path(state_dir) / "logs",
            log_file="train_learning_curves.log"
        )
        
        logger.info("Starting learning curve training")
        logger.info(f"Subset sizes: {SUBSET_SIZES}")
        logger.info(f"Random seed: {RANDOM_SEED}")
        logger.info(f"RF params: {RF_PARAMS}")
        
        # Load data
        df = load_master_dataset(data_dir)
        feature_cols = get_feature_columns(df)
        
        # Group by property
        properties = df['property_name'].unique()
        logger.info(f"Found {len(properties)} properties: {properties}")
        
        all_results = []
        
        for prop in properties:
            logger.info(f"Processing property: {prop}")
            df_prop = df[df['property_name'] == prop].copy()
            
            if len(df_prop) < min(SUBSET_SIZES):
                logger.warning(f"Skipping property '{prop}' due to insufficient data "
                             f"(n={len(df_prop)} < {min(SUBSET_SIZES)})")
                continue
            
            lc_results = generate_learning_curve_for_property(
                df_prop,
                prop,
                feature_cols,
                SUBSET_SIZES,
                RANDOM_SEED
            )
            all_results.extend(lc_results)
            
            logger.info(f"  Completed property '{prop}' with {len(lc_results)} learning curve points")
        
        if not all_results:
            logger.error("No learning curve results generated.")
            sys.exit(1)
        
        # Convert to DataFrame
        result_df = pd.DataFrame([lc.to_dict() for lc in all_results])
        
        # Save output
        output_path = Path(data_dir) / "processed" / "learning_curves.csv"
        output_path.parent.mkdir(parents=True, exist_ok=True)
        result_df.to_csv(output_path, index=False)
        
        logger.info(f"Saved learning curves to {output_path}")
        logger.info(f"Total learning curve points: {len(result_df)}")
        logger.info("Learning curve training completed successfully")
        
    except Exception as e:
        logger.error(f"Error during learning curve training: {e}")
        logger.error(traceback.format_exc())
        sys.exit(1)

if __name__ == "__main__":
    main()