"""
Router Evaluation Module for User Story 2.

Implements evaluation logic for the dynamic router, comparing prediction accuracy
against a random baseline (predicting k=1 for all samples) and performing
statistical significance testing using a paired t-test.
"""

import csv
import json
import logging
import os
import sys
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional
from scipy import stats
import numpy as np

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
OUTPUT_DIR = Path("data/processed")
OUTPUT_FILE = OUTPUT_DIR / "router_accuracy_test.json"


def load_convergence_results(path: Path) -> List[Dict[str, Any]]:
    """
    Load convergence results from a CSV file.

    Args:
        path: Path to the convergence results CSV.

    Returns:
        List of dictionaries containing convergence data.
    """
    if not path.exists():
        raise FileNotFoundError(f"Convergence results file not found: {path}")

    results = []
    with open(path, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Convert numeric fields
            row['k_correct'] = int(row['k_correct'])
            results.append(row)

    logger.info(f"Loaded {len(results)} convergence results from {path}")
    return results


def load_router_predictions(path: Path) -> List[Dict[str, Any]]:
    """
    Load router predictions from a JSON file.

    Args:
        path: Path to the router predictions JSON file.

    Returns:
        List of dictionaries containing router predictions.
    """
    if not path.exists():
        raise FileNotFoundError(f"Router predictions file not found: {path}")

    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # Handle both list and dict formats
    if isinstance(data, dict) and 'predictions' in data:
        predictions = data['predictions']
    elif isinstance(data, list):
        predictions = data
    else:
        raise ValueError(f"Unexpected format in router predictions file: {path}")

    logger.info(f"Loaded {len(predictions)} router predictions from {path}")
    return predictions


def align_data(
    convergence_results: List[Dict[str, Any]],
    router_predictions: List[Dict[str, Any]]
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Align convergence results with router predictions by task_id.

    Args:
        convergence_results: List of convergence result dictionaries.
        router_predictions: List of router prediction dictionaries.

    Returns:
        Tuple of (aligned_convergence, aligned_predictions) lists.
    """
    # Create lookup dictionaries
    conv_lookup = {r['task_id']: r for r in convergence_results}
    pred_lookup = {r['task_id']: r for r in router_predictions}

    # Find common task_ids
    common_ids = set(conv_lookup.keys()) & set(pred_lookup.keys())

    if not common_ids:
        raise ValueError("No common task_ids found between convergence results and router predictions")

    logger.info(f"Aligned {len(common_ids)} samples based on common task_ids")

    # Sort by task_id for consistent ordering
    sorted_ids = sorted(common_ids)

    aligned_convergence = [conv_lookup[tid] for tid in sorted_ids]
    aligned_predictions = [pred_lookup[tid] for tid in sorted_ids]

    return aligned_convergence, aligned_predictions


def calculate_accuracy(
    predictions: List[Dict[str, Any]],
    actual_k_correct: List[int]
) -> float:
    """
    Calculate the accuracy of the router predictions.

    For this evaluation, we consider a prediction accurate if the predicted
    optimal k (minimum k where solution is correct) matches the actual k_correct.

    Args:
        predictions: List of router prediction dictionaries.
        actual_k_correct: List of actual k_correct values from convergence results.

    Returns:
        Accuracy as a float between 0 and 1.
    """
    if len(predictions) != len(actual_k_correct):
        raise ValueError("Length mismatch between predictions and actual_k_correct")

    correct = 0
    total = len(predictions)

    for pred, actual in zip(predictions, actual_k_correct):
        predicted_k = int(pred.get('predicted_k', 1))
        if predicted_k == actual:
            correct += 1

    accuracy = correct / total if total > 0 else 0.0
    logger.info(f"Router accuracy: {accuracy:.4f} ({correct}/{total})")
    return accuracy


def calculate_random_baseline_accuracy(
    convergence_results: List[Dict[str, Any]]
) -> float:
    """
    Calculate the accuracy of a random baseline that predicts k=1 for all samples.

    Args:
        convergence_results: List of convergence result dictionaries.

    Returns:
        Accuracy of the random baseline as a float between 0 and 1.
    """
    if not convergence_results:
        return 0.0

    correct = 0
    total = len(convergence_results)

    for result in convergence_results:
        actual_k = int(result.get('k_correct', 1))
        # Random baseline predicts k=1
        if actual_k == 1:
            correct += 1

    accuracy = correct / total if total > 0 else 0.0
    logger.info(f"Random baseline accuracy (k=1): {accuracy:.4f} ({correct}/{total})")
    return accuracy


def paired_ttest_router_vs_baseline(
    router_predictions: List[Dict[str, Any]],
    convergence_results: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Perform a paired t-test to compare router accuracy against random baseline.

    The test compares the per-sample correctness of the router vs. the baseline
    (which always predicts k=1).

    Args:
        router_predictions: List of router prediction dictionaries.
        convergence_results: List of convergence result dictionaries.

    Returns:
        Dictionary containing t-statistic, p-value, and test details.
    """
    if len(router_predictions) != len(convergence_results):
        raise ValueError("Length mismatch between router predictions and convergence results")

    # Create binary correctness arrays
    router_correct = []
    baseline_correct = []

    for pred, result in zip(router_predictions, convergence_results):
        predicted_k = int(pred.get('predicted_k', 1))
        actual_k = int(result.get('k_correct', 1))

        # Router correctness
        router_correct.append(1 if predicted_k == actual_k else 0)

        # Baseline correctness (always predicts k=1)
        baseline_correct.append(1 if actual_k == 1 else 0)

    # Convert to numpy arrays
    router_arr = np.array(router_correct)
    baseline_arr = np.array(baseline_correct)

    # Perform paired t-test
    t_stat, p_value = stats.ttest_rel(router_arr, baseline_arr)

    # Calculate mean accuracies
    router_acc = np.mean(router_arr)
    baseline_acc = np.mean(baseline_arr)

    result = {
        't_statistic': float(t_stat),
        'p_value': float(p_value),
        'router_mean_accuracy': float(router_acc),
        'baseline_mean_accuracy': float(baseline_acc),
        'sample_size': len(router_arr),
        'test_type': 'paired_ttest',
        'is_significant': p_value < 0.05
    }

    logger.info(f"Paired t-test: t={t_stat:.4f}, p={p_value:.6f}, significant={result['is_significant']}")
    return result


def bootstrap_significance_test(
    router_predictions: List[Dict[str, Any]],
    convergence_results: List[Dict[str, Any]],
    n_bootstrap: int = 1000,
    confidence_level: float = 0.95
) -> Dict[str, Any]:
    """
    Perform a bootstrap test to assess the significance of the accuracy difference.

    Args:
        router_predictions: List of router prediction dictionaries.
        convergence_results: List of convergence result dictionaries.
        n_bootstrap: Number of bootstrap iterations.
        confidence_level: Confidence level for the interval.

    Returns:
        Dictionary containing bootstrap results.
    """
    if len(router_predictions) != len(convergence_results):
        raise ValueError("Length mismatch between router predictions and convergence results")

    # Create binary correctness arrays
    router_correct = []
    baseline_correct = []

    for pred, result in zip(router_predictions, convergence_results):
        predicted_k = int(pred.get('predicted_k', 1))
        actual_k = int(result.get('k_correct', 1))

        router_correct.append(1 if predicted_k == actual_k else 0)
        baseline_correct.append(1 if actual_k == 1 else 0)

    router_arr = np.array(router_correct)
    baseline_arr = np.array(baseline_correct)

    # Bootstrap sampling
    bootstrap_diffs = []
    n = len(router_arr)

    for _ in range(n_bootstrap):
        indices = np.random.choice(n, size=n, replace=True)
        boot_router = router_arr[indices]
        boot_baseline = baseline_arr[indices]
        diff = np.mean(boot_router) - np.mean(boot_baseline)
        bootstrap_diffs.append(diff)

    bootstrap_diffs = np.array(bootstrap_diffs)

    # Calculate confidence interval
    alpha = 1 - confidence_level
    lower = np.percentile(bootstrap_diffs, 100 * alpha / 2)
    upper = np.percentile(bootstrap_diffs, 100 * (1 - alpha / 2))

    # Calculate p-value (one-sided: router > baseline)
    p_value = np.mean(bootstrap_diffs <= 0)

    result = {
        'bootstrap_mean_diff': float(np.mean(bootstrap_diffs)),
        'bootstrap_std_diff': float(np.std(bootstrap_diffs)),
        'confidence_interval': [float(lower), float(upper)],
        'bootstrap_p_value': float(p_value),
        'n_bootstrap': n_bootstrap,
        'confidence_level': confidence_level
    }

    logger.info(f"Bootstrap test: mean_diff={result['bootstrap_mean_diff']:.4f}, "
                f"CI=[{lower:.4f}, {upper:.4f}], p={p_value:.6f}")
    return result


def evaluate_router(
    router_predictions_path: Path,
    convergence_results_path: Path
) -> Dict[str, Any]:
    """
    Evaluate the router against the random baseline and perform statistical tests.

    Args:
        router_predictions_path: Path to router predictions JSON file.
        convergence_results_path: Path to convergence results CSV file.

    Returns:
        Dictionary containing all evaluation results.
    """
    # Load data
    router_predictions = load_router_predictions(router_predictions_path)
    convergence_results = load_convergence_results(convergence_results_path)

    # Align data
    aligned_conv, aligned_pred = align_data(convergence_results, router_predictions)

    # Calculate accuracies
    router_acc = calculate_accuracy(aligned_pred, [r['k_correct'] for r in aligned_conv])
    baseline_acc = calculate_random_baseline_accuracy(aligned_conv)

    # Perform paired t-test
    ttest_result = paired_ttest_router_vs_baseline(aligned_pred, aligned_conv)

    # Perform bootstrap test
    bootstrap_result = bootstrap_significance_test(aligned_pred, aligned_conv)

    # Compile results
    evaluation_results = {
        'router_accuracy': router_acc,
        'random_baseline_accuracy': baseline_acc,
        'accuracy_improvement': router_acc - baseline_acc,
        'sample_size': len(aligned_conv),
        'paired_ttest': ttest_result,
        'bootstrap_test': bootstrap_result,
        'is_significantly_better': ttest_result['is_significant'] and (router_acc > baseline_acc)
    }

    logger.info(f"Evaluation complete. Router accuracy: {router_acc:.4f}, "
                f"Baseline: {baseline_acc:.4f}, Improvement: {router_acc - baseline_acc:.4f}")

    return evaluation_results


def save_evaluation_results(results: Dict[str, Any], output_path: Path) -> None:
    """
    Save evaluation results to a JSON file.

    Args:
        results: Dictionary containing evaluation results.
        output_path: Path to save the results JSON.
    """
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, default=str)

    logger.info(f"Saved evaluation results to {output_path}")


def print_evaluation_summary(results: Dict[str, Any]) -> None:
    """
    Print a summary of the evaluation results to the console.

    Args:
        results: Dictionary containing evaluation results.
    """
    print("\n" + "="*60)
    print("ROUTER EVALUATION SUMMARY")
    print("="*60)
    print(f"Sample Size: {results['sample_size']}")
    print(f"Router Accuracy: {results['router_accuracy']:.4f}")
    print(f"Random Baseline Accuracy: {results['random_baseline_accuracy']:.4f}")
    print(f"Accuracy Improvement: {results['accuracy_improvement']:.4f}")
    print("-"*60)
    print("Paired T-Test Results:")
    print(f"  t-statistic: {results['paired_ttest']['t_statistic']:.4f}")
    print(f"  p-value: {results['paired_ttest']['p_value']:.6f}")
    print(f"  Significant (p < 0.05): {results['paired_ttest']['is_significant']}")
    print("-"*60)
    print("Bootstrap Test Results:")
    print(f"  Mean Difference: {results['bootstrap_test']['bootstrap_mean_diff']:.4f}")
    print(f"  95% CI: [{results['bootstrap_test']['confidence_interval'][0]:.4f}, "
          f"{results['bootstrap_test']['confidence_interval'][1]:.4f}]")
    print(f"  Bootstrap p-value: {results['bootstrap_test']['bootstrap_p_value']:.6f}")
    print("-"*60)
    print(f"Conclusion: Router is {'significantly' if results['is_significantly_better'] else 'NOT significantly'} "
          f"better than random baseline (k=1).")
    print("="*60 + "\n")


def main() -> None:
    """
    Main entry point for router evaluation.
    """
    logger.info("Starting router evaluation...")

    # Define paths
    router_predictions_path = Path("data/processed/router_predictions.json")
    convergence_results_path = Path("data/processed/convergence_results.csv")
    output_path = OUTPUT_DIR / "router_accuracy_test.json"

    # Check if required files exist
    if not router_predictions_path.exists():
        logger.error(f"Router predictions file not found: {router_predictions_path}")
        logger.error("Please ensure T019 has been completed and router_predictions.json exists.")
        sys.exit(1)

    if not convergence_results_path.exists():
        logger.error(f"Convergence results file not found: {convergence_results_path}")
        logger.error("Please ensure T013d has been completed and convergence_results.csv exists.")
        sys.exit(1)

    try:
        # Evaluate router
        results = evaluate_router(router_predictions_path, convergence_results_path)

        # Save results
        save_evaluation_results(results, output_path)

        # Print summary
        print_evaluation_summary(results)

        logger.info("Router evaluation completed successfully.")

    except Exception as e:
        logger.error(f"Error during router evaluation: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
