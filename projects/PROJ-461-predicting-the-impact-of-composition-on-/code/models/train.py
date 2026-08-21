import json
import logging
import os
import pickle
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
import lightgbm as lgb
from sklearn.model_selection import GroupKFold
from sklearn.metrics import mean_absolute_error, r2_score

from config import Config, load_config
from utils.logger import get_logger

logger = get_logger(__name__)


def derive_dominant_element(composition: Dict[str, float]) -> str:
    """
    Derive the dominant element from a composition dictionary.
    Returns the element symbol with the highest mass fraction.
    """
    if not composition:
        raise ValueError("Composition dictionary is empty")
    return max(composition, key=composition.get)


def load_data(config: Config) -> pd.DataFrame:
    """
    Load the processed data from the clean_data.csv file.
    """
    data_path = config.data_dir / "clean_data.csv"
    if not data_path.exists():
        raise FileNotFoundError(f"Data file not found: {data_path}")
    
    df = pd.read_csv(data_path)
    
    # Parse composition column if it's a string representation of a dict
    if 'composition' in df.columns and isinstance(df['composition'].iloc[0], str):
        df['composition'] = df['composition'].apply(lambda x: eval(x) if isinstance(x, str) else x)
    
    return df


def prepare_features_and_target(df: pd.DataFrame) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Prepare features and target for training.
    Returns X, y_residual, and groups (dominant_element).
    """
    # Feature columns (exclude composition, density, residual_density, dominant_element)
    feature_cols = [
        'mean_atomic_mass', 'mean_atomic_radius', 'electronegativity_variance',
        'atomic_radius_mismatch', 'packing_efficiency', 
        'atomic_fraction_1', 'atomic_fraction_2', 'atomic_fraction_3', 'atomic_fraction_4'
    ]
    
    # Filter to only available columns
    available_feature_cols = [col for col in feature_cols if col in df.columns]
    
    if not available_feature_cols:
        raise ValueError("No feature columns found in the dataframe")
    
    X = df[available_feature_cols].values
    y_residual = df['residual_density'].values
    
    # Derive dominant element for grouping
    df['dominant_element'] = df['composition'].apply(derive_dominant_element)
    groups = df['dominant_element'].values
    
    return X, y_residual, groups


def train_model(X: np.ndarray, y: np.ndarray, groups: np.ndarray, config: Config) -> Any:
    """
    Train a LightGBM Gradient Boosting Regressor using Group K-Fold.
    """
    logger.info("Starting model training with Group K-Fold")
    
    # Initialize Group K-Fold
    gkf = GroupKFold(n_splits=5)
    
    # Store fold metrics
    fold_maes = []
    fold_r2s = []
    
    # Prepare LightGBM dataset
    train_data = lgb.Dataset(X, label=y)
    
    # Training parameters
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
        'seed': config.seed
    }
    
    # Perform Group K-Fold cross-validation
    for fold, (train_idx, val_idx) in enumerate(gkf.split(X, y, groups)):
        logger.info(f"Training fold {fold + 1}/5")
        
        X_train, X_val = X[train_idx], X[val_idx]
        y_train, y_val = y[train_idx], y[val_idx]
        groups_train, groups_val = groups[train_idx], groups[val_idx]
        
        # Create LightGBM datasets
        train_set = lgb.Dataset(X_train, label=y_train, feature_name='auto')
        val_set = lgb.Dataset(X_val, label=y_val, reference=train_set)
        
        # Train model
        model = lgb.train(
            params,
            train_set,
            num_boost_round=1000,
            valid_sets=[val_set],
            callbacks=[lgb.early_stopping(stopping_rounds=50, verbose=False)]
        )
        
        # Predict and evaluate
        y_pred = model.predict(X_val)
        mae = mean_absolute_error(y_val, y_pred)
        r2 = r2_score(y_val, y_pred)
        
        fold_maes.append(mae)
        fold_r2s.append(r2)
        
        logger.info(f"Fold {fold + 1} - MAE: {mae:.4f}, R²: {r2:.4f}")
    
    # Calculate mean metrics
    mean_mae = np.mean(fold_maes)
    mean_r2 = np.mean(fold_r2s)
    
    logger.info(f"Cross-validation - Mean MAE: {mean_mae:.4f}, Mean R²: {mean_r2:.4f}")
    
    # Train final model on full dataset
    logger.info("Training final model on full dataset")
    final_model = lgb.train(
        params,
        train_data,
        num_boost_round=1000
    )
    
    # Log feature importance
    importance = final_model.feature_importance(importance_type='gain')
    feature_names = X.columns if hasattr(X, 'columns') else [f'feature_{i}' for i in range(len(importance))]
    
    importance_df = pd.DataFrame({
        'feature': feature_names,
        'importance': importance
    }).sort_values('importance', ascending=False)
    
    logger.info("Top 5 features by importance:")
    for _, row in importance_df.head(5).iterrows():
        logger.info(f"  {row['feature']}: {row['importance']:.2f}")
    
    return final_model, mean_mae, mean_r2


def save_model(model: Any, config: Config) -> Path:
    """
    Save the trained model to disk.
    """
    model_path = config.model_dir / "model.pkl"
    model_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(model_path, 'wb') as f:
        pickle.dump(model, f)
    
    logger.info(f"Model saved to {model_path}")
    return model_path


def main():
    """
    Main entry point for model training.
    """
    config = load_config()
    
    try:
        # Load data
        logger.info("Loading processed data")
        df = load_data(config)
        
        # Prepare features and target
        logger.info("Preparing features and target")
        X, y_residual, groups = prepare_features_and_target(df)
        
        # Train model
        logger.info("Training LightGBM model")
        model, mean_mae, mean_r2 = train_model(X, y_residual, groups, config)
        
        # Save model
        model_path = save_model(model, config)
        
        # Log final metrics
        logger.info(f"Training complete. Mean MAE: {mean_mae:.4f}, Mean R²: {mean_r2:.4f}")
        
        # Save metrics to file for downstream tasks
        metrics = {
            'model_mae': float(mean_mae),
            'model_r2': float(mean_r2),
            'model_path': str(model_path),
            'training_status': 'success'
        }
        
        metrics_path = config.report_dir / "metrics.json"
        metrics_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(metrics_path, 'w') as f:
            json.dump(metrics, f, indent=2)
        
        logger.info(f"Metrics saved to {metrics_path}")
        
    except Exception as e:
        logger.error(f"Training failed: {str(e)}", exc_info=True)
        raise


if __name__ == "__main__":
    main()