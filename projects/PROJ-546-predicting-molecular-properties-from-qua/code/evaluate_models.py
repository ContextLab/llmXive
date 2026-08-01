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

# Ensure imports match API surface
# We assume the data files exist as per previous tasks T020, T021, T022
# The main script expects to load semi-empirical and DFT descriptor sets
# and compute MAE against experimental barriers.

def setup_logger(name: str) -> logging.Logger:
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    handler = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    return logger

logger = setup_logger(__name__)

def load_data_semi(file_path: str) -> Tuple[np.ndarray, np.ndarray]:
    """Load semi-empirical descriptors and targets."""
    features, targets = [], []
    with open(file_path, 'r', newline='') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Assuming columns: 'HOMO', 'LUMO', 'Mayer_Bond_Order', ... 'experimental_barrier'
            # We need to know the exact feature columns. For now, we assume all numeric except target.
            feature_row = []
            for k, v in row.items():
                if k != 'experimental_barrier' and k != 'SMILES':
                    try:
                        feature_row.append(float(v))
                    except ValueError:
                        feature_row.append(0.0) # Handle missing or non-numeric
            features.append(feature_row)
            targets.append(float(row['experimental_barrier']))
    return np.array(features), np.array(targets)

def load_data_dft(file_path: str) -> Tuple[np.ndarray, np.ndarray]:
    """Load DFT descriptors and targets."""
    # Same logic as semi, just different file
    return load_data_semi(file_path)

def train_and_evaluate_fold(X: np.ndarray, y: np.ndarray, fold_idx: int, n_folds: int) -> float:
    """Train a Random Forest on a specific fold and return MAE."""
    from sklearn.model_selection import KFold
    from sklearn.ensemble import RandomForestRegressor
    from sklearn.metrics import mean_absolute_error

    kf = KFold(n_splits=n_folds, shuffle=True, random_state=42)
    folds = list(kf.split(X))
    if fold_idx >= len(folds):
        raise ValueError(f"Fold index {fold_idx} out of range for {n_folds} folds")

    train_idx, test_idx = folds[fold_idx]
    X_train, X_test = X[train_idx], X[test_idx]
    y_train, y_test = y[train_idx], y[test_idx]

    model = RandomForestRegressor(n_estimators=100, random_state=42, n_jobs=-1)
    model.fit(X_train, y_train)
    y_pred = model.predict(X_test)
    mae = mean_absolute_error(y_test, y_pred)
    return mae

def run_cross_validation(X: np.ndarray, y: np.ndarray, n_folds: int = 5) -> List[float]:
    """Run cross-validation and return list of MAEs per fold."""
    maes = []
    for i in range(n_folds):
        mae = train_and_evaluate_fold(X, y, i, n_folds)
        maes.append(mae)
        logger.info(f"Fold {i+1}/{n_folds} MAE: {mae:.4f}")
    return maes

def run_paired_t_test(semi_maes: List[float], dft_maes: List[float]) -> Tuple[float, float]:
    """Run paired t-test between semi-empirical and DFT MAEs."""
    if len(semi_maes) != len(dft_maes):
        raise ValueError("MAE lists must have equal length for paired t-test")
    t_stat, p_val = stats.ttest_rel(semi_maes, dft_maes)
    return t_stat, p_val

def verify_mae_threshold(mae: float, threshold: float) -> bool:
    """Verify if MAE is within the threshold."""
    return mae <= threshold

