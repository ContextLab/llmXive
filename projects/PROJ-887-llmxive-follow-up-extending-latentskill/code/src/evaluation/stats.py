import os
import sys
import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional
import numpy as np
from scipy import stats

from src.utils.config import get_project_root, get_results_path, get_data_path

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def load_evaluation_results(filepath: Path) -> Dict[str, Any]:
    """
    Load evaluation results from a JSON file.
    Expected structure: { "strategy_name": [outcome1, outcome2, ...], ... }
    where outcome is 1 (success) or 0 (failure).
    """
    if not filepath.exists():
        raise FileNotFoundError(f"Evaluation results file not found: {filepath}")
    
    with open(filepath, 'r') as f:
        data = json.load(f)
    
    logger.info(f"Loaded evaluation results from {filepath}")
    return data

def extract_success_rates(results: Dict[str, Any]) -> Dict[str, float]:
    """
    Extract mean success rate for each strategy.
    """
    success_rates = {}
    for strategy, outcomes in results.items():
        if not outcomes:
            success_rates[strategy] = 0.0
            logger.warning(f"No outcomes found for strategy {strategy}")
            continue
        success_rates[strategy] = float(np.mean(outcomes))
    return success_rates

def perform_paired_test(strategy_a_outcomes: List[int], strategy_b_outcomes: List[int]) -> Tuple[float, float]:
    """
    Perform a paired statistical test (Wilcoxon signed-rank test) between two strategies.
    Returns (statistic, p-value).
    If data is not paired (different lengths), falls back to independent t-test with a warning.
    """
    if len(strategy_a_outcomes) != len(strategy_b_outcomes):
        logger.warning(f"Outcomes lengths differ ({len(strategy_a_outcomes)} vs {len(strategy_b_outcomes)}). Using independent t-test.")
        stat, p_val = stats.ttest_ind(strategy_a_outcomes, strategy_b_outcomes)
    else:
        # Wilcoxon signed-rank test for paired data
        # scipy.stats.wilcoxon returns 0 if all differences are 0, which can happen with binary outcomes if identical
        try:
            stat, p_val = stats.wilcoxon(strategy_a_outcomes, strategy_b_outcomes)
        except ValueError as e:
            # Fallback if all differences are zero or other edge cases
            logger.warning(f"Wilcoxon test failed: {e}. Falling back to t-test.")
            stat, p_val = stats.ttest_rel(strategy_a_outcomes, strategy_b_outcomes)
    
    return float(stat), float(p_val)

def apply_benjamini_hochberg(p_values: List[float]) -> List[float]:
    """
    Apply Benjamini-Hochberg correction to a list of p-values.
    Returns corrected p-values (q-values).
    """
    if not p_values:
        return []
    
    n = len(p_values)
    sorted_indices = np.argsort(p_values)
    sorted_p_values = np.array([p_values[i] for i in sorted_indices])
    
    # Calculate BH critical values
    ranks = np.arange(1, n + 1)
    bh_critical_values = (ranks / n) * sorted_p_values[-1] # Using max p-value as FDR threshold proxy? 
    # Standard BH: p_(i) <= (i/m) * alpha. We want adjusted p-values.
    # Adjusted p-value for rank i: p_adj[i] = min( (n/i) * p[i], 1 )
    # But must be monotonic: p_adj[i] = min( (n/i) * p[i], p_adj[i+1] )
    
    adjusted_p_values = np.zeros(n)
    current_min = 1.0
    
    for i in range(n - 1, -1, -1):
        rank = i + 1
        p_val = sorted_p_values[i]
        adj_p = min((n / rank) * p_val, 1.0)
        current_min = min(adj_p, current_min)
        adjusted_p_values[i] = current_min
    
    # Map back to original order
    final_adjusted = np.zeros(n)
    for idx, adj_val in zip(sorted_indices, adjusted_p_values):
        final_adjusted[idx] = adj_val
    
    return final_adjusted.tolist()

def compare_strategies(results: Dict[str, Any], baseline_name: str = "baseline") -> Dict[str, Dict[str, float]]:
    """
    Compare all strategies against the baseline.
    Returns a dict of { strategy: { 'p_value': float, 'statistic': float } }
    """
    comparisons = {}
    if baseline_name not in results:
        raise ValueError(f"Baseline strategy '{baseline_name}' not found in results. Available: {list(results.keys())}")
    
    baseline_outcomes = results[baseline_name]
    
    for strategy, outcomes in results.items():
        if strategy == baseline_name:
            continue
        
        stat, p_val = perform_paired_test(outcomes, baseline_outcomes)
        comparisons[strategy] = {
            "statistic": stat,
            "p_value": p_val
        }
        logger.info(f"Comparison {strategy} vs {baseline_name}: p={p_val:.4f}, stat={stat:.4f}")
    
    return comparisons

