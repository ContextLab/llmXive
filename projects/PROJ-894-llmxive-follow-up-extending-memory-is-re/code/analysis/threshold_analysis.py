"""
Threshold & Inflection Analysis for LLMXive Memory Reconstruction.

This module implements a binning algorithm to identify the inflection point
where mean accuracy drops below 95% of the baseline accuracy.

Outputs:
    data/processed/threshold_analysis.json: Contains inflection_point, 
    correlation_coefficient, and trend_summary.
"""
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

# Constants
BASELINE_ACCURACY_THRESHOLD = 0.95
MIN_BIN_SIZE = 3
OUTPUT_PATH = Path("data/processed/threshold_analysis.json")
BASELINE_RESULTS_PATH = Path("data/processed/baseline_results.csv")
LAZY_RESULTS_PATH = Path("data/processed/lazy_results.csv")
GREEDY_RESULTS_PATH = Path("data/processed/greedy_results.csv")
NOISY_BASELINE_PATH = Path("data/processed/noisy_baseline_results.csv")
NOISY_LAZY_PATH = Path("data/processed/noisy_lazy_results.csv")
NOISY_GREEDY_PATH = Path("data/processed/noisy_greedy_results.csv")

def load_results_from_csv(file_path: Path) -> List[Dict[str, Any]]:
    """
    Load results from a CSV file.
    
    Args:
        file_path: Path to the CSV file.
        
    Returns:
        List of dictionaries containing task results.
    """
    if not file_path.exists():
        logger.warning(f"File not found: {file_path}. Skipping.")
        return []
    
    results = []
    with open(file_path, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Convert numeric fields
            try:
                row['accuracy'] = float(row.get('accuracy', 0))
                row['nodes_visited'] = int(row.get('nodes_visited', 0))
                row['latency_ms'] = float(row.get('latency_ms', 0))
                results.append(row)
            except (ValueError, TypeError) as e:
                logger.warning(f"Skipping malformed row in {file_path}: {e}")
                continue
    
    logger.info(f"Loaded {len(results)} results from {file_path}")
    return results

def calculate_baseline_accuracy(results: List[Dict[str, Any]]) -> float:
    """
    Calculate the mean accuracy from baseline results.
    
    Args:
        results: List of baseline task results.
        
    Returns:
        Mean accuracy as a float.
    """
    if not results:
        logger.error("No baseline results provided. Cannot calculate mean accuracy.")
        raise ValueError("Baseline results cannot be empty.")
    
    accuracies = [r['accuracy'] for r in results]
    mean_acc = np.mean(accuracies)
    logger.info(f"Calculated baseline mean accuracy: {mean_acc:.4f}")
    return mean_acc

def perform_bin_analysis(
    results: List[Dict[str, Any]], 
    baseline_mean_acc: float
) -> Tuple[Optional[int], float, str]:
    """
    Perform binning analysis to find the inflection point.
    
    Bins are created based on 'nodes_visited' counts. We look for the first bin
    where the mean accuracy drops below 95% of the baseline mean accuracy.
    
    Args:
        results: List of task results (lazy, greedy, or noisy variants).
        baseline_mean_acc: The mean accuracy of the baseline strategy.
        
    Returns:
        Tuple of (inflection_point, correlation_coefficient, trend_summary).
        inflection_point: The nodes_visited count where accuracy dropped below threshold.
        correlation_coefficient: Pearson correlation between nodes_visited and accuracy.
        trend_summary: A string describing the overall trend.
    """
    if not results:
        return None, 0.0, "No data available for analysis."

    # Sort results by nodes_visited
    sorted_results = sorted(results, key=lambda x: x['nodes_visited'])
    
    nodes_list = [r['nodes_visited'] for r in sorted_results]
    acc_list = [r['accuracy'] for r in sorted_results]

    # Calculate Pearson correlation
    if len(nodes_list) > 1 and len(acc_list) > 1:
        try:
            correlation = np.corrcoef(nodes_list, acc_list)[0, 1]
            if np.isnan(correlation):
                correlation = 0.0
        except Exception as e:
            logger.warning(f"Correlation calculation failed: {e}")
            correlation = 0.0
    else:
        correlation = 0.0

    # Create bins based on nodes_visited
    # Strategy: Group by unique nodes_visited values, but ensure min_bin_size
    # If a unique value has < min_bin_size, merge with neighbors?
    # Simplified approach for this specific task:
    # 1. Get unique node counts
    # 2. Form bins of consecutive unique counts such that each bin has >= MIN_BIN_SIZE tasks
    
    unique_nodes = sorted(list(set(nodes_list)))
    bins = []
    current_bin_nodes = []
    current_bin_accs = []
    
    for node_val in unique_nodes:
        # Get all accuracies for this node count
        indices = [i for i, n in enumerate(nodes_list) if n == node_val]
        vals = [acc_list[i] for i in indices]
        
        if len(current_bin_nodes) == 0:
            current_bin_nodes = [node_val]
            current_bin_accs = vals
        else:
            # Check if adding this group keeps us >= MIN_BIN_SIZE? 
            # Actually, the constraint is per bin. 
            # If the current bin has >= MIN_BIN_SIZE, we can close it and start a new one.
            if len(current_bin_accs) >= MIN_BIN_SIZE:
                # Save current bin
                bins.append({
                    'nodes': current_bin_nodes,
                    'accuracies': current_bin_accs,
                    'mean_nodes': np.mean(current_bin_nodes),
                    'mean_acc': np.mean(current_bin_accs)
                })
                current_bin_nodes = [node_val]
                current_bin_accs = vals
            else:
                # Add to current bin
                current_bin_nodes.append(node_val)
                current_bin_accs.extend(vals)
    
    # Don't forget the last bin
    if current_bin_accs:
        bins.append({
            'nodes': current_bin_nodes,
            'accuracies': current_bin_accs,
            'mean_nodes': np.mean(current_bin_nodes),
            'mean_acc': np.mean(current_bin_accs)
        })

    logger.info(f"Created {len(bins)} bins for analysis.")
    
    inflection_point = None
    threshold_value = baseline_mean_acc * BASELINE_ACCURACY_THRESHOLD
    
    for i, bin_data in enumerate(bins):
        if bin_data['mean_acc'] < threshold_value:
            inflection_point = int(bin_data['mean_nodes'])
            logger.info(f"Inflection point found at bin {i}: nodes={inflection_point}, mean_acc={bin_data['mean_acc']:.4f} (threshold={threshold_value:.4f})")
            break
    
    if inflection_point is None:
        logger.info(f"No inflection point found. All bins maintained accuracy >= {threshold_value:.4f}")
    
    # Determine trend summary
    if not bins:
        trend_summary = "Insufficient data to determine trend."
    elif len(bins) == 1:
        trend_summary = "Single bin data: no trend analysis possible."
    else:
        first_bin_acc = bins[0]['mean_acc']
        last_bin_acc = bins[-1]['mean_acc']
        if last_bin_acc < first_bin_acc:
            trend_summary = "Negative trend: Accuracy decreases as nodes visited increases."
        elif last_bin_acc > first_bin_acc:
            trend_summary = "Positive trend: Accuracy increases as nodes visited increases."
        else:
            trend_summary = "Flat trend: Accuracy remains stable across node counts."

    return inflection_point, correlation, trend_summary

def analyze_strategy(
    strategy_name: str,
    results_path: Path,
    baseline_mean_acc: float
) -> Dict[str, Any]:
    """
    Analyze a specific strategy and return results.
    
    Args:
        strategy_name: Name of the strategy (e.g., 'lazy', 'greedy').
        results_path: Path to the strategy's results CSV.
        baseline_mean_acc: Baseline mean accuracy.
        
    Returns:
        Dictionary containing analysis results for this strategy.
    """
    results = load_results_from_csv(results_path)
    
    if not results:
        return {
            "strategy": strategy_name,
            "status": "skipped",
            "reason": "No data found"
        }
    
    inflection_point, correlation, trend = perform_bin_analysis(results, baseline_mean_acc)
    
    return {
        "strategy": strategy_name,
        "status": "completed",
        "inflection_point": inflection_point,
        "correlation_coefficient": round(correlation, 4),
        "trend_summary": trend,
        "total_tasks": len(results),
        "baseline_mean_accuracy": round(baseline_mean_acc, 4)
    }

def main():
    """
    Main entry point for threshold and inflection analysis.
    """
    parser = argparse.ArgumentParser(description="Threshold & Inflection Analysis")
    parser.add_argument("--baseline", type=str, default=str(BASELINE_RESULTS_PATH),
                        help="Path to baseline results CSV")
    parser.add_argument("--output", type=str, default=str(OUTPUT_PATH),
                        help="Path for output JSON")
    args = parser.parse_args()

    output_path = Path(args.output)
    baseline_path = Path(args.baseline)

    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Load baseline results
    logger.info(f"Loading baseline results from {baseline_path}")
    baseline_results = load_results_from_csv(baseline_path)
    
    if not baseline_results:
        logger.error("Baseline results are empty or missing. Cannot proceed.")
        raise ValueError("Cannot perform analysis without baseline data.")

    baseline_mean_acc = calculate_baseline_accuracy(baseline_results)

    # Define strategies to analyze
    strategies = [
        ("lazy", LAZY_RESULTS_PATH),
        ("greedy", GREEDY_RESULTS_PATH),
        ("noisy_baseline", NOISY_BASELINE_PATH),
        ("noisy_lazy", NOISY_LAZY_PATH),
        ("noisy_greedy", NOISY_GREEDY_PATH)
    ]

    analysis_results = {
        "baseline_mean_accuracy": round(baseline_mean_acc, 4),
        "threshold_percentage": BASELINE_ACCURACY_THRESHOLD,
        "strategies": []
    }

    for name, path in strategies:
        logger.info(f"Analyzing strategy: {name}")
        result = analyze_strategy(name, path, baseline_mean_acc)
        analysis_results["strategies"].append(result)

    # Write output
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(analysis_results, f, indent=2)
    
    logger.info(f"Analysis complete. Results saved to {output_path}")
    print(f"Threshold analysis complete. Output: {output_path}")

if __name__ == "__main__":
    main()