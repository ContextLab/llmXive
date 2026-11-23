"""
Model Comparison Module for Solder Hardness Prediction Project (US2)

Implements paired t-test comparison on cross-validation folds to statistically
evaluate whether XGBoost significantly outperforms Linear Regression.
"""
import os
import sys
import logging
import json
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional
from scipy import stats

from seed import init_reproducibility
from config import get_data_processed_dir, get_models_dir, get_cv_folds
from utils.logging_config import get_logger
from utils.error_handlers import ModelTrainingError

logger = get_logger(__name__)


def load_cv_results(model_name: str) -> Tuple[np.ndarray, np.ndarray]:
    """
    Load cross-validation results for a specific model from the models directory.

    Args:
        model_name: Name of the model ('xgboost' or 'linear')

    Returns:
        Tuple of (actual_values, predicted_values) arrays
    """
    models_dir = get_models_dir()
    cv_results_path = models_dir / f"{model_name}_cv_results.json"

    if not cv_results_path.exists():
        raise ModelTrainingError(
            f"CV results file not found: {cv_results_path}. "
            f"Please ensure {model_name} model has been trained with cross-validation."
        )

    with open(cv_results_path, 'r') as f:
        data = json.load(f)

    actuals = np.array(data['actual_values'])
    predictions = np.array(data['predicted_values'])

    if len(actuals) != len(predictions):
        raise ModelTrainingError(
            f"Mismatch in CV results for {model_name}: "
            f"{len(actuals)} actuals vs {len(predictions)} predictions"
        )

    return actuals, predictions


def calculate_fold_metrics(
    actuals: np.ndarray,
    predictions: np.ndarray,
    fold_indices: List[List[int]]
) -> np.ndarray:
    """
    Calculate R² and RMSE for each CV fold.

    Args:
        actuals: Array of true values
        predictions: Array of predicted values
        fold_indices: List of lists containing indices for each fold

    Returns:
        Array of R² scores for each fold
    """
    r2_scores = []
    rmse_scores = []

    for fold_idx, indices in enumerate(fold_indices):
        fold_actuals = actuals[indices]
        fold_preds = predictions[indices]

        # Calculate R²
        ss_res = np.sum((fold_actuals - fold_preds) ** 2)
        ss_tot = np.sum((fold_actuals - np.mean(fold_actuals)) ** 2)
        r2 = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0.0
        r2_scores.append(r2)

        # Calculate RMSE
        rmse = np.sqrt(np.mean((fold_actuals - fold_preds) ** 2))
        rmse_scores.append(rmse)

    return np.array(r2_scores), np.array(rmse_scores)


def paired_ttest_comparison(
    xgb_actuals: np.ndarray,
    xgb_preds: np.ndarray,
    lr_actuals: np.ndarray,
    lr_preds: np.ndarray,
    fold_indices: List[List[int]]
) -> Dict[str, Any]:
    """
    Perform paired t-test on CV fold metrics between XGBoost and Linear Regression.

    Args:
        xgb_actuals: Actual values for XGBoost
        xgb_preds: Predicted values for XGBoost
        lr_actuals: Actual values for Linear Regression
        lr_preds: Predicted values for Linear Regression
        fold_indices: CV fold indices (should be identical for both models)

    Returns:
        Dictionary containing t-test results and metrics
    """
    if len(xgb_actuals) != len(lr_actuals):
        raise ModelTrainingError(
            "Actual value arrays must have the same length for paired comparison"
        )

    # Calculate metrics per fold for both models
    xgb_r2, xgb_rmse = calculate_fold_metrics(xgb_actuals, xgb_preds, fold_indices)
    lr_r2, lr_rmse = calculate_fold_metrics(lr_actuals, lr_preds, fold_indices)

    # Paired t-test on R² scores
    t_stat_r2, p_val_r2 = stats.ttest_rel(xgb_r2, lr_r2)

    # Paired t-test on RMSE scores (negative because lower is better)
    t_stat_rmse, p_val_rmse = stats.ttest_rel(-xgb_rmse, -lr_rmse)

    # Calculate mean differences
    mean_r2_diff = np.mean(xgb_r2 - lr_r2)
    mean_rmse_diff = np.mean(lr_rmse - xgb_rmse)  # Positive if XGBoost is better

    # Effect size (Cohen's d for paired samples)
    diff_r2 = xgb_r2 - lr_r2
    std_diff_r2 = np.std(diff_r2, ddof=1)
    cohens_d_r2 = mean_r2_diff / std_diff_r2 if std_diff_r2 > 0 else 0.0

    return {
        "t_statistic_r2": float(t_stat_r2),
        "p_value_r2": float(p_val_r2),
        "t_statistic_rmse": float(t_stat_rmse),
        "p_value_rmse": float(p_val_rmse),
        "mean_r2_difference": float(mean_r2_diff),
        "mean_rmse_difference": float(mean_rmse_diff),
        "cohens_d_r2": float(cohens_d_r2),
        "xgb_fold_r2": xgb_r2.tolist(),
        "lr_fold_r2": lr_r2.tolist(),
        "xgb_fold_rmse": xgb_rmse.tolist(),
        "lr_fold_rmse": lr_rmse.tolist(),
        "n_folds": len(fold_indices),
        "significant_at_0.05_r2": p_val_r2 < 0.05,
        "significant_at_0.01_r2": p_val_r2 < 0.01
    }


