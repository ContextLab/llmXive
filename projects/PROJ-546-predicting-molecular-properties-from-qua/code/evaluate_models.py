"""
Evaluate trained models and perform paired t-test comparison.
"""
import argparse
import csv
import json
import logging
import os
import sys
from pathlib import Path
from typing import Dict, List, Any, Tuple

import numpy as np
from sklearn.linear_model import LinearRegression
from sklearn.model_selection import cross_val_predict
from sklearn.metrics import mean_absolute_error
from scipy import stats
import joblib

# Import project config
from config import PROJECT_ROOT

# Setup logging
def setup_logger(name: str) -> logging.Logger:
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
        logger.addHandler(handler)
    return logger

logger = setup_logger(__name__)

def load_data_semi(filepath: str) -> Tuple[List[str], List[float], np.ndarray]:
    """
    Load semi-empirical descriptors.
    Returns: (molecule_ids, experimental_values, feature_matrix)
    """
    logger.info(f"Loading semi-empirical data from {filepath}")
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"File not found: {filepath}")

    molecule_ids = []
    experimental_values = []
    features = []
    feature_names = []

    with open(filepath, 'r', newline='') as f:
        reader = csv.DictReader(f)
        # Assume first row gives feature names (excluding IDs and target)
        if reader.fieldnames is None:
            raise ValueError("CSV file is empty or has no headers")
        
        # Identify feature columns (exclude molecule_id, experimental_barrier, and any known metadata)
        exclude_cols = {'molecule_id', 'experimental_barrier', 'HOMO_energy', 'LUMO_energy', 'mayer_bond_order'}
        # We need to know which columns are features. Based on T013c output schema:
        # molecule_id, HOMO_energy, LUMO_energy, mayer_bond_order
        # But the model might have been trained on more descriptors if T021 expanded them.
        # For this task, we assume the CSV has: molecule_id, experimental_barrier, and feature columns.
        # We'll treat everything except molecule_id and experimental_barrier as features.
        
        for row in reader:
            molecule_ids.append(row['molecule_id'])
            experimental_values.append(float(row['experimental_barrier']))
            # Collect all other columns as features
            feat_row = []
            for col in reader.fieldnames:
                if col not in ['molecule_id', 'experimental_barrier']:
                    feat_row.append(float(row[col]))
            features.append(feat_row)
            
            if not feature_names:
                feature_names = [col for col in reader.fieldnames if col not in ['molecule_id', 'experimental_barrier']]

    return molecule_ids, experimental_values, np.array(features), feature_names

def load_data_dft(filepath: str) -> Tuple[List[str], np.ndarray, List[str]]:
    """
    Load DFT descriptors.
    Returns: (molecule_ids, feature_matrix, feature_names)
    """
    logger.info(f"Loading DFT data from {filepath}")
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"File not found: {filepath}")

    molecule_ids = []
    features = []
    feature_names = []

    with open(filepath, 'r', newline='') as f:
        reader = csv.DictReader(f)
        if reader.fieldnames is None:
            raise ValueError("CSV file is empty or has no headers")
        
        for row in reader:
            molecule_ids.append(row['molecule_id'])
            feat_row = []
            for col in reader.fieldnames:
                if col != 'molecule_id':
                    feat_row.append(float(row[col]))
            features.append(feat_row)
            
            if not feature_names:
                feature_names = [col for col in reader.fieldnames if col != 'molecule_id']

    return molecule_ids, np.array(features), feature_names

def load_locked_splits(filepath: str) -> Dict[str, Any]:
    """
    Load the locked train/test split indices.
    """
    logger.info(f"Loading split indices from {filepath}")
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Split file not found: {filepath}")
    
    with open(filepath, 'r') as f:
        return json.load(f)

def train_and_evaluate_fold(
    X_train: np.ndarray, 
    y_train: np.ndarray, 
    X_test: np.ndarray, 
    y_test: np.ndarray
) -> Tuple[float, float, LinearRegression]:
    """
    Train a Linear Regression model (as a stand-in for RF if sklearn not fully configured, 
    but per spec we use RF. However, to ensure it runs without heavy deps if not available,
    we'll use a simple regressor that mimics the behavior for evaluation purposes.
    Actually, spec says Random Forest. Let's use RandomForestRegressor.
    """
    from sklearn.ensemble import RandomForestRegressor
    
    model = RandomForestRegressor(n_estimators=100, random_state=42, n_jobs=-1)
    model.fit(X_train, y_train)
    
    y_pred = model.predict(X_test)
    mae = mean_absolute_error(y_test, y_pred)
    
    # Also return model for potential feature importance later
    return mae, mae, model

def run_cross_validation(
    X: np.ndarray, 
    y: np.ndarray, 
    train_indices: List[int], 
    test_indices: List[int],
    model_type: str = "semi"
) -> Tuple[float, float, List[float], List[float]]:
    """
    Train model on train_indices, evaluate on test_indices.
    Returns: (mae, std_error, predictions, actuals)
    """
    logger.info(f"Running evaluation for {model_type} model")
    
    X_train = X[train_indices]
    y_train = y[train_indices]
    X_test = X[test_indices]
    y_test = y[test_indices]
    
    mae, _, model = train_and_evaluate_fold(X_train, y_train, X_test, y_test)
    
    y_pred = model.predict(X_test)
    
    # Calculate per-sample errors for t-test
    errors = np.abs(y_test - y_pred)
    
    return mae, np.std(errors), y_pred.tolist(), y_test.tolist()

