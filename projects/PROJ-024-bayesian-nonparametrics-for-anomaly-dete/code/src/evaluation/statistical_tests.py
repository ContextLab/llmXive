"""
Statistical Tests for Model Comparison

Implements paired t-tests with Bonferroni correction for comparing
anomaly detection models across multiple datasets per US2 acceptance
scenario 2.

This module provides statistical validation that DPGMM performs
significantly better than baselines (ARIMA, Moving Average, LSTM-AE).
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any
import numpy as np
from scipy import stats
from pathlib import Path
import json
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@dataclass
class StatisticalTestResult:
    """
    Result of a statistical hypothesis test comparing two models.

    Attributes:
        test_name: Name of the statistical test performed
        model_a: Name of the first model being compared
        model_b: Name of the second model being compared
        dataset_name: Name of the dataset used for comparison
        t_statistic: t-statistic from the paired t-test
        p_value: p-value from the test (before Bonferroni correction)
        p_value_corrected: p-value after Bonferroni correction
        significant: Whether the difference is statistically significant
        effect_size: Cohen's d effect size
        confidence_interval: 95% confidence interval for the mean difference
        n_observations: Number of paired observations
        direction: 'a_better', 'b_better', or 'no_difference'
    """
    test_name: str
    model_a: str
    model_b: str
    dataset_name: str
    t_statistic: float
    p_value: float
    p_value_corrected: float
    significant: bool
    effect_size: float
    confidence_interval: Tuple[float, float]
    n_observations: int
    direction: str


@dataclass
class ComparisonSummary:
    """
    Summary of all statistical comparisons across datasets.

    Attributes:
        total_comparisons: Total number of pairwise comparisons performed
        significant_comparisons: Number of comparisons with p < alpha
        models_compared: List of unique model names involved
        datasets_tested: List of datasets used
        alpha_level: Significance level used (default 0.05)
        bonferroni_factor: Number of comparisons for correction
        results: List of individual StatisticalTestResult objects
        timestamp: When the analysis was performed
        summary_stats: Dictionary of aggregate statistics
    """
    total_comparisons: int
    significant_comparisons: int
    models_compared: List[str]
    datasets_tested: List[str]
    alpha_level: float
    bonferroni_factor: int
    results: List[StatisticalTestResult] = field(default_factory=list)
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    summary_stats: Dict[str, Any] = field(default_factory=dict)


def apply_bonferroni_correction(
    p_values: List[float],
    num_comparisons: int
) -> List[float]:
    """
    Apply Bonferroni correction to multiple p-values.

    The Bonferroni correction controls the family-wise error rate by
    dividing the significance threshold by the number of comparisons.

    Args:
        p_values: List of raw p-values from hypothesis tests
        num_comparisons: Total number of comparisons being made

    Returns:
        List of Bonferroni-corrected p-values (capped at 1.0)
    """
    if num_comparisons <= 0:
        raise ValueError("num_comparisons must be positive")

    corrected = []
    for p in p_values:
        corrected_p = min(p * num_comparisons, 1.0)
        corrected.append(corrected_p)

    return corrected


def paired_ttest_with_bonferroni(
    scores_a: np.ndarray,
    scores_b: np.ndarray,
    alpha: float = 0.05,
    num_comparisons: int = 1
) -> StatisticalTestResult:
    """
    Perform paired t-test between two models with Bonferroni correction.

    This tests whether the mean difference between paired anomaly scores
    (or performance metrics) from two models is significantly different
    from zero.

    Args:
        scores_a: Array of scores/metrics from model A
        scores_b: Array of scores/metrics from model B
        alpha: Significance level for hypothesis test
        num_comparisons: Total number of comparisons for Bonferroni correction

    Returns:
        StatisticalTestResult with test statistics and corrected p-values

    Raises:
        ValueError: If input arrays have different lengths or are empty
        ValueError: If num_comparisons is not positive
    """
    # Validate inputs
    if len(scores_a) != len(scores_b):
        raise ValueError(
            f"Input arrays must have same length: "
            f"{len(scores_a)} vs {len(scores_b)}"
        )

    if len(scores_a) == 0:
        raise ValueError("Input arrays cannot be empty")

    if num_comparisons <= 0:
        raise ValueError("num_comparisons must be positive")

    # Convert to numpy arrays
    scores_a = np.asarray(scores_a, dtype=np.float64)
    scores_b = np.asarray(scores_b, dtype=np.float64)

    # Check for NaN or Inf values
    if np.any(np.isnan(scores_a)) or np.any(np.isnan(scores_b)):
        logger.warning("Input contains NaN values - replacing with mean")
        mean_a = np.nanmean(scores_a)
        mean_b = np.nanmean(scores_b)
        scores_a = np.nan_to_num(scores_a, nan=mean_a)
        scores_b = np.nan_to_num(scores_b, nan=mean_b)

    # Perform paired t-test
    t_statistic, p_value = stats.ttest_rel(scores_a, scores_b)

    # Apply Bonferroni correction
    p_value_corrected = apply_bonferroni_correction(
        [p_value], num_comparisons
    )[0]

    # Determine significance
    significant = p_value_corrected < alpha

    # Calculate effect size (Cohen's d for paired samples)
    diff = scores_a - scores_b
    effect_size = _cohens_d_paired(scores_a, scores_b)

    # Calculate 95% confidence interval for mean difference
    mean_diff = np.mean(diff)
    se_diff = np.std(diff, ddof=1) / np.sqrt(len(diff))
    ci = stats.t.interval(
        0.95, len(diff) - 1, loc=mean_diff, scale=se_diff
    )

    # Determine direction of difference
    if mean_diff > 0 and significant:
        direction = 'a_better'
    elif mean_diff < 0 and significant:
        direction = 'b_better'
    else:
        direction = 'no_difference'

    return StatisticalTestResult(
        test_name='paired_ttest_bonferroni',
        model_a='DPGMM',
        model_b='Baseline',
        dataset_name='unknown',
        t_statistic=float(t_statistic),
        p_value=float(p_value),
        p_value_corrected=float(p_value_corrected),
        significant=significant,
        effect_size=float(effect_size),
        confidence_interval=(float(ci[0]), float(ci[1])),
        n_observations=len(scores_a),
        direction=direction
    )


def _cohens_d_paired(
    scores_a: np.ndarray,
    scores_b: np.ndarray
) -> float:
    """
    Calculate Cohen's d effect size for paired samples.

    For paired samples, Cohen's d is calculated as the mean difference
    divided by the standard deviation of the differences.

    Args:
        scores_a: Array of scores from condition A
        scores_b: Array of scores from condition B

    Returns:
        Cohen's d effect size
    """
    diff = scores_a - scores_b
    mean_diff = np.mean(diff)
    std_diff = np.std(diff, ddof=1)

    if std_diff == 0:
        return 0.0

    return float(mean_diff / std_diff)


def compare_all_models(
    model_scores: Dict[str, Dict[str, np.ndarray]],
    alpha: float = 0.05
) -> ComparisonSummary:
    """
    Compare all models across all datasets using paired t-tests.

    This performs pairwise comparisons between all models for each
    dataset, applying Bonferroni correction for the total number
    of comparisons.

    Args:
        model_scores: Dictionary mapping model names to dataset scores.
            Structure: {model_name: {dataset_name: scores_array}}
        alpha: Significance level for hypothesis tests

    Returns:
        ComparisonSummary with all test results and aggregate statistics
    """
    # Validate input
    if not model_scores:
        raise ValueError("model_scores cannot be empty")

    model_names = list(model_scores.keys())
    if len(model_names) < 2:
        raise ValueError("At least 2 models required for comparison")

    # Find all datasets
    all_datasets = set()
    for model_name, datasets in model_scores.items():
        all_datasets.update(datasets.keys())

    if not all_datasets:
        raise ValueError("No datasets found in model_scores")

    datasets_list = sorted(list(all_datasets))

    # Calculate total number of comparisons
    # For each dataset: nC2 = n*(n-1)/2 comparisons
    comparisons_per_dataset = len(model_names) * (len(model_names) - 1) // 2
    total_comparisons = comparisons_per_dataset * len(datasets_list)

    # Apply Bonferroni correction factor
    bonferroni_factor = total_comparisons

    results = []
    significant_count = 0

    # Perform pairwise comparisons for each dataset
    for dataset in datasets_list:
        for i, model_a in enumerate(model_names):
            for model_b in model_names[i + 1:]:
                # Check both models have scores for this dataset
                if dataset not in model_scores[model_a]:
                    logger.warning(
                        f"{model_a} has no scores for {dataset}, skipping"
                    )
                    continue
                if dataset not in model_scores[model_b]:
                    logger.warning(
                        f"{model_b} has no scores for {dataset}, skipping"
                    )
                    continue

                scores_a = model_scores[model_a][dataset]
                scores_b = model_scores[model_b][dataset]

                try:
                    result = paired_ttest_with_bonferroni(
                        scores_a=scores_a,
                        scores_b=scores_b,
                        alpha=alpha,
                        num_comparisons=bonferroni_factor
                    )
                    result.dataset_name = dataset
                    result.model_a = model_a
                    result.model_b = model_b
                    results.append(result)

                    if result.significant:
                        significant_count += 1

                except Exception as e:
                    logger.error(
                        f"Comparison {model_a} vs {model_b} on "
                        f"{dataset} failed: {e}"
                    )
                    continue

    # Calculate summary statistics
    summary_stats = _calculate_summary_statistics(results, model_names, alpha)

    return ComparisonSummary(
        total_comparisons=len(results),
        significant_comparisons=significant_count,
        models_compared=model_names,
        datasets_tested=datasets_list,
        alpha_level=alpha,
        bonferroni_factor=bonferroni_factor,
        results=results,
        summary_stats=summary_stats
    )


def _calculate_summary_statistics(
    results: List[StatisticalTestResult],
    model_names: List[str],
    alpha: float
) -> Dict[str, Any]:
    """
    Calculate aggregate statistics from comparison results.

    Args:
        results: List of StatisticalTestResult objects
        model_names: List of model names being compared
        alpha: Significance level used

    Returns:
        Dictionary of summary statistics
    """
    if not results:
        return {
            'total_tests': 0,
            'significant_tests': 0,
            'power': 0.0,
            'models_wins': {},
            'average_effect_size': 0.0
        }

    # Count wins for each model
    model_wins = {name: 0 for name in model_names}
    total_effect_size = 0.0

    for result in results:
        if result.significant:
            if result.direction == 'a_better':
                model_wins[result.model_a] += 1
            elif result.direction == 'b_better':
                model_wins[result.model_b] += 1

        total_effect_size += abs(result.effect_size)

    avg_effect_size = total_effect_size / len(results) if results else 0.0

    return {
        'total_tests': len(results),
        'significant_tests': sum(1 for r in results if r.significant),
        'power': sum(1 for r in results if r.significant) / len(results),
        'models_wins': model_wins,
        'average_effect_size': avg_effect_size,
        'alpha_level': alpha
    }


def format_comparison_summary(
    summary: ComparisonSummary,
    include_individual_results: bool = True
) -> str:
    """
    Format comparison summary as a readable markdown report.

    Args:
        summary: ComparisonSummary object to format
        include_individual_results: Whether to include individual test results

    Returns:
        Formatted markdown string
    """
    lines = [
        "# Statistical Comparison Report",
        "",
        f"**Generated**: {summary.timestamp}",
        "",
        "## Summary Statistics",
        "",
        f"- **Total Comparisons**: {summary.total_comparisons}",
        f"- **Significant Comparisons**: {summary.significant_comparisons}",
        f"- **Significance Level (α)**: {summary.alpha_level}",
        f"- **Bonferroni Factor**: {summary.bonferroni_factor}",
        f"- **Models Tested**: {', '.join(summary.models_compared)}",
        f"- **Datasets Tested**: {', '.join(summary.datasets_tested)}",
        ""
    ]

    # Add individual results if requested
    if include_individual_results and summary.results:
        lines.extend([
            "## Individual Test Results",
            "",
            "| Dataset | Model A | Model B | t-statistic | p-value | p-corrected | Significant | Effect Size | Direction |",
            "|---------|---------|---------|-------------|---------|-------------|-------------|-------------|-----------|"
        ])

        for result in summary.results:
            lines.append(
                f"| {result.dataset_name} | {result.model_a} | "
                f"{result.model_b} | {result.t_statistic:.4f} | "
                f"{result.p_value:.6f} | {result.p_value_corrected:.6f} | "
                f"{'Yes' if result.significant else 'No'} | "
                f"{result.effect_size:.4f} | {result.direction} |"
            )

        lines.append("")

    # Add interpretation
    lines.extend([
        "## Interpretation",
        "",
        f"Out of {summary.total_comparisons} pairwise comparisons, "
        f"{summary.significant_comparisons} showed statistically significant "
        f"differences after Bonferroni correction (α = {summary.alpha_level}).",
        ""
    ])

    if summary.significant_comparisons > 0:
        lines.append("Models with significant performance differences:")
        lines.append("")
        for result in summary.results:
            if result.significant:
                winner = result.model_a if result.direction == 'a_better' else result.model_b
                loser = result.model_b if result.direction == 'a_better' else result.model_a
                lines.append(
                    f"- **{winner}** significantly outperformed **{loser}** "
                    f"on **{result.dataset_name}** (p = {result.p_value_corrected:.6f}, "
                    f"d = {result.effect_size:.4f})"
                )
        lines.append("")

    return "\n".join(lines)


def save_comparison_results(
    summary: ComparisonSummary,
    output_dir: Path,
    output_format: str = 'json'
) -> Path:
    """
    Save comparison results to file.

    Args:
        summary: ComparisonSummary object to save
        output_dir: Directory to save results
        output_format: Output format ('json', 'markdown', or 'both')

    Returns:
        Path to saved file(s)

    Raises:
        ValueError: If output_format is not recognized
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

    if output_format in ['json', 'both']:
        json_path = output_dir / f'comparison_results_{timestamp}.json'
        json_data = {
            'summary': {
                'total_comparisons': summary.total_comparisons,
                'significant_comparisons': summary.significant_comparisons,
                'models_compared': summary.models_compared,
                'datasets_tested': summary.datasets_tested,
                'alpha_level': summary.alpha_level,
                'bonferroni_factor': summary.bonferroni_factor,
                'timestamp': summary.timestamp,
                'summary_stats': summary.summary_stats
            },
            'results': [
                {
                    'test_name': r.test_name,
                    'model_a': r.model_a,
                    'model_b': r.model_b,
                    'dataset_name': r.dataset_name,
                    't_statistic': r.t_statistic,
                    'p_value': r.p_value,
                    'p_value_corrected': r.p_value_corrected,
                    'significant': r.significant,
                    'effect_size': r.effect_size,
                    'confidence_interval': r.confidence_interval,
                    'n_observations': r.n_observations,
                    'direction': r.direction
                }
                for r in summary.results
            ]
        }

        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(json_data, f, indent=2)
        logger.info(f"Saved JSON results to {json_path}")

    if output_format in ['markdown', 'both']:
        md_path = output_dir / f'comparison_report_{timestamp}.md'
        md_content = format_comparison_summary(summary)
        with open(md_path, 'w', encoding='utf-8') as f:
            f.write(md_content)
        logger.info(f"Saved markdown report to {md_path}")

    if output_format == 'json':
        return json_path
    elif output_format == 'markdown':
        return md_path
    else:
        return json_path  # Return primary file path


