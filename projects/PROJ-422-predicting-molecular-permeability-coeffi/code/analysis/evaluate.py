import logging
import json
from typing import List, Tuple, Optional, Dict, Any
from pathlib import Path
import numpy as np
import pandas as pd
from scipy import stats

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def calculate_metrics(y_true: np.ndarray, y_pred: np.ndarray) -> Dict[str, float]:
    """
    Calculate RMSE, MAE, and R² for regression predictions.
    
    Args:
        y_true: Array of true values.
        y_pred: Array of predicted values.
        
    Returns:
        Dictionary containing RMSE, MAE, and R².
    """
    if len(y_true) != len(y_pred):
        raise ValueError("y_true and y_pred must have the same length")
    
    residuals = y_true - y_pred
    
    rmse = np.sqrt(np.mean(residuals ** 2))
    mae = np.mean(np.abs(residuals))
    
    ss_res = np.sum(residuals ** 2)
    ss_tot = np.sum((y_true - np.mean(y_true)) ** 2)
    
    if ss_tot == 0:
        r2 = 0.0
    else:
        r2 = 1 - (ss_res / ss_tot)
        
    return {
        "rmse": float(rmse),
        "mae": float(mae),
        "r2": float(r2)
    }

def paired_ttest(errors_a: np.ndarray, errors_b: np.ndarray) -> Dict[str, float]:
    """
    Perform a paired t-test on two sets of prediction errors.
    Calculates p-value, t-statistic, Cohen's d, and 95% Confidence Interval.
    
    Args:
        errors_a: Array of errors for model A (e.g., GNN).
        errors_b: Array of errors for model B (e.g., RF).
        
    Returns:
        Dictionary containing t-statistic, p-value, Cohen's d, and CI.
    """
    if len(errors_a) != len(errors_b):
        raise ValueError("Error arrays must have the same length for paired test")
    if len(errors_a) < 2:
        raise ValueError("Need at least 2 samples for paired t-test")
    
    # Differences
    diff = errors_a - errors_b
    n = len(diff)
    mean_diff = np.mean(diff)
    std_diff = np.std(diff, ddof=1)
    
    # T-test
    t_stat, p_val = stats.ttest_rel(errors_a, errors_b)
    
    # Cohen's d (effect size)
    # d = mean_diff / std_diff
    if std_diff == 0:
        cohen_d = 0.0
    else:
        cohen_d = mean_diff / std_diff
        
    # 95% Confidence Interval for the mean difference
    # CI = mean_diff ± t_crit * (std_diff / sqrt(n))
    alpha = 0.05
    t_crit = stats.t.ppf(1 - alpha/2, df=n-1)
    margin_error = t_crit * (std_diff / np.sqrt(n))
    ci_lower = mean_diff - margin_error
    ci_upper = mean_diff + margin_error
    
    return {
        "t_statistic": float(t_stat),
        "p_value": float(p_val),
        "cohen_d": float(cohen_d),
        "ci_95_lower": float(ci_lower),
        "ci_95_upper": float(ci_upper),
        "n_samples": n
    }

def post_hoc_power_analysis(effect_size: float, n_samples: int, alpha: float = 0.05, two_tailed: bool = True) -> Dict[str, float]:
    """
    Calculate post-hoc statistical power based on observed effect size and sample size.
    Uses the t-test power calculation logic.
    
    Args:
        effect_size: Cohen's d observed.
        n_samples: Number of paired samples.
        alpha: Significance level (default 0.05).
        two_tailed: Whether the test is two-tailed.
        
    Returns:
        Dictionary containing the calculated power.
    """
    if n_samples < 2:
        raise ValueError("Sample size must be at least 2 for power analysis")
    
    # Calculate non-centrality parameter (delta)
    # For paired t-test, delta = d * sqrt(n)
    delta = effect_size * np.sqrt(n_samples)
    
    # Degrees of freedom
    df = n_samples - 1
    
    # Critical t-value
    if two_tailed:
        t_crit = stats.t.ppf(1 - alpha/2, df)
    else:
        t_crit = stats.t.ppf(1 - alpha, df)
    
    # Calculate power: Probability that a non-central t variable exceeds the critical value
    # Using survival function (1 - CDF) for the upper tail
    # For two-tailed, we sum probabilities of both tails, but usually power is dominated by one direction
    # For simplicity and standard reporting, we use the non-central t CDF logic:
    # Power = P(T > t_crit | non-centrality=delta) + P(T < -t_crit | non-centrality=delta)
    
    # Since scipy.stats.nct.cdf is available:
    # Power = 1 - CDF(t_crit) + CDF(-t_crit)
    # Note: nct.cdf(x, df, nc)
    
    power_upper = 1 - stats.nct.cdf(t_crit, df, delta)
    power_lower = stats.nct.cdf(-t_crit, df, delta)
    
    total_power = power_upper + power_lower
    
    # Ensure power is within [0, 1]
    total_power = max(0.0, min(1.0, total_power))
    
    return {
        "power": float(total_power),
        "alpha": float(alpha),
        "n_samples": n_samples,
        "effect_size": float(effect_size),
        "df": df
    }

