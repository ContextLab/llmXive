"""
Module: code/train_learning_curves.py

Purpose:
Generate learning curves for each material property by training Random Forest
regressors on varying subset sizes.

This implementation:
1. Loads the master dataset from data/processed/materials_master.parquet.
2. Iterates over distinct properties.
3. For each property, checks if the sample count >= 1,000.
   - If < 1,000, it logs a warning and SKIPS the property (error handling).
4. Generates 5 training subsets (sizes: 1000, 5000, 10000, 20000, 40000).
5. Trains a Random Forest model for each subset with a fixed seed.
6. Saves the results to data/processed/learning_curves.csv.
"""

import os
import sys
import logging
import traceback
import gc
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error

# Import config utilities
from config import get_config, require_data_dir
from utils.seed import set_seed
from utils.logging_config import setup_logging, get_logger

# Constants
LEARNING_CURVE_SIZES = [1000, 5000, 10000, 20000, 40000]
MIN_SAMPLES_THRESHOLD = 1000
RANDOM_SEED = 42
TEST_SIZE = 0.2

logger = get_logger(__name__)

def load_master_dataset(data_dir: Path) -> pd.DataFrame:
    """
    Loads the master dataset from data/processed/materials_master.parquet.
    
    Args:
        data_dir: Path to the data directory.
        
    Returns:
        DataFrame containing the master dataset.
        
    Raises:
        FileNotFoundError: If the master dataset does not exist.
    """
    master_path = data_dir / "processed" / "materials_master.parquet"
    if not master_path.exists():
        raise FileNotFoundError(
            f"Master dataset not found at {master_path}. "
            "Please run generate_descriptors.py first."
        )
    
    logger.info(f"Loading master dataset from {master_path}")
    df = pd.read_parquet(master_path)
    logger.info(f"Loaded {len(df)} records with columns: {list(df.columns)}")
    return df

def get_feature_columns(df: pd.DataFrame) -> List[str]:
    """
    Identifies feature columns (Magpie descriptors) in the dataframe.
    Assumes columns starting with 'magpie_' or similar are features,
    and specific property names are targets.
    """
    # Heuristic: Exclude common metadata columns and the target property column
    # We will identify target columns dynamically in the main loop.
    # For now, assume all numeric columns not in a specific exclusion list are features.
    exclude_cols = {'property_name', 'material_id', 'formula', 'target_value'}
    feature_cols = [col for col in df.columns 
                    if col not in exclude_cols and pd.api.types.is_numeric_dtype(df[col])]
    
    # If no features found, try to find columns with 'magpie' in name
    if not feature_cols:
        feature_cols = [col for col in df.columns if 'magpie' in col.lower()]
    
    if not feature_cols:
        raise ValueError("No feature columns found in the dataset.")
    
    return feature_cols

def train_single_model(X_train: pd.DataFrame, y_train: pd.Series, 
                       X_test: pd.DataFrame, y_test: pd.Series,
                       seed: int) -> Tuple[float, RandomForestRegressor]:
    """
    Trains a single Random Forest model and returns the RMSE on the test set.
    """
    set_seed(seed)
    
    model = RandomForestRegressor(
        n_estimators=100,
        max_depth=None,
        random_state=seed,
        n_jobs=-1
    )
    
    model.fit(X_train, y_train)
    y_pred = model.predict(X_test)
    rmse = np.sqrt(mean_squared_error(y_test, y_pred))
    
    return rmse, model

