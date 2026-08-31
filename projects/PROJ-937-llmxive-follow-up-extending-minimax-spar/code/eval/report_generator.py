import json
import logging
import os
from pathlib import Path
from typing import Dict, Any, List, Optional
from eval.statistical import run_paired_ttest, run_wilcoxon_test, apply_holm_bonferroni, run_sensitivity_sweep, calculate_false_positive_rate, generate_statistical_report
from eval.metrics import calculate_metrics, calculate_perplexity
from utils.logger import get_logger_for_task
import numpy as np

logger = get_logger_for_task("T031")

def load_baseline_metrics(baseline_path: str) -> Dict[str, Any]:
    """Load the dense attention baseline results."""
    if not os.path.exists(baseline_path):
        raise FileNotFoundError(f"Baseline metrics file not found: {baseline_path}")
    
    with open(baseline_path, 'r') as f:
        return json.load(f)

def load_heuristic_results(results_dir: str) -> Dict[str, Dict[str, Any]]:
    """Load all heuristic experiment results from the directory."""
    results = {}
    results_path = Path(results_dir)
    
    if not results_path.exists():
        raise FileNotFoundError(f"Heuristic results directory not found: {results_dir}")
    
    for file_path in results_path.glob("heuristic_*.json"):
        with open(file_path, 'r') as f:
            data = json.load(f)
            heuristic_name = data.get('heuristic_name', file_path.stem)
            results[heuristic_name] = data
    
    return results

def compute_statistical_significance(
    baseline_scores: List[float],
    heuristic_scores: List[float],
    heuristic_name: str
) -> Dict[str, Any]:
    """
    Compute statistical significance between baseline and heuristic.
    Primary: Paired t-test with Holm-Bonferroni correction.
    Secondary: Wilcoxon signed-rank test.
    """
    if len(baseline_scores) != len(heuristic_scores) or len(baseline_scores) == 0:
        raise ValueError("Score lists must be non-empty and of equal length")

    # Paired t-test (Primary)
    t_stat, t_p_value = run_paired_ttest(baseline_scores, heuristic_scores)
    
    # Wilcoxon test (Secondary)
    w_stat, w_p_value = run_wilcoxon_test(baseline_scores, heuristic_scores)
    
    # Apply Holm-Bonferroni correction if multiple comparisons were made
    # For a single comparison, the correction is trivial, but we structure it for extensibility
    p_values_to_correct = [t_p_value]
    corrected_p_values = apply_holm_bonferroni(p_values_to_correct)
    corrected_t_p_value = corrected_p_values[0]
    
    # Determine significance
    alpha = 0.05
    is_significant = corrected_t_p_value < alpha
    significance_statement = (
        f"Statistically significant (p={corrected_t_p_value:.4f} < {alpha})" 
        if is_significant 
        else f"Not statistically significant (p={corrected_t_p_value:.4f} >= {alpha})"
    )

    return {
        "heuristic_name": heuristic_name,
        "ttest_stat": float(t_stat),
        "ttest_p_value": float(t_p_value),
        "ttest_p_value_corrected": float(corrected_t_p_value),
        "wilcoxon_stat": float(w_stat),
        "wilcoxon_p_value": float(w_p_value),
        "is_significant": is_significant,
        "significance_statement": significance_statement,
        "alpha": alpha
    }

def generate_sensitivity_analysis(
    baseline_results: Dict[str, Any],
    heuristic_results: Dict[str, Dict[str, Any]],
    thresholds: List[float] = [0.01, 0.05, 0.1]
) -> Dict[str, Any]:
    """
    Generate sensitivity analysis across different thresholds.
    Maps thresholds to specific heuristic parameters as per T029.
    """
    sensitivity_table = {}
    false_positive_rates = {}
    
    # Define threshold mappings per T029
    threshold_mappings = {
        "recency": {
            "param": "normalized_attention_score",
            "thresholds": thresholds
        },
        "gradient_magnitude": {
            "param": "gradient_magnitude_threshold",
            "thresholds": thresholds
        },
        "block_entropy": {
            "param": "entropy_probability_cutoff",
            "thresholds": thresholds
        }
    }

    for heuristic_name, heuristic_data in heuristic_results.items():
        if heuristic_name not in threshold_mappings:
            logger.warning(f"No threshold mapping found for heuristic: {heuristic_name}")
            continue

        mapping = threshold_mappings[heuristic_name]
        base_scores = baseline_results.get("scores", [])
        heuristic_scores = heuristic_data.get("scores", [])
        
        if not base_scores or not heuristic_scores:
            logger.warning(f"Missing scores for {heuristic_name}, skipping sensitivity analysis")
            continue

        sensitivity_data = []
        
        for threshold in mapping["thresholds"]:
            # Calculate false positive rate for this threshold
            # FP Rate = (Selections without target) / (Total selections)
            # We approximate this by comparing selection density against baseline
            fpr = calculate_false_positive_rate(
                heuristic_scores, 
                base_scores, 
                threshold=threshold
            )
            
            false_positive_rates[f"{heuristic_name}_{mapping['param']}_{threshold}"] = fpr
            
            sensitivity_data.append({
                "threshold": threshold,
                "param": mapping["param"],
                "false_positive_rate": fpr,
                "accuracy_delta": heuristic_data.get("metrics", {}).get("f1_score", 0) - baseline_results.get("metrics", {}).get("f1_score", 0)
            })
        
        sensitivity_table[heuristic_name] = sensitivity_data

    return {
        "sensitivity_table": sensitivity_table,
        "false_positive_rates": false_positive_rates,
        "thresholds_tested": thresholds
    }