def load_comparison_results(json_path: Path) -> ComparisonSummary:
    """
    Load comparison results from JSON file.

    Args:
        json_path: Path to JSON file with comparison results

    Returns:
        ComparisonSummary object reconstructed from file
    """
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    summary_data = data['summary']
    results_data = data['results']

    results = [
        StatisticalTestResult(
            test_name=r['test_name'],
            model_a=r['model_a'],
            model_b=r['model_b'],
            dataset_name=r['dataset_name'],
            t_statistic=r['t_statistic'],
            p_value=r['p_value'],
            p_value_corrected=r['p_value_corrected'],
            significant=r['significant'],
            effect_size=r['effect_size'],
            confidence_interval=tuple(r['confidence_interval']),
            n_observations=r['n_observations'],
            direction=r['direction']
        )
        for r in results_data
    ]

    return ComparisonSummary(
        total_comparisons=summary_data['total_comparisons'],
        significant_comparisons=summary_data['significant_comparisons'],
        models_compared=summary_data['models_compared'],
        datasets_tested=summary_data['datasets_tested'],
        alpha_level=summary_data['alpha_level'],
        bonferroni_factor=summary_data['bonferroni_factor'],
        results=results,
        timestamp=summary_data['timestamp'],
        summary_stats=summary_data.get('summary_stats', {})
    )


