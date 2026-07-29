"""
Bootstrap resampling for confidence intervals on held-out test set.

This module implements bootstrap resampling to estimate the uncertainty
of model performance metrics (R², RMSE) on a held-out test set.
"""
import os
import sys
import logging
import json
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional

import numpy as np
import pandas as pd
from sklearn.metrics import r2_score, mean_squared_error
from sklearn.model_selection import train_test_split

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "code"))

from seed import init_reproducibility
from config import (
    get_data_processed_dir,
    get_data_outputs_dir,
    get_bootstrap_iterations,
    get_cv_folds,
    get_log_level,
    get_log_format
)
from utils.logging_config import get_logger
from utils.error_handlers import ModelTrainingError, DataValidationError

logger = get_logger(__name__)


def bootstrap_metrics(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    n_iterations: int,
    random_state: Optional[int] = None
) -> Dict[str, Dict[str, float]]:
    """
    Compute bootstrap confidence intervals for R² and RMSE.

    Args:
        y_true: Ground truth target values.
        y_pred: Predicted target values from the model.
        n_iterations: Number of bootstrap iterations.
        random_state: Random seed for reproducibility.

    Returns:
        Dictionary containing bootstrap statistics for each metric:
        {
            'r2': {
                'mean': float,
                'std': float,
                'ci_lower': float (2.5th percentile),
                'ci_upper': float (97.5th percentile)
            },
            'rmse': {
                'mean': float,
                'std': float,
                'ci_lower': float (2.5th percentile),
                'ci_upper': float (97.5th percentile)
            }
        }
    """
    if random_state is not None:
        np.random.seed(random_state)

    n_samples = len(y_true)
    if n_samples == 0:
        raise DataValidationError("Cannot bootstrap: empty input arrays.")

    r2_scores = []
    rmse_scores = []

    for i in range(n_iterations):
        # Sample with replacement
        indices = np.random.choice(n_samples, size=n_samples, replace=True)
        y_true_boot = y_true[indices]
        y_pred_boot = y_pred[indices]

        # Compute metrics
        r2 = r2_score(y_true_boot, y_pred_boot)
        rmse = np.sqrt(mean_squared_error(y_true_boot, y_pred_boot))

        r2_scores.append(r2)
        rmse_scores.append(rmse)

    r2_scores = np.array(r2_scores)
    rmse_scores = np.array(rmse_scores)

    return {
        'r2': {
            'mean': float(np.mean(r2_scores)),
            'std': float(np.std(r2_scores)),
            'ci_lower': float(np.percentile(r2_scores, 2.5)),
            'ci_upper': float(np.percentile(r2_scores, 97.5))
        },
        'rmse': {
            'mean': float(np.mean(rmse_scores)),
            'std': float(np.std(rmse_scores)),
            'ci_lower': float(np.percentile(rmse_scores, 2.5)),
            'ci_upper': float(np.percentile(rmse_scores, 97.5))
        }
    }


class BootstrapEvaluator:
    """
    Bootstrap resampling evaluator for model performance metrics.
    """

    def __init__(
        self,
        n_iterations: Optional[int] = None,
        random_state: Optional[int] = None,
        test_size: float = 0.2
    ):
        """
        Initialize the BootstrapEvaluator.

        Args:
            n_iterations: Number of bootstrap iterations. Defaults to config value.
            random_state: Random seed for reproducibility.
            test_size: Fraction of data to use for test set.
        """
        self.n_iterations = n_iterations or get_bootstrap_iterations()
        self.random_state = random_state
        self.test_size = test_size

        logger.info(f"BootstrapEvaluator initialized with {self.n_iterations} iterations")

    def evaluate(
        self,
        X: pd.DataFrame,
        y: pd.Series,
        model,
        feature_names: List[str]
    ) -> Dict[str, Any]:
        """
        Perform bootstrap evaluation on a trained model.

        Args:
            X: Feature matrix (training + test).
            y: Target values (training + test).
            model: Trained model with a `predict` method.
            feature_names: List of feature names.

        Returns:
            Dictionary containing:
            - 'bootstrap_results': Bootstrap statistics for R² and RMSE
            - 'test_set_size': Number of samples in test set
            - 'iterations': Number of bootstrap iterations performed
        """
        # Split into train and test
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=self.test_size, random_state=self.random_state
        )

        # Retrain model on bootstrap samples? No, we evaluate on held-out test set
        # by resampling the test set predictions.

        # Get predictions on the full test set
        y_pred_test = model.predict(X_test)

        # Perform bootstrap on test set metrics
        bootstrap_results = bootstrap_metrics(
            y_true=y_test.values,
            y_pred=y_pred_test,
            n_iterations=self.n_iterations,
            random_state=self.random_state
        )

        # Also compute point estimates on the original test set
        point_r2 = r2_score(y_test, y_pred_test)
        point_rmse = np.sqrt(mean_squared_error(y_test, y_pred_test))

        return {
            'bootstrap_results': bootstrap_results,
            'point_estimates': {
                'r2': point_r2,
                'rmse': point_rmse
            },
            'test_set_size': len(y_test),
            'iterations': self.n_iterations,
            'feature_names': feature_names
        }


