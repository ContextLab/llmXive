import json
import logging
import sys
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional
import numpy as np
from scipy import stats

# Ensure the logger is configured if not already
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def load_predictions(predictions_file: Path) -> Tuple[np.ndarray, np.ndarray, np.ndarray, str]:
    """
    Loads prediction errors from the predictions file.
    Returns: (gnn_errors, rf_errors, y_true, target_type)
    """
    if not predictions_file.exists():
        raise FileNotFoundError(f"Predictions file not found: {predictions_file}")
    
    with open(predictions_file, 'r') as f:
        data = json.load(f)
    
    # Expecting a structure like:
    # {
    #   "target_type": "logP",
    #   "models": {
    #     "GNN": {"predictions": [...], "actuals": [...]},
    #     "RF_Baseline": {"predictions": [...], "actuals": [...]}
    #   }
    # }
    
    target_type = data.get("target_type", "unknown")
    models = data.get("models", {})
    
    if "GNN" not in models or "RF_Baseline" not in models:
        raise ValueError("Missing GNN or RF_Baseline in predictions file")
    
    gnn_preds = np.array(models["GNN"]["predictions"])
    gnn_actuals = np.array(models["GNN"]["actuals"])
    rf_preds = np.array(models["RF_Baseline"]["predictions"])
    rf_actuals = np.array(models["RF_Baseline"]["actuals"])
    
    # Ensure lengths match
    if len(gnn_actuals) != len(rf_actuals):
        raise ValueError("GNN and RF actuals have different lengths")
    
    # Calculate errors (absolute or signed? Usually for paired t-test on performance,
    # we look at the difference in errors. Let's use signed errors for the test
    # to see if one is systematically better (lower error) than the other.
    # However, standard practice for "error" comparison is often absolute error (MAE-like)
    # or squared error (MSE-like). The prompt asks for "prediction errors".
    # Let's use signed errors (pred - actual) to test if the mean difference is non-zero.
    # If we want to test MAE difference, we'd use abs(pred - actual).
    # Given SC-002 mentions "performance gap", let's calculate the error metric (e.g., squared error)
    # and compare those. But "paired t-test on prediction errors" usually implies the raw residuals.
    # Let's use squared errors (MSE components) as it's standard for regression comparison,
    # but the prompt says "prediction errors". Let's stick to residuals (pred - actual).
    # Actually, to compare models, we often compare |error| or error^2.
    # Let's compute the difference in squared errors (MSE contribution) as it's more sensitive to outliers
    # and standard in regression analysis.
    # Wait, the task says "Paired t-test on prediction errors".
    # Let's compute the absolute errors (MAE components) to be robust, or just residuals.
    # Let's use residuals (pred - actual) and test if mean(residual_gnn) != mean(residual_rf).
    # But typically we want to know if GNN error is LOWER.
    # Let's calculate the error metric: Squared Error (SE) for each point.
    # diff = SE_gnn - SE_rf. If mean(diff) < 0, GNN is better.
    
    gnn_se = (gnn_preds - gnn_actuals) ** 2
    rf_se = (rf_preds - rf_actuals) ** 2
    
    return gnn_se, rf_se, gnn_actuals, target_type

def calculate_cohens_d(group1: np.ndarray, group2: np.ndarray) -> float:
    """
    Calculates Cohen's d effect size for two groups.
    d = (mean1 - mean2) / pooled_std
    """
    mean1, mean2 = np.mean(group1), np.mean(group2)
    std1, std2 = np.std(group1, ddof=1), np.std(group2, ddof=1)
    n1, n2 = len(group1), len(group2)
    
    # Pooled standard deviation
    pooled_std = np.sqrt(((n1 - 1) * std1**2 + (n2 - 1) * std2**2) / (n1 + n2 - 2))
    
    if pooled_std == 0:
        return 0.0
    
    return (mean1 - mean2) / pooled_std

