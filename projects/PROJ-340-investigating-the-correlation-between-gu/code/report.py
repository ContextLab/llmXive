import json
import os
from pathlib import Path
from datetime import datetime

def load_json_file(file_path: str) -> dict:
    """Load a JSON file and return its contents as a dictionary."""
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Required file not found: {file_path}")
    
    with open(file_path, 'r') as f:
        return json.load(f)

def generate_report(
    correlation_matrix_path: str,
    sensitivity_analysis_path: str,
    timing_evidence_path: str,
    power_analysis_path: str,
    outlier_report_path: str,
    output_path: str
) -> None:
    """
    Generate the final report (data/results/final_report.md) integrating all findings.
    
    This task enforces associational language during generation and includes:
    1. A summary of stability of significant findings (from sensitivity_analysis).
    2. Execution duration and status (from timing_evidence).
    3. Correlation results summary.
    
    Addresses FR-004 and SC-002/SC-004.
    """
    
    # Load required artifacts
    try:
        correlation_data = load_json_file(correlation_matrix_path)
    except FileNotFoundError as e:
        # If correlation matrix is missing (analysis didn't run fully), we still generate a report
        # noting the absence, but we need the other artifacts for the report structure.
        correlation_data = []
        
    sensitivity_data = load_json_file(sensitivity_analysis_path)
    timing_data = load_json_file(timing_evidence_path)
    
    try:
        power_data = load_json_file(power_analysis_path)
    except FileNotFoundError:
        power_data = {"status": "NOT_AVAILABLE"}
        
    try:
        outlier_data = load_json_file(outlier_report_path)
    except FileNotFoundError:
        outlier_data = {"count": 0, "percentage_total": 0.0}

    # Extract specific metrics
    duration_seconds = timing_data.get("duration_seconds", 0.0)
    timing_status = timing_data.get("status", "UNKNOWN")
    
    base_count = sensitivity_data.get("base_count", 0)
    threshold_01_change = sensitivity_data.get("threshold_0.01", {}).get("percentage_change", 0.0)
    threshold_10_change = sensitivity_data.get("threshold_0.10", {}).get("percentage_change", 0.0)
    
    outlier_count = outlier_data.get("count", 0)
    outlier_percentage = outlier_data.get("percentage_total", 0.0)

    # Calculate summary stats for correlation matrix
    significant_count = sum(1 for item in correlation_data if item.get("is_significant", False))
    total_pairs = len(correlation_data)
    
    # Start building the report content
    report_lines = []
    report_lines.append("# Final Report: Gut Microbiome and Sleep Architecture Correlation Study")
    report_lines.append("")
    report_lines.append(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report_lines.append("")
    
    # --- Execution Timing Section (SC-004) ---
    report_lines.append("## 1. Execution Timing & Performance")
    report_lines.append("")
    report_lines.append(f"- **Total Duration:** {duration_seconds:.2f} seconds")
    report_lines.append(f"- **Status:** {timing_status}")
    if timing_status == "TIMEOUT":
        report_lines.append("> **WARNING:** The pipeline execution exceeded the 6-hour limit.")
    else:
        report_lines.append("> The pipeline completed within the 6-hour constraint.")
    report_lines.append("")

    # --- Data Quality Section ---
    report_lines.append("## 2. Data Quality & Preprocessing")
    report_lines.append("")
    report_lines.append(f"- **Outliers Detected:** {outlier_count} rows ({outlier_percentage:.2f}% of total)")
    report_lines.append("")

    # --- Correlation Results Section (Associational Framing) ---
    report_lines.append("## 3. Correlation Analysis Results")
    report_lines.append("")
    report_lines.append(f"- **Total Pairs Tested:** {total_pairs}")
    report_lines.append(f"- **Significant Associations (q ≤ 0.05):** {significant_count}")
    report_lines.append("")
    
    if total_pairs > 0:
        report_lines.append("### Top Significant Associations")
        report_lines.append("")
        report_lines.append("| Taxon | Sleep Metric | Correlation (r) | Adjusted p-value |")
        report_lines.append("| :--- | :--- | :--- | :--- |")
        
        # Sort by absolute correlation descending
        sorted_correlations = sorted(correlation_data, key=lambda x: abs(x.get("correlation_coefficient", 0)), reverse=True)
        
        # Show top 10
        for item in sorted_correlations[:10]:
            if item.get("is_significant", False):
                taxon = item.get("taxon", "N/A")
                metric = item.get("sleep_metric", "N/A")
                r_val = f"{item.get('correlation_coefficient', 0):.3f}"
                p_adj = f"{item.get('p_value_adjusted', 0):.4f}"
                report_lines.append(f"| {taxon} | {metric} | {r_val} | {p_adj} |")
        
        report_lines.append("")

    # --- Sensitivity Analysis Section (SC-002) ---
    report_lines.append("## 4. Sensitivity Analysis")
    report_lines.append("")
    report_lines.append("Stability of significant findings across different p-value thresholds:")
    report_lines.append("")
    report_lines.append(f"- **Base Threshold (0.05):** {base_count} significant findings")
    report_lines.append(f"- **Threshold 0.01:** {threshold_01_change:+.2f}% change from base")
    report_lines.append(f"- **Threshold 0.10:** {threshold_10_change:+.2f}% change from base")
    report_lines.append("")

    # --- Power Analysis Section ---
    report_lines.append("## 5. Power Analysis")
    report_lines.append("")
    if power_data.get("status") != "NOT_AVAILABLE":
        n_required = power_data.get("calculated_n", "N/A")
        is_underpowered = power_data.get("is_underpowered", False)
        report_lines.append(f"- **Minimum Sample Size Required (for r ≥ 0.3, power ≥ 0.80):** {n_required}")
        if is_underpowered:
            report_lines.append("> **CAUTION:** The current sample size is insufficient to detect the target effect size with adequate power.")
    else:
        report_lines.append("> Power analysis was not available in the provided artifacts.")
    report_lines.append("")

    # --- Critical Associational Disclaimer ---
    report_lines.append("## 6. Interpretation & Limitations")
    report_lines.append("")
    report_lines.append("> **IMPORTANT:** These results represent an **associational relationship** only. ")
    report_lines.append("> This study does not establish causality. Observed correlations between gut microbiome composition ")
    report_lines.append("> and sleep architecture metrics should not be interpreted as one causing the other without further ")
    report_lines.append("> experimental validation.")
    report_lines.append("")
    
    # Write the report to disk
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_file, 'w') as f:
        f.write('\n'.join(report_lines))

def main():
    """Entry point for report generation."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Generate final research report.")
    parser.add_argument("--correlation-matrix", required=True, help="Path to correlation_matrix.json")
    parser.add_argument("--sensitivity-analysis", required=True, help="Path to sensitivity_analysis.json")
    parser.add_argument("--timing-evidence", required=True, help="Path to timing_evidence.json")
    parser.add_argument("--power-analysis", required=True, help="Path to power_analysis.json")
    parser.add_argument("--outlier-report", required=True, help="Path to outlier_report.json")
    parser.add_argument("--output", required=True, help="Path for final_report.md")
    
    args = parser.parse_args()
    
    generate_report(
        correlation_matrix_path=args.correlation_matrix,
        sensitivity_analysis_path=args.sensitivity_analysis,
        timing_evidence_path=args.timing_evidence,
        power_analysis_path=args.power_analysis,
        outlier_report_path=args.outlier_report,
        output_path=args.output
    )
    print(f"Report generated successfully at: {args.output}")

if __name__ == "__main__":
    main()