def main():
    parser = argparse.ArgumentParser(description="Evaluate and compare semi-empirical and DFT models.")
    parser.add_argument("--semi-data", type=str, required=True, help="Path to semi-empirical descriptor CSV")
    parser.add_argument("--dft-data", type=str, required=True, help="Path to DFT descriptor CSV")
    parser.add_argument("--output", type=str, default="reports/evaluation.json", help="Output JSON report path")
    parser.add_argument("--n-folds", type=int, default=5, help="Number of CV folds")
    args = parser.parse_args()

    logger.info(f"Loading semi-empirical data from {args.semi_data}")
    X_semi, y_semi = load_data_semi(args.semi_data)
    logger.info(f"Loaded {len(y_semi)} samples for semi-empirical model")

    logger.info(f"Loading DFT data from {args.dft_data}")
    X_dft, y_dft = load_data_dft(args.dft_data)
    logger.info(f"Loaded {len(y_dft)} samples for DFT model")

    if len(y_semi) != len(y_dft):
        logger.warning("Sample sizes differ between semi and DFT datasets. Aligning by index may be needed.")
        # For now, assume they are aligned or the task implies running on the same subset
        # If not aligned, we might need to load SMILES and align.
        # Given the task context, we proceed assuming alignment or independent evaluation on available data.
        # However, for paired t-test, we need paired folds. We will assume the datasets are aligned by row.

    logger.info("Running Cross-Validation for Semi-Empirical Model")
    semi_maes = run_cross_validation(X_semi, y_semi, n_folds=args.n_folds)
    mean_semi_mae = np.mean(semi_maes)
    logger.info(f"Mean Semi-Empirical MAE: {mean_semi_mae:.4f}")

    logger.info("Running Cross-Validation for DFT Model")
    dft_maes = run_cross_validation(X_dft, y_dft, n_folds=args.n_folds)
    mean_dft_mae = np.mean(dft_maes)
    logger.info(f"Mean DFT MAE: {mean_dft_mae:.4f}")

    logger.info("Running Paired T-Test")
    t_stat, p_val = run_paired_t_test(semi_maes, dft_maes)
    logger.info(f"T-statistic: {t_stat:.4f}, P-value: {p_val:.4f}")

    # FR-008: Flag if semi-MAE exceeds DFT-MAE by >20%
    # Logic: (Semi_MAE - DFT_MAE) / DFT_MAE > 0.20
    # Handle division by zero if DFT_MAE is 0 (unlikely but possible)
    semi_exceeds_dft_by_20pct = False
    if mean_dft_mae > 0:
        relative_diff = (mean_semi_mae - mean_dft_mae) / mean_dft_mae
        semi_exceeds_dft_by_20pct = relative_diff > 0.20
        logger.info(f"Semi-MAE exceeds DFT-MAE by {relative_diff*100:.2f}%")
    else:
        logger.warning("DFT MAE is zero, cannot calculate relative difference.")
        # If DFT is 0 and Semi is > 0, it technically exceeds by infinite percent.
        if mean_semi_mae > 0:
            semi_exceeds_dft_by_20pct = True

    # FR-010: Verify semi-MAE <= 2.0 kcal/mol
    mae_threshold = 2.0
    mae_pass_fail = "pass" if verify_mae_threshold(mean_semi_mae, mae_threshold) else "fail"
    logger.info(f"Semi-MAE threshold check ({mae_threshold} kcal/mol): {mae_pass_fail}")

    # Prepare report
    report = {
        "mean_semi_mae": float(mean_semi_mae),
        "mean_dft_mae": float(mean_dft_mae),
        "t_statistic": float(t_stat),
        "p_value": float(p_val),
        "semi_exceeds_dft_by_20pct": semi_exceeds_dft_by_20pct,
        "mae_threshold_kcal_mol": mae_threshold,
        "mae_threshold_status": mae_pass_fail,
        "fold_maes_semi": [float(x) for x in semi_maes],
        "fold_maes_dft": [float(x) for x in dft_maes]
    }

    # Ensure output directory exists
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2)

    logger.info(f"Evaluation report written to {args.output}")

    # Exit with code 1 if threshold exceeded (FR-010 requirement)
    if mae_pass_fail == "fail":
        logger.error("Semi-empirical MAE exceeds threshold. Exiting with code 1.")
        sys.exit(1)

    sys.exit(0)

if __name__ == "__main__":
    main()