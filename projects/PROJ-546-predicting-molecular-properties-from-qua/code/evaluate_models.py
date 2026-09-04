"""
evaluate_models.py

Computes per-fold MAE for Semi-Empirical and DFT Random Forest models,
runs a paired t-test to compare their performance, and reports results.

Output:
    reports/evaluation.json
        {
            "mae_semi": float,
            "mae_dft": float,
            "t_test": {
                "statistic": float,
                "p_value": float,
                "null_hypothesis": str,
                "significance_level": float,
                "models_compared": list
            }
        }
"""
import argparse
import csv
import json
import logging
import os
import sys
from pathlib import Path
from typing import List, Tuple, Dict, Any

import numpy as np
from scipy import stats
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error
from sklearn.model_selection import StratifiedKFold

# Import local utilities
# We assume logging_utils exists based on the API surface provided
try:
    from utils.logging_utils import setup_logger
except ImportError:
    # Fallback for direct execution if path isn't set
    import logging
    def setup_logger(name, log_file, level=logging.INFO):
        logger = logging.getLogger(name)
        logger.setLevel(level)
        fh = logging.FileHandler(log_file)
        fh.setLevel(level)
        ch = logging.StreamHandler()
        ch.setLevel(level)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        fh.setFormatter(formatter)
        ch.setFormatter(formatter)
        logger.addHandler(fh)
        logger.addHandler(ch)
        return logger


LOG_FILE = "logs/evaluation.log"
REPORT_FILE = "reports/evaluation.json"
DATA_SEMI = "data/descriptors_semi.csv"
DATA_DFT = "data/descriptors_dft.csv"
LOCKED_SPLITS = "data/locked_splits.json"
TARGET_COLUMN = "experimental_barrier"


def load_data_semi(filepath: str) -> Tuple[np.ndarray, np.ndarray]:
    """
    Load semi-empirical descriptors and target.
    Returns: (features, target)
    """
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Semi-empirical data file not found: {filepath}")

    features = []
    targets = []
    with open(filepath, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Expect columns: molecule_id, HOMO_energy, LUMO_energy, mayer_bond_order
            # We assume numeric columns are features
            feat_row = []
            for k, v in row.items():
                if k == 'molecule_id':
                    continue
                try:
                    feat_row.append(float(v))
                except ValueError:
                    continue
            features.append(feat_row)
            targets.append(float(row[TARGET_COLUMN]))

    return np.array(features), np.array(targets)


def load_data_dft(filepath: str) -> Tuple[np.ndarray, np.ndarray]:
    """
    Load DFT descriptors and target.
    Returns: (features, target)
    """
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"DFT data file not found: {filepath}")

    features = []
    targets = []
    with open(filepath, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            feat_row = []
            for k, v in row.items():
                if k == 'molecule_id':
                    continue
                try:
                    feat_row.append(float(v))
                except ValueError:
                    continue
            features.append(feat_row)
            targets.append(float(row[TARGET_COLUMN]))

    return np.array(features), np.array(targets)


def load_locked_splits(filepath: str) -> List[Tuple[List[int], List[int]]]:
    """
    Load locked splits from JSON.
    Returns: List of (train_indices, test_indices)
    """
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Locked splits file not found: {filepath}")

    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)

    splits = []
    for fold in data:
        train = fold['train']
        test = fold['test']
        splits.append((train, test))

    return splits


def train_and_evaluate_fold(
    X_train: np.ndarray,
    y_train: np.ndarray,
    X_test: np.ndarray,
    y_test: np.ndarray,
    random_state: int = 42
) -> float:
    """
    Train a Random Forest and return MAE on the test set.
    """
    model = RandomForestRegressor(
        n_estimators=100,
        random_state=random_state,
        n_jobs=-1
    )
    model.fit(X_train, y_train)
    predictions = model.predict(X_test)
    mae = mean_absolute_error(y_test, predictions)
    return mae


def run_cross_validation(
    X: np.ndarray,
    y: np.ndarray,
    locked_splits: List[Tuple[List[int], List[int]]]
) -> List[float]:
    """
    Run cross-validation using locked splits.
    Returns: List of MAE scores per fold.
    """
    mae_scores = []
    for train_idx, test_idx in locked_splits:
        X_train, X_test = X[train_idx], X[test_idx]
        y_train, y_test = y[train_idx], y[test_idx]

        fold_mae = train_and_evaluate_fold(X_train, y_train, X_test, y_test)
        mae_scores.append(fold_mae)

    return mae_scores


