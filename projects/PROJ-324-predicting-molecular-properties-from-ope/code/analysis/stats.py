"""
Statistical analysis module for molecular property prediction.
Handles metrics calculation, statistical tests, and validation reporting.
"""
import os
import sys
import json
import logging
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy import stats
from typing import Dict, List, Tuple, Any, Optional
from pathlib import Path

# Ensure project root is in path
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from utils.config import get_runtime_config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def ensure_dirs():
    """Ensure output directories exist."""
    data_derived = project_root / "data" / "derived"
    data_raw = project_root / "data" / "raw"
    data_derived.mkdir(parents=True, exist_ok=True)
    data_raw.mkdir(parents=True, exist_ok=True)
    return data_derived, data_raw

def load_baseline_predictions(path: str) -> pd.DataFrame:
    """Load baseline predictions from CSV."""
    if not os.path.exists(path):
        raise FileNotFoundError(f"Baseline predictions file not found: {path}")
    df = pd.read_csv(path)
    return df

def load_rf_predictions(path: str) -> pd.DataFrame:
    """Load RF predictions from CSV."""
    if not os.path.exists(path):
        raise FileNotFoundError(f"RF predictions file not found: {path}")
    df = pd.read_csv(path)
    return df

def load_metadata(path: str) -> Dict:
    """Load dataset metadata JSON."""
    if not os.path.exists(path):
        logger.warning(f"Metadata file not found: {path}. Returning empty metadata.")
        return {}
    with open(path, 'r') as f:
        return json.load(f)

def calculate_absolute_errors(df: pd.DataFrame, pred_col: str, exp_col: str) -> np.ndarray:
    """Calculate absolute errors between predicted and experimental values."""
    if pred_col not in df.columns or exp_col not in df.columns:
        raise ValueError(f"Columns {pred_col} or {exp_col} not found in dataframe.")
    return np.abs(df[pred_col] - df[exp_col]).values

def calculate_metrics(errors: np.ndarray) -> Dict[str, float]:
    """Calculate MAE and RMSE from errors."""
    mae = np.mean(errors)
    rmse = np.sqrt(np.mean(errors**2))
    return {"mae": mae, "rmse": rmse}

def perform_wilcoxon_test(errors_baseline: np.ndarray, errors_rf: np.ndarray) -> Dict[str, Any]:
    """Perform paired Wilcoxon signed-rank test."""
    if len(errors_baseline) != len(errors_rf):
        raise ValueError("Error arrays must be of equal length for paired test.")
    stat, p_value = stats.wilcoxon(errors_baseline, errors_rf)
    # Calculate effect size (r)
    n = len(errors_baseline)
    r = stat / (n * (n + 1) / 2) if n > 0 else 0
    return {"statistic": float(stat), "p_value": float(p_value), "effect_size_r": float(r)}

def run_statistical_comparison() -> Dict[str, Any]:
    """Run full statistical comparison between baseline and RF models."""
    data_derived, _ = ensure_dirs()

    baseline_path = data_derived / "baseline_test_predictions.csv"
    rf_path = data_derived / "rf_test_predictions.csv"

    logger.info(f"Loading baseline predictions from {baseline_path}")
    baseline_df = load_baseline_predictions(str(baseline_path))
    logger.info(f"Loading RF predictions from {rf_path}")
    rf_df = load_rf_predictions(str(rf_path))

    # Calculate absolute errors
    baseline_errors = calculate_absolute_errors(baseline_df, 'predicted_value', 'experimental_value')
    rf_errors = calculate_absolute_errors(rf_df, 'predicted_value', 'experimental_value')

    # Calculate metrics
    baseline_metrics = calculate_metrics(baseline_errors)
    rf_metrics = calculate_metrics(rf_errors)

    # Perform Wilcoxon test
    test_results = perform_wilcoxon_test(baseline_errors, rf_errors)

    return {
        "baseline_metrics": baseline_metrics,
        "rf_metrics": rf_metrics,
        "wilcoxon_test": test_results
    }

