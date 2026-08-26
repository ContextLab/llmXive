"""
Point-Biserial Correlation Analysis Module.

Calculates the Point-Biserial correlation coefficient between 'nodes_visited'
and reasoning success rate (binary success/failure) across all tasks.

Input: Reads results from multiple CSV files (baseline, lazy, greedy).
Output: Writes correlation results to data/processed/correlation_results.json.
"""
import os
import json
import csv
import logging
import argparse
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any
import numpy as np
from scipy import stats

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Define expected output path
OUTPUT_PATH = Path("data/processed/correlation_results.json")

def load_results_from_csv(file_path: str) -> List[Dict[str, Any]]:
    """
    Load results from a CSV file and return a list of dictionaries.

    Args:
        file_path: Path to the CSV file.

    Returns:
        List of dictionaries containing task results.
    """
    results = []
    path = Path(file_path)
    if not path.exists():
        logger.warning(f"File not found: {file_path}")
        return results

    with open(path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                # Parse numeric fields
                task = {
                    'task_id': row.get('task_id', ''),
                    'nodes_visited': float(row.get('nodes_visited', 0)),
                    'status': row.get('status', ''),
                    'accuracy': float(row.get('accuracy', 0)) if row.get('accuracy') not in (None, '') else 0.0
                }
                results.append(task)
            except ValueError as e:
                logger.warning(f"Skipping row due to parsing error: {e}")
                continue
    return results

def calculate_point_biserial(nodes_visited: List[float], success: List[int]) -> Tuple[float, float]:
    """
    Calculate the Point-Biserial correlation coefficient (r_pb) and p-value.

    The Point-Biserial correlation measures the relationship between a continuous
    variable (nodes_visited) and a binary variable (success: 1 if successful, 0 otherwise).

    Formula:
      r_pb = (M1 - M0) / S_n * sqrt(n1 * n0 / n^2)
      where:
        M1 = mean of continuous variable for group 1 (success)
        M0 = mean of continuous variable for group 0 (failure)
        S_n = standard deviation of the continuous variable for the whole group
        n1 = number of observations in group 1
        n0 = number of observations in group 0
        n = total number of observations

    Args:
        nodes_visited: List of continuous values (nodes visited).
        success: List of binary values (1 for success, 0 for failure).

    Returns:
        Tuple of (correlation_coefficient, p_value).
    """
    if len(nodes_visited) != len(success):
        raise ValueError("Input lists must have the same length.")

    if len(nodes_visited) < 2:
        logger.warning("Insufficient data points for correlation analysis.")
        return 0.0, 1.0

    n = len(nodes_visited)
    n1 = sum(success)
    n0 = n - n1

    if n1 == 0 or n0 == 0:
        logger.warning("One of the groups is empty. Cannot calculate correlation.")
        return 0.0, 1.0

    nodes_arr = np.array(nodes_visited, dtype=float)
    success_arr = np.array(success, dtype=float)

    # Calculate means for each group
    M1 = np.mean(nodes_arr[success_arr == 1])
    M0 = np.mean(nodes_arr[success_arr == 0])

    # Calculate standard deviation of the continuous variable (population std dev)
    S_n = np.std(nodes_arr, ddof=0)

    if S_n == 0:
        logger.warning("Standard deviation is zero. Cannot calculate correlation.")
        return 0.0, 1.0

    # Calculate r_pb
    r_pb = (M1 - M0) / S_n * np.sqrt((n1 * n0) / (n * n))

    # Calculate p-value using t-test approximation
    # t = r * sqrt((n-2) / (1-r^2))
    if abs(r_pb) >= 1.0:
        # Perfect correlation, p-value is effectively 0 (or undefined if n=2)
        p_value = 0.0 if n > 2 else 1.0
    else:
        t_stat = r_pb * np.sqrt((n - 2) / (1 - r_pb**2))
        # Two-tailed p-value from t-distribution with n-2 degrees of freedom
        from scipy.stats import t
        p_value = 2 * (1 - t.cdf(abs(t_stat), df=n - 2))

    return float(r_pb), float(p_value)

def main():
    """
    Main function to run the Point-Biserial correlation analysis.
    """
    logger.info("Starting Point-Biserial Correlation Analysis...")

    # Define input files
    input_files = [
        "data/processed/baseline_results.csv",
        "data/processed/lazy_results.csv",
        "data/processed/greedy_results.csv",
        "data/processed/noisy_baseline_results.csv"
    ]

    # Aggregate all results
    all_results = []
    for file_path in input_files:
        if os.path.exists(file_path):
            logger.info(f"Loading results from {file_path}")
            results = load_results_from_csv(file_path)
            all_results.extend(results)
        else:
            logger.warning(f"Input file not found: {file_path}")

    if not all_results:
        logger.error("No valid data found in any input files. Aborting analysis.")
        # Ensure output directory exists even if empty
        OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(OUTPUT_PATH, 'w', encoding='utf-8') as f:
            json.dump({
                "status": "failed",
                "reason": "No input data found",
                "correlation_coefficient": None,
                "p_value": None,
                "sample_size": 0
            }, f, indent=2)
        return

    logger.info(f"Aggregated {len(all_results)} results from all input files.")

    # Prepare data for correlation
    nodes_visited = []
    success = []

    for task in all_results:
        # Determine success: accuracy > 0 (or > threshold if specified)
        # Assuming a task is successful if accuracy > 0
        is_success = 1 if task['accuracy'] > 0 else 0
        nodes_visited.append(task['nodes_visited'])
        success.append(is_success)

    # Calculate correlation
    try:
        r_pb, p_value = calculate_point_biserial(nodes_visited, success)
    except Exception as e:
        logger.error(f"Error calculating correlation: {e}")
        OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(OUTPUT_PATH, 'w', encoding='utf-8') as f:
            json.dump({
                "status": "failed",
                "reason": str(e),
                "correlation_coefficient": None,
                "p_value": None,
                "sample_size": len(all_results)
            }, f, indent=2)
        return

    # Prepare output
    result_data = {
        "status": "completed",
        "correlation_coefficient": r_pb,
        "p_value": p_value,
        "sample_size": len(all_results),
        "description": "Point-Biserial correlation between nodes_visited and success rate (accuracy > 0)",
        "interpretation": "Positive r_pb indicates that tasks requiring more nodes visited tend to be more successful.",
        "significant_at_0_05": p_value < 0.05
    }

    # Write output
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_PATH, 'w', encoding='utf-8') as f:
        json.dump(result_data, f, indent=2)

    logger.info(f"Correlation analysis complete. Results written to {OUTPUT_PATH}")
    logger.info(f"Correlation Coefficient (r_pb): {r_pb:.4f}")
    logger.info(f"P-value: {p_value:.4f}")
    logger.info(f"Significant at 0.05: {result_data['significant_at_0_05']}")

if __name__ == "__main__":
    main()