def run_paired_t_test(
    mae_semi: List[float],
    mae_dft: List[float],
    significance_level: float = 0.05
) -> Dict[str, Any]:
    """
    Perform a paired t-test between Semi-Empirical and DFT MAE scores.
    """
    statistic, p_value = stats.ttest_rel(mae_semi, mae_dft)

    return {
        "statistic": float(statistic),
        "p_value": float(p_value),
        "null_hypothesis": "There is no difference in mean MAE between Semi-Empirical and DFT models.",
        "significance_level": significance_level,
        "models_compared": ["Semi-Empirical", "DFT"]
    }


def verify_mae_threshold(mae: float, threshold: float) -> bool:
    """
    Verify if MAE is below a threshold (optional check).
    Note: Task T022 explicitly says DO NOT verify against a fixed threshold for the final report,
    but this function is kept for internal logic if needed elsewhere.
    """
    return mae < threshold


def main():
    parser = argparse.ArgumentParser(description="Evaluate Semi-Empirical vs DFT Models")
    parser.add_argument('--semi-data', type=str, default=DATA_SEMI, help='Path to semi-empirical CSV')
    parser.add_argument('--dft-data', type=str, default=DATA_DFT, help='Path to DFT CSV')
    parser.add_argument('--splits', type=str, default=LOCKED_SPLITS, help='Path to locked splits JSON')
    parser.add_argument('--report', type=str, default=REPORT_FILE, help='Path to output JSON report')
    parser.add_argument('--log', type=str, default=LOG_FILE, help='Path to log file')
    args = parser.parse_args()

    # Ensure log directory exists
    log_dir = os.path.dirname(args.log)
    if log_dir and not os.path.exists(log_dir):
        os.makedirs(log_dir)

    logger = setup_logger("evaluate_models", args.log)
    logger.info("Starting model evaluation.")

    try:
        # Load Data
        logger.info(f"Loading semi-empirical data from {args.semi_data}")
        X_semi, y_semi = load_data_semi(args.semi_data)
        logger.info(f"Loaded {len(y_semi)} samples (Semi-Empirical)")

        logger.info(f"Loading DFT data from {args.dft_data}")
        X_dft, y_dft = load_data_dft(args.dft_data)
        logger.info(f"Loaded {len(y_dft)} samples (DFT)")

        # Verify sample alignment
        if len(y_semi) != len(y_dft):
            raise ValueError(f"Sample count mismatch: Semi={len(y_semi)}, DFT={len(y_dft)}")

        logger.info("Loading locked splits.")
        locked_splits = load_locked_splits(args.splits)
        logger.info(f"Found {len(locked_splits)} folds.")

        # Run Cross-Validation
        logger.info("Running Cross-Validation for Semi-Empirical model...")
        mae_semi_scores = run_cross_validation(X_semi, y_semi, locked_splits)
        mae_semi_avg = np.mean(mae_semi_scores)
        logger.info(f"Semi-Empirical MAE (avg): {mae_semi_avg:.4f}")

        logger.info("Running Cross-Validation for DFT model...")
        mae_dft_scores = run_cross_validation(X_dft, y_dft, locked_splits)
        mae_dft_avg = np.mean(mae_dft_scores)
        logger.info(f"DFT MAE (avg): {mae_dft_avg:.4f}")

        # Paired T-Test
        logger.info("Running paired t-test...")
        t_test_result = run_paired_t_test(mae_semi_scores, mae_dft_scores)
        logger.info(f"T-test statistic: {t_test_result['statistic']:.4f}, p-value: {t_test_result['p_value']:.4f}")

        # Prepare Report
        report = {
            "mae_semi": float(mae_semi_avg),
            "mae_dft": float(mae_dft_avg),
            "t_test": t_test_result
        }

        # Write Report
        report_dir = os.path.dirname(args.report)
        if report_dir and not os.path.exists(report_dir):
            os.makedirs(report_dir)

        with open(args.report, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=4)

        logger.info(f"Evaluation report written to {args.report}")
        logger.info("Evaluation complete.")

    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Error during evaluation: {e}")
        raise


if __name__ == "__main__":
    main()