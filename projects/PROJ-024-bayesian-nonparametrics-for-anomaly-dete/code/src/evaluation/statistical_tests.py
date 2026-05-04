"""
Statistical tests for comparing anomaly detection models across datasets.

Implements paired t-tests with Bonferroni correction for multiple hypothesis testing.
Used in User Story 2 to validate that DPGMM significantly outperforms baselines.
"""
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any
import numpy as np
from scipy import stats
from pathlib import Path
import json
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class StatisticalTestResult:
    """Result of a single statistical test comparison."""
    test_name: str
    model_a: str
    model_b: str
    dataset: str
    statistic: float
    p_value: float
    significant: bool
    effect_size: Optional[float] = None
    confidence_interval: Optional[Tuple[float, float]] = None
    correction_applied: Optional[str] = None
    corrected_p_value: Optional[float] = None


@dataclass
class ComparisonSummary:
    """Summary of all statistical comparisons across datasets."""
    total_comparisons: int
    significant_results: int
    non_significant_results: int
    mean_effect_sizes: Dict[str, float]
    bonferroni_threshold: float
    comparisons: List[StatisticalTestResult] = field(default_factory=list)
    datasets_analyzed: List[str] = field(default_factory=list)
    models_compared: List[str] = field(default_factory=list)


def paired_ttest_with_bonferroni(
    scores_a: np.ndarray,
    scores_b: np.ndarray,
    model_a_name: str,
    model_b_name: str,
    dataset_name: str,
    alpha: float = 0.05
) -> StatisticalTestResult:
    """
    Perform paired t-test between two model score distributions with Bonferroni correction.
    
    This is used to compare anomaly scores from different models on the same dataset,
    where each observation has scores from both models (paired design).
    
    Args:
        scores_a: Array of scores from model A (e.g., DPGMM)
        scores_b: Array of scores from model B (e.g., ARIMA)
        model_a_name: Name of model A
        model_b_name: Name of model B
        dataset_name: Name of the dataset used
        alpha: Significance level (default 0.05)
        
    Returns:
        StatisticalTestResult with test statistics and corrected p-value
        
    Raises:
        ValueError: If input arrays have different lengths or are empty
    """
    # Validate inputs
    scores_a = np.asarray(scores_a)
    scores_b = np.asarray(scores_b)
    
    if len(scores_a) != len(scores_b):
        raise ValueError(
            f"Score arrays must have same length: "
            f"model_a={len(scores_a)}, model_b={len(scores_b)}"
        )
    
    if len(scores_a) < 2:
        raise ValueError("Need at least 2 observations for t-test")
    
    # Check for NaN values
    if np.any(np.isnan(scores_a)) or np.any(np.isnan(scores_b)):
        logger.warning("NaN values detected, removing from analysis")
        valid_mask = ~(np.isnan(scores_a) | np.isnan(scores_b))
        scores_a = scores_a[valid_mask]
        scores_b = scores_b[valid_mask]
        
        if len(scores_a) < 2:
            raise ValueError("Not enough valid observations after NaN removal")
    
    # Perform paired t-test
    t_statistic, p_value = stats.ttest_rel(scores_a, scores_b)
    
    # Calculate effect size (Cohen's d for paired samples)
    diff = scores_a - scores_b
    effect_size = np.mean(diff) / np.std(diff, ddof=1) if np.std(diff) > 0 else 0.0
    
    # Calculate 95% confidence interval for the mean difference
    mean_diff = np.mean(diff)
    se_diff = np.std(diff, ddof=1) / np.sqrt(len(diff))
    ci_low, ci_high = stats.t.interval(
        0.95, len(diff) - 1, loc=mean_diff, scale=se_diff
    )
    
    # Determine significance (without correction for single test)
    significant = p_value < alpha
    
    return StatisticalTestResult(
        test_name="paired_ttest",
        model_a=model_a_name,
        model_b=model_b_name,
        dataset=dataset_name,
        statistic=t_statistic,
        p_value=p_value,
        significant=significant,
        effect_size=effect_size,
        confidence_interval=(ci_low, ci_high),
        correction_applied=None,
        corrected_p_value=None
    )


