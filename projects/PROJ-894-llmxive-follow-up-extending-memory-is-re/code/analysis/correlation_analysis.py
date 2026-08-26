import os
import json
import csv
import logging
import argparse
from pathlib import Path
from typing import List, Tuple, Optional
import numpy as np
from scipy import stats

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def ensure_output_dirs():
    """Ensure the output directory exists."""
    output_dir = Path("data/processed")
    output_dir.mkdir(parents=True, exist_ok=True)
    return output_dir

def load_results_from_csv(file_path: str) -> List[dict]:
    """Load results from a CSV file into a list of dictionaries."""
    results = []
    path = Path(file_path)
    if not path.exists():
        logger.warning(f"File not found: {file_path}")
        return results
    
    with open(path, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            results.append(row)
    return results

def calculate_point_biserial(nodes_visited: List[float], success: List[int]) -> Optional[Tuple[float, float]]:
    """
    Calculate the Point-Biserial correlation coefficient between continuous
    variable (nodes_visited) and binary variable (success: 1 for success, 0 for failure).
    
    Returns:
        Tuple of (correlation_coefficient, p_value) or None if calculation fails.
    """
    if len(nodes_visited) != len(success):
        logger.error("Input lists must have the same length.")
        return None
    
    if len(nodes_visited) < 2:
        logger.error("At least two data points are required for correlation.")
        return None
    
    # Ensure binary variable is strictly 0 or 1
    unique_vals = set(success)
    if not unique_vals.issubset({0, 1}):
        logger.error(f"Success variable must be binary (0 or 1). Found: {unique_vals}")
        return None
    
    if len(unique_vals) < 2:
        logger.error("Success variable must contain both 0s and 1s for correlation.")
        return None
    
    try:
        r_pb, p_value = stats.pointbiserialr(nodes_visited, success)
        return float(r_pb), float(p_value)
    except Exception as e:
        logger.error(f"Error calculating point-biserial correlation: {e}")
        return None

def process_results(baseline_results: List[dict], lazy_results: List[dict], greedy_results: List[dict]) -> dict:
    """
    Process all result files to calculate the point-biserial correlation
    between nodes_visited and reasoning success rate across all tasks.
    
    Reasoning success is determined by the 'status' field being 'COMPLETED'.
    """
    all_nodes_visited = []
    all_success = []

    # Process Baseline
    for row in baseline_results:
        try:
            nodes = float(row.get('nodes_visited', 0))
            status = row.get('status', '').upper()
            success = 1 if status == 'COMPLETED' else 0
            all_nodes_visited.append(nodes)
            all_success.append(success)
        except (ValueError, TypeError) as e:
            logger.warning(f"Skipping invalid baseline row: {e}")

    # Process Lazy
    for row in lazy_results:
        try:
            nodes = float(row.get('nodes_visited', 0))
            status = row.get('status', '').upper()
            success = 1 if status == 'COMPLETED' else 0
            all_nodes_visited.append(nodes)
            all_success.append(success)
        except (ValueError, TypeError) as e:
            logger.warning(f"Skipping invalid lazy row: {e}")

    # Process Greedy
    for row in greedy_results:
        try:
            nodes = float(row.get('nodes_visited', 0))
            status = row.get('status', '').upper()
            success = 1 if status == 'COMPLETED' else 0
            all_nodes_visited.append(nodes)
            all_success.append(success)
        except (ValueError, TypeError) as e:
            logger.warning(f"Skipping invalid greedy row: {e}")

    if not all_nodes_visited:
        logger.error("No valid data points found for correlation analysis.")
        return {
            "correlation_coefficient": None,
            "p_value": None,
            "sample_size": 0,
            "status": "FAILED_NO_DATA"
        }

    logger.info(f"Analyzing {len(all_nodes_visited)} data points.")
    
    result = calculate_point_biserial(all_nodes_visited, all_success)
    
    if result is None:
        return {
            "correlation_coefficient": None,
            "p_value": None,
            "sample_size": len(all_nodes_visited),
            "status": "FAILED_CALCULATION"
        }

    r_pb, p_val = result
    return {
        "correlation_coefficient": r_pb,
        "p_value": p_val,
        "sample_size": len(all_nodes_visited),
        "status": "SUCCESS",
        "interpretation": "Positive correlation indicates more nodes visited correlates with success." if r_pb > 0 else "Negative correlation indicates more nodes visited correlates with failure."
    }

def main():
    """Main entry point for the correlation analysis task."""
    parser = argparse.ArgumentParser(description="Calculate Point-Biserial Correlation")
    parser.add_argument("--baseline", type=str, default="data/processed/baseline_results.csv",
                        help="Path to baseline results CSV")
    parser.add_argument("--lazy", type=str, default="data/processed/lazy_results.csv",
                        help="Path to lazy results CSV")
    parser.add_argument("--greedy", type=str, default="data/processed/greedy_results.csv",
                        help="Path to greedy results CSV")
    parser.add_argument("--output", type=str, default="data/processed/correlation_results.json",
                        help="Path to output JSON file")
    args = parser.parse_args()

    logger.info(f"Loading data from {args.baseline}, {args.lazy}, {args.greedy}")
    
    baseline_data = load_results_from_csv(args.baseline)
    lazy_data = load_results_from_csv(args.lazy)
    greedy_data = load_results_from_csv(args.greedy)

    if not baseline_data and not lazy_data and not greedy_data:
        logger.error("No data loaded from any source. Exiting.")
        return 1

    results = process_results(baseline_data, lazy_data, greedy_data)
    
    output_dir = ensure_output_dirs()
    output_path = Path(args.output)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"Correlation results written to {output_path}")
    logger.info(f"Correlation Coefficient: {results['correlation_coefficient']}")
    logger.info(f"P-Value: {results['p_value']}")
    
    return 0

if __name__ == "__main__":
    exit(main())