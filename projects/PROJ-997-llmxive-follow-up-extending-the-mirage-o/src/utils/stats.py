"""
Statistical analysis utilities for MIPU gap validation.
Implements paired t-tests with Bonferroni correction.
"""
import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional
import numpy as np
from scipy import stats
from dataclasses import dataclass, asdict

@dataclass
class TTestResult:
    """Result of a paired t-test."""
    statistic: float
    p_value: float
    method: str

@dataclass
class StatisticalComparisonReport:
    """Full report of statistical comparisons."""
    acceptance_rate_test: Dict[str, float]
    reasoning_score_test: Dict[str, float]
    method: str
    adjusted_alpha: float

def load_metrics_from_json(filepath: Path, key: str) -> List[float]:
    """
    Load a specific list of metrics from a JSON file.
    
    Args:
        filepath: Path to the JSON file.
        key: The key in the JSON object containing the list of values.
        
    Returns:
        List of float values.
        
    Raises:
        FileNotFoundError: If the file does not exist.
        KeyError: If the key is missing in the JSON.
        ValueError: If the values are not a list of numbers.
    """
    if not filepath.exists():
        raise FileNotFoundError(f"Metrics file not found: {filepath}")
        
    with open(filepath, 'r') as f:
        data = json.load(f)
        
    if key not in data:
        raise KeyError(f"Key '{key}' not found in {filepath}. Available keys: {list(data.keys())}")
        
    values = data[key]
    if not isinstance(values, list):
        raise ValueError(f"Expected list for key '{key}', got {type(values)}")
        
    return [float(v) for v in values]

def perform_paired_ttest(
    baseline_values: List[float], 
    proxy_values: List[float],
    test_name: str
) -> TTestResult:
    """
    Perform a paired t-test between two sets of values.
    
    Args:
        baseline_values: List of values from the baseline policy.
        proxy_values: List of values from the proxy policy.
        test_name: Name of the metric being tested (for logging).
        
    Returns:
        TTestResult object containing statistic, p-value, and method.
        
    Raises:
        ValueError: If the input lists have different lengths or insufficient samples.
    """
    if len(baseline_values) != len(proxy_values):
        raise ValueError(
            f"Length mismatch for {test_name}: baseline={len(baseline_values)}, proxy={len(proxy_values)}"
        )
    
    if len(baseline_values) < 2:
        raise ValueError(
            f"Insufficient samples for {test_name}: need at least 2, got {len(baseline_values)}"
        )
        
    # scipy.stats.ttest_rel performs a paired t-test
    statistic, p_value = stats.ttest_rel(baseline_values, proxy_values)
    
    logging.info(f"Paired t-test for {test_name}: statistic={statistic:.4f}, p-value={p_value:.4f}")
    
    return TTestResult(
        statistic=float(statistic),
        p_value=float(p_value),
        method="paired_t_test"
    )

def apply_bonferroni_correction(p_values: List[float], alpha: float = 0.05) -> Tuple[List[float], float]:
    """
    Apply Bonferroni correction to a list of p-values.
    
    Args:
        p_values: List of raw p-values.
        alpha: Significance level (default 0.05).
        
    Returns:
        Tuple of (adjusted_p_values, adjusted_alpha).
    """
    n_tests = len(p_values)
    if n_tests == 0:
        return [], alpha
        
    adjusted_alpha = alpha / n_tests
    adjusted_p_values = [min(p * n_tests, 1.0) for p in p_values]
    
    logging.info(f"Bonferroni correction: {n_tests} tests, adjusted alpha={adjusted_alpha:.4f}")
    return adjusted_p_values, adjusted_alpha

def run_statistical_comparison(
    baseline_metrics_path: Path,
    proxy_metrics_path: Path,
    output_path: Path
) -> StatisticalComparisonReport:
    """
    Run the full statistical comparison pipeline:
    1. Load acceptance rates and reasoning scores from baseline and proxy metrics.
    2. Perform paired t-tests on both metrics.
    3. Apply Bonferroni correction.
    4. Write results to JSON.
    
    Args:
        baseline_metrics_path: Path to baseline_metrics.json.
        proxy_metrics_path: Path to proxy_metrics.json.
        output_path: Path to write t_test_results.json.
        
    Returns:
        StatisticalComparisonReport object.
    """
    logging.info("Starting statistical comparison (T029)")
    
    # Load data
    baseline_acceptance = load_metrics_from_json(baseline_metrics_path, "acceptance_rates")
    proxy_acceptance = load_metrics_from_json(proxy_metrics_path, "acceptance_rates")
    
    baseline_reasoning = load_metrics_from_json(baseline_metrics_path, "reasoning_scores")
    proxy_reasoning = load_metrics_from_json(proxy_metrics_path, "reasoning_scores")
    
    # Perform t-tests
    acceptance_test = perform_paired_ttest(baseline_acceptance, proxy_acceptance, "acceptance_rate")
    reasoning_test = perform_paired_ttest(baseline_reasoning, proxy_reasoning, "reasoning_score")
    
    # Apply Bonferroni correction
    raw_p_values = [acceptance_test.p_value, reasoning_test.p_value]
    adjusted_p_values, adjusted_alpha = apply_bonferroni_correction(raw_p_values)
    
    # Prepare results
    results = {
        "acceptance_rate": {
            "statistic": acceptance_test.statistic,
            "p_value": adjusted_p_values[0],
            "raw_p_value": acceptance_test.p_value,
            "significant": adjusted_p_values[0] < adjusted_alpha
        },
        "reasoning_score": {
            "statistic": reasoning_test.statistic,
            "p_value": adjusted_p_values[1],
            "raw_p_value": reasoning_test.p_value,
            "significant": adjusted_p_values[1] < adjusted_alpha
        },
        "method": "bonferroni_corrected_t_test",
        "adjusted_alpha": adjusted_alpha,
        "n_tests": 2
    }
    
    # Write output
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
        
    logging.info(f"Statistical comparison results written to {output_path}")
    
    return StatisticalComparisonReport(
        acceptance_rate_test=results["acceptance_rate"],
        reasoning_score_test=results["reasoning_score"],
        method=results["method"],
        adjusted_alpha=results["adjusted_alpha"]
    )

def main():
    """CLI entry point for T029."""
    import argparse
    from pathlib import Path
    
    parser = argparse.ArgumentParser(description="T029: Statistical Comparison with Bonferroni Correction")
    parser.add_argument("--baseline", type=Path, default=Path("data/processed/baseline_metrics.json"),
                      help="Path to baseline metrics JSON")
    parser.add_argument("--proxy", type=Path, default=Path("data/processed/proxy_metrics.json"),
                      help="Path to proxy metrics JSON")
    parser.add_argument("--output", type=Path, default=Path("data/processed/t_test_results.json"),
                      help="Path to output results JSON")
    
    args = parser.parse_args()
    
    logging.basicConfig(level=logging.INFO)
    
    try:
        report = run_statistical_comparison(args.baseline, args.proxy, args.output)
        print(f"Statistical comparison complete. Results saved to {args.output}")
        print(f"Acceptance Rate: p={report.acceptance_rate_test['p_value']:.4f} (adj), sig={report.acceptance_rate_test['significant']}")
        print(f"Reasoning Score: p={report.reasoning_score_test['p_value']:.4f} (adj), sig={report.reasoning_score_test['significant']}")
    except Exception as e:
        logging.error(f"Statistical comparison failed: {e}")
        raise

if __name__ == "__main__":
    main()
