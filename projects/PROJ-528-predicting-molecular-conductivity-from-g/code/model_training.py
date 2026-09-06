import os
import json
import logging
import argparse
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.model_selection import cross_val_score
from code.logging_config import setup_logging
from code.config import SEED, TARGET_VAR
from code.data_loader import load_processed_data
from code.scaffold_split import scaffold_split
from code.analysis import filter_outliers

# Setup logging
logger = setup_logging(__name__)

def apply_log_transformation(df, target_col):
    """
    Apply natural log transformation to the target variable.
    """
    if target_col not in df.columns:
        raise ValueError(f"Target column '{target_col}' not found in DataFrame.")
    
    # Check for non-positive values which cannot be log transformed
    if (df[target_col] <= 0).any():
        logger.warning(f"Found non-positive values in {target_col}. Adding small epsilon for log transform.")
        df[target_col] = df[target_col] + 1e-6
    
    log_col = f"log_{target_col}"
    df[log_col] = np.log(df[target_col])
    return df

def train_models(df, target_col, feature_cols, sigma_threshold=3.0):
    """
    Train Random Forest and Gradient Boosting models on log-transformed target.
    Returns trained models and metrics.
    """
    logger.info(f"Filtering outliers with threshold {sigma_threshold}...")
    df_filtered = filter_outliers(df, target_col, sigma_threshold)
    
    if len(df_filtered) == 0:
        raise ValueError("No data remaining after outlier filtering.")
    
    X = df_filtered[feature_cols].values
    y = df_filtered[f"log_{target_col}"].values
    
    # Scaffold split
    train_idx, test_idx = scaffold_split(df_filtered, seed=SEED)
    
    X_train, X_test = X[train_idx], X[test_idx]
    y_train, y_test = y[train_idx], y[test_idx]
    
    # Random Forest
    rf = RandomForestRegressor(n_estimators=100, max_depth=None, random_state=SEED)
    rf.fit(X_train, y_train)
    rf_r2 = rf.score(X_test, y_test)
    
    # Cross-validation for RF
    rf_cv_scores = cross_val_score(rf, X_train, y_train, cv=5, scoring='r2')
    
    # Gradient Boosting
    gb = GradientBoostingRegressor(n_estimators=100, learning_rate=0.1, random_state=SEED)
    gb.fit(X_train, y_train)
    gb_r2 = gb.score(X_test, y_test)
    
    # Cross-validation for GB
    gb_cv_scores = cross_val_score(gb, X_train, y_train, cv=5, scoring='r2')
    
    return {
        'rf': rf,
        'gb': gb,
        'rf_r2': rf_r2,
        'gb_r2': gb_r2,
        'rf_cv_scores': rf_cv_scores.tolist(),
        'gb_cv_scores': gb_cv_scores.tolist(),
        'train_size': len(train_idx),
        'test_size': len(test_idx)
    }

def save_model_results(metrics, output_path):
    """
    Save model results to JSON file.
    """
    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # Prepare data structure
    results = {
        'rf_r2': metrics['rf_r2'],
        'gb_r2': metrics['gb_r2'],
        'cv_scores': {
            'rf': metrics['rf_cv_scores'],
            'gb': metrics['gb_cv_scores']
        },
        'train_size': metrics['train_size'],
        'test_size': metrics['test_size'],
        'target_variable': TARGET_VAR,
        'seed': SEED
    }
    
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"Model results saved to {output_path}")
    return results

def main():
    parser = argparse.ArgumentParser(description="Train models on processed data.")
    parser.add_argument('--data', type=str, required=True, help='Path to processed descriptors CSV')
    parser.add_argument('--output', type=str, required=True, help='Path to save model results JSON')
    parser.add_argument('--threshold', type=float, default=3.0, help='Outlier threshold (sigma)')
    args = parser.parse_args()
    
    logger.info(f"Loading data from {args.data}")
    df = load_processed_data(args.data)
    
    # Define feature columns (exclude non-feature columns)
    exclude_cols = ['smiles', 'status', TARGET_VAR, f"log_{TARGET_VAR}"]
    feature_cols = [col for col in df.columns if col not in exclude_cols]
    
    if not feature_cols:
        raise ValueError("No feature columns found in the dataset.")
    
    logger.info(f"Training models with {len(feature_cols)} features")
    
    # Apply log transformation
    df = apply_log_transformation(df, TARGET_VAR)
    
    # Train models
    metrics = train_models(df, TARGET_VAR, feature_cols, sigma_threshold=args.threshold)
    
    # Save results
    results = save_model_results(metrics, args.output)
    
    print(json.dumps(results, indent=2))

if __name__ == "__main__":
    main()
