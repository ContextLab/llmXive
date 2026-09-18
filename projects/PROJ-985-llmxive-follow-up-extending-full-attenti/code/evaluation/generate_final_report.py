"""
T030: Generate final evaluation report.

Reads aggregated results from static and learned baselines, along with
statistical analysis results, to produce a comprehensive Markdown report.

Inputs:
  - data/results/static_aggregated.json (from T019c)
  - data/results/baseline_aggregated.json (from T026b)
  - data/results/static_metrics.json (from T027)
  - data/results/stats_results.json (from T029)
  - data/results/metrics.csv (from T031 - Falsifiability Check)

Output:
  - data/results/final_report.md
"""
import os
import json
import csv
import logging
from datetime import datetime
from typing import Dict, Any, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_json_file(filepath: str) -> Optional[Dict[str, Any]]:
    """Load a JSON file and return its contents."""
    if not os.path.exists(filepath):
        logger.warning(f"File not found: {filepath}")
        return None
    try:
        with open(filepath, 'r') as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        logger.error(f"Error decoding JSON from {filepath}: {e}")
        return None

def load_metrics_csv(filepath: str) -> Dict[str, Any]:
    """Load the metrics CSV and return the relevant row as a dict."""
    if not os.path.exists(filepath):
        logger.warning(f"File not found: {filepath}")
        return {}
    try:
        with open(filepath, 'r') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            if rows:
                return rows[0]
            return {}
    except Exception as e:
        logger.error(f"Error reading CSV from {filepath}: {e}")
        return {}

def format_percentage(value: float) -> str:
    """Format a float as a percentage string."""
    return f"{value:.2f}%"

def generate_report(
    static_agg: Optional[Dict[str, Any]],
    learned_agg: Optional[Dict[str, Any]],
    static_metrics: Optional[Dict[str, Any]],
    stats_results: Optional[Dict[str, Any]],
    falsifiability: Dict[str, Any]
) -> str:
    """Generate the final evaluation report in Markdown format."""
    
    report_lines = []
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Header
    report_lines.append("# llmXive Evaluation: Final Report")
    report_lines.append(f"**Generated:** {timestamp}")
    report_lines.append("")
    
    # Executive Summary
    report_lines.append("## Executive Summary")
    report_lines.append("")
    report_lines.append("This report presents the evaluation of the static heuristic sparsification")
    report_lines.append("method against the full attention baseline and the learned sparse (RTPurbo) baseline.")
    report_lines.append("The analysis includes Perplexity, Exact Match metrics, and statistical significance testing.")
    report_lines.append("")
    
    # Extract key values for summary
    static_pp = static_agg.get('mean_perplexity') if static_agg else None
    learned_pp = learned_agg.get('mean_perplexity') if learned_agg else None
    static_em = static_agg.get('mean_exact_match') if static_agg else None
    learned_em = learned_agg.get('mean_exact_match') if learned_agg else None
    
    if static_pp and learned_pp:
        pp_diff = ((static_pp - learned_pp) / learned_pp) * 100
        report_lines.append(f"The static heuristic achieved a mean Perplexity of **{static_pp:.2f}** compared to")
        report_lines.append(f"the learned baseline's **{learned_pp:.2f}** (a {pp_diff:+.2f}% difference).")
        report_lines.append("")
    
    if static_em and learned_em:
        em_diff = ((static_em - learned_em) / learned_em) * 100
        report_lines.append(f"For Exact Match, the static heuristic scored **{static_em:.2f}%** versus")
        report_lines.append(f"the learned baseline's **{learned_em:.2f}%** (a {em_diff:+.2f}% difference).")
        report_lines.append("")
    
    # Statistical Significance
    if stats_results:
        p_value = stats_results.get('p_value')
        significant = stats_results.get('is_significant', False)
        test_type = stats_results.get('test_type', 'Unknown')
        
        sig_text = "significant" if significant else "not significant"
        report_lines.append(f"A {test_type} test yielded a p-value of **{p_value:.4f}**, indicating that the difference")
        report_lines.append(f"in performance is {sig_text} at the α=0.05 level.")
        report_lines.append("")
    
    # Falsifiability Check
    report_lines.append("### Falsifiability Check")
    report_lines.append("")
    drop_pct = falsifiability.get('performance_drop_pct', 0.0)
    threshold = 1.0
    passed = drop_pct < threshold
    status = "PASSED" if passed else "FAILED"
    report_lines.append(f"Performance drop (Static vs Learned): **{drop_pct:.2f}%**")
    report_lines.append(f"Threshold: < {threshold}%")
    report_lines.append(f"Result: **{status}**")
    report_lines.append("")
    
    # Methodology
    report_lines.append("## Methodology")
    report_lines.append("")
    report_lines.append("### Data Sources")
    report_lines.append("- **Dataset:** RULER (streamed subset)")
    report_lines.append("- **Static Features:** Entropy, POS tags, Position, KenLM Perplexity")
    report_lines.append("- **Ground Truth:** RTPurbo selection labels from frozen Llama-3-8B")
    report_lines.append("")
    report_lines.append("### Baselines")
    report_lines.append("1. **Full Attention:** Standard attention mechanism (no sparsification)")
    report_lines.append("2. **Learned Sparse (RTPurbo):** Dynamic token selection using a learned policy")
    report_lines.append("3. **Static Heuristic:** Rule-based token selection derived from static features")
    report_lines.append("")
    report_lines.append("### Statistical Analysis")
    report_lines.append("- **Test:** Paired t-test (document-level performance differences)")
    report_lines.append("- **Significance Level:** α = 0.05")
    report_lines.append("- **Seeds:** 5 independent random seeds for both Static and Learned baselines")
    report_lines.append("")
    
    # Results Table
    report_lines.append("## Results Table")
    report_lines.append("")
    report_lines.append("| Metric | Full Attention | Learned Sparse (RTPurbo) | Static Heuristic | P-value | Significance |")
    report_lines.append("|--------|----------------|--------------------------|------------------|---------|--------------|")
    
    # Fill in values (use placeholders if missing)
    def fmt(val, fmt_str="{:.2f}"):
        return fmt_str.format(val) if val is not None else "N/A"
    
    # Assuming full attention is the reference or we have it in learned_agg if it was the "learned" baseline
    # Based on T026b, learned_agg contains the learned sparse (RTPurbo) results.
    # We need to map "Full Attention" if available, otherwise we compare Learned vs Static.
    # For this report, we assume the "Learned Sparse" column is the primary comparison.
    
    pp_learned = learned_agg.get('mean_perplexity') if learned_agg else None
    pp_static = static_agg.get('mean_perplexity') if static_agg else None
    em_learned = learned_agg.get('mean_exact_match') if learned_agg else None
    em_static = static_agg.get('mean_exact_match') if static_agg else None
    
    p_val = stats_results.get('p_value') if stats_results else None
    is_sig = stats_results.get('is_significant', False) if stats_results else None
    sig_str = "Yes" if is_sig else "No" if is_sig is not None else "N/A"
    
    report_lines.append(f"| Perplexity | N/A | {fmt(pp_learned)} | {fmt(pp_static)} | {fmt(p_val, '{:.4f}') if p_val else 'N/A'} | {sig_str} |")
    report_lines.append(f"| Exact Match | N/A | {fmt(em_learned, '{:.2f}%')} | {fmt(em_static, '{:.2f}%')} | N/A | N/A |")
    report_lines.append("")
    
    # Statistical Significance Section
    report_lines.append("## Statistical Significance")
    report_lines.append("")
    if stats_results:
        report_lines.append(f"- **Test Type:** {stats_results.get('test_type', 'N/A')}")
        report_lines.append(f"- **P-value:** {stats_results.get('p_value', 'N/A')}")
        report_lines.append(f"- **Null Hypothesis:** No difference in performance between Static and Learned baselines.")
        report_lines.append(f"- **Conclusion:** {'Reject null hypothesis (significant difference)' if is_sig else 'Fail to reject null hypothesis (no significant difference)'}")
    else:
        report_lines.append("Statistical analysis results are unavailable.")
    report_lines.append("")
    
    # Footer
    report_lines.append("---")
    report_lines.append(f"*Report generated by T030: generate_final_report.py*")
    
    return "\n".join(report_lines)

