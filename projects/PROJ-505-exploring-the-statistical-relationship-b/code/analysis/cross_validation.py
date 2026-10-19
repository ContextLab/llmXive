"""
Cross‑validation utilities for regression models.
Extends the existing module to compute:
  * 5‑fold time‑series split out‑of‑sample R² for baseline and full models
  * Incremental ΔR² = R²_full − R²_baseline
Writes the results to:
  * data/artifacts/cv_metrics.json
  * data/artifacts/delta_r2.json
"""
import json
from pathlib import Path
from typing import List, Dict, Any

import pandas as pd
import numpy as np
from sklearn.model_selection import TimeSeriesSplit

# Project utilities
from llmxive_toolkit import paths, get_logger
from code.utils.logging import log_duration
from code.analysis.regression import get_coupling_function_columns

logger = get_logger(__name__)

# ----------------------------------------------------------------------
# Existing generic K‑fold helper (kept for backward compatibility)
# ----------------------------------------------------------------------
def run_cross_validation(
    df: pd.DataFrame,
    target: str,
    predictors: List[str],
    k: int = 5,
) -> Dict[str, Any]:
    """
    Perform k‑fold cross‑validation (shuffled) and return mean and std of
    out‑of‑sample R².  This function is retained for compatibility but is
    not used by the T007 workflow.
    """
    from sklearn.model_selection import KFold

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

# ----------------------------------------------------------------------
# TimeSeriesSplit helper used by T007
# ----------------------------------------------------------------------
@log_duration
def run_time_series_cv(
    df: pd.DataFrame,
    target: str,
    predictors: List[str],
    n_splits: int = 5,
) -> Dict[str, Any]:
    """
    Perform a time‑series split (no shuffling) and compute out‑of‑sample
    R² for each fold. Returns the same structure as ``run_cross_validation``.
    """
    X = df[predictors].values
    y = df[target].values

    tscv = TimeSeriesSplit(n_splits=n_splits)
    r2_scores = []

    for train_idx, test_idx in tscv.split(X):
        X_train, X_test = X[train_idx], X[test_idx]
        y_train, y_test = y[train_idx], y[test_idx]

        # Fit OLS using numpy (simple linear regression)
        X_train_const = np.column_stack([np.ones(len(X_train)), X_train])
        beta = np.linalg.lstsq(X_train_const, y_train, rcond=None)[0]

        X_test_const = np.column_stack([np.ones(len(X_test)), X_test])
        y_pred = X_test_const @ beta

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

# ----------------------------------------------------------------------
# ΔR² computation helper
# ----------------------------------------------------------------------
def _load_model_r2(path: Path) -> Dict[str, float]:
    """
    Load a regression JSON artifact and extract the R² for each target.
    Expected format (produced by ``code.analysis.regression``):
    {
        "dst_index": {"r2": 0.42, ...},
        "kp_index": {"r2": 0.35, ...}
    }
    Returns a mapping ``{target: r2}``.
    """
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    r2_map: Dict[str, float] = {}
    for target, metrics in data.items():
        # Guard against unexpected structures
        if isinstance(metrics, dict) and "r2" in metrics:
            r2_map[target] = float(metrics["r2"])
        else:
            # If the file directly stores the r2 value (e.g. {"dst_index": 0.42, ...})
            try:
                r2_map[target] = float(metrics)
            except Exception:
                raise ValueError(
                    f"Unable to locate R² for target '{target}' in {path}"
                )
    return r2_map

