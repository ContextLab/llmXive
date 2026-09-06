import os
import json
import logging
import pandas as pd
import numpy as np
from typing import Dict, Any, List, Tuple, Optional
from sklearn.ensemble import RandomForestRegressor
from sklearn.inspection import permutation_importance
from code.logging_config import setup_logging
from code.config import SEED, TARGET_VAR
from code.data_loader import load_processed_data
from code.scaffold_split import scaffold_split

logger = setup_logging(__name__)

def load_processed_data(path: str) -> pd.DataFrame:
    """Load processed data from CSV."""
    if not os.path.exists(path):
        raise FileNotFoundError(f"Data file not found: {path}")
    return pd.read_csv(path)

def prepare_features_and_target(df, target_col):
    """Prepare feature matrix and target vector."""
    log_col = f"log_{target_col}"
    if log_col not in df.columns:
        df = df.copy()
        df[log_col] = np.log(df[target_col] + 1e-6)
    
    exclude_cols = ['smiles', 'status', target_col, log_col]
    feature_cols = [col for col in df.columns if col not in exclude_cols]
    
    X = df[feature_cols].values
    y = df[log_col].values
    return X, y, feature_cols

def train_model(X_train, y_train):
    """Train a Random Forest model."""
    model = RandomForestRegressor(n_estimators=100, max_depth=None, random_state=SEED)
    model.fit(X_train, y_train)
    return model

def compute_feature_importance(model, X_test, y_test, feature_names, n_repeats=10):
    """Compute permutation importance."""
    result = permutation_importance(model, X_test, y_test, n_repeats=n_repeats, random_state=SEED)
    importance_scores = result.importances_mean
    
    importance_dict = {}
    for i, name in enumerate(feature_names):
        importance_dict[name] = float(importance_scores[i])
    
    return importance_dict

def save_feature_importance_csv(importance_dict, output_path):
    """Save feature importance to CSV."""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    df = pd.DataFrame([
        {'feature': name, 'importance': score}
        for name, score in importance_dict.items()
    ])
    df = df.sort_values('importance', ascending=False)
    df.to_csv(output_path, index=False)
    logger.info(f"Feature importance saved to {output_path}")

def run_feature_importance_analysis(df, target_col, output_path):
    """Run full feature importance analysis."""
    X, y, feature_cols = prepare_features_and_target(df, target_col)
    
    train_idx, test_idx = scaffold_split(df, seed=SEED)
    X_train, X_test = X[train_idx], X[test_idx]
    y_train, y_test = y[train_idx], y[test_idx]
    
    model = train_model(X_train, y_train)
    importance = compute_feature_importance(model, X_test, y_test, feature_cols)
    save_feature_importance_csv(importance, output_path)
    
    return importance

def main():
    parser = argparse.ArgumentParser(description="Compute feature importance.")
    parser.add_argument('--data', type=str, required=True, help='Path to processed data CSV')
    parser.add_argument('--output', type=str, required=True, help='Path to save feature importance CSV')
    args = parser.parse_args()
    
    logger.info(f"Loading data from {args.data}")
    df = load_processed_data(args.data)
    
    logger.info("Computing feature importance...")
    run_feature_importance_analysis(df, TARGET_VAR, args.output)

if __name__ == "__main__":
    main()
