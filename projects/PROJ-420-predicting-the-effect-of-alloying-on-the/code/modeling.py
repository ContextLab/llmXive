from __future__ import annotations

import json
import os
import pickle
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
from compositional import ilr
from joblib import dump, load
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import GridSearchCV, train_test_split
from sklearn.metrics import mean_absolute_error

from config import get_config
from logging_config import get_logger, log_operation

logger = get_logger(__name__)
config = get_config()


def load_features_and_target(data_path: Path) -> Tuple[pd.DataFrame, pd.Series]:
    """Load the cleaned dataset and separate features/target."""
    df = pd.read_parquet(data_path)
    # Features are the 5 major elements in atomic fraction
    feature_cols = ["Cu", "Mg", "Si", "Zn", "Mn"]
    # Ensure columns exist
    missing = [c for c in feature_cols if c not in df.columns]
    if missing:
        raise ValueError(f"Missing feature columns in dataset: {missing}")
    
    X = df[feature_cols]
    y = df["poisson_ratio"]
    return X, y


def apply_ilr_transformation(X: pd.DataFrame) -> pd.DataFrame:
    """Apply ILR transformation to compositional data."""
    # compositional.ilr expects a DataFrame with columns representing parts
    # It returns a DataFrame with ilr coordinates
    ilr_X = ilr(X)
    return ilr_X


def split_dataset(
    X: pd.DataFrame, 
    y: pd.Series, 
    test_size: float = 0.2, 
    random_state: int = 42
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.Series, pd.Series, List[int], List[int]]:
    """Split dataset into training and test sets, returning indices."""
    X_train, X_test, y_train, y_test, train_idx, test_idx = train_test_split(
        X, y, range(len(X)), test_size=test_size, random_state=random_state, stratify=None
    )
    # Convert indices to lists for JSON serialization
    train_indices = list(train_idx)
    test_indices = list(test_idx)
    return X_train, X_test, y_train, y_test, train_indices, test_indices


def load_split_indices(indices_path: Path) -> Tuple[List[int], List[int]]:
    """Load split indices from JSON file."""
    with open(indices_path, "r") as f:
        data = json.load(f)
    return data["train_indices"], data["test_indices"]


def train_random_forest_with_cv(
    X_train: pd.DataFrame, 
    y_train: pd.Series, 
    cv_folds: int = 5
) -> Tuple[RandomForestRegressor, Dict[str, Any], float, float, float]:
    """Train RF with cross-validation and return best model, params, and metrics."""
    param_grid = {
        "n_estimators": [100],
        "max_depth": [None, 5, 10, 20]
    }
    
    rf = RandomForestRegressor(random_state=42)
    grid_search = GridSearchCV(
        rf, param_grid, cv=cv_folds, scoring="neg_mean_absolute_error", n_jobs=-1
    )
    grid_search.fit(X_train, y_train)
    
    best_model = grid_search.best_estimator_
    best_params = grid_search.best_params_
    
    # Calculate CV metrics
    cv_scores = -grid_search.cv_results_["mean_test_score"]
    cv_mae = float(np.mean(cv_scores))
    cv_std = float(np.std(cv_scores))
    # 95% CI approximation: mean +/- 1.96 * std
    cv_ci_lower = cv_mae - 1.96 * cv_std
    cv_ci_upper = cv_mae + 1.96 * cv_std
    
    return best_model, best_params, cv_mae, cv_ci_lower, cv_ci_upper


def load_best_hyperparameters(hyperparams_path: Path) -> Dict[str, Any]:
    """Load best hyperparameters from JSON file."""
    with open(hyperparams_path, "r") as f:
        return json.load(f)


def save_best_hyperparameters(hyperparams: Dict[str, Any], output_path: Path) -> None:
    """Save best hyperparameters to JSON file."""
    with open(output_path, "w") as f:
        json.dump(hyperparams, f, indent=2)


def extract_best_hyperparameters(metrics_path: Path, output_path: Path) -> None:
    """Extract best_params from cv_metrics.json and save to separate file."""
    with open(metrics_path, "r") as f:
        data = json.load(f)
    best_params = data.get("best_params", {})
    save_best_hyperparameters(best_params, output_path)


def train_and_serialize_model(
    model_path: Path,
    X_train: pd.DataFrame,
    y_train: pd.Series,
    best_params: Dict[str, Any]
) -> None:
    """Train final model with best params and serialize to disk."""
    rf = RandomForestRegressor(**best_params, random_state=42)
    rf.fit(X_train, y_train)
    
    # Ensure directory exists
    model_path.parent.mkdir(parents=True, exist_ok=True)
    dump(rf, str(model_path), compress=3, protocol=3)
    logger.info(f"Model saved to {model_path}")


