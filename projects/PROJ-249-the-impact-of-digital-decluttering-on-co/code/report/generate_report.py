"""
T042: Final Report Generator

Generates the comprehensive final research report for the digital decluttering study.
Aggregates outputs from T029 (Sensitivity), T020 (Power), T040 (Statistical Summary),
and T043 (Validation Status) into a single Markdown document.

Output: results/final_report.md
"""
import os
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime

# Import project config for path resolution
from config.env_config import get_path, get_config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_json_file(file_path: Path) -> Optional[Dict[str, Any]]:
    """Load a JSON file safely."""
    if not file_path.exists():
        logger.error(f"Required file not found: {file_path}")
        return None
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        logger.error(f"Error decoding JSON from {file_path}: {e}")
        return None
    except Exception as e:
        logger.error(f"Error reading {file_path}: {e}")
        return None

def load_markdown_file(file_path: Path) -> Optional[str]:
    """Load a Markdown file safely."""
    if not file_path.exists():
        logger.error(f"Required file not found: {file_path}")
        return None
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        logger.error(f"Error reading {file_path}: {e}")
        return None

def format_statistical_summary(summary_data: Dict[str, Any]) -> str:
    """Format the statistical summary section for the report."""
    if not summary_data:
        return "### Statistical Summary\n\n*No statistical summary data available.*\n"

    lines = ["### Statistical Summary", ""]
    
    # Extract metrics if present
    metrics = summary_data.get('metrics', [])
    if metrics:
        lines.append("#### Primary Outcome Measures")
        lines.append("")
        lines.append("| Metric | Mean Change | 95% CI Lower | 95% CI Upper | Corrected p-value | Effect Size (d) | Status |")
        lines.append("| :--- | :--- | :--- | :--- | :--- | :--- | :--- |")
        
        for m in metrics:
            metric_name = m.get('metric', 'Unknown')
            mean_change = m.get('mean_change', 'N/A')
            ci_lower = m.get('ci_95_lower', 'N/A')
            ci_upper = m.get('ci_95_upper', 'N/A')
            p_val = m.get('holm_corrected_p', 'N/A')
            effect_size = m.get('cohens_d', 'N/A')
            significant = "Yes" if m.get('significant', False) else "No"
            
            lines.append(f"| {metric_name} | {mean_change:.4f} | {ci_lower:.4f} | {ci_upper:.4f} | {p_val:.4f} | {effect_size:.4f} | {significant} |")
        lines.append("")
    else:
        # Fallback if structure is flat
        for key, value in summary_data.items():
            if isinstance(value, (dict, list)):
                lines.append(f"**{key}**: (See detailed data below)")
            else:
                lines.append(f"**{key}**: {value}")
        lines.append("")

    return "\n".join(lines)

def format_power_results(power_data: Dict[str, Any]) -> str:
    """Format the power simulation results for the report."""
    if not power_data:
        return "### Power Analysis\n\n*No power simulation data available.*\n"

    lines = ["### Power Analysis", ""]
    
    lines.append("#### Simulation Parameters")
    lines.append(f"- **Iterations**: {power_data.get('iterations', 'N/A')}")
    lines.append(f"- **Sample Size (n)**: {power_data.get('sample_size', 'N/A')}")
    lines.append(f"- **Effect Size (d) Target**: {power_data.get('target_effect_size', 'N/A')}")
    lines.append(f"- **Alpha Level**: {power_data.get('alpha', 'N/A')}")
    lines.append("")

    lines.append("#### Results")
    lines.append(f"- **Estimated Power**: {power_data.get('estimated_power', 'N/A'):.4f}")
    lines.append(f"- **Confidence Interval (95%)**: [{power_data.get('power_ci_lower', 'N/A'):.4f}, {power_data.get('power_ci_upper', 'N/A'):.4f}]")
    lines.append(f"- **Significant Iterations**: {power_data.get('significant_count', 'N/A')} / {power_data.get('iterations', 'N/A')}")
    lines.append("")

    if 'interpretation' in power_data:
        lines.append("#### Interpretation")
        lines.append(power_data['interpretation'])
        lines.append("")

    return "\n".join(lines)

def format_validation_status(validation_data: Dict[str, Any]) -> str:
    """Format the validation status for the report."""
    if not validation_data:
        return "### Validation Status\n\n*No validation data available.*\n"

    lines = ["### Validation Status", ""]
    
    overall_status = "Passed" if validation_data.get('passed', False) else "Failed"
    lines.append(f"**Overall Status**: {overall_status}")
    lines.append("")

    criteria = validation_data.get('criteria_results', [])
    if criteria:
        lines.append("#### Criterion Checks")
        lines.append("")
        lines.append("| Criterion | Description | Result | Details |")
        lines.append("| :--- | :--- | :--- | :--- |")
        
        for c in criteria:
            name = c.get('criterion', 'N/A')
            desc = c.get('description', 'N/A')
            passed = "Pass" if c.get('passed', False) else "Fail"
            details = c.get('details', '')
            lines.append(f"| {name} | {desc} | {passed} | {details} |")
        lines.append("")

    return "\n".join(lines)

