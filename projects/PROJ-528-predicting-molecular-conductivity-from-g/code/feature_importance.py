import os
import json
import logging
import pandas as pd
import numpy as np
from typing import Dict, Any, List, Tuple, Optional

from sklearn.ensemble import RandomForestRegressor
from sklearn.inspection import permutation_importance

import config
from logging_config import setup_logging
from data_loader import load_processed_data
from model_training import train_models

logger = setup_logging(__name__)

def load_processed_data(path: str) -> pd.DataFrame:
    """Load processed data from CSV."""
    if not os.path.exists(path):
        raise FileNotFoundError(f"Data file not found: {path}")
    return pd.read_csv(path)

def prepare_features_and_target(df: pd.DataFrame, target_col: str) -> Tuple[np.ndarray, np.ndarray, List[str]]:
    """Prepare feature matrix and target vector."""
    feature_cols = [c for c in df.columns if c != target_col]
    X = df[feature_cols].values
    y = df[target_col].values
    return X, y, feature_cols

def train_model(X: np.ndarray, y: np.ndarray, seed: int = 42) -> RandomForestRegressor:
    """Train a Random Forest model."""
    rf = RandomForestRegressor(n_estimators=100, random_state=seed)
    rf.fit(X, y)
    return rf

def compute_feature_importance(
    model: RandomForestRegressor, 
    X: np.ndarray, 
    y: np.ndarray, 
    feature_names: List[str],
    n_repeats: int = 10,
    seed: int = 42
) -> pd.DataFrame:
    """Compute permutation importance."""
    result = permutation_importance(model, X, y, n_repeats=n_repeats, random_state=seed)
    
    importance_df = pd.DataFrame({
        'feature': feature_names,
        'importance_mean': result.importances_mean,
        'importance_std': result.importances_std
    })
    
    # Sort by importance descending
    importance_df = importance_df.sort_values(by='importance_mean', ascending=False)
    return importance_df

def save_feature_importance_csv(df: pd.DataFrame, output_path: str) -> None:
    """Save feature importance to CSV."""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    df.to_csv(output_path, index=False)
    logger.info(f"Feature importance saved to {output_path}")

def run_feature_importance_analysis(
    data_path: str, 
    output_path: str,
    target_col: str = 'log_conductivity',
    seed: int = 42
) -> None:
    """Run full feature importance analysis pipeline."""
    logger.info(f"Loading data from {data_path}")
    df = load_processed_data(data_path)
    
    if target_col not in df.columns:
        logger.error(f"Target column {target_col} not found.")
        return
    
    X, y, feature_names = prepare_features_and_target(df, target_col)
    model = train_model(X, y, seed=seed)
    
    importance_df = compute_feature_importance(model, X, y, feature_names, seed=seed)
    save_feature_importance_csv(importance_df, output_path)

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Compute and save feature importance.")
    parser.add_argument('--data', type=str, required=True, help='Path to processed data')
    parser.add_argument('--output', type=str, required=True, help='Path to output CSV')
    parser.add_argument('--target', type=str, default='log_conductivity', help='Target column')
    args = parser.parse_args()
    
    run_feature_importance_analysis(args.data, args.output, args.target)

if __name__ == "__main__":
    main()
