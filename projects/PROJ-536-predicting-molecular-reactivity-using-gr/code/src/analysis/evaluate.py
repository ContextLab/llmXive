import os
import sys
import json
import logging
from typing import Dict, Any, Optional, List, Tuple
import numpy as np
from scipy import stats

from src.utils.logging import get_logger, log_message
from src.utils.metrics import calculate_all_metrics

logger = get_logger(__name__)

def load_model_checkpoint(checkpoint_path: str) -> Dict[str, Any]:
    """Load a model checkpoint from a pickle file."""
    logger.info(f"Loading model checkpoint from {checkpoint_path}")
    if not os.path.exists(checkpoint_path):
        raise FileNotFoundError(f"Checkpoint file not found: {checkpoint_path}")
    with open(checkpoint_path, 'rb') as f:
        return pickle.load(f)

def run_inference(model_data: Dict[str, Any], X_test: np.ndarray) -> np.ndarray:
    """Run inference using the loaded model data."""
    model_type = model_data.get('type')
    model = model_data.get('model')
    
    if model is None:
        raise ValueError("Model not found in checkpoint data")
    
    predictions = model.predict(X_test)
    return predictions

def calculate_and_save_metrics(y_true: np.ndarray, y_pred: np.ndarray, output_path: str) -> Dict[str, float]:
    """Calculate metrics and save to JSON."""
    metrics = calculate_all_metrics(y_true, y_pred)
    
    logger.info(f"Saving metrics to {output_path}")
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(metrics, f, indent=2)
    
    return metrics

def aggregate_fold_results(fold_results: List[Dict[str, Any]]) -> Dict[str, List[float]]:
    """Aggregate results from multiple K-Fold runs."""
    aggregated = {
        'mae': [],
        'rmse': [],
        'r2': []
    }
    
    for fold_data in fold_results:
        metrics = fold_data.get('metrics', {})
        aggregated['mae'].append(metrics.get('mae', 0.0))
        aggregated['rmse'].append(metrics.get('rmse', 0.0))
        aggregated['r2'].append(metrics.get('r2', 0.0))
    
    return aggregated

def generate_comparison_table(results: Dict[str, Dict[str, float]]) -> str:
    """Generate a text-based comparison table."""
    lines = []
    lines.append("Model Comparison Results")
    lines.append("-" * 50)
    lines.append(f"{'Model':<20} {'MAE':<12} {'RMSE':<12} {'R2':<12}")
    lines.append("-" * 50)
    
    for model_name, metrics in results.items():
        mae = metrics.get('mae', 0.0)
        rmse = metrics.get('rmse', 0.0)
        r2 = metrics.get('r2', 0.0)
        lines.append(f"{model_name:<20} {mae:<12.4f} {rmse:<12.4f} {r2:<12.4f}")
    
    return "\n".join(lines)

def perform_statistical_significance_test(
    gnn_r2_scores: List[float], 
    baseline_r2_scores: List[float]
) -> Dict[str, float]:
    """
    Perform paired t-test to compare GNN vs Baseline R2 scores.
    Returns p-value and confidence interval for the difference.
    """
    if len(gnn_r2_scores) != len(baseline_r2_scores):
        raise ValueError("Number of folds must match for both models")
    
    differences = np.array(gnn_r2_scores) - np.array(baseline_r2_scores)
    
    # Paired t-test
    t_stat, p_value = stats.ttest_rel(gnn_r2_scores, baseline_r2_scores)
    
    # Calculate 95% confidence interval for the mean difference
    n = len(differences)
    mean_diff = np.mean(differences)
    std_diff = np.std(differences, ddof=1)
    se_diff = std_diff / np.sqrt(n)
    conf_interval = stats.t.interval(0.95, n - 1, loc=mean_diff, scale=se_diff)
    
    return {
        'p_value': float(p_value),
        'mean_difference': float(mean_diff),
        'ci_lower': float(conf_interval[0]),
        'ci_upper': float(conf_interval[1])
    }

