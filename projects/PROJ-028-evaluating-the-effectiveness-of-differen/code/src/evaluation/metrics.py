"""
Metrics module for evaluating code generation performance.

Implements pass@k calculation and aggregation logic as per FR-003.
Supports pass@1 and pass@10 calculations based on the number of generated
samples per task and their execution outcomes.
"""
import math
from typing import List, Dict, Any, Optional
from collections import defaultdict


def calculate_pass_k(n: int, c: int, k: int) -> float:
    """
    Calculate the pass@k metric for a single task.
    
    Formula: pass@k = 1 - (C(n-c, k) / C(n, k))
    
    Args:
        n: Total number of samples generated for the task.
        c: Number of correct samples (passed execution).
        k: The k value for pass@k (e.g., 1 or 10).
        
    Returns:
        The pass@k value as a float between 0.0 and 1.0.
        
    Raises:
        ValueError: If inputs are invalid (n < k, c < 0, etc.)
    """
    if n < k:
        raise ValueError(f"Total samples (n={n}) must be >= k={k}")
    if c < 0 or c > n:
        raise ValueError(f"Correct count (c={c}) must be between 0 and n={n}")
    if k <= 0:
        raise ValueError(f"k={k} must be positive")
    
    # If all samples are correct, pass@k is 1.0
    if c == n:
        return 1.0
    
    # If no samples are correct, pass@k is 0.0
    if c == 0:
        return 0.0
    
    # Calculate C(n, k) and C(n-c, k)
    # C(n, k) = n! / (k! * (n-k)!)
    # To avoid large factorials, use the product form:
    # C(n, k) = (n * (n-1) * ... * (n-k+1)) / k!
    
    # Probability that ALL k samples fail
    # P(all fail) = C(n-c, k) / C(n, k)
    
    # We calculate 1 - P(all fail)
    
    numerator = 1.0
    denominator = 1.0
    
    for i in range(k):
        numerator *= (n - c - i)
        denominator *= (n - i)
        
    if denominator == 0:
        return 0.0
        
    prob_all_fail = numerator / denominator
    return 1.0 - prob_all_fail


def calculate_pass_1(results: List[bool]) -> float:
    """
    Calculate pass@1 for a list of execution results.
    
    Args:
        results: List of boolean results (True = passed, False = failed).
                
    Returns:
        pass@1 value (1.0 if first sample passed, 0.0 otherwise).
    """
    if not results:
        return 0.0
    return 1.0 if results[0] else 0.0


def calculate_pass_10(results: List[bool]) -> float:
    """
    Calculate pass@10 for a list of execution results.
    
    Args:
        results: List of boolean results (True = passed, False = failed).
                
    Returns:
        pass@10 value calculated using the combinatorial formula.
    """
    if not results:
        return 0.0
    
    n = len(results)
    c = sum(1 for r in results if r)
    
    return calculate_pass_k(n, c, 10)


def aggregate_metrics(
    task_results: Dict[str, Dict[str, Any]],
    k_values: Optional[List[int]] = None
) -> Dict[str, Any]:
    """
    Aggregate pass@k metrics across multiple tasks.
    
    Args:
        task_results: Dictionary mapping task_id to result data.
                     Expected structure:
                     {
                         "task_id": {
                             "samples": [bool, bool, ...],
                             "pass@1": float,
                             "pass@10": float,
                             ...
                         }
                     }
        k_values: List of k values to calculate (default: [1, 10]).
                
    Returns:
        Dictionary containing aggregated metrics:
        {
            "mean_pass_1": float,
            "mean_pass_10": float,
            "std_pass_1": float,
            "std_pass_10": float,
            "task_count": int,
            "per_task_metrics": {task_id: {pass@k values}}
        }
    """
    if k_values is None:
        k_values = [1, 10]
        
    if not task_results:
        return {
            "mean_pass_1": 0.0,
            "mean_pass_10": 0.0,
            "std_pass_1": 0.0,
            "std_pass_10": 0.0,
            "task_count": 0,
            "per_task_metrics": {}
        }
    
    per_task_metrics = {}
    aggregated_values = {k: [] for k in k_values}
    
    for task_id, data in task_results.items():
        samples = data.get("samples", [])
        if not samples:
            continue
            
        task_metrics = {}
        for k in k_values:
            try:
                pass_k = calculate_pass_k(len(samples), sum(samples), k)
                task_metrics[f"pass@{k}"] = pass_k
                aggregated_values[k].append(pass_k)
            except ValueError:
                task_metrics[f"pass@{k}"] = 0.0
                aggregated_values[k].append(0.0)
                
        per_task_metrics[task_id] = task_metrics
    
    # Calculate mean and std for each k
    result = {
        "task_count": len(per_task_metrics),
        "per_task_metrics": per_task_metrics
    }
    
    for k in k_values:
        values = aggregated_values[k]
        if values:
            mean_val = sum(values) / len(values)
            variance = sum((x - mean_val) ** 2 for x in values) / len(values)
            std_val = math.sqrt(variance)
        else:
            mean_val = 0.0
            std_val = 0.0
            
        result[f"mean_pass_{k}"] = mean_val
        result[f"std_pass_{k}"] = std_val
        
    return result


def compute_task_metrics(
    samples: List[bool],
    k_values: Optional[List[int]] = None
) -> Dict[str, float]:
    """
    Compute pass@k metrics for a single task's samples.
    
    Args:
        samples: List of boolean execution results.
        k_values: List of k values to compute (default: [1, 10]).
                
    Returns:
        Dictionary mapping "pass@k" to computed value.
    """
    if k_values is None:
        k_values = [1, 10]
        
    if not samples:
        return {f"pass@{k}": 0.0 for k in k_values}
        
    n = len(samples)
    c = sum(samples)
    
    return {
        f"pass@{k}": calculate_pass_k(n, c, k)
        for k in k_values
    }