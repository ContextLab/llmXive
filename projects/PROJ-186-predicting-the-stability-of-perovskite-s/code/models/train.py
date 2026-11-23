import os
import sys
import json
import logging
import pickle
import argparse
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Dict, List, Tuple, Any, Optional

from sklearn.model_selection import train_test_split, GridSearchCV
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_squared_error
from sklearn.inspection import permutation_importance

from utils.logging_config import get_logger, log_pipeline_event
from utils.config import get_config_summary

# Configure logger
logger = get_logger(__name__)

def load_data(input_path: str) -> pd.DataFrame:
    """Load the input CSV file."""
    logger.info(f"Loading data from {input_path}")
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Input file not found: {input_path}")
    df = pd.read_csv(input_path)
    logger.info(f"Loaded {len(df)} rows with columns: {list(df.columns)}")
    return df

def inner_loop_cv_selection(df: pd.DataFrame, feature_cols: List[str], target_col: str, random_state: int = 42) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Split data into train and test sets.
    Stratified split by quantiles of target variable.
    """
    # Create quantile bins for stratification
    df['target_quantile'] = pd.qcut(df[target_col], q=5, labels=False, duplicates='drop')
    
    # Split
    train_df, test_df = train_test_split(
        df, 
        test_size=0.2, 
        random_state=random_state, 
        stratify=df['target_quantile']
    )
    
    # Drop the helper column
    train_df = train_df.drop(columns=['target_quantile'])
    test_df = test_df.drop(columns=['target_quantile'])
    
    logger.info(f"Train size: {len(train_df)}, Test size: {len(test_df)}")
    return train_df, test_df

def train_model_with_grid_search(train_df: pd.DataFrame, feature_cols: List[str], target_col: str) -> Tuple[RandomForestRegressor, Dict[str, Any]]:
    """
    Train RandomForest with GridSearchCV.
    Grid: max_depth {10, 15, 20}, min_samples_leaf {1, 2, 4}
    """
    X = train_df[feature_cols]
    y = train_df[target_col]

    rf = RandomForestRegressor(random_state=42, n_jobs=-1)

    param_grid = {
        'max_depth': [10, 15, 20],
        'min_samples_leaf': [1, 2, 4]
    }

    logger.info("Starting GridSearchCV...")
    grid_search = GridSearchCV(
        estimator=rf, 
        param_grid=param_grid, 
        cv=5, 
        scoring='neg_mean_squared_error',
        n_jobs=-1,
        verbose=1
    )

    grid_search.fit(X, y)
    
    best_params = grid_search.best_params_
    best_model = grid_search.best_estimator_
    
    logger.info(f"Best parameters: {best_params}")
    logger.info(f"Best CV score (MSE): {-grid_search.best_score_:.4f}")
    
    return best_model, best_params

def evaluate_model(model: RandomForestRegressor, test_df: pd.DataFrame, feature_cols: List[str], target_col: str) -> float:
    """Evaluate model on test set and return RMSE."""
    X_test = test_df[feature_cols]
    y_test = test_df[target_col]
    
    y_pred = model.predict(X_test)
    mse = mean_squared_error(y_test, y_pred)
    rmse = np.sqrt(mse)
    
    logger.info(f"Test RMSE: {rmse:.4f} eV/atom")
    return rmse

def perform_permutation_importance(model: RandomForestRegressor, test_df: pd.DataFrame, feature_cols: List[str], target_col: str) -> Dict[str, float]:
    """Calculate permutation importance."""
    X_test = test_df[feature_cols]
    y_test = test_df[target_col]
    
    result = permutation_importance(model, X_test, y_test, n_repeats=10, random_state=42, n_jobs=-1)
    
    importance_dict = {
        feature: float(result.importances_mean[i]) 
        for i, feature in enumerate(feature_cols)
    }
    
    logger.info("Permutation importance calculated.")
    return importance_dict

def save_artifacts(model: RandomForestRegressor, best_params: Dict, rmse: float, importance: Dict, output_dir: str, dft_functional: str = "PBE"):
    """Save model, metrics, and feature importance."""
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    model_path = output_path / "model.pkl"
    metrics_path = output_path / "metrics.json"
    importance_path = output_path / "permutation_importance.json"
    
    # Save model
    with open(model_path, 'wb') as f:
        pickle.dump(model, f)
    logger.info(f"Model saved to {model_path}")
    
    # Save metrics
    metrics = {
        "test_rmse": float(rmse),
        "best_params": best_params,
        "dft_functional": dft_functional
    }
    with open(metrics_path, 'w') as f:
        json.dump(metrics, f, indent=2)
    logger.info(f"Metrics saved to {metrics_path}")
    
    # Save permutation importance
    with open(importance_path, 'w') as f:
        json.dump(importance, f, indent=2)
    logger.info(f"Permutation importance saved to {importance_path}")

def main():
    parser = argparse.ArgumentParser(description="Train model for perovskite stability prediction")
    parser.add_argument("--input", type=str, default="data/processed/features.csv", help="Path to input CSV")
    parser.add_argument("--output", type=str, default="results", help="Output directory for artifacts")
    args = parser.parse_args()
    
    log_pipeline_event("Training Pipeline Started")
    
    # Load data
    df = load_data(args.input)
    
    # Define feature and target columns
    feature_cols = [
        "tolerance_factor", 
        "octahedral_factor", 
        "ionic_radius_mismatch", 
        "electronegativity_diff"
    ]
    target_col = "decomposition_energy"
    
    # Validate columns exist
    missing_cols = [c for c in feature_cols + [target_col] if c not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing required columns: {missing_cols}")
    
    # Split data
    train_df, test_df = inner_loop_cv_selection(df, feature_cols, target_col)
    
    # Train model with grid search
    model, best_params = train_model_with_grid_search(train_df, feature_cols, target_col)
    
    # Evaluate
    rmse = evaluate_model(model, test_df, feature_cols, target_col)
    
    # Permutation importance
    importance = perform_permutation_importance(model, test_df, feature_cols, target_col)
    
    # Save artifacts
    save_artifacts(model, best_params, rmse, importance, args.output)
    
    log_pipeline_event("Training Pipeline Completed Successfully")
    print(f"Pipeline complete. RMSE: {rmse:.4f} eV/atom")

if __name__ == "__main__":
    main()