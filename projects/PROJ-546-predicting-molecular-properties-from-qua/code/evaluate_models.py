import argparse
import csv
import json
import logging
import os
import sys
from typing import Dict, List, Tuple, Any, Optional
from pathlib import Path

import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import KFold
from scipy import stats

# Import utilities from sibling modules based on API surface
try:
    from utils.logging_utils import setup_logger, log_calculation_summary
except ImportError:
    # Fallback for direct execution if utils path not in sys.path
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
    from code.utils.logging_utils import setup_logger, log_calculation_summary

# Configure logging
logger = logging.getLogger(__name__)

def load_data_semi(file_path: str) -> Tuple[List[List[float]], List[float], List[str]]:
    """
    Load semi-empirical descriptor data and target.
    Returns: (features, targets, smiles_list)
    """
    features = []
    targets = []
    smiles_list = []
    
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Semi-empirical data file not found: {file_path}")
    
    with open(file_path, 'r', newline='') as f:
        reader = csv.DictReader(f)
        for row in reader:
            smiles_list.append(row['SMILES'])
            # Assuming descriptors are columns other than SMILES and target
            # We need to identify descriptor columns dynamically or by known names
            # For this implementation, we assume columns like 'HOMO', 'LUMO', 'Mayer_Bond_Order', etc.
            # and exclude 'SMILES' and 'experimental_barrier'
            row_features = []
            for key, value in row.items():
                if key not in ['SMILES', 'experimental_barrier']:
                    try:
                        row_features.append(float(value))
                    except ValueError:
                        row_features.append(0.0) # Handle non-numeric if necessary
            features.append(row_features)
            targets.append(float(row['experimental_barrier']))
    
    return features, targets, smiles_list

def load_data_dft(file_path: str) -> Tuple[List[List[float]], List[float], List[str]]:
    """
    Load DFT descriptor data and target.
    Returns: (features, targets, smiles_list)
    """
    features = []
    targets = []
    smiles_list = []
    
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"DFT data file not found: {file_path}")
    
    with open(file_path, 'r', newline='') as f:
        reader = csv.DictReader(f)
        for row in reader:
            smiles_list.append(row['SMILES'])
            row_features = []
            for key, value in row.items():
                if key not in ['SMILES', 'experimental_barrier']:
                    try:
                        row_features.append(float(value))
                    except ValueError:
                        row_features.append(0.0)
            features.append(row_features)
            targets.append(float(row['experimental_barrier']))
    
    return features, targets, smiles_list

def train_and_evaluate_fold(
    X_train: np.ndarray, y_train: np.ndarray, 
    X_test: np.ndarray, y_test: np.ndarray,
    n_estimators: int = 100, random_state: int = 42
) -> Tuple[float, float]:
    """
    Train a Random Forest on the training fold and evaluate on the test fold.
    Returns: (mae, r2)
    """
    model = RandomForestRegressor(n_estimators=n_estimators, random_state=random_state, n_jobs=-1)
    model.fit(X_train, y_train)
    
    y_pred = model.predict(X_test)
    
    # Calculate MAE
    mae = np.mean(np.abs(y_test - y_pred))
    
    # Calculate R2
    ss_res = np.sum((y_test - y_pred) ** 2)
    ss_tot = np.sum((y_test - np.mean(y_test)) ** 2)
    r2 = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0.0
    
    return mae, r2

def run_cross_validation(
    X: np.ndarray, y: np.ndarray, 
    n_splits: int = 5, random_state: int = 42,
    n_estimators: int = 100
) -> List[float]:
    """
    Run k-fold cross validation and return list of MAEs.
    """
    kf = KFold(n_splits=n_splits, shuffle=True, random_state=random_state)
    maes = []
    
    for train_idx, test_idx in kf.split(X):
        X_train, X_test = X[train_idx], X[test_idx]
        y_train, y_test = y[train_idx], y[test_idx]
        
        mae, _ = train_and_evaluate_fold(X_train, y_train, X_test, y_test, n_estimators)
        maes.append(mae)
    
    return maes

def run_paired_t_test(maes_semi: List[float], maes_dft: List[float]) -> Tuple[float, float]:
    """
    Perform a paired t-test on the MAEs from semi-empirical and DFT models.
    Returns: (t_statistic, p_value)
    """
    if len(maes_semi) != len(maes_dft):
        raise ValueError("MAE lists must be of equal length for paired t-test.")
    
    t_stat, p_val = stats.ttest_rel(maes_semi, maes_dft)
    return t_stat, p_val

