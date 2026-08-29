"""
Threshold & Inflection Analysis (T027)

Implements dynamic binning to identify the inflection point where mean accuracy
drops below 95% of the baseline.

Algorithm:
1. Sort tasks by `nodes_visited` ascending.
2. Create bins with n >= 3 tasks. Merge adjacent bins if constraint is violated.
3. Find the first bin (lowest node count) where mean accuracy < 0.95 * baseline_accuracy.
4. Output inflection point, correlation, trend summary, significance, and p-value.
"""

import json
import csv
import logging
import argparse
import os
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional

import numpy as np
from scipy import stats

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_results_from_csv(file_path: str) -> List[Dict[str, Any]]:
    """Load results from a CSV file."""
    results = []
    if not os.path.exists(file_path):
        logger.error(f"File not found: {file_path}")
        return results

    with open(file_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                # Parse numeric fields
                task = {
                    'task_id': row.get('task_id', ''),
                    'accuracy': float(row.get('accuracy', 0.0)),
                    'nodes_visited': int(row.get('nodes_visited', 0)),
                    'latency_ms': float(row.get('latency_ms', 0.0)),
                    'status': row.get('status', 'UNKNOWN')
                }
                # Only include completed tasks for analysis
                if task['status'] == 'COMPLETED':
                    results.append(task)
            except (ValueError, TypeError) as e:
                logger.warning(f"Skipping invalid row: {row} due to {e}")
    return results

def calculate_baseline_accuracy(baseline_results: List[Dict[str, Any]]) -> float:
    """Calculate the mean accuracy of the baseline strategy."""
    if not baseline_results:
        return 0.0
    accuracies = [r['accuracy'] for r in baseline_results]
    return float(np.mean(accuracies))

def perform_bin_analysis(
    tasks: List[Dict[str, Any]],
    baseline_accuracy: float,
    min_bin_size: int = 3
) -> Tuple[List[Dict[str, Any]], Optional[int], bool]:
    """
    Perform dynamic binning to find the inflection point.

    Returns:
        bins: List of bin dictionaries with stats
        inflection_node_count: The nodes_visited count of the first failing bin, or None
        is_significant: True if an inflection point was found
    """
    if len(tasks) < min_bin_size:
        logger.warning(f"Insufficient data: {len(tasks)} tasks < min_bin_size {min_bin_size}")
        return [], None, False

    # Sort by nodes_visited ascending
    sorted_tasks = sorted(tasks, key=lambda x: x['nodes_visited'])

    # Initial binning: group by unique node counts or simple chunks
    # To ensure n >= 3, we start with a greedy approach
    bins = []
    current_bin = []

    for task in sorted_tasks:
        current_bin.append(task)
        if len(current_bin) >= min_bin_size:
            bins.append(current_bin)
            current_bin = []

    # Handle remaining tasks
    if current_bin:
        # Merge with previous bin if it exists
        if bins:
            bins[-1].extend(current_bin)
        else:
            # Only one bin exists and it's too small
            # This case is handled by the initial check, but safety first
            bins.append(current_bin)

    # Post-processing: Ensure every bin has n >= 3
    # If a bin has < 3, merge with neighbor (prefer previous)
    final_bins = []
    i = 0
    while i < len(bins):
        bin_data = bins[i]
        if len(bin_data) < min_bin_size:
            # Try to merge with previous
            if final_bins:
                final_bins[-1].extend(bin_data)
            # If no previous, try next (if exists)
            elif i + 1 < len(bins):
                bins[i+1].extend(bin_data)
            # If neither, keep as is (will be handled by result logic)
            else:
                final_bins.append(bin_data)
        else:
            final_bins.append(bin_data)
        i += 1

    # Recalculate stats for merged bins
    bin_stats = []
    for idx, bin_tasks in enumerate(final_bins):
        if not bin_tasks:
            continue
        accuracies = [t['accuracy'] for t in bin_tasks]
        nodes = [t['nodes_visited'] for t in bin_tasks]
        mean_acc = float(np.mean(accuracies))
        mean_nodes = int(np.mean(nodes))
        std_acc = float(np.std(accuracies))

        # Check inflection condition: mean_acc < 0.95 * baseline
        threshold = 0.95 * baseline_accuracy
        is_inflection = mean_acc < threshold

        bin_stats.append({
            'bin_index': idx,
            'n_tasks': len(bin_tasks),
            'mean_nodes_visited': mean_nodes,
            'mean_accuracy': mean_acc,
            'std_accuracy': std_acc,
            'threshold': threshold,
            'is_inflection': is_inflection
        })

    # Find first inflection
    inflection_node_count = None
    for b in bin_stats:
        if b['is_inflection']:
            inflection_node_count = b['mean_nodes_visited']
            break

    return bin_stats, inflection_node_count, inflection_node_count is not None

def analyze_strategy(
    strategy_name: str,
    results_path: str,
    baseline_accuracy: float
) -> Dict[str, Any]:
    """Analyze a specific strategy against the baseline."""
    logger.info(f"Analyzing strategy: {strategy_name} from {results_path}")

    if not os.path.exists(results_path):
        logger.error(f"Results file not found: {results_path}")
        return {
            'strategy': strategy_name,
            'error': 'File not found',
            'bins': [],
            'inflection_node_count': None,
            'is_significant': False
        }

    tasks = load_results_from_csv(results_path)
    if not tasks:
        logger.warning(f"No valid completed tasks found in {results_path}")
        return {
            'strategy': strategy_name,
            'task_count': 0,
            'bins': [],
            'inflection_node_count': None,
            'is_significant': False
        }

    bin_stats, inflection_node, is_sig = perform_bin_analysis(tasks, baseline_accuracy)

    # Calculate correlation for the trend
    if len(tasks) >= 2:
        nodes = [t['nodes_visited'] for t in tasks]
        accs = [t['accuracy'] for t in tasks]
        try:
            corr, p_val = stats.pearsonr(nodes, accs)
            correlation = float(corr)
            p_value = float(p_val)
        except Exception as e:
            logger.warning(f"Correlation calculation failed: {e}")
            correlation = 0.0
            p_value = 1.0
    else:
        correlation = 0.0
        p_value = 1.0

    return {
        'strategy': strategy_name,
        'task_count': len(tasks),
        'bins': bin_stats,
        'inflection_node_count': inflection_node,
        'is_significant': is_sig,
        'correlation_coefficient': correlation,
        'p_value': p_value,
        'trend_summary': "Negative" if correlation < 0 else "Positive" if correlation > 0 else "Neutral"
    }

def main():
    parser = argparse.ArgumentParser(description='Threshold & Inflection Analysis (T027)')
    parser.add_argument('--baseline', type=str, required=True,
                        help='Path to baseline results CSV (e.g., data/processed/baseline_results.csv)')
    parser.add_argument('--strategy', type=str, required=True,
                        help='Path to strategy results CSV (e.g., data/processed/lazy_results.csv)')
    parser.add_argument('--output', type=str, required=True,
                        help='Output JSON path (e.g., data/processed/threshold_analysis.json)')
    args = parser.parse_args()

    # Ensure output directory exists
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Calculate baseline accuracy
    baseline_results = load_results_from_csv(args.baseline)
    if not baseline_results:
        logger.error("Baseline results are empty or missing. Cannot proceed.")
        # Write a failure result
        result = {
            'error': 'Baseline results empty',
            'inflection_point': None,
            'correlation_coefficient': None,
            'trend_summary': 'N/A',
            'is_significant': False,
            'p_value': None
        }
        with open(output_path, 'w') as f:
            json.dump(result, f, indent=2)
        return

    baseline_acc = calculate_baseline_accuracy(baseline_results)
    logger.info(f"Baseline Mean Accuracy: {baseline_acc:.4f}")

    # Analyze the strategy
    strategy_result = analyze_strategy("Strategy", args.strategy, baseline_acc)

    # Construct final output
    final_output = {
        'baseline_accuracy': baseline_acc,
        'inflection_point': strategy_result['inflection_node_count'],
        'correlation_coefficient': strategy_result['correlation_coefficient'],
        'trend_summary': strategy_result['trend_summary'],
        'is_significant': strategy_result['is_significant'],
        'p_value': strategy_result['p_value'],
        'bin_details': strategy_result['bins']
    }

    # Write output
    with open(output_path, 'w') as f:
        json.dump(final_output, f, indent=2)

    logger.info(f"Threshold analysis complete. Output written to {output_path}")
    logger.info(f"Inflection Point (nodes): {final_output['inflection_point']}")
    logger.info(f"Is Significant: {final_output['is_significant']}")

if __name__ == '__main__':
    main()