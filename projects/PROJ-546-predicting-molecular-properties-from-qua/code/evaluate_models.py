"""
evaluate_models.py

Implements the evaluation of Semi-Empirical vs DFT Random Forest models.
Computes per-fold MAE, runs a paired t-test, and writes results to reports/evaluation.json.
"""
import argparse
import csv
import json
import logging
import os
import sys
from pathlib import Path
from typing import List, Dict, Any, Tuple

import numpy as np
from scipy import stats
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import KFold

# Import shared utilities if available, otherwise define minimal logger
try:
    from utils.logging_utils import setup_logger
except ImportError:
    def setup_logger(name: str, log_file: str = None, level=logging.INFO) -> logging.Logger:
        logger = logging.getLogger(name)
        logger.setLevel(level)
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        if log_file:
            fh = logging.FileHandler(log_file)
            fh.setFormatter(formatter)
            logger.addHandler(fh)
        return logger

logger = setup_logger("evaluate_models", "logs/evaluation.log")

def load_data_semi(csv_path: str) -> Tuple[np.ndarray, np.ndarray, List[str]]:
    """
    Load semi-empirical descriptors and target from CSV.
    Returns (X, y, feature_names).
    """
    features = []
    targets = []
    feature_names = []
    
    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"Semi-empirical data file not found: {csv_path}")

    with open(csv_path, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        header = reader.fieldnames
        
        # Identify target column (expected: 'experimental_barrier')
        target_col = 'experimental_barrier'
        if target_col not in header:
            raise ValueError(f"Target column '{target_col}' not found in {csv_path}. Headers: {header}")
        
        feature_names = [h for h in header if h != target_col]
        
        for row in reader:
            try:
                x_row = [float(row[f]) for f in feature_names]
                y_val = float(row[target_col])
                features.append(x_row)
                targets.append(y_val)
            except (ValueError, TypeError) as e:
                logger.warning(f"Skipping row due to parsing error: {e}")
                continue

    if len(features) == 0:
        raise ValueError("No valid data rows found in semi-empirical CSV.")
        
    return np.array(features), np.array(targets), feature_names

def load_data_dft(csv_path: str) -> Tuple[np.ndarray, np.ndarray]:
    """
    Load DFT descriptors and target from CSV.
    Returns (X, y).
    """
    features = []
    targets = []
    
    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"DFT data file not found: {csv_path}")

    with open(csv_path, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        header = reader.fieldnames
        
        target_col = 'experimental_barrier'
        if target_col not in header:
            raise ValueError(f"Target column '{target_col}' not found in {csv_path}. Headers: {header}")
        
        feature_names = [h for h in header if h != target_col]

        for row in reader:
            try:
                x_row = [float(row[f]) for f in feature_names]
                y_val = float(row[target_col])
                features.append(x_row)
                targets.append(y_val)
            except (ValueError, TypeError) as e:
                logger.warning(f"Skipping row due to parsing error: {e}")
                continue

    if len(features) == 0:
        raise ValueError("No valid data rows found in DFT CSV.")
        
    return np.array(features), np.array(targets)

def train_and_evaluate_fold(
    X_train: np.ndarray, y_train: np.ndarray,
    X_test: np.ndarray, y_test: np.ndarray,
    random_state: int
) -> float:
    """
    Train a Random Forest on the training split and return MAE on the test split.
    """
    model = RandomForestRegressor(
        n_estimators=100,
        max_depth=None,
        random_state=random_state,
        n_jobs=1
    )
    model.fit(X_train, y_train)
    predictions = model.predict(X_test)
    
    mae = np.mean(np.abs(predictions - y_test))
    return mae

def run_cross_validation(
    X: np.ndarray, y: np.ndarray, n_splits: int = 5, random_state: int = 42
) -> List[float]:
    """
    Perform k-fold cross-validation and return a list of MAE scores (one per fold).
    """
    kf = KFold(n_splits=n_splits, shuffle=True, random_state=random_state)
    maes = []
    
    logger.info(f"Running {n_splits}-fold cross-validation...")
    
    for fold_idx, (train_idx, test_idx) in enumerate(kf.split(X)):
        X_train, X_test = X[train_idx], X[test_idx]
        y_train, y_test = y[train_idx], y[test_idx]
        
        fold_mae = train_and_evaluate_fold(X_train, y_train, X_test, y_test, random_state)
        maes.append(fold_mae)
        logger.info(f"Fold {fold_idx + 1}/{n_splits}: MAE = {fold_mae:.4f}")
        
    return maes

def run_paired_t_test(semi_maes: List[float], dft_maes: List[float]) -> Dict[str, Any]:
    """
    Perform a paired t-test between Semi-Empirical and DFT MAE lists.
    Returns a dictionary with test statistics.
    """
    if len(semi_maes) != len(dft_maes):
        raise ValueError("MAE lists must have the same length for paired t-test.")
    
    t_statistic, p_value = stats.ttest_rel(semi_maes, dft_maes)
    
    result = {
        "statistic": float(t_statistic),
        "p_value": float(p_value),
        "null_hypothesis": "The mean difference between Semi-Empirical and DFT MAE is zero.",
        "significance_level": 0.05,
        "models_compared": ["RandomForest_SemiEmpirical", "RandomForest_DFT"]
    }
    
    logger.info(f"T-statistic: {t_statistic:.4f}, P-value: {p_value:.4f}")
    if p_value < 0.05:
        logger.info("Result: Reject null hypothesis (significant difference).")
    else:
        logger.info("Result: Fail to reject null hypothesis (no significant difference).")
        
    return result

def verify_mae_threshold(mae_semi: float, mae_dft: float, threshold_pct: float = 20.0) -> bool:
    """
    Check if Semi-Empirical MAE exceeds DFT MAE by more than threshold_pct.
    Returns True if the flag condition is met (i.e., semi is worse by > X%).
    """
    if mae_dft == 0:
        return mae_semi > 0
    
    relative_diff = (mae_semi - mae_dft) / mae_dft * 100.0
    return relative_diff > threshold_pct

def main():
    parser = argparse.ArgumentParser(description="Evaluate Semi-Empirical vs DFT Models")
    parser.add_argument("--semi-csv", type=str, default="data/descriptors_semi.csv",
                        help="Path to semi-empirical descriptors CSV")
    parser.add_argument("--dft-csv", type=str, default="data/descriptors_dft.csv",
                        help="Path to DFT descriptors CSV")
    parser.add_argument("--output", type=str, default="reports/evaluation.json",
                        help="Path to output JSON report")
    parser.add_argument("--n-splits", type=int, default=5,
                        help="Number of CV folds")
    parser.add_argument("--random-state", type=int, default=42,
                        help="Random seed for reproducibility")
    args = parser.parse_args()

    # Ensure output directory exists
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    logger.info("Loading Semi-Empirical data...")
    try:
        X_semi, y_semi, feature_names = load_data_semi(args.semi_csv)
    except Exception as e:
        logger.error(f"Failed to load semi-empirical data: {e}")
        sys.exit(1)

    logger.info("Loading DFT data...")
    try:
        X_dft, y_dft = load_data_dft(args.dft_csv)
    except Exception as e:
        logger.error(f"Failed to load DFT data: {e}")
        sys.exit(1)

    # Verify alignment (same number of samples)
    if X_semi.shape[0] != X_dft.shape[0]:
        logger.error(f"Sample count mismatch: Semi={X_semi.shape[0]}, DFT={X_dft.shape[0]}")
        sys.exit(1)
    
    # Verify target alignment (same y values)
    if not np.allclose(y_semi, y_dft):
        logger.warning("Target values (y) are not identical between datasets. Proceeding with caution.")
    
    # Run Cross Validation
    logger.info("Evaluating Semi-Empirical Model...")
    semi_maes = run_cross_validation(X_semi, y_semi, n_splits=args.n_splits, random_state=args.random_state)
    
    logger.info("Evaluating DFT Model...")
    dft_maes = run_cross_validation(X_dft, y_dft, n_splits=args.n_splits, random_state=args.random_state)

    # Aggregate metrics
    mae_semi_mean = float(np.mean(semi_maes))
    mae_dft_mean = float(np.mean(dft_maes))
    
    logger.info(f"Mean Semi-Empirical MAE: {mae_semi_mean:.4f}")
    logger.info(f"Mean DFT MAE: {mae_dft_mean:.4f}")

    # Run Paired T-Test
    t_test_results = run_paired_t_test(semi_maes, dft_maes)

    # Check Threshold Flag
    flag_exceeds = verify_mae_threshold(mae_semi_mean, mae_dft_mean)
    
    # Construct Output
    report = {
        "mae_semi": mae_semi_mean,
        "mae_dft": mae_dft_mean,
        "mae_semi_per_fold": semi_maes,
        "mae_dft_per_fold": dft_maes,
        "t_test": t_test_results,
        "flags": {
            "semi_exceeds_dft_by_20pct": flag_exceeds
        },
        "metadata": {
            "n_samples": int(X_semi.shape[0]),
            "n_splits": args.n_splits,
            "random_state": args.random_state,
            "feature_count": len(feature_names)
        }
    }

    # Write JSON
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2)
    
    logger.info(f"Evaluation complete. Report written to {output_path}")

if __name__ == "__main__":
    main()