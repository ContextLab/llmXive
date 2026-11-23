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
from utils.runtime_estimator import estimate_total_runtime, calculate_grid_search_size
from logging_config import get_logger

# Configure logging
logger = get_logger(__name__)

def load_aligned_dataset() -> pd.DataFrame:
    """Load the preprocessed aligned dataset."""
    data_path = get_data_path()
    file_path = data_path / "processed" / "aligned_dataset.csv"
    if not file_path.exists():
        raise FileNotFoundError(f"Aligned dataset not found at {file_path}")
    df = pd.read_csv(file_path)
    logger.info(f"Loaded aligned dataset with shape {df.shape}")
    return df

def get_feature_columns(df: pd.DataFrame) -> List[str]:
    """Identify feature columns (exclude targets and metadata)."""
    exclude_cols = ['composition', 'surface_facet', 'energy_change', 'd_band_center', 'adsorption_energy', 'exclude_from_training']
    feature_cols = [col for col in df.columns if col not in exclude_cols]
    return feature_cols

def stratified_split(df: pd.DataFrame, test_size: float = 0.2, random_state: int = 42) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """Split data into train and test sets."""
    # Use energy_change binning for stratification if possible, otherwise random split
    try:
        df['target_bin'] = pd.qcut(df['energy_change'], q=10, duplicates='drop')
        train_df, test_df = train_test_split(
            df, test_size=test_size, stratify=df['target_bin'], random_state=random_state
        )
        train_df = train_df.drop(columns=['target_bin'])
        test_df = test_df.drop(columns=['target_bin'])
    except ValueError:
        logger.warning("Stratification failed (insufficient bins), using random split.")
        train_df, test_df = train_test_split(df, test_size=test_size, random_state=random_state)
    
    logger.info(f"Train size: {len(train_df)}, Test size: {len(test_df)}")
    return train_df, test_df

def train_linear_baseline(train_df: pd.DataFrame, test_df: pd.DataFrame, feature_cols: List[str]) -> Tuple[LinearRegression, float, float]:
    """Train a linear baseline model."""
    X_train = train_df[feature_cols]
    y_train = train_df['energy_change']
    X_test = test_df[feature_cols]
    y_test = test_df['energy_change']

    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)

    model = LinearRegression()
    model.fit(X_train_scaled, y_train)

    y_pred = model.predict(X_test_scaled)
    r2 = r2_score(y_test, y_pred)
    mae = mean_absolute_error(y_test, y_pred)

    logger.info(f"Linear Baseline - R2: {r2:.4f}, MAE: {mae:.4f}")
    return model, r2, mae

def train_xgboost_nested_cv(
    train_df: pd.DataFrame, 
    feature_cols: List[str], 
    max_n_estimators: int = 200
) -> Tuple[xgb.XGBRegressor, Dict[str, Any], float, float]:
    """Train XGBoost with nested cross-validation."""
    X = train_df[feature_cols]
    y = train_df['energy_change']

    # Handle missing values if any
    X = X.fillna(0)

    # Define grid search space
    # Adjust max_depth based on data size if needed, keeping it simple for now
    param_grid = {
        'max_depth': [3, 6, 9],
        'learning_rate': [0.01, 0.1, 0.2],
        'n_estimators': [50, 100, max_n_estimators] # Will be capped by T048 logic
    }

    # Inner CV for grid search
    inner_cv = StratifiedKFold(n_splits=3, shuffle=True, random_state=42)
    # Create dummy bins for inner CV stratification if y is continuous
    y_bins = pd.qcut(y, q=3, duplicates='drop')

    grid_search = GridSearchCV(
        xgb.XGBRegressor(random_state=42, verbosity=0),
        param_grid,
        cv=inner_cv,
        scoring='neg_mean_absolute_error',
        n_jobs=-1
    )

    logger.info("Starting nested CV for XGBoost...")
    grid_search.fit(X, y)

    best_model = grid_search.best_estimator_
    best_params = grid_search.best_params_

    # Outer CV for evaluation (5-fold)
    outer_cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    y_bins_outer = pd.qcut(y, q=5, duplicates='drop')
    
    r2_scores = []
    mae_scores = []

    for train_idx, test_idx in outer_cv.split(X, y_bins_outer):
        X_tr, X_te = X.iloc[train_idx], X.iloc[test_idx]
        y_tr, y_te = y.iloc[train_idx], y.iloc[test_idx]
        
        # Retrain on outer fold training set with best params
        fold_model = xgb.XGBRegressor(**best_params, random_state=42, verbosity=0)
        fold_model.fit(X_tr, y_tr)
        
        y_pred = fold_model.predict(X_te)
        r2_scores.append(r2_score(y_te, y_pred))
        mae_scores.append(mean_absolute_error(y_te, y_pred))

    mean_r2 = np.mean(r2_scores)
    mean_mae = np.mean(mae_scores)

    logger.info(f"XGBoost Nested CV - Mean R2: {mean_r2:.4f}, Mean MAE: {mean_mae:.4f}")
    logger.info(f"Best Params: {best_params}")

    return best_model, best_params, mean_r2, mean_mae

