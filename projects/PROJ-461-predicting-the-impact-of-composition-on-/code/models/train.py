import json
import logging
import os
import pickle
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
from sklearn.model_selection import GroupKFold
from sklearn.metrics import mean_absolute_error, r2_score
import lightgbm as lgb

from config import Config, load_config
from utils.logger import get_logger

logger = get_logger(__name__)

def derive_dominant_element(composition: Dict[str, float]) -> str:
    """
    Derive the dominant element (highest mass fraction) from a composition dict.
    
    Args:
        composition: Dictionary mapping element symbols to mass fractions.
    
    Returns:
        The symbol of the element with the highest mass fraction.
    """
    if not composition:
        raise ValueError("Empty composition provided")
    return max(composition, key=composition.get)

def load_data(config: Config) -> pd.DataFrame:
    """
    Load the preprocessed data from the clean_data.csv file.
    
    Args:
        config: Configuration object containing paths.
    
    Returns:
        DataFrame containing the clean data.
    """
    data_path = config.data_dir / "clean_data.csv"
    if not data_path.exists():
        raise FileNotFoundError(f"Data file not found: {data_path}")
    
    df = pd.read_csv(data_path)
    logger.info(f"Loaded data with {len(df)} rows from {data_path}")
    return df

def prepare_features_and_target(df: pd.DataFrame, config: Config) -> Tuple[pd.DataFrame, pd.Series, pd.Series]:
    """
    Prepare features (X), target (y_residual), and groups (dominant_element) for training.
    
    Args:
        df: Cleaned DataFrame.
        config: Configuration object.
    
    Returns:
        Tuple of (X_features, y_residual, groups)
    """
    # Determine feature columns (exclude non-feature columns)
    exclude_cols = ['composition', 'density', 'density_baseline', 'density_residual', 'dominant_element']
    feature_cols = [col for col in df.columns if col not in exclude_cols]
    
    if not feature_cols:
        raise ValueError("No feature columns found in the dataset.")
    
    X = df[feature_cols]
    
    # Target is the residual density
    if 'density_residual' not in df.columns:
        raise ValueError("Column 'density_residual' not found in data. Run feature engineering first.")
    y = df['density_residual']
    
    # Groups for Group K-Fold: dominant element
    # If 'dominant_element' column doesn't exist, derive it from composition
    if 'dominant_element' not in df.columns:
        logger.info("Deriving dominant_element column from composition...")
        # Assuming 'composition' column contains stringified dicts or JSON
        # If it's a string representation of a dict, we need to parse it
        try:
            # Try to parse as JSON if it's a string
            if isinstance(df['composition'].iloc[0], str):
                df['dominant_element'] = df['composition'].apply(
                    lambda x: derive_dominant_element(json.loads(x))
                )
            else:
                df['dominant_element'] = df['composition'].apply(
                    lambda x: derive_dominant_element(x)
                )
        except Exception as e:
            logger.error(f"Failed to parse composition column: {e}")
            raise
    else:
        logger.info("Using existing 'dominant_element' column for grouping.")
    
    groups = df['dominant_element']
    
    logger.info(f"Prepared {len(X)} samples with {len(feature_cols)} features.")
    logger.info(f"Groups distribution: {groups.value_counts().to_dict()}")
    
    return X, y, groups

def train_model(X: pd.DataFrame, y: pd.Series, groups: pd.Series, config: Config) -> lgb.Booster:
    """
    Train a LightGBM Gradient Boosting Regressor using Group K-Fold cross-validation.
    
    Args:
        X: Feature matrix.
        y: Target vector (residual density).
        groups: Group labels for Group K-Fold.
        config: Configuration object.
    
    Returns:
        Trained LightGBM Booster model.
    """
    n_splits = 5
    logger.info(f"Training with Group K-Fold (k={n_splits}) to prevent data leakage by dominant element.")
    
    gkf = GroupKFold(n_splits=n_splits)
    
    # Store metrics for each fold
    fold_maes = []
    fold_r2s = []
    
    # Prepare LightGBM datasets
    train_data = lgb.Dataset(X, label=y)
    
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
        'seed': config.seed
    }
    
    best_model = None
    
    for fold, (train_idx, val_idx) in enumerate(gkf.split(X, y, groups)):
        X_train, X_val = X.iloc[train_idx], X.iloc[val_idx]
        y_train, y_val = y.iloc[train_idx], y.iloc[val_idx]
        groups_train = groups.iloc[train_idx]
        
        # Create validation sets with group info (though LightGBM doesn't use groups in validation directly)
        train_set = lgb.Dataset(X_train, label=y_train)
        val_set = lgb.Dataset(X_val, label=y_val, reference=train_set)
        
        # Train model
        model = lgb.train(
            params,
            train_set,
            num_boost_round=1000,
            valid_sets=[val_set],
            callbacks=[lgb.early_stopping(stopping_rounds=50, verbose=False)]
        )
        
        # Evaluate
        y_pred = model.predict(X_val)
        mae = mean_absolute_error(y_val, y_pred)
        r2 = r2_score(y_val, y_pred)
        
        fold_maes.append(mae)
        fold_r2s.append(r2)
        
        logger.info(f"Fold {fold+1}/{n_splits}: MAE={mae:.4f}, R²={r2:.4f}")
    
    # Train final model on full data
    logger.info("Training final model on full dataset...")
    final_train_set = lgb.Dataset(X, label=y)
    best_model = lgb.train(
        params,
        final_train_set,
        num_boost_round=1000,
        callbacks=[lgb.early_stopping(stopping_rounds=50, verbose=False)]
    )
    
    # Log aggregate metrics
    logger.info(f"Mean CV MAE: {np.mean(fold_maes):.4f} (+/- {np.std(fold_maes):.4f})")
    logger.info(f"Mean CV R²: {np.mean(fold_r2s):.4f} (+/- {np.std(fold_r2s):.4f})")
    
    return best_model

def save_model(model: lgb.Booster, config: Config) -> Path:
    """
    Save the trained model to disk.
    
    Args:
        model: Trained LightGBM Booster.
        config: Configuration object.
    
    Returns:
        Path to the saved model file.
    """
    model_path = config.model_dir / "model.pkl"
    model_path.parent.mkdir(parents=True, exist_ok=True)
    
    # LightGBM models can be saved as text or binary
    # We'll use pickle for the Booster object as requested in the spec
    with open(model_path, 'wb') as f:
        pickle.dump(model, f)
    
    logger.info(f"Model saved to {model_path}")
    return model_path

def main():
    """Main entry point for model training."""
    config = load_config()
    
    try:
        # Load data
        df = load_data(config)
        
        # Prepare features and target
        X, y, groups = prepare_features_and_target(df, config)
        
        # Train model
        model = train_model(X, y, groups, config)
        
        # Save model
        save_model(model, config)
        
        logger.info("Model training completed successfully.")
        
    except Exception as e:
        logger.error(f"Model training failed: {e}", exc_info=True)
        raise

if __name__ == "__main__":
    main()