"""
Bootstrapped Confidence Interval Calculation for Change Scores.

Implements primary bootstrapped CI calculation (10,000 resamples) as per FR-006.
Calculates mean change, 95% CI, and detects convergence failures for fallback.
"""
import os
import json
import csv
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, asdict
import numpy as np

from utils.random_seed import get_seed, set_global_seed, get_rng
from analysis.change_scores import load_merged_data, get_metric_mapping


@dataclass
class BootstrapResult:
    """Result of a bootstrap CI calculation for a single metric."""
    metric: str
    mean_change: float
    ci_lower: float
    ci_upper: float
    n_resamples: int
    convergence_failed: bool = False
    bootstrap_distribution: Optional[List[float]] = None


def calculate_bootstrap_ci(
    values: List[float],
    n_resamples: int = 10000,
    confidence_level: float = 0.95,
    seed: Optional[int] = None
) -> Tuple[float, float, float, bool]:
    """
    Calculate bootstrapped confidence interval for the mean of a list of values.

    Args:
        values: List of numeric values (change scores).
        n_resamples: Number of bootstrap resamples (default 10,000).
        confidence_level: Confidence level for CI (default 0.95).
        seed: Random seed for reproducibility.

    Returns:
        Tuple of (mean, ci_lower, ci_upper, convergence_failed).
        convergence_failed is True if resampling failed (e.g., empty data).
    """
    if not values or len(values) == 0:
        return 0.0, 0.0, 0.0, True

    if seed is None:
        seed = get_seed()
    set_global_seed(seed)
    rng = get_rng()

    n = len(values)
    mean_original = np.mean(values)

    # Check for singular data (all same values)
    if np.std(values) == 0:
        return mean_original, mean_original, mean_original, False

    try:
        # Bootstrap resampling
        bootstrap_means = []
        for _ in range(n_resamples):
            # Resample with replacement
            resample = rng.choice(values, size=n, replace=True)
            bootstrap_means.append(np.mean(resample))

        bootstrap_means = np.array(bootstrap_means)

        # Calculate confidence interval
        alpha = 1 - confidence_level
        ci_lower = np.percentile(bootstrap_means, 100 * (alpha / 2))
        ci_upper = np.percentile(bootstrap_means, 100 * (1 - alpha / 2))

        return mean_original, ci_lower, ci_upper, False

    except Exception as e:
        # Convergence failure detection
        return 0.0, 0.0, 0.0, True


def run_bootstrap_analysis(
    input_path: str,
    output_path: str,
    n_resamples: int = 10000,
    confidence_level: float = 0.95,
    metrics: Optional[List[str]] = None
) -> List[Dict[str, Any]]:
    """
    Run bootstrap CI analysis on merged baseline/post-intervention data.

    Args:
        input_path: Path to merged data CSV.
        output_path: Path to output JSON results.
        n_resamples: Number of bootstrap resamples.
        confidence_level: Confidence level for CIs.
        metrics: List of metrics to analyze (default: all available).

    Returns:
        List of BootstrapResult objects as dictionaries.
    """
    seed = get_seed()
    set_global_seed(seed)

    # Load merged data
    merged_data = load_merged_data(input_path)

    if not merged_data:
        raise ValueError(f"No data found in {input_path}")

    # Get available metrics
    metric_mapping = get_metric_mapping(merged_data)

    if metrics is None:
        metrics = list(metric_mapping.keys())

    results = []

    for metric_name in metrics:
        if metric_name not in metric_mapping:
            print(f"Warning: Metric '{metric_name}' not found in data, skipping.")
            continue

        # Get change scores for this metric
        change_scores = []
        for participant_id, scores in metric_mapping[metric_name].items():
            if 'change' in scores and scores['change'] is not None:
                change_scores.append(scores['change'])

        if not change_scores:
            print(f"Warning: No change scores for '{metric_name}', skipping.")
            continue

        # Calculate bootstrap CI
        mean_change, ci_lower, ci_upper, convergence_failed = calculate_bootstrap_ci(
            values=change_scores,
            n_resamples=n_resamples,
            confidence_level=confidence_level,
            seed=seed
        )

        result = BootstrapResult(
            metric=metric_name,
            mean_change=mean_change,
            ci_lower=ci_lower,
            ci_upper=ci_upper,
            n_resamples=n_resamples,
            convergence_failed=convergence_failed
        )
        results.append(asdict(result))

        print(f"Metric: {metric_name}")
        print(f"  Mean Change: {mean_change:.4f}")
        print(f"  95% CI: [{ci_lower:.4f}, {ci_upper:.4f}]")
        print(f"  Convergence Failed: {convergence_failed}")
        print()

    # Write results to output file
    output_dir = Path(output_path).parent
    output_dir.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w') as f:
        json.dump({
            'seed': seed,
            'n_resamples': n_resamples,
            'confidence_level': confidence_level,
            'results': results
        }, f, indent=2)

    print(f"Bootstrap analysis results written to: {output_path}")

    return results


def main():
    """Main entry point for bootstrap CI analysis."""
    import argparse

    parser = argparse.ArgumentParser(
        description='Calculate bootstrapped confidence intervals for change scores.'
    )
    parser.add_argument(
        '--input',
        type=str,
        default='data/processed/merged_baseline_post.csv',
        help='Path to merged data CSV file'
    )
    parser.add_argument(
        '--output',
        type=str,
        default='results/bootstrap_ci_results.json',
        help='Path to output JSON results file'
    )
    parser.add_argument(
        '--n-resamples',
        type=int,
        default=10000,
        help='Number of bootstrap resamples (default: 10000)'
    )
    parser.add_argument(
        '--confidence-level',
        type=float,
        default=0.95,
        help='Confidence level for CI (default: 0.95)'
    )
    parser.add_argument(
        '--metrics',
        type=str,
        nargs='+',
        default=None,
        help='Specific metrics to analyze (default: all available)'
    )

    args = parser.parse_args()

    run_bootstrap_analysis(
        input_path=args.input,
        output_path=args.output,
        n_resamples=args.n_resamples,
        confidence_level=args.confidence_level,
        metrics=args.metrics
    )


if __name__ == '__main__':
    main()
