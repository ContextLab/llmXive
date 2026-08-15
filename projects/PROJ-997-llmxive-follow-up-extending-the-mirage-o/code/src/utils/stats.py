import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional

import numpy as np
from scipy import stats

from src.config.logging_config import setup_logger, ensure_log_dir

logger = setup_logger(__name__)


class TTestResult:
    """Container for paired t-test results."""

    def __init__(
        self,
        statistic: float,
        p_value: float,
        method: str = "bonferroni_corrected_t_test",
        alpha: float = 0.05,
    ):
        self.statistic = statistic
        self.p_value = p_value
        self.method = method
        self.alpha = alpha
        self.adjusted_alpha = self._calculate_adjusted_alpha()
        self.is_significant = self.p_value < self.adjusted_alpha

    def _calculate_adjusted_alpha(self) -> float:
        """Calculate Bonferroni-adjusted alpha for multiple comparisons."""
        # We are comparing two metrics: acceptance_rate and reasoning_score
        # So n_tests = 2
        n_tests = 2
        return self.alpha / n_tests

    def to_dict(self) -> Dict[str, Any]:
        return {
            "statistic": self.statistic,
            "p_value": self.p_value,
            "method": self.method,
            "alpha": self.alpha,
            "adjusted_alpha": self.adjusted_alpha,
            "is_significant": self.is_significant,
        }


def load_metrics_from_json(
    file_path: Path, key: str
) -> List[float]:
    """
    Load a list of metric values from a JSON file.

    Expected JSON structure:
    {
        "acceptance_rate": [list of floats],
        "reasoning_score": [list of floats]
    }

    Args:
        file_path: Path to the JSON file
        key: The key in the JSON to extract (e.g., "acceptance_rate")

    Returns:
        List of float values
    """
    if not file_path.exists():
        raise FileNotFoundError(f"Metrics file not found: {file_path}")

    with open(file_path, "r") as f:
        data = json.load(f)

    if key not in data:
        raise KeyError(f"Key '{key}' not found in {file_path}. Available keys: {list(data.keys())}")

    values = data[key]
    if not isinstance(values, list):
        raise ValueError(f"Expected list for key '{key}' in {file_path}, got {type(values)}")

    return [float(v) for v in values]


def perform_paired_ttest(
    baseline_values: List[float],
    proxy_values: List[float],
    metric_name: str = "metric"
) -> TTestResult:
    """
    Perform a paired t-test between baseline and proxy metrics.

    Args:
        baseline_values: List of values from the baseline run
        proxy_values: List of values from the proxy run
        metric_name: Name of the metric being tested (for logging)

    Returns:
        TTestResult object containing statistic, p_value, and method
    """
    if len(baseline_values) != len(proxy_values):
        raise ValueError(
            f"Length mismatch for {metric_name}: "
            f"baseline={len(baseline_values)}, proxy={len(proxy_values)}"
        )

    if len(baseline_values) < 2:
        raise ValueError(
            f"Insufficient samples for {metric_name} t-test: "
            f"n={len(baseline_values)} (need at least 2)"
        )

    # Perform paired t-test
    statistic, p_value = stats.ttest_rel(baseline_values, proxy_values)

    logger.info(
        f"Paired t-test for {metric_name}: "
        f"t-statistic={statistic:.4f}, p-value={p_value:.4e}"
    )

    return TTestResult(
        statistic=float(statistic),
        p_value=float(p_value),
        method="bonferroni_corrected_t_test"
    )


def run_statistical_comparison(
    baseline_metrics_path: Path,
    proxy_metrics_path: Path,
    output_path: Path
) -> Dict[str, Any]:
    """
    Run statistical comparison between baseline and proxy metrics.

    Performs paired t-tests on:
    1. acceptance_rate
    2. reasoning_score

    Applies Bonferroni correction for multiple comparisons.

    Args:
        baseline_metrics_path: Path to baseline_metrics.json
        proxy_metrics_path: Path to proxy_metrics.json
        output_path: Path to write t_test_results.json

    Returns:
        Dictionary containing all test results
    """
    ensure_log_dir(output_path)

    logger.info(f"Loading baseline metrics from {baseline_metrics_path}")
    logger.info(f"Loading proxy metrics from {proxy_metrics_path}")

    # Load data
    baseline_acceptance = load_metrics_from_json(baseline_metrics_path, "acceptance_rate")
    proxy_acceptance = load_metrics_from_json(proxy_metrics_path, "acceptance_rate")

    baseline_reasoning = load_metrics_from_json(baseline_metrics_path, "reasoning_score")
    proxy_reasoning = load_metrics_from_json(proxy_metrics_path, "reasoning_score")

    # Perform t-tests
    logger.info("Running paired t-test on acceptance rates...")
    acceptance_result = perform_paired_ttest(
        baseline_acceptance,
        proxy_acceptance,
        "acceptance_rate"
    )

    logger.info("Running paired t-test on reasoning scores...")
    reasoning_result = perform_paired_ttest(
        baseline_reasoning,
        proxy_reasoning,
        "reasoning_score"
    )

    # Aggregate results
    results = {
        "acceptance_rate": acceptance_result.to_dict(),
        "reasoning_score": reasoning_result.to_dict(),
        "method": "bonferroni_corrected_t_test",
        "bonferroni_correction": {
            "n_tests": 2,
            "original_alpha": 0.05,
            "adjusted_alpha": acceptance_result.adjusted_alpha
        }
    }

    # Write output
    with open(output_path, "w") as f:
        json.dump(results, f, indent=2)

    logger.info(f"Statistical comparison results written to {output_path}")
    logger.info(f"Acceptance rate significant: {acceptance_result.is_significant}")
    logger.info(f"Reasoning score significant: {reasoning_result.is_significant}")

    return results


def main():
    """CLI entry point for T029."""
    import argparse

    parser = argparse.ArgumentParser(description="Run statistical comparison (T029)")
    parser.add_argument(
        "--baseline",
        type=Path,
        default="data/processed/baseline_metrics.json",
        help="Path to baseline metrics JSON"
    )
    parser.add_argument(
        "--proxy",
        type=Path,
        default="data/processed/proxy_metrics.json",
        help="Path to proxy metrics JSON"
    )
    parser.add_argument(
        "--output",
        type=Path,
        default="data/processed/t_test_results.json",
        help="Path to output results JSON"
    )

    args = parser.parse_args()

    setup_logger("T029_stats")
    run_statistical_comparison(args.baseline, args.proxy, args.output)


if __name__ == "__main__":
    main()
