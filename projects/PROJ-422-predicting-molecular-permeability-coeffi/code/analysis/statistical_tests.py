import json
import logging
import sys
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional
import numpy as np
from scipy import stats

from utils.logging import log_result_artifact

logger = logging.getLogger(__name__)

def load_predictions(predictions_file: Path) -> Tuple[np.ndarray, np.ndarray, np.ndarray, int]:
    """
    Load prediction errors from the predictions file.
    Returns: (errors_gnn, errors_rf_baseline, errors_rf_ablation, n_samples)
    """
    logger.info(f"Loading predictions from {predictions_file}")
    
    if not predictions_file.exists():
        raise FileNotFoundError(f"Predictions file not found: {predictions_file}")
    
    with open(predictions_file, 'r') as f:
        data = json.load(f)
    
    # Extract errors for GNN and RF-Baseline
    # The file structure is expected to have 'errors' keys for each model
    errors_gnn = np.array(data.get('errors', {}).get('gnn', []))
    errors_rf_baseline = np.array(data.get('errors', {}).get('rf_baseline', []))
    
    if len(errors_gnn) == 0 or len(errors_rf_baseline) == 0:
        raise ValueError("Prediction errors are empty in the loaded file.")
    
    if len(errors_gnn) != len(errors_rf_baseline):
        raise ValueError("GNN and RF-Baseline error arrays have different lengths.")
    
    n_samples = len(errors_gnn)
    logger.info(f"Loaded {n_samples} prediction errors for paired t-test")
    
    return errors_gnn, errors_rf_baseline, None, n_samples

def calculate_cohens_d(group1: np.ndarray, group2: np.ndarray) -> float:
    """
    Calculate Cohen's d (effect size) for the difference between two groups.
    Uses the pooled standard deviation.
    """
    n1, n2 = len(group1), len(group2)
    mean1, mean2 = np.mean(group1), np.mean(group2)
    std1, std2 = np.std(group1, ddof=1), np.std(group2, ddof=1)
    
    # Pooled standard deviation
    pooled_std = np.sqrt(((n1 - 1) * std1**2 + (n2 - 1) * std2**2) / (n1 + n2 - 2))
    
    if pooled_std == 0:
        logger.warning("Pooled standard deviation is zero. Cohen's d cannot be calculated.")
        return 0.0
    
    cohens_d = (mean1 - mean2) / pooled_std
    return float(cohens_d)

def calculate_confidence_interval(diff_mean: float, diff_std: float, n: int, confidence: float = 0.95) -> Tuple[float, float]:
    """
    Calculate the confidence interval for the mean difference.
    """
    if n <= 1:
        logger.warning("Sample size is too small for CI calculation.")
        return (float('-inf'), float('inf'))
    
    # Standard error of the mean difference
    se = diff_std / np.sqrt(n)
    
    # T-critical value
    dof = n - 1
    t_crit = stats.t.ppf((1 + confidence) / 2.0, dof)
    
    ci_lower = diff_mean - t_crit * se
    ci_upper = diff_mean + t_crit * se
    
    return float(ci_lower), float(ci_upper)

def run_paired_ttest(errors_a: np.ndarray, errors_b: np.ndarray) -> Dict[str, Any]:
    """
    Perform a paired t-test between two sets of errors.
    Returns a dictionary with t-statistic, p-value, mean difference, and std difference.
    """
    if len(errors_a) != len(errors_b):
        raise ValueError("Input arrays must have the same length for paired t-test.")
    
    # Calculate the differences
    differences = errors_a - errors_b
    mean_diff = np.mean(differences)
    std_diff = np.std(differences, ddof=1)
    n = len(differences)
    
    # Perform paired t-test
    t_stat, p_value = stats.ttest_rel(errors_a, errors_b)
    
    result = {
        "t_statistic": float(t_stat),
        "p_value": float(p_value),
        "mean_difference": float(mean_diff),
        "std_difference": float(std_diff),
        "n_samples": int(n),
        "degrees_of_freedom": int(n - 1)
    }
    
    return result

