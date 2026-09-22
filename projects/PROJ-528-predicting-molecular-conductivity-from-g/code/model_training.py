"""
Model training module for Random Forest and Gradient Boosting regressors.
"""
import os
import sys
import json
import logging
import argparse
import numpy as np
import pandas as pd
from typing import Dict, Any, List, Optional
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.model_selection import cross_val_score
from sklearn.metrics import mean_absolute_error, r2_score
from code.config import SEED
from code.scaffold_split import scaffold_split

def apply_log_transformation(target: np.ndarray) -> np.ndarray:
    """Apply natural log transformation to target variable."""
    return np.log(target)

def select_target_variable(df: pd.DataFrame, target_candidates: List[str] = None) -> str:
    """
    Select target variable based on availability.
    
    Args:
        df: Input DataFrame
        target_candidates: List of candidate column names
    
    Returns:
        Selected target column name
    """
    if target_candidates is None:
        target_candidates = ['conductivity', 'charge_carrier_mobility', 'HOMO_LUMO_gap']
    
    for candidate in target_candidates:
        if candidate in df.columns:
            logging.info(f"Using {candidate} as target variable")
            return candidate
    
    raise ValueError("No valid target variable found in DataFrame")

def train_models(X_train: np.ndarray, y_train: np.ndarray,
                 X_test: np.ndarray, y_test: np.ndarray,
                 seed: int = SEED) -> tuple:
    """
    Train Random Forest and Gradient Boosting models.
    
    Args:
        X_train: Training features
        y_train: Training targets
        X_test: Test features
        y_test: Test targets
        seed: Random seed
    
    Returns:
        Tuple of (rf_model, gb_model, rf_metrics, gb_metrics)
    """
    # Random Forest
    rf_model = RandomForestRegressor(n_estimators=100, max_depth=None, random_state=seed)
    rf_model.fit(X_train, y_train)
    y_pred_rf = rf_model.predict(X_test)
    rf_metrics = {
        'r2': float(r2_score(y_test, y_pred_rf)),
        'mae': float(mean_absolute_error(y_test, y_pred_rf))
    }
    
    # Gradient Boosting
    gb_model = GradientBoostingRegressor(n_estimators=100, learning_rate=0.1, random_state=seed)
    gb_model.fit(X_train, y_train)
    y_pred_gb = gb_model.predict(X_test)
    gb_metrics = {
        'r2': float(r2_score(y_test, y_pred_gb)),
        'mae': float(mean_absolute_error(y_test, y_pred_gb))
    }
    
    logging.info(f"RF R²: {rf_metrics['r2']:.4f}, MAE: {rf_metrics['mae']:.4f}")
    logging.info(f"GB R²: {gb_metrics['r2']:.4f}, MAE: {gb_metrics['mae']:.4f}")
    
    return rf_model, gb_model, rf_metrics, gb_metrics

def run_cross_validation(model, X: np.ndarray, y: np.ndarray, cv: int = 5) -> np.ndarray:
    """Run k-fold cross validation and return R² scores."""
    scores = cross_val_score(model, X, y, cv=cv, scoring='r2')
    logging.info(f"CV R² scores: mean={scores.mean():.4f}, std={scores.std():.4f}")
    return scores

def save_model_results(results: Dict[str, Any], output_path: str) -> None:
    """Save model results to JSON file."""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    logging.info(f"Model results saved to {output_path}")

def main():
    """Main entry point for model training."""
    parser = argparse.ArgumentParser(description="Train models on processed data.")
    parser.add_argument('--data', type=str, default='data/processed/descriptors.csv',
                        help='Path to descriptors CSV')
    parser.add_argument('--output', type=str, default='data/processed/model_results.json',
                        help='Path to output results JSON')
    parser.add_argument('--target', type=str, default=None,
                        help='Target column name (default: auto-detect)')
    
    args = parser.parse_args()
    
    # Setup logging
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    try:
        # Load data
        df = pd.read_csv(args.data)
        
        # Select target
        target_col = select_target_variable(df) if args.target is None else args.target
        
        # Prepare features
        feature_cols = [col for col in df.columns if col not in ['smiles', target_col]]
        X = df[feature_cols].values
        y = df[target_col].values
        
        # Split data
        train_idx, test_idx = scaffold_split(df, seed=SEED)
        X_train, X_test = X[train_idx], X[test_idx]
        y_train, y_test = y[train_idx], y[test_idx]
        
        # Log transform target
        y_train_log = apply_log_transformation(y_train)
        y_test_log = apply_log_transformation(y_test)
        
        # Train models
        rf_model, gb_model, rf_metrics, gb_metrics = train_models(
            X_train, y_train_log, X_test, y_test_log
        )
        
        # Cross-validation
        cv_scores_rf = run_cross_validation(rf_model, X_train, y_train_log)
        cv_scores_gb = run_cross_validation(gb_model, X_train, y_train_log)
        
        # Prepare results
        results = {
            'target_variable': target_col,
            'rf_r2': rf_metrics['r2'],
            'rf_mae': rf_metrics['mae'],
            'rf_cv_mean': float(cv_scores_rf.mean()),
            'rf_cv_std': float(cv_scores_rf.std()),
            'gb_r2': gb_metrics['r2'],
            'gb_mae': gb_metrics['mae'],
            'gb_cv_mean': float(cv_scores_gb.mean()),
            'gb_cv_std': float(cv_scores_gb.std())
        }
        
        # Save results
        save_model_results(results, args.output)
        
        print(json.dumps(results, indent=2))
        
    except Exception as e:
        logging.error(f"Error during model training: {str(e)}", exc_info=True)
        sys.exit(1)

if __name__ == '__main__':
    main()
