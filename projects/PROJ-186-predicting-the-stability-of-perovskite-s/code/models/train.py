import os
import sys
import json
import logging
import pickle
from pathlib import Path
from typing import Dict, List, Tuple, Any, Optional

import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split, GridSearchCV, StratifiedKFold
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_squared_error, r2_score
from sklearn.inspection import permutation_importance
import matplotlib.pyplot as plt

# Project imports
from utils.logging_config import get_logger, log_pipeline_event, log_exclusion_reason
from utils.model_metadata import save_model_metadata

# Ensure logger is configured
logger = get_logger(__name__)

# Constants
INPUT_PATH = Path("data/processed/features.csv")
OUTPUT_MODEL_PATH = Path("results/model.pkl")
OUTPUT_METRICS_PATH = Path("results/metrics.json")
OUTPUT_FEATURE_IMP_PATH = Path("results/feature-importance.png")
RANDOM_STATE = 42

def load_data() -> pd.DataFrame:
    """Load the processed features dataset."""
    if not INPUT_PATH.exists():
        raise FileNotFoundError(
            f"Input data file not found: {INPUT_PATH}. "
            "Please run T016 (preprocess.py) first."
        )
    
    logger.info(f"Loading data from {INPUT_PATH}")
    df = pd.read_csv(INPUT_PATH)
    
    # Verify required columns exist
    required_cols = ['decomposition_energy']
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns in {INPUT_PATH}: {missing}")
    
    # Drop rows with NaN in target (should be handled by T016, but safety check)
    initial_count = len(df)
    df = df.dropna(subset=['decomposition_energy'])
    if len(df) < initial_count:
        logger.warning(f"Dropped {initial_count - len(df)} rows with NaN target values.")
    
    logger.info(f"Loaded {len(df)} samples with columns: {list(df.columns)}")
    return df