def update_metrics_file(metrics_file: Path, ttest_results: Dict[str, Any], cohens_d: float, ci: Tuple[float, float], target_type: str) -> None:
    """
    Update the metrics.json file with statistical test results.
    """
    logger.info(f"Updating metrics file at {metrics_file} with statistical results")
    
    if not metrics_file.exists():
        # If metrics file doesn't exist, create a new one with the results
        new_metrics = {
            "statistical_tests": {
                "paired_ttest_gnn_vs_rf_baseline": ttest_results,
                "cohens_d": cohens_d,
                "confidence_interval_95": {
                    "lower": ci[0],
                    "upper": ci[1]
                },
                "target_variable_type": target_type
            }
        }
    else:
        # Load existing metrics and update
        with open(metrics_file, 'r') as f:
            metrics = json.load(f)
        
        if "statistical_tests" not in metrics:
            metrics["statistical_tests"] = {}
        
        metrics["statistical_tests"]["paired_ttest_gnn_vs_rf_baseline"] = ttest_results
        metrics["statistical_tests"]["cohens_d"] = cohens_d
        metrics["statistical_tests"]["confidence_interval_95"] = {
            "lower": ci[0],
            "upper": ci[1]
        }
        metrics["statistical_tests"]["target_variable_type"] = target_type
    
    # Save updated metrics
    with open(metrics_file, 'w') as f:
        json.dump(metrics, f, indent=2)
    
    logger.info("Metrics file updated successfully")

def main():
    """
    Main entry point for running the statistical tests.
    """
    # Define paths
    base_path = Path(__file__).resolve().parent.parent.parent
    predictions_file = base_path / "results" / "predictions_errors.json"
    metrics_file = base_path / "results" / "metrics.json"
    
    # Load target type from metrics if available, otherwise default to unknown
    target_type = "unknown"
    if metrics_file.exists():
        try:
            with open(metrics_file, 'r') as f:
                metrics_data = json.load(f)
                target_type = metrics_data.get("target_variable_type", "unknown")
        except Exception as e:
            logger.warning(f"Could not read target type from metrics: {e}")
    
    try:
        # Load predictions
        errors_gnn, errors_rf_baseline, _, n_samples = load_predictions(predictions_file)
        
        # Run paired t-test
        logger.info("Running paired t-test between GNN and RF-Baseline errors")
        ttest_results = run_paired_ttest(errors_gnn, errors_rf_baseline)
        
        # Calculate Cohen's d
        logger.info("Calculating Cohen's d (effect size)")
        cohens_d = calculate_cohens_d(errors_gnn, errors_rf_baseline)
        
        # Calculate Confidence Interval
        logger.info("Calculating 95% Confidence Interval")
        diff = errors_gnn - errors_rf_baseline
        ci = calculate_confidence_interval(np.mean(diff), np.std(diff, ddof=1), n_samples)
        
        # Update metrics file
        update_metrics_file(metrics_file, ttest_results, cohens_d, ci, target_type)
        
        # Log results
        logger.info(f"T-test Results: t={ttest_results['t_statistic']:.4f}, p={ttest_results['p_value']:.4f}")
        logger.info(f"Cohen's d: {cohens_d:.4f}")
        logger.info(f"95% CI: [{ci[0]:.4f}, {ci[1]:.4f}]")
        
        # Log artifact
        log_result_artifact(
            artifact_type="statistical_test",
            artifact_name="paired_ttest_gnn_vs_rf",
            data={
                "t_statistic": ttest_results["t_statistic"],
                "p_value": ttest_results["p_value"],
                "cohens_d": cohens_d,
                "ci_lower": ci[0],
                "ci_upper": ci[1]
            }
        )
        
        print("Statistical tests completed successfully.")
        
    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        sys.exit(1)
    except ValueError as e:
        logger.error(f"Value error: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
