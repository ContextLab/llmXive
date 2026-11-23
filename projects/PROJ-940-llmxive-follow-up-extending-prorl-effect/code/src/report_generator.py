"""
Report Generator Module for llmXive ProRL Pipeline.

This module handles the aggregation of all pipeline results into a single
comprehensive Markdown report (results/final_report.md).

It reads outputs from:
- results/sc005_status.json (SC-005 validation)
- results/metrics_comparison.json (US2 metric comparison)
- results/statistical_significance.json (US3 significance tests)
- results/sensitivity_report.json (US3 sensitivity analysis)
- results/resource_log.json (Optional: Resource enforcement actions)
"""
import json
import os
from typing import Dict, Any, Optional
from datetime import datetime

# Constants for file paths relative to project root
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RESULTS_DIR = os.path.join(PROJECT_ROOT, "results")
REPORT_PATH = os.path.join(RESULTS_DIR, "final_report.md")

# Input file paths
SC005_PATH = os.path.join(RESULTS_DIR, "sc005_status.json")
METRICS_COMP_PATH = os.path.join(RESULTS_DIR, "metrics_comparison.json")
STATS_SIG_PATH = os.path.join(RESULTS_DIR, "statistical_significance.json")
SENS_REPORT_PATH = os.path.join(RESULTS_DIR, "sensitivity_report.json")
RESOURCE_LOG_PATH = os.path.join(RESULTS_DIR, "resource_log.json")


def load_json_file(filepath: str) -> Optional[Dict[str, Any]]:
    """Safely load a JSON file. Returns None if file does not exist."""
    if not os.path.exists(filepath):
        return None
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        print(f"Warning: Could not load {filepath}: {e}")
        return None


def generate_section_header(title: str) -> str:
    """Generate a Markdown section header."""
    return f"\n## {title}\n\n"


def format_table(headers: list, rows: list) -> str:
    """Format a list of rows as a Markdown table."""
    if not rows:
        return "*No data available.*"

    # Determine column widths based on headers and content
    col_widths = [len(str(h)) for h in headers]
    for row in rows:
        for i, val in enumerate(row):
            if i < len(col_widths):
                col_widths[i] = max(col_widths[i], len(str(val)))

    # Build header row
    header_line = "| " + " | ".join(str(h).ljust(col_widths[i]) for i, h in enumerate(headers)) + " |"
    separator_line = "| " + " | ".join("-" * w for w in col_widths) + " |"

    # Build data rows
    data_lines = []
    for row in rows:
        data_lines.append(
            "| " + " | ".join(str(val).ljust(col_widths[i]) for i, val in enumerate(row)) + " |"
        )

    return "\n".join([header_line, separator_line] + data_lines)


def render_sc005_section(data: Optional[Dict[str, Any]]) -> str:
    """Render the SC-005 Validation section."""
    lines = [generate_section_header("SC-005: Rectification Impact Validation")]

    if not data:
        lines.append("*Status: Not executed or file missing.*\n")
        return "\n".join(lines)

    status = data.get("status", "Unknown")
    mean_diff = data.get("mean_absolute_difference", "N/A")
    threshold = data.get("threshold", "0.01")
    timestamp = data.get("timestamp", "N/A")

    lines.append(f"**Status**: {status.upper()}")
    lines.append(f"**Threshold**: {threshold}")
    lines.append(f"**Observed Mean Absolute Difference**: {mean_diff}")
    lines.append(f"**Timestamp**: {timestamp}")

    if status == "pass":
        lines.append("\n> ✅ **Conclusion**: The ProRL rectification formulas produced a statistically measurable impact on path scores (|Δ| ≥ 0.01).")
    else:
        lines.append("\n> ⚠️ **Conclusion**: The rectification impact was below the required threshold. Review hyperparameters (alpha) or batch sizes.")

    return "\n".join(lines)


def render_metrics_comparison_section(data: Optional[Dict[str, Any]]) -> str:
    """Render the Metrics Comparison section (US2)."""
    lines = [generate_section_header("US2: Baseline vs. ProRL Comparison")]

    if not data:
        lines.append("*Comparison data missing. Ensure T025b has been executed.*\n")
        return "\n".join(lines)

    # Extract metrics for Greedy vs. ProRL
    greedy = data.get("greedy", {})
    prorl = data.get("prorl", {})

    headers = ["Metric", "Greedy Baseline", "ProRL (Rectified)", "Improvement"]
    rows = []

    metrics_to_check = ["precision_at_k", "recall_at_k", "diversity", "coverage"]
    metric_labels = {
        "precision_at_k": "Precision@K",
        "recall_at_k": "Recall@K",
        "diversity": "Diversity",
        "coverage": "Coverage"
    }

    for key in metrics_to_check:
        g_val = greedy.get(key, 0.0)
        p_val = prorl.get(key, 0.0)
        improvement = "N/A"
        if isinstance(g_val, (int, float)) and isinstance(p_val, (int, float)):
            diff = p_val - g_val
            sign = "+" if diff >= 0 else ""
            improvement = f"{sign}{diff:.4f}"

        rows.append([
            metric_labels.get(key, key),
            f"{g_val:.4f}",
            f"{p_val:.4f}",
            improvement
        ])

    lines.append(format_table(headers, rows))
    lines.append("\n*Note: Higher values are better for all metrics listed above.*")

    return "\n".join(lines)


