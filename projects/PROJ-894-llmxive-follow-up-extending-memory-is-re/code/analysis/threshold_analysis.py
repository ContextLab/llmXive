"""
Threshold & Inflection Analysis for LLM Memory Reconstruction Study.

Implements adaptive/quantile-based binning to identify the inflection point
where heuristic strategy accuracy drops below 95% of the baseline.

Requires real execution results from T013 (baseline), T019a (lazy), T019b (greedy).
"""
import json
import csv
import logging
import argparse
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
import numpy as np
from scipy import stats

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def load_results_from_csv(file_path: Path) -> List[Dict[str, Any]]:
    """Load results from a CSV file into a list of dictionaries."""
    if not file_path.exists():
        raise FileNotFoundError(f"Results file not found: {file_path}")
    
    results = []
    with open(file_path, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Convert numeric fields
            try:
                row['accuracy'] = float(row['accuracy'])
                row['nodes_visited'] = int(row['nodes_visited'])
                row['latency_ms'] = float(row['latency_ms'])
            except (ValueError, KeyError) as e:
                logger.warning(f"Skipping row due to conversion error: {e}")
                continue
            results.append(row)
    
    return results

def calculate_baseline_accuracy(baseline_results: List[Dict[str, Any]]) -> float:
    """Calculate the mean accuracy of the baseline strategy."""
    if not baseline_results:
        raise ValueError("Baseline results list is empty")
    
    accuracies = [r['accuracy'] for r in baseline_results]
    return float(np.mean(accuracies))

def perform_bin_analysis(
    strategy_results: List[Dict[str, Any]],
    baseline_accuracy: float,
    alpha: float = 0.05
) -> Dict[str, Any]:
    """
    Perform quantile-based binning and statistical significance testing.
    
    Steps:
    1. Bin data by nodes_visited using quantiles to ensure n >= 3 per bin.
    2. Calculate mean accuracy per bin.
    3. Identify the first bin where mean accuracy < 95% of baseline.
    4. Perform statistical test (t-test or Wilcoxon) on the trend.
    5. Return inflection point only if trend is significant (p < 0.05).
    
    Args:
        strategy_results: List of result dictionaries with 'accuracy' and 'nodes_visited'.
        baseline_accuracy: Mean accuracy of the baseline strategy.
        alpha: Significance level for statistical tests.
    
    Returns:
        Dictionary with analysis results.
    """
    if len(strategy_results) < 3:
        return {
            "inflection_point": None,
            "correlation_coefficient": None,
            "trend_summary": "INSUFFICIENT_DATA",
            "is_significant": False,
            "p_value": None,
            "error": "Dataset too small to form valid bins (n < 3)"
        }
    
    # Extract data
    nodes = np.array([r['nodes_visited'] for r in strategy_results])
    accuracies = np.array([r['accuracy'] for r in strategy_results])
    
    # Sort by nodes_visited for binning
    sort_indices = np.argsort(nodes)
    nodes_sorted = nodes[sort_indices]
    accuracies_sorted = accuracies[sort_indices]
    
    # Determine number of bins
    # Ensure at least 3 bins if possible, but respect n >= 3 per bin constraint
    n_samples = len(nodes_sorted)
    min_bin_size = 3
    max_bins = n_samples // min_bin_size
    
    if max_bins < 2:
        return {
            "inflection_point": None,
            "correlation_coefficient": None,
            "trend_summary": "INSUFFICIENT_DATA",
            "is_significant": False,
            "p_value": None,
            "error": f"Cannot form sufficient bins: {n_samples} samples < {min_bin_size * 2} required"
        }
    
    # Use quantile-based binning
    # Create bin edges based on quantiles to ensure roughly equal distribution
    n_bins = max(2, min(max_bins, 5))  # Limit to 5 bins to avoid over-fragmentation
    
    # Calculate quantile edges
    quantiles = np.linspace(0, 1, n_bins + 1)
    bin_edges = np.quantile(nodes_sorted, quantiles)
    
    # Ensure unique edges to avoid empty bins
    bin_edges = np.unique(bin_edges)
    if len(bin_edges) < 3:
        # Fallback to fewer bins
        n_bins = len(bin_edges) - 1
        if n_bins < 2:
            return {
                "inflection_point": None,
                "correlation_coefficient": None,
                "trend_summary": "INSUFFICIENT_DATA",
                "is_significant": False,
                "p_value": None,
                "error": "Could not form valid bins after edge deduplication"
            }
    
    # Assign bins
    bin_indices = np.digitize(nodes_sorted, bin_edges[1:-1])
    
    # Process bins
    bin_data = []
    for i in range(n_bins):
        # Get indices for this bin
        if i == 0:
            indices = np.where(bin_indices == i)[0]
        else:
            indices = np.where((bin_indices >= i) & (bin_indices <= i + 1))[0]
        
        if len(indices) < min_bin_size:
            # Merge with previous bin if this one is too small
            if bin_data:
                # Merge logic: extend the previous bin's range
                bin_data[-1]['indices'] = np.concatenate([bin_data[-1]['indices'], indices])
                bin_data[-1]['mean_accuracy'] = float(np.mean(accuracies_sorted[bin_data[-1]['indices']]))
                bin_data[-1]['median_nodes'] = float(np.median(nodes_sorted[bin_data[-1]['indices']]))
            continue
        
        bin_data.append({
            'indices': indices,
            'mean_accuracy': float(np.mean(accuracies_sorted[indices])),
            'median_nodes': float(np.median(nodes_sorted[indices]))
        })
    
    if len(bin_data) < 2:
        return {
            "inflection_point": None,
            "correlation_coefficient": None,
            "trend_summary": "INSUFFICIENT_DATA",
            "is_significant": False,
            "p_value": None,
            "error": "Merging resulted in too few bins"
        }
    
    # Calculate threshold: 95% of baseline
    threshold = baseline_accuracy * 0.95
    
    # Find inflection point
    inflection_point = None
    trend_data = []
    
    for i, bin_info in enumerate(bin_data):
        trend_data.append({
            'bin_index': i,
            'median_nodes': bin_info['median_nodes'],
            'mean_accuracy': bin_info['mean_accuracy']
        })
        
        if inflection_point is None and bin_info['mean_accuracy'] < threshold:
            inflection_point = bin_info['median_nodes']
            break
    
    # Statistical significance test
    # Prepare data for testing: compare first half vs second half of trend
    # Or test if the trend is significantly negative
    first_half_accs = [b['mean_accuracy'] for b in bin_data[:len(bin_data)//2]]
    second_half_accs = [b['mean_accuracy'] for b in bin_data[len(bin_data)//2:]]
    
    is_significant = False
    p_value = None
    
    if len(first_half_accs) >= 3 and len(second_half_accs) >= 3:
        # Check normality
        _, p_normal_first = stats.normaltest(first_half_accs) if len(first_half_accs) >= 8 else (0, 1)
        _, p_normal_second = stats.normaltest(second_half_accs) if len(second_half_accs) >= 8 else (0, 1)
        
        use_ttest = (p_normal_first > alpha and p_normal_second > alpha) and len(first_half_accs) == len(second_half_accs)
        
        try:
            if use_ttest:
                stat, p_val = stats.ttest_ind(first_half_accs, second_half_accs)
            else:
                # Wilcoxon signed-rank test (paired) or Mann-Whitney U (unpaired)
                if len(first_half_accs) == len(second_half_accs):
                    stat, p_val = stats.wilcoxon(first_half_accs, second_half_accs)
                else:
                    stat, p_val = stats.mannwhitneyu(first_half_accs, second_half_accs, alternative='less')
            
            p_value = float(p_val)
            # Check if the second half is significantly lower than the first
            # We expect a negative trend, so we check if the difference is significant
            if p_value < alpha:
                # Verify direction: second half should be lower
                if np.mean(second_half_accs) < np.mean(first_half_accs):
                    is_significant = True
        except Exception as e:
            logger.warning(f"Statistical test failed: {e}")
            is_significant = False
            p_value = None
    
    # Calculate correlation coefficient (Spearman for monotonic relationship)
    try:
        corr, _ = stats.spearmanr(
            [b['median_nodes'] for b in bin_data],
            [b['mean_accuracy'] for b in bin_data]
        )
        correlation_coefficient = float(corr)
    except Exception:
        correlation_coefficient = None
    
    # Determine trend summary
    if correlation_coefficient is not None:
        if correlation_coefficient < -0.5:
            trend_summary = "Strong negative correlation"
        elif correlation_coefficient < -0.2:
            trend_summary = "Moderate negative correlation"
        elif correlation_coeffion_coefficient > 0.5:
            trend_summary = "Strong positive correlation"
        elif correlation_coefficient > 0.2:
            trend_summary = "Moderate positive correlation"
        else:
            trend_summary = "Weak or no correlation"
    else:
        trend_summary = "Correlation could not be calculated"
    
    # Only report inflection point if significant
    if not is_significant:
        inflection_point = None
        trend_summary = f"{trend_summary} (not statistically significant, p={p_value:.4f})"
    
    return {
        "inflection_point": inflection_point,
        "correlation_coefficient": correlation_coefficient,
        "trend_summary": trend_summary,
        "is_significant": is_significant,
        "p_value": p_value,
        "bins": trend_data,
        "threshold_used": threshold
    }

def analyze_strategy(
    strategy_name: str,
    results_file: Path,
    baseline_accuracy: float
) -> Dict[str, Any]:
    """Analyze a specific strategy against the baseline."""
    logger.info(f"Analyzing {strategy_name} strategy from {results_file}")
    
    try:
        results = load_results_from_csv(results_file)
        if not results:
            return {
                "strategy": strategy_name,
                "error": "No valid results found in file"
            }
        
        analysis = perform_bin_analysis(results, baseline_accuracy)
        analysis['strategy'] = strategy_name
        analysis['sample_size'] = len(results)
        return analysis
    
    except FileNotFoundError as e:
        logger.error(f"File not found for {strategy_name}: {e}")
        return {
            "strategy": strategy_name,
            "error": f"File not found: {results_file}"
        }
    except Exception as e:
        logger.error(f"Error analyzing {strategy_name}: {e}")
        return {
            "strategy": strategy_name,
            "error": str(e)
        }

def main():
    """Main entry point for threshold analysis."""
    parser = argparse.ArgumentParser(description="Threshold & Inflection Analysis")
    parser.add_argument(
        '--baseline',
        type=Path,
        default=Path("data/processed/baseline_results.csv"),
        help="Path to baseline results CSV"
    )
    parser.add_argument(
        '--lazy',
        type=Path,
        default=Path("data/processed/lazy_results.csv"),
        help="Path to lazy strategy results CSV"
    )
    parser.add_argument(
        '--greedy',
        type=Path,
        default=Path("data/processed/greedy_results.csv"),
        help="Path to greedy strategy results CSV"
    )
    parser.add_argument(
        '--output',
        type=Path,
        default=Path("data/processed/threshold_analysis.json"),
        help="Path to output JSON file"
    )
    
    args = parser.parse_args()
    
    # Ensure output directory exists
    args.output.parent.mkdir(parents=True, exist_ok=True)
    
    # Load baseline
    try:
        baseline_results = load_results_from_csv(args.baseline)
        baseline_accuracy = calculate_baseline_accuracy(baseline_results)
        logger.info(f"Baseline accuracy: {baseline_accuracy:.4f}")
    except Exception as e:
        logger.error(f"Failed to load baseline: {e}")
        # Create error output
        output = {
            "error": f"Failed to load baseline: {e}",
            "baseline_accuracy": None,
            "strategies": {}
        }
        with open(args.output, 'w') as f:
            json.dump(output, f, indent=2)
        return 1
    
    # Analyze strategies
    results = {
        "baseline_accuracy": baseline_accuracy,
        "strategies": {}
    }
    
    # Analyze Lazy
    lazy_analysis = analyze_strategy("lazy", args.lazy, baseline_accuracy)
    results["strategies"]["lazy"] = lazy_analysis
    
    # Analyze Greedy
    greedy_analysis = analyze_strategy("greedy", args.greedy, baseline_accuracy)
    results["strategies"]["greedy"] = greedy_analysis
    
    # Determine overall inflection point (use the most conservative)
    # If either has a significant inflection, report it
    overall_inflection = None
    overall_significant = False
    overall_p_value = None
    
    for strategy_name, analysis in results["strategies"].items():
        if "error" not in analysis and analysis.get("is_significant"):
            if overall_inflection is None or (analysis.get("inflection_point") is not None and 
                                              analysis["inflection_point"] < overall_inflection):
                overall_inflection = analysis["inflection_point"]
                overall_significant = True
                overall_p_value = analysis.get("p_value")
    
    results["overall"] = {
        "inflection_point": overall_inflection,
        "is_significant": overall_significant,
        "p_value": overall_p_value
    }
    
    # Save results
    with open(args.output, 'w') as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"Threshold analysis complete. Results saved to {args.output}")
    logger.info(f"Overall inflection point: {overall_inflection} (significant: {overall_significant})")
    
    return 0

if __name__ == "__main__":
    exit(main())