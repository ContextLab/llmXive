import os
import sys
import json
import logging
import argparse
from pathlib import Path
from typing import Dict, Any, Optional, Tuple
import numpy as np
from scipy import stats

# Import existing utilities from project
# Note: Assuming load_data_splits and load_predictions are defined as per API surface
# If they are not yet fully implemented in the file, they are assumed to exist in the sibling context
# based on the provided API surface list.
from utils import get_logger, get_device
from models import Molecule, Scaffold

# Configure logging
logger = get_logger(__name__)

def load_data_splits(split_path: str) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Loads train/val/test indices from split_indices.json.
    Returns (train_indices, val_indices, test_indices) as numpy arrays.
    """
    with open(split_path, 'r') as f:
        data = json.load(f)
    return (
        np.array(data.get('train_idx', [])),
        np.array(data.get('val_idx', [])),
        np.array(data.get('test_idx', []))
    )

def load_predictions(predictions_path: str) -> Dict[str, np.ndarray]:
    """
    Loads predictions and true values from a JSON file.
    Expected format: {"test_true": [...], "test_pred": [...]}
    """
    with open(predictions_path, 'r') as f:
        return json.load(f)

def compute_metrics(true_vals: np.ndarray, pred_vals: np.ndarray) -> Dict[str, float]:
    """Computes MAE and R2."""
    mae = np.mean(np.abs(true_vals - pred_vals))
    ss_res = np.sum((true_vals - pred_vals) ** 2)
    ss_tot = np.sum((true_vals - np.mean(true_vals)) ** 2)
    r2 = 1 - (ss_res / ss_tot) if ss_tot != 0 else 0.0
    return {'mae': float(mae), 'r2': float(r2)}

def perform_wilcoxon_test(pred_gnn: np.ndarray, pred_baseline: np.ndarray, true_vals: np.ndarray) -> float:
    """Performs Wilcoxon signed-rank test on absolute errors."""
    err_gnn = np.abs(true_vals - pred_gnn)
    err_baseline = np.abs(true_vals - pred_baseline)
    # Wilcoxon signed-rank test
    stat, p_value = stats.wilcoxon(err_gnn, err_baseline)
    return float(p_value)

def compute_confidence_interval(errors: np.ndarray, confidence: float = 0.95) -> Tuple[float, float]:
    """Computes confidence interval for the mean error."""
    n = len(errors)
    mean_err = np.mean(errors)
    std_err = np.std(errors, ddof=1)
    # t-distribution for small samples, normal for large
    if n > 30:
        z = stats.norm.ppf(0.5 + confidence / 2)
    else:
        z = stats.t.ppf(0.5 + confidence / 2, df=n-1)
    
    margin = z * (std_err / np.sqrt(n))
    return float(mean_err - margin), float(mean_err + margin)

def determine_sc001_status(mae: float, p_value: float) -> str:
    """
    Determines SC-001 status based on Decision Logic:
    If p < 0.05 AND MAE < 30 then "PASS", else "FAIL".
    """
    if p_value < 0.05 and mae < 30.0:
        return "PASS"
    return "FAIL"

def compute_effect_size(true_vals: np.ndarray, pred_vals: np.ndarray) -> float:
    """
    Computes Cohen's d effect size for the prediction errors.
    Effect size = mean(diff) / std(diff)
    where diff = |true - pred_baseline| - |true - pred_gnn| (or similar metric)
    Here we use the standardized mean difference of absolute errors.
    """
    # Assuming we compare GNN errors to Baseline errors if available, 
    # but for single model power analysis, we often look at the error distribution.
    # For this task, we calculate effect size based on the deviation from a hypothetical 
    # "perfect" or baseline threshold if comparing, or simply the standardized error.
    # However, standard power analysis for a mean usually compares to a value.
    # Let's assume we are testing if the MAE is significantly different from 0 or a baseline.
    # A common approach in this context: Effect size of the error reduction.
    # Since we only have one set of errors here for power analysis of the test set size:
    # We will calculate the effect size of the mean error relative to its standard deviation.
    errors = np.abs(true_vals - pred_vals)
    mean_err = np.mean(errors)
    std_err = np.std(errors, ddof=1)
    if std_err == 0:
        return 0.0
    return float(mean_err / std_err)

def classify_effect_size(cohens_d: float) -> str:
    """Classifies effect size: <0.2 small, 0.2-0.5 medium, >0.5 large."""
    if abs(cohens_d) < 0.2:
        return "small"
    elif abs(cohens_d) < 0.5:
        return "medium"
    else:
        return "large"

def compute_power_analysis(n: int, effect_size: float, alpha: float = 0.05) -> Dict[str, Any]:
    """
    Computes statistical power for a one-sample t-test (or similar) given:
    - n: sample size
    - effect_size: Cohen's d
    - alpha: significance level
    
    Returns dict with n, effect_size, power, and power_status.
    """
    # Using scipy.stats for power calculation (approximation for t-test)
    # We assume a two-sided test for mean difference
    try:
        # statsmodels is often better for power, but sticking to scipy/numpy if not available
        # Manual approximation for power of t-test:
        # Power = 1 - beta
        # Non-centrality parameter
        ncp = effect_size * np.sqrt(n)
        
        # Critical t-value
        df = n - 1
        t_crit = stats.t.ppf(1 - alpha/2, df)
        
        # Power calculation (approximation using normal distribution for large n, or t-distribution)
        # P(T > t_crit | H1) + P(T < -t_crit | H1)
        # Using survival function of non-central t is complex in pure scipy without statsmodels
        # We will use a standard approximation:
        # Power ≈ Φ( |ncp| - t_crit ) + Φ( -|ncp| - t_crit )
        # This is an approximation. For strict compliance, we might need statsmodels.
        # However, let's use a robust approximation or fallback if statsmodels is missing.
        
        # Using statsmodels if available, else approximation
        try:
            from statsmodels.stats.power import TTestPower
            analysis = TTestPower()
            power = analysis.power(effect_size=effect_size, nobs=n, alpha=alpha, alternative='two-sided')
        except ImportError:
            # Fallback approximation
            # Power is probability that we reject null given effect exists
            # Z = (ncp - t_crit)
            power = stats.norm.cdf(abs(ncp) - t_crit) + stats.norm.cdf(-abs(ncp) - t_crit)
            power = max(0.0, min(1.0, power)) # Clamp

        power_status = "PASS" if power >= 0.8 else "FAIL"
        
        return {
            "n": n,
            "effect_size": float(effect_size),
            "power": float(power),
            "power_status": power_status
        }
    except Exception as e:
        logger.error(f"Error computing power analysis: {e}")
        return {
            "n": n,
            "effect_size": float(effect_size),
            "power": 0.0,
            "power_status": "FAIL"
        }

def enforce_test_size_constraint(n: int, min_n: int = 50) -> None:
    """
    Enforces the constraint that test set size n >= 50.
    Raises ValueError if constraint is violated.
    """
    if n < min_n:
        raise ValueError(f"Test set size (n={n}) is less than minimum required ({min_n}). "
                         f"Power analysis cannot be performed reliably. Halting execution.")

def save_power_analysis(results: Dict[str, Any], output_path: str) -> None:
    """Saves power analysis results to a JSON file."""
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'w') as f:
        json.dump(results, f, indent=2)
    logger.info(f"Power analysis results saved to {output_path}")

def main():
    """
    Main entry point for T018: Power Analysis Logic.
    1. Loads test set predictions (or data) to determine n.
    2. Enforces n >= 50.
    3. Computes effect size.
    4. Computes power.
    5. Saves results to data/processed/power_analysis.json.
    """
    parser = argparse.ArgumentParser(description="Power Analysis for Molecular Excitation Model")
    parser.add_argument("--predictions", type=str, default="data/processed/test_predictions.json",
                        help="Path to test predictions JSON")
    parser.add_argument("--splits", type=str, default="data/processed/split_indices.json",
                        help="Path to split indices JSON")
    parser.add_argument("--output", type=str, default="data/processed/power_analysis.json",
                        help="Output path for power analysis JSON")
    args = parser.parse_args()

    # 1. Load data to get n
    # We need the test set size. If we have predictions, we can just count them.
    # If we only have splits, we count the test indices.
    try:
        if os.path.exists(args.predictions):
            preds = load_predictions(args.predictions)
            n = len(preds.get('test_true', []))
            logger.info(f"Loaded {n} test samples from predictions file.")
        elif os.path.exists(args.splits):
            _, _, test_indices = load_data_splits(args.splits)
            n = len(test_indices)
            logger.info(f"Loaded {n} test samples from split indices.")
        else:
            raise FileNotFoundError("Neither predictions file nor split indices file found.")
    except Exception as e:
        logger.error(f"Failed to load data for power analysis: {e}")
        sys.exit(1)

    # 2. Enforce constraint n >= 50
    try:
        enforce_test_size_constraint(n)
        logger.info(f"Test set size (n={n}) meets minimum requirement (>= 50).")
    except ValueError as e:
        logger.error(str(e))
        # Write failure status to output file before exiting
        failure_result = {
            "n": n,
            "effect_size": 0.0,
            "power": 0.0,
            "power_status": "FAIL",
            "error": str(e)
        }
        save_power_analysis(failure_result, args.output)
        sys.exit(1)

    # 3. Compute Effect Size
    # We need true and predicted values to compute effect size of errors.
    # If predictions file exists, use it.
    if os.path.exists(args.predictions):
        preds = load_predictions(args.predictions)
        true_vals = np.array(preds['test_true'])
        pred_vals = np.array(preds['test_pred'])
        effect_size = compute_effect_size(true_vals, pred_vals)
        logger.info(f"Computed effect size: {effect_size:.4f}")
    else:
        # If we only have indices, we cannot compute effect size without loading the full dataset again.
        # For this task, we assume predictions exist if we passed the n check, 
        # or we fallback to a placeholder effect size if the task strictly requires only n check.
        # However, the task asks for "effect size" in the output.
        # We will raise an error if we can't compute it, as fake data is forbidden.
        logger.error("Cannot compute effect size without true and predicted values.")
        # Fallback to a standard placeholder if we must, but better to fail loud.
        # Let's assume the pipeline produces predictions before this step.
        sys.exit(1)

    # 4. Compute Power
    power_results = compute_power_analysis(n, effect_size)
    logger.info(f"Power analysis: n={n}, effect_size={power_results['effect_size']:.4f}, "
                f"power={power_results['power']:.4f}, status={power_results['power_status']}")

    # 5. Save Results
    save_power_analysis(power_results, args.output)
    logger.info("Power analysis completed successfully.")

if __name__ == "__main__":
    main()