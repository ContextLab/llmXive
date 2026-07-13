import os
import json
import logging
from pathlib import Path
from typing import Dict, Any

from config import get_config_dict
from statistical_analysis import load_saa_results, load_baseline_saa, run_t_test, compute_bootstrap_ci

logger = logging.getLogger(__name__)

def load_saa_results(path: str) -> list:
    """Load SAA results from the intermediate results file."""
    with open(path, 'r') as f:
        data = json.load(f)
    # Ensure we return a list of individual result dictionaries
    if isinstance(data, list):
        return data
    elif isinstance(data, dict) and 'results' in data:
        return data['results']
    else:
        # Fallback for single result or unexpected format
        return [data]

def load_baseline_saa(path: str) -> float:
    """Load the baseline SAA scalar from the baseline file."""
    with open(path, 'r') as f:
        data = json.load(f)
    return float(data['baseline_saa'])

def compute_summary_metrics(results: list, baseline: float) -> Dict[str, Any]:
    """Compute summary statistics including mean, std, and comparison to baseline."""
    if not results:
        raise ValueError("No SAA results found to compute summary.")

    saa_scores = [r.get('saa_score', 0.0) for r in results if 'saa_score' in r]
    
    if not saa_scores:
        raise ValueError("No valid SAA scores found in results.")

    import numpy as np
    
    mean_saa = float(np.mean(saa_scores))
    std_saa = float(np.std(saa_scores))
    count = len(saa_scores)
    
    # Compute t-test against baseline
    t_stat, p_value = run_t_test(saa_scores, baseline)
    
    # Compute bootstrap confidence interval
    ci_lower, ci_upper = compute_bootstrap_ci(saa_scores, confidence=0.95)
    
    # Determine if significantly different
    is_significant = p_value < 0.05
    direction = "higher" if mean_saa > baseline else "lower" if mean_saa < baseline else "equal"
    
    return {
        "mean_saa": mean_saa,
        "std_saa": std_saa,
        "sample_count": count,
        "baseline_saa": baseline,
        "difference_from_baseline": mean_saa - baseline,
        "t_statistic": t_stat,
        "p_value": p_value,
        "is_significant": is_significant,
        "comparison_direction": direction,
        "bootstrap_95_ci": {
            "lower": ci_lower,
            "upper": ci_upper
        }
    }

def save_summary(summary: Dict[str, Any], output_path: str):
    """Save the summary dictionary to a JSON file."""
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_file, 'w') as f:
        json.dump(summary, f, indent=2)
    
    logger.info(f"Saved SAA summary to {output_path}")

def main():
    """Main entry point to generate the SAA summary."""
    config = get_config_dict()
    
    # Define paths based on config
    results_path = Path(config['paths']['data_results']) / 'text_pipeline_results.json'
    baseline_path = Path(config['paths']['data_processed']) / 'baseline_saa.json'
    summary_path = Path(config['paths']['data_results']) / 'saa_summary.json'
    
    logger.info(f"Loading SAA results from {results_path}")
    results = load_saa_results(str(results_path))
    
    logger.info(f"Loading baseline SAA from {baseline_path}")
    baseline = load_baseline_saa(str(baseline_path))
    
    logger.info("Computing summary metrics...")
    summary = compute_summary_metrics(results, baseline)
    
    logger.info("Saving summary...")
    save_summary(summary, str(summary_path))
    
    return summary

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()