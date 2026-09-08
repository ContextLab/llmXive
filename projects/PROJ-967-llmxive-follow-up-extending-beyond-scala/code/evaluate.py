"""
Evaluation module for the llmXive Follow-up pipeline.
Calculates metrics, baseline comparisons, permutation tests, and partial correlations.
"""

import argparse
import json
import logging
import os
import sys
import pickle
import numpy as np
from scipy import stats
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

# Import shared utilities from sibling modules if available, or define locally
# Note: The API surface lists these functions in evaluate.py, so we define them here.

def setup_logging(log_file: Optional[str] = None) -> logging.Logger:
    """Configure logging for the evaluation module."""
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)

    if not logger.handlers:
        ch = logging.StreamHandler(sys.stdout)
        ch.setLevel(logging.INFO)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        ch.setFormatter(formatter)
        logger.addHandler(ch)

        if log_file:
            fh = logging.FileHandler(log_file)
            fh.setLevel(logging.INFO)
            fh.setFormatter(formatter)
            logger.addHandler(fh)

    return logger

def load_features(features_path: str) -> Dict[str, Any]:
    """
    Load features from a JSON file.
    Expected structure: list of records or a dict with 'data' key.
    """
    logger = logging.getLogger(__name__)
    logger.info(f"Loading features from {features_path}")

    if not os.path.exists(features_path):
        raise FileNotFoundError(f"Features file not found: {features_path}")

    with open(features_path, 'r') as f:
        data = json.load(f)

    # Normalize to a list of records if necessary
    if isinstance(data, dict) and 'data' in data:
        return data['data']
    return data

def load_model_selection(model_selection_path: str) -> Dict[str, Any]:
    """Load model selection configuration."""
    logger = logging.getLogger(__name__)
    logger.info(f"Loading model selection config from {model_selection_path}")

    if not os.path.exists(model_selection_path):
        raise FileNotFoundError(f"Model selection file not found: {model_selection_path}")

    with open(model_selection_path, 'r') as f:
        return json.load(f)

def load_split_config(split_config_path: str) -> Dict[str, Any]:
    """Load train/test split configuration."""
    logger = logging.getLogger(__name__)
    logger.info(f"Loading split config from {split_config_path}")

    if not os.path.exists(split_config_path):
        raise FileNotFoundError(f"Split config file not found: {split_config_path}")

    with open(split_config_path, 'r') as f:
        return json.load(f)

def load_model(model_path: str) -> Any:
    """Load a trained model from a pickle file."""
    logger = logging.getLogger(__name__)
    logger.info(f"Loading model from {model_path}")

    if not os.path.exists(model_path):
        raise FileNotFoundError(f"Model file not found: {model_path}")

    with open(model_path, 'rb') as f:
        return pickle.load(f)

def calculate_metrics(y_true: np.ndarray, y_pred: np.ndarray) -> Dict[str, float]:
    """Calculate R² and MAE."""
    logger = logging.getLogger(__name__)

    if len(y_true) != len(y_pred):
        raise ValueError("y_true and y_pred must have the same length")

    if len(y_true) == 0:
        return {"r2": 0.0, "mae": 0.0, "rmse": 0.0}

    mae = np.mean(np.abs(y_true - y_pred))
    ss_res = np.sum((y_true - y_pred) ** 2)
    ss_tot = np.sum((y_true - np.mean(y_true)) ** 2)

    r2 = 1 - (ss_res / ss_tot) if ss_tot != 0 else 0.0
    rmse = np.sqrt(np.mean((y_true - y_pred) ** 2))

    logger.info(f"Metrics: R²={r2:.4f}, MAE={mae:.4f}, RMSE={rmse:.4f}")
    return {"r2": float(r2), "mae": float(mae), "rmse": float(rmse)}

