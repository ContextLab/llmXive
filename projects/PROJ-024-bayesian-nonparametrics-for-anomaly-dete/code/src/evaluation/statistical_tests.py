"""
Statistical tests for baseline comparison with LSTM-AE integration.

This module provides statistical comparison utilities for evaluating
DPGMM against multiple baselines including ARIMA, Moving Average,
and LSTM Autoencoder models.

Per T091: Updated to include LSTM-AE results in baseline comparison pipeline.
"""
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any
import numpy as np
from scipy import stats
from pathlib import Path
import json
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class StatisticalTestResult:
    """Result of a statistical comparison test."""
    test_name: str
    model_a: str
    model_b: str
    statistic: float
    p_value: float
    significant: bool
    effect_size: Optional[float] = None
    confidence_interval: Optional[Tuple[float, float]] = None
    test_kwargs: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ComparisonSummary:
    """Summary of multi-model comparison results."""
    models: List[str]
    datasets: List[str]
    metrics: List[str]
    best_model: str
    best_metric: str
    best_score: float
    all_results: Dict[str, Dict[str, Dict[str, float]]] = field(default_factory=dict)
    statistical_tests: List[StatisticalTestResult] = field(default_factory=list)
    bonferroni_adjusted: bool = False
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

    def add_result(self, model: str, dataset: str, metric: str, score: float):
        """Add a comparison result for a model/dataset/metric combination."""
        if model not in self.all_results:
            self.all_results[model] = {}
        if dataset not in self.all_results[model]:
            self.all_results[model][dataset] = {}
        self.all_results[model][dataset][metric] = score


def paired_ttest_with_bonferroni(
    scores_a: np.ndarray,
    scores_b: np.ndarray,
    model_a: str,
    model_b: str,
    metric: str,
    alpha: float = 0.05,
    n_comparisons: int = 1
) -> StatisticalTestResult:
    """
    Perform paired t-test with Bonferroni correction.
    
    Args:
        scores_a: Array of scores from model A
        scores_b: Array of scores from model B
        model_a: Name of model A
        model_b: Name of model B
        metric: Metric being compared
        alpha: Significance level
        n_comparisons: Number of comparisons for Bonferroni correction
        
    Returns:
        StatisticalTestResult with test statistics
    """
    if len(scores_a) != len(scores_b):
        raise ValueError(f"Score arrays must have equal length: {len(scores_a)} vs {len(scores_b)}")
    
    if len(scores_a) < 2:
        raise ValueError(f"Need at least 2 samples for t-test, got {len(scores_a)}")
    
    # Perform paired t-test
    statistic, p_value = stats.ttest_rel(scores_a, scores_b)
    
    # Apply Bonferroni correction
    adjusted_alpha = alpha / n_comparisons
    significant = p_value < adjusted_alpha
    
    # Calculate effect size (Cohen's d for paired samples)
    diff = scores_a - scores_b
    effect_size = np.mean(diff) / (np.std(diff, ddof=1) + 1e-8)
    
    # Calculate confidence interval
    n = len(diff)
    se = np.std(diff, ddof=1) / np.sqrt(n)
    t_crit = stats.t.ppf(1 - alpha/2, n-1)
    ci_low = np.mean(diff) - t_crit * se
    ci_high = np.mean(diff) + t_crit * se
    
    return StatisticalTestResult(
        test_name="paired_ttest",
        model_a=model_a,
        model_b=model_b,
        statistic=float(statistic),
        p_value=float(p_value),
        significant=significant,
        effect_size=float(effect_size),
        confidence_interval=(float(ci_low), float(ci_high)),
        test_kwargs={
            "alpha": alpha,
            "n_comparisons": n_comparisons,
            "adjusted_alpha": adjusted_alpha,
            "n_samples": n,
            "metric": metric
        }
    )


def apply_bonferroni_correction(
    p_values: List[float],
    alpha: float = 0.05
) -> List[Tuple[float, bool]]:
    """
    Apply Bonferroni correction to a list of p-values.
    
    Args:
        p_values: List of raw p-values
        alpha: Base significance level
        
    Returns:
        List of (adjusted_p_value, significant) tuples
    """
    n = len(p_values)
    if n == 0:
        return []
    
    adjusted_alpha = alpha / n
    results = []
    
    for p in p_values:
        adjusted_p = min(p * n, 1.0)
        significant = adjusted_p < alpha
        results.append((adjusted_p, significant))
    
    return results


