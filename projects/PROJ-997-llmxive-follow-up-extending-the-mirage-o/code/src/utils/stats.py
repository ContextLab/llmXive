"""
Statistical analysis utilities for the llmXive pipeline.
Implements paired t-tests with Bonferroni correction for comparing
baseline and proxy policy performance.
"""
import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional
import numpy as np
from scipy import stats
from dataclasses import dataclass, asdict

logger = logging.getLogger(__name__)

@dataclass
class TTestResult:
    """Result container for a paired t-test."""
    statistic: float
    p_value: float
    method: str
    alternative: str
    n_samples: int

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

def load_metrics_from_json(file_path: Path, key: str) -> List[float]:
    """
    Load a specific list of metrics from a JSON file.

    Args:
        file_path: Path to the JSON file
        key: The key in the JSON containing the list of values

    Returns:
        List of float values

    Raises:
        FileNotFoundError: If the file does not exist
        KeyError: If the key is not found in the JSON
        ValueError: If the value is not a list of numbers
    """
    if not file_path.exists():
        raise FileNotFoundError(f"Metrics file not found: {file_path}")

    with open(file_path, 'r') as f:
        data = json.load(f)

    if key not in data:
        raise KeyError(f"Key '{key}' not found in {file_path}. Available keys: {list(data.keys())}")

    values = data[key]
    if not isinstance(values, list):
        raise ValueError(f"Expected list for key '{key}', got {type(values)}")

    try:
        return [float(v) for v in values]
    except (TypeError, ValueError) as e:
        raise ValueError(f"Could not convert values to float: {e}")

def perform_paired_ttest(
    baseline_values: List[float],
    proxy_values: List[float],
    metric_name: str,
    correction_factor: int = 2
) -> TTestResult:
    """
    Perform a paired t-test between baseline and proxy metrics.

    Args:
        baseline_values: List of baseline metric values
        proxy_values: List of proxy metric values
        metric_name: Name of the metric being tested (for logging)
        correction_factor: Number of tests for Bonferroni correction (default 2 for acceptance_rate and reasoning_score)

    Returns:
        TTestResult object

    Raises:
        ValueError: If input lists have different lengths or insufficient samples
    """
    if len(baseline_values) != len(proxy_values):
        raise ValueError(
            f"Baseline and proxy lists have different lengths: "
            f"{len(baseline_values)} vs {len(proxy_values)}"
        )

    if len(baseline_values) < 2:
        raise ValueError(
            f"Insufficient samples for t-test (n={len(baseline_values)}). "
            f"Need at least 2 samples."
        )

    # Perform paired t-test
    statistic, p_value = stats.ttest_rel(baseline_values, proxy_values)

    # Apply Bonferroni correction
    adjusted_p_value = p_value * correction_factor
    # Cap at 1.0
    adjusted_p_value = min(adjusted_p_value, 1.0)

    logger.info(
        f"T-test for {metric_name}: t-statistic={statistic:.4f}, "
        f"raw p-value={p_value:.4f}, Bonferroni-adjusted p-value={adjusted_p_value:.4f}"
    )

    return TTestResult(
        statistic=float(statistic),
        p_value=float(adjusted_p_value),
        method="bonferroni_corrected_t_test",
        alternative="two-sided",
        n_samples=len(baseline_values)
    )

def run_statistical_comparison(
    baseline_metrics_path: Path,
    proxy_metrics_path: Path,
    output_path: Path
) -> Dict[str, Any]:
    """
    Run statistical comparison between baseline and proxy metrics.

    Performs paired t-tests on both acceptance_rate and continuous_reasoning_score,
    applies Bonferroni correction, and writes results to JSON.

    Args:
        baseline_metrics_path: Path to baseline_metrics.json
        proxy_metrics_path: Path to proxy_metrics.json
        output_path: Path to write t_test_results.json

    Returns:
        Dictionary containing all test results
    """
    # Load metrics
    logger.info(f"Loading baseline metrics from {baseline_metrics_path}")
    baseline_acceptance = load_metrics_from_json(baseline_metrics_path, "acceptance_rates")
    baseline_reasoning = load_metrics_from_json(baseline_metrics_path, "reasoning_scores")

    logger.info(f"Loading proxy metrics from {proxy_metrics_path}")
    proxy_acceptance = load_metrics_from_json(proxy_metrics_path, "acceptance_rates")
    proxy_reasoning = load_metrics_from_json(proxy_metrics_path, "reasoning_scores")

    # Perform t-tests with Bonferroni correction
    # We are testing 2 metrics, so correction factor is 2
    test_acceptance = perform_paired_ttest(
        baseline_acceptance, proxy_acceptance, "acceptance_rate", correction_factor=2
    )

    test_reasoning = perform_paired_ttest(
        baseline_reasoning, proxy_reasoning, "reasoning_score", correction_factor=2
    )

    # Compile results
    results = {
        "acceptance_rate": test_acceptance.to_dict(),
        "reasoning_score": test_reasoning.to_dict(),
        "method": "bonferroni_corrected_t_test",
        "correction_factor": 2,
        "n_samples": test_acceptance.n_samples
    }

    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Write results to JSON
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)

    logger.info(f"Statistical comparison results written to {output_path}")

    return results

def main():
    """Main entry point for statistical comparison."""
    import argparse

    parser = argparse.ArgumentParser(description="Run statistical comparison between baseline and proxy metrics")
    parser.add_argument(
        "--baseline",
        type=Path,
        default=Path("data/processed/baseline_metrics.json"),
        help="Path to baseline metrics JSON file"
    )
    parser.add_argument(
        "--proxy",
        type=Path,
        default=Path("data/processed/proxy_metrics.json"),
        help="Path to proxy metrics JSON file"
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("data/processed/t_test_results.json"),
        help="Path to output results JSON file"
    )
    parser.add_argument(
        "--log-level",
        type=str,
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Logging level"
    )

    args = parser.parse_args()

    # Setup logging
    logging.basicConfig(
        level=getattr(logging, args.log_level),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    try:
        results = run_statistical_comparison(args.baseline, args.proxy, args.output)
        logger.info("Statistical comparison completed successfully")
        logger.info(f"Acceptance rate p-value: {results['acceptance_rate']['p_value']:.4f}")
        logger.info(f"Reasoning score p-value: {results['reasoning_score']['p_value']:.4f}")
    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        raise
    except KeyError as e:
        logger.error(f"Missing key in metrics file: {e}")
        raise
    except ValueError as e:
        logger.error(f"Invalid metrics data: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error during statistical comparison: {e}")
        raise

if __name__ == "__main__":
    main()
