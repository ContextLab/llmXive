"""
Train two Random Forest models (Semi-Empirical vs DFT) using k-fold cross-validation.
Implements locked split indices from T020b to ensure identical splits for paired t-test.
"""
import argparse
import csv
import json
import logging
import os
import sys
from pathlib import Path
from typing import List, Tuple, Dict, Any, Optional

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import KFold, cross_val_score
from sklearn.metrics import mean_absolute_error
from sklearn.preprocessing import StandardScaler

# Import utilities from project
from utils.logging_utils import setup_logger
from utils.error_utils import ConvergenceError, OOMError, StructuralError

# Constants
RANDOM_STATE = 42  # Fixed seed for reproducibility and locked splits
N_FOLDS = 5
OUTPUT_FILE = "data/train_results.json"
LOG_FILE = "logs/train_execution.log"

def setup_logger() -> logging.Logger:
    """Setup the logger for this module."""
    logger = logging.getLogger("train_models")
    logger.setLevel(logging.INFO)
    if not logger.handlers:
        handler = logging.FileHandler(LOG_FILE)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    return logger

def load_data_semi(filepath: str) -> Tuple[np.ndarray, np.ndarray, List[str]]:
    """Load semi-empirical descriptors and target."""
    logger = logging.getLogger("train_models")
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Semi-empirical descriptors file not found: {filepath}")
    
    df = pd.read_csv(filepath)
    required_cols = ['HOMO_energy', 'LUMO_energy', 'mayer_bond_order', 'molecule_id']
    if not all(col in df.columns for col in required_cols):
        raise ValueError(f"Semi-empirical file missing required columns. Found: {df.columns.tolist()}")
    
    # Features
    feature_cols = ['HOMO_energy', 'LUMO_energy', 'mayer_bond_order']
    X = df[feature_cols].values
    # Target is experimental_barrier from the raw data, but we need to merge or assume
    # Based on T020b, the descriptors are aligned with the raw dataset.
    # We assume the raw dataset is available or the target is already merged.
    # However, T020b generates descriptors_dft.csv and descriptors_semi.csv.
    # The target 'experimental_barrier' is in the raw data.
    # We must load the raw data to get the target for the specific molecules in the subset.
    # Let's assume the descriptor files contain 'molecule_id' and we join with raw data.
    # But the task says "using the locked split indices from T020b".
    # T020b generates `data/locked_splits.json` which contains the indices.
    # We need to load the raw data to get the target values.
    
    raw_path = "data/raw/barrier_dataset.csv"
    if not os.path.exists(raw_path):
        raise FileNotFoundError(f"Raw data file not found for target merging: {raw_path}")
    
    raw_df = pd.read_csv(raw_path)
    if 'experimental_barrier' not in raw_df.columns:
        raise ValueError("Raw data missing 'experimental_barrier' column")
    
    # Merge to get targets
    merged = df.merge(raw_df[['molecule_id', 'experimental_barrier']], on='molecule_id', how='inner')
    if len(merged) != len(df):
        logger.warning(f"Merged {len(merged)} rows from {len(df)} input rows. Some molecules missing targets.")
    
    X = merged[feature_cols].values
    y = merged['experimental_barrier'].values
    return X, y, feature_cols

def load_data_dft(filepath: str) -> Tuple[np.ndarray, np.ndarray, List[str]]:
    """Load DFT descriptors and target."""
    logger = logging.getLogger("train_models")
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"DFT descriptors file not found: {filepath}")
    
    df = pd.read_csv(filepath)
    required_cols = ['HOMO_energy', 'LUMO_energy', 'mayer_bond_order', 'molecule_id']
    if not all(col in df.columns for col in required_cols):
        raise ValueError(f"DFT file missing required columns. Found: {df.columns.tolist()}")
    
    feature_cols = ['HOMO_energy', 'LUMO_energy', 'mayer_bond_order']
    
    raw_path = "data/raw/barrier_dataset.csv"
    if not os.path.exists(raw_path):
        raise FileNotFoundError(f"Raw data file not found for target merging: {raw_path}")
    
    raw_df = pd.read_csv(raw_path)
    if 'experimental_barrier' not in raw_df.columns:
        raise ValueError("Raw data missing 'experimental_barrier' column")
    
    merged = df.merge(raw_df[['molecule_id', 'experimental_barrier']], on='molecule_id', how='inner')
    if len(merged) != len(df):
        logger.warning(f"Merged {len(merged)} rows from {len(df)} input rows. Some molecules missing targets.")
    
    X = merged[feature_cols].values
    y = merged['experimental_barrier'].values
    return X, y, feature_cols