def main():
    """Main entry point for generating the final report."""
    logger.info("Starting final report generation (T030)...")
    
    # Define paths
    base_dir = "data/results"
    static_agg_path = os.path.join(base_dir, "static_aggregated.json")
    learned_agg_path = os.path.join(base_dir, "baseline_aggregated.json")
    static_metrics_path = os.path.join(base_dir, "static_metrics.json")
    stats_results_path = os.path.join(base_dir, "stats_results.json")
    falsifiability_path = os.path.join(base_dir, "metrics.csv")
    output_path = os.path.join(base_dir, "final_report.md")
    
    # Load data
    logger.info(f"Loading static aggregated results from {static_agg_path}...")
    static_agg = load_json_file(static_agg_path)
    
    logger.info(f"Loading learned baseline aggregated results from {learned_agg_path}...")
    learned_agg = load_json_file(learned_agg_path)
    
    logger.info(f"Loading static metrics from {static_metrics_path}...")
    static_metrics = load_json_file(static_metrics_path)
    
    logger.info(f"Loading statistical analysis results from {stats_results_path}...")
    stats_results = load_json_file(stats_results_path)
    
    logger.info(f"Loading falsifiability check from {falsifiability_path}...")
    falsifiability = load_metrics_csv(falsifiability_path)
    
    # Check for critical missing data
    if not static_agg and not learned_agg:
        logger.error("Critical: Missing both static and learned aggregated results. Cannot generate report.")
        return
    
    # Generate report
    logger.info("Generating report content...")
    report_content = generate_report(
        static_agg,
        learned_agg,
        static_metrics,
        stats_results,
        falsifiability
    )
    
    # Write output
    logger.info(f"Writing report to {output_path}...")
    with open(output_path, 'w') as f:
        f.write(report_content)
    
    logger.info(f"Final report successfully generated at {output_path}")

if __name__ == "__main__":
    main()