"""
Cross‑validation utilities for regression models.
Provides k‑fold evaluation of out‑of‑sample R².
"""
import json
from pathlib import Path
from typing import List, Dict, Any

import pandas as pd
import numpy as np
from sklearn.model_selection import KFold

# Updated import path
from code.utils.logging import get_logger, log_duration

logger = get_logger(__name__)


@log_duration
def run_cross_validation(
    df: pd.DataFrame,
    target: str,
    predictors: List[str],
    k: int = 5,
) -> Dict[str, Any]:
    """
    Perform k‑fold cross‑validation and return mean and std of out‑of‑sample R².
    """
    X = df[predictors].values
    y = df[target].values

    kf = KFold(n_splits=k, shuffle=True, random_state=42)
    r2_scores = []

    for train_idx, test_idx in kf.split(X):
        X_train, X_test = X[train_idx], X[test_idx]
        y_train, y_test = y[train_idx], y[test_idx]

        # Fit OLS using numpy (simple linear regression)
        X_train_const = np.column_stack([np.ones(len(X_train)), X_train])
        beta = np.linalg.lstsq(X_train_const, y_train, rcond=None)[0]

        X_test_const = np.column_stack([np.ones(len(X_test)), X_test])
        y_pred = X_test_const @ beta

        # Compute R²
        ss_res = np.sum((y_test - y_pred) ** 2)
        ss_tot = np.sum((y_test - np.mean(y_test)) ** 2)
        r2 = 1 - ss_res / ss_tot if ss_tot != 0 else 0.0
        r2_scores.append(r2)

    result = {
        "mean_r2": float(np.mean(r2_scores)),
        "std_r2": float(np.std(r2_scores, ddof=1)),
        "fold_r2s": [float(v) for v in r2_scores],
    }
    return result


def main() -> None:
    logger.info("Cross‑validation module executed as script – no action defined.")


if __name__ == "__main__":
    main()
