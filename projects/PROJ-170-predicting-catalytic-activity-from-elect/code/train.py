import os
import sys
import json
import logging
from pathlib import Path
from typing import Tuple, List, Dict, Any, Optional

import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split, StratifiedKFold, GridSearchCV
from sklearn.linear_model import LinearRegression
from sklearn.metrics import r2_score, mean_absolute_error
from sklearn.preprocessing import StandardScaler
import xgboost as xgb

from config import get_project_root, get_data_path, get_output_path
from logging_config import setup_logging, get_logger

# Configure logging
logger = get_logger(__name__)

def load_aligned_dataset(chunksize: int = 100000) -> pd.DataFrame:
    """
    Load the aligned dataset using pandas chunking to optimize memory usage.
    
    This function reads the CSV in chunks, concatenates them, and returns
    a single DataFrame. This approach prevents memory spikes when loading
    large datasets.
    
    Args:
        chunksize: Number of rows to read at a time. Default is 100,000.
        
    Returns:
        pd.DataFrame: The complete aligned dataset.
    """
    data_path = get_data_path()
    input_file = data_path / "processed" / "aligned_dataset.csv"
    
    if not input_file.exists():
        raise FileNotFoundError(f"Aligned dataset not found at {input_file}")
    
    logger.info(f"Loading aligned dataset from {input_file} with chunking...")
    
    chunks = []
    for chunk in pd.read_csv(input_file, chunksize=chunksize):
        chunks.append(chunk)
        logger.debug(f"Loaded chunk of {len(chunk)} rows")
    
    df = pd.concat(chunks, ignore_index=True)
    logger.info(f"Successfully loaded {len(df)} rows")
    
    return df

def get_feature_columns(df: pd.DataFrame) -> List[str]:
    """
    Get the list of feature columns (excluding target and metadata).
    
    Args:
        df: The dataset DataFrame.
        
    Returns:
        List of feature column names.
    """
    target_col = "energy_change"
    metadata_cols = ["composition", "surface_facet", "adsorption_energy"]
    
    feature_cols = [col for col in df.columns 
                   if col not in metadata_cols and col != target_col]
    
    return feature_cols

