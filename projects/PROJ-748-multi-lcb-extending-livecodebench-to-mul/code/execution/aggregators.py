"""
Pass@k aggregation logic for Multi-LCB benchmark.

Computes mean and standard deviation for Pass@1, Pass@5, and Pass@10
across tasks, grouped by language, model, and temperature.
"""

import json
import logging
import math
import sys
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any

from config import get_config, get_results_path, get_logs_path
from execution.runner import RunResult

logger = logging.getLogger(__name__)


def compute_pass_k_for_task(
    results: List[RunResult],
    k: int
) -> float:
    """
    Compute Pass@k for a single task given a list of RunResult objects.

    Pass@k is defined as: 1 - (C(n-c, k) / C(n, k))
    where:
      n = total number of samples (runs)
      c = number of correct samples
      k = the k in Pass@k

    If n < k, we cannot compute Pass@k, so we return 0.0 or handle as needed.
    In this implementation, if n < k, we assume the task was not run enough
    times to evaluate Pass@k and return 0.0.

    Args:
        results: List of RunResult objects for a single task.
        k: The k value for Pass@k.

    Returns:
        Pass@k value between 0.0 and 1.0.
    """
    n = len(results)
    if n < k:
        # Not enough runs to compute Pass@k
        logger.warning(f"Not enough runs ({n}) to compute Pass@{k}. Returning 0.0.")
        return 0.0

    c = sum(1 for r in results if r.status == "pass")

    if c == 0:
        return 0.0
    if c >= k:
        return 1.0

    # Compute C(n-c, k) / C(n, k)
    # C(n, k) = n! / (k! * (n-k)!)
    # Ratio = (n-c)! * (n-k)! / ((n-c-k)! * n!)
    # We compute this using logarithms to avoid overflow for large n

    def log_combination(n_val: int, k_val: int) -> float:
        """Compute log(C(n, k)) using log-gamma."""
        if k_val < 0 or k_val > n_val:
            return float('-inf')
        if k_val == 0 or k_val == n_val:
            return 0.0
        # Use log-gamma: log(n!) = gammaln(n+1)
        from math import lgamma
        return lgamma(n_val + 1) - lgamma(k_val + 1) - lgamma(n_val - k_val + 1)

    log_num = log_combination(n - c, k)
    log_den = log_combination(n, k)

    if log_den == float('-inf'):
        return 0.0

    ratio = math.exp(log_num - log_den)
    pass_k = 1.0 - ratio
    return max(0.0, min(1.0, pass_k))


def aggregate_pass_k_by_group(
    execution_log_path: str,
    k_values: Optional[List[int]] = None
) -> Dict[str, Dict[str, Dict[str, Dict[str, float]]]]:
    """
    Aggregate Pass@k metrics from an execution log.

    Groups results by language, model, and temperature, then computes
    mean and standard deviation of Pass@k across tasks.

    Args:
        execution_log_path: Path to the execution_log.json file.
        k_values: List of k values to compute (default: [1, 5, 10]).

    Returns:
        Nested dictionary:
        {
            "language": {
                "model": {
                    "temperature": {
                        "pass_1": {"mean": float, "std": float},
                        "pass_5": {"mean": float, "std": float},
                        ...
                    }
                }
            }
        }
    """
    if k_values is None:
        k_values = [1, 5, 10]

    # Load execution log
    with open(execution_log_path, 'r') as f:
        execution_log = json.load(f)

    # Structure to hold Pass@k values for each group
    # group_key -> task_id -> pass_k_value
    groups: Dict[str, Dict[str, float]] = defaultdict(dict)

    for entry in execution_log:
        task_id = entry.get("task_id")
        language = entry.get("language")
        model = entry.get("model")
        temperature = entry.get("temperature")
        runs = entry.get("runs", [])

        if not runs or not task_id or not language or not model or temperature is None:
            continue

        # Convert temperature to string for consistent grouping
        temp_str = str(temperature)

        # Group key
        group_key = (language, model, temp_str)

        # Compute Pass@k for each k value
        pass_k_values = {}
        for k in k_values:
            pass_k = compute_pass_k_for_task(runs, k)
            pass_k_values[k] = pass_k

        # Store in groups
        for k in k_values:
            if group_key not in groups:
                groups[group_key] = {}
            if task_id not in groups[group_key]:
                groups[group_key][task_id] = {}
            groups[group_key][task_id][k] = pass_k_values[k]

    # Aggregate statistics
    aggregated: Dict[str, Dict[str, Dict[str, Dict[str, Dict[str, float]]]]] = defaultdict(
        lambda: defaultdict(lambda: defaultdict(dict))
    )

    for (language, model, temp_str), task_data in groups.items():
        for k in k_values:
            values = [task_data[task_id][k] for task_id in task_data]

            if not values:
                mean_val = 0.0
                std_val = 0.0
            else:
                mean_val = sum(values) / len(values)
                if len(values) > 1:
                    variance = sum((x - mean_val) ** 2 for x in values) / (len(values) - 1)
                    std_val = math.sqrt(variance)
                else:
                    std_val = 0.0

            pass_k_key = f"pass_{k}"
            aggregated[language][model][temp_str][pass_k_key] = {
                "mean": round(mean_val, 6),
                "std": round(std_val, 6),
                "n_tasks": len(values)
            }

    return aggregated


def save_aggregation_results(
    aggregated_results: Dict[str, Dict[str, Dict[str, Dict[str, Dict[str, float]]]]],
    output_path: Optional[str] = None
) -> str:
    """
    Save aggregated Pass@k results to a JSON file.

    Args:
        aggregated_results: The aggregated results dictionary.
        output_path: Optional path to save the results. If None, uses default path.

    Returns:
        Path to the saved file.
    """
    if output_path is None:
        results_path = get_results_path()
        output_path = str(results_path / "aggregation_results.json")

    Path(output_path).parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w') as f:
        json.dump(aggregated_results, f, indent=2)

    logger.info(f"Aggregation results saved to {output_path}")
    return output_path


def main():
    """Main entry point for Pass@k aggregation."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    config = get_config()
    execution_log_path = str(get_results_path() / "execution_log.json")

    if not Path(execution_log_path).exists():
        logger.error(f"Execution log not found at {execution_log_path}")
        sys.exit(1)

    logger.info(f"Loading execution log from {execution_log_path}")

    aggregated = aggregate_pass_k_by_group(execution_log_path)

    output_path = save_aggregation_results(aggregated)

    # Print summary
    logger.info("Aggregation Summary:")
    for language, models in aggregated.items():
        logger.info(f"  Language: {language}")
        for model, temps in models.items():
            logger.info(f"    Model: {model}")
            for temp, metrics in temps.items():
                logger.info(f"      Temperature: {temp}")
                for metric, stats in metrics.items():
                    logger.info(f"        {metric}: mean={stats['mean']:.4f}, std={stats['std']:.4f}, n={stats['n_tasks']}")

    return aggregated


if __name__ == "__main__":
    main()