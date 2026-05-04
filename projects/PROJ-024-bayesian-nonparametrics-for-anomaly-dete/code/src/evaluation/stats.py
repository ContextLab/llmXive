"""
Statistical significance testing utilities for model comparison.

Implements paired t-tests with Bonferroni correction for comparing
anomaly detection model performance across multiple datasets.
"""
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any
import numpy as np
from scipy import stats
from pathlib import Path
import json
import logging
from datetime import datetime

@dataclass
class PairedTTestResult:
    """Result from a paired t-test comparison."""
    statistic: float
    pvalue: float
    mean_difference: float
    std_difference: float
    n_pairs: int
    confidence_interval: Tuple[float, float]
    significant: bool
    alpha: float = 0.05

@dataclass
class ComparisonSummary:
    """Summary of all model comparisons."""
    models_compared: List[str]
    metric: str
    test_type: str
    results: List[PairedTTestResult]
    bonferroni_adjusted: bool
    summary_table: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    generated_at: str = field(default_factory=lambda: datetime.now().isoformat())

def paired_ttest(
    scores1: np.ndarray,
    scores2: np.ndarray,
    alternative: str = "two-sided",
    alpha: float = 0.05
) -> PairedTTestResult:
    """
    Perform paired t-test between two sets of scores.
    
    Args:
        scores1: First set of scores (e.g., model A F1 scores across datasets)
        scores2: Second set of scores (e.g., model B F1 scores across datasets)
        alternative: 'two-sided', 'greater', or 'less'
        alpha: Significance level for determining significance
    
    Returns:
        PairedTTestResult with test statistics and significance determination
    
    Raises:
        ValueError: If input arrays have different lengths or are empty
    """
    scores1 = np.asarray(scores1)
    scores2 = np.asarray(scores2)
    
    if len(scores1) != len(scores2):
        raise ValueError(f"Arrays must have same length: {len(scores1)} vs {len(scores2)}")
    
    if len(scores1) == 0:
        raise ValueError("Input arrays cannot be empty")
    
    if len(scores1) < 2:
        raise ValueError("Need at least 2 pairs for t-test")
    
    # Compute differences
    differences = scores1 - scores2
    mean_diff = np.mean(differences)
    std_diff = np.std(differences, ddof=1)
    n_pairs = len(differences)
    
    # Perform paired t-test
    t_stat, p_value = stats.ttest_rel(scores1, scores2, alternative=alternative)
    
    # Compute confidence interval
    if n_pairs > 1:
        se = std_diff / np.sqrt(n_pairs)
        t_crit = stats.t.ppf(1 - alpha / 2, df=n_pairs - 1)
        ci_lower = mean_diff - t_crit * se
        ci_upper = mean_diff + t_crit * se
    else:
        ci_lower = ci_upper = mean_diff
    
    return PairedTTestResult(
        statistic=float(t_stat),
        pvalue=float(p_value),
        mean_difference=float(mean_diff),
        std_difference=float(std_diff),
        n_pairs=n_pairs,
        confidence_interval=(float(ci_lower), float(ci_upper)),
        significant=float(p_value) < alpha,
        alpha=alpha
    )

def apply_bonferroni_correction(
    pvalues: List[float],
    alpha: float = 0.05
) -> Tuple[List[float], List[bool]]:
    """
    Apply Bonferroni correction for multiple comparisons.
    
    Args:
        pvalues: List of raw p-values from individual tests
        alpha: Family-wise error rate threshold
    
    Returns:
        Tuple of (adjusted p-values, significance decisions)
    """
    n_tests = len(pvalues)
    if n_tests == 0:
        return [], []
    
    # Bonferroni adjusted alpha
    adjusted_alpha = alpha / n_tests
    
    # Adjust p-values (capped at 1.0)
    adjusted_pvalues = [min(p * n_tests, 1.0) for p in pvalues]
    
    # Determine significance
    significant = [p < alpha for p in adjusted_pvalues]
    
    return adjusted_pvalues, significant

def paired_ttest_with_bonferroni(
    model_scores: Dict[str, np.ndarray],
    baseline_name: str,
    metric: str = "f1_score",
    alpha: float = 0.05
) -> ComparisonSummary:
    """
    Perform paired t-tests comparing all models against a baseline
    with Bonferroni correction for multiple comparisons.
    
    Args:
        model_scores: Dict mapping model name to array of scores across datasets
        baseline_name: Name of the baseline model to compare against
        metric: Name of the metric being compared
        alpha: Significance level
    
    Returns:
        ComparisonSummary with all test results
    """
    if baseline_name not in model_scores:
        raise ValueError(f"Baseline model '{baseline_name}' not found in model_scores")
    
    baseline_scores = model_scores[baseline_name]
    models_compared = [name for name in model_scores.keys() if name != baseline_name]
    
    results = []
    pvalues = []
    
    for model_name in models_compared:
        model_scores_arr = model_scores[model_name]
        
        if len(model_scores_arr) != len(baseline_scores):
            logging.warning(
                f"Skipping {model_name}: score array length mismatch "
                f"({len(model_scores_arr)} vs {len(baseline_scores)})"
            )
            continue
        
        result = paired_ttest(
            scores1=model_scores_arr,
            scores2=baseline_scores,
            alternative="two-sided",
            alpha=alpha
        )
        results.append(result)
        pvalues.append(result.pvalue)
    
    # Apply Bonferroni correction
    if pvalues:
        adjusted_pvalues, significant_flags = apply_bonferroni_correction(
            pvalues, alpha
        )
        
        # Update significance in results
        for i, result in enumerate(results):
            result.significant = significant_flags[i]
            result.pvalue = adjusted_pvalues[i]
    
    # Build summary table
    summary_table = {}
    for i, model_name in enumerate(models_compared):
        result = results[i]
        summary_table[model_name] = {
            "t_statistic": result.statistic,
            "p_value": result.pvalue,
            "mean_difference": result.mean_difference,
            "significant": result.significant,
            "ci_lower": result.confidence_interval[0],
            "ci_upper": result.confidence_interval[1]
        }
    
    return ComparisonSummary(
        models_compared=models_compared,
        metric=metric,
        test_type="paired_ttest_bonferroni",
        results=results,
        bonferroni_adjusted=True,
        summary_table=summary_table,
        generated_at=datetime.now().isoformat()
    )

