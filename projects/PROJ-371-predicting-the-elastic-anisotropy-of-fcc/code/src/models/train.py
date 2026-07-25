import os
import sys
import json
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple

import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.linear_model import LinearRegression
from sklearn.model_selection import LeaveOneGroupOut
from sklearn.metrics import r2_score, mean_absolute_error, mean_squared_error

from src.utils.config import get_path, get_config, get_seed
from src.utils.logging import get_logger

logger = get_logger(__name__)

def load_processed_data() -> pd.DataFrame:
    """Load the processed dataset with features and target."""
    data_path = get_path("processed", "elastic_anisotropy.csv")
    if not data_path.exists():
        raise FileNotFoundError(f"Processed data not found at {data_path}")
    return pd.read_csv(data_path)

def prepare_loeo_data(df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.Series, pd.Series]:
    """
    Prepare data for LOEO cross-validation.
    Returns: features_df, target_series, groups_series
    """
    feature_cols = [col for col in df.columns if col not in ['material_id', 'A1', 'C11', 'C12', 'C44']]
    X = df[feature_cols]
    y = df['A1']
    groups = df['element_group']  # Assumes T014b created 'element_group' column
    return X, y, groups

def train_single_model(model_name: str, X_train: pd.DataFrame, y_train: pd.Series) -> Tuple[Any, Dict[str, Any]]:
    """Train a single model and return the model and its hyperparameters."""
    if model_name == "RandomForest":
        model = RandomForestRegressor(random_state=get_seed(), n_estimators=100, max_depth=10)
    elif model_name == "GradientBoosting":
        model = GradientBoostingRegressor(random_state=get_seed(), n_estimators=100, max_depth=5)
    elif model_name == "LinearRegression":
        model = LinearRegression()
    else:
        raise ValueError(f"Unknown model: {model_name}")

    model.fit(X_train, y_train)
    hyperparams = model.get_params()
    return model, hyperparams

def evaluate_model(model: Any, X_test: pd.DataFrame, y_test: pd.Series) -> Dict[str, float]:
    """Evaluate model and return metrics."""
    y_pred = model.predict(X_test)
    return {
        "r2": float(r2_score(y_test, y_pred)),
        "mae": float(mean_absolute_error(y_test, y_pred)),
        "rmse": float(np.sqrt(mean_squared_error(y_test, y_pred)))
    }

def run_loeo_cross_validation(X: pd.DataFrame, y: pd.Series, groups: pd.Series) -> Dict[str, Any]:
    """Run LOEO cross-validation and aggregate results."""
    logo = LeaveOneGroupOut()
    model_names = ["RandomForest", "GradientBoosting", "LinearRegression"]
    all_results = {name: {"scores": [], "hyperparams": None} for name in model_names}
    fold_metrics = []

    for train_idx, test_idx in logo.split(X, y, groups):
        X_train, X_test = X.iloc[train_idx], X.iloc[test_idx]
        y_train, y_test = y.iloc[train_idx], y.iloc[test_idx]
        test_group = groups.iloc[test_idx].iloc[0]

        fold_result = {"test_group": test_group, "metrics": {}}

        for name in model_names:
            model, hyperparams = train_single_model(name, X_train, y_train)
            metrics = evaluate_model(model, X_test, y_test)
            fold_result["metrics"][name] = metrics

            if all_results[name]["hyperparams"] is None:
                all_results[name]["hyperparams"] = hyperparams

            all_results[name]["scores"].append(metrics["r2"])

        fold_metrics.append(fold_result)

    aggregated = {}
    for name in model_names:
        scores = all_results[name]["scores"]
        aggregated[name] = {
            "mean_r2": float(np.mean(scores)),
            "std_r2": float(np.std(scores)),
            "hyperparameters": all_results[name]["hyperparams"]
        }

    return {"aggregated": aggregated, "fold_details": fold_metrics}

def save_results(results: Dict[str, Any], output_path: Path) -> None:
    """Save results to JSON, including hyperparameters and metrics."""
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    logger.info(f"Results saved to {output_path}")

def main():
    """Main entry point for training and logging metrics."""
    config = get_config()
    output_dir = get_path("output")
    output_dir.mkdir(parents=True, exist_ok=True)
    metrics_path = output_dir / "metrics.json"

    logger.info("Loading processed data...")
    df = load_processed_data()

    logger.info("Preparing LOEO data...")
    X, y, groups = prepare_loeo_data(df)

    logger.info("Running LOEO cross-validation...")
    results = run_loeo_cross_validation(X, y, groups)

    # Ensure hyperparameters and metrics are logged to output/metrics.json
    save_results(results, metrics_path)

    logger.info("Training and evaluation complete.")
    return results

if __name__ == "__main__":
    main()