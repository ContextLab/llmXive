import json
import csv
import logging
import argparse
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
import numpy as np

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def load_results_from_csv(file_path: str) -> List[Dict[str, Any]]:
    """Load results from a CSV file into a list of dictionaries."""
    results = []
    try:
        with open(file_path, 'r', newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                # Convert numeric fields
                if 'nodes_visited' in row:
                    row['nodes_visited'] = int(row['nodes_visited'])
                if 'accuracy' in row:
                    row['accuracy'] = float(row['accuracy'])
                results.append(row)
    except FileNotFoundError:
        logger.error(f"File not found: {file_path}")
        return []
    except Exception as e:
        logger.error(f"Error loading {file_path}: {e}")
        return []
    return results

def calculate_baseline_accuracy(baseline_results: List[Dict[str, Any]]) -> float:
    """Calculate the mean accuracy from baseline results."""
    if not baseline_results:
        return 0.0
    accuracies = [r['accuracy'] for r in baseline_results if 'accuracy' in r and isinstance(r['accuracy'], (int, float))]
    if not accuracies:
        return 0.0
    return np.mean(accuracies)

def perform_bin_analysis(tasks: List[Dict[str, Any]], baseline_accuracy: float, p_value: float) -> Dict[str, Any]:
    """
    Perform dynamic binning to find the first bin where mean accuracy < 95% of baseline.
    
    Algorithm:
    1. Sort tasks by nodes_visited.
    2. Create bins with at least 3 tasks (n >= 3).
    3. Merge bins with < 3 tasks with adjacent bins.
    4. Iterate to find the first bin where mean accuracy < 0.95 * baseline_accuracy.
    5. If p_value >= 0.05, return null inflection point.
    """
    if not tasks:
        return {
            "inflection_point": None,
            "correlation_coefficient": None,
            "trend_summary": "No data available for analysis.",
            "is_significant": False,
            "p_value": p_value
        }

    # Check significance
    if p_value >= 0.05:
        return {
            "inflection_point": None,
            "correlation_coefficient": None,
            "trend_summary": "No significant inflection point detected.",
            "is_significant": False,
            "p_value": p_value
        }

    # Sort by nodes_visited
    sorted_tasks = sorted(tasks, key=lambda x: x.get('nodes_visited', 0))

    # Initial binning: create bins of size 3
    # We'll use a sliding window approach to ensure n >= 3
    bins = []
    current_bin = []
    
    for task in sorted_tasks:
        current_bin.append(task)
        if len(current_bin) >= 3:
            bins.append(current_bin)
            current_bin = []
    
    # Handle remaining tasks
    if current_bin:
        if not bins:
            # If we have fewer than 3 tasks total, we can't form a valid bin
            # Return no inflection point
            return {
                "inflection_point": None,
                "correlation_coefficient": None,
                "trend_summary": "Insufficient data to form bins (n < 3).",
                "is_significant": False,
                "p_value": p_value
            }
        # Merge with the last bin
        bins[-1].extend(current_bin)

    # Now iterate through bins to find the first one meeting the criteria
    threshold = 0.95 * baseline_accuracy
    inflection_point = None
    trend_summary = "No significant inflection point detected."
    
    for i, bin_tasks in enumerate(bins):
        if not bin_tasks:
            continue
        
        accuracies = [t['accuracy'] for t in bin_tasks if 'accuracy' in t and isinstance(t['accuracy'], (int, float))]
        if not accuracies:
            continue
        
        mean_accuracy = np.mean(accuracies)
        
        if mean_accuracy < threshold:
            # Found the inflection point
            # Use the maximum nodes_visited in this bin as the inflection point
            nodes_visited_values = [t['nodes_visited'] for t in bin_tasks if 'nodes_visited' in t]
            inflection_point = max(nodes_visited_values) if nodes_visited_values else None
            trend_summary = f"Inflection point detected at {inflection_point} nodes (mean accuracy {mean_accuracy:.4f} < {threshold:.4f})."
            break

    if inflection_point is None:
        trend_summary = "No inflection point detected; accuracy remained above threshold across all bins."

    return {
        "inflection_point": inflection_point,
        "correlation_coefficient": None,  # Will be filled by main if needed, or from T025
        "trend_summary": trend_summary,
        "is_significant": True,
        "p_value": p_value
    }

def analyze_strategy(
    baseline_file: str, 
    strategy_file: str, 
    correlation_file: str, 
    statistical_file: str, 
    output_file: str
) -> None:
    """
    Main analysis function for T027.
    Loads baseline results, strategy results, correlation results, and statistical results.
    Performs binning analysis and writes threshold_analysis.json.
    """
    # Load baseline results
    baseline_results = load_results_from_csv(baseline_file)
    if not baseline_results:
        logger.error("No baseline results found. Cannot perform analysis.")
        # Write empty/null result
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump({
                "inflection_point": None,
                "correlation_coefficient": None,
                "trend_summary": "Error: No baseline results found.",
                "is_significant": False,
                "p_value": None
            }, f, indent=2)
        return

    baseline_accuracy = calculate_baseline_accuracy(baseline_results)
    logger.info(f"Baseline accuracy: {baseline_accuracy:.4f}")

    # Load strategy results (clean or noisy, depending on context, but T027 uses clean by default unless specified)
    # The task description implies analyzing the clean data first (T024a).
    strategy_results = load_results_from_csv(strategy_file)
    if not strategy_results:
        logger.warning(f"Strategy results file {strategy_file} is empty or missing. Using baseline for analysis.")
        strategy_results = baseline_results

    # Load statistical results (p-value)
    p_value = 0.05  # Default
    try:
        with open(statistical_file, 'r', encoding='utf-8') as f:
            stats_data = json.load(f)
            # Look for p-value in various possible keys
            if 'p_value' in stats_data:
                p_value = stats_data['p_value']
            elif 'results' in stats_data and isinstance(stats_data['results'], dict):
                if 'p_value' in stats_data['results']:
                    p_value = stats_data['results']['p_value']
            logger.info(f"Loaded p-value from {statistical_file}: {p_value}")
    except Exception as e:
        logger.warning(f"Could not load statistical results from {statistical_file}: {e}. Using default p=0.05.")

    # Load correlation coefficient (optional, from T025)
    correlation_coefficient = None
    try:
        with open(correlation_file, 'r', encoding='utf-8') as f:
            corr_data = json.load(f)
            if 'correlation_coefficient' in corr_data:
                correlation_coefficient = corr_data['correlation_coefficient']
            elif 'result' in corr_data and isinstance(corr_data['result'], dict):
                if 'correlation_coefficient' in corr_data['result']:
                    correlation_coefficient = corr_data['result']['correlation_coefficient']
            logger.info(f"Loaded correlation coefficient: {correlation_coefficient}")
    except Exception as e:
        logger.warning(f"Could not load correlation results from {correlation_file}: {e}.")

    # Perform bin analysis
    analysis_result = perform_bin_analysis(strategy_results, baseline_accuracy, p_value)
    
    # Attach correlation coefficient if available
    if correlation_coefficient is not None:
        analysis_result['correlation_coefficient'] = correlation_coefficient

    # Ensure output directory exists
    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Write results
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(analysis_result, f, indent=2)
    
    logger.info(f"Threshold analysis written to {output_file}")

def main():
    parser = argparse.ArgumentParser(description="Perform threshold and inflection analysis (T027).")
    parser.add_argument("--baseline", type=str, default="data/processed/baseline_results.csv",
                        help="Path to baseline results CSV.")
    parser.add_argument("--strategy", type=str, default="data/processed/lazy_results.csv",
                        help="Path to strategy results CSV (e.g., lazy, greedy).")
    parser.add_argument("--correlation", type=str, default="data/processed/correlation_results.json",
                        help="Path to correlation results JSON.")
    parser.add_argument("--statistics", type=str, default="data/processed/statistical_results.json",
                        help="Path to statistical results JSON.")
    parser.add_argument("--output", type=str, default="data/processed/threshold_analysis.json",
                        help="Output path for threshold analysis JSON.")
    
    args = parser.parse_args()
    
    analyze_strategy(
        baseline_file=args.baseline,
        strategy_file=args.strategy,
        correlation_file=args.correlation,
        statistical_file=args.statistics,
        output_file=args.output
    )

if __name__ == "__main__":
    main()