def apply_bonferroni_correction(
    p_values: List[float],
    num_comparisons: int,
    alpha: float = 0.05
) -> Tuple[List[float], List[bool]]:
    """
    Apply Bonferroni correction to multiple p-values.
    
    The Bonferroni correction divides the significance threshold by the
    number of comparisons to control family-wise error rate.
    
    Args:
        p_values: List of raw p-values from individual tests
        num_comparisons: Total number of comparisons being made
        alpha: Original significance level (default 0.05)
        
    Returns:
        Tuple of (corrected_p_values, significant_flags)
    """
    # Corrected threshold
    corrected_alpha = alpha / num_comparisons if num_comparisons > 0 else alpha
    
    # Corrected p-values (multiply by number of comparisons, capped at 1.0)
    corrected_p_values = [min(p * num_comparisons, 1.0) for p in p_values]
    
    # Determine significance with correction
    significant_flags = [p < corrected_alpha for p in corrected_p_values]
    
    return corrected_p_values, significant_flags


def compare_all_models(
    model_scores: Dict[str, Dict[str, np.ndarray]],
    model_names: Optional[List[str]] = None,
    alpha: float = 0.05
) -> ComparisonSummary:
    """
    Compare all model pairs across all datasets using paired t-tests with Bonferroni correction.
    
    This is the main entry point for User Story 2 statistical validation. It takes
    a nested dictionary where:
    - Outer keys: dataset names
    - Inner keys: model names
    - Values: arrays of anomaly scores for each observation
    
    Args:
        model_scores: Dict[dataset_name, Dict[model_name, scores_array]]
        model_names: Optional list of models to compare (default: all found)
        alpha: Significance level (default 0.05)
        
    Returns:
        ComparisonSummary with all test results and aggregated statistics
        
    Example:
        >>> scores = {
        ...     'nyc_taxi': {
        ...         'DPGMM': np.array([...]),
        ...         'ARIMA': np.array([...]),
        ...         'MovingAverage': np.array([...])
        ...     },
        ...     'cpu_utilization': {
        ...         'DPGMM': np.array([...]),
        ...         'ARIMA': np.array([...])
        ...     }
        ... }
        >>> summary = compare_all_models(scores)
    """
    if not model_scores:
        raise ValueError("model_scores dictionary cannot be empty")
    
    # Get model names if not provided
    if model_names is None:
        all_models = set()
        for dataset_scores in model_scores.values():
            all_models.update(dataset_scores.keys())
        model_names = sorted(list(all_models))
    
    if len(model_names) < 2:
        raise ValueError("Need at least 2 models to compare")
    
    # Collect all pairwise comparisons
    all_results: List[StatisticalTestResult] = []
    datasets_analyzed = list(model_scores.keys())
    models_compared = model_names.copy()
    
    # Generate all model pairs
    model_pairs = []
    for i, model_a in enumerate(model_names):
        for model_b in model_names[i+1:]:
            model_pairs.append((model_a, model_b))
    
    # Run paired t-tests for each dataset and model pair
    for dataset_name, dataset_scores in model_scores.items():
        # Check that all models have scores for this dataset
        missing_models = [m for m in model_names if m not in dataset_scores]
        if missing_models:
            logger.warning(
                f"Dataset '{dataset_name}' missing scores for: {missing_models}. "
                f"Skipping this dataset for full comparison."
            )
            continue
        
        # Run paired t-test for each model pair
        for model_a, model_b in model_pairs:
            scores_a = dataset_scores[model_a]
            scores_b = dataset_scores[model_b]
            
            try:
                result = paired_ttest_with_bonferroni(
                    scores_a=scores_a,
                    scores_b=scores_b,
                    model_a_name=model_a,
                    model_b_name=model_b,
                    dataset_name=dataset_name,
                    alpha=alpha
                )
                all_results.append(result)
            except ValueError as e:
                logger.warning(
                    f"Skipping {model_a} vs {model_b} on {dataset_name}: {e}"
                )
    
    if not all_results:
        raise ValueError("No valid comparisons could be made")
    
    # Apply Bonferroni correction across all comparisons
    num_comparisons = len(all_results)
    raw_p_values = [r.p_value for r in all_results]
    corrected_p_values, significant_flags = apply_bonferroni_correction(
        raw_p_values, num_comparisons, alpha
    )
    
    # Update results with correction info
    for result, corrected_p, is_significant in zip(
        all_results, corrected_p_values, significant_flags
    ):
        result.corrected_p_value = corrected_p
        result.significant = is_significant
        result.correction_applied = "bonferroni"
    
    # Calculate aggregate statistics
    significant_count = sum(1 for r in all_results if r.significant)
    non_significant_count = num_comparisons - significant_count
    
    # Mean effect sizes per model pair
    effect_sizes: Dict[str, float] = {}
    for result in all_results:
        if result.effect_size is not None:
            pair_key = f"{result.model_a}_vs_{result.model_b}"
            if pair_key not in effect_sizes:
                effect_sizes[pair_key] = []
            effect_sizes[pair_key].append(result.effect_size)
    
    mean_effect_sizes = {
        k: np.mean(v) for k, v in effect_sizes.items()
    }
    
    bonferroni_threshold = alpha / num_comparisons
    
    return ComparisonSummary(
        total_comparisons=num_comparisons,
        significant_results=significant_count,
        non_significant_results=non_significant_count,
        mean_effect_sizes=mean_effect_sizes,
        bonferroni_threshold=bonferroni_threshold,
        comparisons=all_results,
        datasets_analyzed=datasets_analyzed,
        models_compared=models_compared
    )