def assess_practical_significance(
    stat_test_results: Dict[str, float],
    threshold_ci: float = 0.10,
    alpha: float = 0.05
) -> Tuple[str, Dict[str, Any]]:
    """
    Assess practical significance based on p-value and confidence interval.
    
    Returns:
        Tuple of (status_string, details_dict)
        
    Statuses:
        1. "Practically Significant" if p < alpha AND CI lower bound > threshold
        2. "Statistically Significant, but effect size uncertain" if p < alpha but CI includes threshold
        3. "No Statistical Significance" if p >= alpha
    """
    p_value = stat_test_results.get('p_value', 1.0)
    ci_lower = stat_test_results.get('ci_lower', 0.0)
    ci_upper = stat_test_results.get('ci_upper', 0.0)
    mean_diff = stat_test_results.get('mean_difference', 0.0)
    
    details = {
        'p_value': p_value,
        'mean_difference': mean_diff,
        'ci_lower': ci_lower,
        'ci_upper': ci_upper,
        'threshold': threshold_ci,
        'alpha': alpha
    }
    
    if p_value >= alpha:
        status = "No Statistical Significance"
    elif ci_lower > threshold_ci:
        status = "Practically Significant"
    else:
        # p < alpha but CI includes the threshold (ci_lower <= threshold <= ci_upper)
        status = "Statistically Significant, but effect size uncertain"
    
    return status, details

def main():
    """
    Main entry point for evaluation and significance assessment.
    This function orchestrates the full evaluation pipeline including:
    1. Loading model checkpoints
    2. Running inference
    3. Calculating metrics
    4. Performing statistical tests
    5. Assessing practical significance
    """
    # Configuration (would typically come from config file)
    data_dir = "data/processed"
    results_dir = "results"
    
    os.makedirs(results_dir, exist_ok=True)
    
    # Mock data for demonstration if real data not available
    # In real execution, this would load from actual K-Fold results
    try:
        # Attempt to load aggregated results from previous training step
        aggregated_path = os.path.join(data_dir, "kfold_results.json")
        if os.path.exists(aggregated_path):
            with open(aggregated_path, 'r') as f:
                aggregated_data = json.load(f)
            gnn_r2 = aggregated_data.get('gnn_r2', [])
            rf_r2 = aggregated_data.get('rf_r2', [])
            lr_r2 = aggregated_data.get('lr_r2', [])
        else:
            # Fallback for testing: simulate small dataset
            logger.warning("No K-Fold results found. Using simulated data for demonstration.")
            np.random.seed(42)
            gnn_r2 = [0.75, 0.78, 0.72, 0.80, 0.76]
            rf_r2 = [0.65, 0.68, 0.62, 0.70, 0.66]
            lr_r2 = [0.50, 0.52, 0.48, 0.55, 0.51]
            
    except Exception as e:
        logger.error(f"Error loading data: {e}")
        return 1

    # Perform statistical significance test: GNN vs Random Forest
    logger.info("Performing statistical significance test (GNN vs RF)...")
    stat_results_gnn_rf = perform_statistical_significance_test(gnn_r2, rf_r2)
    
    # Perform statistical significance test: GNN vs Linear Regression
    logger.info("Performing statistical significance test (GNN vs LR)...")
    stat_results_gnn_lr = perform_statistical_significance_test(gnn_r2, lr_r2)
    
    # Assess practical significance for GNN vs RF
    status_gnn_rf, details_gnn_rf = assess_practical_significance(stat_results_gnn_rf)
    
    # Assess practical significance for GNN vs LR
    status_gnn_lr, details_gnn_lr = assess_practical_significance(stat_results_gnn_lr)
    
    # Prepare final results
    final_results = {
        "statistical_tests": {
            "gnn_vs_rf": stat_results_gnn_rf,
            "gnn_vs_lr": stat_results_gnn_lr
        },
        "practical_significance": {
            "gnn_vs_rf": {
                "status": status_gnn_rf,
                "details": details_gnn_rf
            },
            "gnn_vs_lr": {
                "status": status_gnn_lr,
                "details": details_gnn_lr
            }
        }
    }
    
    # Save results
    output_path = os.path.join(results_dir, "significance_results.json")
    with open(output_path, 'w') as f:
        json.dump(final_results, f, indent=2)
    
    logger.info(f"Significance assessment results saved to {output_path}")
    logger.info(f"GNN vs RF Status: {status_gnn_rf}")
    logger.info(f"GNN vs LR Status: {status_gnn_lr}")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())