import os
import json
import logging
import numpy as np
import pandas as pd
from typing import Dict, Any, Tuple, Optional
from code.logging_config import setup_logging
from code.config import DATA_PATH, SEED
from code.scaffold_split import scaffold_split
from code.model_training import apply_log_transformation, train_models, run_cross_validation, save_model_results

def load_processed_data(path: Optional[str] = None) -> pd.DataFrame:
    """
    Loads processed data (descriptors + target).
    Default path: data/processed/descriptors.csv
    """
    if path is None:
        path = os.path.join(DATA_PATH, "processed", "descriptors.csv")
    
    if not os.path.exists(path):
        raise FileNotFoundError(f"Processed data not found at {path}")
    
    df = pd.read_csv(path)
    logging.info(f"Loaded processed data: {len(df)} rows, {len(df.columns)} columns")
    return df

def prepare_features_and_target(df: pd.DataFrame, target_col: Optional[str] = None) -> Tuple[np.ndarray, np.ndarray, list]:
    """
    Prepares feature matrix X and target vector y.
    Returns X, y, feature_names.
    """
    # Identify target column
    if target_col is None:
        # Try to find a target column
        possible_targets = ['conductivity', 'log_conductivity', 'HOMO_LUMO_gap', 'log_conductivity_proxy']
        target_col = None
        for col in possible_targets:
            if col in df.columns:
                target_col = col
                break
        
        if target_col is None:
            # Fallback: last column
            target_col = df.columns[-1]
            logging.warning(f"Target column not found, using last column: {target_col}")
    
    if target_col not in df.columns:
        raise ValueError(f"Target column '{target_col}' not found in data.")
    
    # Separate features and target
    feature_cols = [c for c in df.columns if c != target_col]
    X = df[feature_cols].values
    y = df[target_col].values
    
    # Handle log transformation if needed
    # Check if target is already log-transformed
    if 'log_' not in target_col and 'conductivity' in target_col:
        logging.info(f"Applying log transformation to target: {target_col}")
        y = np.log(y)
        # Create new column name
        new_target_col = f"log_{target_col}"
        df[new_target_col] = y
    
    return X, y, feature_cols

def train_and_evaluate(X: np.ndarray, y: np.ndarray, feature_names: list, 
                       train_idx: list, test_idx: list) -> Dict[str, Any]:
    """
    Trains models on the training split and evaluates on test split.
    """
    X_train, X_test = X[train_idx], X[test_idx]
    y_train, y_test = y[train_idx], y[test_idx]
    
    # Train models (RF and GB)
    results = train_models(X_train, y_train, X_test, y_test, seed=SEED)
    
    # Cross-validation
    cv_results = run_cross_validation(X_train, y_train, seed=SEED)
    
    return {
        "models": results,
        "cv_scores": cv_results
    }

def main():
    """
    CLI entry point for model training.
    """
    import argparse
    parser = argparse.ArgumentParser(description="Train models on processed data.")
    parser.add_argument("--input", type=str, default=None, help="Path to processed data CSV.")
    parser.add_argument("--target", type=str, default=None, help="Target column name.")
    args = parser.parse_args()

    setup_logging()
    
    # Load data
    df = load_processed_data(args.input)
    
    # Prepare features and target
    X, y, feature_names = prepare_features_and_target(df, args.target)
    
    # Split data
    train_idx, test_idx = scaffold_split(df, 'smiles') # Assuming 'smiles' column exists
    
    # Train and evaluate
    results = train_and_evaluate(X, y, feature_names, train_idx, test_idx)
    
    # Save results
    save_model_results(results)
    
    logging.info("Model training completed.")

if __name__ == "__main__":
    main()
