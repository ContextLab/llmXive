import json
import logging
import os
from pathlib import Path
from typing import Dict, Any, List, Optional
from eval.statistical import run_paired_ttest, run_wilcoxon_test, apply_holm_bonferroni, run_sensitivity_sweep, calculate_false_positive_rate, generate_statistical_report
from eval.metrics import calculate_metrics

logger = logging.getLogger(__name__)

def load_baseline_metrics(baseline_path: Path) -> List[Dict[str, Any]]:
    if not baseline_path.exists():
        raise FileNotFoundError(f"Baseline metrics file not found: {baseline_path}")
    with open(baseline_path, 'r') as f:
        return json.load(f)

def load_heuristic_results(result_path: Path) -> List[Dict[str, Any]]:
    if not result_path.exists():
        raise FileNotFoundError(f"Heuristic results file not found: {result_path}")
    with open(result_path, 'r') as f:
        return json.load(f)

def compute_statistical_significance(
    baseline_results: List[Dict[str, Any]],
    heuristic_results: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Compute primary (t-test) and secondary (Wilcoxon) significance.
    """
    if not baseline_results or not heuristic_results:
        logger.warning("Empty results provided for significance testing.")
        return {"error": "Empty results"}

    b_scores = [r.get('f1_score', 0.0) for r in baseline_results]
    h_scores = [r.get('f1_score', 0.0) for r in heuristic_results]

    if len(b_scores) != len(h_scores):
        raise ValueError("Baseline and heuristic result counts must match.")

    ttest_res = run_paired_ttest(b_scores, h_scores)
    wilcoxon_res = run_wilcoxon_test(b_scores, h_scores)

    # Apply Holm-Bonferroni if multiple tests were run (e.g. across multiple heuristics)
    # Here we assume single comparison, so correction is trivial, but we include it for structure.
    corrected = apply_holm_bonferroni([ttest_res['p_value']])

    return {
        "paired_ttest": ttest_res,
        "wilcoxon": wilcoxon_res,
        "holm_bonferroni": corrected
    }

def generate_sensitivity_analysis(
    baseline_results: List[Dict[str, Any]],
    heuristic_results: List[Dict[str, Any]],
    thresholds: List[float]
) -> Dict[str, Any]:
    """
    Generate sensitivity analysis table with false_positive_rate for each threshold.
    This function explicitly ensures false_positive_rate is calculated and included.
    """
    return run_sensitivity_sweep(heuristic_results, baseline_results, thresholds)

def generate_final_report(
    baseline_path: Path,
    heuristic_path: Path,
    output_path: Path,
    thresholds: List[float] = [0.01, 0.05, 0.1]
) -> Dict[str, Any]:
    """
    Generate the final benchmark report including:
    - F1 scores
    - P-values (Paired t-test primary)
    - False Positive Rate (explicitly calculated per threshold)
    - Sensitivity table
    """
    logger.info(f"Generating final report. Baseline: {baseline_path}, Heuristic: {heuristic_path}")
    
    baseline_results = load_baseline_metrics(baseline_path)
    heuristic_results = load_heuristic_results(heuristic_path)

    # Compute statistical significance
    stats_res = compute_statistical_significance(baseline_results, heuristic_results)
    
    # Generate sensitivity analysis (includes FPR per threshold)
    sensitivity_res = generate_sensitivity_analysis(baseline_results, heuristic_results, thresholds)

    # Aggregate metrics
    baseline_f1 = [r.get('f1_score', 0.0) for r in baseline_results]
    heuristic_f1 = [r.get('f1_score', 0.0) for r in heuristic_results]
    
    final_report = {
        "baseline_metrics": {
            "mean_f1": float(sum(baseline_f1) / len(baseline_f1)) if baseline_f1 else 0.0,
            "count": len(baseline_f1)
        },
        "heuristic_metrics": {
            "mean_f1": float(sum(heuristic_f1) / len(heuristic_f1)) if heuristic_f1 else 0.0,
            "count": len(heuristic_f1),
            "delta_vs_baseline": (float(sum(heuristic_f1) / len(heuristic_f1)) if heuristic_f1 else 0.0) - 
                                 (float(sum(baseline_f1) / len(baseline_f1)) if baseline_f1 else 0.0)
        },
        "statistical_significance": stats_res,
        "sensitivity_analysis": sensitivity_res,
        "thresholds_tested": thresholds
    }

    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w') as f:
        json.dump(final_report, f, indent=2)

    logger.info(f"Final benchmark report saved to {output_path}")
    return final_report

def main():
    # Example usage
    baseline = Path("data/processed/baseline_results.json")
    heuristic = Path("data/processed/heuristic_results.json")
    output = Path("results/benchmark_report.json")
    
    if baseline.exists() and heuristic.exists():
        report = generate_final_report(baseline, heuristic, output)
        print(json.dumps(report, indent=2))
    else:
        logger.info("Sample data not found. Skipping report generation.")

if __name__ == "__main__":
    main()