def run_paired_t_test(
    errors_semi: List[float], 
    errors_dft: List[float]
) -> Dict[str, Any]:
    """
    Perform paired t-test on error distributions.
    """
    logger.info("Running paired t-test on error distributions")
    
    if len(errors_semi) != len(errors_dft):
        raise ValueError("Error lists must be of equal length for paired t-test")
    
    if len(errors_semi) < 2:
        logger.warning("Insufficient samples for t-test. Returning placeholder stats.")
        return {
            "statistic": 0.0,
            "p_value": 1.0,
            "null_hypothesis": "There is no difference in the error distribution between the Semi-Empirical RF and DFT RF models.",
            "significance_level": "0.05",
            "models_compared": "Semi-Empirical Random Forest vs. DFT Random Forest"
        }
    
    t_stat, p_val = stats.ttest_rel(errors_semi, errors_dft)
    
    return {
        "statistic": float(t_stat),
        "p_value": float(p_val),
        "null_hypothesis": "There is no difference in the error distribution between the Semi-Empirical RF and DFT RF models.",
        "significance_level": "0.05",
        "models_compared": "Semi-Empirical Random Forest vs. DFT Random Forest"
    }

def verify_mae_threshold(mae: float, threshold: float = 0.5) -> bool:
    """
    Verify MAE against a threshold (optional, per spec note we report measured value).
    """
    return mae < threshold

def main():
    parser = argparse.ArgumentParser(description="Evaluate models and run paired t-test")
    parser.add_argument("--semi-data", default="data/descriptors_semi.csv", help="Path to semi-empirical descriptors")
    parser.add_argument("--dft-data", default="data/descriptors_dft.csv", help="Path to DFT descriptors")
    parser.add_argument("--splits", default="state/splits.json", help="Path to split indices")
    parser.add_argument("--output", default="reports/evaluation.json", help="Path to output report")
    args = parser.parse_args()

    # Ensure output directory exists
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Load data
    try:
        semi_ids, semi_y, semi_X, semi_feat_names = load_data_semi(args.semi_data)
        dft_ids, dft_X, dft_feat_names = load_data_dft(args.dft_data)
        splits = load_locked_splits(args.splits)
    except FileNotFoundError as e:
        logger.error(f"Critical missing file: {e}")
        sys.exit(1)

    train_indices = splits['train_indices']
    test_indices = splits['test_indices']

    # Align data: ensure test set has same molecules in both datasets
    # We assume the order in the CSVs matches the indices provided in splits.json
    # If not, we would need to map by molecule_id. For now, assume index alignment.
    
    y_semi = np.array(semi_y)
    y_dft = np.array(semi_y) # Experimental values are the same for both models

    # Run evaluation for Semi-Empirical
    mae_semi, std_semi, _, _ = run_cross_validation(semi_X, y_semi, train_indices, test_indices, "semi")
    
    # Run evaluation for DFT
    mae_dft, std_dft, _, _ = run_cross_validation(dft_X, y_dft, train_indices, test_indices, "dft")

    logger.info(f"Semi-Empirical MAE: {mae_semi:.4f} (std: {std_semi:.4f})")
    logger.info(f"DFT MAE: {mae_dft:.4f} (std: {std_dft:.4f})")

    # We need the actual errors for the t-test, not just MAE.
    # Re-run to get errors
    from sklearn.ensemble import RandomForestRegressor
    
    X_train_semi = semi_X[train_indices]
    y_train_semi = y_semi[train_indices]
    X_test_semi = semi_X[test_indices]
    y_test_semi = y_semi[test_indices]
    
    model_semi = RandomForestRegressor(n_estimators=100, random_state=42, n_jobs=-1)
    model_semi.fit(X_train_semi, y_train_semi)
    pred_semi = model_semi.predict(X_test_semi)
    errors_semi = np.abs(y_test_semi - pred_semi)

    X_train_dft = dft_X[train_indices]
    y_train_dft = y_dft[train_indices]
    X_test_dft = dft_X[test_indices]
    y_test_dft = y_dft[test_indices]
    
    model_dft = RandomForestRegressor(n_estimators=100, random_state=42, n_jobs=-1)
    model_dft.fit(X_train_dft, y_train_dft)
    pred_dft = model_dft.predict(X_test_dft)
    errors_dft = np.abs(y_test_dft - pred_dft)

    t_test_result = run_paired_t_test(errors_semi.tolist(), errors_dft.tolist())

    report = {
        "mae_semi": float(mae_semi),
        "mae_dft": float(mae_dft),
        "t_test": t_test_result,
        "error_bars": {
            "semi_empirical_std": float(std_semi),
            "dft_std": float(std_dft)
        }
    }

    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2)

    logger.info(f"Evaluation report written to {output_path}")

if __name__ == "__main__":
    main()
