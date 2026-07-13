"""
Train Random Forest models for molecular property prediction.

Implements FR-004: Train two Random Forests (semi vs DFT) using 5-fold CV.
Compares MAE via paired t-test (FR-005).

This module provides the implementation for T021.
"""
import os
import sys
import csv
import logging
import argparse
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import KFold
from sklearn.metrics import mean_absolute_error, r2_score
from scipy import stats

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('logs/train_models.log')
    ]
)
logger = logging.getLogger(__name__)

def load_data(filepath: str) -> pd.DataFrame:
    """
    Load molecular descriptors from a CSV file.
    
    Args:
        filepath: Path to the CSV file.
        
    Returns:
        DataFrame with descriptors and target.
    """
    logger.info(f"Loading data from {filepath}")
    df = pd.read_csv(filepath)
    
    # Validate required columns
    required_cols = ['homo', 'lumo', 'mayer_bond_order', 'charge', 'experimental_barrier']
    missing = [col for col in required_cols if col not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns: {missing}")
        
    return df

def prepare_features_target(df: pd.DataFrame):
    """
    Separate features and target from the dataframe.
    """
    feature_cols = ['homo', 'lumo', 'mayer_bond_order', 'charge']
    X = df[feature_cols].values
    y = df['experimental_barrier'].values
    return X, y

def train_and_evaluate_fold(X: np.ndarray, y: np.ndarray, fold_idx: int, random_state: int = 42) -> Tuple[float, float, RandomForestRegressor]:
    """
    Train a Random Forest on a specific fold and return MAE, R2, and the model.
    """
    kf = KFold(n_splits=5, shuffle=True, random_state=random_state)
    train_idx, test_idx = list(kf.split(X))[fold_idx]
    
    X_train, X_test = X[train_idx], X[test_idx]
    y_train, y_test = y[train_idx], y[test_idx]
    
    model = RandomForestRegressor(
        n_estimators=100,
        max_depth=10,
        random_state=random_state,
        n_jobs=-1
    )
    model.fit(X_train, y_train)
    
    y_pred = model.predict(X_test)
    mae = mean_absolute_error(y_test, y_pred)
    r2 = r2_score(y_test, y_pred)
    
    return mae, r2, model

def train_models(semi_path: str, dft_path: str, output_path: str) -> Dict:
    """
    Main function to train models and compare performance.
    
    Args:
        semi_path: Path to semi-empirical descriptors CSV.
        dft_path: Path to DFT descriptors CSV.
        output_path: Path to save the results CSV.
        
    Returns:
        Dictionary containing metrics.
    """
    logger.info("Starting model training pipeline")
    
    # Load data
    try:
        df_semi = load_data(semi_path)
        df_dft = load_data(dft_path)
    except Exception as e:
        logger.error(f"Failed to load data: {e}")
        raise
    
    # Ensure same number of samples for paired t-test (FR-005)
    min_len = min(len(df_semi), len(df_dft))
    if min_len < 30:
        logger.warning(f"Dataset size ({min_len}) is smaller than recommended (30). Results may be unstable.")
    
    # Align data (assuming rows correspond to same molecules in order)
    df_semi = df_semi.head(min_len)
    df_dft = df_dft.head(min_len)
    
    X_semi, y_semi = prepare_features_target(df_semi)
    X_dft, y_dft = prepare_features_target(df_dft)
    
    logger.info(f"Training on {min_len} molecules")
    
    # Train and evaluate using 5-fold CV
    mae_semi_list = []
    mae_dft_list = []
    r2_semi_list = []
    r2_dft_list = []
    models_semi = []
    models_dft = []
    
    kf = KFold(n_splits=5, shuffle=True, random_state=42)
    
    logger.info("Performing 5-fold cross-validation for Semi-Empirical model")
    for fold_idx, (train_idx, test_idx) in enumerate(kf.split(X_semi)):
        X_train, X_test = X_semi[train_idx], X_semi[test_idx]
        y_train, y_test = y_semi[train_idx], y_semi[test_idx]
        
        model = RandomForestRegressor(n_estimators=100, max_depth=10, random_state=42, n_jobs=-1)
        model.fit(X_train, y_train)
        y_pred = model.predict(X_test)
        
        mae_semi_list.append(mean_absolute_error(y_test, y_pred))
        r2_semi_list.append(r2_score(y_test, y_pred))
        models_semi.append(model)
        
    logger.info("Performing 5-fold cross-validation for DFT model")
    for fold_idx, (train_idx, test_idx) in enumerate(kf.split(X_dft)):
        X_train, X_test = X_dft[train_idx], X_dft[test_idx]
        y_train, y_test = y_dft[train_idx], y_dft[test_idx]
        
        model = RandomForestRegressor(n_estimators=100, max_depth=10, random_state=42, n_jobs=-1)
        model.fit(X_train, y_train)
        y_pred = model.predict(X_test)
        
        mae_dft_list.append(mean_absolute_error(y_test, y_pred))
        r2_dft_list.append(r2_score(y_test, y_pred))
        models_dft.append(model)
    
    # Calculate mean metrics
    mean_mae_semi = np.mean(mae_semi_list)
    mean_mae_dft = np.mean(mae_dft_list)
    mean_r2_semi = np.mean(r2_semi_list)
    mean_r2_dft = np.mean(r2_dft_list)
    
    # Paired t-test (FR-005)
    # Compare the MAE of each fold between semi and dft
    t_stat, p_value = stats.ttest_rel(mae_semi_list, mae_dft_list)
    
    logger.info(f"Results - Semi MAE: {mean_mae_semi:.4f}, DFT MAE: {mean_mae_dft:.4f}")
    logger.info(f"Paired t-test p-value: {p_value:.4f}")
    
    # Prepare results
    results = {
        "mae_semi": mean_mae_semi,
        "mae_dft": mean_mae_dft,
        "r2_semi": mean_r2_semi,
        "r2_dft": mean_r2_dft,
        "p_value": p_value,
        "n_folds": 5,
        "n_samples": min_len
    }
    
    # Save results to CSV
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_file, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(["metric", "value"])
        for key, value in results.items():
            writer.writerow([key, value])
    
    logger.info(f"Results saved to {output_path}")
    
    # Save models (optional but good practice)
    # We save the average model or the best fold? For now, we just return the metrics.
    # If needed, we could pickle the models.
    
    return results

def main():
    parser = argparse.ArgumentParser(description="Train Random Forest models for molecular properties.")
    parser.add_argument("--semi-data", required=True, help="Path to semi-empirical descriptors CSV")
    parser.add_argument("--dft-data", required=True, help="Path to DFT descriptors CSV")
    parser.add_argument("--output", required=True, help="Path to output metrics CSV")
    
    args = parser.parse_args()
    
    try:
        train_models(args.semi_data, args.dft_data, args.output)
    except Exception as e:
        logger.error(f"Training failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()