import os
import json
import logging
import numpy as np
import pandas as pd
from typing import Dict, Any, Tuple, Optional
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.model_selection import cross_val_score, train_test_split
from sklearn.metrics import r2_score, mean_absolute_error
from code.config import SEED, TARGET_VAR, DATA_PATH
from code.logging_config import setup_logging
from code.scaffold_split import scaffold_split
from code.data_loader import load_processed_data, apply_log_transformation

# Setup logging
logger = setup_logging(__name__)

def apply_log_transformation(df: pd.DataFrame, target_col: str = None) -> pd.DataFrame:
    """
    Apply natural logarithm transformation to the target variable.
    
    Args:
        df: Input DataFrame
        target_col: Name of the target column. If None, uses TARGET_VAR from config.
        
    Returns:
        DataFrame with new log-transformed column
    """
    if target_col is None:
        target_col = TARGET_VAR
    
    if target_col not in df.columns:
        # Check for fallback target
        if 'HOMO_LUMO_gap' in df.columns:
            logger.warning(f"Target '{target_col}' not found. Falling back to 'HOMO_LUMO_gap'.")
            target_col = 'HOMO_LUMO_gap'
        else:
            raise ValueError(f"No valid target variable found. Expected '{target_col}' or 'HOMO_LUMO_gap'.")
    
    # Handle non-positive values for log transformation
    if (df[target_col] <= 0).any():
        logger.warning(f"Found non-positive values in '{target_col}'. Adding small constant for log transform.")
        min_val = df[target_col].min()
        offset = abs(min_val) + 1e-6
        df[f'log_{target_col}'] = np.log(df[target_col] + offset)
    else:
        df[f'log_{target_col}'] = np.log(df[target_col])
        
    return df