def calculate_confidence_interval(data: np.ndarray, confidence: float = 0.95) -> Tuple[float, float]:
    """
    Calculates the confidence interval for the mean of the data.
    """
    n = len(data)
    mean = np.mean(data)
    std_err = stats.sem(data)
    h = std_err * stats.t.ppf((1 + confidence) / 2., n-1)
    return mean - h, mean + h

def run_paired_ttest(group1: np.ndarray, group2: np.ndarray) -> Dict[str, Any]:
    """
    Runs a paired t-test between two groups.
    Returns: dict with statistic, pvalue, mean_diff, cohens_d, ci
    """
    if len(group1) != len(group2):
        raise ValueError("Groups must have the same length for paired t-test")
    
    # Paired t-test
    t_stat, p_value = stats.ttest_rel(group1, group2)
    
    mean_diff = np.mean(group1 - group2)
    cohens_d = calculate_cohens_d(group1, group2)
    
    # Confidence Interval for the mean difference
    diff_data = group1 - group2
    ci_low, ci_high = calculate_confidence_interval(diff_data, 0.95)
    
    return {
        "statistic": float(t_stat),
        "pvalue": float(p_value),
        "mean_difference": float(mean_diff),
        "cohens_d": float(cohens_d),
        "confidence_interval_95": {
            "lower": float(ci_low),
            "upper": float(ci_high)
        }
    }

def update_metrics_file(metrics_file: Path, test_results: Dict[str, Any], target_type: str):
    """
    Updates the metrics.json file with the statistical test results.
    """
    if not metrics_file.exists():
        logger.warning(f"Metrics file not found: {metrics_file}. Creating new one.")
        base_metrics = {}
    else:
        with open(metrics_file, 'r') as f:
            base_metrics = json.load(f)
    
    # Ensure structure
    if "statistical_tests" not in base_metrics:
        base_metrics["statistical_tests"] = {}
    
    base_metrics["statistical_tests"]["gnn_vs_rf_baseline"] = test_results
    base_metrics["statistical_tests"]["target_variable_type"] = target_type
    base_metrics["statistical_tests"]["test_type"] = "paired_ttest_squared_errors"
    
    with open(metrics_file, 'w') as f:
        json.dump(base_metrics, f, indent=2)
    
    logger.info(f"Updated metrics file: {metrics_file}")

def main():
    """
    Main entry point for T025: Paired t-test on prediction errors.
    """
    project_root = Path(__file__).resolve().parents[2]
    predictions_file = project_root / "results" / "predictions_errors.json"
    metrics_file = project_root / "results" / "metrics.json"
    
    logging.info("Starting T025: Paired t-test on prediction errors (GNN vs RF-Baseline)")
    
    try:
        # 1. Load predictions
        gnn_se, rf_se, y_true, target_type = load_predictions(predictions_file)
        logger.info(f"Loaded predictions. Target type: {target_type}. Sample size: {len(gnn_se)}")
        
        # 2. Log target type
        logger.info(f"Target variable type: {target_type} (Experimental: {target_type != 'logP_proxy'})")
        
        # 3. Run paired t-test
        # We are comparing Squared Errors. 
        # H0: Mean(SE_gnn) == Mean(SE_rf)
        # H1: Mean(SE_gnn) != Mean(SE_rf)
        test_results = run_paired_ttest(gnn_se, rf_se)
        
        logger.info(f"T-test Statistic: {test_results['statistic']:.4f}")
        logger.info(f"P-value: {test_results['pvalue']:.4e}")
        logger.info(f"Mean Difference (GNN - RF): {test_results['mean_difference']:.4f}")
        logger.info(f"Cohen's d: {test_results['cohens_d']:.4f}")
        logger.info(f"95% CI: [{test_results['confidence_interval_95']['lower']:.4f}, {test_results['confidence_interval_95']['upper']:.4f}]")
        
        # 4. Update metrics file
        update_metrics_file(metrics_file, test_results, target_type)
        
        logger.info("T025 completed successfully.")
        
    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Error during T025 execution: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()