def check_experimental_threshold() -> bool:
    """Check if >=50% of test set has experimental values."""
    data_derived, _ = ensure_dirs()
    test_path = data_derived / "test_set.csv"

    if not os.path.exists(test_path):
        logger.error(f"Test set not found at {test_path}")
        return False

    df = pd.read_csv(test_path)
    if 'source_type' not in df.columns:
        logger.warning("source_type column missing in test set. Assuming 0% experimental.")
        return False

    experimental_count = len(df[df['source_type'] == 'Experimental'])
    total_count = len(df)
    ratio = experimental_count / total_count if total_count > 0 else 0

    logger.info(f"Experimental ratio: {ratio:.2f} ({experimental_count}/{total_count})")
    return ratio >= 0.5

def save_comparison_results(results: Dict[str, Any], path: str):
    """Save comparison results to JSON."""
    with open(path, 'w') as f:
        json.dump(results, f, indent=2)

def generate_residual_plot(errors: np.ndarray, title: str, path: str):
    """Generate and save a residual distribution plot."""
    plt.figure(figsize=(8, 6))
    plt.hist(errors, bins=30, edgecolor='black', alpha=0.7)
    plt.title(title)
    plt.xlabel('Absolute Error')
    plt.ylabel('Frequency')
    plt.axvline(x=np.mean(errors), color='r', linestyle='--', label=f'Mean: {np.mean(errors):.2f}')
    plt.legend()
    plt.tight_layout()
    plt.savefig(path)
    plt.close()
    logger.info(f"Saved residual plot to {path}")

def generate_comparison_plots(baseline_metrics: Dict, rf_metrics: Dict) -> str:
    """Generate comparison bar plot of MAE and RMSE."""
    data_derived, _ = ensure_dirs()
    output_path = str(data_derived / "model_comparison.png")

    models = ['Baseline', 'RF']
    mae_vals = [baseline_metrics['mae'], rf_metrics['mae']]
    rmse_vals = [baseline_metrics['rmse'], rf_metrics['rmse']]

    x = np.arange(len(models))
    width = 0.35

    fig, ax = plt.subplots(figsize=(10, 6))
    rects1 = ax.bar(x - width/2, mae_vals, width, label='MAE')
    rects2 = ax.bar(x + width/2, rmse_vals, width, label='RMSE')

    ax.set_ylabel('Error Value')
    ax.set_title('Model Comparison: Baseline vs Random Forest')
    ax.set_xticks(x)
    ax.set_xticklabels(models)
    ax.legend()

    # Add value labels on bars
    for rect in rects1:
        height = rect.get_height()
        ax.annotate(f'{height:.2f}',
                    xy=(rect.get_x() + rect.get_width() / 2, height),
                    xytext=(0, 3),
                    textcoords="offset points",
                    ha='center', va='bottom')
    for rect in rects2:
        height = rect.get_height()
        ax.annotate(f'{height:.2f}',
                    xy=(rect.get_x() + rect.get_width() / 2, height),
                    xytext=(0, 3),
                    textcoords="offset points",
                    ha='center', va='bottom')

    plt.tight_layout()
    plt.savefig(output_path)
    plt.close()
    logger.info(f"Saved model comparison plot to {output_path}")
    return output_path

def calculate_baseline_metrics() -> Dict[str, float]:
    """Calculate baseline metrics on the held-out test set."""
    data_derived, _ = ensure_dirs()
    baseline_path = data_derived / "baseline_test_predictions.csv"

    if not os.path.exists(baseline_path):
        raise FileNotFoundError(f"Baseline predictions file not found: {baseline_path}")

    df = pd.read_csv(baseline_path)
    errors = calculate_absolute_errors(df, 'predicted_value', 'experimental_value')
    metrics = calculate_metrics(errors)

    # Generate residual plot
    plot_path = str(data_derived / "baseline_residuals.png")
    generate_residual_plot(errors, "Baseline Model Residual Distribution", plot_path)

    return metrics

