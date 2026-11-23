import csv
import json
import logging
import os
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

# Import from utils if available, otherwise define locally to ensure independence
# The API surface lists `calculate_flops` in `code/src/utils.py`
try:
    from .utils import calculate_flops
except ImportError:
    # Fallback definition if utils is not importable in this context
    def calculate_flops(model_params: int, seq_len: int, k: int) -> float:
        """
        Calculate FLOPs for a transformer model.
        Approximate formula: 2 * model_params * seq_len * k
        (2 for multiply-add, k for the number of forward passes in the loop)
        """
        return 2.0 * model_params * seq_len * k

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Default model parameter count for CodeLlama-1.3b (approx 1.3 billion)
DEFAULT_MODEL_PARAMS = 1_300_000_000
DEFAULT_SEQ_LEN = 512

def load_convergence_results(input_path: str) -> List[Dict[str, Any]]:
    """
    Load convergence results from a CSV file.
    Expected columns: task_id, k, output, is_correct, first_correct_step, censored, time_to_event
    """
    results = []
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Convergence results not found at {input_path}")
    
    with open(input_path, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Convert string booleans to actual booleans
            row['is_correct'] = row['is_correct'].strip().lower() == 'true'
            row['censored'] = row['censored'].strip().lower() == 'true'
            row['k'] = int(row['k'])
            row['first_correct_step'] = int(row['first_correct_step']) if row['first_correct_step'] else None
            row['time_to_event'] = int(row['time_to_event'])
            results.append(row)
    
    return results

def calculate_accuracy_for_k(results: List[Dict[str, Any]], k: int) -> float:
    """
    Calculate accuracy (pass@1) for a specific k.
    We consider a task correct if it was solved at step k or earlier (first_correct_step <= k).
    However, for a static k=2 baseline, we only get the output at k=2.
    So we check if the output at k=2 is correct.
    """
    if not results:
        return 0.0
    
    correct_count = 0
    task_ids = set()
    
    # Group by task_id to ensure we count each task once
    # For static k=2, we look at the row where k=2
    relevant_rows = [r for r in results if r['k'] == k]
    
    if not relevant_rows:
        # If no rows for k=2, accuracy is 0
        return 0.0
        
    for row in relevant_rows:
        task_ids.add(row['task_id'])
        if row['is_correct']:
            correct_count += 1
    
    if not task_ids:
        return 0.0
        
    return correct_count / len(task_ids)

def calculate_flops_for_static_k(k: int, num_samples: int) -> float:
    """
    Calculate total FLOPs for running inference with a static k across all samples.
    """
    # FLOPs per sample = calculate_flops(model_params, seq_len, k)
    # We assume a fixed sequence length and model size
    flops_per_sample = calculate_flops(DEFAULT_MODEL_PARAMS, DEFAULT_SEQ_LEN, k)
    return flops_per_sample * num_samples

def calculate_static_k2_baseline(convergence_results_path: str, output_path: str) -> Dict[str, Any]:
    """
    Compute FLOPs and accuracy for always using k=2 on the filtered test set.
    
    Logic:
    1. Load convergence results.
    2. Filter for rows where k=2 (since we are simulating a static k=2 policy).
    3. Calculate accuracy based on the correctness of the k=2 output.
    4. Calculate total FLOPs assuming every task runs k=2.
    5. Save results to JSON.
    """
    logger.info(f"Loading convergence results from {convergence_results_path}")
    results = load_convergence_results(convergence_results_path)
    
    if not results:
        logger.warning("No convergence results found. Cannot calculate baseline.")
        return {"total_flops": 0.0, "accuracy": 0.0}

    # Determine the set of unique tasks in the dataset
    unique_task_ids = set(r['task_id'] for r in results)
    num_tasks = len(unique_task_ids)
    
    if num_tasks == 0:
        logger.warning("No tasks found in convergence results.")
        return {"total_flops": 0.0, "accuracy": 0.0}

    # For a static k=2 baseline, we assume we run inference up to k=2 for every task.
    # We use the row where k=2 to determine correctness.
    k2_rows = {r['task_id']: r for r in results if r['k'] == 2}
    
    correct_count = 0
    for task_id in unique_task_ids:
        if task_id in k2_rows:
            if k2_rows[task_id]['is_correct']:
                correct_count += 1
        # If k=2 row is missing for a task, we assume it failed or wasn't reached,
        # contributing 0 to the correct count.
    
    accuracy = correct_count / num_tasks
    
    # Calculate FLOPs: We run k=2 for every task.
    # The cost is proportional to k.
    total_flops = calculate_flops_for_static_k(k=2, num_samples=num_tasks)
    
    baseline_results = {
        "total_flops": total_flops,
        "accuracy": accuracy,
        "num_tasks": num_tasks,
        "k_value": 2,
        "model_params": DEFAULT_MODEL_PARAMS,
        "seq_len": DEFAULT_SEQ_LEN
    }
    
    # Ensure output directory exists
    output_dir = os.path.dirname(output_path)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(baseline_results, f, indent=2)
    
    logger.info(f"Static k=2 baseline saved to {output_path}")
    logger.info(f"Accuracy: {accuracy:.4f}, Total FLOPs: {total_flops:.2e}")
    
    return baseline_results

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Calculate Static K=2 Baseline Metrics")
    parser.add_argument("--convergence", type=str, required=True, 
                        help="Path to convergence results CSV")
    parser.add_argument("--output", type=str, required=True, 
                        help="Path to output JSON file")
    
    args = parser.parse_args()
    
    try:
        calculate_static_k2_baseline(args.convergence, args.output)
    except Exception as e:
        logger.error(f"Error calculating baseline: {e}")
        raise

if __name__ == "__main__":
    main()