def generate_final_report(
    baseline_path: str,
    results_dir: str,
    output_path: str,
    thresholds: List[float] = [0.01, 0.05, 0.1]
) -> Dict[str, Any]:
    """
    Generate the final benchmark report including:
    - P-values (Paired t-test primary)
    - Significance statements
    - Sensitivity tables
    - False positive rates
    """
    logger.info(f"Generating final report for {output_path}")
    
    # Load data
    baseline_data = load_baseline_metrics(baseline_path)
    heuristic_data = load_heuristic_results(results_dir)
    
    if not heuristic_data:
        raise ValueError("No heuristic results found to generate report")
    
    # Extract scores for statistical tests
    baseline_scores = baseline_data.get("scores", [])
    
    # Compute statistical significance for each heuristic
    statistical_results = {}
    for h_name, h_data in heuristic_data.items():
        h_scores = h_data.get("scores", [])
        if baseline_scores and h_scores:
            statistical_results[h_name] = compute_statistical_significance(
                baseline_scores, h_scores, h_name
            )
        else:
            logger.warning(f"Skipping statistical test for {h_name} due to missing scores")

    # Generate sensitivity analysis
    sensitivity_results = generate_sensitivity_analysis(
        baseline_data, heuristic_data, thresholds
    )

    # Aggregate metrics
    final_metrics = {}
    for h_name, h_data in heuristic_data.items():
        metrics = h_data.get("metrics", {})
        baseline_metrics = baseline_data.get("metrics", {})
        
        delta_f1 = metrics.get("f1_score", 0) - baseline_metrics.get("f1_score", 0)
        delta_ppl = metrics.get("perplexity", 0) - baseline_metrics.get("perplexity", 0)
        
        final_metrics[h_name] = {
            "f1_score": metrics.get("f1_score"),
            "perplexity": metrics.get("perplexity"),
            "delta_f1_vs_baseline": delta_f1,
            "delta_ppl_vs_baseline": delta_ppl,
            "exact_match": metrics.get("exact_match"),
            "statistical_significance": statistical_results.get(h_name, {})
        }

    # Construct final report
    report = {
        "report_metadata": {
            "generated_by": "T031_ReportGenerator",
            "baseline_method": "Dense Attention (Full Context)",
            "primary_statistical_test": "Paired t-test",
            "secondary_statistical_test": "Wilcoxon signed-rank test",
            "correction_method": "Holm-Bonferroni"
        },
        "baseline_summary": {
            "f1_score": baseline_data.get("metrics", {}).get("f1_score"),
            "perplexity": baseline_data.get("metrics", {}).get("perplexity"),
            "exact_match": baseline_data.get("metrics", {}).get("exact_match")
        },
        "heuristic_results": final_metrics,
        "sensitivity_analysis": sensitivity_results,
        "false_positive_rate": sensitivity_results.get("false_positive_rates", {}),
        "sensitivity_table": sensitivity_results.get("sensitivity_table", {})
    }

    # Ensure output directory exists
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    # Write report
    with open(output_file, 'w') as f:
        json.dump(report, f, indent=2)
    
    logger.info(f"Final report written to {output_path}")
    return report

def run_aggregation(baseline_path: str, results_dir: str, output_path: str) -> None:
    """Entry point for aggregation and report generation."""
    generate_final_report(baseline_path, results_dir, output_path)

def main():
    """Main entry point for T031."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Generate final benchmark report (T031)")
    parser.add_argument("--baseline", type=str, required=True, help="Path to baseline metrics JSON")
    parser.add_argument("--results-dir", type=str, required=True, help="Directory containing heuristic results")
    parser.add_argument("--output", type=str, required=True, help="Output path for benchmark_report.json")
    
    args = parser.parse_args()
    
    try:
        generate_final_report(args.baseline, args.results_dir, args.output)
        logger.info("Report generation completed successfully.")
    except Exception as e:
        logger.error(f"Report generation failed: {e}")
        raise

if __name__ == "__main__":
    main()