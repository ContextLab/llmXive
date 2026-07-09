"""
Statistical significance testing for RF vs GNN models on ESOL dataset.
Performs paired t-test on absolute errors and calculates post-hoc power.
"""
import os
import sys
import json
import logging
import argparse
from pathlib import Path
from typing import Dict, Tuple, Optional

import numpy as np
from scipy import stats
from statsmodels.stats.power import TTestPower

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_predictions(file_path: str) -> Dict[str, np.ndarray]:
    """
    Load predictions from a JSON file.
    Expected format: {"y_true": [...], "y_pred": [...]}
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Predictions file not found: {file_path}")
    
    with open(file_path, 'r') as f:
        data = json.load(f)
    
    y_true = np.array(data['y_true'])
    y_pred = np.array(data['y_pred'])
    
    if len(y_true) != len(y_pred):
        raise ValueError(f"Mismatch in lengths: y_true ({len(y_true)}) vs y_pred ({len(y_pred)})")
    
    return y_true, y_pred

def calculate_absolute_errors(y_true: np.ndarray, y_pred: np.ndarray) -> np.ndarray:
    """Calculate absolute errors for paired comparison."""
    return np.abs(y_true - y_pred)

def perform_paired_ttest(errors_rf: np.ndarray, errors_gnn: np.ndarray) -> Tuple[float, float]:
    """
    Perform paired t-test on absolute errors.
    Returns (t_statistic, p_value).
    """
    if len(errors_rf) != len(errors_gnn):
        raise ValueError("Error arrays must be of equal length for paired t-test")
    
    t_stat, p_val = stats.ttest_rel(errors_rf, errors_gnn)
    return t_stat, p_val

def calculate_post_hoc_power(t_stat: float, n_samples: int, alpha: float = 0.05) -> float:
    """
    Calculate post-hoc power for the paired t-test.
    Uses effect size derived from t-statistic.
    """
    # Calculate effect size (Cohen's d for paired samples)
    # d = t / sqrt(n)
    effect_size = t_stat / np.sqrt(n_samples)
    
    # Use statsmodels for power analysis
    power_analysis = TTestPower()
    power = power_analysis.solve_power(
        effect_size=abs(effect_size),
        nobs1=n_samples,
        alpha=alpha,
        power=None,
        ratio=1.0,
        alternative='two-sided'
    )
    
    return power

def run_statistical_analysis(
    rf_predictions_path: str,
    gnn_predictions_path: str,
    output_path: str,
    alpha: float = 0.05
) -> Dict:
    """
    Run full statistical analysis: paired t-test and power calculation.
    """
    logger.info(f"Loading RF predictions from: {rf_predictions_path}")
    y_true_rf, y_pred_rf = load_predictions(rf_predictions_path)
    
    logger.info(f"Loading GNN predictions from: {gnn_predictions_path}")
    y_true_gnn, y_pred_gnn = load_predictions(gnn_predictions_path)
    
    # Verify same ground truth (should be identical for same test set)
    if not np.allclose(y_true_rf, y_true_gnn):
        logger.warning("Ground truth arrays differ slightly, proceeding with paired comparison")
    
    # Calculate absolute errors
    abs_errors_rf = calculate_absolute_errors(y_true_rf, y_pred_rf)
    abs_errors_gnn = calculate_absolute_errors(y_true_gnn, y_pred_gnn)
    
    # Perform paired t-test
    t_stat, p_value = perform_paired_ttest(abs_errors_rf, abs_errors_gnn)
    
    # Calculate post-hoc power
    n_samples = len(abs_errors_rf)
    power = calculate_post_hoc_power(t_stat, n_samples, alpha)
    
    # Determine significance
    is_significant = p_value < alpha
    better_model = "GNN" if t_stat > 0 else "RF" if t_stat < 0 else "Equal"
    
    # Compile results
    results = {
        "n_samples": int(n_samples),
        "alpha": alpha,
        "t_statistic": float(t_stat),
        "p_value": float(p_value),
        "is_significant": bool(is_significant),
        "post_hoc_power": float(power),
        "better_model": better_model,
        "mean_abs_error_rf": float(np.mean(abs_errors_rf)),
        "mean_abs_error_gnn": float(np.mean(abs_errors_gnn)),
        "std_abs_error_rf": float(np.std(abs_errors_rf)),
        "std_abs_error_gnn": float(np.std(abs_errors_gnn)),
        "mean_error_diff": float(np.mean(abs_errors_rf - abs_errors_gnn)),
        "std_error_diff": float(np.std(abs_errors_rf - abs_errors_gnn))
    }
    
    # Save results
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"Statistical analysis results saved to: {output_path}")
    logger.info(f"t-statistic: {t_stat:.4f}, p-value: {p_value:.4f}")
    logger.info(f"Significant at alpha={alpha}: {is_significant}")
    logger.info(f"Post-hoc power: {power:.4f}")
    logger.info(f"Better model: {better_model}")
    
    return results

def main():
    parser = argparse.ArgumentParser(description="Statistical significance test for RF vs GNN")
    parser.add_argument(
        "--rf-predictions",
        type=str,
        default="results/baseline_predictions.json",
        help="Path to RF predictions JSON file"
    )
    parser.add_argument(
        "--gnn-predictions",
        type=str,
        default="results/gnn_predictions.json",
        help="Path to GNN predictions JSON file"
    )
    parser.add_argument(
        "--output",
        type=str,
        default="results/statistical_test_results.json",
        help="Path to save statistical test results"
    )
    parser.add_argument(
        "--alpha",
        type=float,
        default=0.05,
        help="Significance level for the test"
    )
    
    args = parser.parse_args()
    
    try:
        results = run_statistical_analysis(
            rf_predictions_path=args.rf_predictions,
            gnn_predictions_path=args.gnn_predictions,
            output_path=args.output,
            alpha=args.alpha
        )
        logger.info("Statistical test completed successfully")
        return 0
    except Exception as e:
        logger.error(f"Statistical test failed: {str(e)}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
