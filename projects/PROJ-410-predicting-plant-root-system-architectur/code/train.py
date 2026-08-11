"""
Model Training Module for Plant Root Architecture Prediction.

This module implements the training loops for various models (Linear, RF, GB)
per nutrient condition as required by User Story 2.

It is created here to satisfy the dependency of the integration test (T026)
and to provide the actual implementation for future tasks (T027-T031).
"""
import os
import sys
import logging
import argparse
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
import pandas as pd
import numpy as np
from sklearn.linear_model import Ridge, Lasso, ElasticNet
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.model_selection import cross_val_score, KFold
from sklearn.metrics import r2_score, mean_absolute_error
import json

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "code"))

from config import ensure_directories

logger = logging.getLogger(__name__)

# Default hyperparameters
DEFAULT_PARAMS = {
    "Linear": {"alpha": 1.0},
    "Lasso": {"alpha": 0.1},
    "RandomForest": {"n_estimators": 100, "max_depth": 10, "random_state": 42},
    "GradientBoosting": {"n_estimators": 100, "max_depth": 5, "random_state": 42}
}

def load_split_data(split_name: str, data_dir: Path) -> pd.DataFrame:
    """Load a specific split (train, val, test) from parquet."""
    path = data_dir / f"{split_name}.parquet"
    if not path.exists():
        raise FileNotFoundError(f"Split data not found at {path}")
    return pd.read_parquet(path)

def train_model(
    model_type: str,
    X_train: pd.DataFrame,
    y_train: pd.Series,
    params: Optional[Dict[str, Any]] = None
) -> Any:
    """
    Initialize and train a model based on type.
    
    Args:
        model_type: One of 'Linear', 'Lasso', 'RandomForest', 'GradientBoosting'
        X_train: Training features
        y_train: Training target
        params: Hyperparameters to override defaults
    
    Returns:
        Trained model instance
    """
    if params is None:
        params = {}
    
    default_params = DEFAULT_PARAMS.get(model_type, {})
    default_params.update(params)
    
    if model_type == "Linear":
        model = Ridge(**default_params)
    elif model_type == "Lasso":
        model = Lasso(**default_params)
    elif model_type == "RandomForest":
        model = RandomForestRegressor(**default_params)
    elif model_type == "GradientBoosting":
        model = GradientBoostingRegressor(**default_params)
    else:
        raise ValueError(f"Unknown model type: {model_type}")
    
    model.fit(X_train, y_train)
    return model

def evaluate_model(
    model: Any,
    X_val: pd.DataFrame,
    y_val: pd.Series,
    cv_folds: int = 3
) -> Dict[str, float]:
    """
    Evaluate model on validation set and perform cross-validation.
    
    Returns:
        Dict with 'val_r2', 'val_mae', 'cv_r2_mean', 'cv_r2_std'
    """
    # Validation metrics
    y_pred = model.predict(X_val)
    val_r2 = float(r2_score(y_val, y_pred))
    val_mae = float(mean_absolute_error(y_val, y_pred))
    
    # Cross-validation
    try:
        kf = KFold(n_splits=cv_folds, shuffle=True, random_state=42)
        cv_scores = cross_val_score(model, X_train, y_train, cv=kf, scoring='r2')
        cv_mean = float(cv_scores.mean())
        cv_std = float(cv_scores.std())
    except Exception as e:
        logger.warning(f"Cross-validation failed: {e}")
        cv_mean = val_r2
        cv_std = 0.0
    
    return {
        "val_r2": val_r2,
        "val_mae": val_mae,
        "cv_r2_mean": cv_mean,
        "cv_r2_std": cv_std
    }

def run_training_loop(
    data_dir: Path,
    output_dir: Path,
    model_types: List[str] = None,
    conditions: List[str] = None
) -> List[Dict[str, Any]]:
    """
    Main training loop per nutrient condition.
    
    Loads train/val splits, iterates over conditions, trains models,
    and collects metrics.
    """
    if model_types is None:
        model_types = ["Linear", "RandomForest", "GradientBoosting"]
    
    ensure_directories(output_dir)
    
    # Load data
    try:
        train_df = load_split_data("train", data_dir)
        val_df = load_split_data("val", data_dir)
    except FileNotFoundError as e:
        logger.error(str(e))
        raise
    
    if conditions is None:
        conditions = train_df["nutrient_condition"].unique().tolist()
    
    all_results = []
    
    for condition in conditions:
        logger.info(f"Processing condition: {condition}")
        
        # Filter data
        train_cond = train_df[train_df["nutrient_condition"] == condition]
        val_cond = val_df[val_df["nutrient_condition"] == condition]
        
        if train_cond.empty or val_cond.empty:
            logger.warning(f"Skipping {condition} due to empty data")
            continue
        
        # Prepare features and target
        # Assuming phenotype_value is the target
        target_col = "phenotype_value"
        feature_cols = [c for c in train_cond.columns if c not in ["accession_id", "nutrient_condition", target_col]]
        
        if not feature_cols:
            logger.warning(f"No features found for {condition}")
            continue
        
        X_train = train_cond[feature_cols].fillna(0)
        y_train = train_cond[target_col]
        X_val = val_cond[feature_cols].fillna(0)
        y_val = val_cond[target_col]
        
        for model_type in model_types:
            logger.info(f"  Training {model_type}...")
            
            try:
                model = train_model(model_type, X_train, y_train)
                metrics = evaluate_model(model, X_val, y_val)
                
                result = {
                    "condition": condition,
                    "model": model_type,
                    **metrics
                }
                all_results.append(result)
                logger.info(f"    Val R2: {metrics['val_r2']:.4f}, CV R2: {metrics['cv_r2_mean']:.4f}")
            except Exception as e:
                logger.error(f"Failed to train {model_type} for {condition}: {e}")
                continue
    
    return all_results

def save_metrics(results: List[Dict[str, Any]], output_path: Path):
    """Save training metrics to CSV."""
    if not results:
        logger.warning("No results to save")
        return
    
    df = pd.DataFrame(results)
    df.to_csv(output_path, index=False)
    logger.info(f"Saved metrics to {output_path}")

def main():
    parser = argparse.ArgumentParser(description="Train models per nutrient condition")
    parser.add_argument("--data_dir", type=str, default=str(PROJECT_ROOT / "data" / "processed"))
    parser.add_argument("--output_dir", type=str, default=str(PROJECT_ROOT / "data" / "processed"))
    parser.add_argument("--models", type=str, nargs="+", default=None, help="Model types to train")
    
    args = parser.parse_args()
    
    data_dir = Path(args.data_dir)
    output_dir = Path(args.output_dir)
    
    results = run_training_loop(data_dir, output_dir, model_types=args.models)
    
    output_file = output_dir / "model_metrics.csv"
    save_metrics(results, output_file)
    
    # Also save a JSON summary
    json_path = output_dir / "training_summary.json"
    with open(json_path, 'w') as f:
        json.dump(results, f, indent=2)
    
    return results

if __name__ == "__main__":
    main()