def compare_all_models(
    model_scores: Dict[str, np.ndarray],
    metric: str = "f1_score",
    alpha: float = 0.05
) -> Dict[str, ComparisonSummary]:
    """
    Compare all models pairwise with Bonferroni correction.
    
    Args:
        model_scores: Dict mapping model name to array of scores
        metric: Name of the metric being compared
        alpha: Significance level
    
    Returns:
        Dict mapping each model to its comparison summary against others
    """
    model_names = list(model_scores.keys())
    comparisons = {}
    
    for model_name in model_names:
        # Create dict with this model as baseline
        baseline_scores = model_scores[model_name]
        other_scores = {
            name: scores for name, scores in model_scores.items()
            if name != model_name
        }
        
        summary = paired_ttest_with_bonferroni(
            model_scores={model_name: baseline_scores, **other_scores},
            baseline_name=model_name,
            metric=metric,
            alpha=alpha
        )
        comparisons[model_name] = summary
    
    return comparisons

def format_comparison_summary(summary: ComparisonSummary) -> str:
    """
    Format a comparison summary as a markdown table.
    
    Args:
        summary: ComparisonSummary to format
    
    Returns:
        Markdown-formatted string
    """
    lines = [
        f"# Statistical Comparison Summary",
        f"",
        f"**Metric**: {summary.metric}",
        f"**Test Type**: {summary.test_type}",
        f"**Bonferroni Adjusted**: {summary.bonferroni_adjusted}",
        f"**Generated**: {summary.generated_at}",
        f"",
        f"## Results",
        f"",
        f"| Model | t-statistic | p-value | Mean Diff | Significant | CI Lower | CI Upper |",
        f"|-------|-------------|---------|-----------|-------------|----------|----------|"
    ]
    
    for model_name, table_entry in summary.summary_table.items():
        sig_mark = "✓" if table_entry["significant"] else "✗"
        lines.append(
            f"| {model_name} | {table_entry['t_statistic']:.4f} | "
            f"{table_entry['p_value']:.4f} | {table_entry['mean_difference']:.4f} | "
            f"{sig_mark} | {table_entry['ci_lower']:.4f} | {table_entry['ci_upper']:.4f} |"
        )
    
    return "\n".join(lines)

def save_comparison_results(
    summary: ComparisonSummary,
    output_path: Path,
    format: str = "json"
) -> None:
    """
    Save comparison results to file.
    
    Args:
        summary: ComparisonSummary to save
        output_path: Path to output file
        format: 'json' or 'markdown'
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    if format == "json":
        # Convert to JSON-serializable format
        data = {
            "models_compared": summary.models_compared,
            "metric": summary.metric,
            "test_type": summary.test_type,
            "bonferroni_adjusted": summary.bonferroni_adjusted,
            "generated_at": summary.generated_at,
            "results": [
                {
                    "statistic": r.statistic,
                    "pvalue": r.pvalue,
                    "mean_difference": r.mean_difference,
                    "std_difference": r.std_difference,
                    "n_pairs": r.n_pairs,
                    "confidence_interval": r.confidence_interval,
                    "significant": r.significant,
                    "alpha": r.alpha
                }
                for r in summary.results
            ],
            "summary_table": summary.summary_table
        }
        
        with open(output_path, 'w') as f:
            json.dump(data, f, indent=2)
    
    elif format == "markdown":
        markdown = format_comparison_summary(summary)
        with open(output_path, 'w') as f:
            f.write(markdown)
    
    else:
        raise ValueError(f"Unsupported format: {format}. Use 'json' or 'markdown'")

def main() -> None:
    """
    Main entry point for standalone testing.
    
    Demonstrates usage of statistical comparison functions.
    """
    # Create sample data for demonstration
    np.random.seed(42)
    n_datasets = 10
    
    # Simulate F1 scores across datasets
    model_scores = {
        "DPGMM": np.random.normal(0.82, 0.05, n_datasets),
        "ARIMA": np.random.normal(0.78, 0.06, n_datasets),
        "MovingAverage": np.random.normal(0.75, 0.07, n_datasets),
        "LSTMAE": np.random.normal(0.80, 0.05, n_datasets)
    }
    
    # Compare all models against DPGMM
    summary = paired_ttest_with_bonferroni(
        model_scores=model_scores,
        baseline_name="DPGMM",
        metric="f1_score",
        alpha=0.05
    )
    
    # Print results
    print(format_comparison_summary(summary))
    
    # Save results
    output_dir = Path("data/processed/results")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    save_comparison_results(
        summary,
        output_dir / "statistical_comparison.json",
        format="json"
    )
    save_comparison_results(
        summary,
        output_dir / "statistical_comparison.md",
        format="markdown"
    )
    
    print(f"\nResults saved to {output_dir}")

if __name__ == "__main__":
    main()
