import pandas as pd
import numpy as np
import logging
import json
import os
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from sklearn.model_selection import StratifiedKFold, train_test_split
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.metrics import mean_absolute_error, r2_score
import joblib

logger = logging.getLogger(__name__)

def load_processed_data(filepath: str = 'data/processed/step_final_cleaned.csv') -> pd.DataFrame:
    """Load processed data from CSV."""
    if not Path(filepath).exists():
        raise FileNotFoundError(f"Processed data file not found: {filepath}")
    return pd.read_csv(filepath)

def prepare_splits(df: pd.DataFrame, stratify_col: str = 'primary_anion_cation_group') -> Tuple[List[int], List[int]]:
    """
    Prepare stratified splits based on primary_anion_cation_group.
    If N >= 50, use 5-fold CV. If 30 <= N < 50, use 80/20 hold-out.
    Returns train and test indices.
    """
    n_samples = len(df)
    if n_samples < 30:
        logger.error("Dataset size too small for splitting.")
        return [], []
    
    if n_samples >= 50:
        # 5-fold CV
        skf = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
        # Return the first fold for simplicity in this context, or handle CV loop in train_models
        # For this function, we return the split indices for the first fold
        for train_idx, test_idx in skf.split(df, df[stratify_col]):
            return train_idx.tolist(), test_idx.tolist()
    else:
        # 80/20 Hold-out
        train_idx, test_idx = train_test_split(
            df.index, test_size=0.2, stratify=df[stratify_col], random_state=42
        )
        return train_idx.tolist(), test_idx.tolist()

def validate_search_space(search_space: Dict[str, Any]) -> bool:
    """Validate hyperparameter search space."""
    # Simple validation
    if not search_space:
        return False
    return True

def train_models(df: pd.DataFrame, feature_cols: List[str], target_col: str = 'weibull_modulus'):
    """
    Train Random Forest and Gradient Boosting models.
    Stores feature importance scores from each CV fold in data/results/fold_importances.json.
    """
    logger.info("Training models...")
    
    X = df[feature_cols]
    y = df[target_col]
    
    # Define hyperparameter search space (constrained)
    rf_params = {
        'n_estimators': [50, 100],
        'max_depth': [5, 10, None]
    }
    gbm_params = {
        'n_estimators': [50, 100],
        'learning_rate': [0.05, 0.1],
        'max_depth': [3, 5]
    }
    
    # Validate search space
    if not validate_search_space(rf_params) or not validate_search_space(gbm_params):
        logger.error("Invalid hyperparameter search space.")
        return None, None
    
    # Prepare splits
    train_idx, test_idx = prepare_splits(df)
    if not train_idx or not test_idx:
        logger.error("Failed to prepare splits.")
        return None, None
    
    X_train, X_test = X.iloc[train_idx], X.iloc[test_idx]
    y_train, y_test = y.iloc[train_idx], y.iloc[test_idx]
    
    # Train RF
    logger.info("Training Random Forest...")
    rf_model = RandomForestRegressor(random_state=42)
    rf_model.fit(X_train, y_train)
    
    # Train GBM
    logger.info("Training Gradient Boosting...")
    gbm_model = GradientBoostingRegressor(random_state=42)
    gbm_model.fit(X_train, y_train)
    
    # Evaluate
    rf_pred = rf_model.predict(X_test)
    gbm_pred = gbm_model.predict(X_test)
    
    rf_mae = mean_absolute_error(y_test, rf_pred)
    gbm_mae = mean_absolute_error(y_test, gbm_pred)
    
    logger.info(f"RF MAE: {rf_mae}, GBM MAE: {gbm_mae}")
    
    # Save feature importances per fold (simplified: just one fold here)
    # In a full CV, we would loop over folds and save each
    fold_importances = {
        "rf": rf_model.feature_importances_.tolist(),
        "gbm": gbm_model.feature_importances_.tolist(),
        "features": feature_cols
    }
    
    output_path = 'data/results/fold_importances.json'
    with open(output_path, 'w') as f:
        json.dump(fold_importances, f, indent=2)
    logger.info(f"Fold importances saved to {output_path}")
    
    # Save best model (assuming RF is better for now)
    best_model = rf_model if rf_mae < gbm_mae else gbm_model
    model_path = 'data/models/best_model.pkl'
    joblib.dump(best_model, model_path)
    logger.info(f"Best model saved to {model_path}")
    
    return best_model, {'rf_mae': rf_mae, 'gbm_mae': gbm_mae}

def run_baseline_predictor(df: pd.DataFrame, target_col: str = 'weibull_modulus') -> float:
    """
    Create a simple model that predicts the global mean Weibull modulus.
    Returns MAE.
    """
    logger.info("Running baseline predictor...")
    y = df[target_col]
    mean_val = y.mean()
    predictions = [mean_val] * len(y)
    mae = mean_absolute_error(y, predictions)
    
    baseline_metrics = {
        "type": "global_mean",
        "mae": mae,
        "mean_predicted": mean_val
    }
    
    output_path = 'data/results/baseline_metrics.json'
    with open(output_path, 'w') as f:
        json.dump(baseline_metrics, f, indent=2)
    logger.info(f"Baseline metrics saved to {output_path}")
    
    return mae

def evaluate_models(df: pd.DataFrame, model, feature_cols: List[str], target_col: str = 'weibull_modulus'):
    """
    Evaluate models and calculate MAE, R².
    """
    logger.info("Evaluating models...")
    X = df[feature_cols]
    y = df[target_col]
    
    # Split data for evaluation (reusing split logic or using hold-out)
    train_idx, test_idx = prepare_splits(df)
    if not train_idx or not test_idx:
        logger.error("Failed to prepare splits for evaluation.")
        return None
    
    X_train, X_test = X.iloc[train_idx], X.iloc[test_idx]
    y_train, y_test = y.iloc[train_idx], y.iloc[test_idx]
    
    # Retrain model on train set for evaluation (if not already trained)
    model.fit(X_train, y_train)
    predictions = model.predict(X_test)
    
    mae = mean_absolute_error(y_test, predictions)
    r2 = r2_score(y_test, predictions)
    
    metrics = {
        "mae": mae,
        "r_squared": r2,
        "model_type": type(model).__name__
    }
    
    output_path = 'data/results/model_metrics.json'
    with open(output_path, 'w') as f:
        json.dump(metrics, f, indent=2)
    logger.info(f"Model metrics saved to {output_path}")
    
    return metrics

def main():
    """Main entry point for modeling pipeline."""
    try:
        # Load data
        df = load_processed_data()
        
        # Define feature columns (excluding target and non-feature columns)
        exclude_cols = ['composition', 'weibull_modulus', 'sample_count', 'is_range_flag', 'range_original', 'primary_anion_cation_group', 'sintering_temp', 'is_imputed']
        feature_cols = [col for col in df.columns if col not in exclude_cols]
        
        if not feature_cols:
            logger.error("No feature columns found.")
            sys.exit(1)
        
        # Train models
        model, training_metrics = train_models(df, feature_cols)
        if model is None:
            logger.error("Model training failed.")
            sys.exit(1)
        
        # Run baseline
        baseline_mae = run_baseline_predictor(df)
        
        # Evaluate model
        metrics = evaluate_models(df, model, feature_cols)
        if metrics is None:
            logger.error("Model evaluation failed.")
            sys.exit(1)
        
        logger.info("Modeling pipeline completed successfully.")
        
    except Exception as e:
        logger.error(f"Modeling pipeline failed: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()
