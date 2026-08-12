"""
Statistical Analysis for Noisy Data (T024b)

Performs paired t-test/Wilcoxon signed-rank test on accuracy distributions
of heuristics (Lazy, Greedy) vs Baseline on noisy data.

Inputs:
  - data/processed/noisy_baseline_results.csv
  - data/processed/noisy_lazy_results.csv
  - data/processed/noisy_greedy_results.csv

Output:
  - data/processed/noisy_stats_report.json
"""
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

def load_results_from_csv(file_path: str) -> List[Dict[str, Any]]:
    """Load results from a CSV file into a list of dictionaries."""
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Results file not found: {file_path}")
    
    results = []
    with open(path, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            results.append(row)
    return results

def extract_accuracies(results: List[Dict[str, Any]], key: str = 'accuracy') -> np.ndarray:
    """Extract accuracy values from results, filtering out non-numeric/NaN."""
    values = []
    for row in results:
        val = row.get(key)
        if val is None:
            continue
        try:
            # Handle potential string representations of numbers
            if isinstance(val, str):
                val = float(val)
            if np.isnan(val):
                continue
            values.append(float(val))
        except (ValueError, TypeError):
            logger.warning(f"Skipping non-numeric value for {key}: {val}")
            continue
    
    if len(values) == 0:
        logger.warning(f"No valid accuracy values found in {results[:1]}")
        return np.array([])
    
    return np.array(values)

def align_pairs(
    baseline_acc: np.ndarray, 
    heuristic_acc: np.ndarray, 
    baseline_ids: List[str], 
    heuristic_ids: List[str]
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Align baseline and heuristic accuracy arrays by task_id.
    Returns only pairs where both exist.
    """
    # Create mapping from id to accuracy
    baseline_map = {id_: acc for id_, acc in zip(baseline_ids, baseline_acc)}
    heuristic_map = {id_: acc for id_, acc in zip(heuristic_ids, heuristic_acc)}
    
    common_ids = set(baseline_map.keys()) & set(heuristic_map.keys())
    if not common_ids:
        logger.error("No common task IDs found between baseline and heuristic.")
        return np.array([]), np.array([])
    
    # Sort by ID to ensure consistent ordering
    sorted_ids = sorted(common_ids)
    
    paired_baseline = np.array([baseline_map[id_] for id_ in sorted_ids])
    paired_heuristic = np.array([heuristic_map[id_] for id_ in sorted_ids])
    
    logger.info(f"Aligned {len(paired_baseline)} task pairs.")
    return paired_baseline, paired_heuristic

def perform_statistical_tests(
    baseline: np.ndarray, 
    heuristic: np.ndarray, 
    name: str
) -> Dict[str, Any]:
    """
    Perform paired t-test and Wilcoxon signed-rank test.
    Returns a dictionary with test statistics and p-values.
    """
    if len(baseline) < 2 or len(heuristic) < 2:
        logger.warning(f"Insufficient data for {name} (n={len(baseline)}). Skipping tests.")
        return {
            "test_name": name,
            "n_samples": len(baseline),
            "t_statistic": None,
            "t_p_value": None,
            "wilcoxon_statistic": None,
            "wilcoxon_p_value": None,
            "mean_diff": None,
            "status": "skipped_insufficient_data"
        }
    
    mean_diff = float(np.mean(baseline - heuristic))
    
    # Paired t-test
    t_stat, t_p = stats.ttest_rel(baseline, heuristic)
    
    # Wilcoxon signed-rank test
    w_stat, w_p = stats.wilcoxon(baseline, heuristic)
    
    return {
        "test_name": name,
        "n_samples": len(baseline),
        "mean_baseline": float(np.mean(baseline)),
        "mean_heuristic": float(np.mean(heuristic)),
        "mean_diff": mean_diff,
        "t_statistic": float(t_stat),
        "t_p_value": float(t_p),
        "wilcoxon_statistic": float(w_stat),
        "wilcoxon_p_value": float(w_p),
        "status": "completed"
    }

def main():
    parser = argparse.ArgumentParser(description="Statistical analysis for noisy data strategies.")
    parser.add_argument(
        "--baseline", 
        type=str, 
        default="data/processed/noisy_baseline_results.csv",
        help="Path to noisy baseline results CSV."
    )
    parser.add_argument(
        "--lazy", 
        type=str, 
        default="data/processed/noisy_lazy_results.csv",
        help="Path to noisy lazy results CSV."
    )
    parser.add_argument(
        "--greedy", 
        type=str, 
        default="data/processed/noisy_greedy_results.csv",
        help="Path to noisy greedy results CSV."
    )
    parser.add_argument(
        "--output", 
        type=str, 
        default="data/processed/noisy_stats_report.json",
        help="Path to output JSON report."
    )
    args = parser.parse_args()
    
    logger.info("Starting statistical analysis for noisy data.")
    
    # Ensure output directory exists
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Load data
    try:
        baseline_results = load_results_from_csv(args.baseline)
        lazy_results = load_results_from_csv(args.lazy)
        greedy_results = load_results_from_csv(args.greedy)
    except FileNotFoundError as e:
        logger.error(f"Data loading failed: {e}")
        # Write an error report instead of crashing silently
        error_report = {
            "status": "failed",
            "error": str(e),
            "tests": []
        }
        with open(output_path, 'w') as f:
            json.dump(error_report, f, indent=2)
        return 1
    
    # Extract accuracies and IDs
    baseline_acc = extract_accuracies(baseline_results)
    baseline_ids = [r.get('task_id', '') for r in baseline_results]
    
    lazy_acc = extract_accuracies(lazy_results)
    lazy_ids = [r.get('task_id', '') for r in lazy_results]
    
    greedy_acc = extract_accuracies(greedy_results)
    greedy_ids = [r.get('task_id', '') for r in greedy_results]
    
    if len(baseline_acc) == 0:
        logger.error("No valid baseline data found. Cannot perform analysis.")
        return 1
    
    # Align and test Baseline vs Noisy Lazy
    lazy_aligned_b, lazy_aligned_h = align_pairs(baseline_acc, lazy_acc, baseline_ids, lazy_ids)
    lazy_stats = perform_statistical_tests(lazy_aligned_b, lazy_aligned_h, "Noisy_Baseline_vs_Lazy")
    
    # Align and test Baseline vs Noisy Greedy
    greedy_aligned_b, greedy_aligned_h = align_pairs(baseline_acc, greedy_acc, baseline_ids, greedy_ids)
    greedy_stats = perform_statistical_tests(greedy_aligned_b, greedy_aligned_h, "Noisy_Baseline_vs_Greedy")
    
    # Compile report
    report = {
        "status": "completed",
        "description": "Statistical analysis (paired t-test, Wilcoxon) on noisy data strategies.",
        "input_files": {
            "baseline": args.baseline,
            "lazy": args.lazy,
            "greedy": args.greedy
        },
        "tests": [lazy_stats, greedy_stats]
    }
    
    # Write report
    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2)
    
    logger.info(f"Statistical report written to {output_path}")
    return 0

if __name__ == "__main__":
    exit(main())