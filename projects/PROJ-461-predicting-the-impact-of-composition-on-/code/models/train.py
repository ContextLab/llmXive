import json
import logging
import os
import pickle
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import lightgbm as lgb
import numpy as np
import pandas as pd
from sklearn.metrics import mean_absolute_error, r2_score
from sklearn.model_selection import GroupKFold

from config import Config, load_config
from utils.logger import get_logger

logger = get_logger(__name__)


def derive_dominant_element(composition: Dict[str, float]) -> str:
    """
    Derive the dominant element from a composition dictionary.
    The dominant element is the one with the highest mass fraction.
    
    Args:
        composition: Dictionary mapping element symbols to mass fractions.
        
    Returns:
        The element symbol with the highest mass fraction.
    """
    if not composition:
        return "Unknown"
    return max(composition, key=composition.get)


def load_data(config: Config) -> pd.DataFrame:
    """
    Load the processed data from the validation log.
    
    Args:
        config: Configuration object containing data paths.
        
    Returns:
        DataFrame containing the processed data.
    """
    validation_log_path = config.data_dir / "validation_log.json"
    if not validation_log_path.exists():
        raise FileNotFoundError(f"Validation log not found at {validation_log_path}")
    
    with open(validation_log_path, 'r') as f:
        validation_log = json.load(f)
    
    data_path = Path(validation_log["data_path"])
    if not data_path.exists():
        raise FileNotFoundError(f"Data file not found at {data_path}")
    
    logger.info(f"Loading data from {data_path}")
    return pd.read_csv(data_path)


