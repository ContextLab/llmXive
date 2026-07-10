"""
Effect Size Calculations for Digital Decluttering Study.

Implements Cohen's d calculation with 95% Confidence Intervals using bootstrapping.
Adheres to FR-007 requirements.
"""

import os
import csv
import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, asdict

import numpy as np
from scipy import stats

# Import project utilities
from utils.random_seed import get_seed, get_rng
from config.env_config import get_path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class EffectSizeResult:
    """Dataclass to hold Cohen's d and CI results."""
    metric_name: str
    mean_baseline: float
    mean_post: float
    mean_change: float
    cohens_d: float
    ci_lower: float
    ci_upper: float
    n_baseline: int
    n_post: int
    bootstrap_samples: int
    seed: int


def calculate_cohens_d(group1: np.ndarray, group2: np.ndarray) -> float:
    """
    Calculate Cohen's d effect size.

    Uses the pooled standard deviation.
    d = (mean1 - mean2) / pooled_std

    Args:
        group1: Baseline data array
        group2: Post-intervention data array

    Returns:
        Cohen's d value
    """
    n1, n2 = len(group1), len(group2)
    mean1, mean2 = np.mean(group1), np.mean(group2)
    
    # Pooled standard deviation
    var1 = np.var(group1, ddof=1)
    var2 = np.var(group2, ddof=1)
    
    if n1 > 1 and n2 > 1:
        pooled_std = np.sqrt(((n1 - 1) * var1 + (n2 - 1) * var2) / (n1 + n2 - 2))
    else:
        # Fallback for small samples, though ideally shouldn't happen in study
        pooled_std = np.sqrt((var1 + var2) / 2)

    if pooled_std == 0:
        logger.warning("Pooled standard deviation is zero. Returning 0 for Cohen's d.")
        return 0.0

    return (mean1 - mean2) / pooled_std


def calculate_bootstrap_ci(
    group1: np.ndarray,
    group2: np.ndarray,
    n_resamples: int = 10000,
    confidence_level: float = 0.95,
    rng: Optional[np.random.Generator] = None
) -> Tuple[float, float]:
    """
    Calculate 95% Confidence Interval for Cohen's d using bootstrapping.

    Args:
        group1: Baseline data array
        group2: Post-intervention data array
        n_resamples: Number of bootstrap resamples
        confidence_level: Confidence level (default 0.95)
        rng: NumPy random generator instance

    Returns:
        Tuple of (lower_bound, upper_bound)
    """
    if rng is None:
        seed = get_seed()
        rng = get_rng()

    d_values = []
    n1, n2 = len(group1), len(group2)

    for _ in range(n_resamples):
        # Resample with replacement
        resample1 = rng.choice(group1, size=n1, replace=True)
        resample2 = rng.choice(group2, size=n2, replace=True)
        
        d = calculate_cohens_d(resample1, resample2)
        d_values.append(d)

    d_values = np.array(d_values)
    alpha = 1 - confidence_level
    lower_idx = int((alpha / 2) * n_resamples)
    upper_idx = int((1 - alpha / 2) * n_resamples) - 1

    return float(np.percentile(d_values, (alpha / 2) * 100)), \
           float(np.percentile(d_values, (1 - alpha / 2) * 100))


def calculate_effect_sizes_for_metric(
    baseline_values: List[float],
    post_values: List[float],
    metric_name: str,
    n_resamples: int = 10000
) -> EffectSizeResult:
    """
    Calculate Cohen's d and 95% CI for a specific metric.

    Args:
        baseline_values: List of baseline measurements
        post_values: List of post-intervention measurements
        metric_name: Name of the metric
        n_resamples: Number of bootstrap resamples

    Returns:
        EffectSizeResult object
    """
    seed = get_seed()
    rng = get_rng()
    
    arr_baseline = np.array(baseline_values)
    arr_post = np.array(post_values)

    mean_b = float(np.mean(arr_baseline))
    mean_p = float(np.mean(arr_post))
    mean_change = mean_p - mean_b # Post - Baseline (change direction)
    
    # Cohen's d is typically (Group1 - Group2) / SD.
    # Here we calculate d for the difference. 
    # If we want to represent the magnitude of change:
    cohens_d = calculate_cohens_d(arr_baseline, arr_post)
    
    ci_lower, ci_upper = calculate_bootstrap_ci(
        arr_baseline, arr_post, n_resamples=n_resamples, rng=rng
    )

    return EffectSizeResult(
        metric_name=metric_name,
        mean_baseline=mean_b,
        mean_post=mean_p,
        mean_change=mean_change,
        cohens_d=cohens_d,
        ci_lower=ci_lower,
        ci_upper=ci_upper,
        n_baseline=len(baseline_values),
        n_post=len(post_values),
        bootstrap_samples=n_resamples,
        seed=seed
    )