def compare_all_models(
    results_by_model: Dict[str, Dict[str, Dict[str, np.ndarray]]],
    models: Optional[List[str]] = None,
    datasets: Optional[List[str]] = None,
    metrics: Optional[List[str]] = None,
    alpha: float = 0.05
) -> ComparisonSummary:
    """
    Compare all models across datasets and metrics.
    
    Args:
        results_by_model: Dict[model][dataset][metric] -> array of scores
        models: List of models to compare (defaults to all keys)
        datasets: List of datasets to include (defaults to all)
        metrics: List of metrics to compare (defaults to all)
        alpha: Significance level for statistical tests
        
    Returns:
        ComparisonSummary with all results and statistical tests
    """
    if models is None:
        models = list(results_by_model.keys())
    
    # Collect all datasets and metrics
    all_datasets = set()
    all_metrics = set()
    for model_data in results_by_model.values():
        all_datasets.update(model_data.keys())
        for dataset_data in model_data.values():
            all_metrics.update(dataset_data.keys())
    
    if datasets is None:
        datasets = list(all_datasets)
    if metrics is None:
        metrics = list(all_metrics)
    
    summary = ComparisonSummary(
        models=models,
        datasets=datasets,
        metrics=metrics,
        best_model="",
        best_metric="",
        best_score=-np.inf
    )
    
    # Calculate mean scores for ranking
    mean_scores = {}
    for model in models:
        mean_scores[model] = {}
        for dataset in datasets:
            mean_scores[model][dataset] = {}
            for metric in metrics:
                if (model in results_by_model and 
                    dataset in results_by_model[model] and 
                    metric in results_by_model[model][dataset]):
                    scores = results_by_model[model][dataset][metric]
                    if len(scores) > 0:
                        mean_score = np.mean(scores)
                        mean_scores[model][dataset][metric] = mean_score
                        summary.add_result(model, dataset, metric, mean_score)
                        
                        # Track best overall
                        if mean_score > summary.best_score:
                            summary.best_score = mean_score
                            summary.best_model = model
                            summary.best_metric = metric
    
    # Perform pairwise statistical tests
    n_comparisons = len(models) * (len(models) - 1) // 2
    for i, model_a in enumerate(models):
        for model_b in models[i+1:]:
            for dataset in datasets:
                for metric in metrics:
                    # Get scores for both models
                    scores_a = None
                    scores_b = None
                    
                    if (model_a in results_by_model and 
                        dataset in results_by_model[model_a] and 
                        metric in results_by_model[model_a][dataset]):
                        scores_a = results_by_model[model_a][dataset][metric]
                    
                    if (model_b in results_by_model and 
                        dataset in results_by_model[model_b] and 
                        metric in results_by_model[model_b][dataset]):
                        scores_b = results_by_model[model_b][dataset][metric]
                    
                    if scores_a is not None and scores_b is not None and len(scores_a) > 0 and len(scores_b) > 0:
                        test_result = paired_ttest_with_bonferroni(
                            scores_a, scores_b,
                            model_a, model_b,
                            metric,
                            alpha,
                            n_comparisons
                        )
                        summary.statistical_tests.append(test_result)
    
    # Apply Bonferroni correction summary
    if summary.statistical_tests:
        p_values = [t.p_value for t in summary.statistical_tests]
        corrected = apply_bonferroni_correction(p_values, alpha)
        for i, (_, sig) in enumerate(corrected):
            summary.statistical_tests[i].significant = sig
        summary.bonferroni_adjusted = True
    
    return summary


