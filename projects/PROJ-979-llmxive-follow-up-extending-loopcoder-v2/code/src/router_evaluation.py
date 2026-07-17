"""
Router Evaluation Logic (T020)

Implements evaluation of the logistic regression router against a random baseline.
Performs statistical significance testing (paired t-test) to confirm the router
outperforms the baseline (predicting k=1 for all samples).

Dependencies:
- T019: logistic_router (trained model saved in data/processed/router_predictions.csv)
- T013/T013b: convergence_results.csv (ground truth for optimal k)
"""

import csv
import json
import logging
import os
import sys
from pathlib import Path
from typing import List, Dict, Tuple, Any, Optional

import numpy as np
from scipy import stats

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Project paths
PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_PROCESSED = PROJECT_ROOT / "data" / "processed"

# File paths
CONVERGENCE_RESULTS_PATH = DATA_PROCESSED / "convergence_results.csv"
ROUTER_PREDICTIONS_PATH = DATA_PROCESSED / "router_predictions.csv"
EVALUATION_RESULTS_PATH = DATA_PROCESSED / "router_evaluation_results.json"

def load_convergence_results() -> List[Dict[str, Any]]:
    """Load convergence results containing ground truth optimal k."""
    if not CONVERGENCE_RESULTS_PATH.exists():
        raise FileNotFoundError(
            f"Convergence results not found at {CONVERGENCE_RESULTS_PATH}. "
            "Ensure T013/T013b have completed and generated this file."
        )
    
    results = []
    with open(CONVERGENCE_RESULTS_PATH, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            results.append({
                'task_id': row['task_id'],
                'optimal_k': int(row['optimal_k']),
                'converged': row['converged'] == 'True'
            })
    
    logger.info(f"Loaded {len(results)} convergence results.")
    return results

def load_router_predictions() -> List[Dict[str, Any]]:
    """Load router predictions containing predicted k values."""
    if not ROUTER_PREDICTIONS_PATH.exists():
        raise FileNotFoundError(
            f"Router predictions not found at {ROUTER_PREDICTIONS_PATH}. "
            "Ensure T019 has completed and generated this file."
        )
    
    predictions = []
    with open(ROUTER_PREDICTIONS_PATH, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            predictions.append({
                'task_id': row['task_id'],
                'predicted_k': int(row['predicted_k']),
                'confidence': float(row['confidence'])
            })
    
    logger.info(f"Loaded {len(predictions)} router predictions.")
    return predictions

def align_data(convergence_data: List[Dict], router_data: List[Dict]) -> Tuple[List[int], List[int]]:
    """
    Align ground truth and predictions by task_id.
    
    Returns:
        Tuple of (ground_truth_k_list, predicted_k_list)
    """
    # Create lookup dictionaries
    ground_truth_map = {item['task_id']: item['optimal_k'] for item in convergence_data}
    prediction_map = {item['task_id']: item['predicted_k'] for item in router_data}
    
    common_ids = set(ground_truth_map.keys()) & set(prediction_map.keys())
    
    if not common_ids:
        raise ValueError("No common task_ids found between convergence results and router predictions.")
    
    logger.info(f"Aligned {len(common_ids)} samples for evaluation.")
    
    # Sort by task_id to ensure consistent ordering
    sorted_ids = sorted(common_ids)
    
    ground_truth_k = [ground_truth_map[tid] for tid in sorted_ids]
    predicted_k = [prediction_map[tid] for tid in sorted_ids]
    
    return ground_truth_k, predicted_k

def calculate_accuracy(ground_truth: List[int], predictions: List[int]) -> float:
    """
    Calculate accuracy: proportion of samples where predicted k == optimal k.
    
    Note: For this task, we define 'correct' as predicting the exact optimal k.
    """
    if len(ground_truth) != len(predictions):
        raise ValueError("Ground truth and predictions must have the same length.")
    
    correct = sum(1 for gt, pred in zip(ground_truth, predictions) if gt == pred)
    accuracy = correct / len(ground_truth)
    
    return accuracy

def calculate_random_baseline_accuracy(ground_truth: List[int]) -> float:
    """
    Calculate accuracy of the random baseline (predict k=1 for all samples).
    
    The random baseline predicts k=1 for every sample.
    Accuracy is the proportion of samples where optimal k == 1.
    """
    if not ground_truth:
        return 0.0
    
    correct = sum(1 for k in ground_truth if k == 1)
    accuracy = correct / len(ground_truth)
    
    return accuracy

def paired_ttest_router_vs_baseline(
    ground_truth: List[int], 
    router_predictions: List[int]
) -> Tuple[float, float]:
    """
    Perform a paired t-test comparing router performance vs random baseline.
    
    For each sample:
    - Router performance: 1 if router predicted optimal k, 0 otherwise
    - Baseline performance: 1 if optimal k == 1 (since baseline predicts k=1), 0 otherwise
    
    Returns:
        Tuple of (t_statistic, p_value)
    """
    if len(ground_truth) != len(router_predictions):
        raise ValueError("Ground truth and router predictions must have the same length.")
    
    # Binary performance: 1 if correct, 0 if incorrect
    router_correct = np.array([1 if gt == pred else 0 for gt, pred in zip(ground_truth, router_predictions)])
    baseline_correct = np.array([1 if gt == 1 else 0 for gt in ground_truth])
    
    # Paired t-test
    t_stat, p_value = stats.ttest_rel(router_correct, baseline_correct)
    
    return t_stat, p_value

def bootstrap_significance_test(
    ground_truth: List[int],
    router_predictions: List[int],
    n_iterations: int = 10000,
    random_seed: int = 42
) -> float:
    """
    Perform a bootstrap test to estimate the probability that router accuracy
    is greater than baseline accuracy.
    
    Returns:
        p_value: Probability that router <= baseline (one-tailed)
    """
    np.random.seed(random_seed)
    n_samples = len(ground_truth)
    
    router_correct = np.array([1 if gt == pred else 0 for gt, pred in zip(ground_truth, router_predictions)])
    baseline_correct = np.array([1 if gt == 1 else 0 for gt in ground_truth])
    
    # Calculate observed difference
    observed_diff = np.mean(router_correct) - np.mean(baseline_correct)
    
    # Bootstrap distribution of the difference
    bootstrap_diffs = []
    for _ in range(n_iterations):
        indices = np.random.choice(n_samples, size=n_samples, replace=True)
        boot_router = router_correct[indices]
        boot_baseline = baseline_correct[indices]
        
        diff = np.mean(boot_router) - np.mean(boot_baseline)
        bootstrap_diffs.append(diff)
    
    # One-tailed p-value: probability that bootstrap diff <= 0
    p_value = np.mean(np.array(bootstrap_diffs) <= 0)
    
    return p_value

def evaluate_router(
    ground_truth: List[int],
    router_predictions: List[int],
    use_bootstrap: bool = False,
    bootstrap_iterations: int = 10000
) -> Dict[str, Any]:
    """
    Comprehensive evaluation of the router against the random baseline.
    
    Returns:
        Dictionary containing:
        - router_accuracy
        - baseline_accuracy
        - accuracy_improvement
        - statistical_test (t-test or bootstrap)
        - is_significant (p < 0.05)
    """
    # Calculate accuracies
    router_accuracy = calculate_accuracy(ground_truth, router_predictions)
    baseline_accuracy = calculate_random_baseline_accuracy(ground_truth)
    accuracy_improvement = router_accuracy - baseline_accuracy
    
    # Statistical significance testing
    if use_bootstrap:
        p_value = bootstrap_significance_test(
            ground_truth, 
            router_predictions, 
            n_iterations=bootstrap_iterations
        )
        test_type = "bootstrap"
    else:
        t_stat, p_value = paired_ttest_router_vs_baseline(ground_truth, router_predictions)
        test_type = "paired_ttest"
    
    is_significant = p_value < 0.05
    
    results = {
        "router_accuracy": router_accuracy,
        "baseline_accuracy": baseline_accuracy,
        "accuracy_improvement": accuracy_improvement,
        "sample_size": len(ground_truth),
        "statistical_test": test_type,
        "p_value": p_value,
        "is_significant": is_significant,
        "significance_threshold": 0.05
    }
    
    if test_type == "paired_ttest":
        results["t_statistic"] = t_stat
    
    return results

def save_evaluation_results(results: Dict[str, Any], output_path: Path) -> None:
    """Save evaluation results to JSON file."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"Evaluation results saved to {output_path}")

def print_evaluation_summary(results: Dict[str, Any]) -> None:
    """Print a human-readable summary of the evaluation results."""
    print("\n" + "="*60)
    print("ROUTER EVALUATION SUMMARY")
    print("="*60)
    print(f"Sample Size: {results['sample_size']}")
    print(f"Router Accuracy: {results['router_accuracy']:.4f}")
    print(f"Baseline Accuracy (k=1): {results['baseline_accuracy']:.4f}")
    print(f"Accuracy Improvement: {results['accuracy_improvement']:.4f}")
    print("-"*60)
    print(f"Statistical Test: {results['statistical_test']}")
    if results['statistical_test'] == 'paired_ttest':
        print(f"t-statistic: {results['t_statistic']:.4f}")
    print(f"p-value: {results['p_value']:.6f}")
    print(f"Significant (p < 0.05): {'YES' if results['is_significant'] else 'NO'}")
    print("="*60 + "\n")

def main() -> None:
    """Main entry point for router evaluation."""
    logger.info("Starting router evaluation (T020)...")
    
    try:
        # Load data
        convergence_data = load_convergence_results()
        router_data = load_router_predictions()
        
        # Align data
        ground_truth_k, router_predictions_k = align_data(convergence_data, router_data)
        
        # Evaluate router
        results = evaluate_router(
            ground_truth_k,
            router_predictions_k,
            use_bootstrap=False,  # Use t-test by default
            bootstrap_iterations=10000
        )
        
        # Save results
        save_evaluation_results(results, EVALUATION_RESULTS_PATH)
        
        # Print summary
        print_evaluation_summary(results)
        
        # Exit with error if not significant (optional, depending on requirements)
        if not results['is_significant']:
            logger.warning("Router performance is NOT statistically significant (p >= 0.05)")
            # Note: We do not exit with error code as the task is to perform the test,
            # not to enforce significance. The result is still valid.
        
        logger.info("Router evaluation completed successfully.")
        
    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        sys.exit(1)
    except ValueError as e:
        logger.error(f"Value error: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error during evaluation: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