def load_locked_splits(filepath: str) -> List[Tuple[np.ndarray, np.ndarray]]:
    """Load the locked split indices from T020b."""
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Locked splits file not found: {filepath}")
    
    with open(filepath, 'r') as f:
        data = json.load(f)
    
    splits = []
    for split_data in data['splits']:
        train_idx = np.array(split_data['train'])
        test_idx = np.array(split_data['test'])
        splits.append((train_idx, test_idx))
    
    return splits

def train_and_evaluate_fold(
    X: np.ndarray, 
    y: np.ndarray, 
    train_idx: np.ndarray, 
    test_idx: np.ndarray, 
    model_type: str
) -> Dict[str, float]:
    """Train a Random Forest on a specific fold and return MAE."""
    logger = logging.getLogger("train_models")
    
    X_train, X_test = X[train_idx], X[test_idx]
    y_train, y_test = y[train_idx], y[test_idx]
    
    # Standardize features
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)
    
    # Initialize model
    rf = RandomForestRegressor(
        n_estimators=100, 
        max_depth=None, 
        random_state=RANDOM_STATE,
        n_jobs=-1
    )
    
    try:
        rf.fit(X_train_scaled, y_train)
        y_pred = rf.predict(X_test_scaled)
        mae = mean_absolute_error(y_test, y_pred)
        
        logger.info(f"{model_type} Fold MAE: {mae:.4f}")
        
        return {
            "mae": float(mae),
            "model_type": model_type,
            "fold_size": len(test_idx)
        }
    except Exception as e:
        logger.error(f"Error training {model_type} fold: {e}")
        raise

def train_models(
    X_semi: np.ndarray, 
    y_semi: np.ndarray, 
    X_dft: np.ndarray, 
    y_dft: np.ndarray, 
    splits: List[Tuple[np.ndarray, np.ndarray]]
) -> Dict[str, Any]:
    """Train models on all locked splits and aggregate results."""
    logger = logging.getLogger("train_models")
    
    semi_results = []
    dft_results = []
    
    logger.info(f"Starting training with {len(splits)} locked folds.")
    
    for i, (train_idx, test_idx) in enumerate(splits):
        logger.info(f"Processing Fold {i+1}/{len(splits)}")
        
        # Train Semi-Empirical
        try:
            semi_res = train_and_evaluate_fold(X_semi, y_semi, train_idx, test_idx, "Semi-Empirical")
            semi_results.append(semi_res['mae'])
        except Exception as e:
            logger.error(f"Failed Semi-Empirical fold {i}: {e}")
            continue
        
        # Train DFT
        try:
            dft_res = train_and_evaluate_fold(X_dft, y_dft, train_idx, test_idx, "DFT")
            dft_results.append(dft_res['mae'])
        except Exception as e:
            logger.error(f"Failed DFT fold {i}: {e}")
            continue
    
    if not semi_results or not dft_results:
        raise RuntimeError("Failed to train at least one complete model.")
    
    avg_mae_semi = np.mean(semi_results)
    avg_mae_dft = np.mean(dft_results)
    
    results = {
        "n_folds": len(splits),
        "mae_semi": {
            "mean": float(avg_mae_semi),
            "std": float(np.std(semi_results)),
            "per_fold": semi_results
        },
        "mae_dft": {
            "mean": float(avg_mae_dft),
            "std": float(np.std(dft_results)),
            "per_fold": dft_results
        },
        "random_state": RANDOM_STATE,
        "model_config": {
            "n_estimators": 100,
            "max_depth": None,
            "random_state": RANDOM_STATE
        }
    }
    
    return results

def main():
    """Main entry point for training models."""
    logger = setup_logger()
    logger.info("Starting model training (T021)")
    
    try:
        # Load data
        semi_path = "data/descriptors_semi.csv"
        dft_path = "data/descriptors_dft.csv"
        splits_path = "data/locked_splits.json"
        
        logger.info(f"Loading Semi-Empirical data from {semi_path}")
        X_semi, y_semi, _ = load_data_semi(semi_path)
        
        logger.info(f"Loading DFT data from {dft_path}")
        X_dft, y_dft, _ = load_data_dft(dft_path)
        
        logger.info(f"Loading locked splits from {splits_path}")
        splits = load_locked_splits(splits_path)
        
        # Verify split consistency
        if len(X_semi) != len(y_semi) or len(X_dft) != len(y_dft):
            raise ValueError("Data and target length mismatch.")
        
        # Train models
        results = train_models(X_semi, y_semi, X_dft, y_dft, splits)
        
        # Save results
        output_dir = Path("reports")
        output_dir.mkdir(exist_ok=True)
        output_file = output_dir / "model_training_results.json"
        
        with open(output_file, 'w') as f:
            json.dump(results, f, indent=2)
        
        logger.info(f"Training complete. Results saved to {output_file}")
        print(f"Training complete. MAE Semi-Empirical: {results['mae_semi']['mean']:.4f}, MAE DFT: {results['mae_dft']['mean']:.4f}")
        
    except Exception as e:
        logger.error(f"Training failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()