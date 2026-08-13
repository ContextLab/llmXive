"""
Statistical testing services for MIPU policy comparison.
Performs paired t-tests on acceptance rates and final scores with Bonferroni correction.
"""
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
    """Container for a single t-test result."""
    metric_name: str
    t_statistic: float
    p_value: float
    bonferroni_p_value: float
    significant_at_alpha_005: bool
    significant_at_bonferroni: bool
    n_samples: int
    mean_diff: float
    std_diff: float

@dataclass
class StatisticalComparisonReport:
    """Container for the full statistical comparison report."""
    test_type: str
    n_samples: int
    baseline_mean: float
    proxy_mean: float
    t_test_results: List[TTestResult]
    bonferroni_alpha: float
    conclusion: str
    artifacts_path: str

def load_metrics_from_json(file_path: Path) -> Dict[str, Any]:
    """
    Load metrics from a JSON file.
    Expects a structure containing 'acceptance_rates' (list) and 'final_scores' (list).
    """
    if not file_path.exists():
        raise FileNotFoundError(f"Metrics file not found: {file_path}")
    
    with open(file_path, 'r') as f:
        data = json.load(f)
    
    if 'acceptance_rates' not in data or 'final_scores' not in data:
        raise ValueError(
            f"Invalid metrics format in {file_path}. "
            "Expected keys 'acceptance_rates' and 'final_scores'."
        )
    
    return data

def perform_paired_ttest(
    baseline_values: List[float], 
    proxy_values: List[float],
    metric_name: str
) -> TTestResult:
    """
    Perform a paired t-test between baseline and proxy metrics.
    Applies Bonferroni correction for multiple comparisons.
    """
    if len(baseline_values) != len(proxy_values):
        raise ValueError(
            f"Mismatched sample sizes for {metric_name}: "
            f"Baseline={len(baseline_values)}, Proxy={len(proxy_values)}"
        )
    
    if len(baseline_values) < 2:
        raise ValueError(
            f"Insufficient samples for t-test on {metric_name}. "
            f"Need at least 2, got {len(baseline_values)}."
        )

    # Calculate differences
    differences = np.array(proxy_values) - np.array(baseline_values)
    mean_diff = np.mean(differences)
    std_diff = np.std(differences, ddof=1)
    n_samples = len(differences)

    # Perform paired t-test
    t_stat, p_value = stats.ttest_rel(baseline_values, proxy_values)

    # Bonferroni correction (assuming 2 tests: acceptance rate and final score)
    # If this function is called multiple times, the caller should handle the global correction.
    # Here we apply a local correction assuming 2 comparisons for this specific report.
    n_comparisons = 2 
    bonferroni_p = min(p_value * n_comparisons, 1.0)

    alpha = 0.05
    significant_at_alpha = p_value < alpha
    significant_at_bonferroni = bonferroni_p < alpha

    return TTestResult(
        metric_name=metric_name,
        t_statistic=float(t_stat),
        p_value=float(p_value),
        bonferroni_p_value=float(bonferroni_p),
        significant_at_alpha_005=significant_at_alpha,
        significant_at_bonferroni=significant_at_bonferroni,
        n_samples=n_samples,
        mean_diff=float(mean_diff),
        std_diff=float(std_diff)
    )

def run_statistical_comparison(
    baseline_metrics_path: Path,
    proxy_metrics_path: Path,
    output_path: Path
) -> StatisticalComparisonReport:
    """
    Main entry point for statistical comparison.
    Loads baseline and proxy metrics, performs paired t-tests,
    applies Bonferroni correction, and saves results to JSON.
    """
    logger.info(f"Loading baseline metrics from: {baseline_metrics_path}")
    baseline_data = load_metrics_from_json(baseline_metrics_path)
    
    logger.info(f"Loading proxy metrics from: {proxy_metrics_path}")
    proxy_data = load_metrics_from_json(proxy_metrics_path)

    baseline_acceptance = baseline_data['acceptance_rates']
    proxy_acceptance = proxy_data['acceptance_rates']
    baseline_scores = baseline_data['final_scores']
    proxy_scores = proxy_data['final_scores']

    logger.info(f"Performing paired t-test on acceptance rates (n={len(baseline_acceptance)})")
    t_test_acceptance = perform_paired_ttest(
        baseline_acceptance, proxy_acceptance, "acceptance_rate"
    )

    logger.info(f"Performing paired t-test on final scores (n={len(baseline_scores)})")
    t_test_scores = perform_paired_ttest(
        baseline_scores, proxy_scores, "final_score"
    )

    results = [t_test_acceptance, t_test_scores]
    
    # Determine conclusion
    # We are testing if the proxy policy is statistically equivalent or better.
    # Typically, we look for p > 0.05 (no significant difference) or specific direction.
    # Based on the task description: "paired t-test result (p > 0.05) comparing policy acceptance rates"
    # implies we want to show they are not significantly different (or that the proxy is valid).
    # However, usually in optimization, we want improvement. The task says "compare", 
    # and the checkpoint says "p > 0.05" which suggests equivalence testing or lack of degradation.
    # Let's assume the goal is to show the proxy is comparable (p > 0.05 for difference).
    
    non_significant_count = sum(1 for r in results if r.significant_at_bonferroni == False)
    
    if non_significant_count == len(results):
        conclusion = "No statistically significant difference found between Proxy and Baseline policies after Bonferroni correction."
    else:
        significant_metrics = [r.metric_name for r in results if r.significant_at_bonferroni]
        conclusion = f"Statistically significant differences found in: {', '.join(significant_metrics)}."

    report = StatisticalComparisonReport(
        test_type="Paired T-Test with Bonferroni Correction",
        n_samples=len(baseline_acceptance),
        baseline_mean=float(np.mean(baseline_acceptance)),
        proxy_mean=float(np.mean(proxy_acceptance)),
        t_test_results=results,
        bonferroni_alpha=0.05 / 2, # 2 comparisons
        conclusion=conclusion,
        artifacts_path=str(output_path)
    )

    # Convert to serializable dict
    report_dict = {
        "test_type": report.test_type,
        "n_samples": report.n_samples,
        "baseline_mean_acceptance_rate": report.baseline_mean,
        "proxy_mean_acceptance_rate": report.proxy_mean,
        "bonferroni_alpha_threshold": report.bonferroni_alpha,
        "conclusion": report.conclusion,
        "test_results": [asdict(r) for r in report.t_test_results],
        "artifacts_path": report.artifacts_path
    }

    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w') as f:
        json.dump(report_dict, f, indent=2)

    logger.info(f"Statistical comparison results saved to: {output_path}")
    logger.info(f"Conclusion: {conclusion}")

    return report

def main():
    """CLI entry point for T029."""
    # Default paths relative to project root
    base_path = Path(__file__).parent.parent.parent.parent
    baseline_path = base_path / "data" / "processed" / "baseline_metrics.json"
    proxy_path = base_path / "data" / "processed" / "proxy_metrics.json"
    output_path = base_path / "data" / "processed" / "t_test_results.json"

    logger.info("Starting Statistical Comparison (T029)...")
    
    try:
        run_statistical_comparison(baseline_path, proxy_path, output_path)
        logger.info("T029 completed successfully.")
    except FileNotFoundError as e:
        logger.error(f"Missing required input file: {e}")
        raise
    except ValueError as e:
        logger.error(f"Data validation error: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error during statistical testing: {e}")
        raise

if __name__ == "__main__":
    main()