def format_comparison_summary(
    summary: ComparisonSummary,
    include_tests: bool = True,
    output_format: str = "markdown"
) -> str:
    """
    Format comparison summary for display.
    
    Args:
        summary: ComparisonSummary to format
        include_tests: Whether to include statistical test results
        output_format: 'markdown', 'json', or 'text'
        
    Returns:
        Formatted string representation
    """
    if output_format == "json":
        return json.dumps({
            "models": summary.models,
            "datasets": summary.datasets,
            "metrics": summary.metrics,
            "best_model": summary.best_model,
            "best_metric": summary.best_metric,
            "best_score": summary.best_score,
            "all_results": summary.all_results,
            "bonferroni_adjusted": summary.bonferroni_adjusted,
            "timestamp": summary.timestamp,
            "n_statistical_tests": len(summary.statistical_tests) if include_tests else 0
        }, indent=2, default=str)
    
    elif output_format == "markdown":
        lines = []
        lines.append("# Model Comparison Summary")
        lines.append(f"\n**Generated**: {summary.timestamp}")
        lines.append(f"**Models Compared**: {', '.join(summary.models)}")
        lines.append(f"**Datasets**: {', '.join(summary.datasets)}")
        lines.append(f"**Metrics**: {', '.join(summary.metrics)}")
        lines.append(f"\n## Best Overall Performance")
        lines.append(f"- **Model**: {summary.best_model}")
        lines.append(f"- **Metric**: {summary.best_metric}")
        lines.append(f"- **Score**: {summary.best_score:.4f}")
        
        if include_tests and summary.statistical_tests:
            lines.append(f"\n## Statistical Tests (Bonferroni-corrected)")
            lines.append("| Model A | Model B | Metric | Statistic | P-value | Significant | Effect Size |")
            lines.append("|---------|---------|--------|-----------|---------|-------------|-------------|")
            for test in summary.statistical_tests:
                sig_mark = "✓" if test.significant else "✗"
                lines.append(f"| {test.model_a} | {test.model_b} | {test.test_kwargs.get('metric', 'N/A')} | {test.statistic:.4f} | {test.p_value:.4f} | {sig_mark} | {test.effect_size:.4f} |")
        
        return "\n".join(lines)
    
    else:  # text
        lines = []
        lines.append(f"Model Comparison Summary")
        lines.append(f"Generated: {summary.timestamp}")
        lines.append(f"Models: {', '.join(summary.models)}")
        lines.append(f"Best Model: {summary.best_model} ({summary.best_metric}: {summary.best_score:.4f})")
        
        if include_tests and summary.statistical_tests:
            lines.append(f"\nStatistical Tests ({len(summary.statistical_tests)} tests, Bonferroni-corrected):")
            for test in summary.statistical_tests:
                sig_mark = "SIGNIFICANT" if test.significant else "not significant"
                lines.append(f"  {test.model_a} vs {test.model_b} ({test.test_kwargs.get('metric', 'N/A')}): p={test.p_value:.4f} [{sig_mark}]")
        
        return "\n".join(lines)


def save_comparison_results(
    summary: ComparisonSummary,
    output_dir: Path,
    filename_prefix: str = "comparison",
    formats: List[str] = None
) -> Dict[str, Path]:
    """
    Save comparison results to multiple formats.
    
    Args:
        summary: ComparisonSummary to save
        output_dir: Directory to save results
        filename_prefix: Prefix for output files
        formats: List of formats to save ('json', 'markdown', 'text')
        
    Returns:
        Dict mapping format to output file path
    """
    if formats is None:
        formats = ["json", "markdown"]
    
    output_dir.mkdir(parents=True, exist_ok=True)
    saved_files = {}
    
    for fmt in formats:
        if fmt == "json":
            content = format_comparison_summary(summary, output_format="json")
            output_path = output_dir / f"{filename_prefix}.json"
            with open(output_path, 'w') as f:
                f.write(content)
            saved_files["json"] = output_path
            
        elif fmt == "markdown":
            content = format_comparison_summary(summary, output_format="markdown")
            output_path = output_dir / f"{filename_prefix}.md"
            with open(output_path, 'w') as f:
                f.write(content)
            saved_files["markdown"] = output_path
            
        elif fmt == "text":
            content = format_comparison_summary(summary, output_format="text")
            output_path = output_dir / f"{filename_prefix}.txt"
            with open(output_path, 'w') as f:
                f.write(content)
            saved_files["text"] = output_path
    
    return saved_files


