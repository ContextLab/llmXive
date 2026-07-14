"""Report generation module for the Brain Network Dynamics project.

Generates a comprehensive Markdown/PDF report by assembling templates
with correlation results, power analysis, plots, and limitations.
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


def load_template(template_path: str) -> str:
    """Load the report template from the specified path.

    Args:
        template_path: Path to the template file.

    Returns:
        The template content as a string.
    """
    path = Path(template_path)
    if not path.exists():
        logger.log("template_not_found", path=str(path))
        # Fallback template if file doesn't exist
        return """
        # Brain Network Dynamics and Sensorimotor Performance Report

        ## Executive Summary
        {{correlation_table}}

        ## Power Analysis
        {{power_analysis}}

        ## Visualizations
        {{plots}}

        ## Limitations
        {{limitations}}

        ## Conclusion
        {{conclusion}}
        """

    with open(path, 'r', encoding='utf-8') as f:
        return f.read()


def format_correlation_table(correlation_file: str) -> str:
    """Format the correlation results as a Markdown table.

    Args:
        correlation_file: Path to the CSV file containing correlation results.

    Returns:
        A Markdown-formatted table string.
    """
    path = Path(correlation_file)
    if not path.exists():
        logger.log("correlation_file_not_found", path=str(correlation_file))
        return "No correlation data available."

    try:
        df = pd.read_csv(path)
        # Ensure required columns exist
        required_cols = ['metric_name', 'r', 'p', 'q', 'significant']
        for col in required_cols:
            if col not in df.columns:
                df[col] = 'N/A'

        # Format the table
        table_lines = []
        table_lines.append("| Metric | Correlation (r) | p-value | FDR-corrected (q) | Significant |")
        table_lines.append("|--------|-----------------|---------|-------------------|-------------|")

        for _, row in df.iterrows():
            sig = "Yes" if row.get('significant', False) else "No"
            table_lines.append(
                f"| {row.get('metric_name', 'N/A')} | {row.get('r', 'N/A'):.4f} | "
                f"{row.get('p', 'N/A'):.4f} | {row.get('q', 'N/A'):.4f} | {sig} |"
            )

        return "\n".join(table_lines)
    except Exception as e:
        logger.log("correlation_table_error", error=str(e))
        return f"Error loading correlation data: {str(e)}"


def format_power_analysis(power_file: str) -> str:
    """Format the power analysis results.

    Args:
        power_file: Path to the file containing power analysis results.

    Returns:
        A formatted string describing the power analysis.
    """
    path = Path(power_file)
    if not path.exists():
        logger.log("power_file_not_found", path=str(power_file))
        return "No power analysis data available."

    try:
        # Try to load as CSV first
        df = pd.read_csv(path)
        if 'effect_size' in df.columns and 'power' in df.columns:
            lines = []
            for _, row in df.iterrows():
                lines.append(
                    f"- Detectable effect size (r) at 80% power: {row['effect_size']:.4f}"
                )
            return "\n".join(lines)
        else:
            # Fallback to text representation
            return df.to_markdown(index=False)
    except Exception as e:
        logger.log("power_analysis_error", error=str(e))
        return f"Error loading power analysis data: {str(e)}"


def format_plots(plots_dir: str) -> str:
    """Format the available plots as a list of image references.

    Args:
        plots_dir: Directory containing the generated plot images.

    Returns:
        A Markdown string with image references.
    """
    plots_path = Path(plots_dir)
    if not plots_path.exists():
        logger.log("plots_dir_not_found", path=str(plots_dir))
        return "No plots available."

    plot_files = list(plots_path.glob("*.png")) + list(plots_path.glob("*.pdf"))
    if not plot_files:
        return "No plot files found in the specified directory."

    plot_lines = []
    for plot_file in sorted(plot_files):
        # Create a relative path for the markdown
        rel_path = f"../{plots_dir}/{plot_file.name}"
        plot_lines.append(f"![{plot_file.stem}]({rel_path})")

    return "\n\n".join(plot_lines)


def generate_conclusion(correlation_results: Optional[pd.DataFrame] = None) -> str:
    """Generate the conclusion section based on correlation results.

    Args:
        correlation_results: DataFrame containing correlation results.

    Returns:
        A conclusion string with appropriate phrasing.
    """
    if correlation_results is None or correlation_results.empty:
        return (
            "The analysis did not yield significant correlation results. "
            "Further investigation with larger sample sizes is recommended."
        )

    significant_count = correlation_results['significant'].sum()
    total_count = len(correlation_results)

    if significant_count > 0:
        return (
            f"Based on the analysis of {total_count} network metrics, "
            f"{significant_count} showed significant associations with sensorimotor performance. "
            "These findings suggest a potential **associational relationship** between brain network dynamics "
            "and individual differences in sensorimotor performance. The observed correlations provide "
            "**correlational evidence** that specific network properties may be linked to motor task outcomes. "
            "However, causality cannot be inferred from these results."
        )
    else:
        return (
            f"Analysis of {total_count} network metrics did not reveal significant correlations "
            "with sensorimotor performance. This may indicate that the specific network properties examined "
            "are not strongly associated with the measured motor outcomes, or that a larger sample size "
            "is required to detect subtle effects. Further research with increased statistical power is recommended."
        )


def generate_report(
    correlation_file: str,
    power_file: str,
    plots_dir: str,
    output_path: str,
    template_path: str = "templates/report_template.md"
) -> str:
    """Generate the full report by assembling all components.

    Args:
        correlation_file: Path to correlation results CSV.
        power_file: Path to power analysis results.
        plots_dir: Directory containing plot images.
        output_path: Path where the final report will be saved.
        template_path: Path to the template file.

    Returns:
        Path to the generated report file.
    """
    # Load template
    template = load_template(template_path)

    # Format components
    correlation_table = format_correlation_table(correlation_file)
    power_analysis = format_power_analysis(power_file)
    plots = format_plots(plots_dir)

    # Load correlation data for conclusion generation
    correlation_df = None
    if Path(correlation_file).exists():
        try:
            correlation_df = pd.read_csv(correlation_file)
        except Exception as e:
            logger.log("conclusion_data_load_error", error=str(e))

    conclusion = generate_conclusion(correlation_df)

    # Define limitations section (REQUIRED)
    limitations = """
    ### Limitations

    - **Motor Task Performance is a proxy for proprioceptive accuracy.** The behavioral measures used in this study are indirect indicators of proprioceptive function and may be influenced by other sensorimotor processes.
    - **Cross-sectional design:** The analysis is based on a single time-point measurement, limiting causal inference.
    - **Sample size constraints:** The study may be underpowered to detect small effect sizes, as indicated by the power analysis.
    - **Network metric selection:** The choice of graph metrics may not capture all relevant aspects of brain network dynamics.
    - **Confounding variables:** While FD was controlled for, other potential confounders (e.g., head motion artifacts, scanner variability) may influence the results.
    """

    # Assemble the report
    report_content = template.replace("{{correlation_table}}", correlation_table)
    report_content = report_content.replace("{{power_analysis}}", power_analysis)
    report_content = report_content.replace("{{plots}}", plots)
    report_content = report_content.replace("{{limitations}}", limitations)
    report_content = report_content.replace("{{conclusion}}", conclusion)

    # Add timestamp
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    report_header = f"# Brain Network Dynamics and Sensorimotor Performance\n\n*Generated: {timestamp}*\n\n"
    report_content = report_header + report_content

    # Ensure output directory exists
    output_path_obj = Path(output_path)
    output_path_obj.parent.mkdir(parents=True, exist_ok=True)

    # Write the report
    with open(output_path_obj, 'w', encoding='utf-8') as f:
        f.write(report_content)

    logger.log("report_generated", output_path=str(output_path_obj))
    return str(output_path_obj)


def main() -> None:
    """Main entry point for report generation."""
    # Define paths
    base_dir = Path(__file__).parent.parent.parent
    correlation_file = base_dir / "data" / "analysis" / "correlations.csv"
    power_file = base_dir / "data" / "analysis" / "power_analysis.csv"
    plots_dir = base_dir / "figures"
    output_path = base_dir / "docs" / "report.md"
    template_path = base_dir / "templates" / "report_template.md"

    # Check if required files exist
    if not correlation_file.exists():
        logger.log("missing_correlation_file", path=str(correlation_file))
        print(f"Error: Correlation file not found at {correlation_file}")
        print("Please run the analysis pipeline first to generate correlation results.")
        sys.exit(1)

    if not power_file.exists():
        logger.log("missing_power_file", path=str(power_file))
        print(f"Warning: Power analysis file not found at {power_file}")
        print("Continuing without power analysis data.")

    # Generate report
    try:
        result_path = generate_report(
            correlation_file=str(correlation_file),
            power_file=str(power_file) if power_file.exists() else "",
            plots_dir=str(plots_dir),
            output_path=str(output_path),
            template_path=str(template_path)
        )
        print(f"Report successfully generated at: {result_path}")
    except Exception as e:
        logger.log("report_generation_failed", error=str(e))
        print(f"Error generating report: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