def evaluate_models(
    metrics_path: Path,
    gnn_errors: np.ndarray,
    rf_errors: np.ndarray,
    model_names: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Evaluate models, perform paired t-test, and calculate post-hoc power.
    Saves results to metrics_path.
    
    Args:
        metrics_path: Path to save the results JSON.
        gnn_errors: Array of errors for GNN model.
        rf_errors: Array of errors for Random Forest model.
        model_names: Optional list of model names for logging.
        
    Returns:
        Dictionary containing all evaluation metrics and statistical tests.
    """
    if model_names is None:
        model_names = ["GNN", "Random Forest"]
    
    logger.info(f"Evaluating models: {model_names[0]} vs {model_names[1]}")
    
    # 1. Basic Metrics (assuming we have predictions or just work with errors directly if provided)
    # If only errors are provided, we can't calculate RMSE/MAE/R2 from scratch without true labels,
    # but the task implies we have the errors (residuals). 
    # However, the signature of calculate_metrics expects y_true and y_pred.
    # To be robust, if only errors are passed, we calculate stats on the errors directly.
    # But the prompt implies we have the full context. Let's assume we calculate metrics 
    # from the errors if true/pred not available, or re-calculate if true/pred were available.
    # Since the input here is specifically errors, we will report stats on the error distribution.
    
    # For the sake of the task, let's assume we might need to re-calculate if we had y_true/y_pred.
    # But here we are given errors. Let's calculate the mean error and std of errors as a proxy for bias/variance
    # or simply rely on the t-test results which are the core of this task.
    # Actually, T024 already calculated RMSE/MAE/R2. T026 is specifically about Power Analysis.
    # We will load the existing metrics if they exist, or just compute the statistical test here.
    # The function signature suggests we are running the analysis now.
    
    # Perform Paired T-Test
    t_test_results = paired_ttest(gnn_errors, rf_errors)
    logger.info(f"T-Test P-value: {t_test_results['p_value']:.6f}")
    logger.info(f"Cohen's d: {t_test_results['cohen_d']:.4f}")
    
    # Perform Post-Hoc Power Analysis
    power_results = post_hoc_power_analysis(
        effect_size=t_test_results['cohen_d'],
        n_samples=t_test_results['n_samples']
    )
    logger.info(f"Post-hoc Power: {power_results['power']:.4f}")
    
    results = {
        "comparison": {
            "model_a": model_names[0],
            "model_b": model_names[1]
        },
        "paired_ttest": t_test_results,
        "post_hoc_power_analysis": power_results,
        "interpretation": {
            "significant": t_test_results['p_value'] < 0.05,
            "effect_size_category": "negligible" if abs(t_test_results['cohen_d']) < 0.2 else 
                                    "small" if abs(t_test_results['cohen_d']) < 0.5 else 
                                    "medium" if abs(t_test_results['cohen_d']) < 0.8 else "large",
            "power_adequate": power_results['power'] >= 0.80
        }
    }
    
    # Ensure directory exists
    metrics_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Save to JSON
    with open(metrics_path, 'w') as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"Results saved to {metrics_path}")
    return results

def main():
    """
    Main entry point for evaluation and power analysis.
    Expects data to be available or passed via arguments.
    For this task, we assume the errors are loaded from the processed test set
    or generated by the training pipeline.
    """
    logger.info("Starting Evaluation and Power Analysis (T026)")
    
    # Paths
    base_path = Path(__file__).parent.parent.parent
    metrics_path = base_path / "results" / "metrics.json"
    
    # Load test data to get errors
    # Assuming the pipeline produces data/processed/test.csv with columns:
    # 'y_true', 'y_pred_gnn', 'y_pred_rf'
    # If not, we might need to load from model outputs.
    # Let's try to load from a standard location or raise error if missing.
    
    test_data_path = base_path / "data" / "processed" / "test.csv"
    
    if not test_data_path.exists():
        logger.error(f"Test data not found at {test_data_path}. Cannot perform evaluation.")
        logger.error("Ensure T024 (evaluate_models) and T022 (train) have run and produced test.csv with predictions.")
        # In a real scenario, we might exit here.
        # For this script, we will raise an error.
        raise FileNotFoundError(f"Required test data file not found: {test_data_path}")
    
    try:
        df = pd.read_csv(test_data_path)
        required_cols = ['y_true', 'y_pred_gnn', 'y_pred_rf']
        missing_cols = [c for c in required_cols if c not in df.columns]
        if missing_cols:
            raise ValueError(f"Missing required columns in test data: {missing_cols}")
        
        y_true = df['y_true'].values
        y_pred_gnn = df['y_pred_gnn'].values
        y_pred_rf = df['y_pred_rf'].values
        
        # Calculate errors
        errors_gnn = y_true - y_pred_gnn
        errors_rf = y_true - y_pred_rf
        
        # Run full evaluation including power analysis
        results = evaluate_models(
            metrics_path=metrics_path,
            gnn_errors=errors_gnn,
            rf_errors=errors_rf,
            model_names=["GNN", "Random Forest"]
        )
        
        print(json.dumps(results, indent=2))
        
    except Exception as e:
        logger.error(f"Evaluation failed: {e}")
        raise

if __name__ == "__main__":
    main()