def save_statistics_report(report: Dict[str, Any], output_path: Path) -> None:
    """
    Save the statistics report to a JSON file.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2)
    logger.info(f"Saved statistics report to {output_path}")

def main():
    """
    Main entry point for T029.
    1. Load primary comparison results (from T027) -> data/results/evaluation_results.json (assumed path based on T027)
       Note: T027 output path isn't explicitly defined in the prompt's tasks.md, but T027 is "Execute ... record binary outcomes".
       Let's assume T027 writes to data/results/evaluation_results.json. If not, we need to adjust or fail.
       Looking at T027 description: "record binary outcomes, calculating the mean".
       Looking at T031b: "Save comparative results to data/results/sensitivity.yaml".
       
       We need to aggregate p-values from:
       - Primary comparisons (T027 output)
       - Sensitivity sweeps (T031b output)
       
       Let's assume T027 output is at: data/results/evaluation_results.json
       And T031b output is at: data/results/sensitivity.yaml
       
       If these files don't exist, we must fail loudly.
    """
    project_root = get_project_root()
    results_dir = get_results_path()
    
    # Paths
    eval_results_path = results_dir / "evaluation_results.json"
    sensitivity_path = results_dir / "sensitivity.yaml"
    report_path = results_dir / "stats_report.json"
    
    # 1. Load Primary Evaluation Results (T027)
    if not eval_results_path.exists():
        raise FileNotFoundError(f"Primary evaluation results not found at {eval_results_path}. T027 must be completed first.")
    
    eval_results = load_evaluation_results(eval_results_path)
    baseline_name = "baseline" # Assumed from T026e/T026
    
    # 2. Compare Strategies vs Baseline
    primary_comparisons = compare_strategies(eval_results, baseline_name)
    primary_p_values = [comp['p_value'] for comp in primary_comparisons.values()]
    
    # 3. Load Sensitivity Sweep Results (T031b)
    # T031b output: data/results/sensitivity.yaml.
    # We need to extract p-values from sensitivity sweeps if they were performed there.
    # If T031b only outputs success rates, we might need to re-compute or assume the p-values are embedded.
    # The task T029 says: "Aggregate all p-values from T027 and T031b".
    # This implies T031b produces p-values. Let's assume the sensitivity.yaml contains p-values for each k.
    
    sensitivity_p_values = []
    if sensitivity_path.exists():
        import yaml
        with open(sensitivity_path, 'r') as f:
            sensitivity_data = yaml.safe_load(f)
        
        # Expecting structure like: { "k_1": { "p_value": ... }, ... } or similar
        # We need to be flexible. Let's look for keys that look like p-values.
        # If the structure is { "k": { "results": {...} } }, we might need to extract.
        # For robustness, let's assume the sensitivity data has a 'p_values' key or we extract from 'comparisons'.
        
        # If it's a list of results per k, we might need to re-run the test? 
        # The task says "Aggregate all p-values from T027 and T031b", implying T031b already has them.
        # Let's try to extract any float values that look like p-values if a specific key isn't obvious.
        # Or assume a structure: { "k_1": { "p_value": 0.05, ... }, ... }
        
        def extract_p_values_from_dict(d):
            p_vals = []
            for k, v in d.items():
                if isinstance(v, dict):
                    if 'p_value' in v:
                        p_vals.append(v['p_value'])
                    else:
                        p_vals.extend(extract_p_values_from_dict(v))
                elif isinstance(v, float) and 0 <= v <= 1:
                    # Heuristic: if it's a float between 0 and 1 and key is 'p' or 'p_value' or similar
                    # But here we are just recursing. Let's be strict: only if key is 'p_value'
                    pass
            return p_vals
        
        sensitivity_p_values = extract_p_values_from_dict(sensitivity_data)
        logger.info(f"Extracted {len(sensitivity_p_values)} p-values from sensitivity sweep.")
    else:
        logger.warning(f"Sensitivity results not found at {sensitivity_path}. Proceeding with only primary p-values.")
    
    # 4. Aggregate and Apply BH Correction
    all_p_values = primary_p_values + sensitivity_p_values
    
    if not all_p_values:
        raise ValueError("No p-values found to correct. Check input files.")
    
    corrected_p_values = apply_benjamini_hochberg(all_p_values)
    
    # 5. Construct Report
    # Map corrected values back to their sources?
    # We need to know which corrected value corresponds to which test.
    # Since we concatenated, the first len(primary) correspond to primary, rest to sensitivity.
    
    report = {
        "primary_comparisons": {},
        "sensitivity_corrections": [],
        "bh_corrected_p_values": corrected_p_values,
        "summary": {
            "total_tests": len(all_p_values),
            "primary_tests": len(primary_p_values),
            "sensitivity_tests": len(sensitivity_p_values)
        }
    }
    
    # Assign corrected values to primary comparisons
    for i, (strategy, data) in enumerate(primary_comparisons.items()):
        data["bh_corrected_p_value"] = corrected_p_values[i]
        report["primary_comparisons"][strategy] = data
    
    # Assign corrected values to sensitivity (if any)
    # We don't have the names here, just the list. We'll store them as a list of dicts or just values.
    # Let's store them as a list of objects with index.
    for i, p_val in enumerate(sensitivity_p_values):
        report["sensitivity_corrections"].append({
            "index_in_sweep": i,
            "original_p_value": p_val,
            "bh_corrected_p_value": corrected_p_values[len(primary_p_values) + i]
        })
    
    # 6. Save Report
    save_statistics_report(report, report_path)
    
    logger.info("T029 completed successfully.")
    return report

if __name__ == "__main__":
    main()