def generate_report(
    sensitivity_content: str,
    power_data: Optional[Dict[str, Any]],
    statistical_summary_data: Optional[Dict[str, Any]],
    validation_data: Optional[Dict[str, Any]],
    output_path: Path
) -> bool:
    """
    Assemble the final report.
    
    Args:
        sensitivity_content: Full text of the sensitivity analysis report (T029).
        power_data: Dict containing power simulation results (T020).
        statistical_summary_data: Dict containing statistical summary (T040).
        validation_data: Dict containing validation report (T043).
        output_path: Path to write the final report.
    
    Returns:
        True if successful, False otherwise.
    """
    logger.info(f"Generating final report at {output_path}")

    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Header
    report_parts = [
        "# Final Research Report: The Impact of Digital Decluttering on Cognitive Performance and Well-being",
        "",
        f"**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "",
        "---",
        "",
        "## Executive Summary",
        "",
        "This report aggregates the findings from the digital decluttering study, including sensitivity analyses, power simulations, statistical summaries of pre-post changes, and validation against success criteria.",
        ""
    ]

    # 1. Sensitivity Analysis (Full Text)
    report_parts.append("## 1. Sensitivity Analysis Report")
    report_parts.append("")
    if sensitivity_content:
        report_parts.append(sensitivity_content)
    else:
        report_parts.append("*Sensitivity analysis report not available.*")
    report_parts.append("")
    report_parts.append("---")
    report_parts.append("")

    # 2. Power Simulation
    report_parts.append("## 2. Power Analysis")
    report_parts.append("")
    report_parts.append(format_power_results(power_data))
    report_parts.append("---")
    report_parts.append("")

    # 3. Statistical Summary
    report_parts.append("## 3. Statistical Summary")
    report_parts.append("")
    report_parts.append(format_statistical_summary(statistical_summary_data))
    report_parts.append("---")
    report_parts.append("")

    # 4. Validation Status
    report_parts.append("## 4. Validation Status")
    report_parts.append("")
    report_parts.append(format_validation_status(validation_data))
    report_parts.append("")

    # Footer
    report_parts.append("---")
    report_parts.append("")
    report_parts.append("*End of Report*")

    # Write to file
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write("\n".join(report_parts))
        logger.info(f"Successfully wrote report to {output_path}")
        return True
    except Exception as e:
        logger.error(f"Failed to write report: {e}")
        return False

def main():
    """Main entry point for the report generation pipeline."""
    config = get_config()
    
    # Define paths based on project structure
    results_dir = get_path("results")
    sensitivity_file = results_dir / "sensitivity_analysis_report.md"
    power_file = results_dir / "power_analysis.json"
    summary_file = results_dir / "statistical_summary.json"
    validation_file = results_dir / "validation_report.json"
    output_file = results_dir / "final_report.md"

    logger.info("Starting Final Report Generation (T042)...")

    # 1. Load Sensitivity Report (T029)
    sensitivity_content = load_markdown_file(sensitivity_file)
    if sensitivity_content is None:
        logger.warning("Sensitivity report (T029) not found. Proceeding with placeholder.")
        sensitivity_content = "## Sensitivity Analysis\n\n*Report not generated or not found.*"

    # 2. Load Power Simulation Results (T020)
    power_data = load_json_file(power_file)
    if power_data is None:
        logger.warning("Power analysis (T020) not found. Proceeding with empty data.")
        power_data = {}

    # 3. Load Statistical Summary (T040)
    summary_data = load_json_file(summary_file)
    if summary_data is None:
        logger.warning("Statistical summary (T040) not found. Proceeding with empty data.")
        summary_data = {}

    # 4. Load Validation Report (T043)
    validation_data = load_json_file(validation_file)
    if validation_data is None:
        logger.warning("Validation report (T043) not found. Proceeding with empty data.")
        validation_data = {}

    # Generate the report
    success = generate_report(
        sensitivity_content=sensitivity_content,
        power_data=power_data,
        statistical_summary_data=summary_data,
        validation_data=validation_data,
        output_path=output_file
    )

    if success:
        logger.info("Final report generation completed successfully.")
        return 0
    else:
        logger.error("Final report generation failed.")
        return 1

if __name__ == "__main__":
    exit(main())