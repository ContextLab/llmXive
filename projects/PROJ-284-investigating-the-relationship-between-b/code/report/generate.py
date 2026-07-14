"""
Report generator for the Brain Network Dynamics project.
Assembles Markdown/PDF reports from analysis results.
"""
from __future__ import annotations

import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd

from code.logging_config import get_logger

logger = get_logger(__name__)

# Constants for required text
LIMITATION_STATEMENT = "Motor Task Performance is a proxy for proprioceptive accuracy."
ASSOCIATIONAL_PHRASES = ["associational relationship", "correlational evidence"]

def load_template(template_path: str = "templates/report_template.md") -> str:
    """Load the report template from disk."""
    path = Path(template_path)
    if not path.exists():
        # Create a default template if missing
        path.parent.mkdir(parents=True, exist_ok=True)
        default_template = """
        # Brain Network Dynamics and Sensorimotor Performance Report

        Generated: {{timestamp}}

        ## Executive Summary
        {{summary}}

        ## Correlation Results
        {{correlation_table}}

        ## Power Analysis
        {{power_analysis}}

        ## Visualizations
        {{plots}}

        ## Discussion and Limitations
        {{limitations}}

        ## Conclusion
        {{conclusion}}
        """
        path.write_text(default_template)
        logger.log("template_created", path=str(path))

    return path.read_text()

def format_correlation_table(results: List[Dict[str, Any]]) -> str:
    """Format correlation results into a Markdown table."""
    if not results:
        return "No correlation results available."

    headers = ["Metric", "Correlation (r)", "p-value", "q-value (FDR)", "Significant"]
    rows = []

    for res in results:
        significant = "Yes" if res.get("significant", False) else "No"
        rows.append([
            res.get("metric_name", "Unknown"),
            f"{res.get('r', 0):.4f}",
            f"{res.get('p', 0):.4f}",
            f"{res.get('q', 0):.4f}",
            significant
        ])

    # Build Markdown table
    table = "| " + " | ".join(headers) + " |\n"
    table += "| " + " | ".join(["---"] * len(headers)) + " |\n"
    for row in rows:
        table += "| " + " | ".join(str(cell) for cell in row) + " |\n"

    return table

def format_power_analysis(power_report: Dict[str, Any]) -> str:
    """Format power analysis results."""
    if not power_report:
        return "No power analysis available."

    lines = [
        f"### Detectable Effect Size",
        f"- **Power**: {power_report.get('power', 0.8):.1%}",
        f"- **Alpha**: {power_report.get('alpha', 0.05):.2f}",
        f"- **Sample Size (N)**: {power_report.get('n', 0)}",
        f"- **Detectable r (2-tailed)**: {power_report.get('detectable_r', 0):.4f}",
        "",
        f"### Confidence Intervals",
    ]

    for metric, ci in power_report.get("confidence_intervals", {}).items():
        lines.append(f"- **{metric}**: [{ci.get('lower', 0):.4f}, {ci.get('upper', 0):.4f}]")

    return "\n".join(lines)

def format_plots(plot_paths: List[str]) -> str:
    """Format plot paths into Markdown image references."""
    if not plot_paths:
        return "No plots generated."

    lines = ["### Generated Visualizations"]
    for i, path in enumerate(plot_paths, 1):
        if Path(path).exists():
          lines.append(f"![Plot {i}]({path})")
        else:
          lines.append(f"*Plot {i} not found: {path}*")

    return "\n".join(lines)

def generate_conclusion(correlation_results: List[Dict[str, Any]], power_report: Optional[Dict[str, Any]] = None) -> str:
    """
    Generate the conclusion section.
    CRITICAL: Must include 'associational relationship' or 'correlational evidence'
    if correlation results exist.
    """
    significant_count = sum(1 for r in correlation_results if r.get("significant", False))
    total_count = len(correlation_results)

    conclusion_parts = []

    if significant_count > 0:
        conclusion_parts.append(
            f"We found {significant_count} significant associations out of {total_count} tested metrics. "
            "This provides **correlational evidence** for a relationship between brain network dynamics "
            "and individual differences in sensorimotor performance. However, these findings represent an "
            "**associational relationship** and do not imply causation."
        )
    else:
        conclusion_parts.append(
            f"No significant associations were found among the {total_count} tested metrics. "
            "This suggests that, within the power of this study, we did not find **correlational evidence** "
            "for a strong **associational relationship** between the measured brain network properties "
            "and sensorimotor performance."
        )

    if power_report:
        detectable_r = power_report.get("detectable_r", 0)
        conclusion_parts.append(
            f"Post-hoc power analysis indicates that with our sample size, we could detect effect sizes "
            f"of r >= {detectable_r:.3f} with 80% power."
        )

    return " ".join(conclusion_parts)

