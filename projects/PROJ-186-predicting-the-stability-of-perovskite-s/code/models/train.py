import os
import sys
import json
import logging
import pickle
from pathlib import Path
from typing import Dict, Any, Optional, Tuple

import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import GridSearchCV, train_test_split
from sklearn.metrics import mean_squared_error, r2_score
from scipy.stats import pearsonr

# Import project utilities
from utils.logging_config import get_logger, log_pipeline_event, log_exclusion_reason
from utils.config import get_config_summary

logger = get_logger(__name__)

def load_data() -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Load preprocessed data from data/processed/features.csv and split it.
    Returns:
        X_train, X_test, y_train, y_test
    """
    logger.info("Loading preprocessed data...")
    features_path = Path("data/processed/features.csv")
    
    if not features_path.exists():
        raise FileNotFoundError(f"Features file not found at {features_path}. "
                              "Please run T018 (preprocess.py) first.")
    
    df = pd.read_csv(features_path)
    
    # Define target and feature columns
    target_col = "decomposition_energy"
    feature_cols = [
        "tolerance_factor", 
        "octahedral_factor", 
        "ionic_radius_mismatch", 
        "electronegativity_difference"
    ]
    
    # Verify columns exist
    missing_cols = [col for col in feature_cols + [target_col] if col not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing required columns in features file: {missing_cols}")
    
    # Check for nulls in target
    if df[target_col].isnull().any():
        raise ValueError(f"Target column '{target_col}' contains null values.")
    
    X = df[feature_cols]
    y = df[target_col]
    
    # Split data (80/20 stratified split)
    # Note: Since target is continuous, we bin for stratification or just use random split
    # Using random split with fixed seed for reproducibility
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )
    
    logger.info(f"Data loaded: Train set size={len(X_train)}, Test set size={len(X_test)}")
    return X_train, X_test, y_train, y_test

def inner_loop_cv_selection(X_train: pd.DataFrame, y_train: pd.Series) -> Dict[str, Any]:
    """
    Perform 5-fold CV grid search to select best hyperparameters.
    Returns dict with best_params and the GridSearchCV object.
    """
    logger.info("Starting inner-loop cross-validation...")
    
    param_grid = {
        'max_depth': [10, 15, 20],
        'min_samples_leaf': [1, 2, 4]
    }
    
    rf = RandomForestRegressor(random_state=42, n_jobs=-1)
    
    grid_search = GridSearchCV(
        estimator=rf,
        param_grid=param_grid,
        cv=5,
        scoring='neg_mean_squared_error',
        n_jobs=-1,
        verbose=1
    )
    
    grid_search.fit(X_train, y_train)
    
    best_params = grid_search.best_params_
    best_cv_score = -grid_search.best_score_  # Convert neg_mse to mse
    
    logger.info(f"Inner loop CV complete. Best params: {best_params}")
    logger.info(f"Best CV RMSE: {np.sqrt(best_cv_score):.4f} eV/atom")
    
    return {
        'best_params': best_params,
        'grid_search': grid_search,
        'best_cv_rmse': np.sqrt(best_cv_score)
    }

def train_model(X_train: pd.DataFrame, y_train: pd.Series, best_params: Dict[str, Any]) -> RandomForestRegressor:
    """
    Re-train the model on the full training set using best hyperparameters.
    """
    logger.info("Re-training model on full training set with best parameters...")
    
    model = RandomForestRegressor(
        random_state=42,
        n_jobs=-1,
        **best_params
    )
    
    model.fit(X_train, y_train)
    logger.info("Model training complete.")
    
    return model

def evaluate_model(model: RandomForestRegressor, X_test: pd.DataFrame, y_test: pd.Series) -> Dict[str, float]:
    """
    Evaluate model on the held-out test set.
    Returns metrics dictionary.
    """
    logger.info("Evaluating model on test set...")
    
    y_pred = model.predict(X_test)
    
    rmse = np.sqrt(mean_squared_error(y_test, y_pred))
    r2 = r2_score(y_test, y_pred)
    mae = mean_squared_error(y_test, y_pred, squared=False)
    corr, _ = pearsonr(y_test, y_pred)
    
    metrics = {
        'test_rmse': float(rmse),
        'test_mae': float(mae),
        'test_r2': float(r2),
        'test_pearson_corr': float(corr),
        'test_samples': len(y_test)
    }
    
    logger.info(f"Test RMSE: {rmse:.4f} eV/atom")
    logger.info(f"Test MAE: {mae:.4f} eV/atom")
    logger.info(f"Test R2: {r2:.4f}")
    logger.info(f"Test Pearson Correlation: {corr:.4f}")
    
    # Low confidence flag
    if rmse > 0.15:
        logger.warning(f"Low confidence flag triggered: RMSE ({rmse:.4f}) > 0.15 eV/atom")
        metrics['low_confidence_flag'] = True
    else:
        metrics['low_confidence_flag'] = False
    
    return metrics

def save_artifacts(model: RandomForestRegressor, metrics: Dict[str, Any], best_params: Dict[str, Any]) -> None:
    """
    Save trained model to results/model.pkl and metrics to results/metrics.json.
    """
    logger.info("Saving model artifacts...")
    
    results_dir = Path("results")
    results_dir.mkdir(exist_ok=True)
    
    # Save model
    model_path = results_dir / "model.pkl"
    with open(model_path, 'wb') as f:
        pickle.dump(model, f)
    logger.info(f"Model saved to {model_path}")
    
    # Save metrics
    metrics_path = results_dir / "metrics.json"
    metrics['best_hyperparameters'] = best_params
    metrics['config_summary'] = get_config_summary()
    
    with open(metrics_path, 'w') as f:
        json.dump(metrics, f, indent=2)
    logger.info(f"Metrics saved to {metrics_path}")
    
    log_pipeline_event("Model training and artifact saving completed successfully")

def main():
    """
    Main execution function for training pipeline.
    """
    try:
        # 1. Load data
        X_train, X_test, y_train, y_test = load_data()
        
        # 2. Inner loop CV for hyperparameter selection
        cv_results = inner_loop_cv_selection(X_train, y_train)
        best_params = cv_results['best_params']
        
        # 3. Train final model
        model = train_model(X_train, y_train, best_params)
        
        # 4. Evaluate on test set
        metrics = evaluate_model(model, X_test, y_test)
        
        # 5. Save artifacts (MODEL AND METRICS)
        save_artifacts(model, metrics, best_params)
        
        logger.info("Pipeline execution successful.")
        return 0
        
    except Exception as e:
        logger.error(f"Pipeline execution failed: {e}", exc_info=True)
        return 1

if __name__ == "__main__":
    sys.exit(main())