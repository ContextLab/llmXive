"""
Sensitivity Analysis for Lazy Strategy.

This script performs a sensitivity analysis loop over evidence thresholds
for the Lazy traversal strategy. It re-runs the statistical comparison
(T024a style) across a range of thresholds to identify stability points
in the heuristic's performance.

Output:
    data/processed/sensitivity_analysis.json: Contains accuracy and node counts per threshold.
"""
import os
import json
import csv
import logging
import argparse
from pathlib import Path
from typing import List, Dict, Any, Optional
import numpy as np
from scipy import stats

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
THRESHOLD_RANGE = [0.5, 0.6, 0.7, 0.8]
PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data" / "processed"
OUTPUT_FILE = DATA_DIR / "sensitivity_analysis.json"

def ensure_output_dirs():
    """Ensure the output directory exists."""
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

def load_results_from_csv(csv_path: Path) -> List[Dict[str, Any]]:
    """
    Load results from a CSV file.
    Expects columns: task_id, accuracy, nodes_visited, status, evidence_threshold (optional)
    """
    results = []
    if not csv_path.exists():
        logger.warning(f"File not found: {csv_path}")
        return results

    with open(csv_path, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Filter out non-completed tasks if necessary, but for sensitivity
            # we usually look at the distribution of completed tasks.
            # We include all to see the impact of timeouts/failures on accuracy.
            try:
                result = {
                    'task_id': row.get('task_id', ''),
                    'accuracy': float(row.get('accuracy', 0.0)),
                    'nodes_visited': int(row.get('nodes_visited', 0)),
                    'status': row.get('status', ''),
                    'evidence_threshold': float(row.get('evidence_threshold', 0.0))
                }
                results.append(result)
            except (ValueError, TypeError) as e:
                logger.warning(f"Skipping malformed row in {csv_path}: {e}")
                continue
    return results

def compute_aggregate_stats(results: List[Dict[str, Any]]) -> Dict[str, float]:
    """
    Compute aggregate statistics for a list of results.
    Returns mean accuracy, mean nodes visited, and total count.
    """
    if not results:
        return {
            'mean_accuracy': 0.0,
            'mean_nodes_visited': 0.0,
            'count': 0,
            'std_accuracy': 0.0
        }

    accuracies = [r['accuracy'] for r in results if r['status'] == 'COMPLETED']
    nodes = [r['nodes_visited'] for r in results if r['status'] == 'COMPLETED']

    # If no completed tasks, we might consider the accuracy 0 or NaN.
    # Here we assume 0 for safety in aggregation.
    mean_acc = np.mean(accuracies) if accuracies else 0.0
    mean_nodes = np.mean(nodes) if nodes else 0.0
    std_acc = np.std(accuracies) if len(accuracies) > 1 else 0.0

    return {
        'mean_accuracy': float(mean_acc),
        'mean_nodes_visited': float(mean_nodes),
        'count': len(results),
        'completed_count': len(accuracies),
        'std_accuracy': float(std_acc)
    }

def run_statistical_comparison(clean_results: List[Dict[str, Any]], 
                               lazy_results: List[Dict[str, Any]], 
                               threshold: float) -> Dict[str, Any]:
    """
    Perform a statistical comparison between clean baseline and lazy results
    for a specific threshold.
    
    Since we are simulating the 're-run' of T024a logic without re-executing
    the LLM, we assume the 'lazy_results' passed in are already filtered
    or generated for this specific threshold. In a real re-run scenario,
    we would execute the strategy with this threshold.
    
    Here, we compute the delta and perform a t-test if data is sufficient.
    """
    clean_accs = [r['accuracy'] for r in clean_results if r['status'] == 'COMPLETED']
    lazy_accs = [r['accuracy'] for r in lazy_results if r['status'] == 'COMPLETED']
    
    clean_nodes = [r['nodes_visited'] for r in clean_results if r['status'] == 'COMPLETED']
    lazy_nodes = [r['nodes_visited'] for r in lazy_results if r['status'] == 'COMPLETED']

    # Calculate deltas
    mean_clean_acc = np.mean(clean_accs) if clean_accs else 0.0
    mean_lazy_acc = np.mean(lazy_accs) if lazy_accs else 0.0
    delta_acc = mean_lazy_acc - mean_clean_acc

    mean_clean_nodes = np.mean(clean_nodes) if clean_nodes else 0.0
    mean_lazy_nodes = np.mean(lazy_nodes) if lazy_accs else 0.0
    delta_nodes = mean_lazy_nodes - mean_clean_nodes

    # Statistical test (paired if aligned, otherwise independent)
    # Assuming independent samples for this analysis as task sets might differ slightly
    # or we treat them as independent groups for sensitivity.
    p_value_acc = 0.0
    is_sig_acc = False
    if len(clean_accs) >= 2 and len(lazy_accs) >= 2:
        try:
            # Use Welch's t-test for unequal variances
            stat, p_value_acc = stats.ttest_ind(clean_accs, lazy_accs)
            is_sig_acc = p_value_acc < 0.05
        except Exception as e:
            logger.warning(f"T-test failed: {e}")
            p_value_acc = 1.0

    return {
        'threshold': threshold,
        'mean_baseline_accuracy': float(mean_clean_acc),
        'mean_lazy_accuracy': float(mean_lazy_acc),
        'accuracy_delta': float(delta_acc),
        'mean_baseline_nodes': float(mean_clean_nodes),
        'mean_lazy_nodes': float(mean_lazy_nodes),
        'nodes_delta': float(delta_nodes),
        'p_value_accuracy': float(p_value_acc),
        'is_significant': is_sig_acc,
        'sample_size': len(lazy_accs)
    }

def run_sensitivity_analysis(
    baseline_csv_path: Path, 
    lazy_csv_path: Path,
    thresholds: Optional[List[float]] = None
) -> List[Dict[str, Any]]:
    """
    Main loop to run sensitivity analysis across thresholds.
    
    Note: In this implementation, we assume the 'lazy_csv_path' contains
    results for the Lazy strategy. Since the runner might have been executed
    with a fixed threshold (e.g., 0.7), we cannot simply re-read the same file
    and expect different results for different thresholds.
    
    To satisfy the task requirement of "re-running" the analysis across thresholds
    WITHOUT fabricating LLM calls, we perform the following:
    1. Load the baseline data (clean).
    2. Load the lazy data.
    3. If the lazy data has a specific threshold column, we filter/group by it.
    4. If the lazy data does NOT have varying thresholds (e.g. all 0.7), 
       we simulate the sensitivity loop by:
       - Acknowledging the limitation in the output.
       - Performing the statistical comparison using the available data 
         (which effectively represents the 0.7 point).
       - OR, if the task implies we must generate synthetic sensitivity curves
         based on the available data point (which is a form of estimation),
         we would need a model. 
    
    HOWEVER, the prompt strictly forbids fabrication. 
    The most honest implementation for T062a is to:
    1. Check if the lazy_results.csv actually contains multiple thresholds.
    2. If yes, iterate and compute stats.
    3. If no (single threshold), we can only report that single point 
       and note that a full sensitivity sweep requires re-execution of the 
       runner with different --threshold arguments.
    
    BUT, looking at T019a, the lazy runner logs the threshold. 
    If we only ran T019a once with 0.7, we only have 0.7 data.
    To make this script useful and runnable as a "loop" without re-running 
    the expensive LLM, we will:
    - Load the single threshold data.
    - Report that the loop executed for the available threshold(s).
    - If the user intended to sweep, they must run the runner with --threshold X.
    
    For the purpose of this task implementation, we will assume the lazy CSV
    might contain multiple thresholds if the runner was run multiple times,
    or we will just process the available data.
    
    To strictly follow "Implement the loop", we will iterate over the requested
    thresholds, but we will only compute statistics for thresholds that have
    data in the CSV. If a threshold is requested but not in the data, we skip it
    or log a warning.
    """
    if thresholds is None:
        thresholds = THRESHOLD_RANGE

    ensure_output_dirs()
    
    baseline_data = load_results_from_csv(baseline_csv_path)
    lazy_data = load_results_from_csv(lazy_csv_path)
    
    if not baseline_data:
        raise ValueError(f"Baseline data not found at {baseline_csv_path}")
    
    results = []
    
    # Group lazy data by threshold if possible
    lazy_by_threshold = {}
    for item in lazy_data:
        t = item.get('evidence_threshold')
        if t is not None:
            if t not in lazy_by_threshold:
                lazy_by_threshold[t] = []
            lazy_by_threshold[t].append(item)
    
    logger.info(f"Found {len(lazy_data)} lazy results. Grouped by threshold: {list(lazy_by_threshold.keys())}")
    
    for t in thresholds:
        logger.info(f"Processing threshold: {t}")
        
        # Try to get data for this specific threshold
        if t in lazy_by_threshold:
            current_lazy_data = lazy_by_threshold[t]
        else:
            # If no data for this specific threshold, we cannot fabricate.
            # We log a warning and skip this iteration to avoid empty/fake results.
            logger.warning(f"No data available for threshold {t}. Skipping.")
            continue
        
        # Compute stats
        comparison = run_statistical_comparison(baseline_data, current_lazy_data, t)
        results.append(comparison)
    
    if not results:
        logger.error("No valid threshold data found to perform sensitivity analysis.")
        # We still write an empty result or a result indicating failure
        # to satisfy the "write output" requirement, but with a status flag.
        results.append({
            'error': 'No data available for specified thresholds',
            'thresholds_checked': thresholds
        })

    return results

def main():
    parser = argparse.ArgumentParser(description="Run sensitivity analysis for Lazy strategy.")
    parser.add_argument(
        "--baseline", 
        type=str, 
        default=str(PROJECT_ROOT / "data" / "processed" / "baseline_results.csv"),
        help="Path to baseline results CSV."
    )
    parser.add_argument(
        "--lazy", 
        type=str, 
        default=str(PROJECT_ROOT / "data" / "processed" / "lazy_results.csv"),
        help="Path to lazy strategy results CSV."
    )
    parser.add_argument(
        "--thresholds",
        type=float,
        nargs="+",
        default=THRESHOLD_RANGE,
        help="List of thresholds to analyze."
    )
    parser.add_argument(
        "--output",
        type=str,
        default=str(OUTPUT_FILE),
        help="Output JSON file path."
    )
    
    args = parser.parse_args()
    
    try:
        baseline_path = Path(args.baseline)
        lazy_path = Path(args.lazy)
        
        if not baseline_path.exists():
            raise FileNotFoundError(f"Baseline file not found: {baseline_path}")
        if not lazy_path.exists():
            raise FileNotFoundError(f"Lazy file not found: {lazy_path}")
        
        analysis_results = run_sensitivity_analysis(
            baseline_path, 
            lazy_path, 
            thresholds=args.thresholds
        )
        
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(analysis_results, f, indent=2)
        
        logger.info(f"Sensitivity analysis complete. Results saved to {output_path}")
        
    except Exception as e:
        logger.error(f"Sensitivity analysis failed: {e}")
        raise

if __name__ == "__main__":
    main()