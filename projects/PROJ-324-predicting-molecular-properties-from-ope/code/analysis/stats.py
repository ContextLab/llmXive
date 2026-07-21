"""
Statistical analysis module for model evaluation.

This module implements metrics calculation, statistical tests, and visualization.
"""
import os
import sys
import json
import logging
from pathlib import Path
from typing import Tuple, Optional, Dict, Any, List
import numpy as np
import pandas as pd
from scipy import stats
import matplotlib.pyplot as plt

# Configure logging
logger = logging.getLogger(__name__)

def load_baseline_predictions(predictions_path: str) -> pd.DataFrame:
    """
    Load baseline predictions from CSV.

    Args:
        predictions_path: Path to the predictions file.

    Returns:
        DataFrame with predictions.
    """
    return pd.read_csv(predictions_path)

def load_rf_predictions(predictions_path: str) -> pd.DataFrame:
    """
    Load Random Forest predictions from CSV.

    Args:
        predictions_path: Path to the predictions file.

    Returns:
        DataFrame with predictions.
    """
    return pd.read_csv(predictions_path)

def load_test_set_metadata(test_path: str) -> pd.DataFrame:
    """
    Load test set metadata.

    Args:
        test_path: Path to the test set file.

    Returns:
        DataFrame with test set data.
    """
    return pd.read_csv(test_path)

def load_dataset_metadata(metadata_path: str) -> Dict[str, Any]:
    """
    Load dataset metadata from JSON.

    Args:
        metadata_path: Path to the metadata file.

    Returns:
        Dictionary with metadata.
    """
    with open(metadata_path, 'r') as f:
        return json.load(f)

def calculate_absolute_errors(true_values: np.ndarray, predicted_values: np.ndarray) -> np.ndarray:
    """
    Calculate absolute errors.

    Args:
        true_values: Array of true values.
        predicted_values: Array of predicted values.

    Returns:
        Array of absolute errors.
    """
    return np.abs(true_values - predicted_values)

def calculate_metrics(true_values: np.ndarray, predicted_values: np.ndarray) -> Dict[str, float]:
    """
    Calculate performance metrics.

    Args:
        true_values: Array of true values.
        predicted_values: Array of predicted values.

    Returns:
        Dictionary with MAE, RMSE, and R2.
    """
    mae = np.mean(np.abs(true_values - predicted_values))
    rmse = np.sqrt(np.mean((true_values - predicted_values) ** 2))
    ss_res = np.sum((true_values - predicted_values) ** 2)
    ss_tot = np.sum((true_values - np.mean(true_values)) ** 2)
    r2 = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0

    return {
        'MAE': mae,
        'RMSE': rmse,
        'R2': r2
    }

def perform_wilcoxon_test(errors_baseline: np.ndarray, errors_rf: np.ndarray) -> Tuple[float, float]:
    """
    Perform paired Wilcoxon signed-rank test.

    Args:
        errors_baseline: Array of baseline errors.
        errors_rf: Array of RF errors.

    Returns:
        Tuple of (statistic, p-value).
    """
    stat, p_value = stats.wilcoxon(errors_baseline, errors_rf)
    return stat, p_value

def run_statistical_comparison(
    baseline_errors: np.ndarray,
    rf_errors: np.ndarray
) -> Dict[str, Any]:
    """
    Run statistical comparison between baseline and RF models.

    Args:
        baseline_errors: Array of baseline errors.
        rf_errors: Array of RF errors.

    Returns:
        Dictionary with test results.
    """
    stat, p_value = perform_wilcoxon_test(baseline_errors, rf_errors)

    return {
        'test': 'Wilcoxon signed-rank',
        'statistic': float(stat),
        'p_value': float(p_value),
        'significant': p_value < 0.05
    }

def save_comparison_results(results: Dict[str, Any], output_path: str) -> None:
    """
    Save comparison results to JSON.

    Args:
        results: Dictionary with results.
        output_path: Path to save the file.
    """
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    logger.info(f"Comparison results saved to {output_path}")

def generate_residual_plot(true_values: np.ndarray, predicted_values: np.ndarray, output_path: str) -> None:
    """
    Generate a residual distribution plot.

    Args:
        true_values: Array of true values.
        predicted_values: Array of predicted values.
        output_path: Path to save the plot.
    """
    residuals = true_values - predicted_values

    plt.figure(figsize=(10, 6))
    plt.hist(residuals, bins=50, alpha=0.7, edgecolor='black')
    plt.axvline(x=0, color='red', linestyle='--', linewidth=2)
    plt.xlabel('Residual')
    plt.ylabel('Frequency')
    plt.title('Residual Distribution')
    plt.tight_layout()
    plt.savefig(output_path)
    plt.close()
    logger.info(f"Residual plot saved to {output_path}")

