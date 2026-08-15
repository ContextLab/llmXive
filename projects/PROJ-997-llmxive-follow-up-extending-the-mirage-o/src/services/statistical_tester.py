import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional
from dataclasses import dataclass, asdict
import numpy as np
from scipy import stats

from src.config.logging_config import setup_logger

logger = setup_logger(__name__)

@dataclass
class TTestResult:
    statistic: float
    p_value: float
    method: str
    n_samples: int
    correction_factor: float
    adjusted_alpha: float

@dataclass
class StatisticalComparisonReport:
    acceptance_rate_test: TTestResult
    reasoning_score_test: TTestResult
    bonferroni_alpha_threshold: float
    conclusion: str

def load_metrics_from_json(file_path: str) -> Dict[str, Any]:
    """Load metrics from a JSON file."""
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Metrics file not found: {file_path}")
    
    with open(path, 'r') as f:
        return json.load(f)

def perform_paired_ttest(
    proxy_values: List[float],
    baseline_values: List[float],
    metric_name: str,
    alpha: float = 0.05,
    n_tests: int = 2
) -> TTestResult:
    """
    Perform a paired t-test between proxy and baseline metrics.
    Applies Bonferroni correction for multiple comparisons.
    
    Args:
        proxy_values: List of values from the proxy policy
        baseline_values: List of values from the baseline policy
        metric_name: Name of the metric being tested
        alpha: Significance level before correction
        n_tests: Number of tests being performed (for Bonferroni)
    
    Returns:
        TTestResult containing statistic, p-value, and metadata
    """
    if len(proxy_values) != len(baseline_values):
        raise ValueError("Proxy and baseline values must have the same length")
    
    if len(proxy_values) < 2:
        raise ValueError("Need at least 2 samples for t-test")
    
    # Perform paired t-test
    statistic, p_value = stats.ttest_rel(baseline_values, proxy_values)
    
    # Bonferroni correction
    correction_factor = n_tests
    adjusted_p_value = min(p_value * correction_factor, 1.0)
    adjusted_alpha = alpha / correction_factor
    
    logger.info(
        f"{metric_name} t-test: statistic={statistic:.4f}, "
        f"raw_p={p_value:.4f}, adjusted_p={adjusted_p_value:.4f}, "
        f"adjusted_alpha={adjusted_alpha:.4f}"
    )
    
    return TTestResult(
        statistic=float(statistic),
        p_value=float(adjusted_p_value),
        method="bonferroni_corrected_t_test",
        n_samples=len(proxy_values),
        correction_factor=float(correction_factor),
        adjusted_alpha=float(adjusted_alpha)
    )

def run_statistical_comparison(
    baseline_file: str,
    proxy_file: str,
    output_file: str
) -> StatisticalComparisonReport:
    """
    Run the full statistical comparison pipeline.
    
    Args:
        baseline_file: Path to baseline_metrics.json
        proxy_file: Path to proxy_metrics.json
        output_file: Path to write t_test_results.json
    
    Returns:
        StatisticalComparisonReport with all test results
    """
    logger.info(f"Loading baseline metrics from {baseline_file}")
    baseline_data = load_metrics_from_json(baseline_file)
    
    logger.info(f"Loading proxy metrics from {proxy_file}")
    proxy_data = load_metrics_from_json(proxy_file)
    
    # Extract lists for paired comparison
    # We expect these to be lists of per-sample or per-run values
    # If the input files contain single aggregated values, we cannot do a t-test
    # Assuming the files contain lists of values from multiple runs/samples
    
    baseline_acceptance = baseline_data.get('acceptance_rates', [])
    proxy_acceptance = proxy_data.get('acceptance_rates', [])
    baseline_scores = baseline_data.get('reasoning_scores', [])
    proxy_scores = proxy_data.get('reasoning_scores', [])
    
    # Fallback: If single values are provided, wrap them in a list (though t-test needs >1 sample)
    # In a real scenario, these should be lists from multiple samples or runs
    if not baseline_acceptance or not isinstance(baseline_acceptance, list):
        raise ValueError(f"baseline_metrics.json must contain 'acceptance_rates' as a list")
    if not proxy_acceptance or not isinstance(proxy_acceptance, list):
        raise ValueError(f"proxy_metrics.json must contain 'acceptance_rates' as a list")
    if not baseline_scores or not isinstance(baseline_scores, list):
        raise ValueError(f"baseline_metrics.json must contain 'reasoning_scores' as a list")
    if not proxy_scores or not isinstance(proxy_scores, list):
        raise ValueError(f"proxy_metrics.json must contain 'reasoning_scores' as a list")
    
    # Perform t-tests
    acceptance_test = perform_paired_ttest(
        proxy_acceptance, 
        baseline_acceptance, 
        "Acceptance Rate"
    )
    
    reasoning_test = perform_paired_ttest(
        proxy_scores, 
        baseline_scores, 
        "Reasoning Score"
    )
    
    # Determine conclusion
    alpha_threshold = 0.05 / 2  # Bonferroni for 2 tests
    if acceptance_test.p_value < alpha_threshold or reasoning_test.p_value < alpha_threshold:
        conclusion = "Significant difference detected between proxy and baseline policies."
    else:
        conclusion = "No statistically significant difference detected between proxy and baseline policies."
    
    report = StatisticalComparisonReport(
        acceptance_rate_test=acceptance_test,
        reasoning_score_test=reasoning_test,
        bonferroni_alpha_threshold=alpha_threshold,
        conclusion=conclusion
    )
    
    # Write results to JSON
    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    result_dict = {
        "p_value": acceptance_test.p_value,
        "statistic": acceptance_test.statistic,
        "method": "bonferroni_corrected_t_test",
        "details": {
            "acceptance_rate": asdict(acceptance_test),
            "reasoning_score": asdict(reasoning_test),
            "bonferroni_alpha_threshold": alpha_threshold,
            "conclusion": conclusion
        }
    }
    
    with open(output_path, 'w') as f:
        json.dump(result_dict, f, indent=2)
    
    logger.info(f"Statistical comparison results written to {output_file}")
    return report

def main():
    """Main entry point for T029."""
    baseline_path = "data/processed/baseline_metrics.json"
    proxy_path = "data/processed/proxy_metrics.json"
    output_path = "data/processed/t_test_results.json"
    
    try:
        report = run_statistical_comparison(baseline_path, proxy_path, output_path)
        logger.info(f"Test completed. Conclusion: {report.conclusion}")
        print(f"Results written to {output_path}")
        print(f"Conclusion: {report.conclusion}")
    except FileNotFoundError as e:
        logger.error(f"Missing input file: {e}")
        raise
    except ValueError as e:
        logger.error(f"Invalid data format: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error during statistical comparison: {e}")
        raise

if __name__ == "__main__":
    main()