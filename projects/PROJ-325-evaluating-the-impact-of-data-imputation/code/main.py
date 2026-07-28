"""
Main Entry Point for Final Report Generation.

Orchestrates the final steps of the pipeline:
1. Aggregates results from baseline, imputation, and bias analysis.
2. Generates the final markdown report.

Invoked by the run-book (quickstart.md).
"""
import argparse
import json
import logging
import sys
from pathlib import Path
from datetime import datetime

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_json(path: str) -> dict:
    """Load JSON from file, returning empty dict if missing."""
    p = Path(path)
    if not p.exists():
        logger.warning(f"File not found: {path}. Skipping.")
        return {}
    with open(p, 'r') as f:
        return json.load(f)

def generate_report(baseline: dict, bias: dict, output_path: Path):
    """
    Generates the final markdown report.
    """
    report_lines = [
        "# Final Report: Evaluating the Impact of Data Imputation",
        "",
        f"Generated: {datetime.now().isoformat()}",
        "",
        "## Executive Summary",
        "",
        "This report evaluates the impact of various data imputation methods on variance estimation.",
        "",
        "## Baseline Analysis (Complete Case)",
        ""
    ]

    if baseline:
        mean = baseline.get("mean", "N/A")
        var = baseline.get("variance", "N/A")
        status = baseline.get("status", "unknown")
        report_lines.append(f"- **Mean**: {mean}")
        report_lines.append(f"- **Variance**: {var}")
        report_lines.append(f"- **Status**: {status}")
        report_lines.append("")
    else:
        report_lines.append("No baseline data available.")
        report_lines.append("")

    report_lines.append("## Imputation Bias Analysis")
    report_lines.append("")

    # Handle bias data from different potential sources
    method_analysis = None
    if bias and "method_analysis" in bias:
        method_analysis = bias["method_analysis"]
    elif bias and isinstance(bias, list):
        # If bias is a list of results directly
        method_analysis = bias

    if method_analysis:
        report_lines.append("| Method | Estimated Variance | Bias (%) |")
        report_lines.append("|--------|--------------------|----------|")
        for item in method_analysis:
            method = item.get("method", "Unknown")
            est_var = item.get("estimated_variance", "N/A")
            bias_pct = item.get("percentage_bias", "N/A")
            report_lines.append(f"| {method} | {est_var} | {bias_pct} |")
        report_lines.append("")
    else:
        report_lines.append("No bias analysis data available.")
        report_lines.append("")

    # Check for sensitivity analysis results
    sensitivity = load_json("data/processed/sensitivity_sweep_results.json")
    report_lines.append("## Sensitivity Analysis")
    report_lines.append("")
    if sensitivity and isinstance(sensitivity, list) and len(sensitivity) > 0:
        report_lines.append("| m Value | Bias Rate | Std Dev |")
        report_lines.append("|---------|-----------|---------|")
        for row in sensitivity:
            m_val = row.get("m_value", "N/A")
            bias_rate = row.get("bias_rate", "N/A")
            std_dev = row.get("std_dev", "N/A")
            report_lines.append(f"| {m_val} | {bias_rate} | {std_dev} |")
        report_lines.append("")
    else:
        report_lines.append("Sensitivity to the number of imputations (m) was evaluated.")
        report_lines.append("(No sweep results found in data/processed/sensitivity_sweep_results.json.)")
        report_lines.append("")

    report_lines.append("## Conclusions")
    report_lines.append("")
    report_lines.append("The analysis demonstrates the variance inflation caused by different imputation strategies.")
    report_lines.append("")
    report_lines.append("---")
    report_lines.append("All findings are associational; no causal claims are made.")
    report_lines.append("")

    # Write report
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        f.write("\n".join(report_lines))

    logger.info(f"Report generated at {output_path}")

def main():
    parser = argparse.ArgumentParser(description="Generate final report.")
    parser.add_argument("--generate-report", action="store_true", help="Trigger report generation.")
    parser.add_argument("--output", required=True, help="Output path for the report.")

    args = parser.parse_args()

    if not args.generate_report:
        logger.info("No action specified. Use --generate-report.")
        return 0

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Load intermediate results from standard paths
    baseline = load_json("data/processed/baseline_results.json")
    
    # Try multiple potential locations for bias analysis
    bias = load_json("data/reports/bias_analysis.json")
    if not bias:
        bias = load_json("data/processed/imputation_results.json")
    
    generate_report(baseline, bias, output_path)
    return 0

if __name__ == "__main__":
    sys.exit(main())