def generate_learning_curve_for_property(
    df: pd.DataFrame, 
    property_name: str, 
    feature_cols: List[str],
    target_col: str
) -> Optional[List[Dict[str, Any]]]:
    """
    Generates a learning curve for a specific property.
    
    Args:
        df: The master dataset.
        property_name: Name of the property to analyze.
        feature_cols: List of feature column names.
        target_col: Name of the target column.
        
    Returns:
        List of dicts containing learning curve data points, or None if insufficient data.
    """
    # Filter data for the specific property
    prop_df = df[df['property_name'] == property_name].copy()
    total_samples = len(prop_df)
    
    # Error Handling: Insufficient Data Points
    if total_samples < MIN_SAMPLES_THRESHOLD:
        logger.warning(
            f"Property '{property_name}' has only {total_samples} samples "
            f"(< {MIN_SAMPLES_THRESHOLD}). Skipping learning curve generation."
        )
        return None
    
    logger.info(
        f"Processing property '{property_name}' with {total_samples} samples."
    )
    
    results = []
    
    # Determine effective sizes (cannot exceed available data)
    # We need to ensure we have enough data for the largest subset requested
    # or cap at the available data if the request is too high.
    # However, the task specifies fixed sizes. If data < 40000, we might cap.
    # But the critical check is >= 1000.
    
    available_sizes = [s for s in LEARNING_CURVE_SIZES if s <= total_samples]
    
    if not available_sizes:
        logger.warning(
            f"No valid subset sizes for '{property_name}' (Total: {total_samples})."
        )
        return None
    
    # Prepare features and target
    X = prop_df[feature_cols].values
    y = prop_df[target_col].values
    
    # To ensure deterministic results across different subset sizes,
    # we sample from the full dataset.
    
    for size in available_sizes:
        # Sample 'size' points
        indices = np.random.choice(len(X), size=size, replace=False)
        X_subset = X[indices]
        y_subset = y[indices]
        
        # Split into train/test
        X_train, X_test, y_train, y_test = train_test_split(
            X_subset, y_subset, test_size=TEST_SIZE, random_state=RANDOM_SEED
        )
        
        # Train
        rmse, _ = train_single_model(X_train, y_train, X_test, y_test, RANDOM_SEED)
        
        results.append({
            "property_name": property_name,
            "training_size": size,
            "rmse": rmse,
            "seed": RANDOM_SEED
        })
        
        # Cleanup memory
        del X_train, X_test, y_train, y_test
        gc.collect()
    
    return results

def main():
    """
    Main entry point for generating learning curves.
    """
    setup_logging(level=logging.INFO)
    config = get_config()
    data_dir = require_data_dir(config)
    
    try:
        # Load data
        df = load_master_dataset(data_dir)
        
        # Identify properties
        if 'property_name' not in df.columns:
            raise ValueError("Column 'property_name' not found in dataset.")
        
        properties = df['property_name'].unique()
        logger.info(f"Found {len(properties)} distinct properties.")
        
        all_curve_data = []
        
        # Get feature columns (assuming they are constant across properties)
        # We need to infer this from the first property or the whole df
        # Assuming the master dataset has a unified schema
        feature_cols = get_feature_columns(df)
        
        # Target column name assumption
        target_col = 'target_value'
        if target_col not in df.columns:
            # Try to find a column that looks like a target
            # If the data is structured with property-specific columns, this logic changes.
            # Based on typical pipelines, 'target_value' is common.
            # If not found, we might need to adapt.
            raise ValueError(f"Target column '{target_col}' not found.")
        
        for prop in properties:
            curve_data = generate_learning_curve_for_property(
                df, prop, feature_cols, target_col
            )
            if curve_data:
                all_curve_data.extend(curve_data)
        
        if not all_curve_data:
            logger.warning("No learning curves generated. Check data availability.")
            # Create empty file to avoid crash downstream
            output_path = data_dir / "processed" / "learning_curves.csv"
            pd.DataFrame(columns=[
                "property_name", "training_size", "rmse", "seed"
            ]).to_csv(output_path, index=False)
        else:
            output_df = pd.DataFrame(all_curve_data)
            output_path = data_dir / "processed" / "learning_curves.csv"
            output_df.to_csv(output_path, index=False)
            logger.info(f"Saved learning curves to {output_path}")
            
    except Exception as e:
        logger.error(f"Error in main: {e}")
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()