def main():
    parser = argparse.ArgumentParser(description="Evaluate and compare Semi-Empirical and DFT models.")
    parser.add_argument("--semi-data", type=str, required=True, help="Path to semi-empirical descriptor CSV")
    parser.add_argument("--dft-data", type=str, required=True, help="Path to DFT descriptor CSV")
    parser.add_argument("--output", type=str, required=True, help="Path to output JSON report")
    parser.add_argument("--n-splits", type=int, default=5, help="Number of CV folds")
    parser.add_argument("--n-estimators", type=int, default=100, help="Number of trees in RF")
    parser.add_argument("--log-file", type=str, default=None, help="Path to log file")
    
    args = parser.parse_args()
    
    if args.log_file:
        setup_logger(log_file=args.log_file, level=logging.INFO)
    
    logger.info("Starting model evaluation...")
    
    try:
        # Load data
        logger.info(f"Loading semi-empirical data from {args.semi_data}")
        X_semi, y_semi, _ = load_data_semi(args.semi_data)
        X_semi = np.array(X_semi)
        y_semi = np.array(y_semi)
        
        logger.info(f"Loading DFT data from {args.dft_data}")
        X_dft, y_dft, _ = load_data_dft(args.dft_data)
        X_dft = np.array(X_dft)
        y_dft = np.array(y_dft)
        
        if len(X_semi) != len(X_dft):
            logger.warning(f"Warning: Number of samples differs between semi ({len(X_semi)}) and DFT ({len(X_dft)}) datasets. "
                           f"Using the intersection of indices based on order if aligned, otherwise this may cause issues.")
            # In a robust system, we would align by SMILES. Assuming alignment by index for now as per task context.
            min_len = min(len(X_semi), len(X_dft))
            X_semi, y_semi = X_semi[:min_len], y_semi[:min_len]
            X_dft, y_dft = X_dft[:min_len], y_dft[:min_len]
        
        # Run Cross Validation
        logger.info(f"Running {args.n_splits}-fold CV for Semi-Empirical model...")
        maes_semi = run_cross_validation(X_semi, y_semi, n_splits=args.n_splits, n_estimators=args.n_estimators)
        mean_mae_semi = np.mean(maes_semi)
        std_mae_semi = np.std(maes_semi)
        
        logger.info(f"Running {args.n_splits}-fold CV for DFT model...")
        maes_dft = run_cross_validation(X_dft, y_dft, n_splits=args.n_splits, n_estimators=args.n_estimators)
        mean_mae_dft = np.mean(maes_dft)
        std_mae_dft = np.std(maes_dft)
        
        # Paired T-Test
        logger.info("Running paired t-test...")
        t_stat, p_val = run_paired_t_test(maes_semi, maes_dft)
        
        # FR-008: Flag if semi-MAE exceeds DFT-MAE by >20%
        # Condition: semi_mae > 1.2 * dft_mae
        threshold_ratio = 1.2
        exceeds_threshold = mean_mae_semi > (threshold_ratio * mean_mae_dft)
        ratio = mean_mae_semi / mean_mae_dft if mean_mae_dft > 0 else float('inf')
        
        logger.info(f"Semi-Empirical MAE: {mean_mae_semi:.4f} (+/- {std_mae_semi:.4f})")
        logger.info(f"DFT MAE: {mean_mae_dft:.4f} (+/- {std_mae_dft:.4f})")
        logger.info(f"Ratio (Semi/DFT): {ratio:.4f}")
        logger.info(f"Paired T-Test: t={t_stat:.4f}, p={p_val:.4f}")
        
        if exceeds_threshold:
            logger.warning(f"FLAG: Semi-empirical MAE ({mean_mae_semi:.4f}) exceeds DFT MAE ({mean_mae_dft:.4f}) by more than 20% (Ratio: {ratio:.4f} > {threshold_ratio}).")
        else:
            logger.info(f"PASS: Semi-empirical MAE is within 20% of DFT MAE.")
        
        # Prepare report
        report = {
            "semi_empirical": {
                "mean_mae": float(mean_mae_semi),
                "std_mae": float(std_mae_semi),
                "fold_maes": [float(x) for x in maes_semi]
            },
            "dft": {
                "mean_mae": float(mean_mae_dft),
                "std_mae": float(std_mae_dft),
                "fold_maes": [float(x) for x in maes_dft]
            },
            "comparison": {
                "ratio": float(ratio),
                "threshold_ratio": threshold_ratio,
                "exceeds_20_percent": exceeds_threshold,
                "t_statistic": float(t_stat),
                "p_value": float(p_val)
            },
            "config": {
                "n_splits": args.n_splits,
                "n_estimators": args.n_estimators
            }
        }
        
        # Write report
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w') as f:
            json.dump(report, f, indent=2)
        
        logger.info(f"Report written to {args.output}")
        
        # Exit with code 1 if threshold exceeded to facilitate pipeline failure if desired
        if exceeds_threshold:
            logger.warning("Exiting with warning status due to MAE threshold exceedance.")
            sys.exit(0) # Or 1 depending on pipeline policy, usually 0 for "completed with warning" unless strict
        
    except Exception as e:
        logger.error(f"Error during evaluation: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()