# ----------------------------------------------------------------------
# Main driver for T007
# ----------------------------------------------------------------------
@log_duration
def main() -> None:
    """
    Orchestrates the incremental R² computation and 5‑fold
    time‑series cross‑validation for both Dst and Kp targets.

    Steps:
    1. Load the processed dataset with coupling functions and composition
       ratios (``data/processed/with_coupling.parquet``).
    2. Identify predictor sets:
         * baseline: coupling function columns only
         * full: baseline + composition ratio columns
    3. For each target (``dst_index`` and ``kp_index``) run
       ``run_time_series_cv`` for baseline and full models.
    4. Write per‑target CV metrics to ``cv_metrics.json``.
    5. Load the regression artifacts (baseline_model.json,
       full_model.json) and compute ΔR² per target.
    6. Write ΔR² values to ``delta_r2.json``.
    """
    # ------------------------------------------------------------------
    # 1. Load the enriched dataset
    # ------------------------------------------------------------------
    data_path = paths.processed("with_coupling.parquet")
    if not data_path.is_file():
        raise FileNotFoundError(
            f"Required input file not found: {data_path}. "
            "Make sure the coupling‑function step has been executed."
        )
    df = pd.read_parquet(data_path)

    # ------------------------------------------------------------------
    # 2. Define predictor sets
    # ------------------------------------------------------------------
    coupling_cols = get_coupling_function_columns()
    # Composition ratio column names are defined in the alignment step
    composition_cols = ["o_fe_ratio", "he_h_ratio", "c_o_ratio"]
    baseline_predictors = coupling_cols
    full_predictors = coupling_cols + composition_cols

    # Targets of interest
    targets = ["dst_index", "kp_index"]

    # ------------------------------------------------------------------
    # 3. Run time‑series cross‑validation for each target/predictor set
    # ------------------------------------------------------------------
    cv_results: Dict[str, Any] = {
        "baseline": {},
        "full": {},
    }

    for target in targets:
        logger.info(
            "Running TimeSeriesSplit CV for target '%s' (baseline predictors)",
            target,
        )
        baseline_cv = run_time_series_cv(
            df=df,
            target=target,
            predictors=baseline_predictors,
            n_splits=5,
        )
        cv_results["baseline"][target] = baseline_cv

        logger.info(
            "Running TimeSeriesSplit CV for target '%s' (full predictors)",
            target,
        )
        full_cv = run_time_series_cv(
            df=df,
            target=target,
            predictors=full_predictors,
            n_splits=5,
        )
        cv_results["full"][target] = full_cv

    # ------------------------------------------------------------------
    # 4. Persist CV metrics
    # ------------------------------------------------------------------
    cv_path = paths.artifacts("cv_metrics.json")
    cv_path.parent.mkdir(parents=True, exist_ok=True)
    with open(cv_path, "w", encoding="utf-8") as f:
        json.dump(cv_results, f, indent=2)
    logger.info("Cross‑validation metrics written to %s", cv_path)

    # ------------------------------------------------------------------
    # 5. Compute ΔR² from regression artifacts
    # ------------------------------------------------------------------
    baseline_model_path = paths.artifacts("baseline_model.json")
    full_model_path = paths.artifacts("full_model.json")

    if not baseline_model_path.is_file() or not full_model_path.is_file():
        raise FileNotFoundError(
            "Baseline or full regression artifact missing. "
            "Ensure that `code.analysis.regression` has been executed."
        )

    baseline_r2 = _load_model_r2(baseline_model_path)
    full_r2 = _load_model_r2(full_model_path)

    delta_r2: Dict[str, float] = {}
    for target in targets:
        b = baseline_r2.get(target)
        f = full_r2.get(target)
        if b is None or f is None:
            raise ValueError(
                f"R² for target '{target}' missing in regression artifacts."
            )
        delta = f - b
        delta_r2[target] = delta

    # ------------------------------------------------------------------
    # 6. Persist ΔR²
    # ------------------------------------------------------------------
    delta_path = paths.artifacts("delta_r2.json")
    delta_path.parent.mkdir(parents=True, exist_ok=True)
    with open(delta_path, "w", encoding="utf-8") as f:
        json.dump(delta_r2, f, indent=2)
    logger.info("ΔR² values written to %s", delta_path)

if __name__ == "__main__":
    main()