"""Power analysis for social memory network experiments.

This module implements power analysis to estimate detectable effect sizes
and required sample sizes for the experiments described in FR-009.

The analysis uses real data from completed experiments to compute:
1. Observed effect sizes (Cohen's d)
2. Statistical power for given sample sizes
3. Detectable effect sizes for target power levels
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
from scipy import stats

# Try to import statsmodels for more advanced power analysis
try:
    from statsmodels.stats.power import TTestIndPower, FTestAnovaPower
    HAS_STATSMODELS = True
except ImportError:
    HAS_STATSMODELS = False


@dataclass
class PowerAnalysisResult:
    """Result of a power analysis computation."""
    sample_size: int
    observed_effect_size: float
    detectable_effect_size: float
    power: float
    alpha: float
    metric_name: str
    context_condition: str
    confidence_level: float = 0.95


def compute_effect_size(
    group1: np.ndarray,
    group2: np.ndarray,
    method: str = "cohen_d"
) -> float:
    """Compute effect size between two groups.

    Args:
        group1: First group of observations
        group2: Second group of observations
        method: Effect size method ("cohen_d", "hedges_g", "pearson_r")

    Returns:
        Effect size value
    """
    if method == "cohen_d":
        # Cohen's d: difference in means divided by pooled standard deviation
        n1, n2 = len(group1), len(group2)
        mean1, mean2 = np.mean(group1), np.mean(group2)
        std1, std2 = np.std(group1, ddof=1), np.std(group2, ddof=1)

        # Pooled standard deviation
        pooled_std = np.sqrt(((n1 - 1) * std1**2 + (n2 - 1) * std2**2) / (n1 + n2 - 2))

        if pooled_std == 0:
            return 0.0

        return (mean1 - mean2) / pooled_std

    elif method == "hedges_g":
        # Hedges' g: bias-corrected Cohen's d
        d = compute_effect_size(group1, group2, "cohen_d")
        n1, n2 = len(group1), len(group2)

        # Correction factor
        n = n1 + n2 - 2
        correction = 1 - (3 / (4 * n - 1))

        return d * correction

    elif method == "pearson_r":
        # Pearson correlation for paired data
        if len(group1) != len(group2):
            raise ValueError("Groups must be same length for Pearson r")

        correlation, _ = stats.pearsonr(group1, group2)
        return correlation

    else:
        raise ValueError(f"Unknown effect size method: {method}")


def compute_power(
    effect_size: float,
    sample_size: int,
    alpha: float = 0.05,
    alternative: str = "two-sided"
) -> float:
    """Compute statistical power for a given effect size and sample size.

    Args:
        effect_size: Cohen's d effect size
        sample_size: Number of observations per group
        alpha: Significance level
        alternative: Type of test ("two-sided", "greater", "less")

    Returns:
        Statistical power (probability of detecting the effect)
    """
    if HAS_STATSMODELS:
        power_analysis = TTestIndPower()
        power = power_analysis.power(
            effect_size=effect_size,
            nobs1=sample_size,
            alpha=alpha,
            ratio=1.0,
            alternative=alternative
        )
        return power
    else:
        # Approximate power calculation without statsmodels
        # Using normal approximation for large samples
        n = sample_size
        z_alpha = stats.norm.ppf(1 - alpha / 2) if alternative == "two-sided" else stats.norm.ppf(1 - alpha)

        # Non-centrality parameter
        ncp = effect_size * np.sqrt(n / 2)

        # Power is probability that test statistic exceeds critical value
        power = stats.norm.cdf(ncp - z_alpha) + stats.norm.cdf(-ncp - z_alpha)

        return max(0.0, min(1.0, power))


def compute_detectable_effect_size(
    sample_size: int,
    power: float = 0.80,
    alpha: float = 0.05,
    alternative: str = "two-sided"
) -> float:
    """Compute the minimum detectable effect size for given power and sample size.

    Args:
        sample_size: Number of observations per group
        power: Target statistical power
        alpha: Significance level
        alternative: Type of test ("two-sided", "greater", "less")

    Returns:
        Minimum detectable effect size (Cohen's d)
    """
    if HAS_STATSMODELS:
        power_analysis = TTestIndPower()
        detectable_es = power_analysis.solve_power(
            effect_size=None,
            nobs1=sample_size,
            alpha=alpha,
            power=power,
            ratio=1.0,
            alternative=alternative
        )
        return detectable_es if detectable_es is not None else float('inf')
    else:
        # Approximate calculation without statsmodels
        # Iterative search for detectable effect size
        z_alpha = stats.norm.ppf(1 - alpha / 2) if alternative == "two-sided" else stats.norm.ppf(1 - alpha)
        z_beta = stats.norm.ppf(power)

        n = sample_size
        # Solve for effect size: ncp = z_alpha + z_beta
        # ncp = effect_size * sqrt(n/2)
        detectable_es = (z_alpha + z_beta) / np.sqrt(n / 2)

        return detectable_es


def load_experiment_results(
    results_path: Path,
    metric: str = "specialization_index"
) -> Tuple[np.ndarray, np.ndarray]:
    """Load experiment results and split by context condition.

    Args:
        results_path: Path to results CSV file
        metric: Metric column to analyze ("specialization_index" or "retrieval_efficiency")

    Returns:
        Tuple of (full_context_values, limited_context_values)
    """
    if not results_path.exists():
        raise FileNotFoundError(f"Results file not found: {results_path}")

    full_context = []
    limited_context = []

    with open(results_path, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                value = float(row[metric])
                context = row.get('context_condition', 'full')

                if context == 'full':
                    full_context.append(value)
                elif context == 'limited':
                    limited_context.append(value)
            except (ValueError, KeyError):
                continue

    return np.array(full_context), np.array(limited_context)


def run_power_analysis(
    results_path: Path,
    metric: str = "specialization_index",
    target_power: float = 0.80,
    alpha: float = 0.05,
    sample_size_override: Optional[int] = None
) -> List[PowerAnalysisResult]:
    """Run comprehensive power analysis on experiment results.

    Args:
        results_path: Path to results CSV file
        metric: Metric to analyze
        target_power: Target statistical power
        alpha: Significance level
        sample_size_override: Override sample size (uses actual if None)

    Returns:
        List of PowerAnalysisResult objects
    """
    full_context, limited_context = load_experiment_results(results_path, metric)

    if len(full_context) == 0 or len(limited_context) == 0:
        raise ValueError("Insufficient data for power analysis")

    # Use override or actual sample size
    n_full = len(full_context)
    n_limited = len(limited_context)
    sample_size = sample_size_override if sample_size_override else min(n_full, n_limited)

    # Compute observed effect size
    observed_es = compute_effect_size(full_context, limited_context)

    # Compute power for observed effect size
    power = compute_power(observed_es, sample_size, alpha)

    # Compute detectable effect size for target power
    detectable_es = compute_detectable_effect_size(sample_size, target_power, alpha)

    return [
        PowerAnalysisResult(
            sample_size=sample_size,
            observed_effect_size=observed_es,
            detectable_effect_size=detectable_es,
            power=power,
            alpha=alpha,
            metric_name=metric,
            context_condition="full_vs_limited",
            confidence_level=1 - alpha
        )
    ]


def generate_power_report(
    results_path: Path,
    output_path: Path,
    metrics: List[str] = None,
    target_power: float = 0.80,
    alpha: float = 0.05,
    sample_size_override: Optional[int] = None
) -> Dict[str, Any]:
    """Generate a comprehensive power analysis report.

    Args:
        results_path: Path to results CSV file
        output_path: Path to write report (JSON format)
        metrics: List of metrics to analyze
        target_power: Target statistical power
        alpha: Significance level
        sample_size_override: Override sample size

    Returns:
        Dictionary containing report data
    """
    if metrics is None:
        metrics = ["specialization_index", "retrieval_efficiency"]

    report = {
        "report_type": "power_analysis",
        "target_power": target_power,
        "alpha": alpha,
        "sample_size_override": sample_size_override,
        "results_path": str(results_path),
        "results": []
    }

    for metric in metrics:
        try:
            results = run_power_analysis(
                results_path,
                metric=metric,
                target_power=target_power,
                alpha=alpha,
                sample_size_override=sample_size_override
            )

            for result in results:
                report["results"].append(asdict(result))

        except Exception as e:
            report["results"].append({
                "metric_name": metric,
                "error": str(e)
            })

    # Write report to file
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2)

    return report


def build_parser() -> argparse.ArgumentParser:
    """Build command-line argument parser."""
    parser = argparse.ArgumentParser(
        description="Generate power analysis report for social memory network experiments"
    )
    parser.add_argument(
        "--results",
        type=str,
        default="data/results_full.csv",
        help="Path to results CSV file"
    )
    parser.add_argument(
        "--output",
        type=str,
        default="results/power_analysis_report.json",
        help="Path to output report file"
    )
    parser.add_argument(
        "--metrics",
        type=str,
        nargs="+",
        default=["specialization_index", "retrieval_efficiency"],
        help="Metrics to analyze"
    )
    parser.add_argument(
        "--target-power",
        type=float,
        default=0.80,
        help="Target statistical power"
    )
    parser.add_argument(
        "--alpha",
        type=float,
        default=0.05,
        help="Significance level"
    )
    parser.add_argument(
        "--sample-size",
        type=int,
        default=None,
        help="Override sample size (uses actual from data if not specified)"
    )
    return parser


def main():
    """Main entry point for power analysis CLI."""
    parser = build_parser()
    args = parser.parse_args()

    results_path = Path(args.results)
    output_path = Path(args.output)

    if not results_path.exists():
        print(f"Error: Results file not found: {results_path}", file=sys.stderr)
        sys.exit(1)

    try:
        report = generate_power_report(
            results_path=results_path,
            output_path=output_path,
            metrics=args.metrics,
            target_power=args.target_power,
            alpha=args.alpha,
            sample_size_override=args.sample_size
        )

        print(f"Power analysis report written to: {output_path}")
        print(f"Analyzed {len(report['results'])} metrics")

        for result in report['results']:
            if 'error' in result:
                print(f"  - {result.get('metric_name', 'unknown')}: ERROR - {result['error']}")
            else:
                print(f"  - {result['metric_name']}:")
                print(f"      Sample size: {result['sample_size']}")
                print(f"      Observed effect size (Cohen's d): {result['observed_effect_size']:.4f}")
                print(f"      Detectable effect size: {result['detectable_effect_size']:.4f}")
                print(f"      Achieved power: {result['power']:.4f}")

    except Exception as e:
        print(f"Error during power analysis: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