def load_model(model_path: Path) -> RandomForestRegressor:
    """Load trained model from disk."""
    return load(str(model_path))


def save_model_metrics(
    metrics: Dict[str, Any],
    output_path: Path
) -> None:
    """Save model metrics to JSON file."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(metrics, f, indent=2)


def save_residuals(
    residuals: pd.Series,
    output_path: Path
) -> None:
    """Save residuals to JSON file."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(residuals.tolist(), f, indent=2)


def save_methodological_flags(
    flags: Dict[str, Any],
    output_path: Path
) -> None:
    """Save methodological flags to JSON file."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(flags, f, indent=2)


def aggregate_model_metrics(
    cv_mae: float,
    cv_ci_lower: float,
    cv_ci_upper: float,
    test_mae: float,
    output_path: Path
) -> None:
    """
    Aggregate model metrics from CV and Test sets into a single file.
    This function satisfies T023d.
    """
    metrics = {
        "cv_mae": cv_mae,
        "cv_ci_lower": cv_ci_lower,
        "cv_ci_upper": cv_ci_upper,
        "test_mae": test_mae
    }
    save_model_metrics(metrics, output_path)
    logger.info(f"Aggregated model metrics saved to {output_path}")


def evaluate_model_on_test(
    model: RandomForestRegressor,
    X_test: pd.DataFrame,
    y_test: pd.Series
) -> Tuple[float, pd.Series]:
    """Evaluate model on test set and return MAE and residuals."""
    y_pred = model.predict(X_test)
    mae = float(mean_absolute_error(y_test, y_pred))
    residuals = y_test - y_pred
    return mae, residuals


def run_modeling_pipeline() -> None:
    """Run the full modeling pipeline: split, CV, train, evaluate, aggregate."""
    cfg = get_config()
    data_path = cfg.data_processed / "alloys_clean.parquet"
    indices_path = cfg.data_processed / "split_indices.json"
    hyperparams_path = cfg.results / "cv_best_hyperparameters.json"
    model_path = cfg.models / "rf_model.pkl"
    metrics_path = cfg.results / "cv_metrics.json"
    aggregated_metrics_path = cfg.results / "model_metrics.json"
    residuals_path = cfg.results / "residuals.json"
    flags_path = cfg.results / "methodological_flags.json"
    
    # 1. Load data and indices
    X, y = load_features_and_target(data_path)
    train_indices, test_indices = load_split_indices(indices_path)
    
    # Filter to training set
    X_train = X.iloc[train_indices]
    y_train = y.iloc[train_indices]
    X_test = X.iloc[test_indices]
    y_test = y.iloc[test_indices]
    
    # 2. Apply ILR transformation to training data
    X_train_ilr = apply_ilr_transformation(X_train)
    
    # 3. Load best hyperparameters
    best_params = load_best_hyperparameters(hyperparams_path)
    
    # 4. Train final model on full training set
    train_and_serialize_model(model_path, X_train_ilr, y_train, best_params)
    
    # 5. Load model and evaluate on test set
    model = load_model(model_path)
    X_test_ilr = apply_ilr_transformation(X_test)
    test_mae, residuals = evaluate_model_on_test(model, X_test_ilr, y_test)
    
    # 6. Load CV metrics to get cv_mae for aggregation
    with open(metrics_path, "r") as f:
        cv_data = json.load(f)
    cv_mae = cv_data["cv_mae"]
    cv_ci_lower = cv_data["cv_ci_lower"]
    cv_ci_upper = cv_data["cv_ci_upper"]
    
    # 7. Save residuals
    save_residuals(residuals, residuals_path)
    
    # 8. Check MAE flag and save methodological flags
    mae_flag = cv_mae > 0.05
    narrative = ""
    if mae_flag:
        narrative = "Methodological Concern: Cross-validation MAE exceeds 0.05 threshold, indicating potential model instability or insufficient signal."
    
    flags = {
        "mae_flag": mae_flag,
        "cv_mae": cv_mae,
        "narrative_limitation": narrative
    }
    save_methodological_flags(flags, flags_path)
    
    # 9. Aggregate model metrics (T023d)
    aggregate_model_metrics(cv_mae, cv_ci_lower, cv_ci_upper, test_mae, aggregated_metrics_path)
    
    logger.info("Modeling pipeline completed successfully.")


def main() -> None:
    """CLI entry point."""
    parser = argparse.ArgumentParser(description="Run modeling pipeline")
    parser.add_argument("--config", type=str, default="code/config.yaml", help="Config file path")
    args = parser.parse_args()
    
    # Override config if provided
    if args.config:
        os.environ["PROJECT_CONFIG"] = args.config
    
    run_modeling_pipeline()


if __name__ == "__main__":
    main()