def format_comparison_summary(summary: ComparisonSummary) -> str:
    """
    Format a ComparisonSummary as a human-readable report string.
    
    Args:
        summary: ComparisonSummary object to format
        
    Returns:
        Formatted string report
    """
    lines = [
        "=" * 70,
        "STATISTICAL COMPARISON SUMMARY",
        "=" * 70,
        "",
        f"Total Comparisons: {summary.total_comparisons}",
        f"Significant Results (p < {summary.bonferroni_threshold:.6f}): {summary.significant_results}",
        f"Non-Significant Results: {summary.non_significant_results}",
        f"Bonferroni Threshold: {summary.bonferroni_threshold:.6f}",
        "",
        "Datasets Analyzed:",
    ]
    
    for dataset in summary.datasets_analyzed:
        lines.append(f"  - {dataset}")
    
    lines.extend([
        "",
        "Models Compared:",
    ])
    
    for model in summary.models_compared:
        lines.append(f"  - {model}")
    
    lines.extend([
        "",
        "Mean Effect Sizes (Cohen's d):",
    ])
    
    for pair, effect in summary.mean_effect_sizes.items():
        lines.append(f"  - {pair}: {effect:.4f}")
    
    lines.extend([
        "",
        "Individual Comparisons:",
        "-" * 70,
    ])
    
    for result in summary.comparisons:
        sig_marker = "✓" if result.significant else "✗"
        lines.extend([
            f"  [{sig_marker}] {result.model_a} vs {result.model_b} on {result.dataset}",
            f"       t-statistic: {result.statistic:.4f}",
            f"       p-value (raw): {result.p_value:.6f}",
            f"       p-value (corrected): {result.corrected_p_value:.6f}",
            f"       effect size: {result.effect_size:.4f}",
            f"       95% CI: [{result.confidence_interval[0]:.4f}, {result.confidence_interval[1]:.4f}]",
            "",
        ])
    
    lines.append("=" * 70)
    
    return "\n".join(lines)