def main():
    """
    Main entry point for command-line usage.

    Demonstrates statistical comparison workflow with synthetic data.
    """
    import argparse

    parser = argparse.ArgumentParser(
        description='Statistical comparison of anomaly detection models'
    )
    parser.add_argument(
        '--alpha',
        type=float,
        default=0.05,
        help='Significance level (default: 0.05)'
    )
    parser.add_argument(
        '--output-dir',
        type=str,
        default='data/processed/results',
        help='Output directory for results'
    )
    parser.add_argument(
        '--format',
        type=str,
        choices=['json', 'markdown', 'both'],
        default='both',
        help='Output format (default: both)'
    )
    parser.add_argument(
        '--demo',
        action='store_true',
        help='Run demo with synthetic data'
    )

    args = parser.parse_args()

    if args.demo:
        logger.info("Running demo with synthetic data...")

        # Create synthetic comparison data
        np.random.seed(42)
        n_samples = 1000

        # Simulate DPGMM vs baselines on 3 datasets
        model_scores = {
            'DPGMM': {
                'electricity': np.random.normal(loc=0.85, scale=0.1, size=n_samples),
                'traffic': np.random.normal(loc=0.82, scale=0.12, size=n_samples),
                'synthetic_control': np.random.normal(loc=0.88, scale=0.08, size=n_samples)
            },
            'ARIMA': {
                'electricity': np.random.normal(loc=0.75, scale=0.15, size=n_samples),
                'traffic': np.random.normal(loc=0.72, scale=0.18, size=n_samples),
                'synthetic_control': np.random.normal(loc=0.78, scale=0.12, size=n_samples)
            },
            'MovingAverage': {
                'electricity': np.random.normal(loc=0.70, scale=0.2, size=n_samples),
                'traffic': np.random.normal(loc=0.68, scale=0.22, size=n_samples),
                'synthetic_control': np.random.normal(loc=0.72, scale=0.18, size=n_samples)
            },
            'LSTM_AE': {
                'electricity': np.random.normal(loc=0.80, scale=0.12, size=n_samples),
                'traffic': np.random.normal(loc=0.78, scale=0.14, size=n_samples),
                'synthetic_control': np.random.normal(loc=0.82, scale=0.1, size=n_samples)
            }
        }

        # Perform comparisons
        summary = compare_all_models(model_scores, alpha=args.alpha)

        # Output results
        output_path = Path(args.output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        saved_path = save_comparison_results(
            summary, output_path, output_format=args.format
        )

        # Print summary
        print(format_comparison_summary(summary))
        print(f"\nResults saved to: {saved_path}")

        return 0

    else:
        parser.print_help()
        return 0


if __name__ == '__main__':
    exit(main())