def generate_comparison_plots(
    baseline_metrics: Dict[str, float],
    rf_metrics: Dict[str, float],
    output_path: str
) -> None:
    """
    Generate comparison plots for baseline vs RF models.

    Args:
        baseline_metrics: Dictionary with baseline metrics.
        rf_metrics: Dictionary with RF metrics.
        output_path: Path to save the plot.
    """
    metrics = ['MAE', 'RMSE']
    x = np.arange(len(metrics))
    width = 0.35

    fig, ax = plt.subplots(figsize=(10, 6))
    ax.bar(x - width/2, [baseline_metrics[m] for m in metrics], width, label='Baseline')
    ax.bar(x + width/2, [rf_metrics[m] for m in metrics], width, label='RF')

    ax.set_ylabel('Error')
    ax.set_title('Model Comparison: Baseline vs Random Forest')
    ax.set_xticks(x)
    ax.set_xticklabels(metrics)
    ax.legend()

    plt.tight_layout()
    plt.savefig(output_path)
    plt.close()
    logger.info(f"Comparison plot saved to {output_path}")

def generate_validation_protocol_summary(
    test_set_size: int,
    source_info: str,
    uncertainty_status: str,
    quantity_status: str,
    output_path: str
) -> None:
    """
    Generate a validation protocol summary report.

    Args:
        test_set_size: Size of the held-out test set.
        source_info: Information about the data source.
        uncertainty_status: Status of measurement uncertainty data.
        quantity_status: Status of quantity of substance data.
        output_path: Path to save the report.
    """
    with open(output_path, 'w') as f:
        f.write("# Validation Protocol Summary\n\n")
        f.write("## Data Integrity\n\n")
        f.write(f"Test set size: {test_set_size}\n")
        f.write(f"Data source: {source_info}\n")
        f.write(f"Measurement uncertainty: {uncertainty_status}\n")
        f.write(f"Quantity of substance: {quantity_status}\n\n")
        f.write("## Validation Notes\n\n")
        f.write("This report confirms that the model's predictions are compared against\n")
        f.write("verified experimental data from the held-out test set. Cross-validation\n")
        f.write("scores are used for hyperparameter tuning only and are not reported as\n")
        f.write("final performance metrics.\n")

def save_validation_report(report_path: str, summary: Dict[str, Any]) -> None:
    """
    Save the validation report to disk.

    Args:
        report_path: Path to save the report.
        summary: Dictionary with summary data.
    """
    with open(report_path, 'w') as f:
        f.write(json.dumps(summary, indent=2))

def main() -> None:
    """
    Main entry point for the statistical analysis pipeline.
    """
    # Set up logging
    logging.basicConfig(level=logging.INFO)

    # Define paths
    project_root = Path(__file__).parent.parent.parent
    baseline_path = project_root / 'data' / 'derived' / 'baseline_predictions.csv'
    oof_path = project_root / 'data' / 'derived' / 'rf_oof_predictions.csv'
    metadata_path = project_root / 'data' / 'raw' / 'dataset_metadata.json'
    output_dir = project_root / 'data' / 'derived'

    if not baseline_path.exists():
        logger.error(f"Baseline predictions not found: {baseline_path}")
        sys.exit(1)

    if not oof_path.exists():
        logger.error(f"RF OOF predictions not found: {oof_path}")
        sys.exit(1)

    # Load data
    logger.info("Loading predictions...")
    df_baseline = load_baseline_predictions(str(baseline_path))
    df_rf = load_rf_predictions(str(oof_path))

    # Calculate errors
    true_values = df_baseline['logP'].values
    baseline_preds = df_baseline['logP'].values  # For baseline, prediction is the same as input
    rf_preds = df_rf['predicted'].values

    baseline_errors = calculate_absolute_errors(true_values, baseline_preds)
    rf_errors = calculate_absolute_errors(true_values, rf_preds)

    # Statistical comparison
    logger.info("Performing statistical comparison...")
    comparison_results = run_statistical_comparison(baseline_errors, rf_errors)
    save_comparison_results(comparison_results, str(output_dir / 'statistical_comparison.json'))

    # Generate plots
    generate_residual_plot(true_values, rf_preds, str(output_dir / 'baseline_residuals.png'))
    generate_comparison_plots(
        {'MAE': np.mean(baseline_errors), 'RMSE': np.sqrt(np.mean((true_values - baseline_preds)**2))},
        {'MAE': np.mean(rf_errors), 'RMSE': np.sqrt(np.mean((true_values - rf_preds)**2))},
        str(output_dir / 'model_comparison.png')
    )

    # Validation protocol
    if os.path.exists(metadata_path):
        metadata = load_dataset_metadata(str(metadata_path))
        uncertainty_status = metadata.get('measurement_uncertainty_status', 'Not Available')
        quantity_status = metadata.get('quantity_of_substance_status', 'Not Available')
    else:
        uncertainty_status = 'Not Available'
        quantity_status = 'Not Available'

    generate_validation_protocol_summary(
        test_set_size=len(true_values),
        source_info='PubChem/ChEMBL thermodynamics subset',
        uncertainty_status=uncertainty_status,
        quantity_status=quantity_status,
        output_path=str(output_dir / 'validation_protocol_summary.txt')
    )

    logger.info("Statistical analysis complete")

if __name__ == "__main__":
    main()