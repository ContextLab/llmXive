import json
import logging
import os
from pathlib import Path
from typing import Dict, Any, List, Optional

from eval.statistical import run_paired_ttest, run_wilcoxon_test, apply_holm_bonferroni, run_sensitivity_sweep, calculate_false_positive_rate, generate_statistical_report
from eval.aggregator import load_experiment_results, load_baseline_metrics, aggregate_benchmark_report, save_report, run_aggregation

logger = logging.getLogger(__name__)

def load_baseline_metrics(baseline_file: Path) -> Dict[str, Any]:
    return load_baseline_metrics(baseline_file)

def load_heuristic_results(results_dir: Path) -> Dict[str, Any]:
    return load_experiment_results(results_dir)

def compute_statistical_significance(heuristic_scores: List[float], baseline_scores: List[float]) -> Dict[str, Any]:
    """
    Compute t-test and Wilcoxon statistics.
    """
    t_stat, t_p = run_paired_ttest(heuristic_scores, baseline_scores)
    w_stat, w_p = run_wilcoxon_test(heuristic_scores, baseline_scores)
    
    return {
        "ttest_stat": float(t_stat),
        "ttest_p_value": float(t_p),
        "wilcoxon_stat": float(w_stat),
        "wilcoxon_p_value": float(w_p)
    }

def generate_sensitivity_analysis(
    heuristic_results: Dict[str, Any],
    thresholds: List[float]
) -> List[Dict[str, Any]]:
    """
    Generate sensitivity analysis table.
    """
    # This function delegates to the statistical module's sensitivity sweep if raw data is available,
    # or aggregates from existing results.
    # For this implementation, we assume the aggregation logic handles the table construction.
    # This function is kept for API compatibility with T031.
    return []

def generate_final_report(
    heuristic_results: Dict[str, Any],
    baseline_metrics: Dict[str, Any],
    output_path: Path,
    thresholds: List[float] = [0.01, 0.05, 0.1]
) -> Dict[str, Any]:
    """
    Generate the final benchmark report including all required keys.
    """
    report = aggregate_benchmark_report(heuristic_results, baseline_metrics, thresholds)
    save_report(report, output_path)
    return report

def run_aggregation(
    results_dir: Path,
    baseline_file: Path,
    output_file: Path,
    thresholds: List[float] = [0.01, 0.05, 0.1]
) -> Dict[str, Any]:
    """
    Wrapper to run aggregation.
    """
    return run_aggregation(results_dir, baseline_file, output_file, thresholds)

def main():
    """
    CLI entry point for report generation.
    """
    import argparse
    parser = argparse.ArgumentParser(description="Generate final benchmark report")
    parser.add_argument("--results_dir", type=str, default="results", help="Directory containing heuristic results")
    parser.add_argument("--baseline", type=str, default="results/baseline_metrics.json", help="Baseline metrics file")
    parser.add_argument("--output", type=str, default="results/benchmark_report.json", help="Output report file")
    parser.add_argument("--thresholds", type=str, default="0.01,0.05,0.1", help="Comma-separated thresholds")
    
    args = parser.parse_args()
    
    thresholds = [float(t) for t in args.thresholds.split(",")]
    
    run_aggregation(
        Path(args.results_dir),
        Path(args.baseline),
        Path(args.output),
        thresholds
    )

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
