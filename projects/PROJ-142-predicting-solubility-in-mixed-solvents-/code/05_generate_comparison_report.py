"""
Generate comparison report for model training results.

This script reads the evaluation metrics and statistical test results,
then generates a comprehensive comparison report in JSON format.
"""
import json
import os
import sys
from pathlib import Path
from utils.constants import DATA_DIR
from utils.errors import CustomDataError


def load_pickle(filepath: Path) -> dict:
    """Load a pickle file and return its contents."""
    try:
        with open(filepath, 'rb') as f:
            return pickle.load(f)
    except FileNotFoundError:
        raise CustomDataError(f"File not found: {filepath}")
    except Exception as e:
        raise CustomDataError(f"Error loading pickle file {filepath}: {e}")


def load_json(filepath: Path) -> dict:
    """Load a JSON file and return its contents."""
    try:
        with open(filepath, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        raise CustomDataError(f"File not found: {filepath}")
    except json.JSONDecodeError as e:
        raise CustomDataError(f"Invalid JSON in {filepath}: {e}")


def calculate_absolute_r2_threshold(metrics: dict, threshold: float = 0.70) -> bool:
    """
    Check if the R² metric exceeds the absolute threshold.

    Args:
        metrics: Dictionary containing evaluation metrics.
        threshold: Minimum acceptable R² value (default 0.70).

    Returns:
        True if R² > threshold, False otherwise.
    """
    r2 = metrics.get('r2', 0.0)
    return r2 > threshold


def generate_report(metrics: dict, stat_results: dict, models_info: dict) -> dict:
    """
    Generate a comprehensive comparison report.

    Args:
        metrics: Evaluation metrics dictionary.
        stat_results: Statistical test results dictionary.
        models_info: Information about trained models.

    Returns:
        Dictionary containing the comparison report.
    """
    # Determine if the model comparison is statistically significant
    p_value = stat_results.get('p_value', 1.0)
    is_significant = p_value < 0.05

    # Determine if R² gate passes
    r2_pass = calculate_absolute_r2_threshold(metrics)

    # Build the report
    report = {
        "report_type": "model_comparison",
        "generated_at": None,  # Will be set by caller if needed
        "metrics_summary": {
            "rmse": metrics.get('rmse', None),
            "r2": metrics.get('r2', None),
            "mae": metrics.get('mae', None)
        },
        "statistical_significance": {
            "test_type": "paired_t_test",
            "p_value": p_value,
            "is_significant": is_significant,
            "alpha": 0.05,
            "conclusion": "XGBoost significantly outperforms Abraham baseline" if is_significant else "No significant difference between models"
        },
        "model_comparison": {
            "xgboost": {
                "rmse": models_info.get('xgboost_rmse', None),
                "r2": models_info.get('xgboost_r2', None)
            },
            "abraham_baseline": {
                "rmse": models_info.get('abraham_rmse', None),
                "r2": models_info.get('abraham_r2', None)
            }
        },
        "gate_results": {
            "r2_gate": "PASS" if r2_pass else "FAIL",
            "statistical_gate": "PASS" if is_significant else "FAIL"
        },
        "recommendation": "Proceed with XGBoost model" if (r2_pass and is_significant) else "Re-evaluate model strategy"
    }

    return report


def main():
    """Main entry point for generating the comparison report."""
    # Define paths
    metrics_path = DATA_DIR / "artifacts" / "evaluation_metrics.json"
    stat_results_path = DATA_DIR / "artifacts" / "statistical_test_results.json"
    models_path = DATA_DIR / "artifacts" / "trained_models.pkl"
    report_path = DATA_DIR / "artifacts" / "training_report.json"

    # Ensure artifacts directory exists
    report_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        # Load evaluation metrics
        print(f"Loading metrics from {metrics_path}...")
        metrics = load_json(metrics_path)

        # Load statistical test results
        print(f"Loading statistical results from {stat_results_path}...")
        stat_results = load_json(stat_results_path)

        # Load trained models info (we only need metrics from here)
        print(f"Loading model info from {models_path}...")
        models_data = load_pickle(models_path)

        # Extract model-specific metrics from the loaded data
        # Assuming models_data contains 'metrics' key with model breakdown
        models_info = {
            'xgboost_rmse': models_data.get('metrics', {}).get('xgboost', {}).get('rmse'),
            'xgboost_r2': models_data.get('metrics', {}).get('xgboost', {}).get('r2'),
            'abraham_rmse': models_data.get('metrics', {}).get('abraham', {}).get('rmse'),
            'abraham_r2': models_data.get('metrics', {}).get('abraham', {}).get('r2')
        }

        # Generate the report
        print("Generating comparison report...")
        report = generate_report(metrics, stat_results, models_info)

        # Write the report to disk
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2)

        print(f"Report successfully written to {report_path}")
        print(f"R² Gate: {report['gate_results']['r2_gate']}")
        print(f"Statistical Significance: {report['statistical_significance']['is_significant']} (p={stat_results.get('p_value', 'N/A')})")
        print(f"Recommendation: {report['recommendation']}")

    except CustomDataError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()