def calculate_baseline_mae(y_true: np.ndarray, strategy: str = 'mean') -> float:
    """Calculate baseline MAE (e.g., predicting mean or median)."""
    logger = logging.getLogger(__name__)

    if strategy == 'mean':
        baseline_pred = np.full_like(y_true, np.mean(y_true))
    elif strategy == 'median':
        baseline_pred = np.full_like(y_true, np.median(y_true))
    else:
        raise ValueError(f"Unknown baseline strategy: {strategy}")

    baseline_mae = np.mean(np.abs(y_true - baseline_pred))
    logger.info(f"Baseline MAE ({strategy}): {baseline_mae:.4f}")
    return float(baseline_mae)

def calculate_permutation_pvalue(
    model: Any,
    X: np.ndarray,
    y: np.ndarray,
    n_permutations: int = 100,
    random_state: int = 42
) -> float:
    """
    Calculate permutation test p-value.
    Compares the model's R² against R² values from permuted targets.
    """
    logger = logging.getLogger(__name__)
    logger.info(f"Running permutation test with {n_permutations} permutations")

    # Calculate original R²
    y_pred_orig = model.predict(X)
    ss_res_orig = np.sum((y - y_pred_orig) ** 2)
    ss_tot = np.sum((y - np.mean(y)) ** 2)
    r2_orig = 1 - (ss_res_orig / ss_tot) if ss_tot != 0 else 0.0

    rng = np.random.default_rng(random_state)
    count_better = 0

    for i in range(n_permutations):
        # Permute y
        y_perm = y.copy()
        rng.shuffle(y_perm)

        # Retrain model on permuted data (simplified: refit with same params)
        # Note: For efficiency, we assume the model can be quickly refit or we use a simple estimator
        # In a full pipeline, this might involve re-running the training step.
        # For this skeleton, we assume 'model' has a 'fit' and 'predict' method.
        try:
            model.fit(X, y_perm)
            y_pred_perm = model.predict(X)
            ss_res_perm = np.sum((y_perm - y_pred_perm) ** 2)
            r2_perm = 1 - (ss_res_perm / ss_tot) if ss_tot != 0 else 0.0

            if r2_perm >= r2_orig:
                count_better += 1
        except Exception as e:
            logger.warning(f"Permutation {i} failed: {e}")
            continue

    p_value = (count_better + 1) / (n_permutations + 1)
    logger.info(f"Permutation p-value: {p_value:.4f}")
    return float(p_value)

def calculate_partial_correlation(
    X: np.ndarray,
    y: np.ndarray,
    control_vars: np.ndarray
) -> Tuple[float, float]:
    """
    Calculate partial correlation between X and y, controlling for control_vars.
    Returns (correlation_coefficient, p_value).
    """
    logger = logging.getLogger(__name__)
    logger.info("Calculating partial correlation")

    # Flatten inputs if necessary
    if X.ndim == 1:
        X = X.reshape(-1, 1)
    if control_vars.ndim == 1:
        control_vars = control_vars.reshape(-1, 1)

    # Combine X and control_vars for regression residuals
    # Residuals of X on Control
    # Residuals of y on Control
    # Correlation of residuals

    # Using scipy's partial correlation approach via regression residuals
    # We regress X on control_vars and get residuals
    # We regress y on control_vars and get residuals
    # Then correlate the residuals

    from sklearn.linear_model import LinearRegression

    # Fit X ~ Control
    reg_x = LinearRegression()
    reg_x.fit(control_vars, X)
    residuals_x = X - reg_x.predict(control_vars)

    # Fit y ~ Control
    reg_y = LinearRegression()
    reg_y.fit(control_vars, y)
    residuals_y = y - reg_y.predict(control_vars)

    # Calculate correlation between residuals
    # Flatten residuals for correlation
    residuals_x_flat = residuals_x.flatten()
    residuals_y_flat = residuals_y.flatten()

    corr, p_val = stats.pearsonr(residuals_x_flat, residuals_y_flat)

    logger.info(f"Partial correlation: {corr:.4f}, p-value: {p_val:.4f}")
    return float(corr), float(p_val)

