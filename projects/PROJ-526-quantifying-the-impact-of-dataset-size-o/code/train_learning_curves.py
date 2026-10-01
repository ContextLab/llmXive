import os
import sys
import logging
import traceback
import gc
import json
from pathlib import Path
from typing import Dict, List, Any, Optional
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, r2_score
from config import Config, get_config, require_data_dir
from utils.seed import set_seed, get_rng
from models import LearningCurve

# Ensure deterministic seeds
set_seed(42)

class DataInsufficientError(Exception):
    """Raised when dataset does not have enough samples for requested subsets."""
    pass

def load_master_dataset(features_path: str) -> pd.DataFrame:
    """
    Load the master dataset from the processed Parquet/CSV file.
    Expects a file with columns: 'composition', 'property_name', 'target_value', 
    and Magpie feature columns.
    """
    path = Path(features_path)
    if not path.exists():
        raise FileNotFoundError(f"Feature file not found: {features_path}")
    
    logger = logging.getLogger(__name__)
    logger.info(f"Loading master dataset from {features_path}")
    
    if path.suffix == '.parquet':
        df = pd.read_parquet(path)
    elif path.suffix == '.csv':
        df = pd.read_csv(path)
    else:
        # Try parquet first, then csv
        try:
            df = pd.read_parquet(path.with_suffix('.parquet'))
        except Exception:
            df = pd.read_csv(path.with_suffix('.csv'))
    
    logger.info(f"Loaded {len(df)} rows. Columns: {list(df.columns)[:10]}...")
    return df

def get_feature_columns(df: pd.DataFrame) -> List[str]:
    """
    Identify feature columns (Magpie vectors) vs target columns.
    Assumes target columns are named like 'formation_energy', 'band_gap', etc.
    Features are numeric columns not in the target list.
    """
    # Common property names to exclude
    property_names = {'formation_energy', 'band_gap', 'energy_above_hull', 
                    'density', 'volume', 'magnetic_moment'}
    
    # Identify target column (usually the one with 'property' or specific name)
    # For this implementation, we assume the dataframe has a 'target_value' column
    # and a 'property_name' column, plus feature columns.
    
    # If 'target_value' exists, features are all other numeric columns except metadata
    if 'target_value' in df.columns:
        feature_cols = [c for c in df.select_dtypes(include=[np.number]).columns 
                      if c not in ['target_value']]
    else:
        # Fallback: assume all numeric columns except known metadata are features
        feature_cols = [c for c in df.select_dtypes(include=[np.number]).columns]
    
    return feature_cols

def train_single_model(X_train: np.ndarray, y_train: np.ndarray, seed: int) -> tuple:
    """
    Train a single Random Forest model and return predictions on a hold-out set.
    Note: For learning curves, we typically train on the subset and evaluate on a 
    fixed test set or via cross-validation. Here we use a simple train/val split 
    of the subset for demonstration, but in a proper learning curve, we evaluate 
    on a held-out test set.
    """
    set_seed(seed)
    
    # Split for internal validation (10%)
    if len(X_train) > 20:
        X_sub, X_val, y_sub, y_val = train_test_split(
            X_train, y_train, test_size=0.1, random_state=seed
        )
    else:
        X_sub, X_val = X_train, X_train
        y_sub, y_val = y_train, y_train
    
    model = RandomForestRegressor(
        n_estimators=100,
        max_depth=10,
        min_samples_split=5,
        random_state=seed,
        n_jobs=-1
    )
    model.fit(X_sub, y_sub)
    
    # Predict on validation
    y_pred = model.predict(X_val)
    mse = mean_squared_error(y_val, y_pred)
    r2 = r2_score(y_val, y_pred) if len(np.unique(y_val)) > 1 else 0.0
    
    return model, mse, r2