def main():
    """
    Main entry point for bootstrap evaluation.

    This function:
    1. Loads the validated dataset
    2. Loads pre-trained models (XGBoost and Linear Regression)
    3. Performs bootstrap resampling on held-out test sets
    4. Saves results to data/processed/bootstrap_results.json
    """
    # Initialize reproducibility
    seed_info = init_reproducibility()
    logger.info(f"Reproducibility initialized: {seed_info}")

    # Setup paths
    data_processed_dir = get_data_processed_dir()
    data_outputs_dir = get_data_outputs_dir()
    models_dir = Path("models")

    # Ensure output directory exists
    data_outputs_dir.mkdir(parents=True, exist_ok=True)

    # Load validated dataset
    validated_data_path = data_processed_dir / "solder_hardness_validated.csv"
    if not validated_data_path.exists():
        raise DataValidationError(
            f"Validated dataset not found at {validated_data_path}. "
            "Please run the ingestion pipeline first."
        )

    logger.info(f"Loading validated dataset from {validated_data_path}")
    df = pd.read_csv(validated_data_path)

    # Identify composition columns and target
    # Assuming the dataset has columns for elements and a 'hardness_hv' target
    composition_cols = [col for col in df.columns if col not in ['hardness_hv', 'alloy_id', 'source']]
    target_col = 'hardness_hv'

    if target_col not in df.columns:
        raise DataValidationError(
            f"Target column '{target_col}' not found in dataset. "
            f"Available columns: {list(df.columns)}"
        )

    X = df[composition_cols]
    y = df[target_col]

    logger.info(f"Dataset loaded: {len(df)} samples, {len(composition_cols)} features")

    # Load pre-trained models
    results = {}

    # Try loading XGBoost model
    xgb_model_path = models_dir / "xgboost_model.pkl"
    if xgb_model_path.exists():
        import joblib
        xgb_model = joblib.load(xgb_model_path)
        logger.info("Loaded XGBoost model")

        # Evaluate XGBoost
        xgb_evaluator = BootstrapEvaluator(
            n_iterations=get_bootstrap_iterations(),
            random_state=42
        )
        xgb_results = xgb_evaluator.evaluate(X, y, xgb_model, composition_cols)
        results['xgboost'] = xgb_results
        logger.info(f"XGBoost bootstrap R²: {xgb_results['bootstrap_results']['r2']['mean']:.4f} "
                    f"([{xgb_results['bootstrap_results']['r2']['ci_lower']:.4f}, "
                    f"{xgb_results['bootstrap_results']['r2']['ci_upper']:.4f}])")
    else:
        logger.warning(f"XGBoost model not found at {xgb_model_path}. Skipping.")

    # Try loading Linear Regression model
    lr_model_path = models_dir / "linear_model.pkl"
    if lr_model_path.exists():
        import joblib
        lr_model = joblib.load(lr_model_path)
        logger.info("Loaded Linear Regression model")

        # Evaluate Linear Regression
        lr_evaluator = BootstrapEvaluator(
            n_iterations=get_bootstrap_iterations(),
            random_state=42
        )
        lr_results = lr_evaluator.evaluate(X, y, lr_model, composition_cols)
        results['linear_regression'] = lr_results
        logger.info(f"Linear Regression bootstrap R²: {lr_results['bootstrap_results']['r2']['mean']:.4f} "
                    f"([{lr_results['bootstrap_results']['r2']['ci_lower']:.4f}, "
                    f"{lr_results['bootstrap_results']['r2']['ci_upper']:.4f}])")
    else:
        logger.warning(f"Linear Regression model not found at {lr_model_path}. Skipping.")

    if not results:
        logger.error("No models found to evaluate. Please train models first.")
        raise ModelTrainingError("No trained models found for bootstrap evaluation.")

    # Save results
    output_path = data_processed_dir / "bootstrap_results.json"
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)

    logger.info(f"Bootstrap results saved to {output_path}")

    # Also save a summary to outputs directory
    summary_path = data_outputs_dir / "bootstrap_summary.json"
    summary = {
        'xgboost': results.get('xgboost', {}).get('bootstrap_results', {}),
        'linear_regression': results.get('linear_regression', {}).get('bootstrap_results', {}),
        'iterations': get_bootstrap_iterations(),
        'test_size_fraction': 0.2
    }
    with open(summary_path, 'w') as f:
        json.dump(summary, f, indent=2)

    logger.info(f"Bootstrap summary saved to {summary_path}")

    return results


if __name__ == "__main__":
    main()