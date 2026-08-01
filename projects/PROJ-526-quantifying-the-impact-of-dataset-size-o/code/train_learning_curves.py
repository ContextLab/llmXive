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
import joblib

# Import local utilities
from utils.seed import set_seed
from utils.logging_config import get_logger, log_error_summary

# Import config
from config import get_config

logger = get_logger(__name__)

# Constants from task description
SUBSET_SIZES = [1000, 5000, 10000, 20000, 40000]
MIN_SAMPLES_THRESHOLD = 1000
RANDOM_SEED = 42

class DataInsufficientError(Exception):
    """Raised when a property does not have enough data points for training."""
    pass

def load_master_dataset() -> pd.DataFrame:
    """
    Loads the consolidated master dataset from the processed data directory.
    Returns:
        pd.DataFrame: The master dataset.
    """
    config = get_config()
    master_path = config.data_dir / "processed" / "materials_master.parquet"
    
    if not master_path.exists():
        raise FileNotFoundError(f"Master dataset not found at {master_path}. "
                                "Please run data generation pipelines first.")
    
    logger.info(f"Loading master dataset from {master_path}")
    df = pd.read_parquet(master_path)
    logger.info(f"Loaded {len(df)} records with {len(df.columns)} columns")
    return df

def get_feature_columns(df: pd.DataFrame) -> List[str]:
    """
    Identifies the Magpie descriptor columns in the dataframe.
    Assumes descriptors are numeric columns not named 'property_name', 'target', or 'material_id'.
    """
    exclude_cols = {'property_name', 'target', 'material_id', 'structure'}
    feature_cols = [col for col in df.columns if col not in exclude_cols and pd.api.types.is_numeric_dtype(df[col])]
    return feature_cols

def train_single_model(X: np.ndarray, y: np.ndarray, seed: int) -> Tuple[RandomForestRegressor, float]:
    """
    Trains a single Random Forest model and returns the model and MSE.
    """
    set_seed(seed)
    X_train, X_val, y_train, y_val = train_test_split(X, y, test_size=0.2, random_state=seed)
    
    model = RandomForestRegressor(
        n_estimators=100, 
        max_depth=10, 
        random_state=seed,
        n_jobs=-1
    )
    model.fit(X_train, y_train)
    
    y_pred = model.predict(X_val)
    mse = mean_squared_error(y_val, y_pred)
    return model, mse

def generate_learning_curve_for_property(
    property_name: str, 
    df_property: pd.DataFrame, 
    feature_cols: List[str]
) -> Optional[Dict[str, Any]]:
    """
    Generates a learning curve for a specific property by training on increasing subset sizes.
    
    Args:
        property_name: Name of the property.
        df_property: DataFrame containing only rows for this property.
        feature_cols: List of feature column names.
        
    Returns:
        Dict containing subset sizes and corresponding MSEs, or None if skipped.
    """
    n_samples = len(df_property)
    
    # --- T022 Implementation: Error Handling for Insufficient Data ---
    if n_samples < MIN_SAMPLES_THRESHOLD:
        logger.warning(
            f"Skipping property '{property_name}': Insufficient data points. "
            f"Found {n_samples} samples, but require at least {MIN_SAMPLES_THRESHOLD}."
        )
        # Log to a dedicated error summary or status file could be added here
        return None
    # ---------------------------------------------------------------

    results = {
        "property_name": property_name,
        "total_samples": n_samples,
        "subset_sizes": [],
        "mse_scores": [],
        "status": "success"
    }

    # Filter valid subset sizes based on available data
    valid_sizes = [size for size in SUBSET_SIZES if size <= n_samples]
    
    if not valid_sizes:
        logger.warning(
            f"Skipping property '{property_name}': No valid subset sizes available. "
            f"Max subset size {max(SUBSET_SIZES)} > {n_samples} samples."
        )
        return None

    logger.info(f"Processing property '{property_name}' with {n_samples} samples. "
                f"Valid subset sizes: {valid_sizes}")

    X = df_property[feature_cols].values
    y = df_property['target'].values

    for size in valid_sizes:
        try:
            # Sample data for this subset size
            # Using a fixed seed for reproducibility of the subset selection
            idx = np.random.RandomState(RANDOM_SEED).choice(len(X), size=size, replace=False)
            X_subset = X[idx]
            y_subset = y[idx]

            model, mse = train_single_model(X_subset, y_subset, RANDOM_SEED)
            
            results["subset_sizes"].append(size)
            results["mse_scores"].append(mse)
            
            logger.debug(f"  Subset {size}: MSE = {mse:.4f}")
            
        except Exception as e:
            logger.error(f"Error training on subset size {size} for {property_name}: {e}")
            results["status"] = "partial_failure"
            results["subset_sizes"].append(size)
            results["mse_scores"].append(None)
            continue

    return results

def main():
    """
    Main entry point for generating learning curves.
    """
    try:
        logger.info("Starting Learning Curve Generation Pipeline")
        set_seed(RANDOM_SEED)

        # Load data
        df = load_master_dataset()
        feature_cols = get_feature_columns(df)
        
        if not feature_cols:
            raise ValueError("No feature columns found in the master dataset.")

        # Group by property
        properties = df['property_name'].unique()
        logger.info(f"Found {len(properties)} distinct properties.")

        all_curves = []
        skipped_properties = []

        for prop in properties:
            df_prop = df[df['property_name'] == prop].copy()
            
            curve_result = generate_learning_curve_for_property(prop, df_prop, feature_cols)
            
            if curve_result:
                all_curves.append(curve_result)
            else:
                skipped_properties.append(prop)

        # Save results
        if all_curves:
            output_df = pd.DataFrame(all_curves)
            # Flatten lists for CSV/Parquet export if needed, or save as JSON
            # For this task, we save a structured JSON or a wide-format CSV
            output_path = get_config().data_dir / "processed" / "learning_curves.json"
            output_df.to_json(output_path, orient='records', indent=2)
            logger.info(f"Saved learning curves to {output_path}")
        else:
            logger.warning("No learning curves were generated.")

        if skipped_properties:
            logger.info(f"Skipped {len(skipped_properties)} properties due to insufficient data: {skipped_properties}")

        logger.info("Learning Curve Generation Pipeline Completed")

    except Exception as e:
        logger.critical(f"Pipeline failed: {e}")
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
