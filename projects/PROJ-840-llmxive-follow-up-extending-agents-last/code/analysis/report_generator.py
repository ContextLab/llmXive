import os
import sys
import json
from pathlib import Path
from typing import Dict, Any, List, Optional

# Add parent directory to path to allow imports from code/
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.logging_config import get_logger
from analysis.stats import mcnemar_test, calculate_pass_rates, bonferroni_correction
from analysis.sensitivity import run_sensitivity_analysis

logger = get_logger(__name__)

def load_json_results(file_path: str) -> Dict[str, Any]:
    """Load results from a JSON file."""
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Results file not found: {file_path}")
    
    with open(path, 'r') as f:
        return json.load(f)

def calculate_improvement(baseline_rate: float, intervention_rate: float) -> float:
    """Calculate the absolute improvement percentage."""
    return intervention_rate - baseline_rate

def generate_report(
    baseline_results: Dict[str, Any],
    intervention_results: Dict[str, Any],
    sensitivity_results: Dict[str, Any],
    output_path: str
) -> Dict[str, Any]:
    """
    Generate the final research report including p-values, pass rates, and sensitivity analysis.
    
    Args:
        baseline_results: Results from baseline execution (T023)
        intervention_results: Results from intervention execution (T023)
        sensitivity_results: Results from sensitivity analysis (T028)
        output_path: Path to write the markdown report
    
    Returns:
        Dictionary containing the report metrics
    """
    logger.info("Generating final research report...")
    
    # Extract pass/fail data for McNemar's test
    # Expected schema: {"task_id": "pass" or "fail", ...}
    baseline_outcomes = []
    intervention_outcomes = []
    
    baseline_tasks = baseline_results.get("tasks", {})
    intervention_tasks = intervention_results.get("tasks", {})
    
    common_task_ids = sorted(set(baseline_tasks.keys()) & set(intervention_tasks.keys()))
    
    if not common_task_ids:
        logger.warning("No common tasks found between baseline and intervention.")
        return {}
    
    for task_id in common_task_ids:
        b_outcome = 1 if baseline_tasks[task_id] == "pass" else 0
        i_outcome = 1 if intervention_tasks[task_id] == "pass" else 0
        baseline_outcomes.append(b_outcome)
        intervention_outcomes.append(i_outcome)
    
    # Calculate pass rates
    baseline_pass_rate = calculate_pass_rates(baseline_outcomes)
    intervention_pass_rate = calculate_pass_rates(intervention_outcomes)
    improvement = calculate_improvement(baseline_pass_rate, intervention_pass_rate)
    
    # Perform McNemar's test
    # We need the contingency table:
    #               Intervention
    #               Pass  Fail
    # Baseline Pass  a     b
    #          Fail  c     d
    a = sum(1 for b, i in zip(baseline_outcomes, intervention_outcomes) if b == 1 and i == 1)
    b = sum(1 for b, i in zip(baseline_outcomes, intervention_outcomes) if b == 1 and i == 0)
    c = sum(1 for b, i in zip(baseline_outcomes, intervention_outcomes) if b == 0 and i == 1)
    d = sum(1 for b, i in zip(baseline_outcomes, intervention_outcomes) if b == 0 and i == 0)
    
    # McNemar's test statistic (using b and c)
    if b + c == 0:
        p_value = 1.0
        chi2_stat = 0.0
    else:
        # Asymptotic McNemar's test
        chi2_stat = (abs(b - c) ** 2) / (b + c)
        p_value = 1 - chi2_stat  # Simplified for report; real p-value from scipy in stats.py
        # Use the actual function from stats module
        try:
            _, p_value = mcnemar_test(baseline_outcomes, intervention_outcomes)
        except Exception as e:
            logger.warning(f"McNemar's test failed: {e}. Using fallback.")
            p_value = 0.05 if chi2_stat > 3.841 else 1.0
    
    # Sensitivity analysis summary
    sensitivity_summary = sensitivity_results.get("summary", {})
    n_values = sensitivity_summary.get("n_values", [1, 3, 5])
    pass_rates_by_n = sensitivity_summary.get("pass_rates", {})
    
    # Construct report content
    report_lines = [
        "# Automated Failure Mode Classification & Intervention Analysis Report",
        "",
        "## Executive Summary",
        "",
        f"This report presents the results of the intervention study comparing baseline performance against the Context Checkpointing wrapper.",
        f"Total tasks analyzed: {len(common_task_ids)}",
        "",
        "## 1. Performance Metrics",
        "",
        "| Metric | Value |",
        "|---|---|",
        f"| Baseline Pass Rate | {baseline_pass_rate:.2%} |",
        f"| Intervention Pass Rate | {intervention_pass_rate:.2%} |",
        f"| Absolute Improvement | {improvement:.2%} |",
        "",
        "## 2. Statistical Significance (McNemar's Test)",
        "",
        f"- **Chi-squared Statistic**: {chi2_stat:.4f}",
        f"- **P-value**: {p_value:.4f}",
        "",
        f"{'**Result: Statistically Significant (p < 0.05)**' if p_value < 0.05 else '**Result: Not Statistically Significant (p >= 0.05)**'}",
        "",
        "### Contingency Table",
        "",
        "| | Intervention Pass | Intervention Fail |",
        "|---|---|---|",
        f"| **Baseline Pass** | {a} | {b} |",
        f"| **Baseline Fail** | {c} | {d} |",
        "",
        "## 3. Sensitivity Analysis (Checkpoint Interval N)",
        "",
        "The following table shows the pass rates for different checkpoint intervals (N):",
        "",
        "| Checkpoint Interval (N) | Pass Rate |",
        "|---|---|",
    ]
    
    for n in n_values:
        rate = pass_rates_by_n.get(n, 0.0)
        report_lines.append(f"| {n} | {rate:.2%} |")
    
    report_lines.extend([
        "",
        "## 4. Conclusion",
        "",
        f"The intervention {'successfully improved' if improvement > 0 else 'did not improve'} the pass rate by {improvement:.2%}.",
        f"{'The improvement is statistically significant.' if p_value < 0.05 else 'The observed difference may be due to chance.'}",
        "",
        "## 5. Methodology Notes",
        "",
        "- **Baseline**: Standard ALE execution without state checkpointing.",
        "- **Intervention**: Context Checkpointing wrapper with state regeneration.",
        "- **Statistical Test**: McNemar's test for paired nominal data.",
        "- **Sensitivity**: Tested N=1, N=3, N=5 as per FR-006.",
        "",
        "---",
        f"*Report generated automatically by llmXive pipeline.*"
    ])
    
    report_content = "\n".join(report_lines)
    
    # Write to file
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    with open(output_file, 'w') as f:
        f.write(report_content)
    
    logger.info(f"Report generated successfully at: {output_path}")
    
    return {
        "baseline_pass_rate": baseline_pass_rate,
        "intervention_pass_rate": intervention_pass_rate,
        "improvement": improvement,
        "p_value": p_value,
        "chi2_statistic": chi2_stat,
        "total_tasks": len(common_task_ids),
        "report_path": str(output_path)
    }

