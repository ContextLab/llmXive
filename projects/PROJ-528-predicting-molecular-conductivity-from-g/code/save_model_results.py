import os
import json
import logging
import argparse
from typing import Dict, Any, List, Optional
import numpy as np
import pandas as pd
from code.logging_config import setup_logging
from code.config import SEED, TARGET_VAR
from code.data_loader import load_processed_data
from code.scaffold_split import scaffold_split
from code.analysis import run_sensitivity_analysis, filter_outliers
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.model_selection import cross_val_score

logger = setup_logging(__name__)

def load_sensitivity_analysis(path: str) -> Dict[str, Any]:
    """Load sensitivity analysis from JSON file."""
    with open(path, 'r') as f:
        return json.load(f)

def prepare_data_and_split(df, target_col, feature_cols, sigma_threshold=3.0):
    """Prepare data and split into train/test sets."""
    log_col = f"log_{target_col}"
    if log_col not in df.columns:
        df = df.copy()
        df[log_col] = np.log(df[target_col] + 1e-6)
    
    df_filtered = filter_outliers(df, target_col, sigma_threshold)
    
    X = df_filtered[feature_cols].values
    y = df_filtered[log_col].values
    
    train_idx, test_idx = scaffold_split(df_filtered, seed=SEED)
    return X[train_idx], X[test_idx], y[train_idx], y[test_idx]

def train_models_and_get_r2(X_train, X_test, y_train, y_test):
    """Train RF and GB models and return R2 scores."""
    rf = RandomForestRegressor(n_estimators=100, max_depth=None, random_state=SEED)
    rf.fit(X_train, y_train)
    rf_r2 = rf.score(X_test, y_test)
    
    gb = GradientBoostingRegressor(n_estimators=100, learning_rate=0.1, random_state=SEED)
    gb.fit(X_train, y_train)
    gb_r2 = gb.score(X_test, y_test)
    
    return rf_r2, gb_r2

def main():
    parser = argparse.ArgumentParser(description="Save model results and sensitivity analysis.")
    parser.add_argument('--data', type=str, required=True, help='Path to processed descriptors CSV')
    parser.add_argument('--output', type=str, required=True, help='Path to save model results JSON')
    parser.add_argument('--sensitivity-output', type=str, default='data/processed/sensitivity_analysis.json', help='Path to save sensitivity analysis JSON')
    args = parser.parse_args()
    
    logger.info(f"Loading data from {args.data}")
    df = load_processed_data(args.data)
    
    # Define feature columns
    exclude_cols = ['smiles', 'status', TARGET_VAR, f"log_{TARGET_VAR}"]
    feature_cols = [col for col in df.columns if col not in exclude_cols]
    
    if not feature_cols:
        raise ValueError("No feature columns found.")
    
    # Apply log transformation
    log_col = f"log_{TARGET_VAR}"
    if log_col not in df.columns:
        df[log_col] = np.log(df[TARGET_VAR] + 1e-6)
    
    # Run sensitivity analysis
    logger.info("Running sensitivity analysis...")
    sensitivity_results = run_sensitivity_analysis(df, TARGET_VAR, feature_cols)
    
    # Save sensitivity analysis
    os.makedirs(os.path.dirname(args.sensitivity_output), exist_ok=True)
    with open(args.sensitivity_output, 'w') as f:
        json.dump(sensitivity_results, f, indent=2)
    logger.info(f"Sensitivity analysis saved to {args.sensitivity_output}")
    
    # Train final models with default threshold
    X_train, X_test, y_train, y_test = prepare_data_and_split(df, TARGET_VAR, feature_cols, sigma_threshold=3.0)
    rf_r2, gb_r2 = train_models_and_get_r2(X_train, X_test, y_train, y_test)
    
    # Prepare final results
    results = {
        'rf_r2': rf_r2,
        'gb_r2': gb_r2,
        'cv_scores': {
            'rf': cross_val_score(RandomForestRegressor(n_estimators=100, max_depth=None, random_state=SEED), X_train, y_train, cv=5, scoring='r2').tolist(),
            'gb': cross_val_score(GradientBoostingRegressor(n_estimators=100, learning_rate=0.1, random_state=SEED), X_train, y_train, cv=5, scoring='r2').tolist()
        },
        'sensitivity_analysis': sensitivity_results
    }
    
    # Save model results
    os.makedirs(os.path.dirname(args.output), exist_ok=True)
    with open(args.output, 'w') as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"Model results saved to {args.output}")
    print(json.dumps(results, indent=2))

if __name__ == "__main__":
    main()
