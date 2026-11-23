import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional
from dataclasses import dataclass, asdict
import numpy as np
from scipy import stats

@dataclass
class TTestResult:
    statistic: float
    pvalue: float
    method: str

@dataclass
class StatisticalComparisonReport:
    t_test_result: TTestResult
    bonferroni_adjusted_alpha: float
    is_significant: bool
    raw_metrics: Dict[str, Any]

logger = logging.getLogger(__name__)

def load_metrics_from_json(file_path: Path) -> Tuple[List[float], List[float]]:
    """
    Loads baseline and proxy metrics from JSON files.
    Expects files with 'acceptance_rate' and 'reasoning_score'.
    Returns two lists: baseline_rates, proxy_rates.
    """
    with open(file_path, 'r') as f:
        data = json.load(f)
    
    # Assuming the file contains a list of samples or aggregated metrics
    # For T029, we assume we are comparing a list of acceptance rates or scores
    # If the file structure is different, adjust accordingly.
    # Based on T027/T028, we expect a list of results or a single aggregated result.
    # For the t-test, we need paired samples.
    # Let's assume the input files contain lists of per-sample metrics or we aggregate them.
    # If the file has 'acceptance_rate' as a single float, we cannot do a t-test on a single value.
    # The task T027/T028 implies running on a test set (multiple samples).
    # We assume the JSON file contains a list of 'samples' with 'acceptance_rate'.
    
    if 'samples' in data:
        rates = [s['acceptance_rate'] for s in data['samples']]
        scores = [s['reasoning_score'] for s in data['samples']]
    elif 'acceptance_rate' in data and isinstance(data['acceptance_rate'], list):
        rates = data['acceptance_rate']
        scores = data.get('reasoning_score', [])
    else:
        # Fallback for single value (should not happen for t-test)
        raise ValueError("Input JSON must contain a list of samples or lists of metrics for t-test.")
        
    return rates, scores

def perform_paired_ttest(group_a: List[float], group_b: List[float], alpha: float = 0.05) -> TTestResult:
    """
    Performs a paired t-test between two groups.
    Applies Bonferroni correction if multiple tests are performed (handled externally).
    """
    if len(group_a) != len(group_b):
        raise ValueError("Groups must be of equal length for paired t-test.")
    if len(group_a) < 2:
        raise ValueError("Need at least 2 samples for t-test.")

    statistic, pvalue = stats.ttest_rel(group_a, group_b)
    
    return TTestResult(
        statistic=statistic,
        pvalue=pvalue,
        method="paired_t_test"
    )

def run_statistical_comparison(
    baseline_path: Path,
    proxy_path: Path,
    output_path: Path,
    alpha: float = 0.05
) -> StatisticalComparisonReport:
    """
    Runs the full statistical comparison pipeline:
    1. Load metrics from baseline and proxy JSON files.
    2. Perform paired t-test on acceptance rates and reasoning scores.
    3. Apply Bonferroni correction (adjusting alpha for 2 tests: rate and score).
    4. Write results to output JSON.
    """
    logger.info(f"Loading metrics from {baseline_path} and {proxy_path}")
    
    baseline_rates, baseline_scores = load_metrics_from_json(baseline_path)
    proxy_rates, proxy_scores = load_metrics_from_json(proxy_path)
    
    # Ensure lengths match
    min_len = min(len(baseline_rates), len(proxy_rates))
    if min_len < 2:
        raise ValueError("Insufficient samples for statistical comparison.")
        
    baseline_rates = baseline_rates[:min_len]
    proxy_rates = proxy_rates[:min_len]
    baseline_scores = baseline_scores[:min_len] if baseline_scores else [0.0]*min_len
    proxy_scores = proxy_scores[:min_len] if proxy_scores else [0.0]*min_len

    # Bonferroni correction for 2 tests (rate and score)
    adjusted_alpha = alpha / 2.0

    # Test 1: Acceptance Rates
    t_test_rate = perform_paired_ttest(baseline_rates, proxy_rates)
    # Test 2: Reasoning Scores
    t_test_score = perform_paired_ttest(baseline_scores, proxy_scores)

    # We need to decide which p-value to report or aggregate.
    # The task asks for a single t_test_results.json. We will report the rate test as primary
    # or combine them. Let's report the rate test as it's the primary metric.
    # Or we can report both. The schema in T029 says: {"p_value": float, "statistic": float, "method": ...}
    # We'll use the acceptance rate test result for the main report.
    
    result = TTestResult(
        statistic=t_test_rate.statistic,
        pvalue=t_test_rate.pvalue,
        method="bonferroni_corrected_t_test"
    )

    report = StatisticalComparisonReport(
        t_test_result=result,
        bonferroni_adjusted_alpha=adjusted_alpha,
        is_significant=result.pvalue < adjusted_alpha,
        raw_metrics={
            "acceptance_rate": {"t": t_test_rate.statistic, "p": t_test_rate.pvalue},
            "reasoning_score": {"t": t_test_score.statistic, "p": t_test_score.pvalue}
        }
    )

    # Write to output
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(asdict(report), f, indent=2)
    
    logger.info(f"Statistical comparison results written to {output_path}")
    return report

def main():
    """CLI entry point for statistical testing."""
    import argparse
    parser = argparse.ArgumentParser(description="Run statistical comparison between baseline and proxy.")
    parser.add_argument("--baseline", type=Path, required=True, help="Path to baseline_metrics.json")
    parser.add_argument("--proxy", type=Path, required=True, help="Path to proxy_metrics.json")
    parser.add_argument("--output", type=Path, default=Path("data/processed/t_test_results.json"), help="Output path")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO)
    run_statistical_comparison(args.baseline, args.proxy, args.output)

if __name__ == "__main__":
    main()