def evaluate_model(
    model: Any,
    X_test: np.ndarray,
    y_test: np.ndarray,
    X_train: np.ndarray,
    y_train: np.ndarray,
    n_permutations: int = 100
) -> Dict[str, Any]:
    """
    Evaluate a trained model on test data and run permutation test.
    """
    logger = logging.getLogger(__name__)

    # Predict
    y_pred = model.predict(X_test)

    # Metrics
    metrics = calculate_metrics(y_test, y_pred)

    # Permutation test (on the trained model's performance vs random chance)
    # Note: Permutation test usually involves retraining, but here we use the provided model structure
    # For a rigorous test, we would retrain on permuted data.
    # We will attempt to use the model's fit method if available.
    p_value_perm = 0.0
    if hasattr(model, 'fit') and hasattr(model, 'predict'):
        try:
            p_value_perm = calculate_permutation_pvalue(model, X_train, y_train, n_permutations)
        except Exception as e:
            logger.error(f"Permutation test failed: {e}")
            p_value_perm = 1.0

    return {
        "metrics": metrics,
        "p_value_permutation": p_value_perm,
        "y_true": y_test.tolist(),
        "y_pred": y_pred.tolist()
    }

def save_results(results: Dict[str, Any], output_path: str) -> None:
    """Save evaluation results to a JSON file."""
    logger = logging.getLogger(__name__)
    logger.info(f"Saving results to {output_path}")

    # Ensure directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)

def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Evaluate model performance")
    parser.add_argument("--features-path", type=str, required=True, help="Path to features JSON")
    parser.add_argument("--model-selection-path", type=str, required=True, help="Path to model selection JSON")
    parser.add_argument("--split-config-path", type=str, required=True, help="Path to split config JSON")
    parser.add_argument("--model-path", type=str, required=True, help="Path to trained model pickle")
    parser.add_argument("--output-path", type=str, required=True, help="Path to output results JSON")
    parser.add_argument("--log-file", type=str, default=None, help="Path to log file")
    parser.add_argument("--n-permutations", type=int, default=100, help="Number of permutations for test")
    return parser.parse_args()

def main() -> None:
    """Main entry point for evaluation."""
    args = parse_args()
    logger = setup_logging(args.log_file)

    try:
        # Load data
        features = load_features(args.features_path)
        model_selection = load_model_selection(args.model_selection_path)
        split_config = load_split_config(args.split_config_path)
        model = load_model(args.model_path)

        # Check model type
        if model_selection.get("model_type") == "fail":
            logger.warning("Model selection failed. Skipping evaluation.")
            results = {
                "status": "fail",
                "message": model_selection.get("reason", "Unknown failure"),
                "r2": None,
                "mae": None,
                "p_value_permutation": None
            }
            save_results(results, args.output_path)
            return

        # Prepare data
        # Assuming features is a list of dicts with 'features' and 'target' keys
        # or a structured format. We need to adapt to the actual data structure.
        # For this implementation, we assume a structure:
        # features: list of { "features": [x1, x2, ...], "target": y }

        X = np.array([f["features"] for f in features])
        y = np.array([f["target"] for f in features])

        # Use split_config to get indices
        train_indices = split_config.get("train_indices", list(range(len(X))))
        test_indices = split_config.get("test_indices", list(range(len(X))))

        X_train, X_test = X[train_indices], X[test_indices]
        y_train, y_test = y[train_indices], y[test_indices]

        # Evaluate
        results = evaluate_model(model, X_test, y_test, X_train, y_train, args.n_permutations)

        # Add metadata
        results["model_type"] = model_selection.get("model_type")
        results["n_samples"] = len(X)
        results["n_train"] = len(X_train)
        results["n_test"] = len(X_test)

        # Save results
        save_results(results, args.output_path)
        logger.info("Evaluation completed successfully")

    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        raise
    except Exception as e:
        logger.error(f"Evaluation failed: {e}")
        raise

if __name__ == "__main__":
    main()