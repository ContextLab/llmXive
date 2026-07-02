"""
Cross-validation utilities for molecular conductivity prediction.
Implements 5-fold cross-validation and metric recording as per FR-004.
"""
import logging
import json
import os
from typing import Dict, Any, List, Tuple, Optional
import numpy as np
import pandas as pd
from sklearn.model_selection import cross_val_score, KFold
from sklearn.metrics import r2_score, mean_absolute_error
from scipy.stats import kruskal

from code.config import SEED
from code.scaffold_split import split_indices
from code.train_models import train_and_evaluate

logger = logging.getLogger(__name__)

def run_cross_validation(
    X: pd.DataFrame,
    y: pd.Series,
    model,
    n_splits: int = 5,
    seed: int = SEED
) -> Dict[str, Any]:
    """
    Perform 5-fold cross-validation on the given data and model.

    Args:
        X: Feature DataFrame
        y: Target Series
        model: Scikit-learn compatible regressor
        n_splits: Number of folds (default 5)
        seed: Random seed for reproducibility

    Returns:
        Dictionary containing:
            - cv_r2_scores: List of R² scores per fold
            - cv_mae_scores: List of MAE scores per fold
            - mean_r2: Mean R² score
            - mean_mae: Mean MAE score
            - std_r2: Standard deviation of R² scores
            - std_mae: Standard deviation of MAE scores
    """
    logger.info(f"Running {n_splits}-fold cross-validation with seed {seed}")

    # Use scaffold-aware splitting if possible, otherwise standard KFold
    # For true scaffold splits, we need to pass scaffold labels
    # Here we use standard KFold as a baseline, but can be enhanced
    kf = KFold(n_splits=n_splits, shuffle=True, random_state=seed)

    r2_scores = []
    mae_scores = []

    for fold_idx, (train_idx, val_idx) in enumerate(kf.split(X)):
        logger.debug(f"Processing fold {fold_idx + 1}/{n_splits}")

        X_train, X_val = X.iloc[train_idx], X.iloc[val_idx]
        y_train, y_val = y.iloc[train_idx], y.iloc[val_idx]

        # Train model
        model.fit(X_train, y_train)

        # Predict
        y_pred = model.predict(X_val)

        # Calculate metrics
        r2 = r2_score(y_val, y_pred)
        mae = mean_absolute_error(y_val, y_pred)

        r2_scores.append(r2)
        mae_scores.append(mae)

        logger.debug(f"Fold {fold_idx + 1}: R²={r2:.4f}, MAE={mae:.4f}")

    # Calculate summary statistics
    result = {
        "cv_r2_scores": [float(s) for s in r2_scores],
        "cv_mae_scores": [float(s) for s in mae_scores],
        "mean_r2": float(np.mean(r2_scores)),
        "mean_mae": float(np.mean(mae_scores)),
        "std_r2": float(np.std(r2_scores)),
        "std_mae": float(np.std(mae_scores)),
        "n_splits": n_splits,
        "seed": seed
    }

    logger.info(f"CV Results: Mean R²={result['mean_r2']:.4f} ± {result['std_r2']:.4f}")
    logger.info(f"CV Results: Mean MAE={result['mean_mae']:.4f} ± {result['std_mae']:.4f}")

    return result


def record_metrics_to_file(
    results: Dict[str, Any],
    output_path: str = "data/processed/cv_results.json",
    model_name: str = "unknown"
) -> None:
    """
    Save cross-validation results to a JSON file.

    Args:
        results: Dictionary of CV results from run_cross_validation
        output_path: Path to output JSON file
        model_name: Name of the model for identification
    """
    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    # Add model metadata
    results["model_name"] = model_name
    results["timestamp"] = pd.Timestamp.now().isoformat()

    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)

    logger.info(f"CV results saved to {output_path}")


def run_cv_for_multiple_models(
    X: pd.DataFrame,
    y: pd.Series,
    models: Dict[str, Any],
    n_splits: int = 5,
    seed: int = SEED
) -> Dict[str, Dict[str, Any]]:
    """
    Run cross-validation for multiple models and compare results.

    Args:
        X: Feature DataFrame
        y: Target Series
        models: Dictionary mapping model names to model instances
        n_splits: Number of folds
        seed: Random seed

    Returns:
        Dictionary mapping model names to their CV results
    """
    all_results = {}

    for name, model in models.items():
        logger.info(f"Running CV for model: {name}")
        cv_results = run_cross_validation(X, y, model, n_splits, seed)
        all_results[name] = cv_results

    return all_results


def compare_cv_results(
    results: Dict[str, Dict[str, Any]],
    output_path: Optional[str] = None
) -> pd.DataFrame:
    """
    Compare cross-validation results across models.

    Args:
        results: Dictionary of CV results from run_cv_for_multiple_models
        output_path: Optional path to save comparison table

    Returns:
        DataFrame with model comparison metrics
    """
    comparison_data = []

    for model_name, cv_data in results.items():
        comparison_data.append({
            "model": model_name,
            "mean_r2": cv_data["mean_r2"],
            "std_r2": cv_data["std_r2"],
            "mean_mae": cv_data["mean_mae"],
            "std_mae": cv_data["std_mae"],
            "n_splits": cv_data["n_splits"]
        })

    df = pd.DataFrame(comparison_data)
    df = df.sort_values("mean_r2", ascending=False)

    if output_path:
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        df.to_csv(output_path, index=False)
        logger.info(f"Comparison saved to {output_path}")

    return df