def stratified_split(df: pd.DataFrame, test_size: float = 0.2, random_state: int = 42) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Split the dataset into train and test sets with stratification.
    
    Stratification is performed based on the 'composition_family' if available,
    otherwise falls back to binning the target variable.
    
    Args:
        df: The dataset DataFrame.
        test_size: Proportion of data to use for testing.
        random_state: Random seed for reproducibility.
        
    Returns:
        Tuple of (train_df, test_df).
    """
    # Determine stratification column
    if "composition_family" in df.columns:
        stratify_col = "composition_family"
    else:
        # Fallback: bin the target variable for stratification
        logger.warning("composition_family not found, using binned target for stratification")
        df["target_bin"] = pd.qcut(df["energy_change"], q=10, duplicates="drop")
        stratify_col = "target_bin"
    
    train_df, test_df = train_test_split(
        df, 
        test_size=test_size, 
        random_state=random_state, 
        stratify=df[stratify_col]
    )
    
    # Clean up temporary bin column if created
    if "target_bin" in train_df.columns:
        train_df = train_df.drop(columns=["target_bin"])
        test_df = test_df.drop(columns=["target_bin"])
    
    logger.info(f"Train set size: {len(train_df)}, Test set size: {len(test_df)}")
    return train_df, test_df

def train_linear_baseline(train_df: pd.DataFrame, test_df: pd.DataFrame) -> Tuple[LinearRegression, float, float]:
    """
    Train a linear baseline model using d_band_center and adsorption_energy.
    
    Args:
        train_df: Training dataset.
        test_df: Test dataset.
        
    Returns:
        Tuple of (model, r2_score, mae).
    """
    feature_cols = ["d_band_center", "adsorption_energy"]
    target_col = "energy_change"
    
    # Handle missing values in features
    for col in feature_cols:
        if col not in train_df.columns:
            raise ValueError(f"Feature column '{col}' not found in dataset")
    
    X_train = train_df[feature_cols].dropna()
    y_train = train_df.loc[X_train.index, target_col]
    
    X_test = test_df[feature_cols].dropna()
    y_test = test_df.loc[X_test.index, target_col]
    
    if len(X_train) == 0 or len(X_test) == 0:
        raise ValueError("No valid data after dropping NaN values")
    
    model = LinearRegression()
    model.fit(X_train, y_train)
    
    y_pred = model.predict(X_test)
    r2 = r2_score(y_test, y_pred)
    mae = mean_absolute_error(y_test, y_pred)
    
    logger.info(f"Linear Baseline - R²: {r2:.4f}, MAE: {mae:.4f}")
    return model, r2, mae

def train_xgboost_nested_cv(train_df: pd.DataFrame) -> Tuple[xgb.XGBRegressor, Dict[str, Any]]:
    """
    Train XGBoost model with nested cross-validation.
    
    Outer loop: 5-fold cross-validation
    Inner loop: Grid search for hyperparameters
    
    Args:
        train_df: Training dataset.
        
    Returns:
        Tuple of (best_model, best_params).
    """
    feature_cols = get_feature_columns(train_df)
    target_col = "energy_change"
    
    X = train_df[feature_cols].dropna()
    y = train_df.loc[X.index, target_col]
    
    if len(X) == 0:
        raise ValueError("No valid training data after dropping NaN values")
    
    # Normalize features
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    X_scaled = pd.DataFrame(X_scaled, columns=feature_cols, index=X.index)
    
    # Define parameter grid
    param_grid = {
        "max_depth": [3, 5, 7],
        "learning_rate": [0.01, 0.1],
        "n_estimators": [100, 200]
    }
    
    # Inner cross-validation for grid search
    inner_cv = StratifiedKFold(n_splits=3, shuffle=True, random_state=42)
    
    # Create XGBoost model
    xgb_model = xgb.XGBRegressor(
        random_state=42,
        verbosity=0
    )
    
    # Grid search with inner CV
    grid_search = GridSearchCV(
        xgb_model,
        param_grid,
        cv=inner_cv,
        scoring="r2",
        n_jobs=-1
    )
    
    # Fit grid search
    grid_search.fit(X_scaled, y)
    
    best_model = grid_search.best_estimator_
    best_params = grid_search.best_params_
    
    logger.info(f"Best parameters: {best_params}")
    logger.info(f"Best CV R² score: {grid_search.best_score_:.4f}")
    
    # Outer loop: 5-fold cross-validation to evaluate performance
    outer_cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    outer_scores = []
    
    for train_idx, val_idx in outer_cv.split(X_scaled):
        X_train_fold = X_scaled.iloc[train_idx]
        y_train_fold = y.iloc[train_idx]
        X_val_fold = X_scaled.iloc[val_idx]
        y_val_fold = y.iloc[val_idx]
        
        fold_model = xgb.XGBRegressor(**best_params, random_state=42, verbosity=0)
        fold_model.fit(X_train_fold, y_train_fold)
        
        y_pred_fold = fold_model.predict(X_val_fold)
        fold_r2 = r2_score(y_val_fold, y_pred_fold)
        outer_scores.append(fold_r2)
    
    avg_outer_r2 = np.mean(outer_scores)
    logger.info(f"Outer CV average R²: {avg_outer_r2:.4f}")
    
    # Retrain on full training data with best parameters
    final_model = xgb.XGBRegressor(**best_params, random_state=42, verbosity=0)
    final_model.fit(X_scaled, y)
    
    return final_model, best_params

def save_split_metadata(train_df: pd.DataFrame, test_df: pd.DataFrame) -> None:
    """
    Save metadata about the train/test split.
    
    Args:
        train_df: Training dataset.
        test_df: Test dataset.
    """
    output_path = get_output_path()
    metadata_file = output_path / "split_metadata.json"
    
    metadata = {
        "train_size": len(train_df),
        "test_size": len(test_df),
        "train_columns": list(train_df.columns),
        "test_columns": list(test_df.columns),
        "feature_columns": get_feature_columns(train_df)
    }
    
    with open(metadata_file, "w") as f:
        json.dump(metadata, f, indent=2)
    
    logger.info(f"Saved split metadata to {metadata_file}")

def save_model(model: Any, model_name: str, params: Dict[str, Any]) -> None:
    """
    Save a trained model to disk.
    
    Args:
        model: The trained model object.
        model_name: Name of the model file (without extension).
        params: Model parameters/hyperparameters.
    """
    models_path = get_project_root() / "code" / "models"
    models_path.mkdir(parents=True, exist_ok=True)
    
    model_file = models_path / f"{model_name}.json"
    
    # Convert model to dictionary for saving
    model_dict = {
        "params": params,
        "type": type(model).__name__
    }
    
    # For XGBoost, save the model directly
    if isinstance(model, xgb.XGBRegressor):
        model.save_model(str(model_file))
        logger.info(f"Saved XGBoost model to {model_file}")
    else:
        # For other models, save parameters and type
        with open(model_file, "w") as f:
            json.dump(model_dict, f, indent=2)
        logger.info(f"Saved model metadata to {model_file}")

def main():
    """Main function to run the training pipeline."""
    setup_logging()
    logger.info("Starting training pipeline...")
    
    try:
        # Load dataset with chunking
        df = load_aligned_dataset(chunksize=100000)
        
        # Split data
        train_df, test_df = stratified_split(df, test_size=0.2, random_state=42)
        
        # Save split metadata
        save_split_metadata(train_df, test_df)
        
        # Train linear baseline
        linear_model, linear_r2, linear_mae = train_linear_baseline(train_df, test_df)
        logger.info(f"Linear baseline complete: R²={linear_r2:.4f}, MAE={linear_mae:.4f}")
        
        # Train XGBoost with nested CV
        xgb_model, xgb_params = train_xgboost_nested_cv(train_df)
        logger.info("XGBoost training complete")
        
        # Save models
        save_model(linear_model, "best_linear", {"type": "LinearRegression"})
        save_model(xgb_model, "best_xgboost", xgb_params)
        
        logger.info("Training pipeline completed successfully")
        
    except Exception as e:
        logger.error(f"Training pipeline failed: {str(e)}")
        raise

if __name__ == "__main__":
    main()