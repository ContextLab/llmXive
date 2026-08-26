"""
Threshold & Inflection Analysis for llmXive follow-up.

Implements dynamic binning algorithm to identify the first bin with mean accuracy < 95% of the baseline.
Output: data/processed/threshold_analysis.json
"""
import json
import csv
import logging
import argparse
import os
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
import numpy as np

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def load_results_from_csv(file_path: str) -> List[Dict[str, Any]]:
    """Load results from a CSV file."""
    results = []
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Results file not found: {file_path}")
    
    with open(file_path, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            results.append(row)
    return results

def calculate_baseline_accuracy(results: List[Dict[str, Any]]) -> float:
    """Calculate the mean accuracy from the baseline results."""
    if not results:
        raise ValueError("No results provided to calculate baseline accuracy.")
    
    accuracies = []
    for row in results:
        try:
            acc = float(row.get('accuracy', 0))
            if not np.isnan(acc):
                accuracies.append(acc)
        except (ValueError, TypeError):
            continue
    
    if not accuracies:
        raise ValueError("No valid accuracy values found in baseline results.")
    
    return float(np.mean(accuracies))

def perform_bin_analysis(results: List[Dict[str, Any]], baseline_accuracy: float) -> Dict[str, Any]:
    """
    Perform dynamic binning analysis to find the inflection point.
    
    Algorithm:
    1. Sort tasks by nodes_visited.
    2. Create bins such that each bin contains at least 3 tasks (n >= 3).
    3. If a bin has fewer than 3 tasks, merge with adjacent bin.
    4. Iterate to find first bin where mean accuracy < 95% of baseline.
    """
    # Filter valid results
    valid_results = []
    for row in results:
        try:
            nodes = int(row.get('nodes_visited', 0))
            acc = float(row.get('accuracy', 0))
            if not np.isnan(acc):
                valid_results.append({'nodes_visited': nodes, 'accuracy': acc, 'task_id': row.get('task_id', 'unknown')})
        except (ValueError, TypeError):
            continue
    
    if not valid_results:
        return {
            'inflection_point': None,
            'correlation_coefficient': None,
            'trend_summary': "No valid data points found.",
            'is_significant': False,
            'p_value': None,
            'bin_details': []
        }
    
    # Sort by nodes_visited
    valid_results.sort(key=lambda x: x['nodes_visited'])
    
    # Dynamic binning with n >= 3 constraint
    bins = []
    current_bin = []
    
    for item in valid_results:
        current_bin.append(item)
        if len(current_bin) >= 3:
            bins.append(current_bin)
            current_bin = []
    
    # Handle remaining items
    if current_bin:
        if len(bins) == 0:
            # If we have fewer than 3 total items, we can't form a valid bin
            # For robustness, we'll return a warning
            return {
                'inflection_point': None,
                'correlation_coefficient': None,
                'trend_summary': f"Insufficient data points ({len(valid_results)}) to form bins of size >= 3.",
                'is_significant': False,
                'p_value': None,
                'bin_details': []
            }
        # Merge with last bin
        bins[-1].extend(current_bin)
    
    # Analyze bins to find inflection point
    inflection_point = None
    inflection_bin_index = None
    bin_details = []
    
    for i, bin_items in enumerate(bins):
        nodes_list = [item['nodes_visited'] for item in bin_items]
        acc_list = [item['accuracy'] for item in bin_items]
        
        mean_nodes = float(np.mean(nodes_list))
        mean_acc = float(np.mean(acc_list))
        threshold = 0.95 * baseline_accuracy
        
        bin_info = {
            'bin_index': i,
            'task_count': len(bin_items),
            'mean_nodes_visited': mean_nodes,
            'mean_accuracy': mean_acc,
            'threshold_95_baseline': threshold,
            'below_threshold': mean_acc < threshold
        }
        bin_details.append(bin_info)
        
        if inflection_point is None and mean_acc < threshold:
            inflection_point = mean_nodes
            inflection_bin_index = i
            logger.info(f"Inflection point found at bin {i}: mean_acc={mean_acc:.4f} < threshold={threshold:.4f}")
            break
    
    # Calculate correlation coefficient (Point-Biserial equivalent for continuous nodes vs accuracy)
    # We use Pearson correlation between nodes_visited and accuracy
    if len(valid_results) >= 2:
        nodes_array = np.array([item['nodes_visited'] for item in valid_results])
        acc_array = np.array([item['accuracy'] for item in valid_results])
        
        # Check for constant values
        if np.std(nodes_array) > 0 and np.std(acc_array) > 0:
            corr, p_val = stats.pearsonr(nodes_array, acc_array)
        else:
            corr, p_val = 0.0, 1.0
    else:
        corr, p_val = 0.0, 1.0
    
    # Determine significance
    is_significant = inflection_point is not None and p_val < 0.05
    
    # Trend summary
    if inflection_point is not None:
        trend_summary = f"Inflection detected at ~{inflection_point:.1f} nodes. Accuracy drops below 95% of baseline."
    else:
        trend_summary = "No inflection point detected. Accuracy remains above 95% of baseline across all bins."
    
    return {
        'inflection_point': inflection_point,
        'correlation_coefficient': float(corr),
        'trend_summary': trend_summary,
        'is_significant': bool(is_significant),
        'p_value': float(p_val),
        'bin_details': bin_details,
        'baseline_accuracy': baseline_accuracy,
        'total_tasks_analyzed': len(valid_results)
    }

def analyze_strategy(strategy_name: str, results_file: str, baseline_file: str) -> Dict[str, Any]:
    """Analyze a specific strategy against the baseline."""
    logger.info(f"Analyzing strategy: {strategy_name}")
    
    try:
        results = load_results_from_csv(results_file)
        baseline_results = load_results_from_csv(baseline_file)
        
        if not baseline_results:
            raise ValueError(f"Baseline file {baseline_file} is empty or invalid.")
        
        baseline_accuracy = calculate_baseline_accuracy(baseline_results)
        logger.info(f"Baseline accuracy: {baseline_accuracy:.4f}")
        
        analysis_result = perform_bin_analysis(results, baseline_accuracy)
        analysis_result['strategy'] = strategy_name
        
        return analysis_result
    except Exception as e:
        logger.error(f"Error analyzing strategy {strategy_name}: {e}")
        return {
            'strategy': strategy_name,
            'error': str(e),
            'inflection_point': None,
            'correlation_coefficient': None,
            'trend_summary': "Analysis failed.",
            'is_significant': False,
            'p_value': None
        }

def main():
    parser = argparse.ArgumentParser(description='Threshold & Inflection Analysis')
    parser.add_argument('--baseline', type=str, default='data/processed/baseline_results.csv',
                        help='Path to baseline results CSV')
    parser.add_argument('--strategy', type=str, default='data/processed/lazy_results.csv',
                        help='Path to strategy results CSV to analyze')
    parser.add_argument('--output', type=str, default='data/processed/threshold_analysis.json',
                        help='Output JSON file path')
    
    args = parser.parse_args()
    
    # Ensure output directory exists
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Run analysis
    result = analyze_strategy('custom', args.strategy, args.baseline)
    
    # Save results
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2)
    
    logger.info(f"Threshold analysis saved to {output_path}")
    logger.info(f"Inflection point: {result.get('inflection_point')}")
    logger.info(f"Is significant: {result.get('is_significant')}")

if __name__ == '__main__':
    main()