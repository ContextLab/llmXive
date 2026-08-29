"""
Statistical tests implementation for User Story 2.
Implements paired t-test, Cohen's d, and Confidence Intervals.
"""
import json
import logging
import sys
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional
import numpy as np
from scipy import stats

# Ensure parent directory is in path for imports if running as script
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

logger = logging.getLogger(__name__)

def load_predictions(predictions_file: Path) -> Dict[str, np.ndarray]:
    """Load prediction errors from the JSON file."""
    if not predictions_file.exists():
        raise FileNotFoundError(f"Predictions file not found: {predictions_file}")
    
    with open(predictions_file, 'r') as f:
        data = json.load(f)
    
    # Expecting keys like 'gnn_errors', 'rf_errors'
    # Convert lists to numpy arrays
    return {k: np.array(v) for k, v in data.items()}

def calculate_cohens_d(group1: np.ndarray, group2: np.ndarray) -> float:
    """
    Calculate Cohen's d effect size for two independent groups.
    Formula: (mean1 - mean2) / pooled_std
    """
    mean1, mean2 = np.mean(group1), np.mean(group2)
    n1, n2 = len(group1), len(group2)
    
    var1, var2 = np.var(group1, ddof=1), np.var(group2, ddof=1)
    
    # Pooled standard deviation
    pooled_std = np.sqrt(((n1 - 1) * var1 + (n2 - 1) * var2) / (n1 + n2 - 2))
    
    if pooled_std == 0:
        return 0.0
    
    return (mean1 - mean2) / pooled_std

def calculate_confidence_interval(diff: np.ndarray, confidence: float = 0.95) -> Tuple[float, float]:
    """
    Calculate confidence interval for the mean difference.
    """
    n = len(diff)
    mean_diff = np.mean(diff)
    std_diff = np.std(diff, ddof=1)
    std_err = std_diff / np.sqrt(n)
    
    # T-distribution critical value
    dof = n - 1
    t_crit = stats.t.ppf((1 + confidence) / 2.0, dof)
    
    margin = t_crit * std_err
    return (mean_diff - margin, mean_diff + margin)

def run_paired_ttest(errors_gnn: np.ndarray, errors_rf: np.ndarray) -> Dict[str, Any]:
    """
    Run paired t-test on prediction errors.
    Returns t-statistic, p-value, and mean difference.
    """
    if len(errors_gnn) != len(errors_rf):
        raise ValueError("Error arrays must be of equal length for paired t-test.")
    
    t_stat, p_val = stats.ttest_rel(errors_gnn, errors_rf)
    mean_diff = np.mean(errors_gnn - errors_rf)
    
    return {
        "t_statistic": float(t_stat),
        "p_value": float(p_val),
        "mean_difference": float(mean_diff),
        "n_samples": int(len(errors_gnn))
    }

def update_metrics_file(metrics_path: Path, results: Dict[str, Any]) -> None:
    """
    Update the main metrics.json file with statistical test results.
    """
    if not metrics_path.exists():
        logger.warning(f"Metrics file not found at {metrics_path}. Creating new one.")
        with open(metrics_path, 'w') as f:
            json.dump(results, f, indent=2)
        return

    with open(metrics_path, 'r') as f:
        metrics = json.load(f)
    
    metrics["statistical_test"] = results
    
    with open(metrics_path, 'w') as f:
        json.dump(metrics, f, indent=2)
    
    logger.info(f"Updated metrics file at {metrics_path}")

def main():
    """
    Main entry point for statistical tests.
    Expects data/processed/predictions_errors.json and results/metrics.json
    """
    # Setup logging
    logging.basicConfig(level=logging.INFO)
    
    base_path = Path(__file__).parent.parent.parent
    predictions_file = base_path / "data" / "processed" / "predictions_errors.json"
    metrics_file = base_path / "results" / "metrics.json"
    
    if not predictions_file.exists():
        logger.error(f"Predictions file not found: {predictions_file}")
        logger.error("Run code/analysis/evaluate.py first to generate predictions_errors.json")
        sys.exit(1)

    try:
        # Load errors
        errors = load_predictions(predictions_file)
        
        if 'gnn_errors' not in errors or 'rf_errors' not in errors:
            logger.error("Required error keys 'gnn_errors' and 'rf_errors' not found in predictions file.")
            sys.exit(1)

        gnn_errors = errors['gnn_errors']
        rf_errors = errors['rf_errors']

        logger.info(f"Running paired t-test on {len(gnn_errors)} samples...")

        # 1. Paired T-Test
        ttest_results = run_paired_ttest(gnn_errors, rf_errors)
        logger.info(f"T-Test p-value: {ttest_results['p_value']:.6f}")

        # 2. Cohen's d
        cohen_d = calculate_cohens_d(gnn_errors, rf_errors)
        logger.info(f"Cohen's d: {cohen_d:.4f}")

        # 3. Confidence Interval
        diff = gnn_errors - rf_errors
        ci_low, ci_high = calculate_confidence_interval(diff)
        logger.info(f"95% CI for mean difference: [{ci_low:.4f}, {ci_high:.4f}]")

        # Compile results
        statistical_results = {
            "t_statistic": ttest_results['t_statistic'],
            "p_value": ttest_results['p_value'],
            "mean_difference": ttest_results['mean_difference'],
            "n_samples": ttest_results['n_samples'],
            "cohens_d": cohen_d,
            "confidence_interval_95": {
                "lower": float(ci_low),
                "upper": float(ci_high)
            }
        }

        # Update metrics file
        update_metrics_file(metrics_file, statistical_results)
        
        # Save standalone report
        report_path = base_path / "results" / "statistical_test_results.json"
        with open(report_path, 'w') as f:
            json.dump(statistical_results, f, indent=2)
        
        logger.info(f"Statistical results saved to {report_path}")

    except Exception as e:
        logger.error(f"Error during statistical analysis: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()