def generate_report(
    correlation_results: List[Dict[str, Any]],
    power_report: Dict[str, Any],
    plot_paths: List[str],
    output_path: str = "data/analysis/report.md"
) -> str:
    """
    Assemble the full report.

    Args:
        correlation_results: List of dicts from T024/T025 (metric_name, r, p, q, significant)
        power_report: Dict from T026 (detectable_r, confidence_intervals, etc.)
        plot_paths: List of paths to generated PNG/PDF files
        output_path: Where to write the final report

    Returns:
        Path to the generated report
    """
    logger.log("report_generation_start", output_path=output_path)

    # Load template
    template = load_template()

    # Format sections
    timestamp = datetime.utcnow().isoformat()
    correlation_table = format_correlation_table(correlation_results)
    power_analysis = format_power_analysis(power_report)
    plots = format_plots(plot_paths)
    conclusion = generate_conclusion(correlation_results, power_report)

    # Limitations section with REQUIRED text
    limitations = f"""
    ### Study Limitations

    {LIMITATION_STATEMENT}

    Additional limitations include:
    - Cross-sectional design prevents causal inference.
    - Sample size may limit detection of small effect sizes.
    - Motion artifacts, while controlled, may still influence connectivity estimates.
    - The Schaefer atlas provides a fixed parcellation that may not capture individual anatomical variability.
    """

    # Assemble report
    report_content = template.replace("{{timestamp}}", timestamp)
    report_content = report_content.replace("{{correlation_table}}", correlation_table)
    report_content = report_content.replace("{{power_analysis}}", power_analysis)
    report_content = report_content.replace("{{plots}}", plots)
    report_content = report_content.replace("{{limitations}}", limitations)
    report_content = report_content.replace("{{conclusion}}", conclusion)
    # Summary placeholder (could be auto-generated from stats)
    summary = f"Analysis of {len(correlation_results)} network metrics against sensorimotor performance."
    report_content = report_content.replace("{{summary}}", summary)

    # Ensure output directory exists
    output_dir = Path(output_path).parent
    output_dir.mkdir(parents=True, exist_ok=True)

    # Write report
    Path(output_path).write_text(report_content)
    logger.log("report_generation_complete", output_path=output_path, length=len(report_content))

    return str(output_path)

def main() -> None:
    """
    Main entry point for report generation.
    Loads results from data files and generates the report.
    """
    logger.log("report_main_start")

    # Define paths
    base_path = Path("data/analysis")
    corr_file = base_path / "correlation_results.csv"
    power_file = base_path / "power_analysis.json"
    plots_dir = base_path / "plots"
    output_file = base_path / "report.md"

    # Load correlation results
    if corr_file.exists():
        df = pd.read_csv(corr_file)
        # Convert to list of dicts expected by formatter
        correlation_results = df.to_dict(orient="records")
    else:
        logger.log("correlation_file_missing", path=str(corr_file))
        correlation_results = []

    # Load power analysis
    power_report = {}
    if power_file.exists():
        import json
        with open(power_file, "r") as f:
            power_report = json.load(f)
    else:
        logger.log("power_file_missing", path=str(power_file))

    # Collect plot paths
    plot_paths = []
    if plots_dir.exists():
        plot_paths = [str(p) for p in plots_dir.glob("*.png")] + [str(p) for p in plots_dir.glob("*.pdf")]

    # Generate report
    report_path = generate_report(
        correlation_results=correlation_results,
        power_report=power_report,
        plot_paths=plot_paths,
        output_path=str(output_file)
    )

    print(f"Report generated successfully: {report_path}")
    logger.log("report_main_complete", report_path=report_path)

if __name__ == "__main__":
    main()