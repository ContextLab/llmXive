import json
import csv
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
import numpy as np
from scipy import stats as scipy_stats
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def load_results_from_csv(file_path: str) -> List[Dict[str, Any]]:
    """Load results from a CSV file into a list of dictionaries."""
    results = []
    try:
        with open(file_path, 'r', newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                # Convert numeric strings to floats/integers where appropriate
                cleaned_row = {}
                for k, v in row.items():
                    if k in ['accuracy', 'latency_ms', 'evidence_threshold']:
                        try:
                            cleaned_row[k] = float(v)
                        except (ValueError, TypeError):
                            cleaned_row[k] = None
                    elif k in ['nodes_visited']:
                        try:
                            cleaned_row[k] = int(v)
                        except (ValueError, TypeError):
                            cleaned_row[k] = 0
                    else:
                        cleaned_row[k] = v
                results.append(cleaned_row)
    except FileNotFoundError:
        logger.error(f"File not found: {file_path}")
        return []
    except Exception as e:
        logger.error(f"Error reading {file_path}: {e}")
        return []
    return results

def count_timeout_tasks(results: List[Dict[str, Any]]) -> int:
    """Count tasks that timed out (marked with a specific flag or missing accuracy)."""
    count = 0
    for r in results:
        if r.get('accuracy') is None or r.get('status') == 'TIMEOUT':
            count += 1
    return count

def count_completed_tasks(results: List[Dict[str, Any]]) -> int:
    """Count tasks that completed successfully."""
    count = 0
    for r in results:
        if r.get('accuracy') is not None and r.get('status') != 'TIMEOUT':
            count += 1
    return count

def aggregate_timeout_stats(results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Aggregate statistics about timeouts."""
    total = len(results)
    timeouts = count_timeout_tasks(results)
    completed = count_completed_tasks(results)
    return {
        "total_tasks": total,
        "timeouts": timeouts,
        "completed": completed,
        "timeout_rate": timeouts / total if total > 0 else 0.0
    }

def save_stats_report(stats: Dict[str, Any], output_path: str) -> None:
    """Save statistics report to a JSON file."""
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(stats, f, indent=2)
    logger.info(f"Stats report saved to {output_path}")

def run_ttest_clean(baseline_results: List[Dict[str, Any]], 
                    heuristic_results: List[Dict[str, Any]], 
                    strategy_name: str) -> Dict[str, Any]:
    """Perform statistical comparison on clean data."""
    # Align by task_id if possible, or just compare distributions if IDs don't match
    # For simplicity, assuming distributions are comparable or paired by index if same length
    if len(baseline_results) != len(heuristic_results):
        logger.warning("Baseline and heuristic result counts differ. Using independent test.")
        baseline_acc = [r['accuracy'] for r in baseline_results if r.get('accuracy') is not None]
        heuristic_acc = [r['accuracy'] for r in heuristic_results if r.get('accuracy') is not None]
        if not baseline_acc or not heuristic_acc:
            return {"error": "Insufficient data for t-test"}
        t_stat, p_val = scipy_stats.ttest_ind(baseline_acc, heuristic_acc)
        return {
            "strategy": strategy_name,
            "test_type": "independent_ttest",
            "t_statistic": float(t_stat),
            "p_value": float(p_val),
            "baseline_mean": float(np.mean(baseline_acc)),
            "heuristic_mean": float(np.mean(heuristic_acc))
        }
    
    # Paired test
    baseline_acc = [r['accuracy'] for r in baseline_results if r.get('accuracy') is not None]
    heuristic_acc = [r['accuracy'] for r in heuristic_results if r.get('accuracy') is not None]
    
    if len(baseline_acc) != len(heuristic_acc):
        # Truncate to shortest
        min_len = min(len(baseline_acc), len(heuristic_acc))
        baseline_acc = baseline_acc[:min_len]
        heuristic_acc = heuristic_acc[:min_len]

    if len(baseline_acc) < 2:
        return {"error": "Insufficient data for paired t-test"}

    t_stat, p_val = scipy_stats.ttest_rel(baseline_acc, heuristic_acc)
    return {
        "strategy": strategy_name,
        "test_type": "paired_ttest",
        "t_statistic": float(t_stat),
        "p_value": float(p_val),
        "baseline_mean": float(np.mean(baseline_acc)),
        "heuristic_mean": float(np.mean(heuristic_acc))
    }

def run_ttest_noisy(baseline_results: List[Dict[str, Any]], 
                    heuristic_results: List[Dict[str, Any]], 
                    strategy_name: str) -> Dict[str, Any]:
    """Perform statistical comparison on noisy data."""
    return run_ttest_clean(baseline_results, heuristic_results, strategy_name)

def calc_point_biserial(nodes_visited: List[float], success_rates: List[float]) -> Dict[str, float]:
    """
    Calculate the Point-Biserial correlation coefficient between nodes_visited and reasoning success.
    
    The Point-Biserial correlation is used when one variable is continuous (nodes_visited)
    and the other is binary (success/failure). Here, 'success_rates' is treated as the binary
    outcome (1 for success, 0 for failure) or a proportion if aggregated.
    
    If 'success_rates' contains values between 0 and 1, it represents a proportion of success.
    If it contains 0.0 and 1.0, it represents binary outcomes.
    
    Args:
        nodes_visited: List of continuous values (number of nodes visited).
        success_rates: List of binary (0.0/1.0) or proportional success values.
    
    Returns:
        Dictionary containing correlation coefficient, p-value, and sample size.
    """
    if len(nodes_visited) != len(success_rates):
        raise ValueError("nodes_visited and success_rates must have the same length")
    
    if len(nodes_visited) < 2:
        raise ValueError("At least two data points are required for correlation")
    
    # Convert success_rates to binary if they are proportions (e.g., 0.8 -> 1, 0.2 -> 0)
    # Or treat them as continuous if they are strictly 0.0 or 1.0
    # For Point-Biserial, the second variable must be truly dichotomous.
    # We will treat any value >= 0.5 as 1 (success) and < 0.5 as 0 (failure) to ensure binary input.
    binary_success = [1.0 if x >= 0.5 else 0.0 for x in success_rates]
    
    # Check if we have both 0s and 1s
    if len(set(binary_success)) < 2:
        logger.warning("Success rates are not dichotomous (all 0s or all 1s). Correlation cannot be computed.")
        return {
            "correlation": 0.0,
            "p_value": 1.0,
            "n": len(nodes_visited),
            "note": "Binary variable is constant"
        }

    # Use scipy.stats.pointbiserialr
    # Note: scipy.stats.pointbiserialr expects the binary variable to be the second argument
    r, p_value = scipy_stats.pointbiserialr(binary_success, nodes_visited)
    
    return {
        "correlation": float(r),
        "p_value": float(p_value),
        "n": len(nodes_visited),
        "interpretation": "Positive correlation implies more nodes visited correlates with success" if r > 0 else "Negative correlation implies fewer nodes visited correlates with success"
    }

def main():
    """Main entry point for statistical analysis."""
    parser = argparse.ArgumentParser(description="Run statistical analysis on LLM agent results.")
    parser.add_argument("--baseline", type=str, required=True, help="Path to baseline results CSV")
    parser.add_argument("--lazy", type=str, required=True, help="Path to lazy results CSV")
    parser.add_argument("--greedy", type=str, required=True, help="Path to greedy results CSV")
    parser.add_argument("--output", type=str, required=True, help="Path to output JSON report")
    args = parser.parse_args()

    logger.info("Loading results...")
    baseline_data = load_results_from_csv(args.baseline)
    lazy_data = load_results_from_csv(args.lazy)
    greedy_data = load_results_from_csv(args.greedy)

    if not baseline_data:
        logger.error("No baseline data found. Exiting.")
        return

    # Run t-tests
    stats_report = {
        "clean": {
            "lazy_vs_baseline": run_ttest_clean(baseline_data, lazy_data, "Lazy"),
            "greedy_vs_baseline": run_ttest_clean(baseline_data, greedy_data, "Greedy")
        }
    }

    # Calculate Point-Biserial Correlation
    # We need to determine 'success' for each task. 
    # Assuming 'accuracy' > 0.5 counts as success (1), else failure (0).
    # We align by task_id if available, otherwise by index.
    # For this implementation, we assume the CSVs are aligned by task_id and sorted identically,
    # or we process the baseline data as the primary source of truth for task IDs.
    
    # Extract nodes_visited and success (binary) from baseline results
    # If other strategies are needed, we can aggregate, but the task asks for correlation across tasks.
    # Let's use the baseline data for the correlation as it represents the "Full" strategy.
    
    nodes_list = []
    success_list = []
    
    for row in baseline_data:
        if row.get('accuracy') is not None:
            nodes_list.append(row['nodes_visited'])
            # Success if accuracy > 0.5 (or any threshold, here 0.5 is standard for binary)
            success_list.append(1.0 if row['accuracy'] > 0.5 else 0.0)
    
    if nodes_list:
        try:
            pb_result = calc_point_biserial(nodes_list, success_list)
            stats_report["point_biserial"] = pb_result
        except ValueError as e:
            logger.warning(f"Could not calculate Point-Biserial: {e}")
            stats_report["point_biserial"] = {"error": str(e)}
    else:
        logger.warning("No valid data points for Point-Biserial correlation.")
        stats_report["point_biserial"] = {"error": "No valid data points"}

    save_stats_report(stats_report, args.output)
    logger.info(f"Statistical analysis complete. Report saved to {args.output}")

if __name__ == "__main__":
    main()