import csv
import json
import logging
import os
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional
import pickle
import numpy as np
from scipy import stats
import pandas as pd

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def load_convergence_results(path: str) -> List[Dict[str, Any]]:
    """Load convergence results from CSV."""
    if not os.path.exists(path):
        raise FileNotFoundError(f"Convergence results not found at {path}")
    results = []
    with open(path, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Convert types
            row['k'] = int(row['k'])
            row['is_correct'] = row['is_correct'] == 'True'
            row['converged'] = row['converged'] == 'True'
            row['censored'] = row['censored'] == 'True'
            row['first_correct_step'] = int(row['first_correct_step']) if row['first_correct_step'] and row['first_correct_step'] != 'None' else None
            results.append(row)
    return results

def load_router_predictions(model_path: str, entropy_path: str, filtered_splits_path: str) -> List[Dict[str, Any]]:
    """Load router model and predict optimal k for filtered splits."""
    if not os.path.exists(model_path):
        raise FileNotFoundError(f"Router model not found at {model_path}")
    
    with open(model_path, 'rb') as f:
        model = pickle.load(f)
    
    # Load entropy results
    entropy_df = pd.read_csv(entropy_path)
    entropy_dict = {row['task_id']: row['entropy'] for _, row in entropy_df.iterrows()}
    
    # Load filtered splits to get task_ids in the correct set
    with open(filtered_splits_path, 'r') as f:
        filtered_splits = json.load(f)
    
    # Combine train and test task_ids from filtered splits
    valid_task_ids = set()
    for split_type in ['train', 'test']:
        if split_type in filtered_splits:
            for item in filtered_splits[split_type]:
                valid_task_ids.add(item['task_id'])
    
    predictions = []
    for task_id in valid_task_ids:
        if task_id in entropy_dict:
            entropy_val = entropy_dict[task_id]
            # Predict using the model (assuming model expects a 2D array)
            X_pred = np.array([[entropy_val]])
            predicted_k = model.predict(X_pred)[0]
            
            # Ensure predicted_k is within valid range (1-3 based on core convergence)
            predicted_k = max(1, min(3, int(predicted_k)))
            
            predictions.append({
                'task_id': task_id,
                'predicted_k': predicted_k
            })
        else:
            logger.warning(f"Entropy not found for task_id: {task_id}")
    
    return predictions

def align_data(predictions: List[Dict[str, Any]], convergence_results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Align router predictions with convergence results."""
    # Create a lookup for convergence results
    conv_lookup = {}
    for row in convergence_results:
        task_id = row['task_id']
        if task_id not in conv_lookup:
            conv_lookup[task_id] = {}
        conv_lookup[task_id][row['k']] = row
    
    aligned = []
    for pred in predictions:
        task_id = pred['task_id']
        if task_id in conv_lookup:
            # Determine actual_k: first correct step, or None if never converged
            # We look at k=1, 2, 3 results
            actual_k = None
            is_censored = False
            
            # Check k=1, 2, 3 in order
            for k_val in [1, 2, 3]:
                if k_val in conv_lookup[task_id]:
                    row = conv_lookup[task_id][k_val]
                    if row['is_correct']:
                        actual_k = k_val
                        break
                elif k_val == 3 and task_id in conv_lookup and 3 in conv_lookup[task_id]:
                    # If we reached k=3 and it wasn't correct, check if it's censored
                    row = conv_lookup[task_id][3]
                    if row['censored']:
                        is_censored = True
            
            # If no correct step found by k=3, and it's censored at k=3
            if actual_k is None:
                if 3 in conv_lookup.get(task_id, {}) and conv_lookup[task_id][3]['censored']:
                    is_censored = True
            
            aligned.append({
                'task_id': task_id,
                'predicted_k': pred['predicted_k'],
                'actual_k': actual_k,
                'is_censored': is_censored
            })
        else:
            logger.warning(f"Convergence results not found for task_id: {task_id}")
    
    return aligned

def calculate_accuracy(aligned_data: List[Dict[str, Any]]) -> float:
    """Calculate router accuracy on non-censored samples."""
    non_censored = [d for d in aligned_data if not d['is_censored']]
    if not non_censored:
        return 0.0
    
    correct = sum(1 for d in non_censored if d['predicted_k'] == d['actual_k'])
    return correct / len(non_censored)

def calculate_random_baseline_accuracy(aligned_data: List[Dict[str, Any]]) -> float:
    """Calculate accuracy if router always predicted k=1."""
    non_censored = [d for d in aligned_data if not d['is_censored']]
    if not non_censored:
        return 0.0
    
    correct = sum(1 for d in non_censored if d['actual_k'] == 1)
    return correct / len(non_censored)

def paired_ttest_router_vs_baseline(aligned_data: List[Dict[str, Any]]) -> Dict[str, float]:
    """Perform paired t-test comparing router accuracy vs random baseline."""
    non_censored = [d for d in aligned_data if not d['is_censored']]
    if len(non_censored) < 2:
        return {'t_statistic': 0.0, 'p_value': 1.0, 'ci_lower': 0.0, 'ci_upper': 0.0}
    
    # For each sample, router is correct if predicted_k == actual_k
    router_correct = np.array([1 if d['predicted_k'] == d['actual_k'] else 0 for d in non_censored])
    # For random baseline (k=1), correct if actual_k == 1
    baseline_correct = np.array([1 if d['actual_k'] == 1 else 0 for d in non_censored])
    
    # Paired t-test
    t_stat, p_value = stats.ttest_rel(router_correct, baseline_correct)
    
    # Calculate confidence interval for the difference
    diff = router_correct - baseline_correct
    mean_diff = np.mean(diff)
    std_diff = np.std(diff, ddof=1)
    n = len(diff)
    se = std_diff / np.sqrt(n)
    ci_lower = mean_diff - 1.96 * se
    ci_upper = mean_diff + 1.96 * se
    
    return {
        't_statistic': float(t_stat),
        'p_value': float(p_value),
        'ci_lower': float(ci_lower),
        'ci_upper': float(ci_upper)
    }

def evaluate_router(predictions: List[Dict[str, Any]], convergence_results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Full router evaluation."""
    aligned = align_data(predictions, convergence_results)
    
    accuracy = calculate_accuracy(aligned)
    random_baseline = calculate_random_baseline_accuracy(aligned)
    t_test_results = paired_ttest_router_vs_baseline(aligned)
    
    return {
        'accuracy': accuracy,
        'random_baseline_accuracy': random_baseline,
        't_test': t_test_results,
        'sample_count': len([d for d in aligned if not d['is_censored']]),
        'censored_count': len([d for d in aligned if d['is_censored']])
    }

def save_evaluation_results(results: List[Dict[str, Any]], output_path: str):
    """Save router evaluation results to CSV."""
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        fieldnames = ['task_id', 'predicted_k', 'actual_k', 'accuracy', 'is_censored']
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        
        for row in results:
            # Determine accuracy for this row (True if predicted matches actual, for non-censored)
            is_accurate = False
            if not row['is_censored'] and row['actual_k'] is not None:
                is_accurate = row['predicted_k'] == row['actual_k']
            
            writer.writerow({
                'task_id': row['task_id'],
                'predicted_k': row['predicted_k'],
                'actual_k': row['actual_k'],
                'accuracy': is_accurate,
                'is_censored': row['is_censored']
            })

def print_evaluation_summary(evaluation_results: Dict[str, Any]):
    """Print a summary of the router evaluation."""
    print("\n" + "="*50)
    print("ROUTER EVALUATION SUMMARY")
    print("="*50)
    print(f"Router Accuracy: {evaluation_results['accuracy']:.4f}")
    print(f"Random Baseline (k=1) Accuracy: {evaluation_results['random_baseline_accuracy']:.4f}")
    print(f"T-statistic: {evaluation_results['t_test']['t_statistic']:.4f}")
    print(f"P-value: {evaluation_results['t_test']['p_value']:.4f}")
    print(f"95% CI for difference: [{evaluation_results['t_test']['ci_lower']:.4f}, {evaluation_results['t_test']['ci_upper']:.4f}]")
    print(f"Non-censored samples: {evaluation_results['sample_count']}")
    print(f"Censored samples: {evaluation_results['censored_count']}")
    print("="*50 + "\n")

def main():
    """Main entry point for router evaluation."""
    # Define paths
    project_root = Path(__file__).parent.parent
    router_model_path = project_root / "data" / "processed" / "router_model.pkl"
    entropy_path = project_root / "data" / "processed" / "entropy_results.csv"
    convergence_path = project_root / "data" / "processed" / "convergence_results_core.csv"
    filtered_splits_path = project_root / "data" / "processed" / "filtered_splits.json"
    output_path = project_root / "data" / "processed" / "router_results.csv"
    
    logger.info("Starting router evaluation...")
    
    try:
        # Load data
        logger.info("Loading router model and predicting...")
        predictions = load_router_predictions(str(router_model_path), str(entropy_path), str(filtered_splits_path))
        
        logger.info("Loading convergence results...")
        convergence_results = load_convergence_results(str(convergence_path))
        
        # Evaluate
        logger.info("Evaluating router...")
        evaluation_results = evaluate_router(predictions, convergence_results)
        
        # Save results
        logger.info(f"Saving results to {output_path}...")
        # Prepare aligned data for saving
        aligned = align_data(predictions, convergence_results)
        save_evaluation_results(aligned, str(output_path))
        
        # Print summary
        print_evaluation_summary(evaluation_results)
        
        logger.info("Router evaluation completed successfully.")
        
    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Error during evaluation: {e}")
        raise

if __name__ == "__main__":
    main()
