import os
import sys
import json
import logging
import pickle
from pathlib import Path
from typing import Dict, Any, Tuple, Optional

import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import r2_score, mean_absolute_error, mean_squared_error
from scipy.stats import ttest_rel
from statsmodels.stats.multitest import multipletests

from config import load_paths
from utils.chemical_families import assign_chemical_family
from utils.io import load_dataframe_safely

logger = logging.getLogger(__name__)


def load_data(input_path: Path) -> pd.DataFrame:
    """Load the processed dataset."""
    return pd.read_csv(input_path)


def perform_stratified_split(
    df: pd.DataFrame,
    target_col: str,
    sample_weight_col: Optional[str] = None,
    test_size: float = 0.2,
    random_state: int = 42,
) -> Tuple[pd.DataFrame, pd.DataFrame, Optional[pd.Series], Optional[pd.Series]]:
    """Perform stratified split by chemical family."""
    df = df.copy()
    df["chem_family"] = df["dominant_element"].apply(assign_chemical_family)

    X = df.drop(columns=[target_col, "chem_family", "dominant_element"])
    y = df[target_col]
    family = df["chem_family"]

    if sample_weight_col and sample_weight_col in df.columns:
        weights = df[sample_weight_col]
    else:
        weights = None

    X_train, X_val, y_train, y_val, w_train, w_val = train_test_split(
        X,
        y,
        weights,
        test_size=test_size,
        stratify=family,
        random_state=random_state,
    )

    return X_train, X_val, y_train, y_val


def load_models(
    rf_path: Path, gb_path: Path
) -> Tuple[RandomForestRegressor, GradientBoostingRegressor]:
    """Load trained models from disk."""
    with open(rf_path, "rb") as f:
        rf = pickle.load(f)
    with open(gb_path, "rb") as f:
        gb = pickle.load(f)
    return rf, gb


def calculate_tvd(
    train_dist: Dict[str, float], val_dist: Dict[str, float]
) -> float:
    """Calculate Total Variation Distance between two distributions."""
    all_keys = set(train_dist.keys()) | set(val_dist.keys())
    tvd = 0.0
    for k in all_keys:
        p = train_dist.get(k, 0.0)
        q = val_dist.get(k, 0.0)
        tvd += abs(p - q)
    return tvd / 2.0


def evaluate_models(
    X_val: pd.DataFrame,
    y_val: pd.Series,
    rf: RandomForestRegressor,
    gb: GradientBoostingRegressor,
) -> Dict[str, Dict[str, float]]:
    """Evaluate models and return metrics."""
    y_pred_rf = rf.predict(X_val)
    y_pred_gb = gb.predict(X_val)

    metrics = {
        "RandomForest": {
            "r2": float(r2_score(y_val, y_pred_rf)),
            "mae": float(mean_absolute_error(y_val, y_pred_rf)),
            "rmse": float(np.sqrt(mean_squared_error(y_val, y_pred_rf))),
        },
        "GradientBoosting": {
            "r2": float(r2_score(y_val, y_pred_gb)),
            "mae": float(mean_absolute_error(y_val, y_pred_gb)),
            "rmse": float(np.sqrt(mean_squared_error(y_val, y_pred_gb))),
        },
    }
    return metrics


def save_metrics(
    metrics: Dict[str, Dict[str, float]],
    output_path: Path,
    additional: Optional[Dict[str, Any]] = None,
) -> None:
    """Save metrics to JSON."""
    if additional:
        metrics.update(additional)
    with open(output_path, "w") as f:
        json.dump(metrics, f, indent=2)


def main() -> None:
    """Main entry point for evaluation."""
    logging.basicConfig(level=logging.INFO)
    paths = load_paths()

    # Load data
    input_path = paths["data_processed"] / "computed_descriptors.csv"
    df = load_data(input_path)

    # Split
    X_train, X_val, y_train, y_val = perform_stratified_split(
        df,
        target_col="formation_energy_per_atom",
        test_size=0.2,
        random_state=42,
    )

    # Train models
    rf = RandomForestRegressor(n_estimators=200, max_depth=20, random_state=42)
    gb = GradientBoostingRegressor(n_estimators=100, random_state=42)

    rf.fit(X_train, y_train)
    gb.fit(X_train, y_train)

    # Evaluate
    metrics = evaluate_models(X_val, y_val, rf, gb)

    # Check predictive power
    best_r2 = max(metrics["RandomForest"]["r2"], metrics["GradientBoosting"]["r2"])
    metrics["predictive_power"] = best_r2 > 0.0

    # Overfitting check
    train_r2_rf = r2_score(y_train, rf.predict(X_train))
    val_r2_rf = metrics["RandomForest"]["r2"]
    if val_r2_rf <= 0:
        metrics["overfitting_ratio"] = None
    else:
        metrics["overfitting_ratio"] = train_r2_rf - val_r2_rf

    # Save models
    rf_path = paths["data_evaluation"] / "model_rf.pkl"
    gb_path = paths["data_evaluation"] / "model_gb.pkl"
    with open(rf_path, "wb") as f:
        pickle.dump(rf, f)
    with open(gb_path, "wb") as f:
        pickle.dump(gb, f)

    # Save metrics
    metrics_path = paths["data_evaluation"] / "model_metrics.json"
    save_metrics(metrics, metrics_path)

    # Statistical test
    y_pred_rf_train = rf.predict(X_train)
    y_pred_gb_train = gb.predict(X_train)
    y_pred_rf_val = rf.predict(X_val)
    y_pred_gb_val = gb.predict(X_val)

    # Paired t-test on validation set
    t_stat, p_val = ttest_rel(y_pred_rf_val, y_pred_gb_val)
    # BH correction (dummy for single comparison)
    _, p_adj, _, _ = multipletests([p_val], alpha=0.05, method="fdr_bh")

    stat_test = {
        "t_statistic": float(t_stat),
        "p_value": float(p_val),
        "p_adjusted": float(p_adj[0]),
        "significant": p_adj[0] < 0.05,
    }
    stat_path = paths["data_evaluation"] / "statistical_tests.json"
    with open(stat_path, "w") as f:
        json.dump(stat_test, f, indent=2)

    logger.info("Evaluation complete")


if __name__ == "__main__":
    main()
