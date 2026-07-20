import csv
import json
import logging
import os
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import numpy as np
from scipy import stats

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_convergence_results(filepath: str) -> List[Dict[str, Any]]:
    """
    Load convergence results from a CSV file.
    
    Args:
        filepath: Path to the convergence results CSV file.
        
    Returns:
        List of dictionaries containing convergence data.
    """
    results = []
    with open(filepath, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Convert numeric fields
            row['convergence_step'] = int(row['convergence_step'])
            row['k'] = int(row['k'])
            results.append(row)
    return results

def load_router_predictions(filepath: str) -> List[Dict[str, Any]]:
    """
    Load router predictions from a CSV file.
    
    Args:
        filepath: Path to the router predictions CSV file.
        
    Returns:
        List of dictionaries containing router predictions.
    """
    results = []
    with open(filepath, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Convert numeric fields
            row['predicted_k'] = int(row['predicted_k'])
            row['actual_k'] = int(row['actual_k'])
            results.append(row)
    return results

def align_data(convergence_results: List[Dict], router_predictions: List[Dict]) -> List[Dict[str, Any]]:
    """
    Align convergence results with router predictions by task_id.
    
    Args:
        convergence_results: List of convergence result dictionaries.
        router_predictions: List of router prediction dictionaries.
        
    Returns:
        List of aligned dictionaries containing both convergence and prediction data.
    """
    # Create a lookup dictionary for router predictions
    pred_lookup = {pred['task_id']: pred for pred in router_predictions}
    
    aligned_data = []
    for conv in convergence_results:
        task_id = conv['task_id']
        if task_id in pred_lookup:
            pred = pred_lookup[task_id]
            aligned = {
                'task_id': task_id,
                'convergence_step': conv['convergence_step'],
                'actual_k': pred['actual_k'],
                'predicted_k': pred['predicted_k'],
                'entropy': float(pred.get('entropy', 0)),
                'difficulty': pred.get('difficulty', 'unknown')
            }
            aligned_data.append(aligned)
        else:
            logger.warning(f"No router prediction found for task_id: {task_id}")
    
    return aligned_data

def calculate_accuracy(aligned_data: List[Dict[str, Any]], tolerance: int = 1) -> float:
    """
    Calculate accuracy of the router's predicted k values.
    A prediction is considered correct if it is within 'tolerance' of the actual k.
    
    Args:
        aligned_data: List of aligned dictionaries.
        tolerance: Acceptable deviation from actual k (default: 1).
        
    Returns:
        Accuracy as a float between 0 and 1.
    """
    if not aligned_data:
        return 0.0
    
    correct = 0
    for item in aligned_data:
        actual = item['actual_k']
        predicted = item['predicted_k']
        if abs(predicted - actual) <= tolerance:
            correct += 1
    
    return correct / len(aligned_data)

def calculate_random_baseline_accuracy(aligned_data: List[Dict[str, Any]], possible_k_values: List[int] = [1, 2, 3, 4]) -> float:
    """
    Calculate accuracy of a random baseline that predicts k=1 for all samples.
    
    Args:
        aligned_data: List of aligned dictionaries.
        possible_k_values: List of possible k values (used for random baseline logic).
        
    Returns:
        Accuracy of the random baseline (predicting k=1 for all).
    """
    if not aligned_data:
        return 0.0
    
    # Random baseline: predict k=1 for all
    # Accuracy is the proportion of samples where actual_k == 1
    correct = sum(1 for item in aligned_data if item['actual_k'] == 1)
    return correct / len(aligned_data)

def paired_ttest_router_vs_baseline(router_accuracies: List[float], baseline_accuracies: List[float]) -> Tuple[float, float]:
    """
    Perform a paired t-test to compare router accuracy vs baseline accuracy.
    
    Args:
        router_accuracies: List of accuracy values for the router (per fold/sample).
        baseline_accuracies: List of accuracy values for the baseline (per fold/sample).
        
    Returns:
        Tuple of (t-statistic, p-value).
    """
    if len(router_accuracies) != len(baseline_accuracies):
        raise ValueError("Router and baseline accuracy lists must have the same length")
    
    if len(router_accuracies) < 2:
        logger.warning("Not enough samples for t-test. Returning NaN.")
        return float('nan'), float('nan')
    
    t_stat, p_val = stats.ttest_rel(router_accuracies, baseline_accuracies)
    return t_stat, p_val

def bootstrap_significance_test(router_accuracies: List[float], baseline_accuracies: List[float], 
                                n_iterations: int = 1000, confidence_level: float = 0.95) -> Tuple[float, float, bool]:
    """
    Perform a bootstrap test to confirm statistical significance.
    
    Args:
        router_accuracies: List of accuracy values for the router.
        baseline_accuracies: List of accuracy values for the baseline.
        n_iterations: Number of bootstrap iterations.
        confidence_level: Confidence level for the test.
        
    Returns:
        Tuple of (mean difference, p-value, is_significant).
    """
    if len(router_accuracies) != len(baseline_accuracies):
        raise ValueError("Router and baseline accuracy lists must have the same length")
    
    n_samples = len(router_accuracies)
    differences = []
    
    for _ in range(n_iterations):
        # Bootstrap sampling with replacement
        indices = np.random.choice(n_samples, size=n_samples, replace=True)
        boot_router = [router_accuracies[i] for i in indices]
        boot_baseline = [baseline_accuracies[i] for i in indices]
        
        # Calculate mean difference for this bootstrap sample
        mean_diff = np.mean(boot_router) - np.mean(boot_baseline)
        differences.append(mean_diff)
    
    # Calculate p-value (one-tailed test: router > baseline)
    observed_diff = np.mean(router_accuracies) - np.mean(baseline_accuracies)
    p_val = sum(1 for d in differences if d >= observed_diff) / n_iterations
    
    # Calculate confidence interval
    alpha = 1 - confidence_level
    lower_bound = np.percentile(differences, 100 * alpha / 2)
    upper_bound = np.percentile(differences, 100 * (1 - alpha / 2))
    
    # Determine significance
    is_significant = (p_val < (1 - confidence_level)) and (lower_bound > 0)
    
    return observed_diff, p_val, is_significant

def evaluate_router(aligned_data: List[Dict[str, Any]], possible_k_values: List[int] = [1, 2, 3, 4]) -> Dict[str, Any]:
    """
    Evaluate the router against a random baseline.
    
    Args:
        aligned_data: List of aligned dictionaries.
        possible_k_values: List of possible k values.
        
    Returns:
        Dictionary containing evaluation results.
    """
    # Calculate router accuracy
    router_accuracy = calculate_accuracy(aligned_data)
    
    # Calculate random baseline accuracy (predicting k=1 for all)
    baseline_accuracy = calculate_random_baseline_accuracy(aligned_data, possible_k_values)
    
    # Prepare data for statistical tests
    # For paired test, we create per-sample "accuracy" (1 if correct, 0 otherwise)
    router_correct = [1 if abs(item['predicted_k'] - item['actual_k']) <= 1 else 0 for item in aligned_data]
    baseline_correct = [1 if item['actual_k'] == 1 else 0 for item in aligned_data]
    
    # Perform paired t-test
    t_stat, p_val_ttest = paired_ttest_router_vs_baseline(router_correct, baseline_correct)
    
    # Perform bootstrap test
    mean_diff, p_val_bootstrap, is_significant = bootstrap_significance_test(
        router_correct, baseline_correct
    )
    
    return {
        'router_accuracy': router_accuracy,
        'baseline_accuracy': baseline_accuracy,
        'accuracy_improvement': router_accuracy - baseline_accuracy,
        't_statistic': t_stat,
        'p_value_ttest': p_val_ttest,
        'bootstrap_mean_difference': mean_diff,
        'bootstrap_p_value': p_val_bootstrap,
        'is_significant': is_significant,
        'significance_level': 0.05,
        'n_samples': len(aligned_data)
    }

def save_evaluation_results(results: Dict[str, Any], filepath: str) -> None:
    """
    Save evaluation results to a JSON file.
    
    Args:
        results: Dictionary containing evaluation results.
        filepath: Path to save the JSON file.
    """
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2)
    logger.info(f"Evaluation results saved to {filepath}")

def print_evaluation_summary(results: Dict[str, Any]) -> None:
    """
    Print a summary of the evaluation results.
    
    Args:
        results: Dictionary containing evaluation results.
    """
    print("\n" + "="*60)
    print("ROUTER EVALUATION SUMMARY")
    print("="*60)
    print(f"Router Accuracy:        {results['router_accuracy']:.4f}")
    print(f"Baseline Accuracy:      {results['baseline_accuracy']:.4f}")
    print(f"Improvement:            {results['accuracy_improvement']:.4f}")
    print(f"Samples Analyzed:       {results['n_samples']}")
    print("-"*60)
    print("Statistical Significance Test (Paired T-Test):")
    print(f"  T-Statistic:          {results['t_statistic']:.4f}")
    print(f"  P-Value:              {results['p_value_ttest']:.4f}")
    print(f"  Significant (p<0.05): {'Yes' if results['p_value_ttest'] < 0.05 else 'No'}")
    print("-"*60)
    print("Bootstrap Significance Test:")
    print(f"  Mean Difference:      {results['bootstrap_mean_difference']:.4f}")
    print(f"  Bootstrap P-Value:    {results['bootstrap_p_value']:.4f}")
    print(f"  Significant:          {'Yes' if results['is_significant'] else 'No'}")
    print("="*60 + "\n")

def main():
    """
    Main function to run the router evaluation.
    """
    # Define paths
    project_root = Path(__file__).resolve().parent.parent.parent
    convergence_file = project_root / "data" / "processed" / "convergence_results.csv"
    router_predictions_file = project_root / "data" / "processed" / "router_predictions.csv"
    output_file = project_root / "data" / "processed" / "router_accuracy_test.json"
    
    logger.info("Starting router evaluation...")
    
    # Check if required files exist
    if not convergence_file.exists():
        logger.error(f"Convergence results file not found: {convergence_file}")
        sys.exit(1)
    
    if not router_predictions_file.exists():
        logger.error(f"Router predictions file not found: {router_predictions_file}")
        sys.exit(1)
    
    # Load data
    logger.info(f"Loading convergence results from {convergence_file}")
    convergence_results = load_convergence_results(str(convergence_file))
    logger.info(f"Loaded {len(convergence_results)} convergence results")
    
    logger.info(f"Loading router predictions from {router_predictions_file}")
    router_predictions = load_router_predictions(str(router_predictions_file))
    logger.info(f"Loaded {len(router_predictions)} router predictions")
    
    # Align data
    logger.info("Aligning convergence results with router predictions...")
    aligned_data = align_data(convergence_results, router_predictions)
    logger.info(f"Aligned {len(aligned_data)} samples")
    
    if len(aligned_data) == 0:
        logger.error("No aligned data found. Cannot proceed with evaluation.")
        sys.exit(1)
    
    # Evaluate router
    logger.info("Evaluating router against random baseline...")
    results = evaluate_router(aligned_data)
    
    # Save results
    logger.info(f"Saving evaluation results to {output_file}")
    save_evaluation_results(results, str(output_file))
    
    # Print summary
    print_evaluation_summary(results)
    
    logger.info("Router evaluation completed successfully.")
    return results

if __name__ == "__main__":
    main()
