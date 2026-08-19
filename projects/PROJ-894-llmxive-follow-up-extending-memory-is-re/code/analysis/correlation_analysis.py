"""
Point-Biserial Correlation Analysis (T025).

Calculates the Point-Biserial correlation coefficient between `nodes_visited`
(continuous variable) and reasoning success rate (binary variable: 1 for success, 0 for failure)
across all tasks from the baseline and heuristic results.

Output: data/processed/correlation_results.json
"""

import os
import json
import csv
import logging
import argparse
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
import numpy as np

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Define the result files to aggregate
RESULT_FILES = [
    "data/processed/baseline_results.csv",
    "data/processed/lazy_results.csv",
    "data/processed/greedy_results.csv",
    "data/processed/noisy_baseline_results.csv",
    "data/processed/noisy_lazy_results.csv",
    "data/processed/noisy_greedy_results.csv"
]

def load_results_from_csv(file_path: str) -> List[Dict[str, Any]]:
    """Load results from a CSV file."""
    results = []
    path = Path(file_path)
    if not path.exists():
        logger.warning(f"File not found: {file_path}, skipping.")
        return results

    with open(path, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Convert relevant fields to numeric types
            try:
                row['nodes_visited'] = int(row.get('nodes_visited', 0))
                # Accuracy is usually a float between 0 and 1
                acc_str = row.get('accuracy', '0.0')
                # Handle potential string formats like "0.95" or "95"
                if acc_str and acc_str != '':
                    if acc_str.endswith('%'):
                        acc_str = acc_str[:-1]
                    val = float(acc_str)
                    # Normalize if > 1 (assuming 0-100 scale)
                    if val > 1.0:
                        val = val / 100.0
                    row['accuracy'] = val
                else:
                    row['accuracy'] = 0.0
            except (ValueError, TypeError) as e:
                logger.warning(f"Skipping row due to parsing error: {row}, error: {e}")
                continue
            
            # Determine success: accuracy > 0.5 (or > 0 if strictly binary success)
            # Based on standard benchmarks, success is usually > 0.5 or exact match.
            # We'll define success as accuracy > 0.5 for this correlation.
            row['success'] = 1 if row['accuracy'] > 0.5 else 0
            results.append(row)

    return results

def calculate_point_biserial(x: np.ndarray, y: np.ndarray) -> Tuple[float, float]:
    """
    Calculate Point-Biserial correlation coefficient and p-value.
    
    x: Continuous variable (nodes_visited)
    y: Binary variable (success: 0 or 1)
    
    Returns: (r_pb, p_value)
    """
    if len(x) != len(y) or len(x) == 0:
        return np.nan, np.nan

    y = y.astype(int)
    n = len(x)
    n1 = np.sum(y)
    n0 = n - n1

    if n1 == 0 or n0 == 0:
        logger.warning("Binary variable has no variance (all 0s or all 1s). Cannot compute correlation.")
        return np.nan, np.nan

    # Mean of x for group 1 (success) and group 0 (failure)
    mean1 = np.mean(x[y == 1])
    mean0 = np.mean(x[y == 0])
    
    # Standard deviation of x
    std_x = np.std(x, ddof=1)
    
    if std_x == 0:
        logger.warning("Continuous variable has zero variance. Cannot compute correlation.")
        return np.nan, np.nan

    # Point-biserial formula: r_pb = (M1 - M0) / S_x * sqrt(p * q)
    # where p = n1/n, q = n0/n
    p = n1 / n
    q = n0 / n
    
    r_pb = (mean1 - mean0) / std_x * np.sqrt(p * q)

    # Calculate t-statistic for p-value
    # t = r_pb * sqrt((n - 2) / (1 - r_pb^2))
    if abs(r_pb) >= 1.0:
        # Perfect correlation or edge case
        t_stat = np.inf if r_pb > 0 else -np.inf
    else:
        t_stat = r_pb * np.sqrt((n - 2) / (1 - r_pb**2))

    # Two-tailed p-value using t-distribution
    # degrees of freedom = n - 2
    df = n - 2
    from scipy import stats
    p_value = 2 * (1 - stats.t.cdf(abs(t_stat), df))

    return r_pb, p_value

def main(args: Optional[argparse.Namespace] = None):
    if args is None:
        parser = argparse.ArgumentParser(description="Calculate Point-Biserial correlation.")
        parser.add_argument('--output', type=str, default="data/processed/correlation_results.json",
                            help='Output file path')
        parser.add_argument('--results-dir', type=str, default="data/processed",
                            help='Directory containing result CSVs')
        args = parser.parse_args()

    output_path = Path(args.output)
    results_dir = Path(args.results_dir)

    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Aggregate data from all result files
    all_nodes_visited = []
    all_success = []
    task_sources = []

    logger.info(f"Loading results from {len(RESULT_FILES)} files...")
    for file_rel_path in RESULT_FILES:
        # Adjust path relative to project root if needed
        file_path = results_dir / file_rel_path
        if not file_path.exists():
            # Try relative to current working directory
            file_path = Path(file_rel_path)
        
        if not file_path.exists():
            logger.warning(f"Skipping missing file: {file_rel_path}")
            continue

        rows = load_results_from_csv(str(file_path))
        for row in rows:
            all_nodes_visited.append(row['nodes_visited'])
            all_success.append(row['success'])
            task_sources.append(file_rel_path)

    if len(all_nodes_visited) == 0:
        logger.error("No valid data found in any result file. Aborting.")
        # Write empty result to indicate failure
        result_data = {
            "status": "failed",
            "reason": "No valid data found in result files.",
            "files_checked": RESULT_FILES
        }
        with open(output_path, 'w') as f:
            json.dump(result_data, f, indent=2)
        return

    logger.info(f"Loaded {len(all_nodes_visited)} data points.")

    # Convert to numpy arrays
    nodes_array = np.array(all_nodes_visited)
    success_array = np.array(all_success)

    # Calculate correlation
    r_pb, p_value = calculate_point_biserial(nodes_array, success_array)

    logger.info(f"Point-Biserial Correlation (r_pb): {r_pb}")
    logger.info(f"P-value: {p_value}")

    # Prepare output
    result_data = {
        "metric": "point_biserial_correlation",
        "description": "Correlation between nodes_visited and reasoning success (accuracy > 0.5)",
        "sample_size": int(len(nodes_array)),
        "nodes_visited_stats": {
            "mean": float(np.mean(nodes_array)),
            "std": float(np.std(nodes_array)),
            "min": float(np.min(nodes_array)),
            "max": float(np.max(nodes_array))
        },
        "success_rate": float(np.mean(success_array)),
        "correlation_coefficient": float(r_pb) if not np.isnan(r_pb) else None,
        "p_value": float(p_value) if not np.isnan(p_value) else None,
        "interpretation": "positive" if r_pb > 0 else "negative" if r_pb < 0 else "none",
        "files_analyzed": RESULT_FILES
    }

    with open(output_path, 'w') as f:
        json.dump(result_data, f, indent=2)

    logger.info(f"Results written to {output_path}")

if __name__ == "__main__":
    main()