def load_merged_data_for_metric(
    metric_name: str,
    data_path: Optional[Path] = None
) -> Tuple[List[float], List[float]]:
    """
    Load baseline and post values for a specific metric from the merged dataset.

    Expects the merged file structure from T034.
    """
    if data_path is None:
        data_path = Path(get_path("merged_data_path"))
    
    if not data_path.exists():
        raise FileNotFoundError(f"Merged data file not found: {data_path}")

    baseline_vals = []
    post_vals = []

    with open(data_path, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Assuming merged data has columns: participant_id, metric_name, phase, value
            # Or similar structure. Adjust based on T034 output format.
            if row.get('metric_name') == metric_name:
                val_str = row.get('value')
                if val_str is not None and val_str.strip() != '':
                    try:
                        val = float(val_str)
                        if row.get('phase') == 'baseline':
                            baseline_vals.append(val)
                        elif row.get('phase') == 'post':
                            post_vals.append(val)
                    except ValueError:
                        continue

    if len(baseline_vals) == 0 or len(post_vals) == 0:
        logger.warning(f"No data found for metric {metric_name} in merged file.")
    
    return baseline_vals, post_vals


def run_effect_size_analysis(
    metrics: Optional[List[str]] = None,
    output_path: Optional[Path] = None,
    n_resamples: int = 10000
) -> List[EffectSizeResult]:
    """
    Run effect size analysis for all specified metrics.

    Args:
        metrics: List of metric names to analyze. If None, attempts to infer from data.
        output_path: Path to write JSON results.
        n_resamples: Number of bootstrap resamples.

    Returns:
        List of EffectSizeResult objects.
    """
    # Default metrics based on study design
    if metrics is None:
        metrics = ['SART_errors', 'Ospan_score', 'PSS10_score', 'PANAS_positive', 'PANAS_negative']

    merged_path = Path(get_path("merged_data_path"))
    results = []

    logger.info(f"Starting effect size analysis for {len(metrics)} metrics.")

    for metric in metrics:
        try:
            baseline, post = load_merged_data_for_metric(metric, merged_path)
            
            if len(baseline) < 2 or len(post) < 2:
                logger.warning(f"Skipping {metric}: Insufficient data (n_base={len(baseline)}, n_post={len(post)})")
                continue

            result = calculate_effect_sizes_for_metric(
                baseline, post, metric, n_resamples=n_resamples
            )
            results.append(result)
            logger.info(f"Calculated effect size for {metric}: d={result.cohens_d:.4f}, CI=[{result.ci_lower:.4f}, {result.ci_upper:.4f}]")

        except Exception as e:
            logger.error(f"Error processing metric {metric}: {e}")
            continue

    if output_path:
        output_dir = output_path.parent
        output_dir.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json_results = [asdict(r) for r in results]
            json.dump(json_results, f, indent=2)
        logger.info(f"Effect size results written to {output_path}")

    return results


def main():
    """Main entry point for effect size calculation."""
    # Determine output path from config or default
    output_file = Path(get_path("results_dir")) / "effect_sizes.json"
    
    # Ensure results directory exists
    output_file.parent.mkdir(parents=True, exist_ok=True)

    # Run analysis
    results = run_effect_size_analysis(
        output_path=output_file,
        n_resamples=10000
    )

    print(f"Analysis complete. Processed {len(results)} metrics.")
    print(f"Results saved to: {output_file}")

    # Print summary
    for r in results:
        print(f"Metric: {r.metric_name}")
        print(f"  Cohen's d: {r.cohens_d:.4f}")
        print(f"  95% CI: [{r.ci_lower:.4f}, {r.ci_upper:.4f}]")
        print(f"  N Baseline: {r.n_baseline}, N Post: {r.n_post}")
        print("-" * 30)


if __name__ == "__main__":
    main()