def generate_validation_protocol_summary() -> str:
    """
    Generate a Validation Protocol Summary (Marie Curie Review Response).
    This explicitly states the absence of measurement_uncertainty and quantity_of_substance
    if T031 detected these fields as missing, reporting source limitations as derived facts.
    """
    data_derived, data_raw = ensure_dirs()

    # Load metadata generated by T031
    metadata_path = data_raw / "dataset_metadata.json"
    metadata = load_metadata(str(metadata_path))

    # Extract status fields, defaulting to "Not Available in Source" if missing
  # Extract status fields, defaulting to "Not Available in Source" if missing
    measurement_uncertainty_status = metadata.get(
        "measurement_uncertainty_status", "Not Available in Source"
    )
    quantity_of_substance_status = metadata.get(
        "quantity_of_substance_status", "Not Available in Source"
    )

    # Check if test set exists to report size
    test_set_path = data_derived / "test_set.csv"
    test_set_size = 0
    experimental_source = "Unknown"

    if os.path.exists(test_set_path):
        try:
            df = pd.read_csv(test_set_path)
            test_set_size = len(df)
            if 'source_type' in df.columns:
                # Determine primary source type in test set
                counts = df['source_type'].value_counts()
                if not counts.empty:
                    experimental_source = counts.index[0]
        except Exception as e:
            logger.warning(f"Could not read test set for size: {e}")

    # Construct the summary report
    summary = {
        "validation_protocol": {
            "description": "Summary of data validation and measurement standards per Marie Curie Review.",
            "dataset_source": metadata.get("source", "Unknown"),
            "test_set_size": test_set_size,
            "experimental_source_in_test_set": experimental_source,
            "measurement_standards": {
                "measurement_uncertainty": {
                    "status": measurement_uncertainty_status,
                    "note": "If 'Not Available in Source', the model validation relies on point estimates without reported uncertainty bounds. This limitation is explicitly acknowledged."
                },
                "quantity_of_substance": {
                    "status": quantity_of_substance_status,
                    "note": "If 'Not Available in Source', the specific quantity of substance used for measurement is not recorded in the source data."
                }
            },
            "limitations": [
                "Experimental data used for validation may lack reported uncertainty bounds.",
                "Physical covariates (pH, temperature) may be missing from source records.",
                "Validation is based on available point estimates from the dataset."
            ]
        }
    }

    # Write to JSON
    output_path = str(data_derived / "validation_summary.json")
    with open(output_path, 'w') as f:
        json.dump(summary, f, indent=2)

    logger.info(f"Generated Validation Protocol Summary at {output_path}")
    return output_path

def main():
    """Main entry point for statistical analysis."""
    logger.info("Starting statistical analysis module...")

    try:
        # 1. Check experimental threshold
        has_experimental = check_experimental_threshold()
        logger.info(f"Experimental threshold met: {has_experimental}")

        # 2. Run statistical comparison if data exists
        if os.path.exists(str(ensure_dirs()[0] / "baseline_test_predictions.csv")) and \
           os.path.exists(str(ensure_dirs()[0] / "rf_test_predictions.csv")):
            logger.info("Running statistical comparison...")
            comparison_results = run_statistical_comparison()
            save_comparison_results(
                comparison_results,
                str(ensure_dirs()[0] / "statistical_comparison_results.json")
            )

            # Generate plots
            generate_comparison_plots(
                comparison_results["baseline_metrics"],
                comparison_results["rf_metrics"]
            )
        else:
            logger.warning("Prediction files not found. Skipping comparison plots.")

        # 3. Calculate baseline metrics (if baseline predictions exist)
        if os.path.exists(str(ensure_dirs()[0] / "baseline_test_predictions.csv")):
            logger.info("Calculating baseline metrics...")
            baseline_metrics = calculate_baseline_metrics()
            logger.info(f"Baseline Metrics: MAE={baseline_metrics['mae']:.4f}, RMSE={baseline_metrics['rmse']:.4f}")

        # 4. Generate Validation Protocol Summary (T043)
        logger.info("Generating Validation Protocol Summary (Marie Curie Response)...")
        generate_validation_protocol_summary()

        logger.info("Statistical analysis completed successfully.")

    except Exception as e:
        logger.error(f"Error during statistical analysis: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()