def train_models(df: pd.DataFrame, target_col: str = None, 
                 test_size: float = 0.2, cv_folds: int = 5) -> Dict[str, Any]:
    """
    Train Random Forest and Gradient Boosting models with 5-fold cross-validation.
    
    Args:
        df: DataFrame with features and target
        target_col: Name of the target column
        test_size: Proportion of data for testing
        cv_folds: Number of cross-validation folds
        
    Returns:
        Dictionary containing model results, metrics, and cross-validation scores
    """
    if target_col is None:
        target_col = TARGET_VAR
    
    # Apply log transformation
    df = apply_log_transformation(df, target_col)
    log_target_col = f'log_{target_col}'
    
    # Identify feature columns (exclude SMILES, status, and target columns)
    exclude_cols = ['smiles', 'status', target_col, log_target_col]
    feature_cols = [col for col in df.columns if col not in exclude_cols]
    
    if not feature_cols:
        raise ValueError("No feature columns found in the dataset.")
    
    X = df[feature_cols].dropna()
    y = df.loc[X.index, log_target_col]
    
    # Remove any rows where features or target are NaN after selection
    valid_indices = X.index.intersection(y.index)
    X = X.loc[valid_indices]
    y = y.loc[valid_indices]
    
    if len(X) == 0:
        raise ValueError("No valid data points remaining after cleaning.")
    
    # Perform scaffold-based split
    try:
        # Use smiles for scaffold split if available, otherwise fall back to random split
        if 'smiles' in df.columns:
            smiles_series = df.loc[valid_indices, 'smiles']
            train_idx, test_idx = scaffold_split(smiles_series, test_size=test_size, seed=SEED)
        else:
            # Fallback to random split if no SMILES
            train_idx, test_idx = train_test_split(
                X.index, test_size=test_size, random_state=SEED
            )
    except Exception as e:
        logger.warning(f"Scaffold split failed ({e}), falling back to random split.")
        train_idx, test_idx = train_test_split(
            X.index, test_size=test_size, random_state=SEED
        )
    
    X_train, X_test = X.loc[train_idx], X.loc[test_idx]
    y_train, y_test = y.loc[train_idx], y.loc[test_idx]
    
    # Initialize models
    rf_model = RandomForestRegressor(
        n_estimators=100,
        max_depth=None,
        random_state=SEED,
        n_jobs=-1
    )
    
    gb_model = GradientBoostingRegressor(
        n_estimators=100,
        learning_rate=0.1,
        random_state=SEED,
        max_depth=5
    )
    
    results = {
        'feature_columns': feature_cols,
        'train_size': len(X_train),
        'test_size': len(X_test),
        'cv_folds': cv_folds
    }
    
    # Train and evaluate Random Forest
    logger.info("Training Random Forest model...")
    rf_model.fit(X_train, y_train)
    rf_pred = rf_model.predict(X_test)
    rf_r2 = r2_score(y_test, rf_pred)
    rf_mae = mean_absolute_error(y_test, rf_pred)
    
    # 5-fold Cross-validation for RF
    rf_cv_scores = cross_val_score(rf_model, X_train, y_train, cv=cv_folds, scoring='r2')
    rf_cv_mean = float(np.mean(rf_cv_scores))
    rf_cv_std = float(np.std(rf_cv_scores))
    
    results['rf'] = {
        'r2': float(rf_r2),
        'mae': float(rf_mae),
        'cv_r2_mean': rf_cv_mean,
        'cv_r2_std': rf_cv_std,
        'cv_scores': rf_cv_scores.tolist()
    }
    logger.info(f"RF - R²: {rf_r2:.4f}, MAE: {rf_mae:.4f}, CV R²: {rf_cv_mean:.4f} ± {rf_cv_std:.4f}")
    
    # Train and evaluate Gradient Boosting
    logger.info("Training Gradient Boosting model...")
    gb_model.fit(X_train, y_train)
    gb_pred = gb_model.predict(X_test)
    gb_r2 = r2_score(y_test, gb_pred)
    gb_mae = mean_absolute_error(y_test, gb_pred)
    
    # 5-fold Cross-validation for GB
    gb_cv_scores = cross_val_score(gb_model, X_train, y_train, cv=cv_folds, scoring='r2')
    gb_cv_mean = float(np.mean(gb_cv_scores))
    gb_cv_std = float(np.std(gb_cv_scores))
    
    results['gb'] = {
        'r2': float(gb_r2),
        'mae': float(gb_mae),
        'cv_r2_mean': gb_cv_mean,
        'cv_r2_std': gb_cv_std,
        'cv_scores': gb_cv_scores.tolist()
    }
    logger.info(f"GB - R²: {gb_r2:.4f}, MAE: {gb_mae:.4f}, CV R²: {gb_cv_mean:.4f} ± {gb_cv_std:.4f}")
    
    # Store models for potential later use (optional, not serialized here)
    results['models'] = {
        'rf': 'RandomForestRegressor',
        'gb': 'GradientBoostingRegressor'
    }
    
    return results

def main():
    """
    Main entry point for model training script.
    Usage: python code/model_training.py --data <input_csv> --output <output_json>
    """
    import argparse
    
    parser = argparse.ArgumentParser(description='Train molecular conductivity models')
    parser.add_argument('--data', type=str, required=True, 
                      help='Path to input descriptors CSV')
    parser.add_argument('--output', type=str, required=True, 
                      help='Path to output results JSON')
    parser.add_argument('--target', type=str, default=None,
                      help='Target variable name (default: from config)')
    args = parser.parse_args()
    
    # Load data
    logger.info(f"Loading data from {args.data}")
    df = load_processed_data(args.data)
    
    if df.empty:
        raise ValueError("Input dataset is empty.")
    
    # Train models
    logger.info("Starting model training...")
    results = train_models(df, target_col=args.target)
    
    # Save results
    output_dir = os.path.dirname(args.output)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)
        
    with open(args.output, 'w') as f:
        json.dump(results, f, indent=2)
        
    logger.info(f"Results saved to {args.output}")
    print(f"Training complete. Results written to {args.output}")

if __name__ == "__main__":
    main()