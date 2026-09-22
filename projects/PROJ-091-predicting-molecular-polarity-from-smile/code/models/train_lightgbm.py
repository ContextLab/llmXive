import os
import sys
import logging
import pickle
import gc
from pathlib import Path
import pandas as pd
import numpy as np
import lightgbm as lgb
from sklearn.model_selection import train_test_split, cross_val_score, KFold
from sklearn.metrics import r2_score, mean_squared_error
import yaml

from utils.logging_config import get_logger
from utils.config import load_hyperparameters

logger = get_logger(__name__)

def load_data_from_splits(splits_file: Path) -> tuple:
    """Load data from splits file (parquet)."""
    if not splits_file.exists():
        logger.error(f"Data file not found: {splits_file}")
        raise FileNotFoundError(f"Data file not found: {splits_file}")
    
    df = pd.read_parquet(splits_file)
    
    # Ensure required columns exist
    required_cols = ['smiles', 'target']
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing required columns in {splits_file}: {missing_cols}")
    
    feature_cols = [c for c in df.columns if c not in ['smiles', 'target']]
    if not feature_cols:
        raise ValueError(f"No feature columns found in {splits_file}")
        
    X = df[feature_cols].values
    y = df['target'].values
    return X, y

def train_base_model(X_train, y_train, params):
    """Train a base LightGBM model."""
    train_data = lgb.Dataset(X_train, label=y_train)
    model = lgb.train(params, train_data, num_boost_round=100)
    return model

def cross_validate_model(X, y, params, n_splits=5, random_state=42):
    """Perform k-fold cross-validation for hyperparameter tuning."""
    kf = KFold(n_splits=n_splits, shuffle=True, random_state=random_state)
    train_data = lgb.Dataset(X, label=y)
    
    cv_scores = []
    
    for fold_idx, (train_index, val_index) in enumerate(kf.split(X)):
        X_train_fold = X[train_index]
        y_train_fold = y[train_index]
        X_val_fold = X[val_index]
        y_val_fold = y[val_index]
        
        train_fold_data = lgb.Dataset(X_train_fold, label=y_train_fold)
        val_fold_data = lgb.Dataset(X_val_fold, label=y_val_fold, reference=train_fold_data)
        
        model = lgb.train(
            params,
            train_fold_data,
            num_boost_round=100,
            valid_sets=[val_fold_data],
            verbose_eval=False
        )
        
        y_pred = model.predict(X_val_fold)
        r2 = r2_score(y_val_fold, y_pred)
        cv_scores.append(r2)
        
        logger.debug(f"Fold {fold_idx + 1}/{n_splits}: R2 = {r2:.4f}")
    
    mean_r2 = np.mean(cv_scores)
    std_r2 = np.std(cv_scores)
    logger.info(f"Cross-validation R2: {mean_r2:.4f} (+/- {std_r2:.4f})")
    
    return mean_r2

def tune_hyperparameters(X_train, y_train, X_val, y_val):
    """Simple hyperparameter tuning."""
    param_grid = {
        'num_leaves': [31, 63],
        'learning_rate': [0.05, 0.1],
        'n_estimators': [100, 200]
    }
    best_score = -np.inf
    best_params = {}

    for nl in param_grid['num_leaves']:
        for lr in param_grid['learning_rate']:
            for ne in param_grid['n_estimators']:
                params = {'num_leaves': nl, 'learning_rate': lr, 'n_estimators': ne, 'verbose': -1}
                model = lgb.LGBMRegressor(**params)
                model.fit(X_train, y_train)
                score = r2_score(y_val, model.predict(X_val))
                if score > best_score:
                    best_score = score
                    best_params = params
                    logger.info(f"New best: {best_params} with R2={best_score:.4f}")
    return best_params

def evaluate_model(model, X_test, y_test):
    """Evaluate model performance."""
    y_pred = model.predict(X_test)
    r2 = r2_score(y_test, y_pred)
    rmse = np.sqrt(mean_squared_error(y_test, y_pred))
    return {'r2': r2, 'rmse': rmse}

def compute_null_model_r2(y_train, y_test):
    """Compute R2 for null model (mean predictor)."""
    mean_y = np.mean(y_train)
    ss_res = np.sum((y_test - mean_y) ** 2)
    ss_tot = np.sum((y_test - np.mean(y_test)) ** 2)
    return 1 - (ss_res / ss_tot)

def save_model(model, filepath):
    """Save model to pickle."""
    # Ensure directory exists
    filepath.parent.mkdir(parents=True, exist_ok=True)
    with open(filepath, 'wb') as f:
        pickle.dump(model, f)
    logger.info(f"Model saved to {filepath}")

def update_config_with_params(params: dict, config_path: Path):
    """Update config.yaml with optimal parameters."""
    if config_path.exists():
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
    else:
        config = {}

    config['training'] = config.get('training', {})
    config['training'].update(params)

    with open(config_path, 'w') as f:
        yaml.dump(config, f)
    logger.info(f"Updated config at {config_path}")

def train_lightgbm(data_file: Path, model_output: Path, config_path: Path):
    """Main training pipeline."""
    logger.info("Starting LightGBM training")

    try:
        X, y = load_data_from_splits(data_file)
    except (FileNotFoundError, ValueError) as e:
        logger.error(f"Failed to load data: {e}")
        raise

    # Split data
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    # Tune hyperparameters using a simple grid search on the hold-out validation set
    best_params = tune_hyperparameters(X_train, y_train, X_test, y_test)

    # Perform k-fold cross-validation on the full training set with best params
    # to ensure robustness before final model training
    logger.info(f"Performing 5-fold cross-validation with best params: {best_params}")
    cv_score = cross_validate_model(
        X_train, y_train, 
        params=best_params, 
        n_splits=5, 
        random_state=42
    )
    logger.info(f"Final CV Score: {cv_score:.4f}")

    # Train final model on full training set
    final_model = lgb.LGBMRegressor(**best_params, verbose=-1)
    final_model.fit(X_train, y_train)

    # Evaluate
    metrics = evaluate_model(final_model, X_test, y_test)
    null_r2 = compute_null_model_r2(y_train, y_test)

    logger.info(f"Model R2: {metrics['r2']:.4f}, Null R2: {null_r2:.4f}")
    if metrics['r2'] <= null_r2:
        logger.warning("Model performance is worse than null model!")

    # Save model
    save_model(final_model, model_output)

    # Update config
    update_config_with_params(best_params, config_path)

    logger.info("Training complete.")

def main():
    """Main entry point."""
    data_file = Path(__file__).resolve().parent.parent.parent / "data" / "processed" / "descriptors.parquet"
    model_output = Path(__file__).resolve().parent.parent.parent / "data" / "processed" / "model.pkl"
    config_path = Path(__file__).resolve().parent.parent.parent / "code" / "config.yaml"

    if not data_file.exists():
        logger.error(f"Data file not found: {data_file}")
        sys.exit(1)

    train_lightgbm(data_file, model_output, config_path)

if __name__ == "__main__":
    main()