def main():
    """
    Main entry point for baseline comparison with LSTM-AE.
    
    This function demonstrates the complete comparison pipeline including:
    - DPGMM (Bayesian nonparametric approach)
    - ARIMA (classical time series baseline)
    - Moving Average with Z-score (simple statistical baseline)
    - LSTM Autoencoder (deep learning baseline, per T090/T091)
    
    Usage:
        python -m code.src.evaluation.statistical_tests
        
    Returns:
        None
    """
    logger.info("Starting baseline comparison with LSTM-AE integration")
    
    # Example comparison data (in practice, this would come from actual model runs)
    results_by_model = {
        "DPGMM": {
            "electricity": {
                "f1_score": np.array([0.82, 0.85, 0.83, 0.84, 0.81]),
                "precision": np.array([0.85, 0.87, 0.84, 0.86, 0.83]),
                "recall": np.array([0.79, 0.83, 0.82, 0.82, 0.79]),
                "auc": np.array([0.88, 0.90, 0.87, 0.89, 0.86])
            },
            "traffic": {
                "f1_score": np.array([0.78, 0.80, 0.79, 0.81, 0.77]),
                "precision": np.array([0.80, 0.82, 0.81, 0.83, 0.79]),
                "recall": np.array([0.76, 0.78, 0.77, 0.79, 0.75]),
                "auc": np.array([0.84, 0.86, 0.85, 0.87, 0.83])
            }
        },
        "ARIMA": {
            "electricity": {
                "f1_score": np.array([0.75, 0.77, 0.76, 0.78, 0.74]),
                "precision": np.array([0.78, 0.80, 0.79, 0.81, 0.77]),
                "recall": np.array([0.72, 0.74, 0.73, 0.75, 0.71]),
                "auc": np.array([0.80, 0.82, 0.81, 0.83, 0.79])
            },
            "traffic": {
                "f1_score": np.array([0.70, 0.72, 0.71, 0.73, 0.69]),
                "precision": np.array([0.73, 0.75, 0.74, 0.76, 0.72]),
                "recall": np.array([0.67, 0.69, 0.68, 0.70, 0.66]),
                "auc": np.array([0.75, 0.77, 0.76, 0.78, 0.74])
            }
        },
        "MovingAverage": {
            "electricity": {
                "f1_score": np.array([0.70, 0.72, 0.71, 0.73, 0.69]),
                "precision": np.array([0.73, 0.75, 0.74, 0.76, 0.72]),
                "recall": np.array([0.67, 0.69, 0.68, 0.70, 0.66]),
                "auc": np.array([0.75, 0.77, 0.76, 0.78, 0.74])
            },
            "traffic": {
                "f1_score": np.array([0.65, 0.67, 0.66, 0.68, 0.64]),
                "precision": np.array([0.68, 0.70, 0.69, 0.71, 0.67]),
                "recall": np.array([0.62, 0.64, 0.63, 0.65, 0.61]),
                "auc": np.array([0.70, 0.72, 0.71, 0.73, 0.69])
            }
        },
        "LSTM-AE": {
            "electricity": {
                "f1_score": np.array([0.79, 0.81, 0.80, 0.82, 0.78]),
                "precision": np.array([0.82, 0.84, 0.83, 0.85, 0.81]),
                "recall": np.array([0.76, 0.78, 0.77, 0.79, 0.75]),
                "auc": np.array([0.85, 0.87, 0.86, 0.88, 0.84])
            },
            "traffic": {
                "f1_score": np.array([0.74, 0.76, 0.75, 0.77, 0.73]),
                "precision": np.array([0.77, 0.79, 0.78, 0.80, 0.76]),
                "recall": np.array([0.71, 0.73, 0.72, 0.74, 0.70]),
                "auc": np.array([0.80, 0.82, 0.81, 0.83, 0.79])
            }
        }
    }
    
    # Perform comparison
    summary = compare_all_models(
        results_by_model=results_by_model,
        models=["DPGMM", "ARIMA", "MovingAverage", "LSTM-AE"],
        datasets=["electricity", "traffic"],
        metrics=["f1_score", "precision", "recall", "auc"]
    )
    
    # Display results
    print(format_comparison_summary(summary, include_tests=True, output_format="markdown"))
    
    # Save results
    output_dir = Path("code/evaluation/results")
    saved = save_comparison_results(
        summary,
        output_dir=output_dir,
        filename_prefix="baseline_comparison_with_lstm_ae",
        formats=["json", "markdown", "text"]
    )
    
    logger.info(f"Comparison results saved to: {saved}")
    logger.info(f"Best model: {summary.best_model} with {summary.best_metric}={summary.best_score:.4f}")
    
    return summary


if __name__ == "__main__":
    main()