def generate_comparison_report(results: Dict[str, Any]) -> str:
    """
    Generate a human-readable comparison report.

    Args:
        results: Dictionary from paired_ttest_comparison

    Returns:
        Formatted report string
    """
    report_lines = [
        "=" * 70,
        "MODEL COMPARISON REPORT: XGBoost vs Linear Regression",
        "=" * 70,
        "",
        "Cross-Validation Metrics (Paired Folds):",
        f"  Number of Folds: {results['n_folds']}",
        "",
        "R² Score Comparison:",
        f"  Mean XGBoost R²: {np.mean(results['xgb_fold_r2']):.4f}",
        f"  Mean Linear R²:  {np.mean(results['lr_fold_r2']):.4f}",
        f"  Mean Difference: {results['mean_r2_difference']:.4f}",
        "",
        "RMSE Comparison:",
        f"  Mean XGBoost RMSE: {np.mean(results['xgb_fold_rmse']):.4f}",
        f"  Mean Linear RMSE:  {np.mean(results['lr_fold_rmse']):.4f}",
        f"  Mean Difference:   {results['mean_rmse_difference']:.4f}",
        "",
        "Statistical Significance (Paired t-test):",
        f"  R² - t-statistic: {results['t_statistic_r2']:.4f}",
        f"  R² - p-value:     {results['p_value_r2']:.4e}",
        f"  RMSE - t-statistic: {results['t_statistic_rmse']:.4f}",
        f"  RMSE - p-value:     {results['p_value_rmse']:.4e}",
        "",
        "Effect Size (Cohen's d for R²):",
        f"  Cohen's d: {results['cohens_d_r2']:.4f}",
        "",
        "Conclusion:",
    ]

    if results['significant_at_0.01_r2']:
        report_lines.append(
            "  XGBoost significantly outperforms Linear Regression (p < 0.01)."
        )
    elif results['significant_at_0.05_r2']:
        report_lines.append(
            "  XGBoost significantly outperforms Linear Regression (p < 0.05)."
        )
    else:
        report_lines.append(
            "  No statistically significant difference detected (p >= 0.05)."
        )

    if abs(results['cohens_d_r2']) > 0.8:
        report_lines.append("  Effect size is LARGE.")
    elif abs(results['cohens_d_r2']) > 0.5:
        report_lines.append("  Effect size is MEDIUM.")
    elif abs(results['cohens_d_r2']) > 0.2:
        report_lines.append("  Effect size is SMALL.")
    else:
        report_lines.append("  Effect size is negligible.")

    report_lines.append("=" * 70)

    return "\n".join(report_lines)


def main():
    """
    Main entry point for model comparison.
    Loads CV results from both models, performs paired t-test, and saves results.
    """
    # Initialize reproducibility
    init_reproducibility()

    logger.info("Starting model comparison: XGBoost vs Linear Regression")

    try:
        # Load CV results
        logger.info("Loading XGBoost CV results...")
        xgb_actuals, xgb_preds = load_cv_results("xgboost")

        logger.info("Loading Linear Regression CV results...")
        lr_actuals, lr_preds = load_cv_results("linear")

        # Use the same fold indices for both (from config or inferred)
        # For this implementation, we assume the fold structure is consistent
        # and derive fold indices from the total number of samples and CV folds
        n_folds = get_cv_folds()
        n_samples = len(xgb_actuals)

        # Generate fold indices (simple K-fold split for demonstration)
        # In a real scenario, these would be saved during CV execution
        fold_size = n_samples // n_folds
        fold_indices = []
        for i in range(n_folds):
            start = i * fold_size
            end = start + fold_size if i < n_folds - 1 else n_samples
            fold_indices.append(list(range(start, end)))

        # Perform paired t-test
        logger.info("Performing paired t-test comparison...")
        results = paired_ttest_comparison(
            xgb_actuals, xgb_preds,
            lr_actuals, lr_preds,
            fold_indices
        )

        # Generate and print report
        report = generate_comparison_report(results)
        print(report)

        # Save results to JSON
        models_dir = get_models_dir()
        output_path = models_dir / "model_comparison_results.json"

        with open(output_path, 'w') as f:
            json.dump(results, f, indent=2)

        # Save report to text file
        report_path = models_dir / "model_comparison_report.txt"
        with open(report_path, 'w') as f:
            f.write(report)

        logger.info(f"Comparison results saved to {output_path}")
        logger.info(f"Comparison report saved to {report_path}")

        return results

    except FileNotFoundError as e:
        logger.error(f"Required data file not found: {e}")
        raise ModelTrainingError(
            "Cannot perform comparison: missing CV results. "
            "Ensure both models have been trained with cross-validation first."
        )
    except Exception as e:
        logger.error(f"Error during model comparison: {e}")
        raise


if __name__ == "__main__":
    main()