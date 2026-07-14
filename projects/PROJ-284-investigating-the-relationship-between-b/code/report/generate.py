from __future__ import annotations

import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd
import numpy as np

from code.logging_config import get_logger

logger = get_logger(__name__)

# Constants for required text
LIMITATION_TEXT = "Motor Task Performance is a proxy for proprioceptive accuracy."
ASSOCIATIONAL_PHRASES = ["associational relationship", "correlational evidence"]

def load_template(template_path: str = "templates/report_template.md") -> str:
    """Load the markdown template from disk."""
    path = Path(template_path)
    if not path.exists():
        # Create a default template if missing to ensure execution
        path.parent.mkdir(parents=True, exist_ok=True)
        default_content = """
        # Brain Network Dynamics and Sensorimotor Performance Report
        Generated: {{timestamp}}

        ## Correlation Results
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
        path.write_text(default_content)
        logger.log("template_created", path=str(path))

    return path.read_text()

def format_correlation_table(results_df: Optional[pd.DataFrame]) -> str:
    """Format correlation results into a markdown table."""
    if results_df is None or results_df.empty:
        return "| Metric | r | p | q | Significant |\n|---|---|---|---|---|\n| *No significant correlations found* | - | - | - | - |"

    # Ensure required columns exist
    required_cols = ["metric_name", "r", "p", "q", "significant"]
    for col in required_cols:
        if col not in results_df.columns:
            # Try to map common aliases
            if "name" in results_df.columns and col == "metric_name":
                results_df = results_df.rename(columns={"name": "metric_name"})
            else:
                # Fill missing with defaults
                results_df[col] = 0.0 if col in ["r", "p", "q"] else False

    # Filter for significant results first for display, or show all if none
    display_df = results_df[results_df["significant"]] if results_df["significant"].any() else results_df

    table_md = "| Metric | r | p | q | Significant |\n|---|---|---|---|---|\n"
    for _, row in display_df.iterrows():
        sig_str = "Yes" if row["significant"] else "No"
        table_md += f"| {row['metric_name']} | {row['r']:.3f} | {row['p']:.4f} | {row['q']:.4f} | {sig_str} |\n"

    return table_md

def format_power_analysis(power_df: Optional[pd.DataFrame]) -> str:
    """Format power analysis results."""
    if power_df is None or power_df.empty:
        return "Power analysis could not be computed due to missing data."

    md = "| Metric | Detectable Effect Size (r) | Power (80%) | Alpha |\n|---|---|---|---|\n"
    for _, row in power_df.iterrows():
        metric = row.get("metric_name", "Unknown")
        r_val = row.get("detectable_r", 0.0)
        md += f"| {metric} | {r_val:.3f} | 0.80 | 0.05 |\n"
    return md

def format_plots(plots_dir: str = "figures") -> str:
    """Generate markdown references for generated plots."""
    plots_path = Path(plots_dir)
    if not plots_path.exists():
        return "No visualization files generated."

    images = list(plots_path.glob("*.png")) + list(plots_path.glob("*.jpg"))
    if not images:
        return "No image files found in figures directory."

    md = ""
    for img in images:
        # Ensure relative path for markdown
        rel_path = img.relative_to(Path("."))
        md += f"![{img.stem}]({rel_path})\n\n"
    return md

def generate_conclusion(results_df: Optional[pd.DataFrame], power_df: Optional[pd.DataFrame]) -> str:
    """
    Generate the conclusion section.
    CRITICAL: Must include 'associational relationship' or 'correlational evidence'
    based on correlation results.
    """
    has_significant = False
    if results_df is not None and not results_df.empty:
        has_significant = results_df["significant"].any()

    conclusion = []

    if has_significant:
        # Use required phrase
        conclusion.append(
            "The analysis provides evidence of an **associational relationship** between specific brain network dynamics "
            "and individual differences in sensorimotor performance. Significant correlations were observed after FDR correction, "
            "suggesting that network topology may influence motor task outcomes."
        )
    else:
        conclusion.append(
            "No statistically significant correlations were found after FDR correction. "
            "While this does not rule out an **associational relationship**, the current sample size "
            "may lack the power to detect smaller effect sizes, as indicated by the power analysis."
        )

    if power_df is not None and not power_df.empty:
        # Add context about power
        avg_detectable = power_df["detectable_r"].mean() if "detectable_r" in power_df.columns else 0.5
        conclusion.append(
            f"Post-hoc power analysis indicates that the study was powered to detect effect sizes (r) of approximately {avg_detectable:.2f} or larger."
        )

    return " ".join(conclusion)

def generate_report(
    correlation_results: Optional[pd.DataFrame] = None,
    power_results: Optional[pd.DataFrame] = None,
    plots_dir: str = "figures",
    output_path: str = "docs/report.md",
    template_path: str = "templates/report_template.md"
) -> Path:
    """
    Assemble the full report.
    """
    logger.log("report_generation_start", output=str(output_path))

    # Load template
    template = load_template(template_path)

    # Format sections
    corr_table = format_correlation_table(correlation_results)
    power_table = format_power_analysis(power_results)
    plots_md = format_plots(plots_dir)
    conclusion = generate_conclusion(correlation_results, power_results)

    # Prepare limitations text (Required)
    limitations = f"""
    - {LIMITATION_TEXT}
    - The study relies on cross-sectional data, limiting causal inference.
    - Motion artifacts, although regressed, may still influence connectivity estimates.
    """

    # Substitute variables
    report_content = template.replace("{{correlation_table}}", corr_table)
    report_content = report_content.replace("{{power_analysis}}", power_table)
    report_content = report_content.replace("{{plots}}", plots_md)
    report_content = report_content.replace("{{limitations}}", limitations)
    report_content = report_content.replace("{{conclusion}}", conclusion)
    report_content = report_content.replace("{{timestamp}}", datetime.utcnow().isoformat())

    # Ensure output directory exists
    out_path = Path(output_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    # Write file
    out_path.write_text(report_content)
    logger.log("report_generation_complete", path=str(out_path), size=len(report_content))

    return out_path

def main():
    """
    Entry point for the report generator.
    Loads data from expected analysis outputs and generates the report.
    """
    # Define paths based on project structure
    base_dir = Path(__file__).resolve().parent.parent.parent
    corr_file = base_dir / "data" / "analysis" / "correlations.csv"
    power_file = base_dir / "data" / "analysis" / "power_analysis.csv"
    output_file = base_dir / "docs" / "report.md"

    # Load data if exists
    correlation_df = None
    if corr_file.exists():
        try:
            correlation_df = pd.read_csv(corr_file)
            logger.log("data_loaded", file=str(corr_file), rows=len(correlation_df))
        except Exception as e:
            logger.log("data_load_error", file=str(corr_file), error=str(e))
    else:
        logger.log("data_missing", file=str(corr_file), warning="Correlation results file not found.")

    power_df = None
    if power_file.exists():
        try:
            power_df = pd.read_csv(power_file)
            logger.log("data_loaded", file=str(power_file), rows=len(power_df))
        except Exception as e:
            logger.log("data_load_error", file=str(power_file), error=str(e))
    else:
        logger.log("data_missing", file=str(power_file), warning="Power analysis file not found.")

    # Generate report
    try:
        result_path = generate_report(
            correlation_results=correlation_df,
            power_results=power_df,
            plots_dir=str(base_dir / "figures"),
            output_path=str(output_file)
        )
        print(f"Report generated successfully: {result_path}")
        return 0
    except Exception as e:
        logger.log("report_generation_failed", error=str(e))
        print(f"Error generating report: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