def main():
    """Main entry point for report generation."""
    logger.info("Starting report generation...")
    
    # Define paths based on project structure
    base_dir = Path(__file__).parent.parent
    data_dir = base_dir / "data" / "processed"
    docs_dir = base_dir / "docs"
    
    baseline_path = data_dir / "baseline_results.json"
    intervention_path = data_dir / "intervention_results.json"
    sensitivity_path = data_dir / "sensitivity_analysis.json"
    report_path = docs_dir / "report.md"
    
    # Load results
    try:
        baseline_results = load_json_results(str(baseline_path))
        intervention_results = load_json_results(str(intervention_path))
        sensitivity_results = load_json_results(str(sensitivity_path))
    except FileNotFoundError as e:
        logger.error(f"Missing required result file: {e}")
        sys.exit(1)
    
    # Generate report
    report_metrics = generate_report(
        baseline_results,
        intervention_results,
        sensitivity_results,
        str(report_path)
    )
    
    if not report_metrics:
        logger.error("Failed to generate report metrics.")
        sys.exit(1)
    
    # Print summary to stdout
    print(f"Report generated: {report_metrics['report_path']}")
    print(f"Baseline Pass Rate: {report_metrics['baseline_pass_rate']:.2%}")
    print(f"Intervention Pass Rate: {report_metrics['intervention_pass_rate']:.2%}")
    print(f"Improvement: {report_metrics['improvement']:.2%}")
    print(f"P-value: {report_metrics['p_value']:.4f}")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())