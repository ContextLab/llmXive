import json
import csv
import logging
import argparse
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any
import numpy as np
from scipy import stats

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def load_results_from_csv(filepath: str) -> List[Dict[str, Any]]:
    """Load results from a CSV file into a list of dictionaries."""
    results = []
    try:
        with open(filepath, 'r', newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                results.append(row)
    except FileNotFoundError:
        logger.error(f"File not found: {filepath}")
        raise
    return results

def extract_accuracies(results: List[Dict[str, Any]]) -> List[float]:
    """Extract accuracy values from results list, handling string-to-float conversion."""
    accuracies = []
    for row in results:
        try:
            acc = float(row.get('accuracy', 0))
            accuracies.append(acc)
        except (ValueError, TypeError):
            logger.warning(f"Invalid accuracy value in row: {row}")
            continue
    return accuracies

def align_pairs(baseline_results: List[Dict[str, Any]], 
                heuristic_results: List[Dict[str, Any]]) -> Tuple[List[float], List[float]]:
    """
    Align baseline and heuristic results by task_id.
    Returns two lists of accuracies: (baseline_accuracies, heuristic_accuracies)
    """
    baseline_map = {row['task_id']: float(row['accuracy']) for row in baseline_results}
    heuristic_map = {row['task_id']: float(row['accuracy']) for row in heuristic_results}
    
    common_ids = sorted(set(baseline_map.keys()) & set(heuristic_map.keys()))
    
    if not common_ids:
        logger.warning("No common task_ids found between baseline and heuristic results.")
        return [], []
    
    baseline_acc = [baseline_map[tid] for tid in common_ids]
    heuristic_acc = [heuristic_map[tid] for tid in common_ids]
    
    return baseline_acc, heuristic_acc

def perform_statistical_tests(baseline_acc: List[float], 
                              heuristic_acc: List[float], 
                              test_name: str = "t-test") -> Dict[str, Any]:
    """
    Perform paired t-test or Wilcoxon signed-rank test.
    Returns a dictionary with test results.
    """
    if len(baseline_acc) != len(heuristic_acc) or len(baseline_acc) < 2:
        logger.error("Insufficient data for statistical testing.")
        return {"error": "Insufficient data", "n": len(baseline_acc)}
    
    result = {}
    try:
        if test_name == "t-test":
            statistic, p_value = stats.ttest_rel(baseline_acc, heuristic_acc)
            result = {
                "test": "Paired t-test",
                "statistic": float(statistic),
                "p_value": float(p_value),
                "n": len(baseline_acc),
                "mean_baseline": float(np.mean(baseline_acc)),
                "mean_heuristic": float(np.mean(heuristic_acc)),
                "std_baseline": float(np.std(baseline_acc)),
                "std_heuristic": float(np.std(heuristic_acc))
            }
        elif test_name == "wilcoxon":
            statistic, p_value = stats.wilcoxon(baseline_acc, heuristic_acc)
            result = {
                "test": "Wilcoxon signed-rank test",
                "statistic": float(statistic),
                "p_value": float(p_value),
                "n": len(baseline_acc),
                "mean_baseline": float(np.mean(baseline_acc)),
                "mean_heuristic": float(np.mean(heuristic_acc))
            }
        else:
            logger.error(f"Unknown test type: {test_name}")
            return {"error": "Unknown test type"}
    except Exception as e:
        logger.error(f"Statistical test failed: {e}")
        return {"error": str(e)}
    
    return result

def main():
    parser = argparse.ArgumentParser(description="Statistical Analysis for Noisy Data")
    parser.add_argument("--baseline", type=str, required=True, 
                        help="Path to baseline noisy results CSV (e.g., data/processed/noisy_baseline_results.csv)")
    parser.add_argument("--lazy", type=str, required=True, 
                        help="Path to lazy noisy results CSV (e.g., data/processed/noisy_lazy_results.csv)")
    parser.add_argument("--greedy", type=str, required=True, 
                        help="Path to greedy noisy results CSV (e.g., data/processed/noisy_greedy_results.csv)")
    parser.add_argument("--output", type=str, default="data/processed/noisy_statistical_results.json",
                        help="Output JSON file path")
    parser.add_argument("--test", type=str, default="t-test", choices=["t-test", "wilcoxon"],
                        help="Statistical test to perform")
    
    args = parser.parse_args()
    
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    logger.info(f"Loading baseline results from {args.baseline}")
    baseline_results = load_results_from_csv(args.baseline)
    
    logger.info(f"Loading lazy results from {args.lazy}")
    lazy_results = load_results_from_csv(args.lazy)
    
    logger.info(f"Loading greedy results from {args.greedy}")
    greedy_results = load_results_from_csv(args.greedy)
    
    all_tests = {}
    
    # Baseline vs Noisy Lazy
    logger.info("Aligning Baseline vs Noisy Lazy...")
    b_acc, l_acc = align_pairs(baseline_results, lazy_results)
    if b_acc:
        logger.info(f"Found {len(b_acc)} aligned pairs for Baseline vs Noisy Lazy.")
        all_tests["baseline_vs_noisy_lazy"] = perform_statistical_tests(b_acc, l_acc, args.test)
    else:
        logger.warning("Skipping Baseline vs Noisy Lazy due to no aligned pairs.")
        all_tests["baseline_vs_noisy_lazy"] = {"error": "No aligned pairs"}
    
    # Baseline vs Noisy Greedy
    logger.info("Aligning Baseline vs Noisy Greedy...")
    b_acc, g_acc = align_pairs(baseline_results, greedy_results)
    if b_acc:
        logger.info(f"Found {len(b_acc)} aligned pairs for Baseline vs Noisy Greedy.")
        all_tests["baseline_vs_noisy_greedy"] = perform_statistical_tests(b_acc, g_acc, args.test)
    else:
        logger.warning("Skipping Baseline vs Noisy Greedy due to no aligned pairs.")
        all_tests["baseline_vs_noisy_greedy"] = {"error": "No aligned pairs"}
    
    # Summary
    summary = {
        "test_type": args.test,
        "comparisons": all_tests,
        "status": "completed"
    }
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(summary, f, indent=2)
    
    logger.info(f"Statistical analysis complete. Results saved to {output_path}")
    print(f"Results written to {output_path}")

if __name__ == "__main__":
    main()