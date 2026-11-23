import os
import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional

from eval.metrics import calculate_metrics, calculate_perplexity
from eval.statistical import run_paired_ttest, run_wilcoxon_test, apply_holm_bonferroni, run_sensitivity_sweep, calculate_false_positive_rate, generate_statistical_report

logger = logging.getLogger(__name__)

def load_experiment_results(results_dir: Path, heuristic_name: str) -> List[Dict[str, Any]]:
    """Load results for a specific heuristic from the results directory."""
    results_file = results_dir / f"{heuristic_name}_results.json"
    if not results_file.exists():
        logger.error(f"Results file not found: {results_file}")
        return []
    
    with open(results_file, 'r') as f:
        return json.load(f)

def load_baseline_metrics(results_dir: Path) -> Dict[str, Any]:
    """Load baseline (Dense Attention) metrics."""
    baseline_file = results_dir / "baseline_metrics.json"
    if not baseline_file.exists():
        raise FileNotFoundError(f"Baseline metrics file not found: {baseline_file}")
    
    with open(baseline_file, 'r') as f:
        return json.load(f)

def aggregate_benchmark_report(
    heuristic_results: Dict[str, List[Dict[str, Any]]],
    baseline_metrics: Dict[str, Any],
    results_dir: Path
) -> Dict[str, Any]:
    """
    Aggregate results from all heuristics and baseline into a single report.
    
    Schema Requirement: Must include all keys:
    f1_score, p_value, false_positive_rate, sensitivity_table, ttest_stat, wilcoxon_stat, significance_statement
    """
    report = {
        "baseline": baseline_metrics,
        "heuristics": {}
    }

    for heuristic_name, results in heuristic_results.items():
        if not results:
            logger.warning(f"No results for heuristic: {heuristic_name}")
            continue

        # Calculate aggregate metrics for this heuristic
        f1_scores = [r.get('f1_score', 0.0) for r in results if 'f1_score' in r]
        ppl_scores = [r.get('perplexity', 0.0) for r in results if 'perplexity' in r]
        
        avg_f1 = sum(f1_scores) / len(f1_scores) if f1_scores else 0.0
        avg_ppl = sum(ppl_scores) / len(ppl_scores) if ppl_scores else 0.0

        # Calculate delta vs baseline
        baseline_f1 = baseline_metrics.get('f1_score', 0.0)
        baseline_ppl = baseline_metrics.get('perplexity', 0.0)
        
        f1_delta = avg_f1 - baseline_f1
        ppl_delta = avg_ppl - baseline_ppl

        # Prepare heuristic summary
        heuristic_summary = {
            "f1_score": avg_f1,
            "perplexity": avg_ppl,
            "f1_delta_vs_baseline": f1_delta,
            "ppl_delta_vs_baseline": ppl_delta,
            "sample_count": len(results),
            "metrics_per_sample": results
        }

        # Perform statistical tests if we have enough samples
        if len(f1_scores) >= 2 and len(baseline_metrics.get('f1_scores', [])) >= 2:
            baseline_f1_scores = baseline_metrics.get('f1_scores', [])
            
            # Paired t-test
            ttest_stat, ttest_pvalue = run_paired_ttest(baseline_f1_scores, f1_scores)
            
            # Wilcoxon signed-rank test
            wilcoxon_stat, wilcoxon_pvalue = run_wilcoxon_test(baseline_f1_scores, f1_scores)
            
            # Apply Holm-Bonferroni correction if multiple comparisons
            corrected_pvalues = apply_holm_bonferroni([ttest_pvalue, wilcoxon_pvalue])
            
            # Determine significance statement
            significance_statement = "p >= 0.05"
            if corrected_pvalues[0] < 0.05 or corrected_pvalues[1] < 0.05:
                significance_statement = "p < 0.05"
            
            heuristic_summary.update({
                "ttest_stat": float(ttest_stat),
                "p_value": float(corrected_pvalues[0]),
                "wilcoxon_stat": float(wilcoxon_stat),
                "wilcoxon_p_value": float(wilcoxon_pvalue),
                "significance_statement": significance_statement
            })

        # Calculate false positive rate against baseline selection
        # This requires comparing selection sets from heuristic vs baseline
        false_positive_rate = calculate_false_positive_rate(
            heuristic_results=results,
            baseline_results=baseline_metrics.get('selections', [])
        )
        heuristic_summary["false_positive_rate"] = false_positive_rate

        # Generate sensitivity analysis if threshold data is available
        sensitivity_data = []
        for r in results:
            if 'threshold' in r and 'accuracy' in r:
                sensitivity_data.append({
                    "threshold": r['threshold'],
                    "accuracy": r['accuracy'],
                    "false_positive_rate": r.get('false_positive_rate', false_positive_rate)
                })
        
        if sensitivity_data:
          # Run full sensitivity sweep if we have the data
          sweep_results = run_sensitivity_sweep(results)
          heuristic_summary["sensitivity_table"] = sweep_results
        else:
            heuristic_summary["sensitivity_table"] = []

        report["heuristics"][heuristic_name] = heuristic_summary

    return report

def save_report(report: Dict[str, Any], output_path: Path) -> None:
    """Save the aggregated benchmark report to JSON."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2)
    logger.info(f"Benchmark report saved to: {output_path}")

def run_aggregation(
    results_dir: Path,
    output_path: Path,
    heuristic_names: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Main entry point for running the aggregation pipeline.
    
    Args:
        results_dir: Directory containing individual result files
        output_path: Path where the final report will be saved
        heuristic_names: List of heuristic names to aggregate (if None, discovers all)
    
    Returns:
        The aggregated report dictionary
    """
    if heuristic_names is None:
        # Discover heuristics from available files
        heuristic_names = []
        for f in results_dir.glob("*_results.json"):
            name = f.stem.replace("_results", "")
            if name != "baseline_metrics":
                heuristic_names.append(name)
    
    # Load baseline metrics
    baseline_metrics = load_baseline_metrics(results_dir)
    
    # Load and aggregate all heuristic results
    heuristic_results = {}
    for name in heuristic_names:
        heuristic_results[name] = load_experiment_results(results_dir, name)
    
    report = aggregate_benchmark_report(heuristic_results, baseline_metrics, results_dir)
    
    # Save the report
    save_report(report, output_path)
    
    return report

def main():
    """CLI entry point for the aggregator."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Aggregate benchmark results")
    parser.add_argument(
        "--results-dir",
        type=Path,
        default=Path("results"),
        help="Directory containing individual result files"
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("results/benchmark_report.json"),
        help="Path for the output benchmark report"
    )
    parser.add_argument(
        "--heuristics",
        type=str,
        nargs="+",
        default=None,
        help="List of heuristic names to aggregate"
    )
    
    args = parser.parse_args()
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    report = run_aggregation(
        results_dir=args.results_dir,
        output_path=args.output,
        heuristic_names=args.heuristics
    )
    
    print(f"Aggregation complete. Report saved to: {args.output}")
    print(f"Heuristics processed: {list(report['heuristics'].keys())}")

if __name__ == "__main__":
    main()