def prepare_features_and_target(df: pd.DataFrame) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Prepare features and target for model training.
    
    Features: Compositional descriptors (mean_atomic_mass, mean_atomic_radius, 
              electronegativity_variance, atomic_radius_mismatch, packing_efficiency)
    Target: Residual density (ρ_residual)
    
    Args:
        df: DataFrame with compositional descriptors and ρ_residual column.
        
    Returns:
        Tuple of (X, y, groups) where:
            X: Feature matrix
            y: Target vector (ρ_residual)
            groups: Grouping vector (dominant_element) for GroupKFold
    """
    feature_cols = [
        "mean_atomic_mass",
        "mean_atomic_radius",
        "electronegativity_variance",
        "atomic_radius_mismatch",
        "packing_efficiency"
    ]
    
    # Check if all required columns exist
    missing_cols = [col for col in feature_cols if col not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing required feature columns: {missing_cols}")
    
    if "ρ_residual" not in df.columns:
        raise ValueError("Missing target column 'ρ_residual'")
    
    if "dominant_element" not in df.columns:
        # Derive dominant element if not present
        df["dominant_element"] = df["composition"].apply(derive_dominant_element)
    
    X = df[feature_cols].values
    y = df["ρ_residual"].values
    groups = df["dominant_element"].values
    
    return X, y, groups


def train_model(X: np.ndarray, y: np.ndarray, groups: np.ndarray, config: Config) -> Tuple[Any, Dict[str, float]]:
    """
    Train a LightGBM Gradient Boosting Regressor using Group K-Fold cross-validation.
    
    Args:
        X: Feature matrix
        y: Target vector
        groups: Grouping vector for GroupKFold
        config: Configuration object
        
    Returns:
        Tuple of (trained_model, metrics_dict) where metrics_dict contains:
            - 'mae': Mean Absolute Error on test set
            - 'r2': R² score on test set
    """
    # Initialize Group K-Fold
    gkf = GroupKFold(n_splits=5)
    
    # Store predictions and actuals for final evaluation
    all_predictions = []
    all_actuals = []
    oof_predictions = np.zeros(len(y))
    
    # LightGBM parameters
    params = {
        'objective': 'regression',
        'metric': 'mae',
        'boosting_type': 'gbdt',
        'num_leaves': 31,
        'learning_rate': 0.05,
        'feature_fraction': 0.9,
        'bagging_fraction': 0.8,
        'bagging_freq': 5,
        'verbose': -1,
        'seed': config.seed,
        'n_jobs': 1  # CPU-only as required
    }
    
    logger.info("Starting Group K-Fold training with LightGBM...")
    
    fold_metrics = []
    
    for fold_idx, (train_idx, val_idx) in enumerate(gkf.split(X, y, groups)):
        logger.info(f"Training fold {fold_idx + 1}/5")
        
        X_train, X_val = X[train_idx], X[val_idx]
        y_train, y_val = y[train_idx], y[val_idx]
        groups_train = groups[train_idx]
        
        # Create LightGBM datasets
        train_data = lgb.Dataset(X_train, label=y_train, feature_name='auto')
        val_data = lgb.Dataset(X_val, label=y_val, reference=train_data)
        
        # Train model
        model = lgb.train(
            params,
            train_data,
            num_boost_round=1000,
            valid_sets=[val_data],
            callbacks=[lgb.early_stopping(stopping_rounds=50, verbose=False)]
        )
        
        # Predict on validation set
        val_pred = model.predict(X_val)
        oof_predictions[val_idx] = val_pred
        
        # Calculate fold metrics
        fold_mae = mean_absolute_error(y_val, val_pred)
        fold_r2 = r2_score(y_val, val_pred)
        fold_metrics.append({'mae': fold_mae, 'r2': fold_r2})
        logger.info(f"Fold {fold_idx + 1} - MAE: {fold_mae:.4f}, R²: {fold_r2:.4f}")
    
    # Calculate overall metrics using out-of-fold predictions
    overall_mae = mean_absolute_error(y, oof_predictions)
    overall_r2 = r2_score(y, oof_predictions)
    
    metrics = {
        'mae': float(overall_mae),
        'r2': float(overall_r2),
        'fold_metrics': fold_metrics
    }
    
    # Retrain on full data for final model
    logger.info("Retraining on full dataset for final model...")
    full_train_data = lgb.Dataset(X, label=y, feature_name='auto')
    final_model = lgb.train(
        params,
        full_train_data,
        num_boost_round=1000
    )
    
    return final_model, metrics


def save_model(model: Any, model_path: Path) -> None:
    """
    Save the trained model to disk.
    
    Args:
        model: Trained LightGBM model
        model_path: Path to save the model
    """
    model_path.parent.mkdir(parents=True, exist_ok=True)
    with open(model_path, 'wb') as f:
        pickle.dump(model, f)
    logger.info(f"Model saved to {model_path}")


def save_residuals(df: pd.DataFrame, predictions: np.ndarray, model_path: Path, residuals_path: Path) -> None:
    """
    Save test set residuals to CSV for statistical testing.
    
    Args:
        df: Original DataFrame with samples
        predictions: Model predictions
        model_path: Path to the saved model (for reference)
        residuals_path: Path to save the residuals CSV
    """
    residuals_df = df.copy()
    residuals_df['sample_id'] = range(len(residuals_df))
    residuals_df['model_residual'] = predictions - residuals_df['ρ_actual']
    residuals_df['lmr_residual'] = residuals_df['ρ_actual'] - residuals_df['ρ_baseline']
    
    residuals_path.parent.mkdir(parents=True, exist_ok=True)
    residuals_df.to_csv(residuals_path, index=False)
    logger.info(f"Residuals saved to {residuals_path}")


def main() -> None:
    """
    Main entry point for model training.
    """
    config = load_config()
    
    try:
        # Load data
        df = load_data(config)
        
        # Prepare features and target
        X, y, groups = prepare_features_and_target(df)
        
        # Train model
        model, metrics = train_model(X, y, groups, config)
        
        # Save model
        model_path = config.model_dir / "model.pkl"
        save_model(model, model_path)
        
        # Generate predictions for residuals file
        predictions = model.predict(X)
        
        # Save residuals
        residuals_path = config.data_dir / "test_residuals.csv"
        save_residuals(df, predictions, model_path, residuals_path)
        
        # Log metrics
        logger.info(f"Training complete. MAE: {metrics['mae']:.4f}, R²: {metrics['r2']:.4f}")
        
        # Save metrics to reports/metrics.json (will be finalized by T026)
        metrics_path = config.report_dir / "training_metrics_temp.json"
        with open(metrics_path, 'w') as f:
            json.dump(metrics, f, indent=2)
        
    except Exception as e:
        logger.error(f"Model training failed: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    main()