def inner_loop_cv_selection(df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Perform stratified split by target variable.
    Since target is continuous, we bin it for stratification.
    Allocates majority (80%) to train, remainder (20%) to test.
    """
    logger.info("Performing stratified split by target variable...")
    
    # Prepare features and target
    feature_cols = [c for c in df.columns if c != 'decomposition_energy']
    X = df[feature_cols]
    y = df['decomposition_energy']
    
    # Create bins for stratification
    # Use quantile-based binning to ensure balanced splits across the target distribution
    n_bins = 10
    y_bins = pd.qcut(y, q=n_bins, labels=False, duplicates='drop')
    
    # Split: 80% train, 20% test
    X_train, X_test, y_train, y_test, train_idx, test_idx = train_test_split(
        X, y, y_bins,
        test_size=0.2,
        random_state=RANDOM_STATE,
        stratify=y_bins
    )
    
    logger.info(f"Train set size: {len(X_train)}, Test set size: {len(X_test)}")
    logger.info(f"Train target range: [{y_train.min():.4f}, {y_train.max():.4f}]")
    logger.info(f"Test target range: [{y_test.min():.4f}, {y_test.max():.4f}]")
    
    return X_train, X_test, y_train, y_test

def train_model(X_train: pd.DataFrame, y_train: pd.Series) -> Tuple[RandomForestRegressor, Dict[str, Any]]:
    """
    Run k-fold GridSearchCV on train_set for max_depth {10, 15, 20} and min_samples_leaf {1, 2, 4}.
    Select best params and re-train on full train_set.
    """
    logger.info("Starting GridSearchCV for hyperparameter tuning...")
    
    # Define parameter grid
    param_grid = {
        'max_depth': [10, 15, 20],
        'min_samples_leaf': [1, 2, 4]
    }
    
    # Base model
    base_model = RandomForestRegressor(random_state=RANDOM_STATE, n_jobs=-1)
    
    # GridSearchCV with 5-fold CV
    # Note: We use 5-fold as per task description
    cv = GridSearchCV(
        estimator=base_model,
        param_grid=param_grid,
        cv=5,
        scoring='neg_mean_squared_error',
        n_jobs=-1,
        verbose=1
    )
    
    logger.info(f"Searching over {len(param_grid['max_depth']) * len(param_grid['min_samples_leaf'])} combinations...")
    cv.fit(X_train, y_train)
    
    best_params = cv.best_params_
    best_score = -cv.best_score_  # Convert back to positive RMSE^2
    
    logger.info(f"Best parameters: {best_params}")
    logger.info(f"Best CV score (MSE): {best_score:.6f}")
    
    # Re-train on full train_set with best params
    logger.info("Re-training model on full training set with best parameters...")
    final_model = RandomForestRegressor(**best_params, random_state=RANDOM_STATE, n_jobs=-1)
    final_model.fit(X_train, y_train)
    
    return final_model, best_params

def evaluate_model(model: RandomForestRegressor, X_test: pd.DataFrame, y_test: pd.Series) -> Dict[str, float]:
    """Evaluate on test_set and log test RMSE."""
    logger.info("Evaluating model on test set...")
    
    y_pred = model.predict(X_test)
    
    rmse = np.sqrt(mean_squared_error(y_test, y_pred))
    r2 = r2_score(y_test, y_pred)
    
    logger.info(f"Test RMSE: {rmse:.6f}")
    logger.info(f"Test R²: {r2:.6f}")
    
    return {
        'rmse': float(rmse),
        'r2': float(r2),
        'test_samples': len(y_test)
    }

def perform_permutation_importance(model: RandomForestRegressor, X_test: pd.DataFrame, y_test: pd.Series) -> pd.DataFrame:
    """Perform permutation importance analysis (SC-002)."""
    logger.info("Performing permutation importance analysis...")
    
    result = permutation_importance(
        model, X_test, y_test,
        n_repeats=10,
        random_state=RANDOM_STATE,
        n_jobs=-1
    )
    
    # Create a DataFrame for easy plotting
    importance_df = pd.DataFrame({
        'feature': X_test.columns,
        'importance_mean': result.importances_mean,
        'importance_std': result.importances_std
    })
    
    # Sort by importance
    importance_df = importance_df.sort_values(by='importance_mean', ascending=False)
    
    logger.info("Permutation importance calculated.")
    return importance_df

def save_artifacts(
    model: RandomForestRegressor,
    metrics: Dict[str, Any],
    best_params: Dict[str, Any],
    importance_df: pd.DataFrame,
    feature_names: List[str]
):
    """Save model, metrics, and feature importance plot."""
    
    # Ensure results directory exists
    OUTPUT_MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_METRICS_PATH.parent.mkdir(parents=True, exist_ok=True)
    
    # 1. Save Model
    logger.info(f"Saving model to {OUTPUT_MODEL_PATH}")
    with open(OUTPUT_MODEL_PATH, 'wb') as f:
        pickle.dump({
            'model': model,
            'best_params': best_params,
            'feature_names': feature_names
        }, f)
    
    # 2. Save Metrics
    # Include dft_functional as required by task description
    metrics['dft_functional'] = 'PBE'
    metrics['best_params'] = best_params
    
    logger.info(f"Saving metrics to {OUTPUT_METRICS_PATH}")
    with open(OUTPUT_METRICS_PATH, 'w') as f:
        json.dump(metrics, f, indent=2)
    
    # 3. Save Feature Importance Plot
    logger.info(f"Saving feature importance plot to {OUTPUT_FEATURE_IMP_PATH}")
    
    plt.figure(figsize=(10, 8))
    y_pos = np.arange(len(importance_df))
    plt.barh(y_pos, importance_df['importance_mean'], xerr=importance_df['importance_std'], align='center')
    plt.yticks(y_pos, importance_df['feature'])
    plt.xlabel('Permutation Importance (Decrease in R²)')
    plt.title('Feature Importance (Permutation)')
    plt.gca().invert_yaxis()  # Most important at top
    plt.tight_layout()
    plt.savefig(OUTPUT_FEATURE_IMP_PATH, dpi=150)
    plt.close()
    
    logger.info("All artifacts saved successfully.")

def main():
    """Main entry point for training pipeline."""
    log_pipeline_event("Starting Model Training (T020)")
    
    try:
        # 1. Load Data
        df = load_data()
        
        # 2. Split Data
        X_train, X_test, y_train, y_test = inner_loop_cv_selection(df)
        
        # 3. Train Model (GridSearchCV + Re-train)
        model, best_params = train_model(X_train, y_train)
        
        # 4. Evaluate
        test_metrics = evaluate_model(model, X_test, y_test)
        
        # 5. Permutation Importance
        importance_df = perform_permutation_importance(model, X_test, y_test)
        
        # 6. Save Artifacts
        feature_names = X_train.columns.tolist()
        save_artifacts(
            model=model,
            metrics=test_metrics,
            best_params=best_params,
            importance_df=importance_df,
            feature_names=feature_names
        )
        
        log_pipeline_event("Model Training (T020) completed successfully")
        return 0
        
    except Exception as e:
        logger.error(f"Training pipeline failed: {str(e)}", exc_info=True)
        log_exclusion_reason("T020", str(e))
        return 1

if __name__ == "__main__":
    sys.exit(main())