def save_split_metadata(train_df: pd.DataFrame, test_df: pd.DataFrame, output_path: Path):
    """Save metadata about the train/test split."""
    metadata = {
        "train_size": len(train_df),
        "test_size": len(test_df),
        "features": list(train_df.columns)
    }
    with open(output_path, 'w') as f:
        json.dump(metadata, f, indent=2)
    logger.info(f"Saved split metadata to {output_path}")

def save_model(model: xgb.XGBRegressor, params: Dict[str, Any], output_path: Path):
    """Save the best XGBoost model."""
    model.save_model(str(output_path))
    # Save params separately for clarity
    params_path = output_path.with_suffix('.json')
    with open(params_path, 'w') as f:
        json.dump(params, f, indent=2)
    logger.info(f"Saved XGBoost model to {output_path}")

def main():
    project_root = get_project_root()
    output_path = get_output_path()
    
    # --- T048: Integrate Runtime Estimator ---
    runtime_projection_path = output_path / "runtime_projection.json"
    max_n_estimators = 200  # Default max
    
    if runtime_projection_path.exists():
        logger.info(f"Reading runtime projection from {runtime_projection_path}")
        with open(runtime_projection_path, 'r') as f:
            projection_data = json.load(f)
        
        projected_hours = projection_data.get('projected_hours', 0)
        logger.info(f"Projected runtime: {projected_hours:.2f} hours")
        
        if projected_hours > 4.0:
            logger.warning("Projected runtime exceeds 4 hours. Reducing grid search range for n_estimators.")
            # Cap max n_estimators to reduce search space
            # Task T048 says "cap max at a defined threshold". 
            # We reduce the max value in the grid search to 50 to significantly cut time.
            max_n_estimators = 50
            logger.info(f"Adjusted max_n_estimators to {max_n_estimators} for grid search.")
        else:
            logger.info("Projected runtime is within limits. Using full grid search range.")
    else:
        logger.warning(f"Runtime projection file not found at {runtime_projection_path}. Proceeding with default max_n_estimators={max_n_estimators}.")
    
    # --- End T048 ---

    # Load data
    df = load_aligned_dataset()
    feature_cols = get_feature_columns(df)
    
    # Split data
    train_df, test_df = stratified_split(df)
    
    # Save split metadata
    save_split_metadata(train_df, test_df, output_path / "split_metadata.json")
    
    # Train Linear Baseline
    linear_model, linear_r2, linear_mae = train_linear_baseline(train_df, test_df, feature_cols)
    
    # Train XGBoost with Nested CV (using adjusted max_n_estimators)
    xgb_model, xgb_params, xgb_r2, xgb_mae = train_xgboost_nested_cv(
        train_df, feature_cols, max_n_estimators=max_n_estimators
    )
    
    # Save XGBoost model
    model_save_path = project_root / "code" / "models" / "best_xgboost.json"
    save_model(xgb_model, xgb_params, model_save_path)
    
    logger.info("Training phase completed successfully.")
    logger.info(f"Linear Baseline: R2={linear_r2:.4f}, MAE={linear_mae:.4f}")
    logger.info(f"XGBoost Model: R2={xgb_r2:.4f}, MAE={xgb_mae:.4f}")

if __name__ == "__main__":
    main()