def save_comparison_results(
    summary: ComparisonSummary,
    output_dir: Path,
    filename: str = "statistical_comparison_results.json"
) -> Path:
    """
    Save comparison results to JSON file and text report.
    
    Args:
        summary: ComparisonSummary to save
        output_dir: Directory to save results
        filename: Name of the JSON file
        
    Returns:
        Path to the saved JSON file
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Convert to JSON-serializable format
    json_data = {
        "total_comparisons": summary.total_comparisons,
        "significant_results": summary.significant_results,
        "non_significant_results": summary.non_significant_results,
        "bonferroni_threshold": summary.bonferroni_threshold,
        "datasets_analyzed": summary.datasets_analyzed,
        "models_compared": summary.models_compared,
        "mean_effect_sizes": summary.mean_effect_sizes,
        "comparisons": [
            {
                "test_name": r.test_name,
                "model_a": r.model_a,
                "model_b": r.model_b,
                "dataset": r.dataset,
                "statistic": float(r.statistic),
                "p_value": float(r.p_value),
                "corrected_p_value": float(r.corrected_p_value) if r.corrected_p_value else None,
                "significant": r.significant,
                "effect_size": float(r.effect_size) if r.effect_size else None,
                "confidence_interval": list(r.confidence_interval) if r.confidence_interval else None,
                "correction_applied": r.correction_applied,
            }
            for r in summary.comparisons
        ],
    }
    
    json_path = output_dir / filename
    with open(json_path, "w") as f:
        json.dump(json_data, f, indent=2)
    
    # Also save human-readable text report
    txt_path = output_dir / filename.replace(".json", "_report.txt")
    with open(txt_path, "w") as f:
        f.write(format_comparison_summary(summary))
    
    logger.info(f"Saved comparison results to {json_path}")
    logger.info(f"Saved text report to {txt_path}")
    
    return json_path


def main():
    """
    Main function to demonstrate statistical tests with synthetic data.
    
    This can be run standalone to verify the statistical test implementation.
    """
    # Set random seed for reproducibility
    np.random.seed(42)
    
    # Generate synthetic anomaly scores for demonstration
    n_observations = 1000
    
    # Simulate DPGMM having better discrimination (higher scores for anomalies)
    dpgmm_normal = np.random.normal(0, 1, n_observations // 2)
    dpgmm_anomaly = np.random.normal(3, 0.5, n_observations // 2)
    dpgmm_scores = np.concatenate([dpgmm_normal, dpgmm_anomaly])
    
    # Simulate ARIMA having slightly worse discrimination
    arima_normal = np.random.normal(0, 1.2, n_observations // 2)
    arima_anomaly = np.random.normal(2.5, 0.7, n_observations // 2)
    arima_scores = np.concatenate([arima_normal, arima_anomaly])
    
    # Simulate Moving Average having even worse discrimination
    ma_normal = np.random.normal(0, 1.5, n_observations // 2)
    ma_anomaly = np.random.normal(2.0, 1.0, n_observations // 2)
    ma_scores = np.concatenate([ma_normal, ma_anomaly])
    
    # Create synthetic dataset
    model_scores = {
        "synthetic_dataset_1": {
            "DPGMM": dpgmm_scores,
            "ARIMA": arima_scores,
            "MovingAverage": ma_scores,
        },
    }
    
    # Run comparison
    print("\n" + "=" * 70)
    print("Running Statistical Comparison Tests")
    print("=" * 70 + "\n")
    
    summary = compare_all_models(model_scores, alpha=0.05)
    
    # Print formatted report
    print(format_comparison_summary(summary))
    
    # Save results
    output_dir = Path("data/results")
    output_dir.mkdir(parents=True, exist_ok=True)
    json_path = save_comparison_results(summary, output_dir)
    
    print(f"\nResults saved to: {json_path}")
    print("\n" + "=" * 70)
    
    return summary


if __name__ == "__main__":
    main()