def render_statistical_significance_section(data: Optional[Dict[str, Any]]) -> str:
    """Render the Statistical Significance section (US3)."""
    lines = [generate_section_header("US3: Statistical Significance Testing")]

    if not data:
        lines.append("*Significance test results missing. Ensure T028b has been executed.*\n")
        return "\n".join(lines)

    test_type = data.get("test_method", "N/A")
    p_value = data.get("p_value", "N/A")
    significant = data.get("is_significant", False)
    confidence_interval = data.get("confidence_interval", "N/A")

    lines.append(f"**Test Method Used**: {test_type}")
    lines.append(f"**P-Value**: {p_value}")
    lines.append(f"**95% Confidence Interval**: {confidence_interval}")

    if significant:
        lines.append(f"\n> ✅ **Result**: The difference between Greedy and ProRL metrics is **statistically significant** (p < 0.05).")
    else:
        lines.append(f"\n> ⚠️ **Result**: The difference is **not statistically significant** (p ≥ 0.05).")

    # Include specific test details if available
    if "details" in data:
        lines.append("\n### Test Details")
        details = data["details"]
        for k, v in details.items():
            lines.append(f"- **{k}**: {v}")

    return "\n".join(lines)


def render_sensitivity_analysis_section(data: Optional[Dict[str, Any]]) -> str:
    """Render the Sensitivity Analysis section (US3)."""
    lines = [generate_section_header("US3: Sensitivity Analysis")]

    if not data:
        lines.append("*Sensitivity report missing. Ensure T029b has been executed.*\n")
        return "\n".join(lines)

    # Path Length Sensitivity
    if "path_length_sweep" in data:
        lines.append("### Path Length Sensitivity (L)")
        lines.append("The following table shows how metrics vary with path length:")
        headers = ["Path Length (L)", "Precision@K", "Diversity", "Coverage"]
        rows = []
        for item in data["path_length_sweep"]:
            rows.append([
                item.get("length", "N/A"),
                f"{item.get('precision', 0):.4f}",
                f"{item.get('diversity', 0):.4f}",
                f"{item.get('coverage', 0):.4f}"
            ])
        lines.append(format_table(headers, rows))
        lines.append("")

    # Similarity Threshold Sensitivity
    if "sim_threshold_sweep" in data:
        lines.append("### Similarity Threshold Sensitivity")
        lines.append("The following table shows how metrics vary with the similarity cutoff:")
        headers = ["Threshold", "Precision@K", "Diversity", "Coverage"]
        rows = []
        for item in data["sim_threshold_sweep"]:
            rows.append([
                item.get("threshold", "N/A"),
                f"{item.get('precision', 0):.4f}",
                f"{item.get('diversity', 0):.4f}",
                f"{item.get('coverage', 0):.4f}"
            ])
        lines.append(format_table(headers, rows))
        lines.append("")

    # Summary
    if "summary" in data:
        lines.append("### Summary")
        summary = data["summary"]
        lines.append(f"- **Optimal Path Length**: {summary.get('optimal_path_length', 'N/A')}")
        lines.append(f"- **Optimal Threshold**: {summary.get('optimal_threshold', 'N/A')}")
        lines.append(f"- **Robustness Note**: {summary.get('robustness_note', 'No robustness analysis performed.')}")

    return "\n".join(lines)


def render_resource_enforcement_section(data: Optional[Dict[str, Any]]) -> str:
    """Render the Resource Enforcement section (Optional)."""
    lines = [generate_section_header("System Resource Enforcement")]

    if not data:
        lines.append("*Resource log not found. Skipping this section.*")
        return "\n".join(lines)

    lines.append("The following resource enforcement actions were taken during execution:")
    for action in data.get("actions", []):
        lines.append(f"- {action}")

    if not data.get("actions"):
        lines.append("- No sampling or capping was required.")

    return "\n".join(lines)


def generate_final_report():
    """
    Main function to generate the final_report.md.
    Reads all result JSON files and compiles them into a Markdown document.
    """
    print("Generating Final Report...")

    # Load all data sources
    sc005_data = load_json_file(SC005_PATH)
    metrics_data = load_json_file(METRICS_COMP_PATH)
    stats_data = load_json_file(STATS_SIG_PATH)
    sens_data = load_json_file(SENS_REPORT_PATH)
    resource_data = load_json_file(RESOURCE_LOG_PATH)

    # Compile sections
    sections = []

    # Title
    sections.append("# llmXive ProRL Pipeline: Final Report")
    sections.append(f"**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    sections.append("")

    # Executive Summary
    sections.append(generate_section_header("Executive Summary"))
    sections.append("This report summarizes the performance of the ProRL (Proactive Recommendation with Reinforcement Learning) pipeline compared to the Greedy baseline.")
    sections.append("It includes validation of the rectification mechanism, metric comparisons, statistical significance testing, and sensitivity analysis.")
    sections.append("")

    # SC-005 Validation
    sections.append(render_sc005_section(sc005_data))
    sections.append("")

    # Metrics Comparison
    sections.append(render_metrics_comparison_section(metrics_data))
    sections.append("")

    # Statistical Significance
    sections.append(render_statistical_significance_section(stats_data))
    sections.append("")

    # Sensitivity Analysis
    sections.append(render_sensitivity_analysis_section(sens_data))
    sections.append("")

    # Resource Enforcement (Optional)
    if resource_data:
        sections.append(render_resource_enforcement_section(resource_data))
        sections.append("")

    # Footer
    sections.append("---")
    sections.append("*Report generated by llmXive automated science pipeline (Task T032)*")

    # Write to file
    full_report = "\n".join(sections)

    os.makedirs(RESULTS_DIR, exist_ok=True)
    with open(REPORT_PATH, 'w', encoding='utf-8') as f:
        f.write(full_report)

    print(f"Final report successfully written to: {REPORT_PATH}")
    return REPORT_PATH


if __name__ == "__main__":
    generate_final_report()