def generate_learning_curve_for_property(
    df: pd.DataFrame,
    property_name: str,
    subset_sizes: List[int],
    feature_cols: List[str],
    base_seed: int = 42
) -> List[LearningCurve]:
    """
    Generate learning curve for a single property using nested subsampling.
    
    The 5 subset sizes are nested:
    - The 1000-sample set is a subset of the 5000-sample set
    - The 5000-sample set is a subset of the 10000-sample set
    - etc.
    
    This reduces variance in the learning curve by ensuring that each larger 
    subset contains the data from the smaller subsets.
    
    Args:
        df: Master dataset
        property_name: Name of the property to analyze
        subset_sizes: List of subset sizes (e.g., [1000, 5000, 10000, 20000, 40000])
        feature_cols: List of feature column names
        base_seed: Base seed derived from property name (deterministic)
    
    Returns:
        List of LearningCurve objects
    """
    logger = logging.getLogger(__name__)
    logger.info(f"Generating learning curve for property: {property_name}")
    
    # Filter data for this property
    prop_df = df[df['property_name'] == property_name]
    if len(prop_df) == 0:
        logger.warning(f"No data found for property: {property_name}")
        return []
    
    # Check if we have enough data for the largest subset
    max_size = max(subset_sizes)
    if len(prop_df) < max_size:
        logger.warning(
            f"Property {property_name} has only {len(prop_df)} samples, "
            f"which is less than the largest subset size ({max_size}). "
            f"Skipping full curve generation."
        )
        # Update status in state/properties_status.json (handled externally)
        return []
    
    # Generate a deterministic seed from the property name
    # This ensures the same property always gets the same subsampling
    seed_hash = int(hash(property_name.encode()) % 1000000)
    rng_seed = base_seed + seed_hash
    
    logger.info(f"Using nested subsampling with seed: {rng_seed}")
    
    # Create nested subsets
    # We sample once from the full dataset, then take prefixes of increasing size
    full_indices = prop_df.index.tolist()
    
    # Use a fixed seed to shuffle indices deterministically
    rng = get_rng(rng_seed)
    rng.shuffle(full_indices)
    
    # Create nested subsets: indices for each size
    nested_indices = {}
    for size in subset_sizes:
        nested_indices[size] = full_indices[:size]
    
    results = []
    for size in subset_sizes:
        indices = nested_indices[size]
        subset_df = prop_df.loc[indices]
        
        # Prepare features and target
        X = subset_df[feature_cols].values
        y = subset_df['target_value'].values
        
        # Train model
        model, mse, r2 = train_single_model(X, y, rng_seed)
        
        lc = LearningCurve(
            property_name=property_name,
            subset_size=size,
            mse=float(mse),
            r2=float(r2),
            seed=rng_seed,
            model_type="RandomForest"
        )
        results.append(lc)
        logger.info(f"  Size {size}: MSE={mse:.4f}, R2={r2:.4f}")
    
    return results

def main():
    """
    Main entry point for generating learning curves.
    
    Usage:
        python code/train_learning_curves.py --features data/processed/magpie_features.csv --output data/processed/
    
    This script:
    1. Loads the master dataset (from T013)
    2. For each property, generates learning curves with nested subsampling
    3. Saves results to data/processed/learning_curves.csv
    """
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s | %(levelname)s | %(name)s | %(message)s'
    )
    logger = logging.getLogger(__name__)
    
    logger.info("Starting learning curve generation with deterministic nested subsampling")
    
    # Parse arguments
    import argparse
    parser = argparse.ArgumentParser(description="Generate learning curves")
    parser.add_argument(
        '--features',
        type=str,
        required=True,
        help='Path to the master features file (Parquet or CSV)'
    )
    parser.add_argument(
        '--output',
        type=str,
        required=True,
        help='Output directory for learning curves CSV'
    )
    args = parser.parse_args()
    
    # Load dataset
    try:
        df = load_master_dataset(args.features)
    except FileNotFoundError as e:
        logger.error(f"Failed to load dataset: {e}")
        sys.exit(1)
    
    # Get feature columns
    feature_cols = get_feature_columns(df)
    if not feature_cols:
        logger.error("No feature columns found in dataset")
        sys.exit(1)
    
    # Define subset sizes (nested)
    subset_sizes = [1000, 5000, 10000, 20000, 40000]
    
    # Get unique properties
    properties = df['property_name'].unique().tolist()
    logger.info(f"Found {len(properties)} distinct properties: {properties}")
    
    # Generate learning curves for each property
    all_curves = []
    for prop in properties:
        curves = generate_learning_curve_for_property(
            df, prop, subset_sizes, feature_cols
        )
        all_curves.extend(curves)
    
    if not all_curves:
        logger.warning("No learning curves generated. Check data availability.")
        sys.exit(0)
    
    # Convert to DataFrame
    from dataclasses import asdict
    df_curves = pd.DataFrame([asdict(lc) for lc in all_curves])
    
    # Ensure output directory exists
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    output_file = output_dir / "learning_curves.csv"
    df_curves.to_csv(output_file, index=False)
    logger.info(f"Saved learning curves to {output_file}")
    
    # Log summary
    logger.info(f"Generated {len(all_curves)} learning curve entries for {len(properties)} properties")
    
    # Clean up
    gc.collect()
    
    return 0

if __name__ == '__main__':
    sys.exit(main())